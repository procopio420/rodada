#!/usr/bin/env python3
"""Busy-shift verification through real HTTP on isolated release-demo fixtures.

No SQL writes, provider callbacks, mocks, actual settlement, or automatic retry.
Credentials remain in memory. The URL must be loopback; test identities must
already have been provisioned by seed_release_demo in a disposable database.
"""

import argparse
import json
import math
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def percentiles(values):
    ordered = sorted(values)
    if not ordered:
        return {"count": 0}
    return {"count": len(ordered), **{
        f"p{n}_ms": round(ordered[max(0, math.ceil(len(ordered) * n / 100) - 1)], 2)
        for n in (50, 95, 99)
    }, "max_ms": round(ordered[-1], 2)}


class Shift:
    def __init__(self, args):
        self.args = args
        self.run_id = "busy-" + uuid.uuid4().hex[:12]
        self.samples = []
        self.errors = []
        self.lock = threading.Lock()
        self.completed = []
        self.owner = None

    def api(self, path, body=None, token=None, operation=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        started = time.monotonic()
        status = 0
        try:
            req = Request(self.args.url.rstrip("/") + path,
                          data=json.dumps(body).encode() if body is not None else None,
                          headers=headers)
            try:
                response = urlopen(req, timeout=30)
            except HTTPError as error:
                response = error
            with response:
                status = response.status
                result = json.load(response)
            require(status in (200, 201, 202), f"{operation or path}: HTTP {status}, code={result.get('code', 'unknown')}")
            return result
        except Exception as error:
            with self.lock:
                self.errors.append({"operation": operation or path, "http_status": status,
                                    "error": str(error)[:240]})
            raise
        finally:
            with self.lock:
                self.samples.append({"operation": operation or path,
                                     "mutation": body is not None,
                                     "status": status,
                                     "ms": (time.monotonic() - started) * 1000})

    def login(self, identifier, pin):
        return self.api("/auth/login/", {"venue_slug": "release-demo",
            "login_identifier": identifier, "pin": pin,
            "installation_id": self.run_id + "-" + uuid.uuid4().hex,
            "platform": "ANDROID"}, operation="login")["access_token"]

    def report(self, day):
        return self.api(f"/management/reports/?start={day}&end={day}",
                        token=self.owner, operation="report")["totals"]

    def tab(self, index, staff, cashier, products):
        label = f"{self.run_id}-{index}"
        tab = self.api("/tabs/", {"display_label": label}, staff, "tab.open")
        tab_id = tab["id"]
        cart = {"idempotency_key": label + "-order", "lines": [
            {"product_id": products["BAR"], "quantity": 1},
            {"product_id": products["KITCHEN"], "quantity": 1}]}
        path = f"/tabs/{tab_id}/orders/confirm/"
        order = self.api(path, cart, staff, "order.confirm")
        replay = self.api(path, cart, staff, "order.exact_retry")
        require(order["id"] == replay["id"], "Duplicate canonical order")
        require(sum(i["line_total_cents"] for i in order["items"]) == 3200, "Order total differs from independent fixture arithmetic")
        for station in ("BAR", "KITCHEN"):
            queue = self.api(f"/production/{station}/", token=cashier, operation="production." + station)
            ids = {i["id"] for i in queue["results"]}
            item = next(i for i in order["items"] if i["product_id"] == products[station])
            require(item["id"] in ids, "Confirmed item absent from station queue")
            require(not any(i["product_id"] == products["KITCHEN" if station == "BAR" else "BAR"] for i in queue["results"]), "Cross-station routing error")
            for state in ("ACCEPTED", "PREPARING", "READY"):
                self.api(f"/order-items/{item['id']}/transition/", {"state": state}, cashier, "production." + state)
        queue = self.api("/dispatch/delivery/", token=cashier, operation="delivery.queue")["results"]
        for item in order["items"]:
            task = next(i for i in queue if i["order_item_id"] == item["id"])
            done = self.api(f"/dispatch/delivery/{task['id']}/complete/", {}, staff, "delivery.complete")
            require(done["state"] == "DONE", "Delivery not complete")
        for name, amount in (("partial", 1000), ("remaining", 2200)):
            body = {"amount_cents": amount, "method": "EXTERNAL_TERMINAL",
                    "idempotency_key": label + "-" + name}
            first = self.api(f"/tabs/{tab_id}/payments/", body, cashier, "payment.manual_test")
            again = self.api(f"/tabs/{tab_id}/payments/", body, cashier, "payment.exact_retry")
            require(first["id"] == again["id"], "Duplicate canonical payment")
            if name == "partial":
                detail = self.api(f"/tabs/{tab_id}/", token=staff, operation="tab.partial_balance")
                require(detail["exposure_cents"] == 2200, "Partial payment balance mismatch")
        self.api(f"/tabs/{tab_id}/close/", {}, cashier, "tab.close")
        detail = self.api(f"/tabs/{tab_id}/", token=staff, operation="tab.reconcile")
        require(detail["state"] == "CLOSED" and detail["exposure_cents"] == 0, "Tab not financially closed")
        require(detail["charges_cents"] == detail["payments_cents"] == 3200, "Canonical ledger differs from independent expected total")
        require(len(detail["orders"]) == 1 and len(detail["payments"]) == 2, "Duplicate persisted records")
        require(all(i["state"] == "DELIVERED" for i in detail["orders"][0]["items"]), "Fulfillment incomplete")
        with self.lock:
            self.completed.append(tab_id)

    def verify_persistence(self):
        evidence = json.loads(Path(self.args.evidence).read_text())
        require(evidence.get("passed"), "Original busy shift did not pass")
        started = time.monotonic()
        result = {"verified_at": datetime.now(timezone.utc).isoformat()}
        try:
            self.owner = self.login("release-owner", "2468")
            for tab_id in evidence["completed_tabs"]:
                detail = self.api(f"/tabs/{tab_id}/", token=self.owner, operation="restart.tab")
                require(detail["state"] == "CLOSED" and detail["exposure_cents"] == 0, "Closed tab lost across restart")
                require(detail["charges_cents"] == detail["payments_cents"] == 3200, "Restart ledger mismatch")
                require(len(detail["orders"]) == 1 and len(detail["payments"]) == 2, "Restart persisted duplicates")
                require(all(i["state"] == "DELIVERED" for i in detail["orders"][0]["items"]), "Restart fulfillment mismatch")
            report = self.report(evidence["business_date"])
            require(all(report[k] == evidence["report_after"][k] for k in evidence["expected_report_delta"]), "Restart report differs; isolate unrelated writes")
            result["passed"] = True
        except Exception as error:
            result.update({"passed": False, "failure": str(error)[:240]})
        result["seconds"] = round(time.monotonic() - started, 3)
        result["latency"] = percentiles([s["ms"] for s in self.samples])
        result["errors"] = self.errors
        result["boundary"] = "Canonical persistence readback only; caller must separately prove which real services were restarted."
        evidence["persistence_verification"] = result
        Path(self.args.evidence).write_text(json.dumps(evidence, indent=2) + "\n")
        print(json.dumps(result))
        return 0 if result["passed"] else 1

    def run(self):
        started = time.monotonic()
        evidence = {"run_id": self.run_id, "started_at": datetime.now(timezone.utc).isoformat(),
            "url": self.args.url, "workers": self.args.workers, "requested_tabs": self.args.tabs,
            "payment_classification": "MANUAL_TEST_EXTERNAL_TERMINAL_NO_PROVIDER_SETTLEMENT",
            "native_android_ui": "NOT_RUN_HTTP_PROTOCOL_ONLY", "mocked_calls": 0}
        try:
            self.owner = self.login("release-owner", "2468")
            day = self.api("/management/calendar/", token=self.owner, operation="calendar")["business_date"]
            evidence["business_date"] = day
            before = self.report(day)
            products = {}
            for station, price in (("BAR", 1200), ("KITCHEN", 2000)):
                products[station] = self.api("/catalog/resolve-or-create/", {
                    "name": self.run_id + " " + station, "price_cents": price,
                    "fulfillment_station": station}, self.owner, "fixture.product")["product"]["id"]
            clients = [(self.login("release-staff", "1357"), self.login("release-owner", "2468"))
                       for _ in range(self.args.workers)]
            load_start = time.monotonic()
            failures = []
            with ThreadPoolExecutor(max_workers=self.args.workers) as pool:
                futures = [pool.submit(self.tab, i, *clients[i % len(clients)], products)
                           for i in range(self.args.tabs)]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as error:
                        failures.append(str(error)[:240])
            evidence["workload_seconds"] = round(time.monotonic() - load_start, 3)
            evidence["workflow_failures"] = failures
            after = self.report(day)
            expected_amount = self.args.tabs * 3200
            expected = {"gross_cents": expected_amount, "paid_cents": expected_amount,
                "adjustments_cents": 0, "refunds_cents": 0, "net_received_cents": expected_amount,
                "current_open_exposure_cents": 0, "current_open_tabs": 0}
            evidence["report_before"] = before
            evidence["report_after"] = after
            evidence["expected_report_delta"] = expected
            evidence["actual_report_delta"] = {key: after[key] - before[key] for key in expected}
            require(not failures, "One or more busy-shift workflows failed; incomplete tabs remain for inspection")
            require(evidence["actual_report_delta"] == expected, "Independent report reconciliation failed; concurrent unrelated traffic also invalidates isolation")
            require(len(self.completed) == self.args.tabs, "Completed tab count mismatch")
            evidence["passed"] = True
        except Exception as error:
            evidence["passed"] = False
            evidence["failure"] = str(error)[:240]
        finally:
            evidence["completed_tabs"] = self.completed
            evidence["total_seconds"] = round(time.monotonic() - started, 3)
            evidence["http_errors"] = self.errors
            evidence["request_count"] = len(self.samples)
            evidence["mutation_count"] = sum(s["mutation"] for s in self.samples)
            evidence["latency"] = percentiles([s["ms"] for s in self.samples])
            evidence["latency_by_operation"] = {op: percentiles([s["ms"] for s in self.samples if s["operation"] == op]) for op in sorted({s["operation"] for s in self.samples})}
            evidence["latency_budget"] = "No pre-agreed busy-shift latency SLA; measurements do not imply SLA approval. Any HTTP/invariant failure fails this harness."
            evidence["http_requests_per_second"] = round(len(self.samples) / evidence["total_seconds"], 2)
            Path(self.args.evidence).write_text(json.dumps(evidence, indent=2) + "\n")
            print(json.dumps({k: evidence[k] for k in ("passed", "request_count", "mutation_count", "latency", "total_seconds")}))
        return 0 if evidence["passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:18766")
    parser.add_argument("--evidence", default="/tmp/rodada-release-busy-shift.json")
    parser.add_argument("--verify", action="store_true", help="Read back recorded tabs/report after separately evidenced service/database restart")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--tabs", type=int, default=64)
    args = parser.parse_args()
    require(urlparse(args.url).hostname in {"127.0.0.1", "localhost", "::1"}, "Only isolated loopback release fixtures are allowed")
    require(args.workers >= 8 and args.tabs >= 64, "Busy-shift evidence requires at least 8 clients and 64 Tabs")
    shift = Shift(args)
    return shift.verify_persistence() if args.verify else shift.run()


if __name__ == "__main__":
    raise SystemExit(main())
