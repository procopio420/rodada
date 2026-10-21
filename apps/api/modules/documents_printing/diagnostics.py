"""Manager-authorized synthetic test document using the existing fenced queue."""

import hashlib
import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from modules.access.context import ActorContext

from .models import AgentPrinterRoute, PrinterEndpoint, ReceiptDocument
from .renderers import canonical_json
from .services import request_job


@transaction.atomic
def request_test(session, endpoint_id, key):
    endpoint = get_object_or_404(
        PrinterEndpoint, pk=endpoint_id, venue_id=session.venue_id, adapter="AGENT", enabled=True
    )
    if not AgentPrinterRoute.objects.filter(endpoint=endpoint, enabled=True).exists():
        raise ValidationError("Configure uma rota habilitada antes do teste.")
    source = uuid.uuid5(uuid.NAMESPACE_URL, f"printing-test:{session.venue_id}:{endpoint.id}:{key}")
    now = timezone.now()
    snapshot = {
        "venue": session.venue.name, "tab_label": "TESTE — NÃO PREPARAR",
        "generated_at": now.isoformat(), "business_date": now.date().isoformat(),
        "items": [{"quantity": 1, "name": "Açúcar, pão, limão, café — NÃO É PEDIDO",
                   "customization": {"special_instructions": "Conferir acentos, largura e corte."},
                   "unit_price_cents": 0, "total_cents": 0}],
    }
    document, _ = ReceiptDocument.objects.get_or_create(
        venue_id=session.venue_id, kind="DIAGNOSTIC_TEST", source_id=source,
        station="", source_version="diagnostic-v1",
        defaults={"snapshot": snapshot,
                  "snapshot_hash": hashlib.sha256(canonical_json(snapshot).encode()).hexdigest(),
                  "created_by_id": session.staff_member_id},
    )
    return request_job(document=document, endpoint=endpoint, key="diagnostic:" + str(key),
                       actor=ActorContext.from_session(session))
