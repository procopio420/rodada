from django.urls import path
from ledger import views

urlpatterns = [
    path("tabs/<int:tab_id>/payment-intents/", views.payment_intents),
    path("payment-intents/<int:intent_id>/test-confirm/", views.test_confirm),
]
