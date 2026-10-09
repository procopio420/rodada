"""Read-only persistence check for spec023-native-demo's disposable fixture.

Run with the separate cluster's PostgreSQL environment. No fixtures, SQL writes,
tokens, provider interaction, migrations or reset occur here.
"""
import json
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
assert os.environ.get('POSTGRES_DB') == 'rodada_demo'
assert os.environ.get('POSTGRES_HOST') == '127.0.0.1'
assert os.environ.get('POSTGRES_PORT') != '55459', 'Never inspect the preserved demo with this test gate'
sys.path.insert(0, str(root / 'apps/api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rodada_api.settings')
import django
django.setup()
from modules.ordering.models import Tab
from modules.cash.models import CashShift

out = root / 'docs/design/evidence/spec023-header/native'
nodes = json.loads((out / 'native-tab.json').read_text(encoding='utf-8'))
labels = [n['text'] for n in nodes if n['text'].startswith('Spec023 test ')]
assert len(labels) == 1
tab = Tab.objects.get(venue__slug='release-demo', display_label=labels[0])
payments = list(tab.payments.filter(status='CONFIRMED').values('amount_cents','method','status'))
charges = list(tab.charges.values_list('amount_cents',flat=True))
assert tab.state == 'CLOSED' and tab.closed_at is not None
assert tab.orders.count() == 1 and sum(charges) == 600
assert payments == [{'amount_cents':600,'method':'CASH','status':'CONFIRMED'}]
assert not tab.ledger_adjustments.exists()
payment = tab.payments.get(status='CONFIRMED')
assert not payment.refunds.exists() and not payment.provider_payment_id
assert payment.confirmed_at is not None and payment.received_by_id == tab.opened_by_id
shift = CashShift.objects.filter(venue=tab.venue, opening_float_cents=0).latest('opened_at')
assert shift.status == 'CLOSED' and shift.closed_at is not None
assert shift.expected_amount_cents_snapshot == shift.counted_amount_cents == 600
assert shift.discrepancy_cents == 0
result = {
    'passed':True, 'source':'read-only Django ORM on real isolated PostgreSQL',
    'native_android_ui':'RUN_API36', 'payment_classification':'MANUAL_TEST',
    'tab_id':str(tab.id), 'tab_state':tab.state, 'order_count':tab.orders.count(),
    'charges_cents':sum(charges), 'payments':payments,
    'open_exposure_cents':sum(charges)-sum(p['amount_cents'] for p in payments),
    'payment_actor_matches_tab_operator':True, 'payment_confirmation_timestamp_present':True,
    'shift_id':str(shift.id), 'shift_status':shift.status,
    'cash_expected_cents':shift.expected_amount_cents_snapshot,
    'cash_counted_cents':shift.counted_amount_cents,'cash_discrepancy_cents':shift.discrepancy_cents,
}
(out/'native-readback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
