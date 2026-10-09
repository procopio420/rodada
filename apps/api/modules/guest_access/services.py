import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from modules.audit.models import AuditEvent
from modules.hospitality.models import (
    GuestOrderingMode,
    Table,
    TableOccupancy,
    TableStatus,
    TabOccupancyAssignment,
)
from modules.ordering.models import OrderSource, Tab
from modules.ordering.services import OrderingServiceError, confirm_order

from .models import GuestSession


@dataclass(frozen=True)
class GuestAccessError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict | None = None


@dataclass(frozen=True)
class GuestResolution:
    session: GuestSession
    token: str
    created: bool


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _session_ttl() -> timedelta:
    return timedelta(seconds=getattr(settings, "RODADA_GUEST_SESSION_TTL_SECONDS", 8 * 60 * 60))


def _record_guest_audit(
    *, session: GuestSession, event_type: str, entity_type: str, entity_id: str, metadata=None
):
    """Audit guest facts without allowing a guest token to impersonate staff."""
    return AuditEvent.objects.create(
        venue_id=session.table.venue_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata={"guest_session_id": str(session.id), **(metadata or {})},
    )


def _active_occupancy(table: Table) -> TableOccupancy | None:
    return TableOccupancy.objects.filter(table=table, released_at__isnull=True).first()


def _assert_table_accepts_guests(table: Table):
    if table.guest_ordering_blocked:
        raise GuestAccessError(
            "GUEST_ORDERING_BLOCKED", "Pedidos pelo QR estão bloqueados nesta mesa.", 403
        )
    if table.guest_ordering_mode == GuestOrderingMode.DISABLED:
        raise GuestAccessError(
            "GUEST_ORDERING_DISABLED", "Pedidos pelo QR não estão disponíveis nesta mesa.", 403
        )


@transaction.atomic
def resolve_table_qr(*, public_token: str, existing_session_token: str = "") -> GuestResolution:
    """Resolve only physical context; it never treats a QR as a Tab credential."""
    table = Table.objects.select_for_update().filter(public_token=public_token).first()
    if table is None:
        raise GuestAccessError("QR_NOT_FOUND", "QR inválido ou expirado.", 404)
    _assert_table_accepts_guests(table)
    occupancy = _active_occupancy(table)
    if occupancy is None:
        if table.guest_ordering_mode != GuestOrderingMode.DIRECT:
            raise GuestAccessError(
                "ACTIVE_OCCUPANCY_REQUIRED",
                "Esta mesa precisa estar ocupada antes de aceitar pedidos pelo QR.",
                409,
            )
        if table.status != TableStatus.AVAILABLE:
            raise GuestAccessError("TABLE_NOT_AVAILABLE", "Mesa não está disponível.", 409)

    if existing_session_token:
        session = (
            GuestSession.objects.select_for_update()
            # `occupancy` is nullable. PostgreSQL rejects FOR UPDATE on the
            # nullable side of the outer join introduced by select_related.
            # The session itself is the row we must serialize here; load an
            # optional occupancy lazily when it is actually needed.
            .select_related("table")
            .filter(token_digest=_token_digest(existing_session_token))
            .first()
        )
        if (
            session
            and session.table_id == table.id
            and session.revoked_at is None
            and session.expires_at > timezone.now()
            and session.generation == table.access_generation
            and session.occupancy_id == (occupancy.id if occupancy else None)
        ):
            session.last_seen_at = timezone.now()
            session.save(update_fields=["last_seen_at"])
            return GuestResolution(session=session, token=existing_session_token, created=False)

    raw_token = secrets.token_urlsafe(32)
    session = GuestSession.objects.create(
        table=table,
        occupancy=occupancy,
        generation=table.access_generation,
        token_digest=_token_digest(raw_token),
        expires_at=timezone.now() + _session_ttl(),
    )
    _record_guest_audit(
        session=session,
        event_type="guest_session.created",
        entity_type="GuestSession",
        entity_id=str(session.id),
        metadata={
            "table_id": str(table.id),
            "occupancy_id": str(occupancy.id) if occupancy else None,
        },
    )
    return GuestResolution(session=session, token=raw_token, created=True)


