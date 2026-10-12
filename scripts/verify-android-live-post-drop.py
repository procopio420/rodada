#!/usr/bin/env python3
"""Prepare an isolated real PostgreSQL fixture and prove exactly-once semantics."""
import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()

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
        timezone="America/Sao_Paulo", business_day_cutoff_hour=4
    )
    staff = StaffMember(display_name="Android Fault Test", login_identifier="android-post-drop-operator")
    staff.set_pin("2468")  # disposable CI fixture, no live staff or merchant
    staff.save()
    VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role="MANAGER")
    product = Product.objects.create(
        venue=venue, name="Android Post Drop Test Soda",
        price_cents=700, fulfillment_station="BAR", active=True
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"product_id": str(product.pk),
                                "venue_slug": venue.slug, "price_cents": 700}))
    print("PASS: disposable PostgreSQL venue, staff and product created", flush=True)


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
    parser.add_argument("action", choices=("prepare", "before", "after"))
    parser.add_argument("--fixture", type=Path, default=Path("/tmp/rodada-android-live-fixture.json"))
    parser.add_argument("--marker", type=Path, default=Path("/tmp/rodada-android-live-drop.json"))
    parser.add_argument("--receipt", type=Path, default=Path("artifacts/android-real-post-drop.json"))
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.fixture)
    else:
        verify(args.action, args.marker, args.fixture, args.receipt)


if __name__ == "__main__":
    main()
