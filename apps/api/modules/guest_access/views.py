from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.catalog.models import AvailabilityState
from modules.catalog.serializers import icon_payload
from modules.ordering.views import _order_payload, _tab_payload

from .serializers import GuestOrderConfirmSerializer, GuestTabCreateSerializer, QrResolveSerializer
from .services import (
    GuestAccessError,
    confirm_guest_order,
    create_or_get_guest_tab,
    guest_catalog,
    guest_session_context,
    resolve_table_qr,
)

_RATE_WINDOW_SECONDS = 60
_RATE_LIMITS = {"resolve": 30, "mutation": 60}
_rate_events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_rate_lock = Lock()


def _error_response(error: GuestAccessError) -> Response:
    payload = {"code": error.code, "message": error.message}
    if error.details:
        payload.update(error.details)
    return Response(payload, status=error.status_code)


def _session_token(request) -> str:
    return request.headers.get("X-Guest-Session", "")


def _rate_limit(request, action: str) -> Response | None:
    # Deliberately process-local baseline. Deployments needing distributed
    # throttling can replace this boundary without changing domain semantics.
    subject = request.META.get("REMOTE_ADDR", "unknown")
    key = (action, subject)
    now = monotonic()
    with _rate_lock:
        events = _rate_events[key]
        while events and events[0] <= now - _RATE_WINDOW_SECONDS:
            events.popleft()
        if len(events) >= _RATE_LIMITS[action]:
            return Response(
                {"code": "GUEST_RATE_LIMITED", "message": "Tente novamente em instantes."},
                status=429,
            )
        events.append(now)
    return None


def _context_payload(session, *, token: str | None = None) -> dict:
    table = session.table
    payload = {
        "table": {"label": table.label},
        "occupancy_active": session.occupancy_id is not None,
        "can_start_occupancy": session.occupancy_id is None,
        "expires_at": session.expires_at,
        "tab": _tab_payload(session.tab) if session.tab_id else None,
    }
    if session.tab_id:
        payload["tab"]["orders"] = [
            _order_payload(order) for order in session.tab.orders.order_by("confirmed_at", "id")
        ]
        # Only persisted canonical/manual states exist in this slice. Future
        # inferred milestones must expose source/confidence explicitly.
        for order in payload["tab"]["orders"]:
            for item in order["items"]:
                item["state_source"] = "CANONICAL"
    if token is not None:
        payload["guest_session_token"] = token
    if session.tab_id:
        payload["tab"]["orders"] = [
            _order_payload(order) for order in session.tab.orders.order_by("confirmed_at", "id")
            .prefetch_related("items__product")
        ]
    return payload


class GuestQrResolveView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        limited = _rate_limit(request, "resolve")
        if limited:
            return limited
        serializer = QrResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            resolution = resolve_table_qr(
                public_token=serializer.validated_data["token"],
                existing_session_token=_session_token(request),
            )
        except GuestAccessError as error:
            return _error_response(error)
        return Response(
            _context_payload(resolution.session, token=resolution.token),
            status=201 if resolution.created else 200,
        )


class GuestContextView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            session = guest_session_context(session_token=_session_token(request))
        except GuestAccessError as error:
            return _error_response(error)
        return Response(_context_payload(session))


class GuestTabCreateView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        limited = _rate_limit(request, "mutation")
        if limited:
            return limited
        serializer = GuestTabCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tab = create_or_get_guest_tab(
                session_token=_session_token(request), **serializer.validated_data
            )
        except GuestAccessError as error:
            return _error_response(error)
        return Response(_tab_payload(tab), status=201)


class GuestCatalogView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            products = guest_catalog(session_token=_session_token(request))
        except GuestAccessError as error:
            return _error_response(error)
        return Response(
            {
                "results": [
                    {
                        "id": str(product.id),
                        "name": product.name,
                        "price_cents": product.price_cents,
                        "fulfillment_station": product.fulfillment_station,
                        "available": product.availability.state == AvailabilityState.AVAILABLE,
                        "icon": icon_payload(product),
                    }
                    for product in products
                ]
            }
        )


class GuestOrderConfirmView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        limited = _rate_limit(request, "mutation")
        if limited:
            return limited
        serializer = GuestOrderConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = confirm_guest_order(
                session_token=_session_token(request),
                lines=serializer.validated_data["lines"],
                idempotency_key=serializer.validated_data["idempotency_key"],
            )
        except GuestAccessError as error:
            return _error_response(error)
        replayed = getattr(order, "_idempotency_replay", False)
        order = order.__class__.objects.prefetch_related("items").get(pk=order.pk)
        return Response(_order_payload(order), status=200 if replayed else 201)
