import uuid

from django.test import TestCase
from rest_framework.test import APIClient

from modules.documents_printing.models import PrintJob, ReceiptDocument
from modules.ordering.models import Order, Tab
from tests.test_agent_delivery import setup_delivery


class DiagnosticTests(TestCase):
    def setUp(self):
        self.venue, self.other, _, _, self.route, self.machine, _, _ = setup_delivery()
        self.manager = APIClient()
        self.manager.credentials(HTTP_AUTHORIZATION="Bearer rat_synthetic")
        self.path = f"/printing/endpoints/{self.route.endpoint_id}/test/"

    def test_synthetic_test_is_idempotent_nonfinancial_and_claimable(self):
        orders, tabs = Order.objects.count(), Tab.objects.count()
        body = {"idempotency_key": str(uuid.uuid4())}
        first = self.manager.post(self.path, body, format="json")
        assert first.status_code == 201, first.data
        replay = self.manager.post(self.path, body, format="json")
        assert replay.status_code == 201 and replay.data["id"] == first.data["id"]
        job = PrintJob.objects.get(pk=first.data["id"])
        assert job.document.kind == "DIAGNOSTIC_TEST" and job.document.tab_id is None
        assert Order.objects.count() == orders and Tab.objects.count() == tabs
        # Isolate this diagnostic job from the fixture's original production ticket.
        PrintJob.objects.exclude(pk=job.pk).update(state="CANCELLED")
        claim = self.machine.post("/printing/agents/v1/me/claim/", {"protocol_version": 1}, format="json")
        assert claim.status_code == 200 and claim.data["job"]["job_id"] == str(job.id)
        assert ReceiptDocument.objects.filter(kind="DIAGNOSTIC_TEST").count() == 1

    def test_test_print_rejects_machine_staff_foreign_or_disabled_route(self):
        from tests.test_print_pairing import manager

        body = {"idempotency_key": str(uuid.uuid4())}
        assert self.machine.post(self.path, body, format="json").status_code in (401, 403)
        _, staff = manager(self.venue, "STAFF")
        assert staff.post(self.path, body, format="json").status_code == 403
        _, foreign = manager(self.other)
        assert foreign.post(self.path, body, format="json").status_code == 404
        self.route.enabled = False
        self.route.save(update_fields=["enabled"])
        assert self.manager.post(self.path, body, format="json").status_code == 400
        assert not ReceiptDocument.objects.filter(kind="DIAGNOSTIC_TEST").exists()
