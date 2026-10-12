import json
from urllib.request import Request,urlopen
from urllib.error import HTTPError
base='http://127.0.0.1:18095';pin=json.load(open('/tmp/rodada-pilot-pinned-credentials.json'))['pin'];body=json.dumps(dict(venue_slug='pinned-pilot-test',login_identifier='pinned-owner-test',pin=pin)).encode();rows=[]
for origin,fetch,expected in [(base,'same-origin',200),('http://127.0.0.1:18096','same-origin',403),('https://untrusted.example','cross-site',403),(base,'cross-site',403)]:
 try:
  with urlopen(Request(base+'/api/auth/login',data=body,headers={'Content-Type':'application/json','Origin':origin,'Sec-Fetch-Site':fetch}),timeout=20) as q:status=q.status
 except HTTPError as q:status=q.code
 assert status==expected,(origin,fetch,status,expected);rows.append(dict(origin=origin,fetch_site=fetch,status=status))
json.dump(rows,open('/tmp/pilot-origin-fix-tests.json','w'),indent=2);print(json.dumps(rows))
