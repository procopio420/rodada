from django.db import connection
from django.http import JsonResponse
from django.urls import path


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
]
