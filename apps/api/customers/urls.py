from django.urls import path
from customers import views

urlpatterns = [
    path("customers/", views.customers),
    path("customers/<int:customer_id>/history/", views.customer_history),
    path("tabs/<int:tab_id>/limit-override/", views.limit_override),
]
