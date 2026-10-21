# Acceptance — Spec 028

**Progresso atual (20/10/2026):** S1/S2 integradas; S3–S6 integradas pelos PRs #274, #275, #276 e #278; QA downloads integrado por #282. Protocolo, verificador e preparação automatizada de S7 incluídos nesta entrega (#280). Distribuição stable e homologação física permanecem NO-GO. Ver [evidências e pendências](completion-20261020.md).
**Status:** S3–S6 software integrated; S7 preparation delivered; signed stable release and physical pilot not accepted.

## Matriz de cobertura por slice

| Slice | Cenários desta especificação | Evidência requerida para fechar o PR |
| --- | --- | --- |
| S1 Foundation | 3 (credencial/revogação de contrato), 12, 15 | API schema/migration, segurança cross-Venue, regressão legacy |
| S2 Pairing | 2, 3, 13 (service startup) | integração Access/Manage + Windows service, replay/expiry/ACL |
| S3 Printing MVP | 4, 5 (single-agent), 8 (driver básico), 9, 10, 11, 15 | mocks spool/TCP e fluxo E2E sem afirmar papel físico |
| S4 Multiagent | 5, 6, 7, 10, 12 | duas instâncias concorrentes, fencing, USB offline, isolamento |
| S5 Compatibility | 4, 8, 11, 14 (pré-homologação) | golden bytes/layout, Windows GDI vs RAW, capabilities; prova física só S7 |
| S6 Distribution | 1, 13, 15 | Windows installer/upgrade/signed artifact e 2 entry points idênticos |
| S7 Pilot | 1–15 | aceite operacional com impressora real, logs redigidos, teste de turno e go/no-go |

**Interpretação:** os cenários parcialmente atribuídos a um slice têm uma parte definida no plan.md; a aprovação integral e física do caso 14 ocorre exclusivamente na S7. Um slice não pode alegar o cenário completo antes de todas as suas dependências e evidências estarem presentes. Os sete PRs são previstos, não estão abertos por esta atualização documental.

## 1 — Universal download and install
**Given** a Windows 11 x64 PC without Python and with administrative permission for installation,
**When** the operator downloads Rodada Impressoras from rodada.bar/downloads or Manage > Impressoras > Adicionar computador,
**Then** both locations resolve to the same signed stable build/checksum and the installer provisions an autostart Windows service, uninstall/repair and diagnostic UI without a permanently open browser.

**Negative:** a tampered or unsigned public update is rejected, and no release called stable is published without signing.

## 2 — Pairing by manager, not slug
**Given** an unpaired installation,
**When** it starts,
**Then** it displays a random one-time pairing code with 10-minute expiry, not a forced Venue slug or login prompt.

**Given** a manager with print.manage on Venue A,
**When** they approve that code through an authenticated Manage session,
**Then** only Venue A can own the agent and a restricted device credential is delivered to the requesting installation, not to another device possessing only the display code.

**Negative:** expired/reused/brute-forced code, unprivileged staff and cross-Venue approval are rejected. No staff password/PIN/refresh token is persisted in the agent.

## 3 — Immediate revocation
**Given** a linked, online agent,
**When** authorized management revokes it,
**Then** subsequent heartbeat/discovery/claim/result writes fail securely and all other authorized agents remain unaffected. Existing history remains; in-flight submission with uncertain physical outcome remains uncertain.

## 4 — Windows printer discovery
**Given** a Windows machine with USB and Windows-installed network/shared queues,
**When** the service enumerates devices,
**Then** it reports only printers accessible to the service security context, with connection mechanism and uncertain capabilities declared truthfully.

**Negative:** a printer installed only for another interactive user does not falsely show READY. Unauthorized shared queue returns understandable diagnostics.

## 5 — One agent and many printers
**Given** one Windows agent can reach BAR, KITCHEN and cashier printers,
**When** three endpoints are configured,
**Then** three independent routes may use that agent and jobs are directed to the correct assigned physical queue or local network address.

## 6 — Many agents and duplicate network visibility
**Given** Agent A and Agent B see the same LAN printer linked to one logical endpoint,
**When** both poll concurrently,
**Then** at most one receives an executable attempt token for a given PrintJob and a backend-enforced owner prevents simultaneous duplicate submissions.

**Negative:** two differently named discoveries are not silently merged and operator assignment is required.

## 7 — USB machine failure and fallback
**Given** Kitchen USB printer is physically attached to Agent A,
**When** PC A turns off,
**Then** other agents do not claim to access the USB unless an independently valid shared queue exists, KDS keeps working and UI reports route/agent offline. Jobs remain persisted centrally.

