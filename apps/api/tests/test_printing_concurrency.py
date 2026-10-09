from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from modules.access.context import ActorContext
from modules.access.models import StaffMember
from modules.catalog.models import Product
from modules.documents_printing.models import (
    PrintAttempt,
    PrinterEndpoint,
    PrintJob,
    ReceiptDocument,
    StationPrinterBinding,
)
from modules.documents_printing.services import (
    claim_job,
    create_document,
    finish_attempt,
    request_job,
)
from modules.ordering.models import Order, OrderItem, Tab
from modules.venue.models import Venue


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL locks")
class PrintConcurrencyTests(TransactionTestCase):
    def setUp(self):
        venue = Venue.objects.create(name="Concurrency", slug="print-race")
        staff = StaffMember.objects.create(display_name="Print", login_identifier="print-race")
        self.actor = ActorContext(venue.id, staff.id, None, None)
        self.tab = Tab.objects.create(venue=venue)
        self.order = Order.objects.create(tab=self.tab, source="STAFF")
        product = Product.objects.create(
            venue=venue, name="Beer", price_cents=1000, fulfillment_station="BAR"
        )
        OrderItem.objects.create(
            order=self.order,
            product=product,
            product_name_snapshot="Beer",
            unit_price_cents=1000,
            quantity=1,
            fulfillment_station_snapshot="BAR",
        )
        self.endpoint = PrinterEndpoint.objects.create(venue=venue, label="LAN", adapter="NETWORK")
        StationPrinterBinding.objects.create(endpoint=self.endpoint, station="BAR")

    def race(self, operation):
        barrier = Barrier(2)

        def worker(i):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return operation(i)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, (0, 1)))

    def document(self):
        return create_document(
            tab_id=self.tab.id,
            kind="PRODUCTION_TICKET",
            source_id=self.order.id,
            station="BAR",
            actor=self.actor,
        )

    def test_simultaneous_documents_and_different_initial_keys(self):
        ids = self.race(lambda i: self.document().id)
        self.assertEqual(ids[0], ids[1])
        doc = ReceiptDocument.objects.get(pk=ids[0])
        jobs = self.race(
            lambda i: (
                request_job(
                    document=doc, endpoint=self.endpoint, key=f"click-{i}", actor=self.actor
                ).id
            )
        )
        self.assertEqual(jobs[0], jobs[1])
        self.assertEqual(PrintJob.objects.count(), 1)

    def test_idempotent_creation_and_skip_locked_worker_claim(self):
        doc = self.document()
        jobs = self.race(
            lambda i: (
                request_job(
                    document=doc, endpoint=self.endpoint, key="same-command", actor=self.actor
                ).id
            )
        )
        self.assertEqual(jobs[0], jobs[1])
        claims = self.race(lambda i: claim_job())
        claimed = [c for c in claims if c is not None]
        self.assertEqual(len(claimed), 1)
        self.assertEqual(PrintAttempt.objects.count(), 1)
        job = claimed[0]
        results = self.race(lambda i: finish_attempt(job.id, job.attempt_token, "SPOOL_ACCEPTED"))
        self.assertCountEqual(results, [True, False])
        self.assertEqual(PrintJob.objects.get(pk=job.id).state, "SPOOL_ACCEPTED")

    def test_same_reprint_command_is_audited_once(self):
        doc = self.document()
        original = request_job(
            document=doc, endpoint=self.endpoint, key="initial", actor=self.actor
        )
        copies = self.race(
            lambda i: (
                request_job(
                    document=doc,
                    endpoint=self.endpoint,
                    key="copy",
                    actor=self.actor,
                    reprint_of=original,
                    reason="Partial paper",
                ).id
            )
        )
        self.assertEqual(copies[0], copies[1])
        from modules.audit.models import AuditEvent

        self.assertEqual(AuditEvent.objects.filter(event_type="print.reprinted").count(), 1)

    def test_cross_endpoint_initial_production_dispatch_is_one_job(self):
        doc = self.document()
        other = PrinterEndpoint.objects.create(
            venue=self.tab.venue, label="Backup", adapter="NETWORK"
        )
        StationPrinterBinding.objects.create(endpoint=other, station="BAR")
        endpoints = [self.endpoint, other]
        jobs = self.race(
            lambda i: (
                request_job(
                    document=doc, endpoint=endpoints[i], key=f"destination-{i}", actor=self.actor
                ).id
            )
        )
        self.assertEqual(jobs[0], jobs[1])
        self.assertEqual(PrintJob.objects.count(), 1)

    def test_postgres_rejects_direct_snapshot_sql_update(self):
        from django.db import DatabaseError, transaction

        doc = self.document()
        with self.assertRaises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                "UPDATE documents_printing_receiptdocument SET snapshot_hash = %s WHERE id = %s",
                ["changed", doc.id],
            )
        doc.refresh_from_db()
        self.assertNotEqual(doc.snapshot_hash, "changed")
