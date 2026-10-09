from django.db import transaction
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.audit.services import record_audit_event
from modules.house_account.services import authorize
from modules.ledger import pricing
from modules.ledger.models import Charge, PricingApproval, PricingPolicy


class Command(serializers.Serializer):
    kind = serializers.ChoiceField(
        choices=[
            "ITEM_DISCOUNT",
            "TAB_DISCOUNT",
            "COURTESY",
            "SERVICE_CHARGE",
            "SERVICE_CHARGE_REDUCTION",
            "REVERSAL",
        ]
    )
    expected_version = serializers.IntegerField(min_value=0)
    idempotency_key = serializers.CharField(max_length=120)
    charge_id = serializers.UUIDField(required=False)
    adjustment_id = serializers.UUIDField(required=False)
    calculation_type = serializers.ChoiceField(choices=["FIXED", "PERCENTAGE"], default="FIXED")
    value = serializers.IntegerField(min_value=0, max_value=2147483647, required=False)
    reason_code = serializers.CharField(max_length=80, default="", allow_blank=True)
    reason_text = serializers.CharField(max_length=240, default="", allow_blank=True)

    def validate_idempotency_key(self, value):
        if value.startswith("refresh:"):
            raise serializers.ValidationError("Prefixo reservado.")
        return value

    def validate(self, data):
        if data["kind"] not in ("REVERSAL", "SERVICE_CHARGE") and "value" not in data:
            raise serializers.ValidationError("Informe o valor.")
        if (
            data["kind"] in ("SERVICE_CHARGE", "SERVICE_CHARGE_REDUCTION", "REVERSAL")
            and "charge_id" in data
        ):
            raise serializers.ValidationError("Ação não aceita item.")
        return data


class PricingView(APIView):
    permission_classes = [IsAuthenticated]
    action = "apply"

    def get(self, request, tab_id):
        with transaction.atomic():
            try:
                tab = pricing.locked_tab(tab_id, request.actor_context)
                history = [
                    {
                        "id": str(a.id),
                        "kind": a.kind,
                        "amount_cents": a.amount_cents,
                        "basis_cents": a.basis_cents,
                        "requested_value": a.requested_value,
                        "reason_code": a.reason_code,
                        "created_by": str(a.created_by_id),
                        "approved_by": str(a.approved_by_id) if a.approved_by_id else None,
                        "created_at": a.created_at,
                        "reverses_id": str(a.reverses_id) if a.reverses_id else None,
                        "allocations": list(
                            a.allocations.values("charge_id", "basis_cents", "amount_cents")
                        ),
                    }
                    for a in tab.ledger_adjustments.order_by("created_at", "id")
                ]
                values_by_charge = pricing.components(tab)
                names = {
                    str(charge.id): charge.order_item.product_name_snapshot
                    if charge.order_item else "Consumo"
                    for charge in Charge.objects.filter(pk__in=values_by_charge)
                    .select_related("order_item")
                }
                return Response(
                    {
                        **pricing.commercial_summary(tab),
                        "version": tab.version,
                        "policy": pricing.policy_data(pricing.get_policy(tab.venue_id)),
                        "history": history,
                        "charges": [
                            {"charge_id": key, "product_name": names[key], **values}
                            for key, values in values_by_charge.items()
                        ],
                    }
                )
            except pricing.PricingError as error:
                return Response(
                    {"code": error.code, "message": error.message}, status=error.status_code
                )

    def post(self, request, tab_id):
        serializer = Command(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = getattr(pricing, self.action)(
                tab_id=tab_id, data=serializer.validated_data, actor=request.actor_context
            )
        except pricing.PricingError as error:
            return Response(
                {"code": error.code, "message": error.message}, status=error.status_code
            )
        return Response(result)


class PricingPreviewView(PricingView):
    action = "preview"


class PricingRequestApprovalView(PricingView):
    action = "request_approval"


class PricingApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        authorize(request.actor_context, Capability.DISCOUNT_OVERRIDE)
        rows = PricingApproval.objects.filter(
            tab__venue_id=request.actor_context.venue_id, adjustment__isnull=True
        ).select_related("tab", "requested_by__staff_member")
        return Response(
            {
                "results": [
                    {
                        "id": str(a.id),
                        "tab_id": str(a.tab_id),
                        "label": a.tab.display_label,
                        "requester": a.requested_by.staff_member.display_name,
                        "command": a.command,
                        "preview": a.preview,
                    }
                    for a in rows.order_by("created_at")[:200]
                ]
            }
        )

    def post(self, request, approval_id):
        try:
            return Response(pricing.approve(approval_id=approval_id, actor=request.actor_context))
        except pricing.PricingError as error:
            return Response(
                {"code": error.code, "message": error.message}, status=error.status_code
            )


class RefundItemPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, tab_id, charge_id):
        authorize(request.actor_context, Capability.REFUND_CREATE)
        try:
            with transaction.atomic():
                tab = pricing.locked_tab(tab_id, request.actor_context)
                return Response(pricing.refund_preview(tab, charge_id))
        except pricing.PricingError as error:
            return Response(
                {"code": error.code, "message": error.message}, status=error.status_code
            )


class PolicyInput(serializers.Serializer):
    expected_version = serializers.IntegerField(min_value=1)
    service_enabled = serializers.BooleanField()
    service_basis_points = serializers.IntegerField(min_value=0, max_value=10000)
    service_max_basis_points = serializers.IntegerField(min_value=0, max_value=10000)
    service_opt_out = serializers.BooleanField()
    service_removal_requires_manager = serializers.BooleanField(default=True)
    service_treatment = serializers.ChoiceField(choices=["REVENUE", "PASS_THROUGH"])
    service_refundable = serializers.BooleanField()
    staff_discount_basis_points = serializers.IntegerField(min_value=0, max_value=10000)
    cashier_discount_basis_points = serializers.IntegerField(min_value=0, max_value=10000)
    maximum_discount_basis_points = serializers.IntegerField(min_value=0, max_value=10000)
    allow_post_payment = serializers.BooleanField()

    def validate(self, data):
        if data["service_basis_points"] > data["service_max_basis_points"]:
            raise serializers.ValidationError("Taxa excede o máximo.")
        if (
            max(data["staff_discount_basis_points"], data["cashier_discount_basis_points"])
            > data["maximum_discount_basis_points"]
        ):
            raise serializers.ValidationError("Limite do operador excede o máximo.")
        return data


class PricingPolicyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        authorize(request.actor_context, Capability.VENUE_CONFIGURE)
        return Response(pricing.policy_data(pricing.get_policy(request.actor_context.venue_id)))

    @transaction.atomic
    def put(self, request):
        authorize(request.actor_context, Capability.VENUE_CONFIGURE, privileged=True)
        data = PolicyInput(data=request.data)
        data.is_valid(raise_exception=True)
        pricing.get_policy(request.actor_context.venue_id)
        policy = PricingPolicy.objects.select_for_update().get(
            venue_id=request.actor_context.venue_id
        )
        values = dict(data.validated_data)
        if values.pop("expected_version") != policy.version:
            return Response(
                {"code": "VERSION_CONFLICT", "message": "Política mudou. Atualize."}, status=409
            )
        before = pricing.policy_data(policy)
        for key, value in values.items():
            setattr(policy, key, value)
        policy.version += 1
        policy.save()
        record_audit_event(
            actor=request.actor_context,
            event_type="pricing.policy_changed",
            entity_type="Venue",
            entity_id=str(policy.venue_id),
            metadata={"before": before, "after": pricing.policy_data(policy)},
        )
        return Response(pricing.policy_data(policy))
