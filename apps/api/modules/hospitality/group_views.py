"""Staff-authorised physical grouping surface (Spec 004 TABLE-011)."""

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.hospitality.groups import (
    create_table_group, dissolve_table_group, group_payload,
)
from modules.hospitality.models import TableGroup
from modules.hospitality.services import HospitalityServiceError


class GroupCreateInput(serializers.Serializer):
    table_ids = serializers.ListField(
        child=serializers.UUIDField(), min_length=2, max_length=20,
    )
    label = serializers.CharField(max_length=80, allow_blank=True, default="")
    request_key = serializers.UUIDField()

    def validate_table_ids(self, values):
        if len(set(values)) != len(values):
            raise serializers.ValidationError("Mesas duplicadas não são permitidas.")
        return values


def _error(error):
    return Response(
        {"code": error.code, "message": error.message, **(error.details or {})},
        status=error.status_code,
    )


class TableGroupListCreateView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability)
    required_capability = Capability.TABLE_MANAGE

    def get(self, request):
        groups = (
            TableGroup.objects.filter(
                venue_id=request.actor_context.venue_id, dissolved_at__isnull=True,
            )
            .order_by("created_at", "id")
        )
        return Response({"results": [group_payload(group) for group in groups]})

    def post(self, request):
        data = GroupCreateInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            group, replayed = create_table_group(
                actor=request.actor_context, **data.validated_data
            )
        except HospitalityServiceError as error:
            return _error(error)
        return Response(
            {**group_payload(group), "replayed": replayed},
            status=200 if replayed else 201,
        )


class TableGroupDissolveView(APIView):
    permission_classes = (IsAuthenticated, RequireCapability)
    required_capability = Capability.TABLE_MANAGE

    def post(self, request, group_id):
        try:
            group, replayed = dissolve_table_group(
                actor=request.actor_context, group_id=group_id
            )
        except HospitalityServiceError as error:
            return _error(error)
        return Response({**group_payload(group), "replayed": replayed})
