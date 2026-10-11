"""Opt-in UI smoke on an isolated API36 emulator, real test API, no injected state.

Build first with -ProdadaApiBaseUrl=http://10.0.2.2:8144/ and seed_release_demo
in a separate PostgreSQL cluster. Never run against an operator's device.
Credentials below belong only to the existing disposable test fixture.
"""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from xml.etree import ElementTree as ET

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--adb', required=True)
p.add_argument('--serial', required=True)
p.add_argument('--phase', choices=['login', 'tab', 'order', 'payment-guard', 'cash-open', 'payment', 'payment-open', 'refund', 'refund-return', 'refund-repay', 'cash-close', 'inspect', 'offline', 'recovery'], required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
assert a.serial.startswith('emulator-'), 'Only isolated emulator accepted'
out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)

def adb(*args, binary=False):
    result = subprocess.check_output([a.adb, '-s', a.serial, *args], timeout=25)
    return result if binary else result.decode('utf-8')

def tree():
    adb('shell', 'uiautomator', 'dump', '/data/local/tmp/spec023-ui.xml')
    return ET.fromstring(adb('shell', 'cat', '/data/local/tmp/spec023-ui.xml'))

def find(label, field=False):
    nodes = list(tree().iter('node'))
    if not field:
        for node in nodes:
            if node.get('clickable') == 'true' and any(c.get('text') == label or c.get('content-desc') == label for c in node.iter('node')):
                return node
    for node in nodes:
        if field and node.get('class') != 'android.widget.EditText':
            continue
        if any(c.get('text') == label or c.get('content-desc') == label for c in node.iter('node')):
            if field or node.get('text') == label or node.get('content-desc') == label:
                return node
    raise AssertionError('Control absent: ' + label)

def tap(label, field=False):
    node = find(label, field)
    assert node.get('enabled') == 'true', label
    tap_node(node)

def tap_node(node):
    x1,y1,x2,y2 = map(int,re.findall(r'\d+',node.get('bounds')))
    adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2))

def enter(label,value):
    tap(label,True)
    adb('shell','input','text',value)
    adb('shell','input','keyevent','4')

def wait(label):
    for _ in range(10):
        nodes = list(tree().iter('node'))
        if any(n.get('text') == label or n.get('content-desc') == label for n in nodes):
            return
        # The actual operational warning must be acknowledged before the screen
        # becomes accessible; do not invent or bypass domain state.
        for node in nodes:
            if node.get('text') == 'Entendi':
                tap_node(node)
        time.sleep(1)
    raise AssertionError('Expected state absent: ' + label)

