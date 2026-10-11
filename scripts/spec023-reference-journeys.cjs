// Test-only inspection of the supplied exports. Never imports product code or touches API data.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const { chromium } = require('../apps/web/node_modules/playwright');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'docs/design/evidence/spec023-reference-journeys');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.ttf': 'font/ttf' };

(async () => {
  await fs.mkdir(out, { recursive: true });
  const original = JSON.parse(await fs.readFile(path.join(root, 'docs/design/evidence/v01-night-agora/measurements.json')));
  const allSources = [...original.sources.flatMap(source => source.files), ...original.fonts];
  for (const file of allSources) assert.equal(hash(await fs.readFile(path.join(root, file.path))), file.sha256, file.path);
  const server = http.createServer(async (req, res) => {
    try {
      const target = path.resolve(root, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
      assert.ok(target.startsWith(path.join(root, 'prototype') + path.sep));
      res.setHeader('Content-Type', types[path.extname(target)] || 'application/octet-stream');
      res.end(await fs.readFile(target));
    } catch { res.writeHead(404); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch();
  const contracts = [], errors = [];
  try {
    const context = await browser.newContext({ viewport: { width: 1760, height: 1060 }, deviceScaleFactor: 1, locale: 'pt-BR', timezoneId: 'America/Sao_Paulo' });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => errors.push(request.url()));
    page.on('response', response => { if (response.status() !== 200) errors.push(`${response.status()} ${response.url()}`); });
    await page.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
    await page.clock.install({ time: new Date('2026-10-09T00:38:00Z') });
    await page.clock.pauseAt(new Date('2026-10-09T00:38:00Z'));
    async function ready() {
      await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(image => image.decode())); });
      assert.ok(await page.evaluate(() => [...document.fonts].some(font => font.family.includes('Archivo') && font.status === 'loaded')));
    }
    async function freezeAnimation() {
      await page.addStyleTag({ content: '*, *::before, *::after { animation: none !important; transition: none !important; caret-color: transparent !important; }' });
    }
    async function record(id, entry, selector, state, interactions, optionalRegions = []) {
      // React commits and local font/image requests finish outside the paused demo clock.
      await page.waitForTimeout(250);
      await ready();
      const locator = page.locator(selector);
      assert.equal(await locator.count(), 1, selector);
      const measured = await locator.evaluate(element => {
        const rect = element.getBoundingClientRect();
        return { crop: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }, text: element.innerText };
      });
      const regions = [];
      for (const region of optionalRegions) {
        const elements = locator.locator(region);
        const count = await elements.count();
        for (let index = 0; index < count; index++) {
          regions.push(await elements.nth(index).evaluate((element, identity) => {
            const rect = element.getBoundingClientRect(), style = getComputedStyle(element);
            return { ...identity, crop: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }, text: element.textContent.trim(), styles: Object.fromEntries(['fontFamily','fontSize','fontWeight','fontStretch','fontVariationSettings','lineHeight','letterSpacing','color','backgroundColor','display','gridTemplateColumns','padding','gap','height','borderRadius'].map(key => [key, style[key]])) };
          }, { selector: region, instance: index + 1, count }));
        }
      }
      const first = await locator.screenshot({ animations: 'disabled', caret: 'hide' });
      const second = await locator.screenshot({ animations: 'disabled', caret: 'hide' });
      if (hash(first) !== hash(second)) {
        await fs.writeFile(path.join(out, `${id}.unstable-first.png`), first);
        await fs.writeFile(path.join(out, `${id}.unstable-second.png`), second);
      }
      assert.equal(hash(first), hash(second), `Unstable ${id}`);
      await fs.writeFile(path.join(out, `${id}.png`), first);
      contracts.push({ id, entry, selector, state, interactions, ...measured, regions, screenshot: `${id}.png`, sha256: hash(first), repeatedSha256: hash(second), fixture: 'literal export; simulated only' });
    }
    await page.goto(origin + '/prototype/references/night/Main.dc.html');
    await freezeAnimation();
    await page.locator('.phone .ahead h1').waitFor();
    const steps = await page.locator('.rail .step').count();
    assert.equal(steps, 19);
    for (let index = 0; index < steps; index++) {
      const step = page.locator('.rail .step').nth(index);
      const state = (await step.textContent()).trim();
      await step.click();
      await record(`night-${String(index + 1).padStart(2,'0')}`, 'night/Main.dc.html', '.phone', state, [`fresh export; click .rail .step instance ${index + 1}; export replay prepares preceding mock actions`], ['.top','.nav','.screen','.h1','.tname','.inp','.sheet','.btn']);
    }
    await page.locator('.rail .step').first().click();
    await page.locator('.rail .tgl').filter({ hasText: 'Pico' }).click();
    await record('night-peak', 'night/Main.dc.html', '.phone', 'Pico', ['step1', 'rail toggle Pico'], ['.pkh','.pkc','.row','.nav']);
    await page.locator('.rail .tgl').filter({ hasText: 'Sem sinal' }).click();
    await record('night-offline', 'night/Main.dc.html', '.phone', 'Pico offline', ['step1', 'Pico', 'Sem sinal'], ['.netbar','.nav']);
    await page.locator('.rail .tgl').filter({ hasText: 'Sem sinal' }).click();
    await record('night-recovery', 'night/Main.dc.html', '.phone', 'Literal synchronized mock state', ['toggle Sem sinal off; mock only, no reconciliation proof'], ['.netbar','.nav']);
    const manifest = JSON.parse(await fs.readFile(path.join(root, 'prototype/references/manifest.json')));
    for (const reference of manifest.filter(reference => reference.id !== 'night')) {
      await page.goto(origin + '/prototype/references/' + reference.entry);
      await freezeAnimation();
      const selector = { system: '.ds .sec', kitchen: '.k', peak: '.ph', connectivity: '.ph' }[reference.id];
      await page.locator(selector).first().waitFor();
      const count = await page.locator(selector).count();
      assert.ok(count > 0);
      for (let index = 0; index < count; index++) {
        const exact = `:nth-match(${selector}, ${index + 1})`;
        await record(`${reference.id}-${index + 1}`, reference.entry, exact, `literal instance ${index + 1}/${count}`, ['fresh document load; no behavior in static export'], ['h2','h4','.btn','.row','.age','.top','.net','.nav','.h1','.cnt','.pkc','.expo']);
      }
    }
    assert.deepEqual(errors, []);
    for (const file of allSources) assert.equal(hash(await fs.readFile(path.join(root, file.path))), file.sha256, file.path);
    const result = { spec: '023', scope: 'V01 reference states; no product parity approval', base: original.base, environment: original.environment, clock: original.clock, normalization: ['export rail replay is literal mock behavior', 'clock paused; test-only style disables animation/transition/caret', 'source files unchanged; no data/layout/color/font changes'], sources: allSources, contracts, errors, limitations: ['native comparison and baseline pending','static controls have no runtime behavior','offline payment and mocked synchronized state are not authorized domain behavior','responsive adaptations and hardware are separate contracts'] };
    await fs.writeFile(path.join(out, 'contracts.json'), JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify({ status: 'PASS', states: contracts.length, references: [...new Set(contracts.map(contract => contract.entry))], stablePairs: contracts.length }));
  } finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
