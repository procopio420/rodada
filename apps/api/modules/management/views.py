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
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
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
            changed = before != data.validated_data
            if changed:
                # Historical reports currently derive dates from the Venue policy.
                # A quiet live service alone cannot protect that history: until
                # effective-dated policy exists, reject edits once facts exist.
                blockers = []
                if Charge.objects.filter(tab__venue=venue).exists(): blockers.append('CHARGE_HISTORY')
                if Payment.objects.filter(tab__venue=venue).exists(): blockers.append('PAYMENT_HISTORY')
                if CashShift.objects.filter(venue=venue).exists(): blockers.append('CASH_SHIFT_HISTORY')
                if blockers:
                    return Response({'code': 'HISTORICAL_POLICY_CHANGE_BLOCKED',
                        'message': 'O calendário possui histórico. Alteração exige política versionada.',
                        'blockers': blockers, 'current': before}, status=409)
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
        from modules.ledger.pricing import category
        commercial = {"item_discounts_cents": 0, "tab_discounts_cents": 0, "courtesy_cents": 0,
                      "service_assessed_cents": 0, "service_reductions_cents": 0,
                      "corrections_cents": 0, "service_revenue_cents": 0, "service_pass_through_cents": 0}
        category_rows = []
        for fact in adjustments.select_related("reverses"):
            kind = fact.reverses.kind if fact.kind == "REVERSAL" else fact.kind
            field = {"ITEM_DISCOUNT": "item_discounts_cents", "TAB_DISCOUNT": "tab_discounts_cents",
                     "COURTESY": "courtesy_cents", "COURTESY_REPLACEMENT": "courtesy_cents",
                     "SERVICE_CHARGE": "service_assessed_cents", "SERVICE_CHARGE_REDUCTION": "service_reductions_cents"}.get(kind, "corrections_cents")
            sign = -1 if field in ("item_discounts_cents", "tab_discounts_cents", "courtesy_cents", "service_reductions_cents") else 1
            commercial[field] += sign * fact.amount_cents
            category_rows.append((fact.created_at, field, sign * fact.amount_cents))
            if category(fact) == "service":
                splits = fact.policy_snapshot.get("service_allocations")
                if splits is not None:
                    for treatment_key, report_key in [("service_revenue", "service_revenue_cents"), ("service_pass_through", "service_pass_through_cents")]:
                        amount = sum(split.get(treatment_key, 0) for split in splits.values())
                        commercial[report_key] += amount
                        category_rows.append((fact.created_at, report_key, amount))
                else:
                    treatment = (fact.reverses.policy_snapshot if fact.kind == "REVERSAL" else fact.policy_snapshot).get("service_treatment", "PASS_THROUGH")
                    treatment_field = "service_revenue_cents" if treatment == "REVENUE" else "service_pass_through_cents"
                    commercial[treatment_field] += fact.amount_cents
                    category_rows.append((fact.created_at, treatment_field, fact.amount_cents))
        service = commercial["service_assessed_cents"] - commercial["service_reductions_cents"]
        days = {}
        for day_offset in range((end - start).days + 1):
            key = str(start + timedelta(days=day_offset))
            days[key] = {**dict.fromkeys(commercial, 0), "date": key, "gross_cents": 0, "adjustments_cents": 0, "paid_cents": 0, "refunds_cents": 0}
        for rows, timestamp, field in [(charges, "created_at", "gross_cents"), (adjustments, "created_at", "adjustments_cents"), (payments, "confirmed_at", "paid_cents"), (refunds, "confirmed_at", "refunds_cents")]:
            for instant, amount in rows.values_list(timestamp, "amount_cents").iterator():
                days[str(business_date(venue, instant))][field] += amount
        for instant, field, amount in category_rows:
            days[str(business_date(venue, instant))][field] += amount
        for row in days.values():
            row["net_consumption_cents"] = row["gross_cents"] + row["adjustments_cents"] - row["service_assessed_cents"] + row["service_reductions_cents"]
            row["net_sales_cents"] = row["net_consumption_cents"] + row["service_revenue_cents"]
            row["payable_cents"] = row["gross_cents"] + row["adjustments_cents"]
            row["net_received_cents"] = row["paid_cents"] - row["refunds_cents"]
        products = list(charges.values("order_item__product_id", "order_item__product_name_snapshot").annotate(quantity=Sum("order_item__quantity"), gross_cents=Sum("amount_cents")).order_by("-gross_cents", "order_item__product_name_snapshot"))
        orders = Order.objects.filter(tab__venue=venue, confirmed_at__gte=lower, confirmed_at__lt=upper)
        open_tabs = Tab.objects.filter(venue=venue).exclude(state__in=["CLOSED", "CANCELLED"])
        from modules.ledger.services import totals
        exposure = sum(max(0, totals(tab)["exposure_cents"]) for tab in open_tabs)
        return Response({"generated_at": timezone.now(), "timezone": venue.timezone,
            "cutoff_hour": venue.business_day_cutoff_hour, "start": start, "end": end,
            "totals": {**commercial, "gross_cents": gross, "adjustments_cents": adjustment,
                "net_consumption_cents": gross + adjustment - service, "payable_cents": gross + adjustment,
                "net_sales_cents": gross + adjustment - commercial["service_pass_through_cents"],
                "paid_cents": paid, "refunds_cents": refunded, "net_received_cents": paid - refunded,
                "current_open_exposure_cents": exposure, "current_open_tabs": open_tabs.count()},
            "daily": list(days.values()), "products": products,
            "payment_methods": list(payments.values("method").annotate(amount_cents=Sum("amount_cents"), count=Count("id")).order_by("method")),
            "orders": list(orders.values("source", "status").annotate(count=Count("id")).order_by("source", "status")),
            "cash_shifts": [{**_shift_payload(shift), "cash_point_label": shift.cash_point.label} for shift in CashShift.objects.filter(venue=venue, business_date__range=(start, end)).select_related("cash_point").order_by("business_date", "opened_at")]})


