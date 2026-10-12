# Plano

Executar o [plano canônico do produto completo](../../docs/architecture/full-product-implementation-plan.md).

1. P0: auditar estado real e definir contratos/fixtures, antes de implementar lacunas.
2. P1: runtime, contratos tipados, configuração e autorização.
3. P2: turno básico conectado e recovery honesto; gate de piloto reduzido.
4. P3/P4: dispatch passivo e financeiro/pagamentos completos, com dependências explícitas.
5. P5: guest, administração e gerência completos.
6. P6: homologação, recuperação e rollout com evidência.

R01–R18 no plano detalham PRs e dependências. ADRs aceitos continuam autoridade: modular monolith, Atendimento Android, projeções, HTTP/SSE/outbox e telemetria passiva. Atualizar ADR apenas quando a implementação exigir decisão nova.

Validação desta entrega é documental. Futuras alterações de código executam os checks correspondentes ao domínio/superfície, incluindo visual Web para UI, PostgreSQL para concorrência financeira e instrumentação Android para jornadas nativas.

## Demo integrada Windows

Conferir Git/PRs; preservar serviços; provisionar stack portátil; reusar scripts HTTP e SQL read-only; executar suites PostgreSQL/browser, pricing, recibos e Android disponível; verificar restart; registrar evidência/limites e publicar PR draft sem merge.

O teste de revogação conserva a credencial anterior somente em memória antes de liberar a mesa. SSE pode apagar sessionStorage imediatamente; a request de credencial antiga continua exigindo exatamente 403/GUEST_SESSION_REVOKED, sem aceitar status alternativo nem enfraquecer autorização.

Secure pilot runtime slice: add explicit demo/pilot preflight, gate existing demo seed,
refuse active known demo PINs, document protected first-owner bootstrap via existing
models/audit; verify shell failures and empty disposable PostgreSQL startup/restart.

Preserve Nginx `$http_host` instead of normalized `$host` on the two authority headers; validate through actual Nginx/Next/Django in Docker smoke.
