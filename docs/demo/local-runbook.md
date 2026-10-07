# Demo local — Rodada

This runbook uses the persisted Django API and the deterministic local dataset. It
does not require creating or editing rows in Django admin.

## Reset and seed

From the repository root, with the API dependencies installed:

```bash
./scripts/reset_local_demo.sh
```

The reset script refuses to run when `DEBUG` is not `1`. It flushes the configured
local database, migrates it, and recreates the demo venue. Never point it at a
production database.

To only create or refresh the demo records without clearing other local data:

```bash
cd apps/api
python manage.py migrate
python manage.py seed_demo
```

`seed_demo` is idempotent. It restores the demo catalogue's current price,
availability, station and active state, ensures one open demo cash shift, and keeps
the named demo users usable.

## Local credentials

These are local demo PINs only; they must not be deployed as production credentials.

| Staff member | PIN | Intended demo use |
| --- | --- | --- |
| Ana Gerente | `0420` | availability, payment and tab close |
| Bia Staff | `1234` | opening tabs, orders and fulfillment |

The staff login request is:

```text
POST /api/auth/login/
{"venue_id": 1, "display_name": "Bia Staff", "pin": "1234"}
```

Use its `session_token` on subsequent staff requests as
`Authorization: Bearer <session_token>`.

## Start the demo

With Docker:

```bash
docker compose up --build
docker compose exec api python manage.py migrate
docker compose exec api python manage.py seed_demo
```

Open `http://localhost:3000`. The API is `http://localhost:8000/api/`.

Without Docker, use separate terminals:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

```bash
cd apps/web
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000/api npm run dev
```

For Android, point the app's API base URL to the reachable development-machine
address (not Android's own `localhost`), then log in with the same demo staff
credentials.

## Verify the real backend loop

After migrations, run this from `apps/api`:

```bash
python manage.py smoke_demo
```

It logs in with the seeded credentials and verifies, via staff API routes:

1. stale-cart availability rejection;
2. tab creation and a Bar + Kitchen order;
3. price snapshots and exactly-once order confirmation;
4. item production transitions and persisted delivery work;
5. failed early close, partial payment, final payment and close;
6. rejection of a new order on the closed tab.
