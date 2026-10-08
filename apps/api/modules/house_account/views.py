from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
from modules.audit.models import AuditEvent
from modules.audit.services import record_audit_event
from modules.ordering.models import Tab
from modules.ordering.services import OrderingServiceError
from modules.ordering.views import _error_response, _tab_payload

from .models import Customer, Relationship, RelationshipKind
from .services import (
    approve_override,
    associate_customer,
    authorize,
    locked_tab,
    policy,
    reassess_tab,
)


class CustomerInput(serializers.Serializer):
    display_name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=40, allow_blank=True, required=False)
    notes = serializers.CharField(max_length=240, allow_blank=True, required=False)
    kind = serializers.ChoiceField(choices=RelationshipKind.choices, default="KNOWN")


class OverrideInput(serializers.Serializer):
    limit_cents = serializers.IntegerField(min_value=1, max_value=2147483647)
    reason = serializers.CharField(max_length=240)
    expires_at = serializers.DateTimeField()
    idempotency_key = serializers.CharField(max_length=120)


def customer_payload(relationship):
    customer = relationship.customer
    return {
        "id": str(customer.id),
        "display_name": customer.display_name,
        "phone": customer.phone,
        "notes": customer.notes,
        "kind": relationship.kind,
    }


class CustomerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = Relationship.objects.filter(venue=request.auth.venue).select_related("customer")
        query = request.query_params.get("q", "").strip()[:120]
        if query:
            rows = rows.filter(
                Q(customer__display_name__icontains=query) | Q(customer__phone__icontains=query)
            )
        return Response(
            {
                "results": [
                    customer_payload(r) for r in rows.order_by("customer__display_name")[:100]
                ]
            }
        )

    @transaction.atomic
    def post(self, request):
        authorize(request.actor_context, Capability.CUSTOMER_MANAGE)
        serializer = CustomerInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        kind = data.pop("kind")
        customer = Customer.objects.create(**data)
        row = Relationship.objects.create(venue=request.auth.venue, customer=customer, kind=kind)
        record_audit_event(
            actor=request.actor_context,
            event_type="customer.created",
            entity_type="Customer",
            entity_id=str(customer.id),
            metadata={"kind": kind},
        )
        return Response(customer_payload(row), status=201)


class CustomerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id):
        row = (
            Relationship.objects.filter(venue=request.auth.venue, customer_id=customer_id)
            .select_related("customer")
            .first()
        )
        if not row:
            return Response({"code": "CUSTOMER_NOT_FOUND"}, status=404)
        return Response(
            {
                **customer_payload(row),
                "tabs": [
                    _tab_payload(tab)
                    for tab in Tab.objects.filter(
                        venue=request.auth.venue, customer_id=customer_id
                    )[:100]
                ],
            }
        )

    @transaction.atomic
    def patch(self, request, customer_id):
        authorize(request.actor_context, Capability.CUSTOMER_MANAGE, privileged=True)
        row = (
            Relationship.objects.select_for_update()
            .filter(venue=request.auth.venue, customer_id=customer_id)
            .first()
        )
        if not row:
            return Response({"code": "CUSTOMER_NOT_FOUND"}, status=404)
        serializer = CustomerInput(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        before = customer_payload(row)
        for field, value in serializer.validated_data.items():
            if field == "kind":
                row.kind = value
            else:
                setattr(row.customer, field, value)
        row.customer.save()
        row.save()
        record_audit_event(
            actor=request.actor_context,
            event_type="relationship.updated",
            entity_type="Customer",
            entity_id=str(customer_id),
            metadata={"before": before, "after": customer_payload(row)},
        )
        return Response(customer_payload(row))


class PolicyView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CUSTOMER_MANAGE

    def get(self, request):
        return Response(
            {
                "results": [
                    {"kind": kind, "limit_cents": p.limit_cents, "version": p.version}
                    for kind in RelationshipKind.values
                    for p in [policy(request.auth.venue_id, kind)]
                ]
            }
        )

    @transaction.atomic
    def put(self, request):
        authorize(request.actor_context, Capability.VENUE_CONFIGURE, privileged=True)

        class Input(serializers.Serializer):
            kind = serializers.ChoiceField(choices=RelationshipKind.choices)
            limit_cents = serializers.IntegerField(min_value=0, max_value=2147483647)

        serializer = Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        value = policy(request.auth.venue_id, data["kind"])
        value = value.__class__.objects.select_for_update().get(pk=value.pk)
        before = value.limit_cents
        value.limit_cents = data["limit_cents"]
        value.version += 1
        value.save(update_fields=["limit_cents", "version"])
        record_audit_event(
            actor=request.actor_context,
            event_type="relationship_policy.updated",
            entity_type="VenueRelationshipPolicy",
            entity_id=str(value.pk),
            metadata={
                "kind": value.kind,
                "previous_limit_cents": before,
                "limit_cents": value.limit_cents,
                "version": value.version,
            },
        )
        return Response(
            {"kind": value.kind, "limit_cents": value.limit_cents, "version": value.version}
        )


class TabLimitOverrideView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability, RequireRecentReauthentication]
    required_capability = Capability.LIMIT_OVERRIDE

    def post(self, request, tab_id):
        serializer = OverrideInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tab = approve_override(
                tab_id=tab_id, actor=request.actor_context, **serializer.validated_data
            )
        except OrderingServiceError as error:
            return _error_response(error)
        return Response(_tab_payload(tab))


