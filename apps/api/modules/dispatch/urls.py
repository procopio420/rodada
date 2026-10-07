from django.urls import path

from modules.dispatch.views import DeliveryCompleteView, DeliveryQueueView


urlpatterns = [
    path("delivery/", DeliveryQueueView.as_view(), name="dispatch-delivery-queue"),
    path(
        "delivery/<uuid:task_id>/complete/",
        DeliveryCompleteView.as_view(),
        name="dispatch-delivery-complete",
    ),
]
