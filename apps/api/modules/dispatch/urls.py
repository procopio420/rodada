from django.urls import path

from modules.dispatch.views import DeliveryCompleteView, DeliveryQueueView, ServiceRequestQueueView, ServiceRequestClaimView, ServiceRequestCompleteView


urlpatterns = [
    path("requests/", ServiceRequestQueueView.as_view()),
    path("requests/<uuid:task_id>/claim/", ServiceRequestClaimView.as_view()),
    path("requests/<uuid:task_id>/complete/", ServiceRequestCompleteView.as_view()),
    path("delivery/", DeliveryQueueView.as_view(), name="dispatch-delivery-queue"),
    path(
        "delivery/<uuid:task_id>/complete/",
        DeliveryCompleteView.as_view(),
        name="dispatch-delivery-complete",
    ),
]
