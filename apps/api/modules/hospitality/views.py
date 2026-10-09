from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.hospitality.models import Table, TableOccupancy, Zone
from modules.hospitality.serializers import (
    AssignTabSerializer,
    GuestOrderingBlockSerializer,
    OccupyTableSerializer,
    TableCreateSerializer,
    TableLocationSerializer,
    ZoneCreateSerializer,
)
from modules.hospitality.services import (
    HospitalityServiceError,
    assign_tab,
    complete_cleaning,
    create_table,
    create_zone,
    occupy_table,
    release_table,
    set_table_location,
    set_guest_ordering_blocked,
    start_cleaning,
)


def _error_response(error: HospitalityServiceError) -> Response:
    payload = {"code": error.code, "message": error.message}
    if error.details:
        payload.update(error.details)
    return Response(payload, status=error.status_code)


def _occupancy_payload(occupancy: TableOccupancy) -> dict:
    from modules.hospitality.party_size import current_party_size, observation_payload

    assignments = occupancy.tab_assignments.select_related("tab").all()
    return {
        "id": str(occupancy.id),
        "table_id": str(occupancy.table_id),
        "generation": occupancy.generation,
        "party_size": observation_payload(current_party_size(occupancy_id=occupancy.id)),
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
        "zone": ({"id": str(table.zone_id), "label": table.zone.label} if table.zone_id else None),
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
        tables = (
            Table.objects.filter(venue=request.auth.venue)
            .select_related("zone")
            .prefetch_related("occupancies__tab_assignments__tab")
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


class ZoneListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        zones = Zone.objects.filter(venue=request.auth.venue, is_active=True)
        return Response(
            {
                "results": [
                    {"id": str(zone.id), "label": zone.label, "is_active": zone.is_active}
                    for zone in zones
                ]
            }
        )

    def post(self, request):
        permission = RequireCapability()
        self.required_capability = Capability.VENUE_CONFIGURE
        permission.has_permission(request, self)
        serializer = ZoneCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        zone = create_zone(actor=request.actor_context, **serializer.validated_data)
        return Response(
            {"id": str(zone.id), "label": zone.label, "is_active": zone.is_active}, status=201
        )


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


class TableLocationView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.TABLE_MANAGE

    def post(self, request, table_id):
        serializer = TableLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            table = set_table_location(
                table_id=table_id,
                zone_id=serializer.validated_data["zone_id"],
                actor=request.actor_context,
            )
        except HospitalityServiceError as error:
            return _error_response(error)
        return Response(_table_payload(table))


class TableGuestOrderingBlockView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.TABLE_MANAGE

    def post(self, request, table_id):
        serializer = GuestOrderingBlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            table = set_guest_ordering_blocked(
                table_id=table_id,
                blocked=serializer.validated_data["blocked"],
                actor=request.actor_context,
            )
        except HospitalityServiceError as error:
            return _error_response(error)
        return Response(_table_payload(table))


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


class PartySizeView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.TABLE_MANAGE

    def get(self, request, occupancy_id=None, tab_id=None):
        from modules.hospitality.models import PartySizeObservation
        from modules.hospitality.party_size import current_party_size, observation_payload
        from modules.ordering.models import Tab

        target = (
            TableOccupancy.objects.filter(
                pk=occupancy_id, table__venue_id=request.actor_context.venue_id
            ).first()
            if occupancy_id
            else Tab.objects.filter(pk=tab_id, venue_id=request.actor_context.venue_id).first()
        )
        if target is None:
            return Response({"code": "TARGET_NOT_FOUND"}, status=404)
        history = PartySizeObservation.objects.filter(occupancy_id=occupancy_id, tab_id=tab_id)
        return Response(
            {
                "current": observation_payload(
                    current_party_size(occupancy_id=occupancy_id, tab_id=tab_id)
                ),
                "history": [observation_payload(row) for row in history],
            }
        )

    def post(self, request, occupancy_id=None, tab_id=None):
        from modules.hospitality.serializers import PartySizeSerializer
        from modules.hospitality.party_size import record_party_size, observation_payload

        serializer = PartySizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            row = record_party_size(
                actor=request.actor_context,
                occupancy_id=occupancy_id,
                tab_id=tab_id,
                **serializer.validated_data,
            )
        except HospitalityServiceError as error:
            return _error_response(error)
        return Response(observation_payload(row))
