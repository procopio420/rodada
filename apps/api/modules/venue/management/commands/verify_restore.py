"""Verify that immutable operational/financial history survived a restore."""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum

from modules.cash.models import CashShift, CashShiftStatus
from modules.cash.services import cash_shift_position
from modules.corrections.models import FinancialDisposition, OrderCorrection
from modules.dispatch.models import DispatchTask, DispatchTaskState
from modules.guest_access.models import GuestSession
from modules.hospitality.models import TableOccupancy
from modules.ledger.models import Charge, LedgerAdjustment, Refund, RefundStatus
from modules.ledger.services import totals
from modules.ordering.models import Tab
from modules.venue.models import Venue


class Command(BaseCommand):
    help = "Verifica integridade financeira e operacional dos fatos do ensaio restaurado."

    def add_arguments(self, parser):
        parser.add_argument("--venue-slug", default="restore-rehearsal")

    def handle(self, *args, **options):
        venue = Venue.objects.filter(slug=options["venue_slug"]).first()
        if venue is None:
            raise CommandError("RESTORE_VENUE_NOT_FOUND: rehearsal venue is absent from this database.")

        tab = Tab.objects.filter(venue=venue, display_label="Restore history").order_by("-opened_at").first()
        if tab is None:
            raise CommandError("RESTORE_TAB_NOT_FOUND: representative tab is absent.")
        tab_totals = totals(tab)
        if tab_totals["exposure_cents"] != 0:
            raise CommandError(f"RESTORE_EXPOSURE_MISMATCH: expected 0, got {tab_totals['exposure_cents']}.")

        refunds = Refund.objects.filter(payment__tab=tab, status=RefundStatus.CONFIRMED)
        if refunds.count() != 1 or refunds.first().amount_cents != 2400:
            raise CommandError("RESTORE_REFUND_MISMATCH: confirmed refund history is incomplete.")
        correction = OrderCorrection.objects.filter(
            venue=venue,
            financial_disposition=FinancialDisposition.REFUND_REQUIRED,
        ).select_related("refund", "financial_adjustment").first()
        if correction is None or correction.refund_id is None or correction.financial_adjustment_id is None:
            raise CommandError("RESTORE_CORRECTION_LINK_MISMATCH: refund/reversal linkage is incomplete.")
        if not LedgerAdjustment.objects.filter(tab=tab, amount_cents__lt=0).exists():
            raise CommandError("RESTORE_REVERSAL_MISSING: append-only reversal is absent.")
        if Charge.objects.filter(tab=tab).aggregate(total=Sum("amount_cents"))["total"] != 4200:
            raise CommandError("RESTORE_CHARGE_HISTORY_MISMATCH: original charges were rewritten or lost.")

        closed = CashShift.objects.filter(venue=venue, status=CashShiftStatus.CLOSED).first()
        open_shift = CashShift.objects.filter(venue=venue, status=CashShiftStatus.OPEN).first()
        if closed is None or open_shift is None:
            raise CommandError("RESTORE_CASH_SHIFT_MISMATCH: both closed and open shift history are required.")
        position = cash_shift_position(closed)
        if position["expected_at_close_cents"] != 11_000 or position["discrepancy_cents"] != 0:
            raise CommandError("RESTORE_CASH_POSITION_MISMATCH: close snapshot was not preserved.")
        if closed.movements.count() < 4:
            raise CommandError("RESTORE_CASH_MOVEMENTS_MISSING: opening/payment/supply/withdrawal are incomplete.")

        occupancy = TableOccupancy.objects.filter(table__venue=venue, released_at__isnull=True).first()
        if occupancy is None or not GuestSession.objects.filter(occupancy=occupancy, revoked_at__isnull=True).exists():
            raise CommandError("RESTORE_OCCUPANCY_MISMATCH: active occupancy or guest session is absent.")
        if not DispatchTask.objects.filter(
            venue=venue, state=DispatchTaskState.DONE, order_item__order__tab=tab
        ).exists():
            raise CommandError("RESTORE_DELIVERY_MISMATCH: completed delivery history is absent.")

        self.stdout.write(
            self.style.SUCCESS(
                "RESTORE VERIFIED: exposure=0; refund/reversal linked; cash open+closed preserved; "
                "occupancy/guest session active; delivery history done."
            )
        )
