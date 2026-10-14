# Tasks — Spec 028

**S1 em implementação:** ver [contrato, auditoria e evidências](s1-foundation.md). Os slices S2–S7 continuam pendentes; nenhum agente Windows ou instalador foi entregue.
**Legend:** [ ] = pending. Writing a spec does not count as implementing an item.

## Tracking por slice (um PR de implementação por slice)

Estes itens de tracking agregam as tarefas detalhadas abaixo; **S1 está implementada no PR #149, ainda aguardando CI/aprovação; S2–S7 continuam pendentes**. Não fechar slice apenas por abrir PR ou por CI verde: anexar evidências dos contratos em acceptance.md, SHA e ambiente.

- [ ] **S1 — Foundation:** schema/API/Access/credencial de máquina/isolamento/compatibilidade da Spec 015. Gate: acceptance **3 (parcial), 12, 15**; testes de migrations, permissão e regressão bridge; sem instalador.
- [ ] **S2 — Pairing:** serviço Windows inicial, proof-of-possession, pareamento Manager/Owner no Manage, heartbeat e revogação. Gate: acceptance **2, 3, 13 (start no Windows)**; teste de código vencido/replay e host sem usuário logado.
- [ ] **S3 — Printing MVP:** um PC -> uma rota -> printer endpoint, WinSpool/ESC-POS ou WindowsDriver, job da Spec 015 até SPOOL_ACCEPTED. Gate: acceptance **4, 5 (parcial), 8 (básico), 9, 10, 11, 15**; mocks Windows e teste E2E sem hardware obrigatório.
- [ ] **S4 — Multiagent:** múltiplos computadores/rotas e claim com lease/fencing; failover pré-envio e sem reenvio incerto. Gate: acceptance **5, 6, 7, 10, 12**; corrida real PostgreSQL + dois agentes simulados.
- [ ] **S5 — Compatibility:** perfis ESC/POS/Bematech candidata/WindowsDriver, 58/80, acentos, corte/diagnóstico e teste. Gate: acceptance **4, 8, 11, 14 (pré-requisitos)**; golden tests e spool virtual; aprovação física só na S7.
- [ ] **S6 — Distribution:** pipeline Windows, setup EXE, assinatura Authenticode, atualização, /downloads e Manage apontando para mesma release. Gate: acceptance **1, 13, 15**; install/uninstall/upgrade, SHA e assinatura; não declarar release pública stable antes do gate S7.
- [ ] **S7 — Pilot:** documentação da conexão real da Bematech, tickets reais, matriz, falhas, rollback e decisão de ativação. Gate: acceptance **1–15**, especialmente **14 físico**; testemunho e fotos do papel sem PII.

**Ordem:** S1 -> S2 -> S3 -> (S4 || S5) -> S6 -> S7. S6 pode ter preparação de CI em paralelo, mas depende da integração dos drivers/rotas para conclusão. Manter ownership distinto entre S4 e S5 e apontar todos os PRs para esta spec e ADR 0020.

## Contracts / backend
- [x] Trace Spec 015 state/route APIs and freeze backwards compatibility for legacy bridge (S1 evidence in s1-foundation.md).
- [x] Add scoped PrintAgent identity (Access), lifecycle and audit migrations (S1).
- [ ] Implement pairing start/status/approval: high-entropy single-use expiring codes, proof of possession, throttling and Venue membership.
- [x] Implement device-scoped credential issue/rotation/revocation and dedicated API authentication; never reuse staff refresh token (S1; provisioning via pairing is S2).
- [ ] Add discovered devices and AgentPrinterRoute, route profile/capability/version CAS, schema+indexes+retention.
- [ ] Implement agent heartbeat/version and manager status APIs without conflating physical printer health.
- [ ] Implement agent-limited claim/results using existing PrintJob lease/attempt token and mapping checks.
- [ ] Preserve PrintJob initial production uniqueness across endpoints; no double print when multiple agents can reach one endpoint.
- [ ] Fault handling for pre-send error, ambiguous submit, interrupted result, revoked device and route move during send.
- [ ] Validate server-side private-LAN destinations; no arbitrary internet print from configured route.
- [ ] New backend tests: isolation, replay, races, negative auth, CAS, health and failover safety.

## Windows agent
- [x] Standalone typed contracts and interfaces at apps/printer-agent, with contract parity test; no Django model dependencies (S1; no runtime service yet).
- [ ] Windows Service + optional local wizard/status window, no logged-in desktop session requirement.
- [ ] Installer setup/remove/repair + machine-scope DPAPI secrets/ACL and safe unpair.
- [ ] Windows Print Spooler printer/queue enumeration in service context.
- [ ] WinSpool GDI/raster WindowsDriver (non-RAW), print preview/test page and status normalization.
- [ ] Windows RAW spool adapter gated on verified ESC/POS profile; block raw commands to incompatible queue.
- [ ] LAN TCP adapter with private address validation, optional scoped discovery + manual IP.
- [ ] PrinterProfile registry (generic ESC/POS, WindowsDriver and conditional Bematech).
- [ ] Test ASCII/UTF-8/codepage behavior and Portuguese diacritics; feature flags for cut/QR/status.
- [ ] Agent telemetry, bounded redacted logs, local diagnostics, spool accepted != printed.
- [ ] Host restart/agent crash/resume safe attempt recovery; never blind-resend uncertain ticket.
- [ ] Simulate USB, shared Windows queue, network printer and duplicate network visibility in two agents.
- [ ] Background update with signature validation, idle/roll-back semantics and version compatibility.

## Web/landing/release
- [ ] Expand /manage/printing with Add computer, pairing approval, agent list/revoke, discovered printers and routes.
- [ ] Configure BAR, KITCHEN and receipt destination from logical endpoint; no raw credentials to browser.
- [ ] Add test print flow, normalized errors and visible uncertain result + reprint authorization.
- [ ] Add /downloads page to apps/landing, same stable artifact used by Manage, SHA/version/help.
- [ ] Windows GitHub Actions pipeline, lock dependencies, test install/uninstall, build immutable artifacts.
- [ ] Authenticode release signing and updater manifest; public stable download only after signing/hardware gate.
- [ ] Ops runbook onboarding, printer model compatibility matrix, support/recovery and rollback.

## Pilot acceptance
- [ ] Inventory Aderlan PC OS, printer models, connection/ports and installed drivers (real hardware).
- [ ] Print physical Bematech test page under actual service account on Windows.
- [ ] Run kitchen/bar correct station routing, original vs REIMPRESSÃO, receipt and PDF fallback.
- [ ] Simulate second Windows agent and network printer accessible by both; prove only one send.
- [ ] Test queue offline, USB unplugged, spool restart, LAN down, VPN/rebinding, revoked token, expired lease.
- [ ] Observe and record the outcome *on physical paper*; no CI-only go-live claim.
- [ ] Decide venue trigger mode OPTIONAL_MIRROR separately, after Spec 015 health/fallback gates.
- [ ] Record release SHA, installer checksum, profile/driver/OS and approved go/no-go sign-off.
