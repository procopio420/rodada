from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ledger.models import Payment, PaymentIntent
from ledger.services import confirm_test_intent, create_intent
from pos.models import Tab
from pos.views import actor_for, command


@api_view(["POST"])
@command
def payment_intents(request, tab_id):
    tab = Tab.objects.select_related("venue").get(pk=tab_id)
    actor = actor_for(request, tab.venue)
    result = create_intent(tab, int(request.data["amount_cents"]), request.data.get("method", Payment.Method.CARD), request.data["idempotency_key"], actor)
    return Response({"id": result.id, "provider": result.provider, "provider_reference": result.provider_reference, "status": result.status, "test_mode": result.provider == "TEST"}, status=201)


@api_view(["POST"])
@command
def test_confirm(request, intent_id):
    intent = PaymentIntent.objects.select_related("tab__venue").get(pk=intent_id)
    actor = actor_for(request, intent.tab.venue)
    result = confirm_test_intent(intent, actor)
    return Response({"id": result.id, "status": result.status, "payment_id": result.payment_id})
