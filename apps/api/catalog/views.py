from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from catalog.models import CanonicalItem, Product
from catalog.services import canonical_matches, create_canonical_item, set_product_availability
from audit.models import AuditEvent
from pos.views import actor_for, command, request_actor


def canonical_data(item):
    return {"id": item.id, "name": item.name, "description": item.description, "icon_key": item.icon_key, "icon_status": item.icon_status}


@api_view(["GET", "POST"])
@command
def canonical_items(request):
    if request.method == "GET":
        return Response([canonical_data(item) for item in canonical_matches(request.query_params.get("q", ""))])
    actor = request_actor(request)
    item, created = create_canonical_item(request.data["name"], request.data.get("description", ""))
    return Response(canonical_data(item), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(["POST"])
@command
def create_product(request):
    actor = request_actor(request)
    if not actor.can_manage_finance:
        raise PermissionDenied("Only managers can create menu items.")
    canonical_id = request.data.get("canonical_item_id")
    if canonical_id:
        canonical = CanonicalItem.objects.get(pk=canonical_id)
    else:
        canonical, _ = create_canonical_item(request.data["name"], request.data.get("description", ""))
    product = Product.objects.create(
        venue=actor.venue, canonical_item=canonical, name=request.data.get("name", canonical.name).strip(),
        description=request.data.get("description", canonical.description), current_price_cents=int(request.data["current_price_cents"]),
        fulfillment_station=request.data.get("fulfillment_station", Product.Station.BAR),
    )
    return Response({"id": product.id, "name": product.name, "canonical_item": canonical_data(canonical)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@command
def availability(request, product_id):
    actor = request_actor(request)
    product = Product.objects.get(pk=product_id, venue=actor.venue)
    if not actor.can_manage_finance:
        raise PermissionDenied("Only managers can change availability.")
    previous = product.available
    product = set_product_availability(product, bool(request.data["available"]))
    AuditEvent.objects.create(venue=product.venue, actor=actor, action="product.availability_changed",
        entity_type=product._meta.label, entity_id=product.id,
        before={"available": previous}, after={"available": product.available})
    return Response({"id": product.id, "available": product.available})
