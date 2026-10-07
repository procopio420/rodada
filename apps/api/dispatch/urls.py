from django.urls import path
from dispatch import views

urlpatterns = [
    path("dispatch/tasks/", views.tasks), path("dispatch/tasks/<int:task_id>/claim/", views.claim), path("dispatch/tasks/<int:task_id>/done/", views.done),
    path("dispatch/events/", views.events), path("dispatch/runs/", views.runs), path("zones/", views.zones), path("zones/<int:zone_id>/configure/", views.configure_zone),
    path("service-points/create/", views.create_point), path("service-points/<int:point_id>/configure/", views.configure_point),
]
