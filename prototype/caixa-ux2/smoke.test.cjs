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


check("equal split rejects tampered cash installment and preserves pending part", () => {
  const x=mount();
  x.click("select-tab",{id:"t2"});x.click("split");x.click("split-plus");x.click("split-plus");x.click("split-continue");
  x.input("tendered","28,00");x.click("confirm-payment");
  x.click("next-split");
  assert(x.app.innerHTML.includes("valor fixo"));
  x.input("payAmount","1,00");x.input("tendered","1,00");x.click("confirm-payment");
  let tab=x.db().tabs.find(t=>t.id==="t2");
  assert.equal(tab.payments.length,1);
  assert.equal(tab.splitPlan.paidParts,1);
  x.input("payAmount","28,00");x.input("tendered","28,00");x.click("confirm-payment");
  tab=x.db().tabs.find(t=>t.id==="t2");
  assert.equal(tab.payments.length,2);
  assert.equal(tab.splitPlan.paidParts,2);
});

check("split installment cannot bypass locked amount for Pix/Card", () => {
  const x=mount();
  x.click("select-tab",{id:"t2"});x.click("split");x.click("split-plus");x.click("split-plus");x.click("split-continue");
  x.click("method",{method:"PIX"});
  x.input("payAmount","1,00");x.click("confirm-payment");
  assert.equal(x.db().attempts.length,0);
  x.input("payAmount","28,00");x.click("confirm-payment");
  assert.equal(x.db().attempts.length,1);
  assert.equal(x.db().attempts[0].amount,2800);
});

check("cash refund cannot drive physical drawer below zero; supplement first", () => {
  const x=mount();x.click("select-tab",{id:"t2"});x.click("pay");x.input("tendered","112,00");
  x.click("confirm-payment");x.click("close-tab");
  const payment=x.db().activity.find(a=>a.type==="payment"&&a.tabId==="t2");
  const drawerExpected=()=>x.db().drawer.movements.reduce((n,m)=>n+m.amount,0);
  x.click("nav",{view:"shift"});x.click("movement",{type:"out"});
  x.input("movementAmount",(drawerExpected()/100).toFixed(2).replace(".",","));
  x.input("movementReason","Sangria ao cofre");x.click("commit-movement");
  assert.equal(drawerExpected(),0);
  x.click("nav",{view:"activity"});x.click("refund",{id:payment.id});
  x.input("refundReason","Cliente solicitou");x.input("refundPin","1234");
  assert(x.app.innerHTML.includes("Dinheiro insuficiente"));
  x.click("commit-refund");assert.equal(drawerExpected(),0);
  assert.equal(x.db().tabs.find(t=>t.id==="t2").payments[0].refund,0);
  x.click("modal-close");x.click("nav",{view:"shift"});x.click("movement",{type:"in"});
  x.input("movementAmount","112,00");x.input("movementReason","Suprimento autorizado");x.click("commit-movement");
  x.click("nav",{view:"activity"});x.click("refund",{id:payment.id});
  x.input("refundReason","Cliente solicitou");x.input("refundPin","1234");x.click("commit-refund");
  assert.equal(drawerExpected(),0);
  assert.equal(x.db().tabs.find(t=>t.id==="t2").payments[0].refund,11200);
});

check("undelivered change blocks counting and closing across reload", () => {
  const x=mount();x.click("pay");x.input("tendered","200,00");x.click("confirm-payment");
  x.click("nav",{view:"shift"});
  assert(x.app.innerHTML.includes("troco(s) ainda não marcado(s)"));
  x.click("start-count");
  assert.equal(x.db().drawer.counting,false);
  const y=mount(x.saved.current);y.click("nav",{view:"shift"});
  y.click("start-count");assert.equal(y.db().drawer.counting,false);
  y.click("dismiss-change");y.click("start-count");
  assert.equal(y.db().drawer.counting,true);
  y.input("countInput","1.384,50");y.click("count-next");y.click("commit-count");
  assert.equal(y.db().drawer.open,false);
  assert(y.db().activity.some(a=>a.title==="Troco entregue (demo)"));
});

check("post-close refund is discoverable and requires managerial review", () => {
  const x=mount();x.click("select-tab",{id:"t2"});x.click("pay");x.input("tendered","112,00");
  x.click("confirm-payment");x.click("close-tab");
  const activity=x.db().activity.find(a=>a.type==="payment"&&a.tabId==="t2");
  x.click("nav",{view:"activity"});x.click("refund",{id:activity.id});
  x.input("refundReason","Cliente solicitou");x.input("refundPin","1234");x.click("commit-refund");
  x.click("nav",{view:"receive"});
  assert(x.app.innerHTML.includes("C-2837"));
  assert(x.app.innerHTML.includes("Revisar estorno"));
  x.click("review-refund",{id:"t2"});x.input("refundReviewNote","Encaminhado ao gerente");
  x.input("refundReviewPin","9999");x.click("commit-refund-review");
  assert.equal(x.db().tabs.find(t=>t.id==="t2").refundReview,"PENDING");
  x.input("refundReviewPin","1234");x.click("commit-refund-review");
  const tab=x.db().tabs.find(t=>t.id==="t2");
  assert.equal(tab.refundReview,"REVIEWED");
  assert.equal(tab.closed,true);
  assert.equal(tab.payments[0].refund,11200);
  assert(x.db().activity.some(a=>a.title==="Revisão gerencial de estorno"));
  x.click("filter",{filter:"closed"});
  assert(x.app.innerHTML.includes("Estorno revisado"));
});

