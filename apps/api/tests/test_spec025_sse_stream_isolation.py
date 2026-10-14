"""Spec 025: an SSE stream must retain verified Host isolation after HTTP returns."""

import asyncio
import hashlib
import hmac
import time
from unittest.mock import patch

from asgiref.sync import sync_to_async
from django.test import AsyncClient, TransactionTestCase, override_settings
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.access.services import session_for_access_token
from modules.guest_access.services import guest_session_context, resolve_table_qr
from modules.hospitality.models import GuestOrderingMode, Table
from modules.realtime.services import replay_batch, snapshot_cursor
from modules.venue.hostnames import resolved_venue_id
from modules.venue.models import Venue, VenueDomain


SECRET = "test-sse-tenant-signature-only"
HOST_A = "ssetesta.rodada.bar"
HOST_B = "ssetestb.rodada.bar"


def signed_headers(host, path="/realtime/stream/"):
    stamp = str(int(time.time()))
    assertion = f"{stamp}\nGET\n{path}\n{host}"
    signature = hmac.new(SECRET.encode(), assertion.encode(), hashlib.sha256).hexdigest()
    return {
        "HTTP_X_RODADA_BFF_HOST": host,
        "HTTP_X_RODADA_BFF_TIME": stamp,
        "HTTP_X_RODADA_BFF_SIGNATURE": signature,
    }


async def first_stream_event(response):
    iterator = response.streaming_content.__aiter__()
    try:
        return await asyncio.wait_for(iterator.__anext__(), timeout=3)
    finally:
        await iterator.aclose()


