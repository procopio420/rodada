from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.audit.services import record_audit_event
from modules.catalog.models import AvailabilityState, ProductAvailability
from modules.catalog.queries import catalog_for_venue
from modules.catalog.models import normalize_product_name
from modules.catalog.services import ResolveProductInput, product_payload, resolve_or_create_product


class ProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = catalog_for_venue(venue_id=request.auth.venue_id, include_inactive=request.query_params.get("include_inactive") == "true").select_related("icon")
        query = normalize_product_name(request.query_params.get("q", ""))
        if query:
            products = products.filter(normalized_name__contains=query)
        return Response({"results": [product_payload(product) for product in products]})


class ProductResolveView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CATALOG_PRODUCT_CREATE

    def post(self, request):
        data = ResolveProductInput(data=request.data)
        data.is_valid(raise_exception=True)
        product, created = resolve_or_create_product(actor=request.actor_context, **data.validated_data)
        return Response({"product": product_payload(product), "created": created}, status=201 if created else 200)


class ProductAvailabilityView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CATALOG_AVAILABILITY_MANAGE_STATION

    def post(self, request, product_id):
        state = request.data.get("state")
        if state not in AvailabilityState.values:
            return Response({"code": "INVALID_AVAILABILITY", "message": "Disponibilidade inválida."}, status=400)
        availability = ProductAvailability.objects.select_related("product").filter(product_id=product_id, product__venue_id=request.actor_context.venue_id).first()
        if not availability:
            return Response({"code": "PRODUCT_NOT_FOUND", "message": "Produto não encontrado."}, status=404)
        before = availability.state
        availability.state, availability.version, availability.changed_by_id = state, availability.version + 1, request.actor_context.staff_id
        availability.save(update_fields=["state", "version", "changed_by", "changed_at"])
        record_audit_event(actor=request.actor_context, event_type="product.availability_changed", entity_type="Product", entity_id=str(product_id), metadata={"before": before, "after": state})
        return Response({"product_id": str(product_id), "state": state, "version": availability.version})
