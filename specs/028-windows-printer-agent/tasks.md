# Tasks — Spec 028

**Progresso atual (20/10/2026):** S1/S2 integradas; S3–S6 integradas pelos PRs #274, #275, #276 e #278; QA downloads integrado por #282. Protocolo, verificador e preparação automatizada de S7 incluídos nesta entrega (#280). Distribuição stable e homologação física permanecem NO-GO. Ver [evidências e pendências](completion-20261020.md).
**Legend:** [ ] = pending. Writing a spec does not count as implementing an item.

## Tracking por slice (um PR de implementação por slice)

Estes itens de tracking agregam as tarefas detalhadas abaixo; **S1 está integrada pelo PR #149; S2 está integrada no PR #155; S3/S4/S5/S6 software integrado; S7 preparado, sem aceite físico ou distribuição stable**. Não fechar slice apenas por abrir PR ou por CI verde: anexar evidências dos contratos em acceptance.md, SHA e ambiente.

- [x] **S1 — Foundation:** schema/API/Access/credencial de máquina/isolamento/compatibilidade da Spec 015. Gate: acceptance **3 (parcial), 12, 15**; testes de migrations, permissão e regressão bridge; sem instalador.
- [x] **S2 — Pairing:** serviço Windows inicial, proof-of-possession, pareamento Manager/Owner no Manage, heartbeat e revogação. Gate: acceptance **2, 3, 13 (start no Windows)**; teste de código vencido/replay e host sem usuário logado.
- [x] **S3 — Printing MVP:** um PC -> uma rota -> printer endpoint, WinSpool/ESC-POS ou WindowsDriver, job da Spec 015 até SPOOL_ACCEPTED. Gate: acceptance **4, 5 (parcial), 8 (básico), 9, 10, 11, 15**; mocks Windows e teste E2E sem hardware obrigatório.
- [x] **S4 — Multiagent:** múltiplos computadores/rotas e claim com lease/fencing; failover pré-envio e sem reenvio incerto. Gate: acceptance **5, 6, 7, 10, 12**; corrida real PostgreSQL + dois agentes simulados.
- [x] **S5 — Compatibility:** perfis ESC/POS/Bematech candidata/WindowsDriver, 58/80, acentos, corte/diagnóstico e teste. Gate: acceptance **4, 8, 11, 14 (pré-requisitos)**; golden tests e spool virtual; aprovação física só na S7.
- [ ] **S6 — Distribution:** pipeline Windows, setup EXE, assinatura Authenticode, atualização, /downloads e Manage apontando para mesma release. Gate: acceptance **1, 13, 15**; install/uninstall/upgrade, SHA e assinatura; não declarar release pública stable antes do gate S7.
- [ ] **S7 — Pilot:** documentação da conexão real da Bematech, tickets reais, matriz, falhas, rollback e decisão de ativação. Gate: acceptance **1–15**, especialmente **14 físico**; testemunho e fotos do papel sem PII.

**Ordem:** S1 -> S2 -> S3 -> (S4 || S5) -> S6 -> S7. S6 pode ter preparação de CI em paralelo, mas depende da integração dos drivers/rotas para conclusão. Manter ownership distinto entre S4 e S5 e apontar todos os PRs para esta spec e ADR 0020.

## Contracts / backend
- [x] Trace Spec 015 state/route APIs and freeze backwards compatibility for legacy bridge (S1 evidence in s1-foundation.md).
- [x] Add scoped PrintAgent identity (Access), lifecycle and audit migrations (S1).
- [x] Implement pairing start/status/approval: high-entropy single-use expiring codes, proof of possession, throttling and Venue membership.
- [x] Implement device-scoped credential issue/rotation/revocation and dedicated API authentication; never reuse staff refresh token (S1; provisioning via pairing is S2).
- [x] Add discovered devices and AgentPrinterRoute, route profile/capability/version CAS, schema+indexes; retained identity/history capped at 500 printers per installation (no TTL).
- [x] Implement agent heartbeat/version and manager status APIs without conflating physical printer health.
- [x] Implement agent-limited claim/results using existing PrintJob lease/attempt token and mapping checks.
- [x] Preserve PrintJob initial production uniqueness across endpoints; one executable fenced attempt per job/intent when multiple agents can reach one endpoint; no physical exactly-once claim.
- [x] Fault handling for pre-send error, ambiguous submit, interrupted result, revoked device and route move during send.
- [x] Validate server-side private-LAN destinations; no arbitrary internet print from configured route.
- [x] New backend tests: isolation, replay, races, negative auth, CAS, health and failover safety.

