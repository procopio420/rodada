from modules.access.context import ActorContext
from modules.audit.models import AuditEvent


def record_audit_event(
    *,
    actor: ActorContext,
    event_type: str,
    entity_type: str = "",
    entity_id: str = "",
    reason: str = "",
    metadata: dict | None = None,
) -> AuditEvent:
    return AuditEvent.objects.create(
        **actor.audit_kwargs(),
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        reason=reason,
        metadata=metadata or {},
    )
