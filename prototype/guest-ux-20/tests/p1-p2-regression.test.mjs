import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { createContext, runInContext } from 'node:vm';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script, 'Guest UX 2.0 script missing');

function boot(hash = '') {
  const nodes = new Map();
  const document = {
    getElementById(id) {
      if (!nodes.has(id)) nodes.set(id, {
        innerHTML: '', textContent: '', value: '', scrollTop: 0,
        classList: { add() {}, remove() {} }, focus() {}, setSelectionRange() {},
      });
      return nodes.get(id);
    },
  };
  const window = { location: { hash }, history: { replaceState() {} } };
  const vm = createContext({ document, window, setTimeout: () => 0, clearTimeout() {}, console });
  runInContext(script, vm, { timeout: 5000 });
  return (expression) => runInContext(expression, vm, { timeout: 5000 });
}

test('P1 persistent navigation with unpaid account and nonempty cart', () => {
  const run = boot('#pay');
  assert.equal(run('balance()'), 6000);
  assert.ok(run('nav().includes("<nav")'));
  run("S.scene='catalog';S.cart=[{...getProduct('ipa'),productId:'ipa',variant:'',qty:1,price:1900}]");
  assert.ok(run("nav().includes('Pedir')"));
});

test('P1 ready pickup is prioritized and historical items are collapsed', () => {
  const run = boot('#pickup');
  assert.ok(run("renderFicha().indexOf('Pronto para retirar') < renderFicha().indexOf('Em andamento')"));
  run("markPickupLine(S.orders[0].id,S.orders[0].items[1].id)");
  assert.ok(run("renderFicha().includes('<details')"));
  assert.equal(run('readyPickupCount()'), 1);
  assert.equal(run('S.orders[0].status'), 'Pronto para retirar');
});

test('P1 couvert count is independent of visits/QR scans, service is opt-in', () => {
  const run = boot('#fees');
  assert.equal(run('total()'), 7200);
  run("scenario('fees-multi')");
  assert.equal(run('total()'), 9600);
  assert.ok(run("renderAccount().includes('3 pessoas')"));
  run('toggleServiceCharge()');
  assert.equal(run('total()'), 10200);
});

test('P1 self payment has a consumption-first next action', () => {
  const run = boot('#pay');
  run("startPayment('amount');S.paymentValue='10';previewPayment();choosePaymentMethod('PIX');approveDemoPayment()");
  assert.ok(run("renderOverlay().includes('Continuar pedindo')"));
  assert.ok(run("renderOverlay().includes('Ver conta')"));
  run("startPayment('all');previewPayment();choosePaymentMethod('CARD');approveDemoPayment()");
  assert.ok(run("renderOverlay().includes('Ver minha comanda')"));
});

test('P1 invalid join and payment amounts display persistent, local alerts', () => {
  const join = boot('#multi');
  join("enter();S.modal='join-tab';el('joinCode').value='NOT-VALID';joinKnownTab()");
  assert.equal(join('S.hasJoined'), false);
  assert.ok(join('renderOverlay().includes(\'role="alert"\')'));
  const pay = boot('#pay');
  pay("startPayment('amount');S.paymentValue='9999';previewPayment()");
  assert.equal(pay('S.modal'), 'payment-amount');
  assert.ok(pay('renderOverlay().includes(\'role="alert"\')'));
});

test('P2 demo scenarios move off content; essential size remains on menu', () => {
  const run = boot('#stock');
  assert.ok(run("renderModeSwitch().includes('Abrir cenários de teste')"));
  assert.equal(run("productMeta(getProduct('heineken'))"), '330 ml');
  assert.ok(run("renderCatalog().includes('330 ml')"));
  assert.ok(run("renderCatalog().includes('Esgotado')"));
});

test('P0 regressions: QR authorization, pending payment, partial and prepaid', () => {
  const qr = boot('#multi');
  assert.equal(qr('S.orders.length'), 0);
  qr('enter()');
  assert.equal(qr('S.modal'), 'choose-tab');

  const partial = boot('#partial');
  partial("sendCart();checkoutFromBlock();choosePaymentMethod('PIX');approveDemoPayment()");
  assert.equal(partial('S.orders.length'), 2);
  assert.equal(partial('paid()'), 1900);

  const prepaid = boot('#prepaid');
  prepaid("sendCart();checkoutFromBlock();choosePaymentMethod('CARD');approveDemoPayment()");
  assert.equal(prepaid('S.orders.length'), 1);
  assert.equal(prepaid('balance()'), 0);
});


test('Guest has exactly two primary destinations: Pedir and Minha comanda', () => {
  const run = boot('#pay');
  assert.equal(run("nav().includes('Agora')"), false);
  assert.equal(run("(nav().match(/<button/g)||[]).length"), 2);
  assert.ok(run("nav().includes('Pedir')"));
  assert.ok(run("nav().includes('Minha comanda')"));
  assert.ok(run("renderAccount().includes('Minha comanda')"));
  assert.ok(run("renderAccount().includes('Mais uma rodada')"));
  assert.ok(run("renderAccount().includes('Ver todos')"));
  assert.ok(run("renderAccount().includes('Trocar de comanda')") || run("renderAccount().includes('Ajuda e opções')"));
});

