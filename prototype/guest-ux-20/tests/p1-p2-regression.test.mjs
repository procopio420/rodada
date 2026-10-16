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
  assert.ok(run("renderOverlay().includes('Voltar ao agora')"));
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
