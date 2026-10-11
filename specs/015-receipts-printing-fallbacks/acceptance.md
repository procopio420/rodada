# Acceptance — Spec 015

## Customer check

**Given** an OPEN Tab with confirmed items, discounts, service charge and partial payment  
**When** staff generates a customer check  
**Then** it shows canonical current subtotal/adjustments/confirmed receipts/remaining balance with generation time and non-fiscal labeling.

## Stale check

**Given** a check was generated  
**When** Tab changes later  
**Then** historical check remains unchanged and a newly generated check reflects the new source version.

## Payment receipt

**Given** Payment is CONFIRMED  
**When** receipt is generated  
**Then** it contains safe amount/method/time/reference and no sensitive card data.

## Ambiguous payment

**Given** Payment is CONFIRMATION_PENDING  
**When** user requests definitive paid receipt  
**Then** system refuses or renders pending-status document, never “pago confirmado”.

## Production ticket source

**Given** an unconfirmed cart  
**When** production print is requested  
**Then** no canonical production ticket is generated.

**Given** confirmed KITCHEN OrderItems  
**When** fallback print is requested  
**Then** ticket is rendered from immutable confirmed snapshots including modifiers/notes.

## Retry idempotency

**Given** a production PrintJob times out  
**When** worker retries the same job  
**Then** it remains one logical production ticket/job and does not create a second OrderItem/task.

## Explicit reprint

**Given** an initial production ticket exists  
**When** authorized station staff reprints it  
**Then** a new linked job is created, output is prominently marked REIMPRESSÃO and actor/reason policy is audited.

## Auto-fallback dedupe

**Given** KDS is unhealthy and AUTO_FALLBACK enabled  
**When** repeated health checks observe the same confirmed Order  
**Then** only one initial logical fallback ticket is enqueued for that station/order generation.

## Printer offline

**Given** every printer is OFFLINE  
**When** staff confirms an Order through healthy API  
**Then** canonical Order/Fulfillment still succeeds and UI surfaces print fallback failure without rolling back the sale.

## WebSocket outage

**Given** realtime is down but API healthy  
**When** print is requested  
**Then** printing may proceed through canonical API/job flow.

## Digital receipt authorization

**Given** guest has valid opaque receipt token for their receipt  
**When** they open it  
**Then** only that receipt is returned; guessing another sequential id is not possible.

## Multiple stations

**Given** an Order has BAR and KITCHEN items  
**When** production fallback triggers  
**Then** each station receives only its routed item snapshots through its binding.

## Permission denial

**Given** staff is not authorized to reprint another station's production ticket  
**When** direct API request is made  
**Then** backend denies it and no PrintJob is created.

## Audit

**Given** production reprint and printer binding change occur  
**When** management timeline is inspected  
**Then** actor, time, target and reprint/config provenance are available.

## P0 implementation evidence — 2026-10-09

| Gate | Observed evidence |
| --- | --- |
| API regression suite | 291 passed, 16 environment-dependent skips; no financial/provider rule changes |
| Final printing/bridge/security PostgreSQL gate | 53 passed, including five PostgreSQL transaction/immutability cases |
| Output snapshots | 20 original/copy/width/kind combinations, each checked as text, HTML and ESC/POS |
| Existing Web visual regression | 144 passed; existing prototype primitives/baselines retained |
| New printing visual/accessibility | 6 passed at 360, 390 and 1280px |
| Real API/Web acceptance | Order → station ticket → explicit copy → partial receipt → share/revoke → final payment → closed receipt; passed |
| Portable PDF | Chromium-generated 80mm PDF, valid `%PDF` artifact; no physical printing |
| Build/types/schema | Production Web build, TypeScript check, Django check and migration drift check passed |
| Hardware | Not tested; checklist remains pending |

The final PostgreSQL gate also verifies immutable SQL history, cross-printer initial dedupe,
SKIP LOCKED claims, simultaneous acknowledgement fencing, safe retry/backoff, lease expiry,
late acknowledgement without a recovery poll, explicit copy audit, permission denial for
another station, historical failure filtering/pagination, partial-payment refusal while
confirmation is pending, guest scope/revocation, hashed/expired/revoked receipt links and
local bridge refresh/lost-ack behavior. Confirmed Order/payment/closure continue while the
print job fails. Transfers reuse the canonical responsibility projection and record original
quantities plus actual transferred quantity/amount rather than inferred fractional quantities.

Artifacts are reproducibly generated in `visual-artifacts/printing/` by
`apps/web/tests/integration/printing.spec.ts`; they are local review evidence, not committed
customer records or physical printer certification. Simulated operator confirmation in the
test verifies audit behavior only. Receipt preview iframes prohibit scripts; accessibility
checks inspect their parent controls and validate document content separately.

Automatic KDS heartbeat fallback and Android Bluetooth acceptance above remain rollout
criteria, not P0 claims. P0 does not expose an AUTO_FALLBACK configuration. Fiscal issuance
and vendor-mandated payment receipt metadata are separate external decisions.

## Fixtures em Windows

Comparação golden lê os arquivos existentes como UTF-8 explícito, preservando bytes e igualdade literal de texto/HTML/ESC-POS. Não substituir fixtures nem aplicar normalização que esconda diferenças. O encoding padrão da máquina não define o contrato do documento.

Verificação10/10: revogação de link compartilhado deve aguardar resposta canônica de sucesso antes de recarregar a página leitora; leitor exige erro expirado e ausência do documento. Sincronizar o teste com POST share contendo revoke_id, sem timeout maior ou redução do aceite.
