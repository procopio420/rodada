from django.urls import path
from pos import views
from pos import public_views

urlpatterns = [
    path("auth/login/", views.login), path("auth/session/", views.session),
    path("products/", views.products), path("service-points/", views.service_points), path("tabs/", views.tabs), path("tabs/<int:tab_id>/", views.tab_detail), path("tabs/<int:tab_id>/service-point/", views.move_tab),
    path("tabs/<int:tab_id>/orders/", views.create_order), path("orders/<int:order_id>/confirm/", views.confirm), path("order-items/<int:item_id>/transition/", views.transition),
    path("tabs/<int:tab_id>/payments/", views.payment), path("tabs/<int:tab_id>/adjustments/", views.adjustment), path("tabs/<int:tab_id>/close/", views.close),
    path("cash-shifts/", views.shifts), path("cash-shifts/<int:shift_id>/close/", views.close_shift),
    path("physical-tables/", views.physical_tables), path("physical-tables/<int:table_id>/configure/", views.configure_physical_table), path("physical-tables/<int:table_id>/lifecycle/", views.table_lifecycle),
    path("public/qr/<str:qr_token>/", public_views.qr_entry), path("public/qr/<str:qr_token>/sessions/", public_views.create_session),
    path("public/sessions/<str:session_token>/", public_views.customer_session), path("public/sessions/<str:session_token>/orders/", public_views.customer_order), path("public/sessions/<str:session_token>/payment-intents/", public_views.customer_payment_intent),
]
