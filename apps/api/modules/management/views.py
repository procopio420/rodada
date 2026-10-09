from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.audit.services import record_audit_event
from modules.venue.models import Venue
from modules.venue.calendar import business_date, business_boundary
from modules.ledger.models import Charge, LedgerAdjustment, Payment, PaymentStatus, Refund, RefundStatus
from modules.ordering.models import Order, Tab
from modules.cash.models import CashShift
from modules.cash.views import _shift_payload


class CalendarView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.MANAGEMENT_REPORTS_READ

    def get(self, request):
        venue = request.auth.venue
        return Response({"timezone": venue.timezone, "cutoff_hour": venue.business_day_cutoff_hour,
                         "business_date": business_date(venue)})

    def patch(self, request):
        # Reading reports never grants configuration authority.
        from modules.access.capabilities import has_capability
        if not has_capability(request.auth.membership, Capability.VENUE_CONFIGURE):
            return Response({"code": "CAPABILITY_REQUIRED", "message": "Configuração não autorizada."}, status=403)
        class Input(serializers.Serializer):
            timezone = serializers.CharField(max_length=64)
            cutoff_hour = serializers.IntegerField(min_value=0, max_value=23)
            def validate_timezone(self, value):
                try: ZoneInfo(value)
                except (ZoneInfoNotFoundError, ValueError): raise serializers.ValidationError("Timezone inválido.")
                return value
        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            venue = Venue.objects.select_for_update().get(pk=request.actor_context.venue_id)
            before = {"timezone": venue.timezone, "cutoff_hour": venue.business_day_cutoff_hour}
            venue.timezone = data.validated_data["timezone"]
            venue.business_day_cutoff_hour = data.validated_data["cutoff_hour"]
            venue.save(update_fields=["timezone", "business_day_cutoff_hour"])
            record_audit_event(actor=request.actor_context, event_type="business_date_policy.changed",
                entity_type="Venue", entity_id=str(venue.id), metadata={"before": before, "after": data.validated_data})
        return Response({**data.validated_data, "business_date": business_date(venue)})


class ReportView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.MANAGEMENT_REPORTS_READ

    def get(self, request):
        class Query(serializers.Serializer):
            start = serializers.DateField()
            end = serializers.DateField()
            def validate(self, data):
                if not 0 <= (data["end"] - data["start"]).days <= 365:
                    raise serializers.ValidationError("Escolha até 366 dias, em ordem cronológica.")
                return data
        data = Query(data=request.query_params)
        data.is_valid(raise_exception=True)
        start, end = data.validated_data["start"], data.validated_data["end"]
        venue = request.auth.venue
        lower, upper = business_boundary(venue, start), business_boundary(venue, end + timedelta(days=1))
        charges = Charge.objects.filter(tab__venue=venue, created_at__gte=lower, created_at__lt=upper)
        adjustments = LedgerAdjustment.objects.filter(tab__venue=venue, created_at__gte=lower, created_at__lt=upper)
        payments = Payment.objects.filter(tab__venue=venue, status__in=PaymentStatus.confirmed_money_values(), confirmed_at__gte=lower, confirmed_at__lt=upper)
        refunds = Refund.objects.filter(payment__tab__venue=venue, status=RefundStatus.CONFIRMED, confirmed_at__gte=lower, confirmed_at__lt=upper)
        total = lambda rows: rows.aggregate(value=Sum("amount_cents"))["value"] or 0
        gross, adjustment, paid, refunded = map(total, (charges, adjustments, payments, refunds))
        days = {}
        for day_offset in range((end - start).days + 1):
            key = str(start + timedelta(days=day_offset))
            days[key] = {"date": key, "gross_cents": 0, "adjustments_cents": 0, "paid_cents": 0, "refunds_cents": 0}
        for rows, timestamp, field in [(charges, "created_at", "gross_cents"), (adjustments, "created_at", "adjustments_cents"), (payments, "confirmed_at", "paid_cents"), (refunds, "confirmed_at", "refunds_cents")]:
            for instant, amount in rows.values_list(timestamp, "amount_cents").iterator():
                days[str(business_date(venue, instant))][field] += amount
        for row in days.values():
            row["net_sales_cents"] = row["gross_cents"] + row["adjustments_cents"]
            row["net_received_cents"] = row["paid_cents"] - row["refunds_cents"]
        products = list(charges.values("order_item__product_id", "order_item__product_name_snapshot").annotate(quantity=Sum("order_item__quantity"), gross_cents=Sum("amount_cents")).order_by("-gross_cents", "order_item__product_name_snapshot"))
        orders = Order.objects.filter(tab__venue=venue, confirmed_at__gte=lower, confirmed_at__lt=upper)
        open_tabs = Tab.objects.filter(venue=venue).exclude(state__in=["CLOSED", "CANCELLED"])
        # A credit on one Tab must not hide another Tab's outstanding exposure.
        balances = dict.fromkeys(open_tabs.values_list("id", flat=True), 0)
        for rows, key, sign in [
            (Charge.objects.filter(tab__in=open_tabs), "tab_id", 1),
            (LedgerAdjustment.objects.filter(tab__in=open_tabs), "tab_id", 1),
            (Payment.objects.filter(tab__in=open_tabs, status__in=PaymentStatus.confirmed_money_values()), "tab_id", -1),
            (Refund.objects.filter(payment__tab__in=open_tabs, status=RefundStatus.CONFIRMED), "payment__tab_id", 1),
        ]:
            for row in rows.values(key).annotate(amount=Sum("amount_cents")):
                balances[row[key]] = balances.get(row[key], 0) + sign * row["amount"]
        exposure = sum(max(0, balance) for balance in balances.values())
        return Response({"generated_at": timezone.now(), "timezone": venue.timezone,
            "cutoff_hour": venue.business_day_cutoff_hour, "start": start, "end": end,
            "totals": {"gross_cents": gross, "adjustments_cents": adjustment, "net_sales_cents": gross + adjustment,
                "paid_cents": paid, "refunds_cents": refunded, "net_received_cents": paid - refunded,
                "current_open_exposure_cents": exposure, "current_open_tabs": open_tabs.count()},
            "daily": list(days.values()), "products": products,
            "payment_methods": list(payments.values("method").annotate(amount_cents=Sum("amount_cents"), count=Count("id")).order_by("method")),
            "orders": list(orders.values("source", "status").annotate(count=Count("id")).order_by("source", "status")),
            "cash_shifts": [{**_shift_payload(shift), "cash_point_label": shift.cash_point.label} for shift in CashShift.objects.filter(venue=venue, business_date__range=(start, end)).select_related("cash_point").order_by("business_date", "opened_at")]})
