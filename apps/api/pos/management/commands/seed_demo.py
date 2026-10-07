from django.core.management.base import BaseCommand
from cash.models import CashShift
from catalog.models import Product
from catalog.services import create_canonical_item, generate_pending_icons
from pos.models import PhysicalTable, ServicePoint, StaffMember, TableAccessToken, Venue, Zone
from customers.models import Customer, Relationship, VenueRelationshipPolicy
from customers.services import DEFAULT_LIMITS


class Command(BaseCommand):
    help = "Create deterministic Bar do Aderlan demo data. Safe to run repeatedly."

    def handle(self, *args, **options):
        venue, _ = Venue.objects.get_or_create(name="Bar do Aderlan")
        manager, _ = StaffMember.objects.get_or_create(venue=venue, display_name="Ana Gerente", defaults={"role": StaffMember.Role.MANAGER})
        bia, _ = StaffMember.objects.get_or_create(venue=venue, display_name="Bia Staff", defaults={"role": StaffMember.Role.STAFF})
        # Local demo-only PINs. They are deliberately documented, never production credentials.
        for staff, pin in ((manager, "0420"), (bia, "1234")):
            staff.set_pin(pin)
            staff.save(update_fields=["pin_hash"])
        zones = {name: Zone.objects.get_or_create(venue=venue, name=name)[0] for name in ["Rua", "Calçada", "Bar principal"]}
        for code, zone in [("P37", "Rua"), ("P41", "Calçada"), ("P44", "Bar principal")]:
            ServicePoint.objects.get_or_create(venue=venue, code=code, defaults={"zone": zones[zone]})
        for label, zone, x, y, temporary in [("Mesa 1", "Rua", 22, 25, False), ("Mesa 2", "Rua", 65, 22, False), ("Balcão", "Bar principal", 45, 68, False), ("Extra A", "Calçada", 76, 72, True)]:
            table, _ = PhysicalTable.objects.get_or_create(venue=venue, label=label, defaults={"zone": zones[zone], "x": x, "y": y, "is_temporary": temporary})
            TableAccessToken.objects.get_or_create(table=table)
        for relationship_status, limit in DEFAULT_LIMITS.items():
            VenueRelationshipPolicy.objects.update_or_create(venue=venue, status=relationship_status, defaults={"operating_limit_cents": limit})
        customer, _ = Customer.objects.get_or_create(display_name="João da Oficina", defaults={"phone": "11999990000"})
        Relationship.objects.update_or_create(customer=customer, venue=venue, defaults={"status": Relationship.Status.HOUSE, "nickname": "João"})
        products = [("Brahma 600ml", 1200, "BAR"), ("Heineken", 1400, "BAR"), ("Coca-Cola", 700, "BAR"), ("Fritas", 2800, "KITCHEN"), ("Caipirinha", 1800, "BAR")]
        for name, price, station in products:
            canonical, _ = create_canonical_item(name)
            Product.objects.update_or_create(venue=venue, name=name, defaults={"canonical_item": canonical, "current_price_cents": price, "fulfillment_station": station, "active": True, "available": True})
        generate_pending_icons()
        CashShift.objects.get_or_create(venue=venue, closed_at__isnull=True, defaults={"opened_by": manager, "opening_float_cents": 20000})
        self.stdout.write(self.style.SUCCESS("Demo ready: Bar do Aderlan (venue id %s; Ana Gerente/0420, Bia Staff/1234)." % venue.id))
