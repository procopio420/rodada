#!/usr/bin/env python3
"""Seed only the dedicated Spec033 shell tenant in the allowlisted local test DB."""
import os,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','rodada_api.settings')
import django;django.setup()
from django.db import connection,transaction
assert connection.settings_dict['NAME']=='rodada_android_post_drop'
assert connection.settings_dict['HOST']=='127.0.0.1' and connection.settings_dict['PORT']=='55501'
from modules.venue.models import Venue
from modules.access.models import StaffMember,VenueStaffMembership
from modules.access.context import ActorContext
from modules.catalog.models import Product
from modules.ordering.models import Tab
from modules.ordering.services import confirm_order
from modules.hospitality.models import Table,Zone
from modules.hospitality.services import occupy_table
with transaction.atomic():
 v,created=Venue.objects.get_or_create(slug='spec033-native-shell-parity',defaults={'name':'Bar do Zé','table_service_enabled':True})
 if not v.table_service_enabled:
  v.table_service_enabled=True;v.save(update_fields=['table_service_enabled'])
 staff=StaffMember.objects.get(login_identifier='android-post-drop-operator')
 VenueStaffMembership.objects.get_or_create(venue=v,staff_member=staff,defaults={'role':'MANAGER'})
 web_staff,web_created=StaffMember.objects.get_or_create(login_identifier='spec033-web-shell-operator',defaults={'display_name':'Lucas'})
 if web_created:
  web_staff.set_pin('2468');web_staff.save(update_fields=['pin_hash'])
 VenueStaffMembership.objects.get_or_create(venue=v,staff_member=web_staff,defaults={'role':'MANAGER'})
 a=ActorContext(v.id,staff.id,None,None)
 products=[]
 for name,price,cat in [('Chopp Pilsen',1400,'Bebidas'),('Água sem gás',600,'Bebidas'),('Refrigerante lata',800,'Bebidas'),('Suco de laranja',1200,'Bebidas'),('Batata frita',2800,'Porções'),('Polenta frita',2600,'Porções'),('Pastel de queijo',1600,'Porções'),('Hambúrguer da casa',3400,'Lanches')]:
  p,_=Product.objects.get_or_create(venue=v,name=name,defaults={'price_cents':price,'category':cat,'fulfillment_station':'BAR' if cat=='Bebidas' else 'KITCHEN'})
  products.append(p)
 t,_=Table.objects.get_or_create(venue=v,label='08')
 tab=Tab.objects.filter(venue=v,display_label='Marina').first()
 if tab is None:
  tab=Tab.objects.create(venue=v,display_label='Marina',operating_limit_cents=20000,relationship_snapshot='REGULAR',opened_by=staff)
  occupy_table(table_id=t.pk,actor=a,tab_id=tab.pk)
  confirm_order(tab_id=tab.pk,source='STAFF',actor=a,idempotency_key='spec033-shell-seed56',lines=[{'product_id':products[0].id,'quantity':2},{'product_id':products[4].id,'quantity':1}])
 print(json.dumps({'venue_slug':v.slug,'table_id':str(t.pk),'tab_id':str(tab.pk),'balance_cents':5600}))
