# Runbook — usuário, papel, sessão e aparelho

**Risco:** alto em OWNER, `staff.manage` ou bloqueio de sessão. [Índice OPS](README.md), [API de acesso](../../apps/api/README.md) e [modelos](../../apps/api/modules/access/models.py).

## Gates

- Especificar Venue e pessoa autorizada, função exata, motivo/ticket, operador OWNER responsável e se é **novo `StaffMember`**, vínculo existente ou apenas alteração de papel. Não usar a conta de outro bar sem autorização dos dois.
- `login_identifier` é **globalmente único** em `StaffMember`; `VenueStaffMembership(venue, staff)` define `STAFF`, `CASHIER`, `MANAGER`, `OWNER`. Só OWNER tem `staff.manage` por padrão; privilégios extras requerem decisão explícita.
- Autorização recente obrigatória para PATCH de vínculo/device e POST de revogação; nunca contornar essa checagem fazendo mutation casual no banco. Novos usuários **não possuem endpoint `POST /manage/access/memberships/`** no código atual.
- Não solicitar PIN em chat, mandar por mensagem, logar `Authorization` nem persistir em script/CLI args. Entregar PIN por canal protegido ao titular.

## Procedimento

### Listar e gerir contas **já existentes** (API oficial)

Use sessão do próprio OWNER no Venue correto; se necessário, autentique/reautentique no app (`POST /auth/reauthenticate/` recebe PIN sem exposição a logs). As rotas são relativas ao backend autenticado:

| Operação | Rota | Gate |
| --- | --- | --- |
| Ver vínculos | `GET /manage/access/memberships/` | `staff.manage` |
| Trocar role/status | `PATCH /manage/access/memberships/{membership_id}/` | `staff.manage` + reauth recente + `expected_version` |
| Dispositivos | `GET /manage/access/devices/` | `staff.manage` |
| Confiar/revogar dispositivo | `PATCH /manage/access/devices/{device_id}/` | reauth recente |
| Listar/revogar sessão | `GET /manage/access/sessions/`; `POST /manage/access/sessions/{session_id}/revoke/` | reauth para revogação |
| Auditoria | `GET /manage/access/audit/` | `staff.manage` |

Exemplo de payload de **alteração de usuário existente** (não usar UUID de outro Venue):
```json
{"expected_version": 3, "role": "CASHIER", "reason": "Mudança aprovada #TICKET"}
```
Um `409 VERSION_CONFLICT` exige novo GET/revisão; não repetir PATCH cegamente. Não rebaixar/remover o último OWNER, nem mudar o próprio role/remover o próprio acesso (guards da API).

### Criar funcionário novo — bootstrap **supervisionado**, não endpoint

**Limitação verificada:** API atual não cria `StaffMember`/`VenueStaffMembership` por POST. Faça **somente** com acesso Django administrativo protegido, dono do Venue autorizado e aprovação específica. Railway MCP não oferece `manage.py shell`. Usar padrão existente de [provisionamento protegido](../../deploy/railway/pilot-provisioning.md), adaptado ao staff de **um Venue já existente**, com esses passos: (1) selecionar Venue/owner autorizado; (2) validar `login_identifier` globalmente livre, comparar sem case, escolher role **mínimo** (STAFF por padrão), confirmar identidade; (3) coletar PIN interativamente com `getpass`/verificador (nunca argumento/arquivo/env log), armazenar somente por `StaffMember.set_pin(pin)`; (4) numa única `transaction.atomic`, criar staff e membership e `AuditEvent` com `actor_staff=OWNER`, `venue`, ticket e role; (5) testar login na Venue certa, 403 para Venue alheio e capacidade esperada; (6) destruir PIN do processo. Não usar `seed_demo` para cadastrar usuário real.

OWNER adicional requer segunda aprovação e conferência de auditoria; *não atribuir OWNER só para facilitar a revisão Play ou depuração* em ambientes reais.

### Desligamento/comprometimento

Para revogar imediatamente, OWNER reautenticado muda status para `SUSPENDED` ou `REVOKED` via PATCH com versão atual e motivo auditável; serviço revoga sessões e emite invalidação. Para dispositivo perdido, `trust_state=REVOKED`, que não pode voltar a TRUSTED; nova instalação precisará de registro. Pode revogar sessões individualmente pelo endpoint. Confirmar em outra sessão que login/refresh/comandos já não têm acesso.

## Evidências

Somente IDs técnicos, Venue, papel anterior/novo, `version`, status, motivo, evento auditado e teste de capacidade negativo, sem PIN/access/refresh tokens. Para criação inicial manual, incluir quem executou, sessão administrativa protegida e mudança aprovada.

## Rollback / contenção

- Papel indevido: reautenticar como OWNER correto, revisar versão e restaurar papel mínimo via endpoint; documentar antes/depois.
- Conta/dispositivo suspeito: **revogar primeiro**, investigar depois; nunca reabilitar `REVOKED` device, não apagar audit ou StaffMember para "limpar" histórico.
- Se fluxo de criação manual frequentemente necessário, abrir spec de onboarding/admin API com autorização, idempotência, criação auditada e testes cross-Venue. Não simular endpoint ausente.
