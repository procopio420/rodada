from django.urls import path

from dispatch.consumers import DispatchConsumer

websocket_urlpatterns = [
    path("ws/venues/<int:venue_id>/dispatch/", DispatchConsumer.as_asgi()),
]
