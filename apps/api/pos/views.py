from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from catalog.models import Product
from cash.models import CashShift
from ledger.models import Payment
from pos.models import CustomerSession, Order, OrderItem, PhysicalTable, ServicePoint, StaffMember, StaffSession, Tab, TableAccessToken, Venue, Zone
from pos.serializers import OrderItemSerializer, OrderSerializer, ProductSerializer, TabSerializer
from pos.services import close_tab, confirm_order, create_adjustment, exposure_cents, record_payment, transition_order_item
from customers.models import Customer
from customers.services import initial_limit
from django.utils import timezone


def actor_for(request, venue):
    actor = request_actor(request)
    try:
        return StaffMember.objects.get(pk=actor.pk, venue=venue, active=True)
    except StaffMember.DoesNotExist as exc:
        raise PermissionDenied("Staff member does not belong to this venue.") from exc


def request_actor(request):
    authorization = request.headers.get("Authorization", "")
    session_token = request.headers.get("X-Staff-Session")
    if authorization.startswith("Bearer "):
        session_token = authorization.removeprefix("Bearer ").strip()
    if session_token:
        session = StaffSession.objects.select_related("staff_member__venue").filter(
            token=session_token, revoked_at__isnull=True, staff_member__active=True
        ).first()
        if session and (session.expires_at is None or session.expires_at > timezone.now()):
            return session.staff_member
        raise PermissionDenied("Staff session is invalid or expired.")
    staff_id = request.headers.get("X-Staff-ID") or request.data.get("staff_id")
    if not staff_id:
        raise PermissionDenied("An active staff identity is required.")
    try:
        return StaffMember.objects.select_related("venue").get(pk=staff_id, active=True)
    except StaffMember.DoesNotExist as exc:
        raise PermissionDenied("An active staff identity is required.") from exc


def staff_data(staff):
    return {"id": staff.id, "venue_id": staff.venue_id, "display_name": staff.display_name, "role": staff.role}


def command(fn):
    def inner(request, *args, **kwargs):
        try:
            return fn(request, *args, **kwargs)
        except PermissionDenied as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ObjectDoesNotExist:
            return Response({"detail": "Resource not found."}, status=status.HTTP_404_NOT_FOUND)
        except (ValidationError, ValueError, TypeError, KeyError, IntegrityError) as exc:
            detail = getattr(exc, "message", None) or (str(exc) if not isinstance(exc, KeyError) else f"Missing field: {exc.args[0]}")
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
    return inner


