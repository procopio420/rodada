// Reference-only V01 inspection. No product, API or database is started.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const { chromium } = require(process.env.RODADA_PLAYWRIGHT_PATH || '../apps/web/node_modules/playwright');

const root = path.resolve(__dirname, '..');
const output = path.join(root, 'docs/design/evidence/v01-night-agora');
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const regions = {
  phone: '.phone', header: '.phone .top', screen: '.phone .screen',
  title: '.phone .ahead', titleText: '.phone .ahead h1', counters: '.phone .cnt',
  counterValue: '.phone .cnt > div:first-child > b',
  firstRow: ':nth-match(.phone .row, 1)',
  firstDestination: ':nth-match(.phone .row, 1) .pl',
  firstAge: ':nth-match(.phone .row, 1) .age .t',
  firstAction: ':nth-match(.phone .row, 1) .ra button',
  navigation: '.phone .nav',
  bar: '.kds', barHeader: '.kds .kh', barProduction: '.kds .kcol.l',
  barPass: '.kds .kcol:not(.l)',
};
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.png': 'image/png' };

async function walk(dir) {
  const files = [];
  for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...await walk(file)); else files.push(file);
  }
  return files;
}

(async () => {
  await fs.mkdir(output, { recursive: true });
  const manifest = JSON.parse(await fs.readFile(path.join(root, 'prototype/references/manifest.json')));
  const sources = [];
  for (const reference of manifest) {
    const archive = path.join(root, 'prototype', reference.archive);
    assert.equal(hash(await fs.readFile(archive)), reference.sha256, `ZIP changed: ${reference.id}`);
    const directory = path.join(root, 'prototype/references', reference.id);
    const files = [archive, path.join(root, 'prototype/references', reference.entry), path.join(directory, 'support.js'), ...await walk(path.join(directory, 'vendor')), ...await walk(path.join(directory, 'assets'))];
    sources.push({ id: reference.id, files: await Promise.all(files.map(async file => ({ path: path.relative(root, file).replaceAll('\\', '/'), sha256: hash(await fs.readFile(file)) }))) });
  }
  const fontFiles = await walk(path.join(root, 'prototype/fonts'));
  const fonts = await Promise.all(fontFiles.map(async file => ({ path: path.relative(root, file).replaceAll('\\', '/'), sha256: hash(await fs.readFile(file)) })));
  const server = http.createServer(async (req, res) => {
    try {
      const target = path.resolve(root, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
      if (!target.startsWith(path.join(root, 'prototype') + path.sep)) { res.writeHead(403); res.end(); return; }
      res.setHeader('Content-Type', mime[path.extname(target)] || 'application/octet-stream');
      res.end(await fs.readFile(target));
    } catch { res.writeHead(404); res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch();
    const context = await browser.newContext({ viewport: { width: 1760, height: 1060 }, deviceScaleFactor: 1, locale: 'pt-BR', timezoneId: 'America/Sao_Paulo', colorScheme: 'dark' });
    const page = await context.newPage();
    const errors = [], resources = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => errors.push(`request failed: ${request.url()}`));
    page.on('response', response => { resources.push({ path: new URL(response.url()).pathname, status: response.status() }); });
    const origin = `http://127.0.0.1:${server.address().port}`;
    await page.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
    await page.clock.install({ time: new Date('2026-10-09T00:38:00Z') });
    await page.clock.pauseAt(new Date('2026-10-09T00:38:00Z'));
    await page.goto(origin + '/prototype/references/night/Main.dc.html');
    await page.locator('.phone .ahead h1').waitFor();
    assert.equal((await page.locator('.phone .ahead h1').textContent()).trim(), 'Agora');
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all([...document.images].map(image => image.decode()));
    });
    const fontState = await page.evaluate(() => ({ archivo: document.fonts.check('900 22px Archivo'), mono: document.fonts.check('700 20px "JetBrains Mono"'), faces: [...document.fonts].map(font => ({ family: font.family, status: font.status })) }));
    assert.ok(fontState.archivo && fontState.mono);
    assert.ok(fontState.faces.some(face => face.family.includes('Archivo') && face.status === 'loaded'));
    assert.ok(fontState.faces.some(face => face.family.includes('JetBrains Mono') && face.status === 'loaded'));
    const measured = {};
    for (const [name, selector] of Object.entries(regions)) {
      const locator = page.locator(selector);
      assert.equal(await locator.count(), 1, `Selector must be unique: ${selector}`);
      measured[name] = await locator.evaluate(element => {
        const box = element.getBoundingClientRect(), style = getComputedStyle(element);
        const properties = ['display', 'gridTemplateColumns', 'gridTemplateRows', 'padding', 'gap', 'fontFamily', 'fontSize', 'fontWeight', 'fontStretch', 'fontVariationSettings', 'lineHeight', 'letterSpacing', 'color', 'backgroundColor', 'borderRadius', 'boxShadow', 'overflow'];
        return { crop: { x: box.x, y: box.y, width: box.width, height: box.height }, text: element.innerText, style: Object.fromEntries(properties.map(property => [property, style[property]])) };
      });
      measured[name].selector = selector;
    }
    assert.deepEqual([measured.phone.crop.width, measured.phone.crop.height], [390, 844]);
    const captures = [];
    for (const name of ['phone', 'header', 'screen', 'navigation', 'bar']) {
      const locator = page.locator(regions[name]);
      const first = await locator.screenshot({ animations: 'disabled', caret: 'hide' });
      const second = await locator.screenshot({ animations: 'disabled', caret: 'hide' });
      assert.equal(hash(first), hash(second), `Unstable capture: ${name}`);
      await fs.writeFile(path.join(output, name + '.png'), first);
      captures.push({ region: name, file: name + '.png', sha256: hash(first), repeatedSha256: hash(second) });
    }
    assert.deepEqual(errors, []);
    assert.ok(resources.every(resource => resource.status === 200));
    // Network completion order varies even when the rendered reference is identical.
    resources.sort((left, right) => left.path.localeCompare(right.path));
    for (const source of sources) for (const file of source.files) assert.equal(hash(await fs.readFile(path.join(root, file.path))), file.sha256, `Source changed: ${file.path}`);
    for (const font of fonts) assert.equal(hash(await fs.readFile(path.join(root, font.path))), font.sha256);
    const contract = { base: '45c4742b3de4e6a21ed607342f75e53e18b07d7d', reference: 'night', entry: 'night/Main.dc.html', state: 'initial Agora / Bar', interactions: ['fresh document load; no demo action'], fixture: 'literal export state; test-only', clock: '2026-10-09T00:38:00Z; paused before navigation', environment: { os: process.platform, node: process.version, playwright: require((process.env.RODADA_PLAYWRIGHT_PATH || '../apps/web/node_modules/playwright') + '/package.json').version, chromium: browser.version(), viewport: { width: 1760, height: 1060 }, dpr: 1, locale: 'pt-BR', timezone: 'America/Sao_Paulo' }, normalization: ['paused clock and screenshot animation/caret handling only; no stylesheet/data/DOM changes'], chrome: { excluded: ['presentation rail', 'devlabel', 'outer device shadow'], phone: 'literal rounded phone retained; not an approved native baseline', statusBar: 'no simulated OS status bar in this initial phone; .top is product header', appRegions: ['header', 'screen', 'navigation'] }, regions: measured, fontState, fonts, captures, resources, sources, errors, status: 'V01 partial; reference only; no product parity assertion' };
    await fs.writeFile(path.join(output, 'measurements.json'), JSON.stringify(contract, null, 2) + '\n');
    console.log(JSON.stringify({ status: 'PASS', sources: sources.map(source => ({ id: source.id, files: source.files.length })), regions: Object.keys(measured).length, stableCaptures: captures.length, browser: browser.version(), phone: measured.phone.crop, bar: measured.bar.crop }));
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
