import { test } from 'node:test';
import assert from 'node:assert/strict';
import { beginOrderObservation, observeOrderIntentSaved } from '../lib/client/order-observation.ts';

const origin = { api_root: '/api/attendance', venue: 'fixture-venue', session: 'original-session',
  payload: { idempotency_key: 'a-random-financial-intent', lines: [{ note: 'never transmit' }] } };
const drain = () => new Promise(resolve => setImmediate(resolve));
async function until(predicate) {
  const deadline = Date.now() + 5000;
  while (!predicate()) {
    assert.ok(Date.now() < deadline, 'observation did not complete');
    await drain();
  }
}

test('passive observations redact financial data and correlate a replay without sharing its key', async () => {
  const originalFetch = globalThis.fetch;
  const sent = [];
  globalThis.fetch = async (url, options) => { sent.push({ url, body: JSON.parse(options.body), signal: options.signal }); return new Response(null, { status: 204 }); };
  try {
    observeOrderIntentSaved(origin);
    beginOrderObservation(origin, false).finish('UNKNOWN', 'UNCERTAIN');
    const replay = beginOrderObservation(origin, true);
    replay.finish('CONFIRMED'); replay.finish('UNKNOWN', 'UNCERTAIN');
    await until(() => sent.length === 3);
    assert.equal(sent.length, 3);
    assert.equal(new Set(sent.map(x => x.body.events[0].intent_ref)).size, 1);
    assert.ok(sent.every(x => /^[a-f0-9]{64}$/.test(x.body.events[0].intent_ref)));
    assert.ok(sent.every(x => x.url === '/api/attendance-observations' && x.signal instanceof AbortSignal));
    assert.ok(sent.every(x => x.body.origin_session === 'original-session'));
    assert.equal(JSON.stringify(sent).includes(origin.payload.idempotency_key), false);
    assert.equal(JSON.stringify(sent).includes('never transmit'), false);
    const attempts = sent.flatMap(x => x.body.events).filter(x => x.kind === 'ATTEMPT_FINISHED');
    assert.deepEqual(attempts.map(x => [x.outcome, x.recovery]), [['UNKNOWN', false], ['CONFIRMED', true]]);
    assert.equal(new Set(attempts.map(x => x.attempt_id)).size, 2);
  } finally { globalThis.fetch = originalFetch; }
});

test('unavailable telemetry is bounded and lossy, while legacy POS is not labelled UX2', async () => {
  const originalFetch = globalThis.fetch;
  let requests = 0;
  let release;
  const held = new Promise(resolve => { release = resolve; });
  globalThis.fetch = async () => { requests += 1; await held; throw new Error('endpoint unavailable'); };
  try {
    observeOrderIntentSaved({ ...origin, api_root: '/api/pos' });
    for (let count = 0; count < 40; count++) beginOrderObservation(origin, true).finish('UNKNOWN', 'UNCERTAIN');
    await until(() => requests === 8);
    assert.equal(requests, 8);
    release(); await drain();
    beginOrderObservation(origin, true).finish('CONFIRMED');
    await until(() => requests === 9);
    assert.equal(requests, 9);
  } finally { release(); globalThis.fetch = originalFetch; }
});


test('hash failure drops the observation without changing context or throwing', async () => {
  const originalDigest = crypto.subtle.digest;
  const originalFetch = globalThis.fetch;
  let calls = 0;
  crypto.subtle.digest = async () => { throw new Error('hash unavailable'); };
  globalThis.fetch = async () => { calls += 1; throw new Error('must not send'); };
  try {
    const copy = JSON.stringify(origin);
    assert.doesNotThrow(() => observeOrderIntentSaved(origin));
    assert.doesNotThrow(() => beginOrderObservation(origin, false).finish('UNKNOWN', 'UNCERTAIN'));
    await drain();
    assert.equal(calls, 0);
    assert.equal(JSON.stringify(origin), copy);
  } finally { crypto.subtle.digest = originalDigest; globalThis.fetch = originalFetch; }
});
