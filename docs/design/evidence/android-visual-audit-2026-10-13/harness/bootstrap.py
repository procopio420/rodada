"""Disposable local fixture. No seed or remote environment is accepted."""
import os, sys, secrets, json, uuid
from pathlib import Path
root = Path(__file__).resolve().parents[1]
for line in (root/'.audit-local/private.env').read_text().splitlines():
    k,v=line.split('=',1); os.environ[k]=v
sys.path.insert(0,str(root/'apps/api'))
import django
django.setup()
from django.conf import settings
assert settings.DATABASES['default']['NAME']=='rodada_visual_audit'
assert settings.DATABASES['default']['PORT']=='15483'
from modules.venue.models import Venue
from modules.access.models import StaffMember, VenueStaffMembership
from modules.access.context import ActorContext
from modules.catalog.models import Product, ProductVariant, ModifierGroup, ModifierOption, ProductModifierGroup
from modules.hospitality.services import create_table, release_table, start_cleaning, occupy_table, assign_tab
from modules.hospitality.table_service import start_table_service, open_tab_in_occupancy
from modules.ordering.services import open_tab, confirm_order, transition_order_item
from modules.house_account.models import VenueRelationshipPolicy
from modules.dispatch.services import create_service_request
venue=Venue.objects.create(slug='audit-aderlan',name='Bar do Aderlan · DEMONSTRAÇÃO',table_service_enabled=True)
pin=str(secrets.randbelow(10000)).zfill(4)
staff=StaffMember(login_identifier='audit-operador',display_name='Operador de demonstração')
staff.set_pin(pin); staff.save()
VenueStaffMembership.objects.create(venue=venue,staff_member=staff,role='OWNER')
VenueRelationshipPolicy.objects.create(venue=venue,kind='VISITOR',limit_cents=100000)
actor=ActorContext(venue.id,staff.id,None,None)
products={}
for name,price,cat,station in [('Água mineral',500,'Sem álcool','BAR'),('Cerveja artesanal',1200,'Cervejas','BAR'),('Fritas da casa',2800,'Porções','KITCHEN'),('Hambúrguer artesanal com queijo curado e molho da casa',3200,'Lanches','KITCHEN'),('Suco de maracujá',900,'Sem álcool','BAR'),('Bolinho indisponível',2500,'Porções','KITCHEN')]:
    products[name]=Product.objects.create(venue=venue,name=name,price_cents=price,category=cat,fulfillment_station=station)
for i in range(36):
    Product.objects.create(venue=venue,name=f'Demo {i+1:02d} · opção de cardápio com nome extenso',price_cents=700+i*50,category=['Cervejas','Sem álcool','Porções','Lanches'][i%4],fulfillment_station='BAR' if i%4<2 else 'KITCHEN')
burger=products['Hambúrguer artesanal com queijo curado e molho da casa']
ProductVariant.objects.create(product=burger,name='Individual',price_cents=3200,is_default=True)
ProductVariant.objects.create(product=burger,name='Duplo',price_cents=4200,sort_order=1)
group=ModifierGroup.objects.create(venue=venue,name='Complementos',selection_mode='MULTI',min_selections=0,max_selections=2)
ModifierOption.objects.create(group=group,name='Queijo extra',price_delta_cents=400,semantic_kind='ADD')
ModifierOption.objects.create(group=group,name='Sem cebola',semantic_kind='REMOVE',sort_order=1)
ProductModifierGroup.objects.create(product=burger,group=group)
# Availability changed through its canonical API below, after login is available.
tables={label:create_table(label=label,guest_ordering_mode='JOIN_ACTIVE',actor=actor) for label in ['01','02','03','04','05','06','07','08']}
tabs=[]
for label,names in [('01',['Alex','Alex','']),('05',['Rodadas · demonstração']),('07',['Fila 07']),('08',['Fila 08'])]:
    result=start_table_service(table_id=tables[label].id,idempotency_key=str(uuid.uuid4()),actor=actor)
    occ=result['active_occupancy']
    for name in names:
        r=open_tab_in_occupancy(occupancy_id=occ['id'],expected_generation=tables[label].access_generation,idempotency_key=str(uuid.uuid4()),actor=actor,display_label=name)
        tabs.append((label,r['tab_id']))
for label in ['03','04']:
    start_table_service(table_id=tables[label].id,idempotency_key=str(uuid.uuid4()),actor=actor)
    release_table(table_id=tables[label].id,actor=actor)
    if label=='03': start_cleaning(table_id=tables[label].id,actor=actor)
tables['04'].status='OUT_OF_SERVICE'; tables['04'].save(update_fields=['status'])
# Legacy/guest-like unassigned occupancy; no invented staff ownership.
occ=occupy_table(table_id=tables['06'].id,actor=actor)
tab=open_tab(actor=actor,display_label='QR · sem responsável')
assign_tab(occupancy_id=occ.id,tab_id=tab.id,actor=actor)
qr=confirm_order(tab_id=tab.id,source='GUEST',lines=[{'product_id':products['Água mineral'].id,'quantity':1}],idempotency_key=str(uuid.uuid4()),actor=None)
for label,tabid in tabs:
    if label not in ['05','07','08']: continue
    for round_no in range(2 if label=='05' else 1):
        order=confirm_order(tab_id=tabid,source='STAFF',actor=actor,idempotency_key=str(uuid.uuid4()),lines=[{'product_id':products[n].id,'quantity':q} for n,q in [('Água mineral',2),('Cerveja artesanal',1),('Fritas da casa',1)]])
        for j,item in enumerate(order.items.all()):
            if j<2:
                transition_order_item(item_id=item.id,target_state='PREPARING',actor=actor)
                if j==0 or label!='05': transition_order_item(item_id=item.id,target_state='READY',actor=actor)
for label,kind in [('01','SERVICE_REQUEST'),('07','BILL_REQUEST'),('08','SERVICE_REQUEST')]:
    create_service_request(request_id=uuid.uuid4(),task_type=kind,table_id=tables[label].id,actor=actor)
auth={'venue_slug':venue.slug,'login_identifier':staff.login_identifier,'pin':pin,'installation_id':'audit-local-fixture','platform':'ANDROID','device_label':'Audit fixture'}
p=root/'.audit-local/login.json'; p.write_text(json.dumps(auth)); p.chmod(0o600)
(root/'.audit-local/fixture.json').write_text(json.dumps({'venue':venue.slug,'tables':{k:str(v.id) for k,v in tables.items()},'tabs':tabs,'products':{k:str(v.id) for k,v in products.items()}},ensure_ascii=False,indent=2))
print('Fixture fictícia criada com serviços canônicos: 8 mesas, 42 produtos, variantes, rodadas, fila e chamadas.')
