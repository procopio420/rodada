"""Read-only, venue-scoped tab location projections for operational displays.

Never changes the financial identity of a Tab. Current location is derived from
active assignments rather than a mutable customer-supplied display_label.
"""

from modules.hospitality.models import TabOccupancyAssignment


def tab_location_labels(tab_ids, *, include_history=False):
    """Return (current, last_known) labels indexed by string Tab UUID.

    The caller must already scope tab_ids to the authorized venue. This helper
    intentionally does not expose customer identities or alter placement.
    """
    identifiers = list(tab_ids)
    if not identifiers:
        return {}, {}
    assignments = TabOccupancyAssignment.objects.filter(
        tab_id__in=identifiers,
    ).select_related("occupancy__table")
    if not include_history:
        assignments = assignments.filter(
            released_at__isnull=True, occupancy__released_at__isnull=True,
        )
    current = {}
    historical = {}
    for assignment in assignments.order_by("-assigned_at", "-id"):
        tab_id = str(assignment.tab_id)
        location = f"Mesa {assignment.occupancy.table.label}"
        if include_history:
            historical.setdefault(tab_id, location)
        if assignment.released_at is None and assignment.occupancy.released_at is None:
            current.setdefault(tab_id, location)
    return current, historical
