#!/usr/bin/env python3
"""Prepare an isolated real PostgreSQL fixture and prove exactly-once semantics."""
import argparse
import json
import os
import subprocess
from pathlib import Path

from cross_surface_fixture import (
    require_connected_database,
    require_disposable_database,
    require_fixture_order,
    database_instance_identity,
)

require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django

django.setup()
from django.db import connection

require_connected_database(connection)

from modules.access.models import StaffMember, VenueStaffMembership
from modules.catalog.models import Product
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Order, OrderItem
from modules.venue.models import Venue


def prepare(path):
    if Venue.objects.filter(slug="android-post-drop-ci").exists():
        raise SystemExit("Refusing to overwrite a pre-existing test Venue")
    venue = Venue.objects.create(
        name="Isolated Android POST Drop CI", slug="android-post-drop-ci",
        timezone="America/Sao_Paulo", business_day_cutoff_hour=4, table_service_enabled=True
    )
    staff = StaffMember(display_name="Android Fault Test", login_identifier="android-post-drop-operator")
    staff.set_pin("2468")  # disposable CI fixture, no live staff or merchant
    staff.save()
    VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role="MANAGER")
    product = Product.objects.create(
        venue=venue, name="Android Post Drop Test Soda",
        price_cents=700, fulfillment_station="BAR", active=True
    )
    from modules.cash.models import CashPoint
    cash_point = CashPoint.objects.create(venue=venue, label="Issue106 disposable drawer")
    kitchen_product = Product.objects.create(venue=venue, name="Android Compose Test Meal", price_cents=1000, fulfillment_station="KITCHEN", active=True)
    from modules.hospitality.models import Table
    table = Table.objects.create(venue=venue, label="Fault 027", guest_ordering_mode="DIRECT")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"venue_id": str(venue.pk), "database": connection.settings_dict["NAME"],
                                "database_instance_id": database_instance_identity(connection),
                                "table_id": str(table.pk), "product_id": str(product.pk),
                                "kitchen_product_id": str(kitchen_product.pk), "cash_point_id": str(cash_point.pk),
                                "venue_slug": venue.slug, "price_cents": 700}))
    print("PASS: disposable PostgreSQL venue, staff and product created", flush=True)


def extend_resilience(path):
    """Extend this exact disposable fixture; never seed a second backend."""
    from cross_surface_fixture import VENUE_SLUG
    from modules.hospitality.models import Table, TableOccupancy
    from modules.house_account.services import snapshot
    from modules.ordering.models import Tab
    data = json.loads(path.read_text())
    assert data["database_instance_id"] == database_instance_identity(connection)
    assert data["database"] == connection.settings_dict["NAME"]
    venue = Venue.objects.get(pk=data["venue_id"], slug=VENUE_SLUG)
    if "race_tables" in data:
        raise SystemExit("Refusing to overwrite an existing resilience fixture")
    other = StaffMember(display_name="Concurrent Fixture Staff", login_identifier="android-post-drop-other")
    other.set_pin("2468")
    other.save()
    VenueStaffMembership.objects.create(venue=venue, staff_member=other, role="STAFF")
    tables = {kind: Table.objects.create(venue=venue, label=f"Race {kind}", guest_ordering_mode="DIRECT") for kind in ("start", "claim", "release")}
    tables["claim"].status = "OCCUPIED"
    tables["claim"].save()
    claim_visit = TableOccupancy.objects.create(table=tables["claim"], generation=1)
    foreign = Venue.objects.create(name="Isolated foreign control", slug="android-post-drop-foreign-ci", table_service_enabled=True)
    foreign_staff = StaffMember(display_name="Foreign Fixture Staff", login_identifier="android-post-drop-foreign-operator")
    foreign_staff.set_pin("2468")
    foreign_staff.save()
    VenueStaffMembership.objects.create(venue=foreign, staff_member=foreign_staff, role="MANAGER")
    foreign_product = Product.objects.create(venue=foreign, name="Foreign control item", price_cents=300, fulfillment_station="BAR")
    foreign_tab = Tab.objects.create(venue=foreign, display_label="Foreign control Tab", **snapshot(foreign.pk))
    # Only local Host headers use these records; no DNS/hosting/provider operation occurs.
    from modules.venue.models import VenueDomain
    hosts = {"a":"issue106a-ci.rodada.bar", "b":"issue106b-ci.rodada.bar"}
    for host, owner in ((hosts["a"],venue),(hosts["b"],foreign)):
        VenueDomain.objects.create(hostname=host,venue=owner,is_active=True,is_verified=True)
    data.update(local_tenant_hosts=hosts, other_staff_id=str(other.pk), race_tables={k:str(t.pk) for k,t in tables.items()},
                claim_occupancy_id=str(claim_visit.pk), foreign_venue_id=str(foreign.pk),
                foreign_tab_id=str(foreign_tab.pk), foreign_product_id=str(foreign_product.pk))
    path.write_text(json.dumps(data, indent=2) + "\n")
    print("PASS: extended only the same guarded cluster/Venue with concurrency and foreign control fixtures")


