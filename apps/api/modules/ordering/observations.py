"""Passive, bounded, session-scoped intake, deliberately separate from ordering."""
import hashlib
import json
from datetime import timedelta

from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.ordering.models import OrderClientObservation

RETENTION_DAYS = 7


class StrictInput(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError("Campos de observação inválidos.")
        return super().to_internal_value(data)


class ObservationInput(StrictInput):
    event_id = serializers.UUIDField()
    intent_ref = serializers.RegexField(r"\A[a-f0-9]{64}\Z")
    kind = serializers.ChoiceField(choices=["INTENT_SAVED", "ATTEMPT_FINISHED"])
    channel = serializers.ChoiceField(choices=["WEB", "ANDROID"])
    ux_version = serializers.ChoiceField(choices=["033-ux2"])
    app_version = serializers.RegexField(r"\A[a-zA-Z0-9._+-]{1,40}\Z")
    attempt_id = serializers.UUIDField(allow_null=True, default=None)
    outcome = serializers.ChoiceField(choices=["", "CONFIRMED", "REJECTED", "UNKNOWN", "PREFLIGHT"], default="")
    reason = serializers.ChoiceField(choices=["", "SERVER_REJECTION", "UNCERTAIN", "SESSION_CHANGED", "AUTH_UNAVAILABLE", "PREPARATION_FAILED"], default="")
    recovery = serializers.BooleanField(default=False)
    duration_ms = serializers.IntegerField(min_value=0, max_value=3_600_000, allow_null=True, default=None)

    def validate(self, data):
        if data["kind"] == "INTENT_SAVED":
            if any(data[k] for k in ("attempt_id", "outcome", "reason", "recovery")) or data["duration_ms"] is not None:
                raise serializers.ValidationError("Intenção não é tentativa.")
        else:
            reason = {"CONFIRMED": "", "REJECTED": "SERVER_REJECTION", "UNKNOWN": "UNCERTAIN"}
            if not data["attempt_id"] or not data["outcome"]:
                raise serializers.ValidationError("Tentativa sem resultado.")
            if data["outcome"] in reason and data["reason"] != reason[data["outcome"]]:
                raise serializers.ValidationError("Proveniência inválida.")
            if data["outcome"] == "PREFLIGHT" and data["reason"] not in {"SESSION_CHANGED", "AUTH_UNAVAILABLE", "PREPARATION_FAILED"}:
                raise serializers.ValidationError("Proveniência inválida.")
        return data


class BatchInput(StrictInput):
    origin_venue = serializers.UUIDField()
    origin_session = serializers.UUIDField()
    events = ObservationInput(many=True, allow_empty=False, max_length=8)


class ObservationThrottle(SimpleRateThrottle):
    scope = "attendance_observation"
    rate = "120/min"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": str(request.auth.pk)}


class ObservationIntakeView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability)
    required_capability = Capability.ORDER_CONFIRM
    throttle_classes = (ObservationThrottle,)

    def post(self, request):
        if len(request.body) > 8192:
            return Response({"code": "OBSERVATION_TOO_LARGE"}, status=413)
        data = BatchInput(data=request.data)
        data.is_valid(raise_exception=True)
        batch = data.validated_data
        if batch["origin_venue"] != request.auth.venue_id or batch["origin_session"] != request.auth.pk:
            return Response({"code": "OBSERVATION_ORIGIN_CHANGED"}, status=403)
        # This transaction touches only observation rows. A conflict rolls back
        # the batch; it can never commit/rollback an Order or a ledger posting.
        with transaction.atomic():
            for event in sorted(batch["events"], key=lambda item: str(item["event_id"])):
                fingerprint = hashlib.sha256(json.dumps(event, sort_keys=True, default=str).encode()).hexdigest()
                obj, created = OrderClientObservation.objects.get_or_create(
                    venue_id=request.auth.venue_id, event_id=event["event_id"],
                    defaults={**event, "fingerprint": fingerprint})
                if not created and obj.fingerprint != fingerprint:
                    transaction.set_rollback(True)
                    return Response({"code": "OBSERVATION_EVENT_CONFLICT"}, status=409)
        return Response(status=204)


class ObservationReportView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability)
    required_capability = Capability.MANAGEMENT_REPORTS_READ

    def get(self, request):
        now = timezone.now()
        lower = now - timedelta(days=RETENTION_DAYS)
        groups = OrderClientObservation.objects.filter(venue_id=request.auth.venue_id,
            created_at__gte=lower, created_at__lte=now).values(
                "channel", "ux_version", "app_version", "kind", "outcome", "reason", "recovery",
            ).annotate(events=Count("id"), intents=Count("intent_ref", distinct=True),
                timed=Count("duration_ms"), mean_duration_ms=Avg("duration_ms")).order_by(
                    "channel", "ux_version", "app_version", "kind", "outcome", "reason", "recovery")
        rows = list(groups[:501])
        return Response({"truncated": len(rows) > 500, "source": "CLIENT_REPORTED_BEST_EFFORT", "start": lower, "end": now,
            "retention_days": RETENTION_DAYS, "groups": rows[:500],
            "limitations": ["Events may be lost or forged by authorized clients.",
                "No financial duplicate/order count or confirmed delivery can be inferred.",
                "Duration covers one logical attempt, never elapsed time across restart.",
                "Intent counts are distinct within each group, not additive between groups."]})
