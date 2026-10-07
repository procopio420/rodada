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

GET   /manage/access/memberships/
PATCH /manage/access/memberships/{id}/
GET   /manage/access/devices/
PATCH /manage/access/devices/{id}/
GET   /manage/access/sessions/
POST  /manage/access/sessions/{id}/revoke/
GET   /manage/access/audit/
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


## Access management

As rotas de management exigem `staff.manage`; por default isso fica no role OWNER.

Mutações administrativas também exigem reautenticação recente. Atualização de membership usa `expected_version` para evitar last-write-wins silencioso. Suspender/revogar membership e revogar device encerram as sessões afetadas imediatamente.

Device em estado `REVOKED` não pode ser promovido novamente para `TRUSTED`; um aparelho revogado deve se registrar como nova instalação após o fluxo administrativo apropriado.


## Access invalidation e replay

`GET /auth/invalidation-events/?after=<cursor>` expõe um feed durável e escopado ao staff/session/device atual. Ele acelera atualização de role/device e limpeza de estado privilegiado nos clientes, mas nunca substitui a autorização da API.

Toda request autenticada continua revalidando membership, device e session no PostgreSQL. Comandos capturados para replay devem usar `authorize_replayed_command(...)`, que recarrega o estado atual e reavalia capability antes da execução.

Tokens staff usam namespace `rat_`; credenciais de guest não são aceitas pelo authenticator de staff. O logging padrão aplica redaction de PIN, access token, refresh token e Authorization Bearer.


## Catalog foundation

O módulo `catalog` mantém `Product` e `ProductAvailability` separados desde o início:

- `Product.active` controla publicação/configuração;
- `ProductAvailability.state` controla disponibilidade operacional;
- preço usa centavos inteiros;
- nome normalizado é único por Venue;
- todo Product novo recebe estado operacional `AVAILABLE`;
- `catalog_for_venue(...)` é a query canônica compartilhada para catálogo ativo.

Seed local idempotente:

```bash
python manage.py seed_demo_catalog
```

A mutation de disponibilidade entra em slice posterior, depois do contrato de escopo por estação.


## Tabs e Orders

O módulo `ordering` introduz o núcleo de consumo sem dependência de mesa/Customer:

- `Tab` pode ser anônima ou ter `display_label`;
- `Tab.version` prepara optimistic concurrency dos fluxos estruturais;
- todo `Order` pertence a uma Tab;
- `Order.source` suporta STAFF, CASHIER e GUEST;
- `OrderItem` captura nome/preço do Product no momento da confirmação;
- confirmação é transacional e revalida `Product.active` + `ProductAvailability` sob lock;
- um único item inválido rejeita o pedido inteiro;
- alteração posterior de catálogo/availability não reescreve item confirmado.

Endpoints staff iniciais:

```text
GET  /tabs/
POST /tabs/
GET  /tabs/{id}/
POST /tabs/{id}/orders/confirm/  # requires idempotency_key
```

Order confirmation is an idempotent command scoped to its Tab. A replay of the same
`idempotency_key` and cart returns the original order; reusing a key for a different
cart is rejected. Confirmed order-item price snapshots create Charges exactly once.

## Ledger and manual payments (partial Spec 006)

The canonical balance is derived from confirmed Charges, Payments and Refunds; no
mutable `paid` field exists on `Tab`. Manual cash, external terminal and other
fallback methods are confirmed only by the authenticated staff command and carry
actor/session/device audit provenance. Provider-backed Tap/card-online methods are
explicitly rejected until a provider adapter and server reconciliation exist.

```text
POST /tabs/{id}/payments/                 # payment.collect, idempotency_key
POST /payments/{payment_id}/refunds/      # refund.create, idempotency_key
POST /tabs/{id}/close/                    # payment.collect, only exposure zero
```

Refunds are append-only compensating records. Only confirmed money changes exposure;
pending provider records do not.

## Table operations (partial Spec 004)

`hospitality` mantém a mesa como contexto físico, fora do ledger. Uma ocupação pode
ter várias Tabs através de associações históricas; a Tab não recebe uma FK de mesa.
Fechar uma Tab, portanto, nunca libera uma mesa.

```text
GET  /hospitality/tables/
POST /hospitality/tables/                         # venue.configure
POST /hospitality/tables/{id}/occupy/             # table.manage, tab_id opcional
POST /hospitality/occupancies/{id}/tabs/          # table.manage
POST /hospitality/tables/{id}/release/            # table.manage
POST /hospitality/tables/{id}/cleaning/start/     # table.manage
POST /hospitality/tables/{id}/cleaning/complete/  # table.manage
```

O ciclo persistido é `AVAILABLE → OCCUPIED → DIRTY → CLEANING → AVAILABLE`.
`public_token` é aleatório/opaco para o QR físico; o resolver público e GuestSession
ainda pertencem ao próximo slice. A geração de acesso só aumenta no fim da limpeza.
