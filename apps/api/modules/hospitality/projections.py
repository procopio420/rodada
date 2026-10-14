"""Staff-only batch projection; no financial aggregation or dispatch mutations."""

from django.db.models import Prefetch

from modules.hospitality.models import Table, TableOccupancy, TabOccupancyAssignment
from modules.ordering.models import Order


def staff_tables(venue_id):
    tables = list(
        Table.objects.filter(venue_id=venue_id)
        .select_related("zone")
        .prefetch_related(
            Prefetch(
                "occupancies",
                queryset=TableOccupancy.objects.filter(released_at__isnull=True)
                .select_related("responsible_staff")
                .prefetch_related(
                    Prefetch(
                        "tab_assignments",
                        queryset=TabOccupancyAssignment.objects.filter(released_at__isnull=True)
                        .exclude(tab__state__in=("CLOSED", "CANCELLED"))
                        .select_related("tab"),
                        to_attr="current_assignments",
                    ),
                    "party_size_observations",
                ),
                to_attr="current_occupancies",
            ),
        )
    )
    placements = {
        a.tab_id: (o, a)
        for t in tables
        for o in t.current_occupancies
        for a in o.current_assignments
    }
    orders = Order.objects.filter(
        tab_id__in=placements, source="GUEST", status="CONFIRMED"
    ).prefetch_related("items")
    grouped = {}
    for order in orders:
        occupancy, assignment = placements[order.tab_id]
        if occupancy.responsible_staff_id or order.confirmed_at < assignment.assigned_at:
            continue
        pending = [i for i in order.items.all() if i.state not in ("DELIVERED", "CANCELLED")]
        if pending:
            grouped.setdefault(occupancy.id, []).append(
                (order.confirmed_at, any(i.state == "READY" for i in pending))
            )
    for table in tables:
        for occupancy in table.current_occupancies:
            pending = grouped.get(occupancy.id, [])
            occupancy.service_attention = {
                "unassigned_service_attention": (
                    "NONE"
                    if occupancy.responsible_staff_id
                    else "UNASSIGNED_READY"
                    if any(ready for _, ready in pending)
                    else "UNASSIGNED_GUEST_ORDER"
                    if pending
                    else "UNASSIGNED_NO_ORDER"
                ),
                "unassigned_guest_order_count": len(pending),
                "oldest_unassigned_guest_order_at": min((at for at, _ in pending), default=None),
            }
    return tables
