"""Public establishment identity; middleware has already authenticated host provenance."""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class VenueHostView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        venue = request._request.host_venue
        if venue is None:
            return Response({'mode': 'compatibility'})
        return Response({'mode': 'establishment', 'venue': {
            'id': str(venue.pk), 'slug': venue.slug, 'name': venue.name}},
            headers={'Cache-Control': 'no-store'})
