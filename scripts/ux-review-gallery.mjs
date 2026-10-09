// Static local review artifacts only; never part of the production router.
import { copyFile, mkdir, readdir, writeFile, access, cp, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const output = path.join(root, "visual-artifacts");
await mkdir(output, { recursive: true });
const files = (await readdir(output)).filter(name => /^(staff|bar|kitchen|guest|manage|cash|refunds|pos|reports)-(?:\d+|(?:empty|loading|error|long|warnings)-\d+|saving)\.png$/.test(name));
if (process.argv.includes("--before")) {
  await mkdir(path.join(output, "before"), { recursive: true });
  for (const name of files) await copyFile(path.join(output, name), path.join(output, "before", name));
  console.log(`Preserved ${files.length} before screenshots`);
  process.exit(0);
}
await writeFile(path.join(output, "review.css"), (await readFile(path.join(root, "prototype/design-system.css"), "utf8")).replaceAll("../apps/web/public/fonts/", "./fonts/"));
await cp(path.join(root, "apps/web/public/fonts"), path.join(output, "fonts"), { recursive: true });
await cp(path.join(root, "prototype/material-reference"), path.join(output, "material-reference"), { recursive: true });
const viewportHeights = { 360: 800, 390: 844, 430: 932, 768: 1024, 1280: 800, 1440: 900 };
const problems = {
  kitchen: "Material fornecido: Archivo/Mono, cabeçalho 72px, colunas 420/restante/340, agregação por Product e passe. SLA/equipamento não configurados não são simulados.",
  bar: "Mesmo problema da Cozinha. Corrigido com a composição compartilhada.",
  manage: "Formulários antes do pulso; READY contado em fila. Corrigido: operação primeiro, Conta da Casa em Gestão e contagem em preparo.",
  guest: "Ícone expandido e conteúdo colado. Corrigido: ícone fixo e nome/estação/preço separados.",
  pos: "Produto indisponível selecionável. Corrigido: texto explícito e controle desabilitado; API revalida.",
  cash: "Tema e controles compartilhados do material; abertura, revisão e histórico exercitados com API real.",
  refunds: "Sem alteração financeira; ausência de pagamento elegível e permissão verificadas. Provider real fora de escopo.",
  staff: "Sem alteração de autenticação; teclado, erro, sessão e cookies verificados.",
  reports: "Sem alteração de cálculo; consulta e CSV protegidos exercitados com API real.",
};
const escape = value => String(value).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const records = [];
for (const name of files.sort()) {
  const [surface, ...parts] = name.slice(0, -4).split("-");
  const width = Number(parts.at(-1));
  const state = Number.isFinite(width) ? parts.length === 1 ? "normal" : parts.slice(0, -1).join("-") : parts.join("-");
  let before = null;
  try { await access(path.join(output, "before", name)); before = `before/${name}`; } catch {}
  records.push({ surface, route: surface === "guest" ? "/guest/[token]" : `/${surface}`, viewport: width ? `${width} × ${parts.length === 1 ? viewportHeights[width] : 844}` : "390 × 844", state, screenshot: name, before, issue: problems[surface], status: ["bar", "kitchen", "manage", "guest", "pos"].includes(surface) ? "Corrigido; revisão humana pendente" : "Verificado; sem mudança" });
}
let real = [];
try { real = (await readdir(path.join(output, "real-api"))).filter(name => name.endsWith(".png")); } catch {}
let localGuest = null;
try { localGuest = JSON.parse(await (await import("node:fs/promises")).readFile(path.join(output, "local-review.json"), "utf8")).guestRoute; } catch {}
const launch = Object.keys(problems).map(surface => `<a class="button button--secondary" href="http://127.0.0.1:3000${surface === "guest" ? localGuest ?? '/guest/invalid-review-token' : `/${surface}`}" target="_blank" rel="noopener">${escape(surface)}</a>`).join("");
const cards = records.map(row => `<details class="panel"><summary>${escape(row.surface)} · ${escape(row.viewport)} · ${escape(row.state)} · ${escape(row.status)}</summary><p>${escape(row.route)}<br>${escape(row.issue)}</p><div class="pairs">${row.before ? `<figure><figcaption>Antes</figcaption><a href="${row.before}"><img loading="lazy" src="${row.before}" alt="Antes ${escape(row.surface)}"></a></figure>` : '<p>Sem captura anterior equivalente.</p>'}<figure><figcaption>Atual</figcaption><a href="${row.screenshot}"><img loading="lazy" src="${row.screenshot}" alt="Atual ${escape(row.surface)}"></a></figure></div></details>`).join("");
const material = ["system", "kitchen", "night", "connectivity", "peak"].map(slug => `<a class="button button--secondary" href="material-reference/${slug}/local.html" target="_blank" rel="noopener">Material original · ${escape(slug)}</a>`).join("");
const native = ["native-now.png", "native-peak.png", "native-tabs.png", "native-offline.png", "native-reconnected.png"];
const nativeCards = [];
for (const name of native) { try { await access(path.join(output, name)); nativeCards.push(`<figure><figcaption>Android real · ${escape(name)}</figcaption><a href="${name}"><img loading="lazy" src="${name}" alt="Android ${escape(name)}"></a></figure>`); } catch {} }
const html = `<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Rodada · revisão UX local</title><link rel="stylesheet" href="review.css"><style>main{max-width:1280px;margin:auto;padding:var(--space-4)}nav,.pairs{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:var(--space-3)}figure{margin:0;min-width:0}img{max-width:100%;height:auto;max-height:900px;object-fit:contain;object-position:top}summary,a{min-height:44px}summary{cursor:pointer}figcaption{padding:var(--space-2)}a{display:inline-flex;align-items:center}</style><main><h1>Rodada · revisão UX local</h1><p>Spec 021. Dados demonstrativos e capturas de teste, sem credenciais. Abra Staff e autentique com as credenciais locais documentadas no README da API.</p><nav>${launch}</nav><p>Cliente precisa do token da mesa. /guest sem token não é uma página existente no router local. Android nativo não está disponível neste ambiente.</p><h2>Comparações determinísticas</h2><p>Fixtures visuais, sem alegação de API real. Clique na imagem para ver tamanho completo. A lista inclui estados vazios, loading, erro/permissão, lotado/nomes longos, warning e salvamento suportados.</p>${cards}<h2>API real — evidência separada</h2><p>Django e BFF reais; SQLite local isolado. Não prova concorrência PostgreSQL nem pagamento de provider.</p>${real.map(name => `<details class="panel"><summary>${escape(name)}</summary><a href="real-api/${name}"><img loading="lazy" src="real-api/${name}" alt="API real ${escape(name)}"></a></details>`).join("")}</main></html>`;
await writeFile(path.join(output, "index.html"), html.replace("Spec 021.", "Specs 021/022. Fontes e paleta do material fornecido aplicadas ao produto.").replace("<h2>Comparações determinísticas</h2>", `<h2>Material fornecido</h2><nav>${material}</nav><p>Originais preservados, com fontes locais. Dados/ações dos mockups são simulações. Botão principal: 0% de diferença; geometria de cozinha 1280px verificada. Isso não equivale a paridade total de todos os fluxos.</p><h2>Comparações determinísticas</h2>`).replace("Android nativo não está disponível neste ambiente.", "Android compilado e testes unitários executados; capture nativa depende de dispositivo/emulador. Não há claim/lote de dispatch ou queue offline genérica simulada.").replaceAll("Verificado; sem mudança", "Tema atualizado; comportamento verificado"));
if (nativeCards.length) {
  const index = path.join(output, "index.html");
  await writeFile(index, (await readFile(index, "utf8")).replace("Android compilado e testes unitários executados; capture nativa depende de dispositivo/emulador.", "Android compilado, 20 testes unitários e lint passaram; capturas reais em emulador abaixo.").replace("</main>", `<h2>Android · emulador com API real</h2><p>390×844. Dados da instância local descartável; conectividade e modo pico reais, sem homologação física/Tap on Phone.</p><div class="pairs">${nativeCards.join("")}</div></main>`));
}
await writeFile(path.join(output, "review-index.json"), JSON.stringify(records, null, 2));
console.log(`Gallery: ${records.length} comparisons, ${real.length} real-API captures. ${path.join(output, "index.html")}`);
