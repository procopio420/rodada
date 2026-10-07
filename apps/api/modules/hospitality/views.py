from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.hospitality.models import Table, TableOccupancy
from modules.hospitality.serializers import (
    AssignTabSerializer,
    OccupyTableSerializer,
    TableCreateSerializer,
)
from modules.hospitality.services import (
    HospitalityServiceError,
    assign_tab,
    complete_cleaning,
    create_table,
    occupy_table,
    release_table,
    start_cleaning,
)


def _error_response(error: HospitalityServiceError) -> Response:
    payload = {"code": error.code, "message": error.message}
    if error.details:
        payload.update(error.details)
    return Response(payload, status=error.status_code)


def _occupancy_payload(occupancy: TableOccupancy) -> dict:
    assignments = occupancy.tab_assignments.select_related("tab").all()
    return {
        "id": str(occupancy.id),
        "table_id": str(occupancy.table_id),
        "generation": occupancy.generation,
        "started_at": occupancy.started_at,
        "released_at": occupancy.released_at,
        "cleaning_started_at": occupancy.cleaning_started_at,
        "ready_at": occupancy.ready_at,
        "tabs": [
            {"id": str(assignment.tab_id), "display_label": assignment.tab.display_label}
            for assignment in assignments
        ],
    }


def _table_payload(table: Table) -> dict:
    active = table.occupancies.filter(released_at__isnull=True).first()
    return {
        "id": str(table.id),
        "label": table.label,
        "public_token": table.public_token,
        "access_generation": table.access_generation,
        "guest_ordering_mode": table.guest_ordering_mode,
        "guest_ordering_blocked": table.guest_ordering_blocked,
        "status": table.status,
        "active_occupancy": _occupancy_payload(active) if active else None,
    }


class TableListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tables = Table.objects.filter(venue=request.auth.venue).prefetch_related(
            "occupancies__tab_assignments__tab"
        )
        return Response({"results": [_table_payload(table) for table in tables]})

    def post(self, request):
        permission = RequireCapability()
        self.required_capability = Capability.VENUE_CONFIGURE
        permission.has_permission(request, self)
        serializer = TableCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        table = create_table(actor=request.actor_context, **serializer.validated_data)
        return Response(_table_payload(table), status=201)


class TableOccupyView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.TABLE_MANAGE

    def post(self, request, table_id):
        serializer = OccupyTableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            occupancy = occupy_table(
                table_id=table_id, actor=request.actor_context, **serializer.validated_data
            )
        except HospitalityServiceError as error:
            return _error_response(error)
        return Response(_occupancy_payload(occupancy), status=201)


class OccupancyAssignTabView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.TABLE_MANAGE

    def post(self, request, occupancy_id):
        serializer = AssignTabSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assignment = assign_tab(
                occupancy_id=occupancy_id, actor=request.actor_context, **serializer.validated_data
            )
        except HospitalityServiceError as error:
            return _error_response(error)
        return Response({"id": str(assignment.id), "tab_id": str(assignment.tab_id)}, status=201)


class TableReleaseView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.TABLE_MANAGE

    def post(self, request, table_id):
        try:
            occupancy = release_table(table_id=table_id, actor=request.actor_context)
        except HospitalityServiceError as error:
            return _error_response(error)
        return Response(_occupancy_payload(occupancy))


class TableCleaningStartView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.TABLE_MANAGE

    def post(self, request, table_id):
        try:
            occupancy = start_cleaning(table_id=table_id, actor=request.actor_context)
        except HospitalityServiceError as error:
            return _error_response(error)
        return Response(_occupancy_payload(occupancy))


class TableCleaningCompleteView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.TABLE_MANAGE

    def post(self, request, table_id):
        try:
            occupancy = complete_cleaning(table_id=table_id, actor=request.actor_context)
        except HospitalityServiceError as error:
            return _error_response(error)
        return Response(_occupancy_payload(occupancy))
