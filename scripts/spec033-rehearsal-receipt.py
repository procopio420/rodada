"""Run the original E06 API rehearsal and retain only safe synthetic evidence."""
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")

import django

django.setup()

from django.db import connection
from django.test.runner import DiscoverRunner
from modules.dispatch.models import DispatchTask
from modules.hospitality.models import Table, TableOccupancy
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Order, OrderItem, Tab
from tests.test_spec033_integrated_rehearsal import IntegratedAttendanceRehearsal

receipt = {}


def rows(query, *fields):
    return list(query.order_by("id").values(*fields))


class EvidenceRehearsal(IntegratedAttendanceRehearsal):
    def tearDown(self):
        venue = self.venue
        receipt.update({
            "scope": "API/PostgreSQL; synthetic fixtures; no browser/device/PSP",
            "venue_id": venue.id,
            "postgresql_version": connection.pg_version,
            "tabs": rows(Tab.objects.filter(venue=venue), "id", "state", "version"),
            "orders": rows(Order.objects.filter(tab__venue=venue), "id", "tab_id", "status"),
            "items": rows(OrderItem.objects.filter(order__tab__venue=venue), "id", "order_id", "state", "fulfillment_station_snapshot"),
            "charges": rows(Charge.objects.filter(tab__venue=venue), "id", "tab_id", "amount_cents"),
            "payments": rows(Payment.objects.filter(tab__venue=venue), "id", "tab_id", "amount_cents", "status"),
            "tasks": rows(DispatchTask.objects.filter(venue=venue), "id", "order_item_id", "state", "completion_source"),
            "tables": rows(Table.objects.filter(venue=venue), "id", "status"),
            "occupancies": rows(TableOccupancy.objects.filter(table__venue=venue), "id", "table_id", "generation", "released_at"),
        })
        super().tearDown()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: spec033-rehearsal-receipt.py NEW_OUTPUT_JSON")
    output = Path(sys.argv[1])
    if output.exists():
        raise SystemExit("Output must be a new file")
    config = connection.settings_dict
    if (connection.vendor != "postgresql"
        or config["HOST"] not in ("127.0.0.1", "localhost", "::1")
        or config["NAME"] != "rodada033_evidence"
        or config.get("OPTIONS")
        or config.get("TEST", {}).get("NAME") not in (None, "test_rodada033_evidence")):
        raise SystemExit("Requires isolated loopback PostgreSQL database rodada033_evidence")
    result = DiscoverRunner(verbosity=1, interactive=False).run_tests(["__main__.EvidenceRehearsal"])
    if result:
        raise SystemExit(result)
    expected = {"tabs": 3, "orders": 3, "items": 6, "charges": 6, "payments": 6, "tasks": 6}
    if any(len(receipt.get(key, [])) != count for key, count in expected.items()):
        raise SystemExit("Receipt cardinality mismatch; no evidence published")
    states = {"tabs": "CLOSED", "items": "DELIVERED", "tasks": "DONE", "payments": "CONFIRMED"}
    if any(row["state" if key != "payments" else "status"] != state
           for key, state in states.items() for row in receipt[key]):
        raise SystemExit("Receipt terminal state mismatch; no evidence published")
    receipt.update({"result": "PASS", "python": platform.python_version(), "django": django.get_version(),
        "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip()})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        json.dump(receipt, stream, indent=2, default=str)
        stream.write("\n")
    print("PASS: synthetic rehearsal receipt saved")


if __name__ == "__main__":
    main()