test('After sending a table order, guest stays in Pedir with inline confirmation', () => {
  const run = boot('#mesa');
  run('enter()');
  assert.equal(run('S.scene'), 'catalog');
  run("S.cart=[{...getProduct('ipa'),productId:'ipa',variant:'',qty:1,price:1900}];sendCart()");
  assert.equal(run('S.scene'), 'catalog');
  assert.equal(run('S.orders.length'), 1);
  assert.ok(run("el('alert').innerHTML.includes('Pedido #')"));
  assert.ok(run("el('alert').innerHTML.includes('Ver pedido')"));
  assert.equal(run("renderCatalog().includes('sent-order-notice')"), false);
  run("switchView('account')");
  assert.ok(run("renderAccount().includes('Mais uma rodada')"));
  run('repeatLast();confirmRepeat()');
  assert.equal(run('S.orders.length'), 2);
  assert.equal(run('S.scene'), 'account');
});

test('Nightclub Ficha replaces Agora and retains pickup/repeat/help/payment', () => {
  const run = boot('#pickup');
  assert.equal(run("nav().includes('Agora')"), false);
  assert.equal(run("(nav().match(/<button/g)||[]).length"), 2);
  assert.ok(run("nav().includes('Minha ficha')"));
  assert.ok(run("renderFicha().includes('FG84')"));
  assert.ok(run("renderFicha().includes('Mais uma rodada')"));
  assert.ok(run("header().includes('Pedir ajuda à equipe')"));
  assert.ok(run("renderFicha().includes('Conta e pagamento')"));
  assert.equal(run("(renderFicha().match(/Pagar agora/g)||[]).length"), 0);
  assert.ok(run("renderFicha().includes('Pronto para retirar')"));
});

test('Migrates legacy home scene to Comanda and updates current table label', () => {
  const run = boot('#move');
  run("S.scene='home';render()");
  assert.equal(run('S.scene'), 'account');
  run("requestMove('12');staffConfirmMove()");
  assert.equal(run('S.scene'), 'account');
  assert.ok(run("header().includes('Mesa 12')"));
});


test('All active table orders contribute to one compact, actionable summary', () => {
  const run = boot('#pay');
  run("S.orders=[{id:'#201',status:'Recebido',items:[makeItem('heineken',1,'','you')]},{id:'#202',status:'Em preparo',items:[makeItem('batata',1,'','you')]},{id:'#203',status:'Pronto / chegando',items:[makeItem('ipa',1,'','you')]},{id:'#204',status:'Entregue (cliente confirmou)',items:[makeItem('heineken',1,'','you')]}]");
  assert.equal(run('S.orders.length'), 4);
  assert.ok(run("renderComandaOrders().includes('1 pronto ou chegando')"));
  assert.ok(run("renderComandaOrders().includes('1 em preparo')"));
  assert.ok(run("renderComandaOrders().includes('1 recebido')"));
  assert.ok(run("renderComandaOrders().includes('+ 1 pedido em andamento')"));
  assert.ok(run("renderComandaOrders().includes('Ver todos (4)')"));
});

test('Account keeps balance prominent and detailed consumption collapsed', () => {
  const run = boot('#pay');
  const account = run('renderAccount()');
  assert.ok(account.includes('FALTA PAGAR'));
  assert.ok(account.includes('R$ 60,00'));
  assert.ok(account.includes('<details class="bill-details">'));
  assert.ok(account.includes('Ver consumo detalhado'));
  assert.ok(run("header().includes('Pedir ajuda à equipe')"));
});

test('Header gear opens lab while DEMO strip is not customer-facing', () => {
  const run = boot('#mesa');
  assert.ok(run("header().includes('Abrir laboratório do protótipo')"));
  assert.equal(run("renderOverlay()"), '');
  run("S.modal='lab'");
  assert.ok(run("renderOverlay().includes('Visualizar')"));
  assert.ok(run("renderOverlay().includes('Mesa')"));
  assert.ok(run("renderOverlay().includes('Ficha')"));
});


test('Sent order notice stays visible outside the scrolled catalogue and can be dismissed', () => {
  const run = boot('#mesa');
  run("enter();S.cart=[{...getProduct('ipa'),productId:'ipa',variant:'',qty:1,price:1900}];sendCart()");
  assert.equal(run('S.scene'), 'catalog');
  assert.ok(run("el('alert').innerHTML.includes('Pedido #')"));
  assert.ok(run("el('alert').innerHTML.includes('Ver pedido')"));
  assert.equal(run("renderCatalog().includes('sent-order-notice')"), false);
  run('dismissOrderNotice()');
  assert.equal(run("el('alert').innerHTML.includes('sent-order-notice')"), false);
});

test('Two-tab navigation and payment CTA remain visible with a populated account', () => {
  const run = boot('#pay');
  assert.equal(run("(nav().match(/<button/g)||[]).length"), 2);
  assert.ok(run("nav().includes('Pedir')"));
  assert.ok(run("nav().includes('Minha comanda')"));
  assert.ok(run("S.scene==='account' && balance()>0"));
  assert.ok(run("renderAccount().includes('Ver consumo detalhado')"));
});


test('Cancelled orders are not suggested as a new round', () => {
  const run = boot('#pay');
  run("S.orders.push({id:'#999',status:'Cancelado pela equipe',cancelled:true,items:[makeItem('ipa',1,'','you')]})");
  assert.ok(run("repeatableOrder().id !== '#999'"));
  run("repeatLast()");
  assert.ok(run("S.repeated.every(x=>x.productId!=='ipa')"));
  run("S.orders.forEach(x=>{x.cancelled=true;x.status='Cancelado pela equipe'})");
  assert.equal(run('repeatableOrder()'), null);
  assert.equal(run("renderComandaOrders().includes('Mais uma rodada')"), false);
});
