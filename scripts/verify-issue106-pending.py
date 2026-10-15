#!/usr/bin/env python3
"""Read-only PostgreSQL proof: an unconfirmed fixture payment has no money effects."""
import json
import os
from pathlib import Path
import subprocess
from cross_surface_fixture import require_disposable_database, require_connected_database, database_instance_identity
require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from django.db import connection
from modules.ordering.models import Tab, Order
from modules.ledger.models import Payment, Charge
from modules.cash.models import CashMovement
from modules.payment_provider.models import PaymentAttempt
require_connected_database(connection)
f = json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
r = json.loads(Path("artifacts/pending-payment-browser.json").read_text())
assert r["sha"] == subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
assert r["database_instance_id"] == f["database_instance_id"] == database_instance_identity(connection)
tab = Tab.objects.get(pk=f["pending_tab_id"], venue_id=f["venue_id"], state="OPEN")
payment = Payment.objects.get(pk=f["pending_payment_id"], tab=tab, status="PENDING")
assert payment.confirmed_at is None and not payment.provider and not payment.provider_payment_id
assert payment.metadata["test_only"] is True
assert Payment.objects.filter(tab=tab).count() == 1
assert not Order.objects.filter(tab=tab).exists() and not Charge.objects.filter(tab=tab).exists()
assert not CashMovement.objects.filter(payment=payment).exists()
assert not PaymentAttempt.objects.filter(payment=payment).exists()
r.update(sql_independent=True, orders=0, charges=0, confirmed_payments=0, cash_movements=0, provider_attempts=0)
Path("artifacts/pending-payment-sql.json").write_text(json.dumps(r,indent=2)+"\n")
print("PASS: PENDING preserved, Tab OPEN, no confirmed money/cash/provider attempt")
