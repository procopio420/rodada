import asyncio,json
from datetime import datetime,timezone
from pathlib import Path
from rodada_api.asgi import application as real
log=Path('/home/lucas/.cache/rodada033-origin-evidence/delay-events.jsonl')
async def application(scope,receive,send):
 path=scope.get('path','')
 delay=2.0 if path.startswith('/dispatch/tasks/') and scope.get('method')=='GET' else 0.8 if path=='/hospitality/tables/' else 0
 if delay:
  with log.open('a') as f:f.write(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'path':path,'delay_seconds':delay})+'\n')
  await asyncio.sleep(delay)
 await real(scope,receive,send)
