"""Run with Django manage.py shell in dedicated local synthetic DB; no reset/flush."""
import json, os, secrets, uuid
from django.db import transaction
from modules.access.models import StaffMember, VenueStaffMembership
from modules.venue.models import Venue
from modules.dispatch.models import DispatchTask
if (os.environ.get('POSTGRES_HOST'), os.environ.get('POSTGRES_PORT'), os.environ.get('POSTGRES_DB')) != ('127.0.0.1', '55501', 'rodada_android_post_drop'):
 raise RuntimeError('Dedicated local synthetic DB required')
prefix='spec033-session-fence-'+uuid.uuid4().hex[:10]
with transaction.atomic():
 venue=Venue.objects.get(slug='spec033-native-shell-parity')
 config={'venue':venue.slug,'liveServiceSessionFence':'true'}
 for suffix,op,pin in [('a','operator','testPin'),('b','operatorB','testPinB')]:
  staff=StaffMember(login_identifier=prefix+'-'+suffix,display_name='Synthetic session '+suffix)
  value=str(secrets.randbelow(900000)+100000)
  staff.set_pin(value);staff.save()
  VenueStaffMembership.objects.create(venue=venue,staff_member=staff,role='MANAGER')
  config[op]=staff.login_identifier;config[pin]=value
 pairs=[]
 for n in range(4):
  pair={key:str(DispatchTask.objects.create(venue=venue,task_type='SERVICE_REQUEST',destination_label=prefix+'-'+str(n)+'-'+key).id) for key in ['x','y']}
  pairs.append(pair)
 config['serviceTaskPairs']=json.dumps(pairs,separators=(',',':'))
 path='/tmp/spec033-service-session-runner.json'
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'w') as stream:json.dump(config,stream)
 print('Created isolated synthetic staff pair and eight service tasks; private runner config mode0600.')