@override_settings(ALLOWED_HOSTS=["testserver"], RODADA_BFF_HOST_SECRET=SECRET)
class TenantSseStreamIsolationTests(TransactionTestCase):
    def setUp(self):
        self.a = Venue.objects.create(name="SSE A", slug="sse-a")
        self.b = Venue.objects.create(name="SSE B", slug="sse-b")
        self.domain_a = VenueDomain.objects.create(
            venue=self.a, hostname=HOST_A, is_active=True, is_verified=True,
        )
        VenueDomain.objects.create(
            venue=self.b, hostname=HOST_B, is_active=True, is_verified=True,
        )

        staff = StaffMember.objects.create(
            display_name="SSE operator", login_identifier="sse-operator",
        )
        staff.set_pin("1234")
        staff.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.a, staff_member=staff, role=StaffRole.MANAGER,
        )
        self.staff_client = APIClient()
        login = self.staff_client.post(
            "/auth/login/",
            {
                "venue_slug": self.a.slug,
                "login_identifier": staff.login_identifier,
                "pin": "1234",
                "installation_id": "sse-tenant-test",
                "platform": "WEB",
            },
            format="json",
        )
        self.assertEqual(login.status_code, 200, login.content)
        self.staff_token = login.json()["access_token"]
        self.staff_client.credentials(
            HTTP_AUTHORIZATION="Bearer " + self.staff_token,
        )

        table = Table.objects.create(
            venue=self.a, label="SSE QR", guest_ordering_mode=GuestOrderingMode.DIRECT,
        )
        guest = resolve_table_qr(public_token=table.public_token)
        self.guest_token = guest.token
        self.guest_client = APIClient()
        self.guest_client.credentials(HTTP_X_GUEST_SESSION=self.guest_token)

    def stream(self, guest=False, host=HOST_A):
        path = "/guest/realtime/stream/" if guest else "/realtime/stream/"
        client = self.guest_client if guest else self.staff_client
        response = client.get(
            path, {"cursor": snapshot_cursor(self.a.pk)},
            **signed_headers(host, path),
        )
        return response

    def test_foreign_host_rejects_staff_and_guest_before_stream_starts(self):
        staff = self.stream(host=HOST_B)
        self.assertEqual(staff.status_code, 403)
        guest = self.stream(guest=True, host=HOST_B)
        self.assertEqual(guest.status_code, 404)

    def test_staff_lazy_poll_restores_verified_host_scope(self):
        seen = []

        def traced(token):
            seen.append(resolved_venue_id.get())
            return session_for_access_token(token)

        with patch("modules.realtime.views.session_for_access_token", side_effect=traced):
            response = self.stream()
            self.assertEqual(response.status_code, 200, response.content if not response.streaming else "")
            # HostMiddleware has returned: the request-scoped ContextVar is gone.
            self.assertIsNone(resolved_venue_id.get())
            first = asyncio.run(first_stream_event(response))

        self.assertIn(b"event: ready", first)
        self.assertGreaterEqual(len(seen), 2)
        self.assertEqual(seen, [self.a.pk] * len(seen))

    def test_guest_lazy_poll_restores_verified_host_scope(self):
        seen = []

        def traced(*, session_token):
            seen.append(resolved_venue_id.get())
            return guest_session_context(session_token=session_token)

        with patch("modules.realtime.views.guest_session_context", side_effect=traced):
            response = self.stream(guest=True)
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(resolved_venue_id.get())
            first = asyncio.run(first_stream_event(response))

        self.assertIn(b"event: ready", first)
        self.assertGreaterEqual(len(seen), 2)
        self.assertEqual(seen, [self.a.pk] * len(seen))

    def test_replay_poll_remains_bound_during_outbox_query(self):
        # Token checks alone are insufficient: helpers reading the outbox must
        # execute under the same validated request-scoped Venue identity.
        seen = []

        def traced(venue_id, cursor):
            seen.append((resolved_venue_id.get(), venue_id))
            return replay_batch(venue_id, cursor)

        with patch("modules.realtime.views.replay_batch", side_effect=traced):
            for guest in (False, True):
                with self.subTest(guest=guest):
                    response = self.stream(guest=guest)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(
                        b"event: ready", asyncio.run(first_stream_event(response)),
                    )

        self.assertEqual(len(seen), 2)
        self.assertEqual(seen, [(self.a.pk, self.a.pk)] * 2)

    def test_asgi_request_enforces_venue_through_lazy_stream(self):
        # AsyncClient makes an actual ASGIRequest, unlike APIClient's WSGI
        # request. This exercises the production response/iterator code path.
        seen = []

        def traced(venue_id, cursor):
            seen.append((resolved_venue_id.get(), venue_id))
            return replay_batch(venue_id, cursor)

        async def exercise(guest):
            path = "/guest/realtime/stream/" if guest else "/realtime/stream/"
            headers = {
                key.removeprefix("HTTP_").replace("_", "-"): value
                for key, value in signed_headers(HOST_A, path).items()
            }
            if guest:
                headers["X-Guest-Session"] = self.guest_token
            else:
                headers["Authorization"] = "Bearer " + self.staff_token
            response = await AsyncClient().get(
                path, {"cursor": f"{self.a.pk}:0"}, headers=headers,
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.is_async)
            return await first_stream_event(response)

        with patch("modules.realtime.views.replay_batch", side_effect=traced):
            for guest in (False, True):
                with self.subTest(guest=guest):
                    first = asyncio.run(exercise(guest))
                    self.assertIn(b"event: ready", first)

        self.assertEqual(len(seen), 2)
        self.assertEqual(seen, [(self.a.pk, self.a.pk)] * 2)

    def test_concurrent_asgi_guest_streams_do_not_mix_two_venues(self):
        table_b = Table.objects.create(
            venue=self.b, label="SSE QR B",
            guest_ordering_mode=GuestOrderingMode.DIRECT,
        )
        token_b = resolve_table_qr(public_token=table_b.public_token).token
        observed = []

        def traced(venue_id, cursor):
            observed.append((resolved_venue_id.get(), venue_id))
            return replay_batch(venue_id, cursor)

        async def consume(venue, host, token):
            path = "/guest/realtime/stream/"
            headers = {
                key.removeprefix("HTTP_").replace("_", "-"): value
                for key, value in signed_headers(host, path).items()
            }
            headers["X-Guest-Session"] = token
            response = await AsyncClient().get(
                path, {"cursor": f"{venue.pk}:0"}, headers=headers,
            )
            self.assertEqual(response.status_code, 200)
            return await first_stream_event(response)

        async def run_pair():
            return await asyncio.gather(
                consume(self.a, HOST_A, self.guest_token),
                consume(self.b, HOST_B, token_b),
            )

        with patch("modules.realtime.views.replay_batch", side_effect=traced):
            first_a, first_b = asyncio.run(run_pair())

        self.assertIn(b"event: ready", first_a)
        self.assertIn(b"event: ready", first_b)
        self.assertCountEqual(
            observed, [(self.a.pk, self.a.pk), (self.b.pk, self.b.pk)],
        )

    def test_disabled_host_revokes_active_staff_and_guest_streams(self):
        for guest in (False, True):
            with self.subTest(guest=guest):
                response = self.stream(guest=guest)
                self.assertEqual(response.status_code, 200)

                async def consume_and_disable():
                    iterator = response.streaming_content.__aiter__()
                    try:
                        first = await asyncio.wait_for(iterator.__anext__(), timeout=3)
                        self.assertIn(b"event: ready", first)
                        await sync_to_async(
                            VenueDomain.objects.filter(pk=self.domain_a.pk).update,
                            thread_sensitive=True,
                        )(is_active=False)
                        frames = []
                        for _ in range(3):
                            event = await asyncio.wait_for(iterator.__anext__(), timeout=4)
                            frames.append(event)
                            if b"event: revoked" in event:
                                break
                        return frames
                    finally:
                        await iterator.aclose()

                frames = asyncio.run(consume_and_disable())
                self.assertTrue(
                    any(b"event: revoked" in event for event in frames),
                    frames,
                )
                # Re-enable only the test fixture for the other subtest.
                VenueDomain.objects.filter(pk=self.domain_a.pk).update(is_active=True)

    def test_legacy_shared_api_stream_remains_compatible(self):
        response = self.staff_client.get(
            "/realtime/stream/", {"cursor": snapshot_cursor(self.a.pk)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"event: ready", asyncio.run(first_stream_event(response)))
