import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer, request as httpRequest } from 'node:http';
import { once } from 'node:events';
import { spawn } from 'node:child_process';

test('tenant guard preserves authority and upstream failures before auth dispatch', async () => {
  let status = 421;
  let payload = { code: 'VENUE_HOST_NOT_FOUND' };
  let mutations = 0;
  let contextSequence = [];
  const api = createServer(async (req, res) => {
    for await (const _chunk of req) { /* consume the complete body */ }
    if (req.method === 'POST') {
      mutations++;
      res.writeHead(421, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ code: 'VENUE_HOST_NOT_FOUND' }));
      return;
    }
    assert.equal(req.url, '/venue/context/');
    assert.equal(req.headers['x-rodada-bff-host'], 'unknown.rodada.bar');
    assert.match(req.headers['x-rodada-bff-signature'], /^[a-f0-9]{64}$/);
    res.writeHead(contextSequence.shift() ?? status, { 'content-type': 'application/json' });
    res.end(JSON.stringify(payload));
  });
  api.listen(0, '127.0.0.1'); await once(api, 'listening');
  const port = Number(process.env.RODADA_HOST_GUARD_TEST_PORT || 3115);
  const server = spawn(process.execPath, ['node_modules/next/dist/bin/next', 'start', '--hostname', '127.0.0.1', '--port', String(port)], {
    env: { ...process.env, RODADA_API_BASE_URL: `http://127.0.0.1:${api.address().port}`, RODADA_ENABLE_TENANT_HOST_UI: 'true', RODADA_BFF_HOST_SECRET: 'disposable-guard-test-secret-only' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  // Native fetch may ignore custom Host and retry421; http.request does neither.
  const call = (path = '/api/auth/me', method = 'GET', headers = {}, body) => new Promise((resolve, reject) => {
    const req = httpRequest(`http://127.0.0.1:${port}${path}`, { method, headers: { Host: 'unknown.rodada.bar', Origin: 'http://unknown.rodada.bar', ...headers } }, res => {
      res.resume();
      res.on('end', () => resolve({ status: res.statusCode, headers: new Headers(res.headers) }));
    });
    req.on('error', reject); req.end(body);
  });
  try {
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(Error('Next readiness timed out')), 30000);
      server.stdout.on('data', data => { if (data.toString().includes('Ready')) { clearTimeout(timeout); resolve(); } });
      server.once('error', e => { clearTimeout(timeout); reject(e); });
      server.once('exit', () => { clearTimeout(timeout); reject(Error('Next exited')); });
    });
    for (const code of [421, 403, 500, 503]) {
      status = code; payload = { code: code === 403 ? 'HOST_ASSERTION_INVALID' : 'VENUE_HOST_NOT_FOUND' };
      const r = await call(); assert.equal(r.status, code);
      assert.match(r.headers.get('cache-control'), /no-store/);
    }
    status = 200; payload = { mode: 'establishment', venue: { id: 7, slug: 'invalid', name: 'Invalid' } };
    assert.equal((await call()).status, 502, 'malformed context must not become421');
    payload = { mode: 'establishment', venue: { id: 'fake-test-id', slug: 'test', name: 'Test' } };
    assert.equal((await call()).status, 401, 'active host still requires auth');
    for (const path of ['/api/venue/context', '/manifest.webmanifest']) {
      for (const failure of [403, 503]) {
        contextSequence = [200, failure];
        assert.equal((await call(path)).status, failure, 'second lookup must preserve authority failures');
      }
    }
    for (const [path, method, headers, body] of [
      ['/api/auth/me', 'GET', { Cookie: 'rodada_staff_refresh=invalid-audit-proof' }],
      ['/api/guest/qr/resolve', 'POST', { 'content-type': 'application/json' }, '{"token":"invalid-audit-proof"}'],
    ]) {
      const before = mutations;
      assert.equal((await call(path, method, headers, body)).status, 421, 'Django revalidation after guard can still reject domain');
      assert.equal(mutations - before, 1, 'BFF must not replay mutation after421');
    }
    await new Promise(resolve => api.close(resolve));
    assert.equal((await call()).status, 503, 'unreachable authority must not become421');
  } finally {
    server.kill(); api.closeAllConnections(); if (api.listening) await new Promise(resolve => api.close(resolve));
  }
});
