"""Privacy-minimal, bounded-schema UX2 telemetry ingestion."""
from django.db import IntegrityError, transaction
from django.db.models import F
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.venue.calendar import business_date
from modules.venue.models import AttendanceTelemetryDaily, AttendanceTelemetryReceipt

EVENTS = ("intent_started", "confirm_attempted", "confirm_failed", "confirm_recovered", "confirm_acknowledged")
PLATFORMS = ("WEB", "ANDROID")

class TelemetryInput(serializers.Serializer):
    event_id = serializers.UUIDField()
    version = serializers.IntegerField(min_value=1, max_value=1)
    platform = serializers.ChoiceField(choices=PLATFORMS)
    event = serializers.ChoiceField(choices=EVENTS)
    duration_ms = serializers.IntegerField(min_value=0, max_value=3600000, required=False)

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - {"event_id", "version", "platform", "event", "duration_ms"}:
            raise serializers.ValidationError({"non_field_errors": ["Unknown telemetry fields."]})
        return super().to_internal_value(data)

    def validate(self, data):
        if "duration_ms" in data and data["event"] != "confirm_acknowledged":
            raise serializers.ValidationError({"duration_ms": "Only confirmation can carry a duration."})
        return data

class AttendanceTelemetryIngestView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.ORDER_CONFIRM

    def post(self, request):
        payload = TelemetryInput(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        venue = request.auth.venue
        with transaction.atomic():
            try:
                with transaction.atomic():
                    AttendanceTelemetryReceipt.objects.create(id=data["event_id"], venue=venue)
            except IntegrityError:
                if AttendanceTelemetryReceipt.objects.filter(pk=data["event_id"], venue=venue).exists():
                    return Response({"accepted": True, "duplicate": True})
                return Response({"accepted": False, "code": "EVENT_ID_COLLISION"}, status=409)
            row, _ = AttendanceTelemetryDaily.objects.get_or_create(
                venue=venue, business_date=business_date(venue), platform=data["platform"],
                event=data["event"])
            duration = data.get("duration_ms")
            AttendanceTelemetryDaily.objects.filter(pk=row.pk).update(
                count=F("count") + 1,
                duration_total_ms=F("duration_total_ms") + (duration or 0),
                duration_observed=F("duration_observed") + int(duration is not None))
        return Response({"accepted": True, "duplicate": False}, status=202)
