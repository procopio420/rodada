from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.access.services import AccessServiceError
from modules.venue.stations import (STATIONS, StationChangeError, apply_station_change,
                                   preview_station_change, station_snapshot)


class StationChangeInput(serializers.Serializer):
    expected_version = serializers.IntegerField(min_value=1)
    enabled = serializers.BooleanField()
    label = serializers.CharField(max_length=120, allow_blank=True, default="")
    reason = serializers.CharField(max_length=240, allow_blank=True, default="")

    def validate(self, data):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError("Configuração desconhecida.")
        return data


class StationListView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.VENUE_CONFIGURE

    def get(self, request):
        return Response({"section": "stations", "results": [
            station_snapshot(request.actor_context.venue_id, station) for station in STATIONS]})


class StationPreviewView(StationListView):
    http_method_names = ["post", "options"]

    def post(self, request, station):
        data = StationChangeInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = dict(data.validated_data)
        values.pop("reason")
        try:
            return Response(preview_station_change(venue_id=request.actor_context.venue_id,
                                                   station=station, **values))
        except StationChangeError as exc:
            return Response({"code": exc.code, "message": exc.message, **(exc.details or {})}, status=exc.status_code)


class StationApplyView(StationListView):
    http_method_names = ["post", "options"]

    def post(self, request, station):
        data = StationChangeInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            return Response(apply_station_change(actor=request.actor_context, station=station,
                                                 **data.validated_data))
        except (StationChangeError, AccessServiceError) as exc:
            return Response({"code": exc.code, "message": exc.message, **(exc.details or {})}, status=exc.status_code)