class TabCustomerView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.TAB_OPEN

    def post(self, request, tab_id):
        class Input(serializers.Serializer):
            customer_id = serializers.UUIDField()

        serializer = Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tab = associate_customer(
                tab_id=tab_id, actor=request.actor_context, **serializer.validated_data
            )
        except OrderingServiceError as error:
            return _error_response(error)
        return Response(_tab_payload(tab))


class TabReassessView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability, RequireRecentReauthentication]
    required_capability = Capability.LIMIT_OVERRIDE

    def post(self, request, tab_id):
        class Input(serializers.Serializer):
            reason = serializers.CharField(max_length=240)

        serializer = Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tab = reassess_tab(
                tab_id=tab_id, actor=request.actor_context, **serializer.validated_data
            )
        except OrderingServiceError as error:
            return _error_response(error)
        return Response(_tab_payload(tab))


class TabApprovalRequestView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.TAB_OPEN

    @transaction.atomic
    def post(self, request, tab_id):
        class Input(serializers.Serializer):
            reason = serializers.CharField(max_length=240)
            idempotency_key = serializers.CharField(max_length=120)

        serializer = Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tab = locked_tab(tab_id, request.actor_context)
        except OrderingServiceError as error:
            return _error_response(error)
        data = serializer.validated_data
        existing = AuditEvent.objects.filter(
            venue=request.auth.venue,
            entity_id=str(tab_id),
            event_type="tab.limit_approval_requested",
            metadata__idempotency_key=data["idempotency_key"],
        ).first()
        if existing and existing.reason != data["reason"]:
            return Response({"code": "IDEMPOTENCY_CONFLICT"}, status=409)
        if not existing:
            record_audit_event(
                actor=request.actor_context,
                event_type="tab.limit_approval_requested",
                entity_type="Tab",
                entity_id=str(tab.id),
                reason=data["reason"],
                metadata={"idempotency_key": data["idempotency_key"]},
            )
        return Response({"requested": True})


class TabHouseHistoryView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.LIMIT_OVERRIDE

    def get(self, request, tab_id):
        if not Tab.objects.filter(pk=tab_id, venue=request.auth.venue).exists():
            return Response({"code": "TAB_NOT_FOUND"}, status=404)
        rows = (
            AuditEvent.objects.filter(
                venue=request.auth.venue, entity_type="Tab", entity_id=str(tab_id)
            )
            .select_related("actor_staff")
            .order_by("-occurred_at")[:100]
        )
        return Response(
            {
                "results": [
                    {
                        "id": str(r.id),
                        "event_type": r.event_type,
                        "actor": str(r.actor_staff_id) if r.actor_staff_id else None,
                        "actor_name": r.actor_staff.display_name if r.actor_staff_id else "Sistema",
                        "reason": r.reason,
                        "occurred_at": r.occurred_at,
                        "metadata": r.metadata,
                    }
                    for r in rows
                ]
            }
        )
