from collections.abc import Iterable

from modules.access.models import MembershipStatus, StaffRole, VenueStaffMembership


class Capability:
    TAB_OPEN = "tab.open"
    ORDER_CONFIRM = "order.confirm"
    ORDER_CORRECT = "order.correct"
    TABLE_MANAGE = "table.manage"
    CATALOG_AVAILABILITY_MANAGE_STATION = "catalog.availability.manage_station"
    PAYMENT_COLLECT = "payment.collect"
    REFUND_CREATE = "refund.create"
    CASH_SHIFT_OPEN = "cash.shift.open"
    CASH_ADJUSTMENT_CREATE = "cash.adjustment.create"
    CASH_REVIEW = "cash.review"
    TAB_REOPEN = "tab.reopen"
    DISCOUNT_OVERRIDE = "discount.override"
    STAFF_MANAGE = "staff.manage"
    VENUE_CONFIGURE = "venue.configure"
    CUSTOMER_MANAGE = "customer.manage"
    LIMIT_OVERRIDE = "tab.limit.override"
    CATALOG_PRODUCT_CREATE = "catalog.product.create"
    MANAGEMENT_REPORTS_READ = "management.reports.read"


ALL_CAPABILITIES = frozenset(
    value
    for key, value in Capability.__dict__.items()
    if key.isupper() and isinstance(value, str)
)

_STAFF = {
    Capability.TAB_OPEN,
    Capability.ORDER_CONFIRM,
    Capability.ORDER_CORRECT,
    Capability.TABLE_MANAGE,
    Capability.CATALOG_AVAILABILITY_MANAGE_STATION,
}
_CASHIER = _STAFF | {
    Capability.PAYMENT_COLLECT,
    Capability.CASH_SHIFT_OPEN,
    Capability.CASH_ADJUSTMENT_CREATE,
}
_MANAGER = _CASHIER | {
    Capability.CATALOG_PRODUCT_CREATE,
    Capability.MANAGEMENT_REPORTS_READ,
    Capability.CUSTOMER_MANAGE,
    Capability.LIMIT_OVERRIDE,
    Capability.REFUND_CREATE,
    Capability.CASH_ADJUSTMENT_CREATE,
    Capability.TAB_REOPEN,
    Capability.DISCOUNT_OVERRIDE,
    Capability.CASH_REVIEW,
    Capability.VENUE_CONFIGURE,
}

ROLE_CAPABILITIES: dict[str, frozenset[str]] = {
    StaffRole.STAFF: frozenset(_STAFF),
    StaffRole.CASHIER: frozenset(_CASHIER),
    StaffRole.MANAGER: frozenset(_MANAGER),
    StaffRole.OWNER: ALL_CAPABILITIES,
}


def _known(values: Iterable[str]) -> set[str]:
    return {value for value in values if value in ALL_CAPABILITIES}


def effective_capabilities(membership: VenueStaffMembership) -> frozenset[str]:
    if membership.status != MembershipStatus.ACTIVE or not membership.staff_member.is_active:
        return frozenset()

    capabilities = set(ROLE_CAPABILITIES.get(membership.role, frozenset()))
    overrides = membership.capability_overrides or {}
    capabilities.update(_known(overrides.get("allow", ())))
    capabilities.difference_update(_known(overrides.get("deny", ())))
    return frozenset(capabilities)


def has_capability(membership: VenueStaffMembership, capability: str) -> bool:
    return capability in effective_capabilities(membership)
