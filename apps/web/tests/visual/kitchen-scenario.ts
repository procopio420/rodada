import { expect, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fixture } from "./fixtures";

// Demonstration model and adapters are imported only by tests, never the app.
const now = "2026-10-09T02:14:00Z";
const products = [
  { id: "v03-fries", name: "Fritas", asset: "c74be2bf7ae8d32da5f77ec39f311a18.svg" },
  { id: "v03-cod", name: "Bolinho de bacalhau", asset: "1e9830bdd3cf72f57dc17c0bd356214f.svg" },
  { id: "v03-sausage", name: "Calabresa", asset: "431ed6655f8c54cccf2eea5b7faf92ca.svg" },
  { id: "v03-pork", name: "Torresmo", asset: "73ba944a476ce094605977a1b0205ec9.svg" },
];
const timestamp = (seconds: number) => new Date(Date.parse(now) - seconds * 1000).toISOString();
const rows = [
  ["P22", "v03-cod", 2, "PREPARING", 790, null],
  ["P08", "v03-fries", 1, "PREPARING", 562, null],
  ["P08", "v03-sausage", 1, "PREPARING", 562, null],
  ["P25", "v03-fries", 2, "PREPARING", 375, null],
  ["P41", "v03-sausage", 1, "PREPARING", 250, null],
  ["P37", "v03-fries", 1, "NEW", 31, null],
  ["P12", "v03-sausage", 1, "READY", 900, 220],
  ["B4", "v03-cod", 1, "READY", 600, 80],
  ["P44", "v03-pork", 1, "PICKED_UP", 480, 120],
] as const;
export const kitchenScenario = {
  now, products,
  items: rows.map(([tab, productId, quantity, state, age, readyAge], index) => ({
    id: `v03-item-${index}`, order_id: `v03-order-${tab}`, product_id: productId,
    product_name: products.find(product => product.id === productId)!.name,
    tab_label: tab, quantity, state, created_at: timestamp(age),
    ready_at: readyAge === null ? null : timestamp(readyAge),
  })),
};
export const waitingItems = kitchenScenario.items.filter(item => ["NEW", "ACCEPTED", "PREPARING"].includes(item.state));
export const readyItems = kitchenScenario.items.filter(item => item.state === "READY");
export const transitItems = kitchenScenario.items.filter(item => item.state === "PICKED_UP");
export const kitchenBatches = products.map(product => ({ ...product, items: waitingItems.filter(item => item.product_id === product.id) }))
  .filter(batch => batch.items.length).map(batch => ({ ...batch, quantity: batch.items.reduce((sum, item) => sum + item.quantity, 0) }))
  .sort((a, b) => b.quantity - a.quantity || waitingItems.findIndex(item => item.product_id === a.id) - waitingItems.findIndex(item => item.product_id === b.id));
