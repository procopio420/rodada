# ruff: noqa: RUF012
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .kds import assess_station, configure_detector, heartbeat
from .views import authorize, manage


class StrictInput(serializers.Serializer):
    def to_internal_value(self, data):
        if set(data) - set(self.fields):
            raise serializers.ValidationError("Unknown fields; identity and time are server-owned.")
        return super().to_internal_value(data)


class HeartbeatInput(StrictInput):
    queue_observed = serializers.BooleanField()
    client_version = serializers.CharField(max_length=64, required=False, default="", allow_blank=True)


class DetectorInput(StrictInput):
    expected_version = serializers.IntegerField(min_value=1)
    heartbeat_ttl_seconds = serializers.IntegerField(min_value=5, max_value=300)
    failure_threshold_seconds = serializers.IntegerField(min_value=30, max_value=3600)
    recovery_threshold_seconds = serializers.IntegerField(min_value=30, max_value=3600)
    reason = serializers.CharField(max_length=240)


def payload(row):
    return {
        "station": row.station, "state": row.state, "version": row.version,
        "heartbeat_ttl_seconds": row.heartbeat_ttl_seconds,
        "failure_threshold_seconds": row.failure_threshold_seconds,
        "recovery_threshold_seconds": row.recovery_threshold_seconds,
        "suspect_since": row.suspect_since, "recovery_since": row.recovery_since,
        "updated_at": row.updated_at,
        # D1 deliberately has no activation path or PrintJob-producing evaluator.
        "auto_fallback_enabled": False,
    }


class KdsHeartbeatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, station):
        authorize(request, station)
        data = HeartbeatInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(payload(heartbeat(session_id=request.auth.id, station=station, **data.validated_data)))


class KdsHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        manage(request)
        return Response({"results": [payload(assess_station(venue_id=request.auth.venue_id, station=station)) for station in ("BAR", "KITCHEN")]})


class KdsDetectorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, station):
        manage(request)
        data = DetectorInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(payload(configure_detector(actor=request.actor_context, station=station, **data.validated_data)))
