from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from pos.models import StaffMember, StaffSession


class DispatchConsumer(AsyncJsonWebsocketConsumer):
    """Realtime acceleration for dispatch; the HTTP event feed remains the recovery path."""

    async def connect(self):
        self.venue_id = self.scope["url_route"]["kwargs"]["venue_id"]
        session_token = self._query_value("session_token")
        staff_id = self._query_value("staff_id")
        authorized = await self._active_session(session_token, self.venue_id) if session_token else await self._active_staff(staff_id, self.venue_id)
        if not authorized:
            await self.close(code=4403)
            return
        self.group_name = f"dispatch.venue.{self.venue_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, _code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def dispatch_event(self, event):
        await self.send_json(event["event"])

    def _query_value(self, key):
        values = dict(pair.split("=", 1) for pair in self.scope["query_string"].decode().split("&") if "=" in pair)
        return values.get(key)

    @database_sync_to_async
    def _active_staff(self, staff_id, venue_id):
        return StaffMember.objects.filter(pk=staff_id, venue_id=venue_id, active=True).exists()

    @database_sync_to_async
    def _active_session(self, token, venue_id):
        return StaffSession.objects.filter(
            token=token, revoked_at__isnull=True,
            staff_member__venue_id=venue_id, staff_member__active=True,
        ).exists()
