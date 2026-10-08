from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.audit.services import record_audit_event
from modules.catalog.models import AvailabilityState, ProductAvailability
from modules.catalog.queries import catalog_for_venue


class ProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"results": [{"id": str(product.id), "name": product.name, "price_cents": product.price_cents, "active": product.active, "fulfillment_station": product.fulfillment_station, "availability": product.availability.state} for product in catalog_for_venue(venue_id=request.auth.venue_id)]})


class ProductAvailabilityView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CATALOG_AVAILABILITY_MANAGE_STATION

    @transaction.atomic
    def post(self, request, product_id):
        state = request.data.get("state")
        if state not in AvailabilityState.values:
            return Response({"code": "INVALID_AVAILABILITY", "message": "Disponibilidade inválida."}, status=400)
        availability = ProductAvailability.objects.select_for_update().select_related("product").filter(product_id=product_id, product__venue_id=request.actor_context.venue_id).first()
        if not availability:
            return Response({"code": "PRODUCT_NOT_FOUND", "message": "Produto não encontrado."}, status=404)
        before = availability.state
        availability.state, availability.version, availability.changed_by_id = state, availability.version + 1, request.actor_context.staff_id
        availability.save(update_fields=["state", "version", "changed_by", "changed_at"])
        record_audit_event(actor=request.actor_context, event_type="product.availability_changed", entity_type="Product", entity_id=str(product_id), metadata={"before": before, "after": state})
        return Response({"product_id": str(product_id), "state": state, "version": availability.version})