export const elapsed = (time: string) => { const seconds = (Date.parse(now) - Date.parse(time)) / 1000; return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`; };

export async function kitchenFixture(page: Page, station: "KITCHEN" | "BAR" = "KITCHEN") {
  await fixture(page, "normal", false, { now });
  await page.clock.pauseAt(new Date(now));
  await page.route(`**/api/pos/production/${station}/`, route => {
    expect(route.request().method()).toBe("GET");
    return route.fulfill({ json: { results: kitchenScenario.items } });
  });
  await page.route("**/api/pos/catalog/products/", route => route.fulfill({ json: { results: products.map(product => ({
    id: product.id, name: product.name, active: true, price_cents: 100, // test DTO only; price is outside compared regions
    fulfillment_station: station, availability: "AVAILABLE",
    icon: { id: `icon-${product.id}`, source: "UPLOADED", status: "READY", published_asset_url: `/product-icons/${product.id}.svg` },
  })) } }));
  await page.route("**/product-icons/v03-*.svg", async route => {
    const id = path.basename(new URL(route.request().url()).pathname, ".svg");
    const product = products.find(product => product.id === id)!;
    const body = await readFile(path.resolve(process.cwd(), "../../prototype/references/kitchen/assets", product.asset));
    await route.fulfill({ contentType: "image/svg+xml", body });
  });
}

/** Explicit data-only derivation of the preserved export. Original CSS/templates stay intact. */
export async function normalizeKitchenReference(page: Page) {
  return page.evaluate(({ scenario, batches }) => {
    const root = document.querySelector(".k")!;
    const sections = Array.from(root.querySelectorAll(":scope > section"));
    const waiting = scenario.items.filter(item => ["NEW", "ACCEPTED", "PREPARING"].includes(item.state));
    const ready = scenario.items.filter(item => item.state === "READY");
    const transit = scenario.items.filter(item => item.state === "PICKED_UP");
    const age = (time: string) => { const seconds = (Date.parse(scenario.now) - Date.parse(time)) / 1000; return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`; };
    const counters = root.querySelectorAll("header b");
    counters[1].textContent = String(new Set(waiting.map(item => item.order_id)).size);
    counters[3].textContent = String(ready.length);
    const templates = Array.from(sections[0].querySelectorAll(".dish"));
    const dishes = batches.map(batch => {
      const index = scenario.products.findIndex(product => product.id === batch.id);
      const dish = templates[index].cloneNode(true) as HTMLElement;
      dish.dataset.productId = batch.id;
      dish.querySelector(".n")!.textContent = batch.name;
      dish.querySelector(".q")!.textContent = String(batch.quantity);
      const image = dish.querySelector("img")!; image.setAttribute("src", `./assets/${batch.asset}`);
      const chips = dish.querySelector(".chips")!, template = chips.firstElementChild!;
      chips.replaceChildren(...batch.items.map(item => { const chip = template.cloneNode(true); chip.textContent = item.tab_label + (item.quantity > 1 ? ` ×${item.quantity}` : ""); return chip; }));
      return dish;
    });
    sections[0].replaceChildren(sections[0].querySelector(".lbl")!, ...dishes);
    const orders = [...new Set(waiting.map(item => item.order_id))];
    const ticketTemplates = Array.from(sections[1].querySelectorAll(".tk"));
    const newTag = ticketTemplates[4].querySelector(".i span")!.cloneNode(true);
    const tickets = orders.map((order, index) => {
      const items = waiting.filter(item => item.order_id === order), first = items[0];
      const ticket = ticketTemplates[index].cloneNode(true) as HTMLElement;
      ticket.dataset.orderId = order; ticket.dataset.state = first.state;
      // Keep the original location/customer demo metadata visibly unmatched.
      ticket.querySelector(".p")!.firstChild!.textContent = first.tab_label;
      ticket.querySelector(".i")!.textContent = items.map(item => `${item.quantity} ${item.product_name}`).join(" · ");
      if (first.state === "NEW") ticket.querySelector(".i")!.append(" ", newTag.cloneNode(true));
      ticket.querySelector(".a .mono")!.textContent = age(first.created_at);
      ticket.querySelector("button")!.textContent = first.state === "NEW" ? "Aceitar" : "Pronto";
      return ticket;
    });
    sections[1].replaceChildren(sections[1].querySelector(".lbl")!, ...tickets);
    sections[2].querySelector(".lbl")!.lastElementChild!.textContent = String(ready.length);
    const passes = Array.from(sections[2].querySelectorAll(".pass"));
    [...ready, ...transit].forEach((item, index) => {
      const row = passes[index] as HTMLElement;
      row.dataset.itemId = item.id; row.dataset.state = item.state;
      row.querySelector(".p")!.textContent = item.tab_label;
      row.querySelector(".i")!.textContent = `${item.quantity} ${item.product_name}`;
      row.querySelector(".w")!.textContent = item.state === "READY" ? `${index === 0 ? "Ninguém pegou" : "Esperando"} · ${age(item.ready_at!)}` : "Retirada registrada";
    });
    return { waitingOrders: orders.length, waitingItems: waiting.length, ready: ready.length, transit: transit.length };
  }, { scenario: kitchenScenario, batches: kitchenBatches });
}
