from django.db import connection
from django.http import JsonResponse
from django.urls import path

from modules.ordering.views import OrderConfirmView, TabDetailView, TabListCreateView

from modules.access.views import (
    AccessAuditListView,
    AccessInvalidationFeedView,
    CurrentStaffView,
    DeviceDetailView,
    DeviceListView,
    SessionListView,
    SessionRevokeView,
    StaffMembershipDetailView,
    StaffMembershipListView,
    StaffLockView,
    StaffLoginView,
    StaffLogoutView,
    StaffReauthenticateView,
    StaffRefreshView,
    StaffSwitchOperatorView,
)


def health(request):
    return JsonResponse({"status": "ok"})


def readiness(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status": "ready"})


urlpatterns = [
    path("health/", health, name="health"),
    path("ready/", readiness, name="readiness"),
    path("auth/login/", StaffLoginView.as_view(), name="staff-login"),
    path("auth/refresh/", StaffRefreshView.as_view(), name="staff-refresh"),
    path("auth/me/", CurrentStaffView.as_view(), name="staff-me"),
    path("auth/lock/", StaffLockView.as_view(), name="staff-lock"),
    path("auth/logout/", StaffLogoutView.as_view(), name="staff-logout"),
    path("auth/switch-operator/", StaffSwitchOperatorView.as_view(), name="staff-switch-operator"),
    path("auth/reauthenticate/", StaffReauthenticateView.as_view(), name="staff-reauthenticate"),
    path("auth/invalidation-events/", AccessInvalidationFeedView.as_view(), name="access-invalidation-events"),
    path("manage/access/memberships/", StaffMembershipListView.as_view(), name="access-memberships"),
    path("manage/access/memberships/<uuid:membership_id>/", StaffMembershipDetailView.as_view(), name="access-membership-detail"),
    path("manage/access/devices/", DeviceListView.as_view(), name="access-devices"),
    path("manage/access/devices/<uuid:device_id>/", DeviceDetailView.as_view(), name="access-device-detail"),
    path("manage/access/sessions/", SessionListView.as_view(), name="access-sessions"),
    path("manage/access/sessions/<uuid:session_id>/revoke/", SessionRevokeView.as_view(), name="access-session-revoke"),
    path("manage/access/audit/", AccessAuditListView.as_view(), name="access-audit"),
    path("tabs/", TabListCreateView.as_view(), name="tab-list-create"),
    path("tabs/<uuid:tab_id>/", TabDetailView.as_view(), name="tab-detail"),
    path("tabs/<uuid:tab_id>/orders/confirm/", OrderConfirmView.as_view(), name="order-confirm"),
]