def capture(name):
    # No login/PIN entry screenshot or hierarchy is published.
    doc = tree()
    assert not any(n.get('password') == 'true' and n.get('text') for n in doc.iter('node'))
    (out/(name+'.png')).write_bytes(adb('exec-out','screencap','-p',binary=True))
    (out/(name+'.json')).write_text(json.dumps([
        {k:n.get(k) for k in ('text','content-desc','bounds','enabled','selected')}
        for n in doc.iter('node') if n.get('text') or n.get('content-desc')
    ],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def seek(label, up=False):
    for _ in range(12):
        try:
            return find(label)
        except AssertionError:
            regions = [n for n in tree().iter('node') if n.get('scrollable') == 'true']
            boxes = [list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in regions]
            boxes = [b for b in boxes if b[2]-b[0] > 44 and b[3]-b[1] > 100]
            assert boxes, 'No observed scrollable viewport for ' + label
            x1,y1,x2,y2 = max(boxes,key=lambda b:(b[2]-b[0])*(b[3]-b[1]))
            x = str((x1+x2)//2)
            low,high = str(y1+(y2-y1)*3//4),str(y1+(y2-y1)//4)
            adb('shell','input','swipe',x,high if up else low,x,low if up else high,'350')
    raise AssertionError('Scrolled control absent: ' + label)

if a.phase == 'login':
    try:
        find('ONLINE')
    except AssertionError:
        wait('Estabelecimento')
        enter('Estabelecimento','release-demo')
        enter('Operador','release-owner')
        enter('PIN','2468')
        tap('Entrar')
    wait('ONLINE')
    capture('native-agora')
    tap('Ativar modo pico')
    wait('Sair do modo pico')
    capture('native-peak')
    tap('Sair do modo pico')
    tap('Conta')
    wait('Operador ativo')
    capture('native-account')
    tap('← Atendimento')
    wait('ONLINE')
elif a.phase == 'tab':
    try:
        tap('← Comandas')
        wait('Pedir')
    except AssertionError:
        pass
    tap('Pedir')
    wait('Abrir comanda')
    tab_label = 'Spec023 test ' + str(int(time.time()))
    enter('Nome ou apelido (opcional)', tab_label.replace(' ', '%s'))
    tap('Abrir')
    wait('← Comandas')
    find(tab_label)
    find('ABERTA · versão 1')
    capture('native-tab')
elif a.phase == 'order':
    seek('Buscar no catálogo')
    enter('Buscar no catálogo','QA%sWrong%sitem')
    nodes = [n for n in tree().iter('node') if n.get('text','').startswith('QA Wrong item ')]
    assert len(nodes) == 1, 'Expected the existing full-shift fixture product, not invented data'
    tap_node(nodes[0])
    seek('Confirmar pedido')
    capture('native-cart')
    tap('Confirmar pedido')
    # Confirmed balance is durable evidence; a transient notice can disappear
    # during SSE revalidation and is insufficient to prove order confirmation.
    wait('Atualizar')
    seek('Total a pagar R$ 6,00', up=True)
    capture('native-order-confirmed')
elif a.phase == 'payment-guard':
    seek('Pagar', up=True)
    tap('Pagar')
    wait('Pagar comanda')
    seek('Abra ou selecione um caixa com turno ativo antes de receber dinheiro.')
    capture('native-payment-guard')
    tap('Cancelar')
elif a.phase == 'cash-open':
    seek('← Comandas', up=True)
    tap('← Comandas')
    tap('Caixa')
    wait('Caixa fechado')
    tap('Abrir caixa')
    wait('Fundo inicial')
    enter('Fundo inicial','0')
    tap('Abrir caixa')
    wait('Iniciar contagem')
    capture('native-cash-open')
elif a.phase in ('payment', 'payment-open'):
    tap('CONTAS')
    saved = json.loads((out/'native-tab.json').read_text(encoding='utf-8'))
    labels = [n['text'] for n in saved if n['text'].startswith('Spec023 test ')]
    assert len(labels) == 1
    seek(labels[0])
    tap(labels[0])
    wait('Atualizar')
    seek('Pagar',up=True)
    tap('Pagar')
    wait('Pagar comanda')
    find('Saldo restante: R$ 6,00')
    capture('native-payment-manual-test')
    tap('Confirmar pagamento')
    wait('Atualizar')
    seek('R$ 0,00',up=True)
    find('Pagamentos recebidos R$ 6,00 · estornos R$ 0,00')
    capture('native-payment-confirmed')
    if a.phase == 'payment':
        tap('Fechar')
        wait('Atualizar')
        seek('Fechada',up=True)
        capture('native-tab-closed')
elif a.phase == 'refund':
    seek('Estornar R$ 6,00')
    tap('Estornar R$ 6,00')
    wait('Estornar pagamento')
    tap('Valor do estorno',True)
    adb('shell','input','keyevent','KEYCODE_MOVE_END')
    for _ in range(16): adb('shell','input','keyevent','KEYCODE_DEL')
    adb('shell','input','text','3,00')
    adb('shell','input','keyevent','4')
    seek('Motivo')
    enter('Motivo','Estorno%stest%snativo')
    seek('Seu PIN')
    capture('native-refund-before-pin')
    enter('Seu PIN','2468')
    tap('Confirmar estorno')
    wait('Estorno confirmado.')
    capture('native-refund-alert')
    tap('Entendi')
    # Existing UI keeps the cleared form open; closing it never undoes a refund.
    tap('Cancelar')
    wait('Atualizar')
    seek('Já estornado: R$ 3,00')
    capture('native-refund-confirmed')
elif a.phase == 'refund-return':
    # Resume only after a read-only DB check confirmed the first refund.
    # No PIN entry or financial submission is repeated here.
    tap('Cancelar')
    wait('Atualizar')
    seek('Já estornado: R$ 3,00')
    capture('native-refund-confirmed')
elif a.phase == 'refund-repay':
    seek('Pagar',up=True)
    tap('Pagar')
    wait('Pagar comanda')
    find('Saldo restante: R$ 3,00')
    capture('native-refund-repay')
    tap('Confirmar pagamento')
    wait('Atualizar')
    seek('R$ 0,00',up=True)
    find('Pagamentos recebidos R$ 9,00 · estornos R$ 3,00')
    capture('native-refund-reconciled')
    tap('Fechar')
    wait('Atualizar')
    seek('Fechada',up=True)
    capture('native-tab-closed')
elif a.phase == 'cash-close':
    try:
        find('Valor contado')
    except AssertionError:
        try:
            find('Iniciar contagem')
        except AssertionError:
            seek('← Comandas',up=True)
            tap('← Comandas')
            tap('Caixa')
        wait('Iniciar contagem')
        # Cash uses Java NumberFormat's literal NBSP; do not normalize away
        # a difference from the Tab formatter's ordinary space.
        find('R$\u00a06,00')
        capture('native-cash-received')
        tap('Iniciar contagem')
        wait('Informar contagem')
        tap('Informar contagem')
    wait('Valor contado')
    enter('Valor contado','6,00')
    capture('native-cash-count')
    tap('Fechar caixa')
    wait('Caixa fechado')
    capture('native-cash-closed')
elif a.phase == 'offline':
    try:
        find('Sem conexão com o Rodada.')
        capture('native-offline-alert')
    except AssertionError:
        pass
    wait('Atualizar')
    tap('Atualizar')
    wait('SEM SINAL')
    capture('native-offline')
elif a.phase == 'recovery':
    wait('Atualizar')
    tap('Atualizar')
    wait('ONLINE')
    capture('native-recovered')
else:
    capture('native-current')
result = {'phase':a.phase,'passed':True,'platform':'API36 emulator','api':'real isolated PostgreSQL','payments':'MANUAL_TEST only'}
(out/(a.phase+'.result.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
