from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.house_account.services import authorize
from modules.ordering.models import Tab
from .models import ServicePoint
from .services import OperationError, execute, preview, transferability


class Line(serializers.Serializer):
    charge_id = serializers.UUIDField()
    amount_cents = serializers.IntegerField(min_value=1, max_value=2147483647, required=False)
    quantity = serializers.IntegerField(min_value=1, required=False)


class Command(serializers.Serializer):
    kind = serializers.ChoiceField(choices=("MOVE_LOCATION", "SPLIT", "MOVE_ITEMS", "MERGE", "CANCEL_EMPTY", "REOPEN"))
    expected_version = serializers.IntegerField(min_value=1)
    destination_tab_id = serializers.UUIDField(required=False)
    destination_version = serializers.IntegerField(min_value=1, required=False)
    destination_label = serializers.CharField(max_length=120, required=False, allow_blank=True)
    lines = Line(many=True, required=False)
    reason = serializers.CharField(max_length=240, required=False, allow_blank=True)
    occupancy_id = serializers.UUIDField(required=False, allow_null=True)
    service_point_id = serializers.UUIDField(required=False, allow_null=True)
    idempotency_key = serializers.CharField(max_length=120, required=False)


def error_response(error):
    return Response({"code": error.code, "message": error.message, **(error.details or {})}, status=error.status_code)


class OperationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, tab_id):
        authorize(request.actor_context, Capability.TAB_OPEN)
        tab = Tab.objects.filter(pk=tab_id, venue_id=request.auth.venue_id).first()
        if not tab:
            return Response({"code": "TAB_NOT_FOUND", "message": "Comanda não encontrada."}, status=404)
        from modules.audit.models import AuditEvent
        payload = transferability(tab)
        payload["history"] = list(AuditEvent.objects.filter(venue_id=tab.venue_id, entity_type="Tab", entity_id=str(tab.id)).order_by("occurred_at").values("event_type", "occurred_at", "reason", "metadata"))
        from django.db.models import Q
        from .models import TabTransfer
        payload["transfers"] = [{"id": str(t.id), "kind": t.kind, "source_tab_id": str(t.source_tab_id),
            "destination_tab_id": str(t.destination_tab_id), "amount_cents": sum(l.amount_cents for l in t.lines.all())}
            for t in TabTransfer.objects.filter(Q(source_tab=tab) | Q(destination_tab=tab)).prefetch_related("lines")]
        return Response(payload)

    def post(self, request, tab_id):
        serializer = Command(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return Response(execute(tab_id=tab_id, data=serializer.validated_data, actor=request.actor_context))
        except OperationError as error:
            return error_response(error)


class PreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, tab_id):
        serializer = Command(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["kind"] not in ("SPLIT", "MOVE_ITEMS", "MERGE"):
            return Response({"code": "INVALID_OPERATION", "message": "Prévia disponível para transferências."}, status=400)
        try:
            return Response(preview(tab_id=tab_id, data=serializer.validated_data, actor=request.actor_context))
        except OperationError as error:
            return error_response(error)


class ServicePointView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"results": list(ServicePoint.objects.filter(venue_id=request.auth.venue_id, is_active=True).values("id", "label"))})