@api_view(["POST"])
@command
def login(request):
    venue = Venue.objects.get(pk=request.data["venue_id"])
    name = request.data.get("display_name", "").strip()
    pin = str(request.data.get("pin", ""))
    staff = StaffMember.objects.filter(venue=venue, display_name__iexact=name, active=True).first()
    if not staff or not staff.check_pin(pin):
        raise PermissionDenied("Invalid staff credentials.")
    session = StaffSession.objects.create(staff_member=staff)
    return Response({"session_token": session.token, "staff": staff_data(staff)}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@command
def session(request):
    return Response({"staff": staff_data(request_actor(request))})


@api_view(["GET"])
@command
def products(request):
    actor = request_actor(request)
    return Response(ProductSerializer(Product.objects.filter(venue=actor.venue, active=True), many=True).data)


@api_view(["GET"])
@command
def service_points(request):
    actor = request_actor(request)
    points = ServicePoint.objects.filter(venue=actor.venue, active=True).select_related("zone").order_by("code")
    return Response([{"id": point.id, "code": point.code, "zone": point.zone.name} for point in points])


@api_view(["GET", "POST"])
@command
def tabs(request):
    if request.method == "GET":
        actor = request_actor(request)
        rows = Tab.objects.filter(venue=actor.venue).exclude(status=Tab.Status.CLOSED).select_related("service_point", "customer").prefetch_related("orders__items__product", "payments", "adjustments")
        return Response(TabSerializer(rows, many=True).data)
    venue = Venue.objects.get(pk=request.data.get("venue_id", 1)); actor = actor_for(request, venue)
    point = ServicePoint.objects.filter(pk=request.data.get("service_point_id"), venue=venue).first() if request.data.get("service_point_id") else None
    customer = Customer.objects.get(pk=request.data["customer_id"], relationships__venue=venue) if request.data.get("customer_id") else None
    physical_table = None
    if request.data.get("physical_table_id"):
        physical_table = PhysicalTable.objects.get(pk=request.data["physical_table_id"], venue=venue, active=True)
    tab = Tab.objects.create(venue=venue, customer=customer, service_point=point, physical_table=physical_table, label=request.data.get("label", ""),
        operating_limit_cents=initial_limit(venue, customer), opened_by=actor)
    if physical_table and physical_table.status != PhysicalTable.Status.OCCUPIED:
        physical_table.status = PhysicalTable.Status.OCCUPIED; physical_table.save(update_fields=["status"])
    return Response(TabSerializer(tab).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@command
def tab_detail(request, tab_id):
    actor = request_actor(request)
    tab = Tab.objects.select_related("service_point", "customer").prefetch_related("orders__items__product", "payments", "adjustments").get(pk=tab_id, venue=actor.venue)
    return Response(TabSerializer(tab).data)


@api_view(["POST"])
@command
def move_tab(request, tab_id):
    tab = Tab.objects.select_related("venue").get(pk=tab_id); actor_for(request, tab.venue)
    point_id = request.data.get("service_point_id")
    tab.service_point = ServicePoint.objects.get(pk=point_id, venue=tab.venue) if point_id else None
    tab.save(update_fields=["service_point"])
    return Response(TabSerializer(tab).data)


@api_view(["GET", "POST"])
@command
def physical_tables(request):
    actor = request_actor(request) if request.method == "GET" else None
    if request.method == "GET":
        rows = PhysicalTable.objects.filter(venue=actor.venue, active=True).select_related("zone", "service_point")
        return Response([table_data(row) for row in rows])
    venue = Venue.objects.get(pk=request.data.get("venue_id", 1)); actor = actor_for(request, venue)
    if not actor.can_manage_finance: raise PermissionDenied("Only managers can create tables.")
    zone = Zone.objects.get(pk=request.data["zone_id"], venue=venue) if request.data.get("zone_id") else None
    table = PhysicalTable.objects.create(venue=venue, zone=zone, label=request.data["label"].strip(), is_temporary=bool(request.data.get("is_temporary")), x=int(request.data.get("x", 50)), y=int(request.data.get("y", 50)))
    TableAccessToken.objects.create(table=table)
    return Response(table_data(table, include_qr=True), status=201)


def table_data(table, include_qr=False):
    data = {"id": table.id, "label": table.label, "public_id": table.public_id, "zone": table.zone.name if table.zone else None,
            "zone_id": table.zone_id, "temporary": table.is_temporary, "status": table.status, "x": table.x, "y": table.y,
            "cleaning_started_at": table.cleaning_started_at, "cleaned_at": table.cleaned_at}
    if include_qr:
        token = table.access_tokens.filter(enabled=True).order_by("-id").first()
        data["qr_token"] = token.token if token else None
    return data


@api_view(["POST"])
@command
def configure_physical_table(request, table_id):
    table = PhysicalTable.objects.select_related("venue").get(pk=table_id); actor = actor_for(request, table.venue)
    if not actor.can_manage_finance: raise PermissionDenied("Only managers can configure tables.")
    changed = []
    if "zone_id" in request.data:
        table.zone = Zone.objects.get(pk=request.data["zone_id"], venue=table.venue) if request.data["zone_id"] else None; changed.append("zone")
    for name in ("x", "y"):
        if name in request.data: setattr(table, name, max(0, min(100, int(request.data[name])))); changed.append(name)
    if "label" in request.data: table.label = request.data["label"].strip(); changed.append("label")
    if changed: table.save(update_fields=changed)
    return Response(table_data(table))


@api_view(["POST"])
@command
def table_lifecycle(request, table_id):
    table = PhysicalTable.objects.select_related("venue").get(pk=table_id); actor_for(request, table.venue)
    target = request.data["status"]
    if target not in PhysicalTable.Status.values: raise ValidationError("Invalid table status.")
    if target == PhysicalTable.Status.NEEDS_CLEANING:
        table.cleaning_started_at = timezone.now()
    elif target == PhysicalTable.Status.AVAILABLE:
        table.cleaned_at = timezone.now()
    table.status = target
    table.save(update_fields=["status", "cleaning_started_at", "cleaned_at"])
    from dispatch.services import publish_venue_event
    publish_venue_event(table.venue_id, "tables.lifecycle_changed", {"table_id": table.id, "status": target})
    return Response(table_data(table))


@api_view(["POST"])
@command
def create_order(request, tab_id):
    with transaction.atomic():
        tab = Tab.objects.select_for_update().select_related("venue").get(pk=tab_id); actor = actor_for(request, tab.venue)
        if tab.status != Tab.Status.OPEN: raise ValidationError("Orders can only be added to an open tab.")
        idempotency_key = request.data.get("idempotency_key")
        if idempotency_key:
            existing = Order.objects.filter(tab=tab, idempotency_key=idempotency_key).first()
            if existing: return Response(OrderSerializer(existing).data)
        rows = request.data.get("items", [])
        if not isinstance(rows, list) or not rows: raise ValidationError("Order needs items.")
        prepared = []
        for row in rows:
            quantity = int(row["quantity"])
            if quantity <= 0: raise ValidationError("Item quantity must be positive.")
            product = Product.objects.get(pk=row["product_id"], venue=tab.venue, active=True)
            prepared.append((product, quantity))
        order = Order.objects.create(tab=tab, created_by=actor, idempotency_key=idempotency_key or None)
        OrderItem.objects.bulk_create([OrderItem(order=order, product=product, quantity=quantity) for product, quantity in prepared])
    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@command
def confirm(request, order_id):
    order = Order.objects.select_related("tab__venue").get(pk=order_id); order = confirm_order(order_id, actor_for(request, order.tab.venue)); return Response(OrderSerializer(order).data)


@api_view(["POST"])
@command
def transition(request, item_id):
    item = OrderItem.objects.select_related("order__tab__venue").get(pk=item_id)
    item = transition_order_item(item_id, request.data["state"], actor_for(request, item.order.tab.venue), request.data.get("reason", "")); return Response(OrderItemSerializer(item).data)


@api_view(["POST"])
@command
def payment(request, tab_id):
    tab = Tab.objects.select_related("venue").get(pk=tab_id); actor = actor_for(request, tab.venue)
    value = record_payment(tab_id, actor, amount_cents=int(request.data["amount_cents"]), method=request.data["method"], idempotency_key=request.data.get("idempotency_key"), status=Payment.Status.CONFIRMED)
    return Response({"id": value.id, "exposure_cents": exposure_cents(tab)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@command
def adjustment(request, tab_id):
    tab = Tab.objects.select_related("venue").get(pk=tab_id); result = create_adjustment(tab_id, actor_for(request, tab.venue), amount_cents=int(request.data["amount_cents"]), kind=request.data["type"], reason=request.data.get("reason", "")); return Response({"id": result.id}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@command
def close(request, tab_id):
    tab = Tab.objects.select_related("venue").get(pk=tab_id); tab = close_tab(tab_id, actor_for(request, tab.venue), force=bool(request.data.get("force")), reason=request.data.get("reason", "")); return Response(TabSerializer(tab).data)


@api_view(["GET", "POST"])
@command
def shifts(request):
    if request.method == "POST":
        venue = Venue.objects.get(pk=request.data.get("venue_id", 1)); actor = actor_for(request, venue)
        if not actor.can_operate_cash: raise PermissionDenied("Only a cashier or manager can open a cash shift.")
        opening_float_cents = int(request.data.get("opening_float_cents", 0))
        if opening_float_cents < 0: raise ValidationError("Opening float cannot be negative.")
        shift = CashShift.objects.create(venue=venue, opened_by=actor, opening_float_cents=opening_float_cents); return Response({"id": shift.id}, status=201)
    actor = request_actor(request)
    data = []
    for shift in CashShift.objects.filter(venue=actor.venue).order_by("-opened_at"):
        totals = dict(shift.payments.filter(status=Payment.Status.CONFIRMED).values_list("method").annotate(total=Sum("amount_cents")))
        data.append({"id": shift.id, "opened_at": shift.opened_at, "closed_at": shift.closed_at, "opening_float_cents": shift.opening_float_cents, "payments_by_method": totals, "adjustments_cents": shift.adjustments.aggregate(total=Sum("amount_cents"))["total"] or 0})
    return Response(data)


@api_view(["POST"])
@command
def close_shift(request, shift_id):
    with transaction.atomic():
        shift = CashShift.objects.select_for_update().select_related("venue").get(pk=shift_id)
        actor = actor_for(request, shift.venue)
        if not actor.can_operate_cash: raise PermissionDenied("Only a cashier or manager can close a cash shift.")
        if shift.closed_at is None:
            shift.closed_by = actor; shift.closed_at = timezone.now(); shift.closing_note = request.data.get("closing_note", ""); shift.save(update_fields=["closed_by", "closed_at", "closing_note"])
        return Response({"id": shift.id, "closed_at": shift.closed_at})
