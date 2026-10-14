"""Compose a local evidence gallery; originals are never altered."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,html,hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/design/evidence/android-visual-audit-2026-10-13'
font=ImageFont.truetype(str(ROOT/'apps/attendance-android/app/src/main/res/font/archivo_body.ttf'),18)
small=ImageFont.truetype(str(ROOT/'apps/attendance-android/app/src/main/res/font/archivo_body.ttf'),13)
heroes=[('A · Mesas','004-mesas-390.png'),('B · Cardápio','009-cardapio-390.png'),('C · Lançamento','024-revisao-agregada-390.png'),('D · Comanda','042-rodadas-estados-390.png'),('E · Pico','033-pico-entregas-390.png')]
montage=Image.new('RGB',(5*330,780),'#120f0c');d=ImageDraw.Draw(montage)
for i,(label,file) in enumerate(heroes):
 im=Image.open(OUT/file).convert('RGB'); im.thumbnail((312,690))
 montage.paste(im,(i*330+9,70));d.text((i*330+10,12),label,font=font,fill='#f3ece1');d.text((i*330+10,40),'Android real · API36 · 390dp',font=small,fill='#bbae9b')
montage.save(OUT/'five-experiences-montage.png')
pairs=[('mesas','ref-night-4.png','004-mesas-390.png','Referência: escolha de localização; lista nativa é extensão, sem paridade literal.'),('cardapio','ref-night-6.png','009-cardapio-390.png','Referência simulada vs catálogo da fixture; dados diferentes.'),('lancamento','ref-night-6.png','024-revisao-agregada-390.png','Pedido completo no rodapé da referência vs total agregado no app.'),('comanda','ref-night-5.png','040-comanda-rodadas-topo-390.png','Referência simulada vs saldo canônico da fixture, sem receber dinheiro.'),('pico','ref-peak-0.png','031-pico-topo-390.png','Referência expõe tarefas; app real mantém QR/chamadas antes das entregas.')]
comparisons=[]
for name,ref,actual,note in pairs:
 canvas=Image.new('RGB',(820,960),'#120f0c');draw=ImageDraw.Draw(canvas)
 draw.text((10,10),'REFERÊNCIA HTML · simulação',font=font,fill='#f3ece1');draw.text((420,10),'ANDROID REAL · 390dp',font=font,fill='#f3ece1')
 for x,file in [(10,ref),(420,actual)]:
  im=Image.open(OUT/file).convert('RGB'); im.thumbnail((390,844));canvas.paste(im,(x,55))
 for j,line in enumerate([note,'Exibição: PNG nativo em 50% (2px/dp). Originais preservados.', 'Comparação qualitativa; não mede igualdade de pixels nem de dados.']):draw.text((10,907+j*17),line,font=small,fill='#bbae9b')
 name='compare-'+name+'.png';canvas.save(OUT/name);comparisons.append((name,note))
inspections={r['file']:r for r in json.loads((OUT/'inspection-journal.json').read_text())} if (OUT/'inspection-journal.json').exists() else {}
metadata={}
for source in ['captures.jsonl','browser-captures.json','web-real.json','reference-extra.json']:
 p=OUT/source
 if p.exists():
  rows=[json.loads(s) for s in p.read_text().splitlines()] if p.suffix=='.jsonl' else json.loads(p.read_text())
  metadata.update({r['file']:r for r in rows})
thumbs=OUT/'thumbnails';thumbs.mkdir(exist_ok=True)
cards=[];manifest=[]
for file in sorted(OUT.glob('*.png')):
 im=Image.open(file);pixel_size=im.size
 thumb=im.copy();thumb.thumbnail((240,400));thumb.save(thumbs/file.name)
 meta=metadata.get(file.name,{})
 kind='Referência HTML simulada' if file.name.startswith('ref-') else 'Atendimento Web / API real' if file.name.startswith('web-') else 'Montagem/comparação' if file.name.startswith(('compare-','five-')) else 'Android executado / API real'
 caption=meta.get('state') or meta.get('source') or kind
 row={**meta,'file':file.name,'kind':kind,'pixels':pixel_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'inspected':inspections.get(file.name,{}).get('sha256')==hashlib.sha256(file.read_bytes()).hexdigest()}
 manifest.append(row)
 caption=html.escape(caption);name=html.escape(file.name)
 cards.append(f'<article data-filter="{name} {caption}"><a href="{name}"><img loading="lazy" src="thumbnails/{name}" alt="{name}" width="240"></a><h3><a href="{name}">{name}</a></h3><p>{caption}</p><small>{pixel_size[0]} × {pixel_size[1]} px · {html.escape(kind)}</small></article>')
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Rodada — auditoria visual Android 13/10/2026</title><style>body{background:#120f0c;color:#f3ece1;font:16px system-ui;margin:24px}a{color:#82b8ff}h1{font-size:26px}header{max-width:1100px}input{font:inherit;padding:12px;min-width:280px;background:#252019;border:1px solid #4d4335;color:#f3ece1}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px;margin-top:24px}article{padding:12px;background:#252019;border:1px solid #3a3228}article img{display:block;max-width:100%;height:400px;object-fit:contain;margin:auto}h3{font-size:14px;overflow-wrap:anywhere}small{color:#bbae9b}.hero{display:block;width:min(100%,1650px);height:auto;margin:24px 0}</style><header><h1>Rodada Android — evidência executada em 13/10/2026</h1><p>SHA 41e32d9853bc18ad08f136f5ead8bddc80afec77 · PostgreSQL descartável · fixture audit-aderlan-v1 · emulador API36/KVM/SwiftShader.</p><p>Esta galeria documenta execução e problemas. Não é aceite de fidelidade, homologação física nem material aprovado para a Play Store. Referências são simulações; confirmações do app vêm da API real.</p><p><a href="../../android-visual-audit-2026-10-13.md">Relatório</a> · <a href="../../android-visual-audit-2026-10-13-slices.md">Slices / Play Store</a> · <a href="manifest.json">Manifesto</a> · <a href="REPRODUCE.md">Reprodução</a></p><label for="filter">Filtrar nome, largura ou estado</label><br><input id="filter" type="search" placeholder="Ex.: 360, pico, erro"></header><a href="five-experiences-montage.png"><img class="hero" src="five-experiences-montage.png" alt="As cinco experiências capturadas no Android real"></a><div class="grid">'''+''.join(cards)+'''</div><script>document.querySelector('#filter').addEventListener('input',e=>{const q=e.target.value.toLocaleLowerCase('pt-BR');document.querySelectorAll('article').forEach(n=>n.hidden=!n.dataset.filter.toLocaleLowerCase('pt-BR').includes(q))})</script></html>'''
(OUT/'index.html').write_text(page)
(OUT/'manifest.json').write_text(json.dumps({'environment':json.loads((OUT/'environment.json').read_text()),'captures':manifest,'comparisons':[{'file':f,'note':n} for f,n in comparisons]},ensure_ascii=False,indent=2))
print('Gallery:',len(manifest),'originals/comparisons; five-experiences-montage.png')
