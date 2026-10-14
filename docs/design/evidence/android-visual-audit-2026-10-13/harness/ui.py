import subprocess,re,time,json,sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/design/evidence/android-visual-audit-2026-10-13'
OUT.mkdir(parents=True,exist_ok=True)
ADB='/home/lucas/Android/Sdk/platform-tools/adb'
SERIAL='emulator-5584'
def adb(*args,binary=False):
    p=subprocess.run([ADB,'-s',SERIAL,*map(str,args)],capture_output=True,timeout=35)
    if p.returncode: raise RuntimeError(p.stderr.decode())
    return p.stdout if binary else p.stdout.decode()
def tree():
    adb('shell','uiautomator','dump','/data/local/tmp/audit.xml')
    return ET.fromstring(adb('shell','cat','/data/local/tmp/audit.xml'))
def nodes(): return list(tree().iter('node'))
def bounds(n): return list(map(int,re.findall(r'\d+',n.get('bounds'))))
def tap_node(n):
    x,y,r,b=bounds(n); adb('shell','input','tap',(x+r)//2,(y+b)//2)
def find(label,field=False,index=0,ns=None):
    ns=nodes() if ns is None else ns; matches=[]
    if not field:
        matches=[n for n in ns if n.get('clickable')=='true' and any(c.get('text')==label or c.get('content-desc')==label for c in n.iter('node'))]
    if not matches: matches=[n for n in ns if (not field or n.get('class')=='android.widget.EditText') and (n.get('text')==label or n.get('content-desc')==label)]
    if not matches:
        matches=[n for n in ns if (n.get('class')=='android.widget.EditText' if field else n.get('clickable')=='true') and any(c.get('text')==label or c.get('content-desc')==label for c in n.iter('node'))]
    if not matches: raise AssertionError('Absent: '+label)
    return matches[index]
def tap(label,index=0):
    n=find(label,index=index); assert n.get('enabled')=='true',label; tap_node(n)
    trace('tap',label)
    time.sleep(.35)
def trace(kind,label):
    with (OUT/'interaction-trace.jsonl').open('a') as f: f.write(json.dumps({'kind':kind,'label':label,'time_machine':time.time(),'note':'Automation timestamp; not human service duration'},ensure_ascii=False)+'\n')
def enter(label,value,clear=False):
    field=find(label,field=True); tap_node(field)
    if clear:
        adb('shell','input','keyevent','KEYCODE_MOVE_END',*(['KEYCODE_DEL']*(len(field.get('text',''))+4)))
    adb('shell','input','text',value.replace(' ','%s'))
    adb('shell','input','keyevent','4'); time.sleep(.3)
    trace('field',label)
def text(): return '\n'.join(n.get('text') or n.get('content-desc','') for n in nodes() if n.get('text') or n.get('content-desc'))
def wait(label):
    for _ in range(20):
        try: return find(label)
        except AssertionError: time.sleep(.6)
    raise AssertionError('Expected: '+label)
def swipe(up=False,ns=None):
    ns=[n for n in (nodes() if ns is None else ns) if n.get('scrollable')=='true']; boxes=[bounds(n) for n in ns]
    if boxes: x,y,r,b=max(boxes,key=lambda b:(b[2]-b[0])*(b[3]-b[1]))
    else: x,y,r,b=0,140,780,1420
    mid=(x+r)//2; lo=y+int((b-y)*.8); hi=y+int((b-y)*.2)
    adb('shell','input','swipe',mid,hi if up else lo,mid,lo if up else hi,350); time.sleep(.3)
    trace('scroll','up' if up else 'down')
def seek(label,up=False):
    previous=None;reversed_once=False
    for _ in range(18):
        ns=nodes()
        try: return find(label,ns=ns)
        except AssertionError:
            if any(n.get('text') in ['Entendi','Sem conexão com o Rodada.'] for n in ns):raise AssertionError('Modal blocks scrolling: '+label)
            signature=tuple((n.get('text'),n.get('bounds')) for n in ns if n.get('text'))
            if signature==previous and not reversed_once:
                up=not up;reversed_once=True;trace('seek-direction-reversal',label)
            elif signature==previous and reversed_once:raise AssertionError('No scroll progress: '+label)
            previous=signature;swipe(up,ns=ns)
    raise AssertionError('Scrolled absent: '+label)
def capture(name,state='',steps='',transient=False):
    ns=[] if transient else nodes()
    assert not any(n.get('password')=='true' and n.get('text') for n in ns),'No credentials in evidence'
    (OUT/(name+'.png')).write_bytes(adb('exec-out','screencap','-p',binary=True))
    (OUT/(name+'.ui.json')).write_text(json.dumps([{**{k:n.get(k) for k in ['text','content-desc','bounds','enabled','selected','clickable','class']},'label': ' | '.join(c.get('text') or c.get('content-desc','') for c in n.iter('node') if c.get('text') or c.get('content-desc'))} for n in ns if n.get('text') or n.get('content-desc') or n.get('clickable')=='true'],ensure_ascii=False,indent=2))
    meta={'file':name+'.png','state':state,'steps':steps,'sha':'41e32d9853bc18ad08f136f5ead8bddc80afec77','fixture':'audit-aderlan-v1','serial':SERIAL,'wm_size':adb('shell','wm','size').strip(),'wm_density':adb('shell','wm','density').strip(),'fontScale':adb('shell','settings','get','system','font_scale').strip(),'android':adb('shell','getprop','ro.build.version.release').strip(),'api':adb('shell','getprop','ro.build.version.sdk').strip(),'inspected':False}
    with (OUT/'captures.jsonl').open('a') as f: f.write(json.dumps(meta,ensure_ascii=False)+'\n')
    print('CAPTURE',name,flush=True)
def config(width,font=1):
    adb('shell','wm','density','320'); adb('shell','wm','size',f'{width*2}x1688'); adb('shell','settings','put','system','font_scale',font); time.sleep(1)
if __name__=='__main__':
    op=sys.argv[1]
    if op=='text': print(text())
    elif op=='tap': tap(sys.argv[2])
    elif op=='capture': capture(sys.argv[2])
    elif op=='swipe': swipe(len(sys.argv)>2)
    elif op=='config': config(int(sys.argv[2]),float(sys.argv[3]) if len(sys.argv)>3 else 1)
