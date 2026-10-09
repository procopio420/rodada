import asyncio
import json
from time import monotonic

from asgiref.sync import sync_to_async
from django.http import StreamingHttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability, effective_capabilities
from modules.access.services import AccessServiceError, session_for_access_token
from modules.guest_access.services import GuestAccessError, guest_session_context
from modules.guest_access.views import _context_payload, _error_response

from .services import replay_batch, snapshot_cursor


def frame(event, data, cursor=None):
    identity = f"id: {cursor}\n" if cursor else ""
    serialized = json.dumps(data, default=str, separators=(",", ":"))
    return f"{identity}event: {event}\ndata: {serialized}\n\n"


class SnapshotView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"schema_version": 1, "cursor": snapshot_cursor(request.auth.venue_id)})


class GuestSnapshotView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            session = guest_session_context(
                session_token=request.headers.get("X-Guest-Session", "")
            )
        except GuestAccessError as error:
            return _error_response(error)
        # Baseline precedes reads: concurrent mutations will be replayed.
        cursor = snapshot_cursor(session.table.venue_id)
        return Response({"schema_version": 1, "cursor": cursor, **_context_payload(session)})


def visible(event, identity, guest):
    if guest:
        tab_event = event.event_type.startswith(
            (
                "tab.",
                "guest_tab.",
                "order.",
                "order_item.",
                "dispatch.",
                "payment.",
                "charge.",
                "replacement.",
            )
        )
        return (tab_event and identity.tab_id is not None and event.tab_id == identity.tab_id) or (
            event.aggregate_type in ("Product", "ProductIcon")
            and event.event_type.startswith(("product.", "catalog."))
        )
    capabilities = effective_capabilities(identity.membership)
    if event.event_type.startswith("cash."):
        return bool({Capability.CASH_SHIFT_OPEN, Capability.CASH_REVIEW} & capabilities)
    if event.event_type.startswith(("payment.", "charge.", "replacement.")):
        return Capability.PAYMENT_COLLECT in capabilities
    if event.event_type.startswith(("order.", "order_item.", "dispatch.")):
        return Capability.ORDER_CONFIRM in capabilities
    if event.event_type.startswith(("table.", "table_occupancy.", "zone.")):
        return Capability.TABLE_MANAGE in capabilities
    if event.event_type.startswith("guest_session."):
        return False
    if event.event_type.startswith(("tab.", "guest_tab.")):
        return Capability.TAB_OPEN in capabilities
    if event.event_type.startswith(("product.", "catalog.")):
        return bool(
            {Capability.ORDER_CONFIRM, Capability.CATALOG_AVAILABILITY_MANAGE_STATION}
            & capabilities
        )
    # New domain ports must add an explicit routing policy before public delivery.
    return False


class EventStreamRenderer(JSONRenderer):
    # DRF negotiates before get(); allow clients to request the SSE media type.
    media_type = "text/event-stream"
    format = "sse"


class StreamView(APIView):
    renderer_classes = (EventStreamRenderer, JSONRenderer)
    permission_classes = [IsAuthenticated]
    guest = False

    def get(self, request):
        guest = self.guest
        token = (
            request.headers.get("X-Guest-Session", "")
            if guest
            else request.headers.get("Authorization", "").split(" ", 1)[-1]
        )

        def authorize():
            return (
                guest_session_context(session_token=token)
                if guest
                else session_for_access_token(token)
            )

        try:
            identity = authorize()
        except GuestAccessError as error:
            return _error_response(error)
        except AccessServiceError as error:
            return Response(
                {"code": error.code, "message": error.message}, status=error.status_code
            )
        venue_id = identity.table.venue_id if guest else identity.venue_id
        cursor = request.headers.get("Last-Event-ID") or request.query_params.get("cursor", "")

        def read(cursor):
            try:
                identity = authorize()
            except AccessServiceError as error:
                if error.code == "ACCESS_TOKEN_EXPIRED":
                    return [frame("reauthenticate", {"reason": error.code})], cursor, True
                return [frame("revoked", {"reason": "AUTH_REVOKED"})], cursor, True
            except GuestAccessError:
                return [frame("revoked", {"reason": "AUTH_REVOKED"})], cursor, True
            rows = replay_batch(venue_id, cursor)
            if rows is None:
                return (
                    [frame("reset", {"reason": "CURSOR_GAP", "snapshot_required": True})],
                    cursor,
                    True,
                )
            messages = []
            for row in rows:
                if visible(row, identity, guest):
                    messages.append(frame("change", row.envelope(), row.cursor))
                cursor = row.cursor
            messages.append(frame("ready", {"cursor": cursor}, cursor))
            return messages, cursor, False

        async def stream():
            accepted = cursor
            started = monotonic()
            last_heartbeat = 0
            first = True
            while monotonic() - started < 300:
                previous = accepted
                messages, accepted, done = await sync_to_async(read)(accepted)
                if first or accepted != previous or done:
                    for message in messages:
                        yield message
                first = False
                if done:
                    return
                if monotonic() - last_heartbeat >= 15:
                    yield frame("heartbeat", {"cursor": accepted})
                    last_heartbeat = monotonic()
                await asyncio.sleep(1)

        if request.query_params.get("once") == "1":
            messages, _, _ = read(cursor)
            content = iter(messages)
        else:
            content = stream()
        response = StreamingHttpResponse(content, content_type="text/event-stream")
        response["Cache-Control"] = "no-store, no-transform"
        response["X-Accel-Buffering"] = "no"
        return response


class GuestStreamView(StreamView):
    authentication_classes = []
    permission_classes = [AllowAny]
    guest = True
