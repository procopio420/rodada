"""Read-only operational targets. Labels never establish an account identity."""

from django.db.models import F
from django.utils import timezone

from modules.hospitality.models import TableStatus, TabOccupancyAssignment


def staff_tasks(queryset):
    return queryset.select_related(
        "destination_occupancy__table", "requested_tab", "requesting_guest_session",
        "order_item__order__tab", "order_item__product",
    ).prefetch_related("order_item__corrections")


class StaffTargets:
    def __init__(self, tasks, *, venue_id):
        self.venue_id = venue_id
        tab_ids = {
            task.order_item.order.tab_id if task.order_item_id else task.requested_tab_id
            for task in tasks
        } - {None}
        self.assignments = {
            assignment.tab_id: assignment
            for assignment in TabOccupancyAssignment.objects.filter(
                tab_id__in=tab_ids, tab__venue_id=venue_id,
                released_at__isnull=True, occupancy__released_at__isnull=True,
                occupancy__table__venue_id=venue_id,
                occupancy__table__status=TableStatus.OCCUPIED,
                occupancy__generation=F("occupancy__table__access_generation"),
            ).select_related("occupancy__table")
        }

    def target(self, task):
        target = {
            "kind": "UNAVAILABLE", "tab_id": None, "table_id": None,
            "occupancy_id": None, "generation": None,
        }
        if task.venue_id != self.venue_id:
            return target
        if task.order_item_id:
            tab = task.order_item.order.tab
            if tab.venue_id != self.venue_id:
                return target
            target.update(kind="TAB", tab_id=str(tab.id))
            assignment = self.assignments.get(tab.id)
            if assignment:
                self._context(target, assignment.occupancy)
            # Financial close never strands already confirmed production.
            return target
        occupancy = task.destination_occupancy
        if not self._active(occupancy):
            return target
        target["kind"] = "TABLE"
        self._context(target, occupancy)
        session = task.requesting_guest_session
        assignment = self.assignments.get(task.requested_tab_id)
        if (
            task.requested_tab_id and task.requested_tab.venue_id == self.venue_id
            and task.requested_tab.state in ("OPEN", "REQUIRES_ACTION")
            and session and session.revoked_at is None and session.expires_at > timezone.now()
            and session.tab_id == task.requested_tab_id
            and session.table_id == occupancy.table_id
            and session.occupancy_id == occupancy.id and session.generation == occupancy.generation
            and assignment and assignment.occupancy_id == occupancy.id
        ):
            target.update(kind="TAB", tab_id=str(task.requested_tab_id))
        return target

    def _active(self, occupancy):
        return bool(
            occupancy and occupancy.released_at is None
            and occupancy.table.venue_id == self.venue_id
            and occupancy.table.status == TableStatus.OCCUPIED
            and occupancy.generation == occupancy.table.access_generation
        )

    def zone_id(self, task):
        target = self.target(task)
        if target["table_id"] is None:
            return None
        assignment = self.assignments.get(task.order_item.order.tab_id) if task.order_item_id else None
        occupancy = assignment.occupancy if assignment else task.destination_occupancy
        return str(occupancy.table.zone_id) if occupancy.table.zone_id else None

    @staticmethod
    def _context(target, occupancy):
        target.update(
            table_id=str(occupancy.table_id), occupancy_id=str(occupancy.id),
            generation=occupancy.generation,
        )