Checks abaixo comprovam implementação e simulação/CI; não certificam USB/share, papel, reboot físico ou release stable. Fontes e runs: [registro de evidências](completion-20261020.md). Atualização automática, assinatura e piloto continuam abertos.

## Windows agent
- [x] Standalone typed contracts and interfaces at apps/printer-agent, with contract parity test; no Django model dependencies (S1; no runtime service yet).
- [x] Windows Service + optional local wizard/status window, no logged-in desktop session requirement (S2; Windows CI session 0).
- [x] Installer setup/remove/repair + machine-scope DPAPI secrets/ACL; revoke preserves protected state/history. Re-pair/reset is not offered by the installer.
- [x] Windows Print Spooler printer/queue enumeration in service context.
- [x] WinSpool GDI/raster WindowsDriver (non-RAW), print preview/test page and status normalization.
- [x] Windows RAW spool adapter gated on verified ESC/POS profile; block raw commands to incompatible queue.
- [x] LAN TCP adapter with private address validation, optional scoped discovery + manual IP.
- [x] PrinterProfile registry (generic ESC/POS, WindowsDriver and conditional Bematech).
- [x] Test ASCII/UTF-8/codepage behavior and Portuguese diacritics; explicit cut profile opt-in; QR/status commands remain disabled.
- [x] Agent telemetry and latest bounded redacted local diagnostic snapshot (not historical log capture), spool accepted != printed.
- [x] Host restart/agent crash/resume safe attempt recovery; never blind-resend uncertain ticket.
- [ ] Simulate USB, shared Windows queue, network printer and duplicate network visibility in two agents.
- [ ] Background update with signature validation, idle/roll-back semantics and version compatibility.

## Web/landing/release
- [x] Expand /manage/printing with Add computer, pairing approval, agent list/revoke, discovered printers and routes.
- [x] Configure BAR, KITCHEN and receipt destination from logical endpoint; no raw credentials to browser.
- [x] Add test print flow, normalized errors and visible uncertain result + reprint authorization.
- [x] Add /downloads page to apps/landing and shared canonical manifest/URL in Manage; stable unavailable, version/hash null until approved release, help implemented.
- [x] Windows GitHub Actions pipeline, lock dependencies, test install/uninstall, build immutable artifacts.
- [ ] Authenticode release signing and updater manifest; public stable download only after signing/hardware gate.
- [x] Ops runbook onboarding, printer model compatibility matrix, support/recovery and rollback.

## Pilot acceptance
- [ ] Inventory Aderlan PC OS, printer models, connection/ports and installed drivers (real hardware).
- [ ] Print physical Bematech test page under actual service account on Windows.
- [ ] Run kitchen/bar correct station routing, original vs REIMPRESSÃO, receipt and PDF fallback.
- [ ] Simulate second Windows agent and network printer accessible by both; prove only one send.
- [ ] Test queue offline, USB unplugged, spool restart, LAN down, VPN/rebinding, revoked token, expired lease.
- [ ] Observe and record the outcome *on physical paper*; no CI-only go-live claim.
- [ ] Decide venue trigger mode OPTIONAL_MIRROR separately, after Spec 015 health/fallback gates.
- [ ] Record release SHA, installer checksum, profile/driver/OS and approved go/no-go sign-off.
