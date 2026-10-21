# S1/S2 — integração canônica com a Spec 033

Execução autorizada em 20/10/2026, base `0af41928`. Contrato de implementação;
não autoriza deploy/rollout de produção. Policy 1:1 em house_account, backfill e
bootstrap ENFORCE, fallback sem linha ENFORCE/version null com log de integridade.
GET nunca escreve. Novos Venues também ENFORCE até configuração explícita.

Rota canônica GET/PUT `/house-account/enforcement/`: GET staff autenticado;
PUT MANAGER/OWNER + venue.configure + PIN recente no serviço. CAS e receipt
idempotente persistido, audit antes/depois; replay retorna a resposta original
mesmo após alterações posteriores. No-op não incrementa versão. Não reescrever
Tabs, snapshots ou ledger. Rollback funcional é PUT auditado para ENFORCE.

Confirm atual já trava Venue(NO KEY UPDATE)→Tab→Products: manter ordem e travar
policy após produtos, antes da decisão. Pricing/transferências: Tabs→policy.
PUT trava somente policy, não lê/trava Tabs. Payment/refund não precisam travar
policy porque não autorizam consumo novo. Reusar financial_position/totals e
avaliador comum para Order, pricing positivo e transferências. Replay confirmado
antecede regras mutáveis. WARN_ONLY preserva motivos independentes de atenção.
Excesso registra modo, versão e exposição antes/depois, sem Payment fictício.

Gates: migração forward/backward, schema, PostgreSQL real, concorrência, replay,
isolamento/auth, canais Web/Compose, R3 e CI no SHA candidato. Nenhum AC aceito
pela existência de código; rollback de schema requer retirar clientes/escritas.
