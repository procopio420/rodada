from django.db.models import Q
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from customers.models import Customer, Relationship
from customers.services import override_limit
from pos.models import Tab, Venue
from pos.serializers import TabSerializer
from pos.views import actor_for, command


def customer_data(customer, venue=None):
    relationship = customer.relationships.filter(venue=venue).first() if venue else customer.relationships.first()
    return {"id": customer.id, "display_name": customer.display_name, "phone": customer.phone, "notes": customer.notes,
        "relationship": relationship.status if relationship else None, "nickname": relationship.nickname if relationship else ""}


@api_view(["GET", "POST"])
@command
def customers(request):
    venue = Venue.objects.get(pk=request.data.get("venue_id", 1) if request.method == "POST" else request.query_params.get("venue_id", 1))
    actor_for(request, venue)
    if request.method == "POST":
        display_name = request.data["display_name"].strip()
        if not display_name: raise ValidationError("Display name is required.")
        customer = Customer.objects.create(display_name=display_name, phone=request.data.get("phone", ""), notes=request.data.get("notes", ""))
        Relationship.objects.create(customer=customer, venue=venue, status=request.data.get("relationship", Relationship.Status.VISITOR), nickname=request.data.get("nickname", ""))
        return Response(customer_data(customer, venue), status=status.HTTP_201_CREATED)
    query = request.query_params.get("q", "").strip()
    rows = Customer.objects.filter(relationships__venue=venue)
    if query:
        rows = rows.filter(Q(display_name__icontains=query) | Q(phone__icontains=query) | Q(relationships__nickname__icontains=query))
    return Response([customer_data(row, venue) for row in rows.distinct()[:30]])


@api_view(["GET"])
@command
def customer_history(request, customer_id):
    customer = Customer.objects.get(pk=customer_id)
    venue = Venue.objects.get(pk=request.query_params.get("venue_id", 1)); actor_for(request, venue)
    tabs = Tab.objects.filter(venue=venue, customer=customer).order_by("-opened_at")
    return Response({**customer_data(customer, venue), "tabs": TabSerializer(tabs, many=True).data})


@api_view(["POST"])
@command
def limit_override(request, tab_id):
    tab = Tab.objects.select_related("venue").get(pk=tab_id)
    return Response(TabSerializer(override_limit(tab_id, actor_for(request, tab.venue), int(request.data["operating_limit_cents"]), request.data.get("reason", ""))).data)