class AlertPolicyView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.VENUE_CONFIGURE

    @staticmethod
    def snapshot(policy):
        return {**{name: getattr(policy, name) for name in ('version', 'fulfillment_warning_seconds', 'fulfillment_danger_seconds', 'payment_pending_seconds')}, 'strategic_product_ids': [str(value) for value in policy.strategic_products.values_list('id', flat=True)]}

    def get(self, request):
        from modules.venue.models import OperationalAlertPolicy
        policy, _ = OperationalAlertPolicy.objects.get_or_create(venue=request.auth.venue)
        return Response({'section': 'operational_alerts', **self.snapshot(policy)})

    def patch(self, request):
        RequireRecentReauthentication().has_permission(request, self)
        from modules.venue.models import OperationalAlertPolicy
        from modules.management.alerts import evaluate_alerts
        class Input(serializers.Serializer):
            expected_version = serializers.IntegerField(min_value=1)
            fulfillment_warning_seconds = serializers.IntegerField(min_value=1, max_value=86400)
            fulfillment_danger_seconds = serializers.IntegerField(min_value=2, max_value=172800)
            payment_pending_seconds = serializers.IntegerField(min_value=1, max_value=86400)
            strategic_product_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
            reason = serializers.CharField(max_length=240, required=False, default='')
            def validate(self, data):
                if data['fulfillment_warning_seconds'] >= data['fulfillment_danger_seconds']:
                    raise serializers.ValidationError('O SLA crítico deve ser maior que o SLA de atenção.')
                if set(self.initial_data) - set(self.fields):
                    raise serializers.ValidationError('Configuração desconhecida.')
                return data
        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            venue = Venue.objects.select_for_update().get(pk=request.auth.venue_id)
            policy, _ = OperationalAlertPolicy.objects.get_or_create(venue=venue)
            if policy.version != data.validated_data['expected_version']:
                return Response({'code': 'STALE_VERSION', 'current': self.snapshot(policy)}, status=409)
            before = self.snapshot(policy)
            for name in ('fulfillment_warning_seconds', 'fulfillment_danger_seconds', 'payment_pending_seconds'):
                setattr(policy, name, data.validated_data[name])
            if 'strategic_product_ids' in data.validated_data:
                from modules.catalog.models import Product
                selected = set(data.validated_data['strategic_product_ids'])
                products = Product.objects.filter(venue=venue, id__in=selected)
                if products.count() != len(selected):
                    return Response({'code':'INVALID_STRATEGIC_PRODUCT', 'message':'Produto fora deste estabelecimento.'}, status=400)
                policy.strategic_products.set(products)
            policy.version += 1
            policy.save()
            applied_at = timezone.now()
            record_audit_event(actor=request.actor_context, event_type='operational_threshold.changed',
                entity_type='OperationalAlertPolicy', entity_id=str(venue.pk), reason=data.validated_data['reason'],
                metadata={'before': before, 'after': self.snapshot(policy), 'applied_at': applied_at.isoformat(), 'change_mode': 'IMMEDIATE_SAFE'})
            from modules.realtime.services import emit_event
            emit_event(venue_id=venue.id, event_type='venue.configuration_changed', aggregate_type='OperationalAlertPolicy', aggregate_id=venue.id, payload={'section':'operational_alerts', 'version':policy.version})
            evaluate_alerts(venue, applied_at)
        return Response({'section': 'operational_alerts', **self.snapshot(policy), 'effective_at': applied_at, 'change_mode': 'IMMEDIATE_SAFE'})


