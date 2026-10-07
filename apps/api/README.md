# Rodada API

Django + Django REST Framework em **modular monolith**.

## Estado atual

A fundação executável cobre os primeiros slices da Spec 008:

- `Venue`;
- `StaffMember` + PIN com verifier do Django;
- `VenueStaffMembership`;
- STAFF / CASHIER / MANAGER / OWNER + capabilities server-side;
- `DeviceRegistration`;
- `StaffSession` com access/refresh opacos e revogáveis;
- throttle/backoff de PIN por Venue + conta + device;
- `AuditEvent`;
- health/readiness;
- autenticação DRF protegida por padrão.

Management endpoints, realtime invalidation e UI entram nos próximos slices. Fast operator switch e privileged reauthentication já estão disponíveis no backend.

## Auth API

```text
POST /auth/login/
POST /auth/refresh/
GET  /auth/me/
POST /auth/lock/
POST /auth/logout/
POST /auth/switch-operator/
POST /auth/reauthenticate/
```

Login recebe `venue_slug`, `login_identifier`, `pin`, `installation_id`, `platform` e label opcional.

O backend retorna access token curto e refresh token com expiração absoluta de sessão. Apenas hashes SHA-256 dos tokens aleatórios de alta entropia são persistidos; refresh rotaciona access + refresh.

Rotas protegidas usam:

```http
Authorization: Bearer rat_...
```

Erros de autorização usam códigos estáveis como `AUTH_REQUIRED`, `ACCESS_TOKEN_EXPIRED`, `MEMBERSHIP_REVOKED`, `DEVICE_REVOKED`, `CAPABILITY_REQUIRED` e `AUTH_THROTTLED`.

## Estrutura

```text
modules/
  venue/
  access/
  audit/
rodada_api/
tests/
```

Novas capacidades devem seguir as fronteiras de `docs/architecture/overview.md`; não criar um app Django por tabela.

## Ambiente local

Python 3.12+.

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

export POSTGRES_DB=rodada
export POSTGRES_USER=rodada
export POSTGRES_PASSWORD=rodada
export POSTGRES_HOST=localhost

python manage.py migrate
python manage.py runserver
```

Configuração relevante:

- `RODADA_ACCESS_TOKEN_TTL_SECONDS` — default 900;
- `RODADA_REFRESH_TOKEN_TTL_SECONDS` — default 43200;
- `RODADA_PIN_FAILURE_THRESHOLD` — default 5;
- `RODADA_PIN_BACKOFF_BASE_SECONDS` — default 15;
- `RODADA_PIN_BACKOFF_MAX_SECONDS` — default 300;
- `RODADA_REAUTH_WINDOW_SECONDS` — default 300.

## Testes

A suíte usa SQLite em memória apenas para testes rápidos de domínio/API:

```bash
pytest
python manage.py makemigrations --check --dry-run --settings=rodada_api.settings_test
```

PostgreSQL continua sendo o banco principal da aplicação.
