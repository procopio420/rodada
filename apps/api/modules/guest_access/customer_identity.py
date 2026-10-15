"""Opt-in profile credentials bound to an independently revocable guest visit.

Customer display_name, phone, Table label and Tab identifiers are never proofs.
No unauthenticated enrollment against an existing Customer record is permitted.
"""
import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError, transaction
from django.utils import timezone

from modules.hospitality.models import TabOccupancyAssignment
from modules.house_account.models import Customer, Relationship
from modules.ordering.models import Tab, TabState

from .models import CustomerAuthSession, CustomerCredential
from .services import (
    GuestAccessError, _locked_authorized_session, _record_guest_audit, _token_digest,
)

AUTH_TTL = timedelta(hours=2)
INVALID_CREDENTIALS = "Não foi possível autenticar. Confira as credenciais."


def _name(value):
    return value.strip().casefold()


def _issue_auth(*, session, credential):
    raw = secrets.token_urlsafe(32)
    CustomerAuthSession.objects.create(
        credential=credential, guest_session=session,
        venue_id=session.table.venue_id, credential_version=credential.version,
        token_digest=_token_digest(raw), expires_at=timezone.now() + AUTH_TTL,
    )
    return raw


def _audit(session, kind, customer_id):
    _record_guest_audit(
        session=session, event_type="guest_customer." + kind,
        entity_type="Customer", entity_id=str(customer_id),
        metadata={"tab_id": str(session.tab_id) if session.tab_id else None},
    )


@transaction.atomic
def register_customer(*, guest_token, username, password, display_name):
    session = _locked_authorized_session(token=guest_token, require_tab=True)
    tab = Tab.objects.select_for_update().filter(
        pk=session.tab_id, venue_id=session.table.venue_id
    ).first()
    if tab is None or tab.customer_id is not None or tab.state in (TabState.CLOSED, TabState.CANCELLED):
        raise GuestAccessError(
            "TAB_CANNOT_ENROLL", "Esta comanda não permite criar um novo perfil.", 409
        )
    customer = Customer.objects.create(display_name=display_name.strip())
    normalized = _name(username)
    try:
        with transaction.atomic():
            credential = CustomerCredential.objects.create(
                customer=customer, username=normalized, password_hash=make_password(password),
            )
    except IntegrityError as error:
        raise GuestAccessError(
            "USERNAME_UNAVAILABLE", "Identificador não está disponível.", 409
        ) from error
    Relationship.objects.create(
        venue_id=session.table.venue_id, customer=customer, kind="VISITOR"
    )
    # Do not resnapshot limits, exposure, payments or historical Order.
    tab.customer = customer
    tab.version += 1
    tab.save(update_fields=["customer", "version"])
    _audit(session, "registered", customer.id)
    return customer, _issue_auth(session=session, credential=credential)


@transaction.atomic
def login_customer(*, guest_token, username, password):
    session = _locked_authorized_session(
        token=guest_token, require_ordering_enabled=False, require_mutation=False,
    )
    credential = CustomerCredential.objects.select_for_update().filter(
        username=_name(username)
    ).first()
    now = timezone.now()
    if credential is None:
        # Same generic error, no profile lookup by displayed name or phone.
        check_password(password, make_password("not-a-real-customer-password"))
        raise GuestAccessError("INVALID_CREDENTIALS", INVALID_CREDENTIALS, 401)
    if credential.revoked_at or (credential.locked_until and credential.locked_until > now):
        return None, ""
    if not check_password(password, credential.password_hash):
        credential.failed_logins += 1
        if credential.failed_logins >= 5:
            credential.locked_until = now + timedelta(minutes=15)
            credential.failed_logins = 0
        credential.save(update_fields=["failed_logins", "locked_until"])
        # Return an auth failure so the failed-attempt lockout commits.
        # The HTTP boundary converts it to a generic 401 after this transaction.
        return None, ""
    if not Relationship.objects.filter(
        venue_id=session.table.venue_id, customer_id=credential.customer_id,
    ).exists():
        raise GuestAccessError(
            "CUSTOMER_NOT_IN_VENUE", "Perfil não está disponível neste estabelecimento.", 403
        )
    credential.failed_logins = 0
    credential.locked_until = None
    credential.save(update_fields=["failed_logins", "locked_until"])
    _audit(session, "authenticated", credential.customer_id)
    return credential.customer, _issue_auth(session=session, credential=credential)


