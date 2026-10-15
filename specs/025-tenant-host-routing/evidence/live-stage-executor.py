if not __debug__: raise RuntimeError("Python optimization disables operational guards")
import os,sys,json,hashlib,io
from collections import Counter
os.chdir('/app/apps/api');sys.path.insert(0,os.getcwd())
p=json.load(sys.stdin); op=p['operation']; assert op in ('inspect','provision','activate','deactivate')
assert os.environ.get('RAILWAY_GIT_COMMIT_SHA')==p['sha']
if op in ('provision','activate'):
 assert os.environ.get('RODADA_DEMO_SEED_ON_START','').lower()=='false'
 assert os.environ.get('RODADA_ENABLE_TENANT_HOST_UI','').lower() not in ('1','true','yes','on')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','rodada_api.settings')
import django;django.setup()
from django.db import connection,transaction
from django.core.management import call_command
from modules.venue.management.commands.provision_spec025_ab import QA_VENUES
from modules.venue.models import Venue,VenueDomain
from modules.access.models import StaffMember,VenueStaffMembership,StaffSession,AccessInvalidationEvent
from modules.guest_access.models import GuestSession
from modules.hospitality.models import Table
from modules.audit.models import AuditEvent
slugs=[s['slug'] for s in QA_VENUES];logins=[s['login'] for s in QA_VENUES]
def state():
 result=[]
 for s in QA_VENUES:
  v=Venue.objects.filter(slug=s['slug']).first();d=VenueDomain.objects.filter(hostname=s['host']).first();u=StaffMember.objects.filter(login_identifier=s['login']).first()
  m=VenueStaffMembership.objects.filter(venue=v,staff_member=u).first() if v and u else None
  result.append(dict(host=s['host'],venue_id=str(v.pk) if v else None,operator_id=str(u.pk) if u else None,domain_owner_matches=bool(v and d and d.venue_id==v.pk),active=bool(d and d.is_active),verified=bool(d and d.is_verified),membership_status=m.status if m else None,guest_blocked=bool(v and v.guest_mutations_blocked)))
 return result
def snapshot():
 out={}
 with connection.cursor() as c:
  for t in connection.introspection.table_names(c):
   c.execute('SELECT to_jsonb(t)::text FROM '+connection.ops.quote_name(t)+' t')
   out[t]=Counter(hashlib.sha256(r[0].encode()).digest() for r in c.fetchall())
 return out
def allowed():
 vids=list(Venue.objects.filter(slug__in=slugs).values_list('pk',flat=True));uids=list(StaffMember.objects.filter(login_identifier__in=logins).values_list('pk',flat=True))
 qs=[Venue.objects.filter(pk__in=vids),VenueDomain.objects.filter(venue_id__in=vids),StaffMember.objects.filter(pk__in=uids),VenueStaffMembership.objects.filter(venue_id__in=vids),Table.objects.filter(venue_id__in=vids),AuditEvent.objects.filter(venue_id__in=vids),StaffSession.objects.filter(venue_id__in=vids),AccessInvalidationEvent.objects.filter(venue_id__in=vids),GuestSession.objects.filter(table__venue_id__in=vids)]
 out={}
 with connection.cursor() as c:
  for q in qs:
   ids=list(q.values_list('pk',flat=True));t=q.model._meta.db_table
   if not ids:out[t]=Counter();continue
   c.execute('SELECT to_jsonb(t)::text FROM '+connection.ops.quote_name(t)+' t WHERE '+connection.ops.quote_name(q.model._meta.pk.column)+' IN ('+','.join(['%s']*len(ids))+')',ids)
   out[t]=Counter(hashlib.sha256(r[0].encode()).digest() for r in c.fetchall())
 return out
s0=state();captured=io.StringIO()
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');c.execute("SET LOCAL lock_timeout='5s'");c.execute("SET LOCAL statement_timeout='30s'")
 before=snapshot();allowed_before=allowed()
 if op=='provision':
  pins=p['pins'];assert len(pins['a'])==len(pins['b'])==12 and pins['a']!=pins['b']
  os.environ['RODADA_SPEC025_A_PIN']=pins['a'];os.environ['RODADA_SPEC025_B_PIN']=pins['b']
  call_command('provision_spec025_ab',operation='provision',apply=True,backup_reference=p['reference'],logical_backup_verified=True,stdout=captured)
 elif op in ('activate','deactivate'):
  if op=='activate':assert p.get('edge_confirmed') is True
  kw=dict(operation=op,apply=True,stdout=captured)
  if op=='activate':kw.update(backup_reference=p['reference'],logical_backup_verified=True,edge_confirmed=True)
  call_command('provision_spec025_ab',**kw)
 else:call_command('provision_spec025_ab',stdout=captured)
 after=snapshot();good=allowed()
 assert before.keys()==after.keys()
 for t in before:
  if op in ('inspect','provision'):
   assert not (before[t]-after[t]),'pre-existing row modified: '+t
   assert not ((after[t]-before[t])-good.get(t,Counter())),'foreign row added: '+t
  else:
   assert before[t]-allowed_before.get(t,Counter())==after[t]-good.get(t,Counter()),'foreign row changed: '+t
 s1=state()
 if op=='provision':
  assert len({v['venue_id'] for v in s1})==2 and len({v['operator_id'] for v in s1})==2
  assert all(v['domain_owner_matches'] and not v['active'] and not v['verified'] and v['membership_status']=='SUSPENDED' and v['guest_blocked'] for v in s1)
 if op=='activate':
  assert all(v['domain_owner_matches'] and v['active'] and v['verified'] and v['membership_status']=='ACTIVE' and v['guest_blocked'] for v in s1)
 if op=='deactivate':
  assert all(v['domain_owner_matches'] and not v['active'] and v['guest_blocked'] for v in s1)
  vids=Venue.objects.filter(slug__in=slugs).values_list('pk',flat=True)
  assert not VenueStaffMembership.objects.filter(venue_id__in=vids,status='ACTIVE').exists()
  assert not StaffSession.objects.filter(venue_id__in=vids,revoked_at__isnull=True).exists()
  assert not GuestSession.objects.filter(table__venue_id__in=vids,revoked_at__isnull=True).exists()
committed_readback_matches=state()==s1
print(json.dumps(dict(operation=op,sha=p['sha'],foreign_rows_preserved_by_this_transaction=True,preexisting_rows_preserved_by_this_transaction=op in ('inspect','provision'),new_rows_only_reserved_qa=True,state_unchanged=s0==s1,database_unchanged=before==after,committed_readback_matches=committed_readback_matches,qa=s1)))
