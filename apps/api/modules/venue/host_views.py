"""Public host identity only; never authenticates an operator."""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .hostnames import resolved_venue_id
from .models import Venue


class VenueHostContextView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        venue_id = resolved_venue_id.get()
        if venue_id is None:
            return Response({"mode": "compatibility"}, headers={"Cache-Control": "no-store"})
        venue = Venue.objects.only("id", "name", "slug").get(pk=venue_id)
        return Response(
            {"mode": "establishment", "venue": {
                "id": str(venue.pk), "slug": venue.slug, "name": venue.name,
            }},
            headers={"Cache-Control": "no-store", "Vary": "Host"},
        )