def _authorized_customer(session, auth_token):
    if not auth_token:
        raise GuestAccessError("CUSTOMER_AUTH_REQUIRED", "Entre no seu perfil.", 401)
    authorization = (
        CustomerAuthSession.objects.select_for_update()
        .select_related("credential__customer")
        .filter(token_digest=_token_digest(auth_token))
        .first()
    )
    now = timezone.now()
    if (
        authorization is None or authorization.revoked_at is not None
        or authorization.expires_at <= now
        or authorization.guest_session_id != session.id
        or authorization.venue_id != session.table.venue_id
        or authorization.credential.revoked_at is not None
        or authorization.credential_version != authorization.credential.version
    ):
        raise GuestAccessError(
            "CUSTOMER_AUTH_REVOKED", "Seu acesso ao perfil expirou. Entre novamente.", 401
        )
    return authorization


@transaction.atomic
def customer_context(*, guest_token, auth_token):
    session = _locked_authorized_session(
        token=guest_token, require_ordering_enabled=False, require_mutation=False,
    )
    if not auth_token:
        return {"authenticated": False, "claimable_tabs": []}
    auth = _authorized_customer(session, auth_token)
    assignments = TabOccupancyAssignment.objects.none()
    if session.occupancy_id is not None:
        assignments = TabOccupancyAssignment.objects.filter(
            occupancy_id=session.occupancy_id,
            occupancy__released_at__isnull=True,
            occupancy__table_id=session.table_id,
            occupancy__generation=session.generation,
            released_at__isnull=True,
            tab__venue_id=auth.venue_id,
            tab__customer_id=auth.credential.customer_id,
            tab__state__in=(TabState.OPEN, TabState.REQUIRES_ACTION, TabState.SETTLING),
        ).select_related("tab")
    return {
        "authenticated": True,
        "display_name": auth.credential.customer.display_name,
        "linked_tab_id": str(session.tab_id) if session.tab_id else None,
        "claimable_tabs": [
            {"id": str(row.tab_id), "label": row.tab.display_label or "Comanda sem nome"}
            for row in assignments
        ],
    }


@transaction.atomic
def claim_customer_tab(*, guest_token, auth_token, target_tab_id):
    session = _locked_authorized_session(token=guest_token)
    auth = _authorized_customer(session, auth_token)
    customer_id = auth.credential.customer_id
    tab = Tab.objects.select_for_update().filter(
        pk=target_tab_id, venue_id=session.table.venue_id,
    ).first()
    if tab is None:
        raise GuestAccessError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    if tab.state in (TabState.CLOSED, TabState.CANCELLED):
        raise GuestAccessError("TAB_NOT_ACTIVE", "Comanda não está ativa.", 409)
    if session.tab_id:
        if tab.id != session.tab_id:
            raise GuestAccessError(
                "GUEST_TAB_ALREADY_LINKED", "Este dispositivo já possui outra comanda.", 409
            )
        if session.occupancy_id is None or not TabOccupancyAssignment.objects.filter(
            occupancy_id=session.occupancy_id,
            occupancy__table_id=session.table_id,
            occupancy__released_at__isnull=True,
            occupancy__generation=session.generation,
            tab=tab, released_at__isnull=True,
        ).exists():
            raise GuestAccessError(
                "TAB_NOT_IN_VISIT", "A comanda não está mais nesta visita.", 403
            )
        if tab.customer_id not in (None, customer_id):
            raise GuestAccessError(
                "TAB_OWNED_BY_OTHER_CUSTOMER", "Esta comanda já pertence a outro perfil.", 403
            )
        if tab.customer_id is None:
            tab.customer_id = customer_id
            tab.version += 1
            tab.save(update_fields=["customer", "version"])
            _audit(session, "tab_linked", customer_id)
        return tab
    if tab.customer_id != customer_id:
        raise GuestAccessError(
            "TAB_OWNED_BY_OTHER_CUSTOMER", "Perfil não tem acesso a esta comanda.", 403
        )
    if session.occupancy_id is None or not TabOccupancyAssignment.objects.filter(
        occupancy_id=session.occupancy_id,
        occupancy__table_id=session.table_id,
        occupancy__released_at__isnull=True,
        occupancy__generation=session.generation,
        tab=tab, released_at__isnull=True,
    ).exists():
        raise GuestAccessError(
            "TAB_NOT_IN_VISIT", "Comanda não pertence a esta visita.", 403
        )
    session.tab = tab
    session.save(update_fields=["tab"])
    _audit(session, "tab_claimed", customer_id)
    return tab


@transaction.atomic
def logout_customer(*, guest_token, auth_token):
    session = _locked_authorized_session(
        token=guest_token, require_ordering_enabled=False, require_mutation=False,
    )
    auth = _authorized_customer(session, auth_token)
    auth.revoked_at = timezone.now()
    auth.save(update_fields=["revoked_at"])
    _audit(session, "logged_out", auth.credential.customer_id)
