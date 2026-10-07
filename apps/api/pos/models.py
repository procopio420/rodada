from django.db import models
from django.contrib.auth.hashers import check_password, make_password
import secrets


def opaque_token():
    return secrets.token_urlsafe(32)


def public_table_id():
    return secrets.token_urlsafe(18)


class Venue(models.Model):
    name = models.CharField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.name


class StaffMember(models.Model):
    class Role(models.TextChoices):
        STAFF = "STAFF", "Staff"
        CASHIER = "CASHIER", "Cashier"
        MANAGER = "MANAGER", "Manager"
        OWNER = "OWNER", "Owner"
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="staff")
    display_name = models.CharField(max_length=120)
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.STAFF)
    active = models.BooleanField(default=True)
    # Stored hashed; an empty value means this legacy staff record cannot sign in
    # until an operator sets a PIN.
    pin_hash = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def can_manage_finance(self): return self.role in {self.Role.MANAGER, self.Role.OWNER}

    @property
    def can_operate_cash(self): return self.role in {self.Role.CASHIER, self.Role.MANAGER, self.Role.OWNER}

    def set_pin(self, raw_pin):
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin):
        return bool(self.pin_hash) and check_password(raw_pin, self.pin_hash)


class StaffSession(models.Model):
    """Opaque local staff session, kept separate from financial records."""
    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name="sessions")
    token = models.CharField(max_length=64, unique=True, default=opaque_token)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)


class Zone(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="zones")
    name = models.CharField(max_length=80)
    active = models.BooleanField(default=True)
    class Meta: constraints = [models.UniqueConstraint(fields=["venue", "name"], name="unique_zone_name_per_venue")]


class ServicePoint(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="service_points")
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT, related_name="service_points")
    code = models.CharField(max_length=40)
    active = models.BooleanField(default=True)
    class Meta: constraints = [models.UniqueConstraint(fields=["venue", "code"], name="unique_service_point_per_venue")]


class PhysicalTable(models.Model):
    """Mutable physical context; it never owns a Tab, Order, or payment."""
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        OCCUPIED = "OCCUPIED", "Occupied"
        NEEDS_CLEANING = "NEEDS_CLEANING", "Needs cleaning"

    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="physical_tables")
    zone = models.ForeignKey(Zone, null=True, blank=True, on_delete=models.SET_NULL, related_name="physical_tables")
    service_point = models.OneToOneField(ServicePoint, null=True, blank=True, on_delete=models.SET_NULL, related_name="physical_table")
    label = models.CharField(max_length=80)
    public_id = models.CharField(max_length=32, unique=True, default=public_table_id)
    is_temporary = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.AVAILABLE)
    x = models.PositiveSmallIntegerField(default=50)
    y = models.PositiveSmallIntegerField(default=50)
    cleaning_started_at = models.DateTimeField(null=True, blank=True)
    cleaned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["venue", "label"], name="unique_table_label_per_venue")]
        ordering = ["zone__name", "label"]


class TableAccessToken(models.Model):
    """Opaque QR credential. The secret is intentionally unrelated to a table id."""
    table = models.ForeignKey(PhysicalTable, on_delete=models.CASCADE, related_name="access_tokens")
    token = models.CharField(max_length=64, unique=True, default=opaque_token)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)


class Tab(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        REQUIRES_ACTION = "REQUIRES_ACTION", "Requires action"
        SETTLING = "SETTLING", "Settling"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="tabs")
    customer = models.ForeignKey("customers.Customer", null=True, blank=True, on_delete=models.PROTECT, related_name="tabs")
    service_point = models.ForeignKey(ServicePoint, null=True, blank=True, on_delete=models.SET_NULL, related_name="tabs")
    physical_table = models.ForeignKey(PhysicalTable, null=True, blank=True, on_delete=models.SET_NULL, related_name="tabs")
    label = models.CharField(max_length=120, blank=True)
    public_token = models.CharField(max_length=64, unique=True, default=opaque_token)
    operating_limit_cents = models.PositiveIntegerField(default=3000)
    limit_overridden_by = models.ForeignKey(StaffMember, null=True, blank=True, on_delete=models.SET_NULL, related_name="limit_overrides")
    limit_overridden_at = models.DateTimeField(null=True, blank=True)
    limit_override_reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    opened_by = models.ForeignKey(StaffMember, null=True, on_delete=models.SET_NULL, related_name="opened_tabs")
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)


class CustomerSession(models.Model):
    """Public customer capability scoped to a venue/table and optionally one Tab."""
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="customer_sessions")
    table = models.ForeignKey(PhysicalTable, on_delete=models.PROTECT, related_name="customer_sessions")
    tab = models.ForeignKey(Tab, null=True, blank=True, on_delete=models.SET_NULL, related_name="customer_sessions")
    token = models.CharField(max_length=64, unique=True, default=opaque_token)
    guest_name = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)


class Order(models.Model):
    class Status(models.TextChoices): DRAFT = "DRAFT", "Draft"; CONFIRMED = "CONFIRMED", "Confirmed"
    tab = models.ForeignKey(Tab, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(StaffMember, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=100, null=True, blank=True)
    class Meta: constraints = [models.UniqueConstraint(fields=["tab", "idempotency_key"], condition=models.Q(idempotency_key__isnull=False), name="unique_order_command_per_tab")]


class OrderItem(models.Model):
    class State(models.TextChoices):
        NEW = "NEW", "New"; ACCEPTED = "ACCEPTED", "Accepted"; PREPARING = "PREPARING", "Preparing"; READY = "READY", "Ready"; PICKED_UP = "PICKED_UP", "Picked up"; DELIVERED = "DELIVERED", "Delivered"; CANCELLED = "CANCELLED", "Cancelled"
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price_cents = models.PositiveIntegerField(null=True, blank=True)
    fulfillment_station = models.CharField(max_length=16, blank=True)
    state = models.CharField(max_length=16, choices=State.choices, default=State.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    class Meta: constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0), name="item_quantity_positive")]
