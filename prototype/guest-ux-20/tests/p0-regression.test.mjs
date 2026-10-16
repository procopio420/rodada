import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { createContext, runInContext } from 'node:vm';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script, 'Guest UX 2.0 must contain its inline application script');

function storage() {
  const memory = new Map();
  return {
    setItem(key, value) { memory.set(key, value); },
    getItem(key) { return memory.get(key) ?? null; },
  };
}
function boot(hash = '', sharedStorage = storage()) {
  const elements = new Map();
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, {
        innerHTML: '', textContent: '', value: '', scrollTop: 0,
        classList: { add() {}, remove() {} },
        focus() {}, setSelectionRange() {},
      });
      return elements.get(id);
    },
  };
  const window = { location: { hash }, history: { replaceState() {} }, sessionStorage: sharedStorage };
  const context = createContext({ document, window, setTimeout: () => 0, clearTimeout() {}, console });
  runInContext(script, context, { timeout: 5000 });
  return {
    evaluate(statement) { return runInContext(statement, context, { timeout: 5000 }); },
    storage: sharedStorage,
  };
}

test('P0 occupied QR never grants group access without authorization', () => {
  const app = boot('#multi');
  assert.equal(app.evaluate('S.hasJoined'), false);
  assert.equal(app.evaluate('S.orders.length'), 0);
  app.evaluate('enter()');
  assert.equal(app.evaluate('S.modal'), 'choose-tab');
  app.evaluate('join()');
  assert.equal(app.evaluate('S.hasJoined'), false);
  app.evaluate("S.modal='join-tab';el('joinCode').value='WRONG';joinKnownTab()");
  assert.equal(app.evaluate('S.orders.length'), 0);
  app.evaluate("el('joinCode').value='AB72';joinKnownTab()");
  assert.equal(app.evaluate('S.tabKey'), 'group');
  assert.equal(app.evaluate('S.orders[0].id'), '#181');
});

test('P0 two financial Tabs and pending Pix stay isolated', () => {
  const app = boot('#multi');
  app.evaluate("enter();S.modal='join-tab';el('joinCode').value='AB72';joinKnownTab()");
  app.evaluate("startPayment('amount');S.paymentValue='10';previewPayment();choosePaymentMethod('PIX')");
  const intent = app.evaluate('S.checkout.id');
  app.evaluate('exitGuestTab()');
  assert.equal(app.evaluate('S.orders.length'), 0);
  app.evaluate("enter();S.modal='join-tab';el('joinCode').value='XY93';joinKnownTab()");
  assert.equal(app.evaluate('S.tabKey'), 'private');
  assert.equal(app.evaluate('total()'), 1900);
  assert.equal(app.evaluate('S.paymentIntents.length'), 0);
  app.evaluate("registerPayment(500,'you')");
  assert.equal(app.evaluate('paid()'), 500);
  app.evaluate("exitGuestTab();enter();activateAuthorizedTab('group')");
  assert.equal(app.evaluate('S.checkout.id'), intent);
  assert.equal(app.evaluate('paid()'), 0);
  app.evaluate('resumePendingPayment();approveDemoPayment()');
  assert.equal(app.evaluate('paid()'), 1000);
  app.evaluate('approveDemoPayment()');
  assert.equal(app.evaluate('S.payments.length'), 1);
  app.evaluate("exitGuestTab();enter();activateAuthorizedTab('private')");
  assert.equal(app.evaluate('paid()'), 500);
  assert.equal(app.evaluate('S.payments.length'), 1);
});

test('P0 pending Pix can be dismissed, resumed and restored on the same deep link', () => {
  const shared = storage();
  const app = boot('#pay', shared);
  app.evaluate("startPayment('amount');S.paymentValue='10';previewPayment();choosePaymentMethod('PIX')");
  const intent = app.evaluate('S.checkout.id');
  app.evaluate('dismissModal()');
  assert.equal(app.evaluate('S.modal'), null);
  assert.ok(app.evaluate("paymentStatusBanner().includes('Pagamento em verificação')"));
  app.evaluate("startPayment('all')");
  assert.equal(app.evaluate('S.checkout.id'), intent);
  assert.equal(app.evaluate('S.paymentIntents.length'), 1);
  app.evaluate('cancelDemoCheckout()');
  assert.equal(app.evaluate('S.modal'), null);
  assert.equal(app.evaluate('unresolvedPayment().id'), intent);
  const reloaded = boot('#pay', shared);
  assert.equal(reloaded.evaluate('S.checkout.id'), intent);
  reloaded.evaluate('resumePendingPayment();approveDemoPayment()');
  assert.equal(reloaded.evaluate('paid()'), 1000);
  reloaded.evaluate('approveDemoPayment()');
  assert.equal(reloaded.evaluate('S.payments.length'), 1);
  const freshFixture = boot('#prepaid', shared);
  assert.equal(freshFixture.evaluate('S.policy'), 'PREPAID');
  assert.equal(freshFixture.evaluate('S.payments.length'), 0);
});

test('P0 partial and prepaid checkout still submit once on approval', () => {
  const partial = boot('#partial');
  partial.evaluate("sendCart();checkoutFromBlock();choosePaymentMethod('PIX')");
  assert.equal(partial.evaluate('S.orders.length'), 1);
  partial.evaluate('approveDemoPayment()');
  assert.equal(partial.evaluate('S.orders.length'), 2);
  assert.equal(partial.evaluate('paid()'), 1900);
  assert.equal(partial.evaluate('balance()'), 6000);
  assert.equal(partial.evaluate('S.pendingOrder'), null);
  const prepaid = boot('#prepaid');
  prepaid.evaluate("sendCart();checkoutFromBlock();choosePaymentMethod('CARD');approveDemoPayment()");
  assert.equal(prepaid.evaluate('S.orders.length'), 1);
  assert.equal(prepaid.evaluate('paid()'), 1900);
  assert.equal(prepaid.evaluate('balance()'), 0);
});
