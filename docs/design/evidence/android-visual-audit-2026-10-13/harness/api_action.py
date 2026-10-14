"""Canonical API commands restricted to this audit's fixture."""
import json,urllib.request,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
fixture=json.loads((ROOT/'.audit-local/fixture.json').read_text())
def call(path,body=None,method=None):
    assert fixture['venue']=='audit-aderlan'
    auth=json.loads((ROOT/'.audit-local/login.json').read_text())
    login=urllib.request.Request('http://127.0.0.1:18081/auth/login/',data=json.dumps(auth).encode(),headers={'Content-Type':'application/json'})
    session=json.load(urllib.request.urlopen(login))
    request=urllib.request.Request('http://127.0.0.1:18081'+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+session['access_token']},method=method)
    with urllib.request.urlopen(request) as response: return json.load(response)
if __name__=='__main__':
    if sys.argv[1]=='availability':
        pid=fixture['products'][sys.argv[2]]
        result=call('/catalog/products/'+pid+'/availability/',{'state':sys.argv[3]})
        print('Canonical availability:',result['state'])
    elif sys.argv[1]=='readback':
        tabs=call('/tabs/?active=false&offset=0')
        rows=tabs.get('results',tabs) if isinstance(tabs,dict) else tabs
        p=ROOT/'docs/design/evidence/android-visual-audit-2026-10-13/api-readback.json'
        p.write_text(json.dumps(rows,ensure_ascii=False,indent=2));print('Canonical tabs saved; no auth secrets.')
