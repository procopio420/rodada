from django.urls import path

from .kds_views import KdsDetectorView, KdsHealthView, KdsHeartbeatView

from .views import (
    BridgeClaimView,
    BridgeResultView,
    DocumentView,
    EndpointsView,
    JobsView,
    JobView,
    ReceiptTokenView,
)

urlpatterns = [
    path("kds/", KdsHealthView.as_view()),
    path("kds/<str:station>/heartbeat/", KdsHeartbeatView.as_view()),
    path("kds/<str:station>/detector/", KdsDetectorView.as_view()),
    path("documents/", DocumentView.as_view()),
    path("documents/<uuid:document_id>/", DocumentView.as_view()),
    path("documents/<uuid:document_id>/share/", ReceiptTokenView.as_view()),
    path("endpoints/", EndpointsView.as_view()),
    path("jobs/", JobsView.as_view()),
    path("jobs/<uuid:job_id>/", JobView.as_view()),
    path("bridge/claim/", BridgeClaimView.as_view()),
    path("bridge/jobs/<uuid:job_id>/result/", BridgeResultView.as_view()),
]