check("open modal suppresses change overlay, preserves reminder on return", () => {
  const x=mount();x.click("pay");x.input("tendered","200,00");x.click("confirm-payment");
  assert(x.app.innerHTML.includes('class="change-reminder"'));
  x.click("select-tab",{id:"t2"});x.click("pay");
  assert(x.app.innerHTML.includes('class="modal-screen"'));
  assert(!x.app.innerHTML.includes('class="change-reminder"'));
  x.click("modal-close");
  assert(x.app.innerHTML.includes('class="change-reminder"'));
  assert.equal(x.db().changeNotices.length,1);
  assert(html.includes(".change-reminder{position:fixed;z-index:45;"));
});

check("rerender preserves scroll position within payment modal", () => {
  const app={innerHTML:""};
  const events={};
  let snapshot=null;
  let oldBody={scrollTop:278,scrollLeft:6};
  const document={
    activeElement:null,
    querySelector(selector){
      if(selector==="#app")return app;
      if(selector===".modal-body")return oldBody;
      return null;
    },
    addEventListener(name,fn){events[name]=fn;},
  };
  vm.runInNewContext(source,{
    document,window:{scrollY:0,scrollTo(){},print(){}},
    localStorage:{getItem(){return snapshot},setItem(_key,v){snapshot=v}},
    crypto:{randomUUID:()=>"scroll-id"},structuredClone,
    setTimeout:()=>0,clearTimeout(){},
  },{timeout:1000});
  const click=(act,extra={})=>{const target={dataset:{act,...extra},closest:()=>({dataset:{act,...extra}})};events.click({target})};
  click("pay");
  const before=oldBody;
  before.scrollTop=278;before.scrollLeft=6;
  // A real browser replaces the scroll container during innerHTML; model the
  // replacement on the next lookup so the regression is observable without a browser.
  let first=true,newBody={scrollTop:0,scrollLeft:0};
  document.querySelector=selector=>{
    if(selector==="#app")return app;
    if(selector===".modal-body"){if(first){first=false;return before;}return newBody}
    return null;
  };
  click("method",{method:"PIX"});
  assert.equal(newBody.scrollTop,278);
  assert.equal(newBody.scrollLeft,6);
});


check("cashier sees plain-language Add/Remove money actions and not accounting jargon alone", () => {
  const x=mount();x.click("nav",{view:"shift"});
  assert(x.app.innerHTML.includes("Retirar dinheiro"));
  assert(x.app.innerHTML.includes("Adicionar dinheiro"));
  assert(x.app.innerHTML.includes("Sangria · levar ao cofre"));
  assert(x.app.innerHTML.includes("Suprimento · colocar troco"));
  assert(x.app.innerHTML.includes("não registram venda ou pagamento"));
});

check("sangria modal explains withdrawal and accurately decreases drawer balance", () => {
  const x=mount();x.click("nav",{view:"shift"});
  const cash=()=>x.db().drawer.movements.reduce((n,m)=>n+m.amount,0);
  const start=cash();
  x.click("movement",{type:"out"});
  assert(x.app.innerHTML.includes("Retirar dinheiro da gaveta"));
  assert(x.app.innerHTML.includes("O dinheiro vai SAIR do caixa"));
  assert(x.app.innerHTML.includes("guardar no cofre"));
  x.input("movementAmount","200,00");x.click("reason",{reason:"Envio ao cofre"});
  assert(x.app.innerHTML.includes("Dinheiro esperado depois"));
  assert(x.app.innerHTML.includes("Confirmar retirada"));
  x.click("commit-movement");
  assert.equal(cash(),start-20000);
  assert(x.app.innerHTML.includes("Retirada · Sangria"));
  assert.equal(x.db().drawer.movements.at(-1).kind,"Sangria");
});

check("suprimento modal explains cash addition and increases physical drawer only", () => {
  const x=mount();x.click("nav",{view:"shift"});
  const cash=()=>x.db().drawer.movements.reduce((n,m)=>n+m.amount,0);
  const start=cash();const existingPayments=x.db().tabs.reduce((n,t)=>n+t.payments.length,0);
  x.click("movement",{type:"in"});
  assert(x.app.innerHTML.includes("Adicionar dinheiro à gaveta"));
  assert(x.app.innerHTML.includes("O dinheiro vai ENTRAR no caixa"));
  assert(x.app.innerHTML.includes("dar troco"));
  x.input("movementAmount","100,00");x.click("reason",{reason:"Reforço de troco"});
  assert(x.app.innerHTML.includes("Confirmar entrada"));
  x.click("commit-movement");
  assert.equal(cash(),start+10000);
  assert.equal(x.db().drawer.movements.at(-1).kind,"Suprimento");
  assert.equal(x.db().tabs.reduce((n,t)=>n+t.payments.length,0),existingPayments);
  assert(x.app.innerHTML.includes("Entrada · Suprimento"));
});
console.log("All Caixa UX2 prototype regression scenarios passed.");
