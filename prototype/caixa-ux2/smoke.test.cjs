#!/usr/bin/env node
/* Caixa 2.0 prototype interaction regressions. No npm, browser or provider required.
 * This VM exercises the actual HTML event handlers with an intentionally tiny DOM.
 * It does not substitute for real-browser, payment-provider or POS acceptance.
 * Run: node prototype/caixa-ux2/smoke.test.cjs
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const html = fs.readFileSync(path.join(__dirname, "index.html"), "utf8");
const source = html.slice(html.lastIndexOf("<script>") + 8, html.lastIndexOf("</script>"));
assert(source.startsWith("\n(function()"), "Expected the executable, local prototype script");
new vm.Script(source, { filename: "caixa-ux2/index.html" });
let nextId = 0;

function mount(previous = null) {
  const app = { innerHTML: "" };
  const listeners = {};
  const saved = { current: previous };
  const document = {
    activeElement: null,
    querySelector: (selector) => selector === "#app" ? app : null,
    addEventListener: (event, callback) => { listeners[event] = callback; },
  };
  const window = { scrollY: 0, scrollTo() {}, print() {} };
  const localStorage = {
    getItem() { return saved.current; },
    setItem(_key, value) { saved.current = value; },
  };
  vm.runInNewContext(source, {
    document, window, localStorage,
    crypto: { randomUUID: () => "test-uuid-" + ++nextId },
    structuredClone, setTimeout: () => 0, clearTimeout() {},
  }, { timeout: 1000 });
  return {
    app, saved,
    db: () => JSON.parse(saved.current).db,
    click(act, extra = {}) {
      const target = { dataset: { act, ...extra }, closest: () => ({ dataset: { act, ...extra } }) };
      listeners.click({ target });
    },
    input(input, value) { listeners.input({ target: { dataset: { input }, value } }); },
  };
}
const check = (name, task) => { task(); console.log("PASS " + name); };

check("blind count hides drawer until sealed; survives reload and closes", () => {
  const x = mount();
  x.click("nav", { view: "shift" }); x.click("start-count"); x.click("modal-close");
  assert.equal(x.db().drawer.counted, null);
  assert(x.app.innerHTML.includes("Valor oculto"));
  x.click("nav", { view: "activity" });
  assert(x.app.innerHTML.includes("Movimentações protegidas"));
  x.click("start-count"); x.input("countInput", "1.284,50"); x.click("count-next");
  assert.equal(x.db().drawer.counted, 128450);
  const y = mount(x.saved.current);
  y.click("nav", { view: "shift" }); y.click("start-count");
  assert(y.app.innerHTML.includes("Resultado da conferência"));
  y.click("commit-count");
  assert.equal(y.db().drawer.open, false);
  assert.equal(y.db().drawer.difference, 0);
});

check("equal split keeps four 28-real installments after refresh", () => {
  const x = mount();
  x.click("select-tab", { id: "t2" }); x.click("split");
  x.click("split-plus"); x.click("split-plus"); x.click("split-continue");
  x.input("tendered", "28,00"); x.click("confirm-payment");
  assert.equal(x.db().tabs.find(t => t.id === "t2").splitPlan.paidParts, 1);
  const y = mount(x.saved.current);
  y.click("select-tab", { id: "t2" });
  assert(y.app.innerHTML.includes("Próxima parte"));
  for (let i = 1; i < 4; i++) {
    y.click("next-split"); y.input("tendered", "28,00"); y.click("confirm-payment");
  }
  const tab = y.db().tabs.find(t => t.id === "t2");
  assert.equal(tab.payments.length, 4);
  assert.equal(tab.payments.reduce((sum, p) => sum + p.amount, 0), 11200);
  assert.equal(tab.splitPlan, null);
});

check("change notice remains visible across reload until operator dismisses", () => {
  const x = mount();
  x.click("pay"); x.input("tendered", "200,00"); x.click("confirm-payment");
  assert.equal(x.db().changeNotices.length, 1);
  const y = mount(x.saved.current);
  assert(y.app.innerHTML.includes("TROCO A DEVOLVER"));
  y.click("dismiss-change");
  assert.equal(y.db().changeNotices.length, 0);
});

check("unknown payment is visible globally and blocks retry until verified", () => {
  const x = mount();
  x.click("select-tab", { id: "t2" }); x.click("pay");
  x.click("method", { method: "PIX" }); x.click("confirm-payment");
  x.click("pay-unknown"); x.click("modal-close");
  assert(x.app.innerHTML.includes("cobrança(s) sem confirmação"));
  const y = mount(x.saved.current);
  y.click("go-uncertain");
  assert(y.app.innerHTML.includes("Verificar cobrança"));
  y.click("resolve-attempt", { result: "not-paid" });
  assert.equal(y.db().attempts[0].status, "NOT_CHARGED");
});

check("refund preserves a previously closed Tab and requires separate review", () => {
  const x = mount();
  x.click("select-tab", { id: "t2" }); x.click("pay");
  x.input("tendered", "112,00"); x.click("confirm-payment"); x.click("close-tab");
  assert.equal(x.db().tabs.find(t => t.id === "t2").closed, true);
  const activity = x.db().activity.find(a => a.type === "payment" && a.tabId === "t2");
  x.click("nav", { view: "activity" }); x.click("refund", { id: activity.id });
  x.input("refundReason", "Solicitação do cliente"); x.input("refundPin", "1234");
  x.click("commit-refund");
  const tab = x.db().tabs.find(t => t.id === "t2");
  assert.equal(tab.closed, true);
  assert.equal(tab.refundReview, "PENDING");
  assert.equal(tab.payments[0].refund, 11200);
});

check("quick-sale stages visibly simulated Bar and Kitchen routing", () => {
  const x = mount();
  x.click("quick-sale"); x.click("sale-more", { index: "3" }); x.click("sale-commit");
  const tab = x.db().tabs.find(t => t.code === "B-018");
  assert(tab.production.some(p => p.station === "BAR"));
  assert(tab.production.some(p => p.station === "KITCHEN"));
  x.click("modal-close");
  assert(x.app.innerHTML.includes("não o enviou"));
});

check("item allocation unavailable after payments with no item association", () => {
  const x = mount();
  x.click("select-tab", { id: "t1" }); x.click("split");
  x.click("split-mode", { mode: "items" });
  assert(x.app.innerHTML.includes("Há pagamentos sem itens associados"));
  assert(x.app.innerHTML.includes("Quantidade de pessoas"));
});

console.log("All Caixa UX2 prototype regression scenarios passed.");
