from modules.catalog.models import Product


def catalog_for_venue(*, venue_id, include_inactive: bool = False):
    products = Product.objects.filter(venue_id=venue_id).select_related("availability")
    if not include_inactive:
        products = products.filter(active=True)
    return products.order_by("fulfillment_station", "name", "id")
