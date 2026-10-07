from django.db import connection
from django.http import JsonResponse
from django.urls import path

from modules.access.views import (
    CurrentStaffView,
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
]
