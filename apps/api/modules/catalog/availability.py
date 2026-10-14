"""Versioned, session-bound availability commands; legacy clients remain separate."""
import hashlib
import json

from django.db import transaction

from modules.access.capabilities import Capability, has_capability
from modules.access.models import StaffSession
from modules.audit.services import record_audit_event
from modules.catalog.models import AvailabilityCommand, ProductAvailability


class AvailabilityError(Exception):
    def __init__(self, code, message, status):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)


@transaction.atomic
def execute_availability(*, actor, product_id, state, expected_version, idempotency_key, reason=""):
    session = StaffSession.objects.select_for_update(of=("self",), no_key=True).select_related(
        "membership", "staff_member", "device",
    ).filter(pk=actor.session_id, venue_id=actor.venue_id, staff_member_id=actor.staff_id).first()
    if session is None or not session.is_valid:
        raise AvailabilityError("SESSION_INVALID", "Sessão original indisponível.", 403)
    if not has_capability(session.membership, Capability.CATALOG_AVAILABILITY_MANAGE_STATION):
        raise AvailabilityError("CAPABILITY_REQUIRED", "Sem autorização para disponibilidade.", 403)
    payload = {"product_id": str(product_id), "state": state, "expected_version": expected_version, "reason": reason}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    previous = AvailabilityCommand.objects.filter(venue_id=actor.venue_id, session=session, idempotency_key=idempotency_key).first()
    if previous:
        if previous.request_fingerprint != fingerprint:
            raise AvailabilityError("IDEMPOTENCY_CONFLICT", "Chave já usada para outra alteração.", 409)
        return previous.receipt
    availability = ProductAvailability.objects.select_for_update(of=("self",)).filter(product_id=product_id, product__venue_id=actor.venue_id).first()
    if availability is None:
        raise AvailabilityError("PRODUCT_NOT_FOUND", "Produto não encontrado.", 404)
    before, version = availability.state, availability.version
    rejected = version != expected_version
    changed = not rejected and before != state
    command = AvailabilityCommand.objects.create(venue_id=actor.venue_id, session=session,
        actor_id=actor.staff_id, idempotency_key=idempotency_key, request_fingerprint=fingerprint)
    if changed:
        availability.state, availability.version, availability.changed_by_id = state, version + 1, actor.staff_id
        availability.save(update_fields=["state", "version", "changed_by", "changed_at"])
        record_audit_event(actor=actor, event_type="product.availability_changed", entity_type="Product", entity_id=str(product_id),
            metadata={"before": before, "after": state, "before_version": version, "after_version": availability.version,
                      "command_id": str(command.pk), "reason": reason})
    receipt = {"command_id": str(command.pk), "idempotency_key": idempotency_key, "product_id": str(product_id),
        "requested_state": state, "expected_version": expected_version, "state": availability.state, "version": availability.version,
        "status": "REJECTED" if rejected else "APPLIED", "changed": changed, "conflicts": ["VERSION_CONFLICT"] if rejected else []}
    command.receipt = receipt
    command.save(update_fields=["receipt"])
    record_audit_event(actor=actor, event_type="product.availability_command.completed", entity_type="AvailabilityCommand",
        entity_id=str(command.pk), metadata={**receipt, "reason": reason})
    return receipt