def prepare_pending(path):
    """Controlled unconfirmed model state; no PSP adapter or external payment call."""
    from modules.house_account.services import snapshot
    from modules.ordering.models import Tab
    from modules.ledger.models import PaymentMethod, PaymentStatus
    data = json.loads(path.read_text())
    assert data["database_instance_id"] == database_instance_identity(connection)
    venue = Venue.objects.get(pk=data["venue_id"], slug="android-post-drop-ci")
    if "pending_tab_id" in data:
        raise SystemExit("Refusing to overwrite pending-control evidence")
    tab = Tab.objects.create(venue=venue, display_label="Issue106 controlled PENDING no PSP", **snapshot(venue.pk))
    payment = Payment.objects.create(tab=tab, amount_cents=700, method=PaymentMethod.OTHER,
        idempotency_key="issue106-controlled-pending", status=PaymentStatus.PENDING,
        received_by=StaffMember.objects.get(login_identifier="android-post-drop-operator"),
        metadata={"test_only":True,"fixture":"controlled-unconfirmed-state-no-PSP"})
    data.update(pending_tab_id=str(tab.pk), pending_payment_id=str(payment.pk))
    path.write_text(json.dumps(data, indent=2)+"\n")
    print("Prepared explicit unconfirmed fixture state only; no provider or settlement")


def verify(stage, marker, fixture, receipt):
    evidence = json.loads(marker.read_text())
    events = evidence["events"]
    assert events, "No successful upstream order response was dropped"
    assert events[0]["upstream_status"] == 201, events
    assert all(event["upstream_status"] in (200, 201) for event in events)
    assert len({event["idempotency_key"] for event in events}) == 1, "Different key across retransmissions"
    assert len({event["body_sha256"] for event in events}) == 1, "Payload changed across retransmissions"
    assert len({event["order_id"] for event in events}) == 1, "Different order across retransmissions"
    assert len({event["tab_id"] for event in events}) == 1
    first = events[0]
    order = Order.objects.get(pk=first["order_id"])
    fixture_data = json.loads(fixture.read_text())
    assert fixture_data["database"] == connection.settings_dict["NAME"], "fixture from another database"
    assert fixture_data["database_instance_id"] == database_instance_identity(connection)
    require_fixture_order(order, fixture_data)
    assert str(order.tab_id) == first["tab_id"]
    assert order.idempotency_key == first["idempotency_key"]
    assert Order.objects.filter(tab_id=order.tab_id).count() == 1, "DUPLICATED ORDER"
    items = OrderItem.objects.filter(order=order)
    assert items.count() == 1, "Duplicated order item"
    item = items.get()
    product_id = json.loads(fixture.read_text())["product_id"]
    assert str(item.product_id) == product_id
    assert item.quantity == 1
    assert Charge.objects.filter(tab=order.tab).count() == 1, "DUPLICATED LEDGER CHARGE"
    assert Charge.objects.get(tab=order.tab).amount_cents == 700
    assert Payment.objects.filter(tab=order.tab).count() == 0, "Unexpected payment operation"
    assert evidence["armed"] == (stage == "before"), "Fault was not disarmed at expected stage"
    replays = evidence.get("replays", [])
    if stage == "before":
        assert not replays, "Healthy replay occurred before explicit reconnect"
    else:
        assert len(replays) == 1, "Expected one and only one recovered HTTP POST"
        replay = replays[0]
        assert replay["upstream_status"] == 200, "Recovery did not receive idempotent HTTP 200"
        for field in ("order_id", "tab_id", "idempotency_key", "body_sha256"):
            assert replay[field] == first[field], f"Recovered POST changed {field}"
    summary = {
        "sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "database": connection.settings_dict["NAME"],
        "database_instance_id": fixture_data["database_instance_id"],
        "venue_id": str(order.tab.venue_id),
        "venue_slug": order.tab.venue.slug,
        "scenario": (
            "real_android_post_server_commit_held_response_uplink_cut"
            if evidence.get("hold_response")
            else "real_android_post_server_commit_tcp_reset"
        ),
        "hold_response": bool(evidence.get("hold_response")),
        "released_after_cut": bool(evidence.get("released_after_cut")),
        "phase": stage,
        "disconnected_responses": len(events),
        "recovery_http_status": replays[0]["upstream_status"] if replays else None,
        "recovery_post_count": len(replays),
        "original_order_id": str(order.pk),
        "original_tab_id": str(order.tab_id),
        "orders": 1, "order_items": 1, "charges": 1, "payments": 0,
        "original_key_preserved": True,
        "all_dropped_requests_identical": True,
        "result": "PASS"
    }
    if stage == "after":
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"PASS {stage}: real PostgreSQL Order=1 Item=1 Charge=1 Payment=0 "
          f"dropped_responses={len(events)} id={str(order.pk)[:8]}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "prepare-resilience", "prepare-pending", "before", "after"))
    parser.add_argument("--fixture", type=Path, default=Path("/tmp/rodada-android-live-fixture.json"))
    parser.add_argument("--marker", type=Path, default=Path("/tmp/rodada-android-live-drop.json"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/android-real-post-drop.json"))
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.fixture)
    elif args.action == "prepare-resilience":
        extend_resilience(args.fixture)
    elif args.action == "prepare-pending":
        prepare_pending(args.fixture)
    else:
        verify(args.action, args.marker, args.fixture, args.receipt)


if __name__ == "__main__":
    main()