@transaction.atomic
def _locked_authorized_session(
    *, token: str, require_tab: bool = False, require_ordering_enabled: bool = True
) -> GuestSession:
    if not token:
        raise GuestAccessError("GUEST_SESSION_REQUIRED", "Sessão guest obrigatória.", 401)
    session = (
        GuestSession.objects.select_for_update()
        # GuestSession is the lock boundary. Both occupancy and tab are
        # nullable, so joining them would make PostgreSQL attempt to lock an
        # outer-join nullable relation.  Resolving those optional relations
        # below preserves the lock and works on PostgreSQL and SQLite.
        .select_related("table")
        .filter(token_digest=_token_digest(token))
        .first()
    )
    if session is None:
        raise GuestAccessError("GUEST_SESSION_INVALID", "Sessão guest inválida.", 401)
    table = Table.objects.select_for_update().get(pk=session.table_id)
    now = timezone.now()
    if session.revoked_at is not None or session.expires_at <= now:
        raise GuestAccessError("GUEST_SESSION_EXPIRED", "Sessão guest expirada ou revogada.", 401)
    if session.generation != table.access_generation:
        # The generation check is authoritative even before a staff lifecycle
        # hook writes a terminal marker to old session rows.  Do not save then
        # raise here: callers are atomic and that write would be rolled back.
        raise GuestAccessError("GUEST_SESSION_REVOKED", "A sessão desta mesa foi revogada.", 403)
    if require_ordering_enabled:
        _assert_table_accepts_guests(table)
    # Keep the object returned to callers aligned with the row protected above.
    session.table = table

    occupancy = _active_occupancy(table)
    if session.occupancy_id is not None:
        if occupancy is None or occupancy.id != session.occupancy_id:
            raise GuestAccessError("GUEST_SESSION_REVOKED", "A ocupação desta mesa terminou.", 403)
    elif require_tab:
        raise GuestAccessError("GUEST_TAB_REQUIRED", "Crie uma comanda antes de pedir.", 409)

    if require_tab and session.tab_id is None:
        raise GuestAccessError("GUEST_TAB_REQUIRED", "Crie uma comanda antes de pedir.", 409)
    session.last_seen_at = now
    session.save(update_fields=["last_seen_at"])
    return session


def guest_session_context(*, session_token: str) -> GuestSession:
    """Return the currently authorized public context (Tab is optional)."""
    return _locked_authorized_session(token=session_token, require_ordering_enabled=False)


@transaction.atomic
def create_or_get_guest_tab(*, session_token: str, display_label: str = "") -> Tab:
    session = _locked_authorized_session(token=session_token)
    if session.tab_id:
        return session.tab

    table = session.table
    occupancy = session.occupancy
    if occupancy is None:
        # DIRECT does not claim a physical table on mere scan. The first guest
        # Tab atomically starts the visit, binding the session to that visit.
        if (
            table.guest_ordering_mode != GuestOrderingMode.DIRECT
            or table.status != TableStatus.AVAILABLE
        ):
            raise GuestAccessError("TABLE_NOT_AVAILABLE", "Mesa não está disponível.", 409)
        occupancy = TableOccupancy.objects.create(table=table, generation=table.access_generation)
        table.status = TableStatus.OCCUPIED
        table.save(update_fields=["status", "updated_at"])
        session.occupancy = occupancy

    from modules.house_account.services import snapshot, sync_attention
    tab = Tab.objects.create(venue_id=table.venue_id, display_label=display_label.strip(),
                             **snapshot(table.venue_id))
    sync_attention(tab)
    TabOccupancyAssignment.objects.create(occupancy=occupancy, tab=tab, assigned_by=None)
    session.tab = tab
    session.save(update_fields=["occupancy", "tab", "last_seen_at"])
    _record_guest_audit(
        session=session,
        event_type="guest_tab.created",
        entity_type="Tab",
        entity_id=str(tab.id),
        metadata={"occupancy_id": str(occupancy.id), "table_id": str(table.id)},
    )
    return tab


@transaction.atomic
def guest_tab_for_session(*, session_token: str) -> Tab:
    return _locked_authorized_session(token=session_token, require_tab=True).tab


@transaction.atomic
def confirm_guest_order(*, session_token: str, lines: list[dict], idempotency_key: str):
    session = _locked_authorized_session(token=session_token, require_tab=True)
    try:
        order = confirm_order(
            tab_id=session.tab_id,
            source=OrderSource.GUEST,
            lines=lines,
            idempotency_key=idempotency_key,
            actor=None,
        )
    except OrderingServiceError as error:
        raise GuestAccessError(
            error.code, error.message, error.status_code, error.details
        ) from error
    if not getattr(order, "_idempotency_replay", False):
        _record_guest_audit(
            session=session,
            event_type="guest_order.confirmed",
            entity_type="Order",
            entity_id=str(order.id),
            metadata={"tab_id": str(session.tab_id), "source": OrderSource.GUEST},
        )
    return order


def guest_catalog(*, session_token: str):
    # A staff block stops mutations immediately but should not erase the
    # guest's ability to inspect the menu/current visit in the PWA.
    session = _locked_authorized_session(token=session_token, require_ordering_enabled=False)
    from modules.catalog.models import Product

    return Product.objects.filter(venue_id=session.table.venue_id, active=True).select_related(
        "availability", "icon"
    )
