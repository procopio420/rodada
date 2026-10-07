from django.urls import path
from catalog import views

urlpatterns = [
    path("catalog/canonical-items/", views.canonical_items),
    path("catalog/products/", views.create_product),
    path("products/<int:product_id>/availability/", views.availability),
]
