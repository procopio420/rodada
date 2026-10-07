from django.urls import include, path

urlpatterns = [
    path("api/", include("pos.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("ledger.urls")),
    path("api/", include("customers.urls")),
    path("api/", include("dispatch.urls")),
]
