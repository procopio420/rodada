# Rodada API

Django + Django REST Framework em **modular monolith**.

## Estado atual

O primeiro slice executável implementa a fundação da Spec 008:

- `Venue`;
- `StaffMember`;
- `VenueStaffMembership`;
- roles/capabilities server-side;
- `DeviceRegistration`;
- `StaffSession`;
- `AuditEvent`;
- health/readiness endpoints.

Login/PIN HTTP, refresh, operator switching, reauth e UI entram no slice 008.2.

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

Endpoints iniciais:

- `GET /health/` — processo está vivo;
- `GET /ready/` — processo consegue consultar o banco.

## Testes

A suíte usa SQLite em memória apenas para testes rápidos de domínio/foundation:

```bash
pytest
python manage.py makemigrations --check --dry-run --settings=rodada_api.settings_test
```

PostgreSQL continua sendo o banco principal da aplicação.