class AlertListView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.MANAGEMENT_REPORTS_READ

    def get(self, request):
        from modules.management.alerts import evaluate_alerts, payload
        from django.db.models import Case, When, Value, IntegerField
        alerts = evaluate_alerts(request.auth.venue).order_by(Case(When(severity='DANGER', then=Value(0)), default=Value(1), output_field=IntegerField()), 'first_detected_at')
        return Response({'results': [payload(alert) for alert in alerts], 'evaluated_at': timezone.now()})


class AlertDetailView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.MANAGEMENT_REPORTS_READ

    def get(self, request, alert_id):
        from django.shortcuts import get_object_or_404
        from modules.venue.models import OperationalAlert
        from modules.management.alerts import evaluate_alerts, payload
        evaluate_alerts(request.auth.venue)
        alert = get_object_or_404(OperationalAlert, venue=request.auth.venue, pk=alert_id)
        return Response({**payload(alert), 'history': list(alert.history.values('kind', 'occurred_at', 'metadata'))})

    def post(self, request, alert_id):
        from django.shortcuts import get_object_or_404
        from modules.access.capabilities import has_capability
        from modules.venue.models import OperationalAlert
        from modules.management.alerts import evaluate_alerts, payload, _event
        if not has_capability(request.auth.membership, Capability.VENUE_CONFIGURE):
            return Response({'code': 'CAPABILITY_REQUIRED'}, status=403)
        with transaction.atomic():
            venue = Venue.objects.select_for_update().get(pk=request.auth.venue_id)
            evaluate_alerts(venue)
            alert = get_object_or_404(OperationalAlert.objects.select_for_update(), venue=venue, pk=alert_id)
            if alert.status == 'RESOLVED':
                return Response({'code': 'ALERT_RESOLVED', 'current': payload(alert)}, status=409)
            if alert.status == 'ACTIVE':
                now = timezone.now()
                alert.status, alert.acknowledged_at, alert.updated_at = 'ACKNOWLEDGED', now, now
                alert.acknowledged_by_id = request.actor_context.staff_id
                alert.save(update_fields=['status', 'acknowledged_at', 'updated_at', 'acknowledged_by'])
                _event(alert, 'ACKNOWLEDGED', now, actor_id=str(request.actor_context.staff_id))
                record_audit_event(actor=request.actor_context, event_type='alert.acknowledged',
                    entity_type='OperationalAlert', entity_id=str(alert.pk))
        return Response(payload(alert))
