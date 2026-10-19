"""Seed an isolated synthetic payment tenant in the allowlisted local test DB only."""
import json,os,secrets,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'apps/api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','rodada_api.settings')
import django;django.setup()
from django.db import connection,transaction
from django.utils import timezone
assert connection.settings_dict['NAME']=='rodada_android_post_drop'
assert connection.settings_dict['HOST']=='127.0.0.1' and connection.settings_dict['PORT']=='55501'
from modules.venue.models import Venue
from modules.access.models import StaffMember,VenueStaffMembership
from modules.catalog.models import Product
from modules.cash.models import CashPoint,CashShift
slug='spec033-native-autoclose-current';operator='spec033-native-autoclose-operator';config=Path('/tmp/spec033-native-autoclose-runner.json')
with transaction.atomic():
 venue,_=Venue.objects.get_or_create(slug=slug,defaults={'name':'Synthetic current-main payment test'})
 staff,created=StaffMember.objects.get_or_create(login_identifier=operator,defaults={'display_name':'Synthetic native payment operator'})
 if not created:raise SystemExit('Fixture already exists; reuse private config without rotating credentials')
 pin=f'{secrets.randbelow(1000000):06d}';staff.set_pin(pin);staff.save(update_fields=['pin_hash'])
 VenueStaffMembership.objects.create(venue=venue,staff_member=staff,role='MANAGER')
 Product.objects.create(venue=venue,name='Synthetic auto-close drink',price_cents=500,category='Bebidas',fulfillment_station='BAR')
 point=CashPoint.objects.create(venue=venue,label='Synthetic receipt drawer')
 CashShift.objects.create(venue=venue,cash_point=point,business_date=timezone.localdate(),opened_by=staff,opening_idempotency_key='spec033-native-autoclose-fixture')
 config.touch(mode=0o600,exist_ok=False);config.write_text(json.dumps({'venue':slug,'operator':operator,'testPin':pin}));config.chmod(0o600)
 print('PASS: dedicated synthetic payment tenant created; credentials written privately, no existing fixture changed.')
