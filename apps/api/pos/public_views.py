from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from catalog.models import Product
from ledger.models import Payment
from ledger.services import create_intent
from pos.models import CustomerSession, Order, OrderItem, PhysicalTable, StaffMember, Tab, TableAccessToken
from pos.serializers import ProductSerializer, TabSerializer
from pos.services import confirm_order


def public_command(fn):
    def inner(request, *args, **kwargs):
        try:
            return fn(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return Response({"detail": "QR access is invalid or unavailable."}, status=404)
        except (ValidationError, KeyError, ValueError, TypeError) as exc:
            return Response({"detail": getattr(exc, "message", None) or str(exc)}, status=400)
    return inner


def token_context(qr_token):
    access = TableAccessToken.objects.select_related("table__venue", "table__zone").get(token=qr_token, enabled=True, table__active=True)
    return access.table


def session_context(session_token):
    session = CustomerSession.objects.select_related("venue", "table", "tab").get(token=session_token, revoked_at__isnull=True)
    if session.expires_at and session.expires_at <= timezone.now():
        raise ValidationError("This customer session has expired.")
    return session


def public_tab(tab):
    return TabSerializer(Tab.objects.select_related("service_point", "customer").prefetch_related("orders__items__product", "payments", "adjustments").get(pk=tab.id)).data


@api_view(["GET"])
@public_command
def qr_entry(request, qr_token):
    table = token_context(qr_token)
    TableAccessToken.objects.filter(token=qr_token).update(last_used_at=timezone.now())
    products = Product.objects.filter(venue=table.venue, active=True)
    tab_options = Tab.objects.filter(venue=table.venue, physical_table=table, status__in=[Tab.Status.OPEN, Tab.Status.REQUIRES_ACTION]).order_by("-opened_at")
    return Response({"venue": table.venue.name, "table": {"label": table.label, "zone": table.zone.name if table.zone else None, "status": table.status},
                     "products": ProductSerializer(products, many=True).data,
                     "tabs": [{"token": tab.public_token, "label": tab.label or "Comanda aberta"} for tab in tab_options]})


@api_view(["POST"])
@public_command
@transaction.atomic
def create_session(request, qr_token):
    table = token_context(qr_token)
    tab_token = request.data.get("tab_token")
    if tab_token:
        tab = Tab.objects.select_for_update().get(public_token=tab_token, venue=table.venue, physical_table=table, status__in=[Tab.Status.OPEN, Tab.Status.REQUIRES_ACTION])
    else:
        staff, _ = StaffMember.objects.get_or_create(venue=table.venue, display_name="Cliente QR", defaults={"role": StaffMember.Role.STAFF})
        tab = Tab.objects.create(venue=table.venue, physical_table=table, label=request.data.get("guest_name", "").strip(), opened_by=staff)
    table.status = PhysicalTable.Status.OCCUPIED
    table.save(update_fields=["status"])
    session = CustomerSession.objects.create(venue=table.venue, table=table, tab=tab, guest_name=request.data.get("guest_name", "").strip())
    return Response({"session_token": session.token, "tab": public_tab(tab)}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@public_command
def customer_session(request, session_token):
    session = session_context(session_token)
    products = Product.objects.filter(venue=session.venue, active=True)
    return Response({"table": {"label": session.table.label, "status": session.table.status}, "products": ProductSerializer(products, many=True).data, "tab": public_tab(session.tab)})


@api_view(["POST"])
@public_command
@transaction.atomic
def customer_order(request, session_token):
    session = session_context(session_token)
    tab = Tab.objects.select_for_update().get(pk=session.tab_id, venue=session.venue)
    if tab.status != Tab.Status.OPEN: raise ValidationError("This comanda needs staff attention before another order.")
    items = request.data.get("items", [])
    if not items: raise ValidationError("Order needs items.")
    staff, _ = StaffMember.objects.get_or_create(venue=session.venue, display_name="Cliente QR", defaults={"role": StaffMember.Role.STAFF})
    order = Order.objects.create(tab=tab, created_by=staff, idempotency_key=request.data.get("idempotency_key"))
    for row in items:
        product = Product.objects.get(pk=row["product_id"], venue=session.venue, active=True, available=True)
        OrderItem.objects.create(order=order, product=product, quantity=int(row["quantity"]))
    confirm_order(order.id, staff)
    return Response({"tab": public_tab(tab)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@public_command
def customer_payment_intent(request, session_token):
    session = session_context(session_token)
    amount = int(request.data["amount_cents"])
    intent = create_intent(session.tab, amount, Payment.Method.CARD, request.data["idempotency_key"], initiated_by=None)
    return Response({"id": intent.id, "provider": intent.provider, "provider_reference": intent.provider_reference, "status": intent.status, "test_mode": intent.provider == "TEST"}, status=201)
