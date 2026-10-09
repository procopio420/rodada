import hashlib
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError as ModelValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from modules.access.context import ActorContext
from modules.access.models import StaffMember, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import Product
from modules.documents_printing.adapters import FileAdapter, NetworkAdapter, SpoolAdapter
from modules.documents_printing.models import (
    PrintAttempt,
    PrinterEndpoint,
    PrintJob,
    ReceiptDocument,
    StationPrinterBinding,
)
from modules.documents_printing.renderers import (
    canonical_json,
    render_escpos,
    render_html,
    render_text,
)
from modules.documents_printing.services import (
    claim_job,
    create_document,
    finish_attempt,
    operator_action,
    recover_expired,
    request_job,
)
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Order, OrderItem, Tab
from modules.venue.models import Venue


class PrintingTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Bar do Aderlan", slug="printing")
        self.staff = StaffMember.objects.create(display_name="Caixa", login_identifier="printing")
        self.actor = ActorContext(self.venue.id, self.staff.id, None, None)
        self.tab = Tab.objects.create(venue=self.venue, display_label="Balcão")
        self.order = Order.objects.create(tab=self.tab, source="STAFF")
        for station, name in [("BAR", "Cerveja"), ("KITCHEN", "Porção")]:
            product = Product.objects.create(
                venue=self.venue, name=name, price_cents=1200, fulfillment_station=station
            )
            item = OrderItem.objects.create(
                order=self.order,
                product=product,
                product_name_snapshot=name,
                unit_price_cents=1200,
                quantity=2,
                fulfillment_station_snapshot=station,
                customization_snapshot={
                    "variant": {"name": "Grande"},
                    "modifiers": [{"name": "cebola", "semantic_kind": "REMOVE"}],
                    "special_instructions": "<script>!\x1b\x1d",
                },
            )
            Charge.objects.create(tab=self.tab, order_item=item, amount_cents=2400)
        self.endpoint = PrinterEndpoint.objects.create(
            venue=self.venue, label="Arquivo", adapter="FILE"
        )
        StationPrinterBinding.objects.create(endpoint=self.endpoint, station="BAR")

    def document(self, kind="CUSTOMER_CHECK", **kwargs):
        return create_document(tab_id=self.tab.id, kind=kind, actor=self.actor, **kwargs)

    def job(self, document=None, **kwargs):
        return request_job(
            document=document or self.document(),
            endpoint=self.endpoint,
            actor=self.actor,
            key=kwargs.pop("key", "first"),
            **kwargs,
        )

    def test_snapshot_and_new_financial_version(self):
        first = self.document()
        self.assertEqual(first.snapshot["totals"]["exposure_cents"], 4800)
        self.assertEqual(first.id, self.document().id)
        self.assertEqual(
            first.snapshot_hash, hashlib.sha256(canonical_json(first.snapshot).encode()).hexdigest()
        )
        Payment.objects.create(
            tab=self.tab,
            amount_cents=1200,
            method="CASH",
            idempotency_key="partial",
            received_by=self.staff,
            confirmed_at=timezone.now(),
        )
        second = self.document()
        self.assertNotEqual(first.id, second.id)
        first.refresh_from_db()
        self.assertEqual(first.snapshot["totals"]["exposure_cents"], 4800)
        self.assertEqual(second.snapshot["totals"]["exposure_cents"], 3600)
        with self.assertRaises(ModelValidationError):
            first.save()

    def test_formats_and_printer_control_injection(self):
        doc = self.document()
        text = render_text(doc, 58)
        self.assertTrue(all(len(line) <= 32 for line in text.splitlines()))
        self.assertIn("DOCUMENTO NÃO FISCAL", text)
        self.assertIn("Grande", text)
        self.assertIn("Sem cebola", text)
        html = render_html(doc, 80)
        self.assertIn("size:80mm", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        esc = render_escpos(doc, 58)
        self.assertEqual(esc.count(b"\x1b"), 1)
        self.assertNotIn(b"\x1d", esc)
        self.assertTrue(render_escpos(doc, 80, True, True).endswith(b"\x1dV\x00"))
        self.assertIn("REIMPRESSÃO", render_text(doc, reprint=True))
        self.assertEqual(html, render_html(ReceiptDocument.objects.get(pk=doc.id), 80))
        self.assertEqual(esc, render_escpos(doc, 58))

    def test_partial_payment_closed_receipt_and_pending_rejection(self):
        payment = Payment.objects.create(
            tab=self.tab,
            amount_cents=1000,
            method="PIX",
            idempotency_key="pending",
            received_by=self.staff,
            status="CONFIRMATION_PENDING",
        )
        with self.assertRaises(ValidationError):
            self.document("PAYMENT_RECEIPT", source_id=payment.id)
        payment.status = "CONFIRMED"
        payment.confirmed_at = timezone.now()
        payment.metadata = {"PAN": "SECRET", "token": "SECRET"}
        payment.save()
        doc = self.document("PARTIAL_PAYMENT_RECEIPT", source_id=payment.id)
        self.assertEqual(doc.snapshot["payment"]["amount_cents"], 1000)
        self.assertNotIn("SECRET", canonical_json(doc.snapshot))
        with self.assertRaises(ValidationError):
            self.document("CLOSED_TAB_RECEIPT")
        self.tab.state = "CLOSED"
        self.tab.closed_at = timezone.now()
        self.tab.save()
        doc = self.document("CLOSED_TAB_RECEIPT")
        original = self.job(doc)
        copy = self.job(doc, key="copy", reprint_of=original, reason="Cliente pediu")
        self.assertEqual(copy.reprint_of_id, original.id)
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type="print.reprinted", actor_staff=self.staff, reason="Cliente pediu"
            ).exists()
        )

    def test_station_routing_and_immutable_production_identity(self):
        doc = self.document("PRODUCTION_TICKET", source_id=self.order.id, station="BAR")
        self.assertEqual([i["name"] for i in doc.snapshot["items"]], ["Cerveja"])
        self.assertNotIn("totals", doc.snapshot)
        first = self.job(doc)
        self.assertEqual(first.id, self.job(doc, key="another-click").id)
        kitchen = self.document("PRODUCTION_TICKET", source_id=self.order.id, station="KITCHEN")
        with self.assertRaises(ValidationError):
            self.job(kitchen)
        self.tab.display_label = "Mudou"
        self.tab.save()
        self.assertEqual(
            doc.id, self.document("PRODUCTION_TICKET", source_id=self.order.id, station="BAR").id
        )
        self.assertEqual(doc.snapshot["tab_label"], "Balcão")

    def test_retry_backoff_and_bounded_failure(self):
        job = self.job()
        for attempt in range(1, 6):
            claim = claim_job()
            self.assertEqual(claim.id, job.id)
            self.assertEqual(claim.attempt_count, attempt)
            self.assertIsNone(claim_job())
            finish_attempt(job.id, claim.attempt_token, "FAILED_RETRYABLE", "No connection")
            job.refresh_from_db()
            self.assertGreater(job.available_at, timezone.now())
            self.assertIsNone(claim_job())
            if attempt < 5:
                operator_action(job.id, "retry", self.actor)
        self.assertEqual(job.state, "FAILED_FINAL")
        self.assertEqual(PrintAttempt.objects.filter(job=job).count(), 5)
        self.assertEqual(OrderItem.objects.count(), 2)

    def test_crash_recovery_fences_late_ack_and_never_resends(self):
        job = self.job()
        claim = claim_job()
        PrintJob.objects.filter(pk=job.pk).update(lease_until=timezone.now() - timedelta(seconds=1))
        recover_expired()
        job.refresh_from_db()
        self.assertEqual(job.state, "DELIVERY_UNCERTAIN")
        self.assertFalse(finish_attempt(job.id, claim.attempt_token, "SPOOL_ACCEPTED"))
        self.assertIsNone(claim_job())
        with self.assertRaises(ValidationError):
            operator_action(job.id, "retry", self.actor)
        copy = self.job(key="explicit", reprint_of=job, reason="Papel parcial")
        self.assertNotEqual(copy.id, job.id)

    def test_spool_and_file_are_not_physical_success(self):
        job = self.job()
        claim = claim_job()
        finish_attempt(job.id, claim.attempt_token, "SPOOL_ACCEPTED")
        job.refresh_from_db()
        self.assertEqual(job.state, "SPOOL_ACCEPTED")
        self.assertIsNone(claim_job())
        with self.assertRaises(ValueError):
            finish_attempt(job.id, claim.attempt_token, "PRINTED")
        operator_action(job.id, "confirm", self.actor)
        job.refresh_from_db()
        self.assertEqual(job.state, "PRINTED")
        self.assertTrue(AuditEvent.objects.filter(event_type="print.confirm").exists())
        with TemporaryDirectory() as directory:
            result = FileAdapter(directory).deliver(str(job.id), b"<html>test</html>")
            self.assertEqual(result.outcome, "OUTPUT_READY")
            self.assertEqual(
                (Path(directory) / (str(job.id) + ".html")).read_bytes(), b"<html>test</html>"
            )

    def test_adapter_definitive_and_ambiguous_faults(self):
        with patch("socket.create_connection", side_effect=ConnectionRefusedError):
            self.assertEqual(
                NetworkAdapter("localhost").deliver("job", b"data").outcome, "FAILED_RETRYABLE"
            )
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection.sendall.side_effect = OSError()
        with patch("socket.create_connection", return_value=connection):
            self.assertEqual(
                NetworkAdapter("localhost").deliver("job", b"data").outcome, "DELIVERY_UNCERTAIN"
            )
        with patch("shutil.which", return_value=None):
            self.assertEqual(
                SpoolAdapter("usb").deliver("job", b"data").outcome, "FAILED_RETRYABLE"
            )
        with (
            patch("shutil.which", return_value="/bin/lp"),
            patch("subprocess.run", return_value=MagicMock(returncode=1)),
        ):
            self.assertEqual(
                SpoolAdapter("usb").deliver("job", b"data").outcome, "DELIVERY_UNCERTAIN"
            )

    def login(self, role="STAFF", overrides=None):
        self.staff.set_pin("1234")
        self.staff.save()
        VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            role=role,
            capability_overrides=overrides or {},
        )
        client = APIClient()
        response = client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.staff.login_identifier,
                "pin": "1234",
                "installation_id": "printing",
                "platform": "WEB",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION="Bearer " + response.json()["access_token"])
        return client

    def test_api_permissions_cross_venue_station_and_management(self):
        client = self.login(overrides={"allow": ["print.production.bar"]})
        doc = self.document("PRODUCTION_TICKET", source_id=self.order.id, station="BAR")
        job = self.job(doc)
        self.assertEqual(client.get(f"/printing/jobs/{job.id}/").status_code, 200)
        denied = client.post(
            "/printing/documents/",
            {
                "tab_id": str(self.tab.id),
                "source_id": str(self.order.id),
                "kind": "PRODUCTION_TICKET",
                "station": "KITCHEN",
            },
            format="json",
        )
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(client.get("/printing/jobs/").status_code, 403)
        self.assertEqual(client.post("/printing/endpoints/", {}, format="json").status_code, 403)
        other = Venue.objects.create(name="Other", slug="other-printing")
        other_tab = Tab.objects.create(venue=other)
        response = client.post(
            "/printing/documents/",
            {"tab_id": str(other_tab.id), "kind": "CUSTOMER_CHECK"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        response = client.post(
            f"/printing/jobs/{job.id}/",
            {"action": "reprint", "idempotency_key": "copy-api", "reason": "Papel falhou"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        copy = PrintJob.objects.get(pk=response.json()["id"])
        self.assertEqual(copy.reprint_of_id, job.id)
        self.assertIn(
            "REIMPRESSÃO", client.get(f"/printing/jobs/{copy.id}/").json()["output"]["text"]
        )

    def test_bridge_claim_result_and_fencing(self):
        client = self.login("MANAGER")
        job = self.job()
        claim = client.post(
            "/printing/bridge/claim/", {"endpoint_ids": [str(self.endpoint.id)]}, format="json"
        )
        self.assertEqual(claim.status_code, 200)
        result = {"attempt_token": claim.json()["attempt_token"], "outcome": "OUTPUT_READY"}
        self.assertEqual(
            client.post(
                f"/printing/bridge/jobs/{job.id}/result/", result, format="json"
            ).status_code,
            200,
        )
        self.assertEqual(
            client.post(
                f"/printing/bridge/jobs/{job.id}/result/", result, format="json"
            ).status_code,
            409,
        )
        self.assertEqual(
            client.post(
                "/printing/bridge/claim/", {"endpoint_ids": [str(self.endpoint.id)]}, format="json"
            ).status_code,
            204,
        )

    def test_mismatched_idempotency_and_disabled_endpoint(self):
        doc = self.document()
        original = self.job(doc)
        with self.assertRaises(ValidationError):
            self.job(doc, reprint_of=original, reason="Copy")
        self.endpoint.enabled = False
        self.endpoint.save()
        with self.assertRaises(ValidationError):
            self.job(doc, key="disabled")

    def test_browser_dialog_request_is_uncertain_and_cannot_be_opened_twice(self):
        self.endpoint.adapter = "BROWSER"
        self.endpoint.save()
        job = self.job()
        self.assertEqual(job.state, "OUTPUT_READY")
        operator_action(job.id, "browser_open", self.actor)
        job.refresh_from_db()
        self.assertEqual(job.state, "DELIVERY_UNCERTAIN")
        with self.assertRaises(ValidationError):
            operator_action(job.id, "browser_open", self.actor)

    def test_order_to_production_to_final_customer_receipt_e2e(self):
        client = self.login("MANAGER")
        tab = client.post("/tabs/", {"display_label": "E2E impressão"}, format="json").json()
        products = list(Product.objects.filter(venue=self.venue))
        response = client.post(
            f"/tabs/{tab['id']}/orders/confirm/",
            {
                "idempotency_key": "e2e-order",
                "lines": [{"product_id": str(p.id), "quantity": 1} for p in products],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        order = response.json()
        response = client.post(
            "/printing/documents/",
            {
                "tab_id": tab["id"],
                "source_id": order["id"],
                "kind": "PRODUCTION_TICKET",
                "station": "BAR",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        doc = response.json()
        job = client.post(
            "/printing/jobs/",
            {
                "document_id": doc["id"],
                "endpoint_id": str(self.endpoint.id),
                "idempotency_key": "e2e-print",
            },
            format="json",
        )
        self.assertEqual(job.status_code, 201)
        claim = claim_job([self.endpoint.id])
        finish_attempt(claim.id, claim.attempt_token, "FAILED_RETRYABLE", "Printer disconnected")
        self.assertTrue(Order.objects.filter(pk=order["id"], status="CONFIRMED").exists())
        payment = client.post(
            f"/tabs/{tab['id']}/payments/",
            {"amount_cents": 2400, "method": "EXTERNAL_TERMINAL", "idempotency_key": "e2e-payment"},
            format="json",
        )
        self.assertEqual(payment.status_code, 201, payment.json())
        response = client.post(f"/tabs/{tab['id']}/close/", {}, format="json")
        self.assertEqual(response.status_code, 200, response.json())
        response = client.post(
            "/printing/documents/",
            {"tab_id": tab["id"], "kind": "CLOSED_TAB_RECEIPT"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["snapshot"]["totals"]["exposure_cents"], 0)
        self.assertIn("DOCUMENTO NÃO FISCAL", response.json()["text"])
        self.assertEqual(len(response.json()["snapshot"]["items"]), 2)

    def test_share_token_is_read_only_scoped_expiring_and_revocable(self):
        client = self.login()
        document = self.document()
        response = client.post(f"/printing/documents/{document.id}/share/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        share = response.json()
        from modules.documents_printing.models import ReceiptAccessToken

        self.assertNotEqual(
            ReceiptAccessToken.objects.get(pk=share["id"]).token_hash, share["token"]
        )
        public = APIClient()
        response = public.get(f"/receipts/{share['token']}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], str(document.id))
        self.assertEqual(public.get("/receipts/guessed-id/").status_code, 404)
        self.assertEqual(public.post("/printing/jobs/", {}, format="json").status_code, 401)
        client.post(
            f"/printing/documents/{document.id}/share/", {"revoke_id": share["id"]}, format="json"
        )
        self.assertEqual(public.get(f"/receipts/{share['token']}/").status_code, 404)
        share = client.post(f"/printing/documents/{document.id}/share/", {}, format="json").json()
        ReceiptAccessToken.objects.filter(pk=share["id"]).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertEqual(public.get(f"/receipts/{share['token']}/").status_code, 404)

    def test_guest_document_can_only_use_its_authorized_tab(self):
        from modules.guest_access.services import create_or_get_guest_tab, resolve_table_qr
        from modules.hospitality.models import Table, TableOccupancy

        table = Table.objects.create(venue=self.venue, label="Guest", guest_ordering_mode="DIRECT")
        TableOccupancy.objects.create(table=table, generation=table.access_generation)
        resolution = resolve_table_qr(public_token=table.public_token)
        tab = create_or_get_guest_tab(session_token=resolution.token, display_label="Minha conta")
        public = APIClient()
        public.credentials(HTTP_X_GUEST_SESSION=resolution.token)
        response = public.get(
            "/guest/receipt/", {"tab_id": str(self.tab.id), "kind": "PRODUCTION_TICKET"}
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["snapshot"]["tab_id"], str(tab.id))
        self.assertEqual(response.json()["kind"], "CUSTOMER_CHECK")
        document = ReceiptDocument.objects.get(pk=response.json()["id"])
        self.assertEqual(document.created_guest_session_id, resolution.session.id)
        resolution.session.revoked_at = timezone.now()
        resolution.session.save()
        self.assertEqual(public.get("/guest/receipt/").status_code, 401)

    def test_split_bill_uses_canonical_responsibility_and_transfer_quantity(self):
        from modules.tab_operations.models import TabOperation, TabTransfer, TabTransferLine

        destination = Tab.objects.create(venue=self.venue, display_label="Separada")
        charge = Charge.objects.filter(
            tab=self.tab, order_item__fulfillment_station_snapshot="BAR"
        ).get()
        operation = TabOperation.objects.create(
            source_tab=self.tab,
            idempotency_key="split-print",
            request_fingerprint="x",
            kind="SPLIT",
            created_by=self.staff,
        )
        transfer = TabTransfer.objects.create(
            operation=operation,
            venue=self.venue,
            source_tab=self.tab,
            destination_tab=destination,
            kind="SPLIT",
            source_version=1,
            destination_version=1,
        )
        TabTransferLine.objects.create(
            transfer=transfer, source_charge=charge, amount_cents=1200, quantity=1
        )
        document = create_document(tab_id=destination.id, kind="CUSTOMER_CHECK", actor=self.actor)
        self.assertEqual(document.snapshot["totals"]["exposure_cents"], 1200)
        self.assertEqual(document.snapshot["items"][0]["name"], "Cerveja")
        self.assertEqual(document.snapshot["items"][0]["responsibility_cents"], 1200)
        text = render_text(document)
        self.assertIn("pedido original", text)
        self.assertIn("Recebido: 1 x Cerveja", text)
        self.assertEqual(document.snapshot["transfers"][0]["source_charge_id"], str(charge.id))

    def test_late_result_without_recovery_poll_still_fences_delivery(self):
        job = self.job()
        claim = claim_job()
        PrintJob.objects.filter(pk=job.id).update(lease_until=timezone.now() - timedelta(seconds=1))
        self.assertFalse(finish_attempt(job.id, claim.attempt_token, "SPOOL_ACCEPTED"))
        job.refresh_from_db()
        self.assertEqual(job.state, "DELIVERY_UNCERTAIN")
        self.assertIsNone(claim_job())

    def test_receipt_bulk_mutation_and_token_url_logging_protection(self):
        document = self.document()
        with self.assertRaises(ModelValidationError):
            ReceiptDocument.objects.filter(pk=document.pk).update(snapshot={})
        with self.assertRaises(ModelValidationError):
            document.delete()
        from modules.access.logging import redact_auth_secrets

        raw = "a" * 43
        self.assertEqual(
            redact_auth_secrets("/receipts/" + raw + "/"), "/receipts/[REDACTED_RECEIPT_TOKEN]/"
        )

    def test_failed_job_filter_finds_old_failures_and_history_is_paginated(self):
        client = self.login("MANAGER")
        original = self.job()
        PrintJob.objects.filter(pk=original.id).update(state="FAILED_FINAL")
        PrintJob.objects.bulk_create(
            [
                PrintJob(
                    document=original.document,
                    endpoint=self.endpoint,
                    idempotency_key=f"history-{i}",
                    state="OUTPUT_READY",
                    reprint_of=original,
                    requested_by=self.staff,
                    reason="Fixture copy",
                    available_at=timezone.now(),
                )
                for i in range(101)
            ]
        )
        page = client.get("/printing/jobs/").json()
        self.assertEqual(len(page["results"]), 100)
        self.assertEqual(page["next_offset"], 100)
        self.assertNotIn(str(original.id), [j["id"] for j in page["results"]])
        failed = client.get("/printing/jobs/", {"failed_only": "true"}).json()
        self.assertEqual([j["id"] for j in failed["results"]], [str(original.id)])
        self.assertEqual(len(client.get("/printing/jobs/", {"offset": 100}).json()["results"]), 2)

    def test_other_station_reprint_is_denied_and_creates_no_copy(self):
        client = self.login(overrides={"allow": ["print.production.bar"]})
        StationPrinterBinding.objects.create(endpoint=self.endpoint, station="KITCHEN")
        doc = self.document("PRODUCTION_TICKET", source_id=self.order.id, station="KITCHEN")
        original = self.job(doc, key="kitchen")
        response = client.post(
            f"/printing/jobs/{original.id}/",
            {"action": "reprint", "reason": "Unauthorized", "idempotency_key": "unauthorized"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(PrintJob.objects.count(), 1)

    def test_document_source_cannot_be_spoofed_or_unconfirmed(self):
        with self.assertRaises(ValidationError):
            self.document(source_id=self.order.id)
        with self.assertRaises(ValidationError):
            self.document("PAYMENT_RECEIPT")
        self.order.status = "CANCELLED"
        self.order.save()
        with self.assertRaises(ValidationError):
            self.document("PRODUCTION_TICKET", source_id=self.order.id, station="BAR")
        self.assertEqual(ReceiptDocument.objects.count(), 0)
