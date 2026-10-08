from django.urls import path

from .views import GuestSnapshotView, GuestStreamView, SnapshotView, StreamView

urlpatterns = [
    path("realtime/snapshot/", SnapshotView.as_view()),
    path("realtime/stream/", StreamView.as_view()),
    path("guest/realtime/snapshot/", GuestSnapshotView.as_view()),
    path("guest/realtime/stream/", GuestStreamView.as_view()),
]