## 8 — Driver compatibility / verified profile
**Given** a printer with known compatible ESC/POS RAW mode,
**When** a test runs,
**Then** an 80mm non-fiscal ticket formats quantitites, Portuguese text, modifications and notes according to certified profile; cut is issued only if supported and enabled.

**Given** a device with installed Windows GDI driver but no RAW capability,
**When** user selects WindowsDriver,
**Then** it prints via Windows rendering/spooler without sending ESC/POS control bytes as RAW.

**Negative:** unsupported status/QR/cut commands are disabled. ASCII transliteration remains an explicit fallback rather than silent false support for accents.

## 9 — Correct source and station binding
**Given** a confirmed mixed BAR/KITCHEN order and the venue's explicit print mode allows printing,
**When** the Spec 015 document/job pipeline dispatches,
**Then** each station gets only its immutable, routed items, no print occurs for unconfirmed orders, and print failure never changes ledger, OrderItem or KDS task.

**Negative:** installing an agent does not silently enable AUTO_FALLBACK or OPTIONAL_MIRROR.

## 10 — Uncertain delivery / no duplicate food
**Given** submission completes partially or worker dies after entering a potentially side-effectful spool/network call,
**When** the lease expires or result API is unavailable,
**Then** the job is DELIVERY_UNCERTAIN, never blindly re-sent by another agent, and the operator sees a reprint action requiring explicit authorization and a marked copy.

**Given** failure is provably before sending any bytes,
**When** retry occurs,
**Then** existing job identity and fencing are preserved.

## 11 — Agent & printer status semantics
**Given** a live agent but no accessible printer status,
**When** Manage displays diagnostics,
**Then** agent = ONLINE, printer = UNKNOWN or DEGRADED as observed, and SPOOL_ACCEPTED does not render as printed paper.

## 12 — Multi-tenant isolation / network safety
**Given** a device registered to Venue A,
**When** it attempts to claim Venue B endpoints or a route with an arbitrary public internet host,
**Then** backend denies claim and agent denies unsafe network destination, without printing or disclosing customer receipt data.

## 13 — Service lifecycle and update
**Given** the agent has no logged-in user,
**When** Windows restarts,
**Then** it starts, reads protected configuration and resumes *server-safe* polling, without replaying an uncertain physical submission.

**Given** an update during an in-flight job,
**When** release update is installed,
**Then** service quiesces and honors leases; failed update rolls back without exposing secret or silently duplicating ticket.

## 14 — Aderlan hardware pilot
**Given** real Bematech MP-4200 TH, driver and connection topology documented,
**When** testing on a Windows host,
**Then** at least one fully evidenced physical ticket is produced, with operator validation for accents, widths, columns, cutting and recovery; only actually tested driver/transport combinations are marked VERIFIED. Software mocks cannot satisfy this gate.

## 15 — Legacy compatibility
**Given** existing BROWSER, FILE, NETWORK and CUPS/SPOOL endpoints from Spec 015,
**When** Spec 028 models and APIs are deployed behind a flag,
**Then** their existing printing workflows remain functional, with identical document/attempt semantics and no automatic migration of a legacy bridge credential.

## S1 technical evidence — 2026-10-14

Implementation/review: [PR #149](https://github.com/procopio420/rodada/pull/149),
[s1-foundation.md](s1-foundation.md). Final code tree: 5da5799.

- Scenario 3, S1 scope: valid/invalid/expired/revoked machine credentials,
  atomic rotation/revocation, one live credential, preserved route/audit history.
- Scenario 12, S1 scope: cross-Venue DB references and identity reparenting denied,
  signed foreign Host denied, staff/machine separation, unsafe literal TCP targets denied.
  Executable route claims/shared queue checks remain S3/S4.
- Scenario 15: legacy printing/bridge semantics retained; focused printing gate
  79 PASS PostgreSQL, including 32 S1 tests. Full prior candidate regression 755 PASS.
- Forward/reverse/reapply schema tested with a legacy FILE endpoint retained.
- Independent R3 review completed; Host P1 fixed and re-reviewed; import/export
  registration fix re-reviewed with Django model/FK registry checks.
- Mypy strict standalone contracts, Ruff, Django check and migration drift PASS.

CI is tracked on the PR and must pass before recommending merge. No Windows
service, pairing, claims, physical print, installation or production acceptance
is inferred from these results.


## Regressão visual Web (2026-10-18)
A tela de impressoras mantém simulação explícita de agentes desabilitados e inventário vazio no teste legado. Seletores RAW/habilitar rota usam os alvos mínimos de 44px do design system em 360/390/1280px. Não alterar pareamento, rotas, POSTs, confirmação física ou semântica de papel impresso.
