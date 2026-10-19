import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';

test('table-service gateway requires authentication and rejects financial paths', async () => {
  const port = Number(process.env.RODADA_GATEWAY_TEST_PORT || 3114);
  const server = spawn(process.execPath, ['node_modules/next/dist/bin/next', 'start', '--hostname', '127.0.0.1', '--port', String(port)]);
  try {
    await new Promise((resolve, reject) => {
      const deadline = setTimeout(() => reject(new Error('Gateway startup timed out')), 30000);
      server.stdout.on('data', data => { if (data.toString().includes('Ready')) { clearTimeout(deadline); resolve(); } });
      server.once('error', error => { clearTimeout(deadline); reject(error); });
      server.once('exit', code => { clearTimeout(deadline); reject(new Error(`Gateway stopped: ${code}`)); });
    });
    for (const [route, status, code] of [
      ['hospitality/tables/table-test/service/start/', 401, 'AUTH_REQUIRED'],
      ['hospitality/tables/table-test/service/open-tab/', 401, 'AUTH_REQUIRED'],
      ['hospitality/occupancies/occupancy-test/tabs/open/', 401, 'AUTH_REQUIRED'],
      ['hospitality/occupancies/occupancy-test/responsibility/claim/', 401, 'AUTH_REQUIRED'],
      ['tabs/tab-test/payments/', 403, 'ATTENDANCE_OPERATION_DISABLED'],
      ['cash/points/cash-test/withdrawal/', 403, 'ATTENDANCE_OPERATION_DISABLED'],
      ['tabs/tab-test/refunds/', 403, 'ATTENDANCE_OPERATION_DISABLED'],
    ]) {
      const response = await fetch(`http://127.0.0.1:${port}/api/attendance/${route}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: '{}' });
      assert.equal(response.status, status, route);
      assert.equal((await response.json()).code, code, route);
    }
    const cashPayload = { method: 'CASH', amount_cents: 100, expected_version: 2,
      cash_point_id: '11111111-1111-4111-8111-111111111111',
      originating_session_id: '22222222-2222-4222-8222-222222222222', idempotency_key: '033-gateway' };
    for (const [body, status] of [
      [cashPayload, 401],
      [{ ...cashPayload, method: 'PIX' }, 403],
      [{ ...cashPayload, method: 'CARD' }, 403],
      [{ ...cashPayload, amount_cents: 0 }, 403],
      [{ ...cashPayload, amount_cents: 1.1 }, 403],
      [{ ...cashPayload, expected_version: 0 }, 403],
      [{ ...cashPayload, provider: 'fake' }, 403],
      [{ ...cashPayload, cash_point_id: null }, 403],
    ]) {
      const response = await fetch(`http://127.0.0.1:${port}/api/attendance/tabs/tab-test/payments/`, {
        method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body),
      });
      assert.equal(response.status, status);
    }
    assert.equal((await fetch(`http://127.0.0.1:${port}/api/attendance/cash/points/`)).status, 401);
    for (const body of [
      { kind: 'MOVE_LOCATION', expected_version: 1, occupancy_id: '11111111-1111-4111-8111-111111111111', idempotency_key: 'move' },
      { kind: 'MERGE', expected_version: 1 },
      { kind: 'MOVE_LOCATION', expected_version: 1, lines: [] },
    ]) {
      const response = await fetch(`http://127.0.0.1:${port}/api/attendance/tabs/tab-test/operations/`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
      assert.equal(response.status, body.kind === 'MOVE_LOCATION' && !('lines' in body) ? 401 : 403);
    }
  } finally { server.kill(); }
});
