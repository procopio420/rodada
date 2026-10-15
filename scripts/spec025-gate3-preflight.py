"""Private runtime read-only Gate3 inventory; emits counts, never credentials/rows."""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

if not __debug__:
    raise RuntimeError("Operational guards require Python assertions")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--expected-sha", required=True)
args = parser.parse_args()
assert os.environ.get("RAILWAY_GIT_COMMIT_SHA") == args.expected_sha
os.chdir("/app/apps/api")
sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django

django.setup()
from django.db import connection, transaction
from django.db.models import Count, F, Q
from modules.access.models import StaffSession, VenueStaffMembership
from modules.guest_access.models import GuestSession
from modules.ledger.models import Charge, Payment, PaymentMethod, PaymentStatus, Refund
from modules.ordering.models import Order
from modules.venue.models import Venue, VenueDomain

secret = os.environ.get("RODADA_BFF_HOST_SECRET", "")
result = {
    "observed_at": datetime.now(timezone.utc).isoformat(),
    "sha": os.environ.get("RAILWAY_GIT_COMMIT_SHA"),
    "deployment": os.environ.get("RAILWAY_DEPLOYMENT_ID"),
    "seed_off": os.environ.get("RODADA_DEMO_SEED_ON_START", "").lower() == "false",
    "tenant_ui_flag_off": os.environ.get("RODADA_ENABLE_TENANT_HOST_UI", "").lower()
    == "false",
    "hmac_present": bool(secret),
    "hmac_minimum_policy_valid": len(secret) >= 32 and len(set(secret)) >= 5,
    "hmac_distinct_from_django_secret": bool(secret)
    and secret != os.environ.get("DJANGO_SECRET_KEY"),
    "cash_scope": "Read-only historical counts; no amounts, payment IDs or customer data. Confirmed-money statuses include refunded/partially-refunded payments. No repair.",
}
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        cursor.execute("SET LOCAL statement_timeout='15s'")
        cursor.execute("SET LOCAL lock_timeout='2s'")
        cursor.execute(
            "SELECT current_setting('transaction_read_only'), current_setting('server_version')"
        )
        readonly, version = cursor.fetchone()
        result.update(transaction_read_only=readonly == "on", postgres_version=version)
        result["current_table_count"] = len(
            connection.introspection.table_names(cursor)
        )
    qa_ids = list(
        Venue.objects.filter(slug__in=["spec025-qa-a", "spec025-qa-b"]).values_list(
            "pk", flat=True
        )
    )
    result["qa"] = []
    for slug, host in [
        ("spec025-qa-a", "e2ea.rodada.bar"),
        ("spec025-qa-b", "e2eb.rodada.bar"),
    ]:
        venue = Venue.objects.get(slug=slug)
        domain = VenueDomain.objects.get(hostname=host)
        result["qa"].append(
            {
                "host": host,
                "owner_matches": domain.venue_id == venue.pk,
                "domain_active": domain.is_active,
                "domain_verified": domain.is_verified,
                "guest_blocked": venue.guest_mutations_blocked,
                "active_memberships": VenueStaffMembership.objects.filter(
                    venue=venue, status="ACTIVE"
                ).count(),
                "unrevoked_staff_sessions": StaffSession.objects.filter(
                    venue=venue, revoked_at__isnull=True
                ).count(),
                "unrevoked_guest_sessions": GuestSession.objects.filter(
                    table__venue=venue, revoked_at__isnull=True
                ).count(),
            }
        )
    result["qa_financial_counts"] = {
        "orders": Order.objects.filter(tab__venue_id__in=qa_ids).count(),
        "charges": Charge.objects.filter(tab__venue_id__in=qa_ids).count(),
        "payments": Payment.objects.filter(tab__venue_id__in=qa_ids).count(),
        "refunds": Refund.objects.filter(payment__tab__venue_id__in=qa_ids).count(),
    }
    venue_labels = {
        v.pk: {
            "bar-do-aderlan": "pilot_aderlan",
            "spec025-qa-a": "qa_a",
            "spec025-qa-b": "qa_b",
        }.get(v.slug, "venue_" + hashlib.sha256(str(v.pk).encode()).hexdigest()[:12])
        for v in Venue.objects.all()
    }
    rows = (
        Payment.objects.filter(
            method=PaymentMethod.CASH, status__in=PaymentStatus.confirmed_money_values()
        )
        .values("tab__venue_id")
        .annotate(
            confirmed_money_count=Count("pk"),
            confirmed_only_count=Count("pk", filter=Q(status=PaymentStatus.CONFIRMED)),
            missing_movement_count=Count("pk", filter=Q(cash_movement__isnull=True)),
            foreign_movement_venue_count=Count(
                "pk",
                filter=Q(cash_movement__isnull=False)
                & ~Q(cash_movement__shift__venue_id=F("tab__venue_id")),
            ),
            unexpected_movement_kind_count=Count(
                "pk",
                filter=Q(cash_movement__isnull=False)
                & ~Q(cash_movement__kind="CASH_PAYMENT"),
            ),
        )
    )
    result["historical_cash_by_venue"] = [
        {"venue": venue_labels[row.pop("tab__venue_id")], **row} for row in rows
    ]
    result["historical_cash_gap_count"] = sum(
        row["missing_movement_count"] for row in result["historical_cash_by_venue"]
    )
    result["financial_inspection_completed"] = True
    result["historical_reconciliation_not_performed"] = True
print(json.dumps(result))
