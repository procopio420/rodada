"""Private read-only Gate3 business baseline; publish equality only, never digests/rows."""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

if not __debug__:
    raise RuntimeError("Operational guards require Python assertions")
assert os.getenv("RAILWAY_GIT_COMMIT_SHA") == "c589ff0862b1a7702e12c20a00cffda6cb2f289e"
os.chdir("/app/apps/api")
sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django

django.setup()
from django.db import connection, transaction
from modules.cash.models import CashMovement, CashPoint, CashShift, CashTenderDetail
from modules.catalog.models import Product
from modules.guest_access.models import CustomerAuthSession, CustomerCredential
from modules.hospitality.models import (
    Table,
    TableGroup,
    TableGroupMembership,
    TableOccupancy,
    TabOccupancyAssignment,
)
from modules.house_account.models import Customer, Relationship
from modules.ledger.models import Charge, LedgerAdjustment, Payment, Refund
from modules.ordering.models import Order, OrderItem, Tab
from modules.venue.models import Venue, VenueDomain

slugs = ["spec025-qa-a", "spec025-qa-b"]
qa_customers = (
    Customer.objects.filter(
        pk__in=Relationship.objects.filter(venue__slug__in=slugs).values("customer_id")
    )
    .exclude(
        pk__in=Relationship.objects.exclude(venue__slug__in=slugs).values("customer_id")
    )
    .values("pk")
)
qs = [
    Venue.objects.exclude(slug__in=slugs),
    VenueDomain.objects.exclude(venue__slug__in=slugs),
    Tab.objects.exclude(venue__slug__in=slugs),
    Order.objects.exclude(tab__venue__slug__in=slugs),
    OrderItem.objects.exclude(order__tab__venue__slug__in=slugs),
    Charge.objects.exclude(tab__venue__slug__in=slugs),
    Payment.objects.exclude(tab__venue__slug__in=slugs),
    Refund.objects.exclude(payment__tab__venue__slug__in=slugs),
    LedgerAdjustment.objects.exclude(tab__venue__slug__in=slugs),
    Product.objects.exclude(venue__slug__in=slugs),
    Table.objects.exclude(venue__slug__in=slugs),
    TableOccupancy.objects.exclude(table__venue__slug__in=slugs),
    TabOccupancyAssignment.objects.exclude(tab__venue__slug__in=slugs),
    TableGroup.objects.exclude(venue__slug__in=slugs),
    TableGroupMembership.objects.exclude(group__venue__slug__in=slugs),
]
qs += [
    Customer.objects.exclude(pk__in=qa_customers),
    Relationship.objects.exclude(venue__slug__in=slugs),
    CustomerCredential.objects.exclude(customer_id__in=qa_customers),
    CustomerAuthSession.objects.exclude(venue__slug__in=slugs),
]
qs += [
    CashPoint.objects.exclude(venue__slug__in=slugs),
    CashShift.objects.exclude(venue__slug__in=slugs),
    CashMovement.objects.exclude(shift__venue__slug__in=slugs),
    CashTenderDetail.objects.exclude(payment__tab__venue__slug__in=slugs),
]
out = {}
with transaction.atomic(), connection.cursor() as c:
    c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    c.execute("SET LOCAL statement_timeout='15s'")
    for q in qs:
        sql, params = q.query.sql_with_params()
        c.execute("SELECT to_jsonb(t)::text FROM (" + sql + ") t", params)
        hashes = sorted(
            hashlib.sha256(row[0].encode()).digest() for row in c.fetchall()
        )
        out[q.model._meta.db_table] = hashlib.sha256(b"".join(hashes)).hexdigest()
print(
    json.dumps(
        {
            "sha": os.getenv("RAILWAY_GIT_COMMIT_SHA"),
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "foreign_table_fingerprints": out,
        }
    )
)
