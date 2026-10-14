"""Two-Venue negative proof. All money is confined to pytest's disposable DB."""

import base64
import secrets
import tempfile
from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.catalog.models import Product
from modules.documents_printing.models import ReceiptAccessToken
from modules.ledger.models import Charge, Payment, Refund
from modules.ordering.models import Order, Tab
from modules.venue.models import Venue, VenueDomain
from tests.test_quick_catalog import image_bytes
from tests.test_spec025_host_security import SECRET, signed


@override_settings(RODADA_BFF_HOST_SECRET=SECRET)
class AuditTwoVenueTests(TestCase):
    def setUp(self):
        storage = tempfile.TemporaryDirectory()
        self.addCleanup(storage.cleanup)
        setting = override_settings(MEDIA_ROOT=storage.name)
        setting.enable()
        self.addCleanup(setting.disable)
        self.rows = []
        for label in ("a", "b"):
            venue = Venue.objects.create(name=f"Audit {label}", slug=f"audit-{label}")
            host = f"e2e{label}.rodada.bar"
            VenueDomain.objects.create(
                venue=venue, hostname=host, is_active=True, is_verified=True,
            )
            staff = StaffMember.objects.create(display_name=label, login_identifier=label)
            staff.set_pin("2468")
            staff.save(update_fields=["pin_hash"])
            VenueStaffMembership.objects.create(
                venue=venue, staff_member=staff, role=StaffRole.OWNER,
            )
            client = APIClient()
            login = client.post("/auth/login/", {
                "venue_slug": venue.slug, "login_identifier": label, "pin": "2468",
                "installation_id": f"audit-{label}", "platform": "ANDROID",
            }, format="json", HTTP_HOST="api.rodada.bar")
            self.assertEqual(login.status_code, 200)
            client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
            self.assertEqual(client.post(
                "/auth/reauthenticate/", {"pin": "2468"}, format="json",
            ).status_code, 200)
            product = Product.objects.create(
                venue=venue, name=f"Private product {label}", price_cents=1000,
                fulfillment_station="BAR",
            )
            tab = client.post("/tabs/", {"display_label": f"Private tab {label}"},
                              format="json").json()
            path = f"/tabs/{tab['id']}/orders/confirm/"
            payload = {"idempotency_key": "same-local-order",
                       "lines": [{"product_id": str(product.pk), "quantity": 1}]}
            self.assertEqual(client.post(path, payload, format="json").status_code, 201)
            self.assertEqual(client.post(path, payload, format="json").status_code, 200)
            path = f"/tabs/{tab['id']}/payments/"
            payload = {"amount_cents": 500, "method": "EXTERNAL_TERMINAL",
                       "idempotency_key": "same-local-payment"}
            payment = client.post(path, payload, format="json")
            self.assertEqual(payment.status_code, 201)
            self.assertEqual(client.post(path, payload, format="json").json()["id"],
                             payment.json()["id"])
            self.rows.append((venue, host, client, product, tab, payment.json()))

    def request(self, client, host, path, data=None):
        verb = "GET" if data is None else "POST"
        assertion = signed(host, method=path, verb=verb)
        if data is None:
            return client.get(path, **assertion)
        return client.post(path, data, format="json", **assertion)

    def counts(self):
        return tuple(model.objects.count() for model in (Tab, Order, Charge, Payment, Refund))

    def test_symmetric_reads_mutations_financial_replays_and_native_api(self):
        before = self.counts()
        self.assertEqual(before, (2, 2, 2, 2, 0))
        for own, foreign in ((self.rows[0], self.rows[1]), (self.rows[1], self.rows[0])):
            venue, host, client, _, tab, payment = own
            _, other_host, _, _, other_tab, other_payment = foreign
            local = self.request(client, host, "/tabs/")
            self.assertEqual(local.status_code, 200)
            self.assertEqual({row["id"] for row in local.json()["results"]}, {tab["id"]})
            # Native shared-host identity and ORM isolation are independent of BFF Host.
            native = client.get("/auth/me/", HTTP_HOST="api.rodada.bar")
            self.assertEqual(native.json()["venue"]["id"], str(venue.pk))
            self.assertEqual(client.get(f"/tabs/{other_tab['id']}/").status_code, 404)
            for path, data in (
                (f"/tabs/{other_tab['id']}/payments/", {
                    "amount_cents": 500, "method": "EXTERNAL_TERMINAL",
                    "idempotency_key": "same-local-payment"}),
                (f"/payments/{other_payment['id']}/refunds/", {
                    "amount_cents": 100, "idempotency_key": "same-local-refund"}),
            ):
                self.assertEqual(self.request(client, host, path, data).status_code, 404)
            self.assertEqual(self.request(client, other_host, "/tabs/").status_code, 403)
            self.assertEqual(self.request(client, other_host, "/tabs/", {
                "display_label": "must-not-exist"}).status_code, 403)
            self.assertEqual(self.counts(), before)
            refund_path = f"/payments/{payment['id']}/refunds/"
            refund_body = {"amount_cents": 100, "idempotency_key": "same-local-refund"}
            first = self.request(client, host, refund_path, refund_body)
            self.assertEqual(first.status_code, 201, first.content)
            replay = self.request(client, host, refund_path, refund_body)
            self.assertEqual(replay.status_code, 200)
            self.assertEqual(replay.json()["id"], first.json()["id"])
            before = self.counts()
        self.assertEqual(self.counts(), (2, 2, 2, 2, 2))
        # Refund identifiers are independently scoped before provider lookup.
        for own, foreign in ((self.rows[0], self.rows[1]), (self.rows[1], self.rows[0])):
            _, host, client, _, _, _ = own
            foreign_refund = Refund.objects.get(payment_id=foreign[5]["id"])
            response = self.request(client, host, f"/refunds/{foreign_refund.pk}/reconcile/", {})
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["code"], "REFUND_NOT_FOUND")
            self.assertEqual(self.counts(), (2, 2, 2, 2, 2))

    def test_published_assets_are_portable_but_private_assets_and_mutations_are_not(self):
        public = APIClient()
        for own, foreign in ((self.rows[0], self.rows[1]), (self.rows[1], self.rows[0])):
            _, host, client, product, _, _ = own
            _, other_host, other_client, _, _, _ = foreign
            path = f"/catalog/products/{product.pk}/icon/"
            body = {"action": "upload", "mime": "image/png",
                    "image_base64": base64.b64encode(image_bytes()).decode()}
            uploaded = self.request(client, host, path, body)
            self.assertEqual(uploaded.status_code, 200)
            url = uploaded.json()["icon"]["published_asset_url"]
            for access_host in (host, other_host):
                response = self.request(public, access_host, url)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(b"".join(response.streaming_content))
                self.assertEqual(self.request(public, access_host,
                                             url.replace(".png", "-private.png")).status_code, 404)
            self.assertEqual(self.request(other_client, other_host, path,
                                         {"action": "remove"}).status_code, 404)
            self.assertEqual(self.request(client, host, path, {"action": "remove"}).status_code, 200)
            self.assertEqual(self.request(public, other_host, url).status_code, 404)

    def test_receipt_capability_is_portable_read_only_scoped_and_revocable(self):
        public = APIClient()
        for own, foreign in ((self.rows[0], self.rows[1]), (self.rows[1], self.rows[0])):
            _, host, client, _, tab, _ = own
            _, other_host, other_client, _, _, _ = foreign
            created = self.request(client, host, "/printing/documents/", {
                "tab_id": tab["id"], "kind": "CUSTOMER_CHECK"})
            self.assertEqual(created.status_code, 201, created.content)
            document = created.json()
            share_path = f"/printing/documents/{document['id']}/share/"
            share = self.request(client, host, share_path, {}).json()
            url = f"/receipts/{share['token']}/"
            for access_host in (host, other_host):
                response = self.request(public, access_host, url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["snapshot"]["tab_id"], tab["id"])
                self.assertEqual(response["Cache-Control"], "no-store")
                self.assertNotIn("encrypted_credentials", response.json())
                self.assertEqual(self.request(public, access_host, url, {}).status_code, 405)
                self.assertEqual(self.request(public, access_host,
                    f"/receipts/{secrets.token_urlsafe(32)}/").status_code, 404)
            self.assertEqual(self.request(other_client, other_host, share_path,
                {"revoke_id": share["id"]}).status_code, 404)
            self.assertEqual(self.request(client, host, share_path,
                {"revoke_id": share["id"]}).status_code, 200)
            self.assertEqual(self.request(public, other_host, url).status_code, 404)
            share = self.request(client, host, share_path, {}).json()
            ReceiptAccessToken.objects.filter(pk=share["id"]).update(
                expires_at=timezone.now() - timedelta(seconds=1))
            self.assertEqual(self.request(public, other_host,
                f"/receipts/{share['token']}/").status_code, 404)
