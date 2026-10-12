from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from modules.access.models import StaffMember, StaffSession, VenueStaffMembership
from modules.access.context import ActorContext
from modules.venue.models import Venue
from modules.catalog.models import Product
from modules.ordering.models import Tab, Order, OrderItem
from modules.dispatch.models import DispatchTask
from modules.ledger.models import Charge, Payment, LedgerAdjustment
from modules.ledger.services import exposure_cents
from modules.ordering.local_test_reset import reset_test_tabs


class LocalResetTests(TestCase):
    def setUp(self):
        venue=Venue.objects.create(name="Local reset test",slug="local-reset-test")
        staff=StaffMember.objects.create(display_name="Test owner",login_identifier="local-reset-owner")
        member=VenueStaffMembership.objects.create(venue=venue,staff_member=staff,role="OWNER")
        session=StaffSession.objects.create(venue=venue,staff_member=staff,membership=member,expires_at=timezone.now()+timedelta(hours=1))
        self.actor=ActorContext.from_session(session)
        self.tab=Tab.objects.create(venue=venue,opened_by=staff)
        product=Product.objects.create(venue=venue,name="Test item",price_cents=1000,fulfillment_station="BAR")
        order=Order.objects.create(tab=self.tab,source="STAFF")
        self.item=OrderItem.objects.create(order=order,product=product,product_name_snapshot=product.name,unit_price_cents=1000,quantity=1,state="READY",ready_at=timezone.now())
        Charge.objects.create(tab=self.tab,order_item=self.item,amount_cents=1000)
        self.task=DispatchTask.objects.create(venue=venue,task_type="DELIVERY",order_item=self.item,state="OPEN")
        self.payment=Payment.objects.create(received_by=staff,confirmed_at=timezone.now(),tab=self.tab,amount_cents=300,method="CASH",status="CONFIRMED",idempotency_key="partial-reset-test")

    def test_partial_test_balance_is_waived_once_without_payment_or_snapshot_changes(self):
        payments=list(Payment.objects.values())
        original=(self.item.product_name_snapshot,self.item.unit_price_cents,self.item.ready_at)
        result=reset_test_tabs(tab_ids=[self.tab.pk],actor=self.actor)
        assert result[0]["waived_cents"]==700
        self.tab.refresh_from_db(); self.item.refresh_from_db(); self.task.refresh_from_db()
        assert self.tab.state=="CLOSED" and exposure_cents(self.tab)==0
        assert self.item.state=="CANCELLED" and self.task.state=="CANCELLED"
        assert original==(self.item.product_name_snapshot,self.item.unit_price_cents,self.item.ready_at)
        assert list(Payment.objects.values())==payments
        reset_test_tabs(tab_ids=[self.tab.pk],actor=self.actor)
        assert LedgerAdjustment.objects.filter(reason_code="LOCAL_TEST_RESET").count()==1

    def test_pending_payment_rolls_back_and_foreign_venue_is_rejected(self):
        self.payment.status="PROCESSING";self.payment.save(update_fields=["status"])
        with self.assertRaises(ValueError): reset_test_tabs(tab_ids=[self.tab.pk],actor=self.actor)
        assert not LedgerAdjustment.objects.exists()
        self.item.refresh_from_db();assert self.item.state=="READY"
        other=Venue.objects.create(name="Other",slug="local-reset-other")
        tab=Tab.objects.create(venue=other)
        with self.assertRaises(ValueError): reset_test_tabs(tab_ids=[tab.pk],actor=self.actor)
