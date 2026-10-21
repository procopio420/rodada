# Spec 028 — evidências da missão de 20/10/2026

Baseline consultada no GitHub: main@4652b3013e69fa8e4f08a5a3a4e1f8c3a2720cfe.
Este registro distingue implementação, CI e homologação física. Nenhum deploy,
release pública, ativação real ou teste físico foi executado.

## Entregas e validação

| Slice | Existente / lacuna corrigida | PR / integração | Evidência |
| --- | --- | --- | --- |
| S3 | Serviço, descoberta, journal DPAPI e protocolo existentes; abort RAW/GDI incompleto e disco cheio corrigidos | [#274](https://github.com/procopio420/rodada/pull/274) / 512336fe2fb2a124da2bc36157a65b8581e01452 | Windows39526683643 PASS:30 testes, types, serviço sessão0/DPAPI/ACL |
| S4 | Reuso de PrintJob/token/lease; múltiplas rotas, ausência OFFLINE, disputa e failover pré-envio | [#275](https://github.com/procopio420/rodada/pull/275) / 8aeac95ba450b95e84cdfddde32abe60f4e8cc2c | API39526901194 PASS:1042 PostgreSQL17; Web39526901193 PASS |
| S5 | Registry ASCII/PC860/GDI, 58/80, corte opt-in e envelope seguro; confirmação por perfil no Manage | [#276](https://github.com/procopio420/rodada/pull/276) / f7f7312d04cdfefbfed2c49ddb6107849f7f1e04 | API39528843074 PASS:1044; Web39528843061 e Windows39528843063 PASS |
| S6 | Setup universal, repair/reinstall/uninstall, teste não financeiro e downloads indisponível até stable | [#278](https://github.com/procopio420/rodada/pull/278) / c6ac5b718b948dc2f971786d8c1d7d07b8764aee | HEAD042bd373: API39532661504 PASS:1046; Web39532661632, Windows39532661356, Landing39532661482/Visual39532661291 PASS |
| S7 | Roteiro físico, template NOT_RUN, verificador de completude/hashes; regressões CAS/reaparecimento e gate visual | [#280](https://github.com/procopio420/rodada/pull/280), preparação entregue neste PR | Código45e5bdab: API39532720103 PASS:1048 PG17; Web39532720034 PASS:17 visuais+159 BFF; Windows39532719881 PASS:35 |
| QA downloads | Chromium360/390/430/1280, teclado,44px, manifesto false e nenhum EXE oferecido | [#282](https://github.com/procopio420/rodada/pull/282) / 59ab4099a3b0cea944c61182e52270c4c066c22f | Landing Visual39532751847 PASS; anterior39529615922/artifact12314537727; telas360/390/1280 inspecionadas |

Runs estão em `https://github.com/procopio420/rodada/actions/runs/{id}`.
Logs/screenshots têm retenção limitada; as suítes são versionadas e reproduzíveis.
A integração final de S7 preserva o código validado, acrescenta esta KB e incorpora
o QA já integrado. SHA de squash e checks finais são rastreáveis no PR #280.

Artifact visual integrado12316522732, SHA256 do ZIP
`cb2201271e0c0db33bc191346c5cbf36133006ea6430c4f1a48309d9d1f58c87`.
Screenshots finais360/390 inspecionados;1280 inspecionado no candidato anterior
do mesmo componente. Nenhuma evidência representa papel real.

## Correções e revisão

- AbortPrinter/AbortDoc é limpeza best-effort; resultado permanece UNCERTAIN.
- Falha de persistência do journal impede entrada no spool.
- Fila ausente fica OFFLINE imediatamente; reaparecimento restaura observação.
- Uninstall aborta quando o serviço não consegue parar.
- Test print mantém UUID após POST201/GET503 e independentemente por destino A→B→A.
- IDs explícitos substituem seletores ambíguos; assertions de perfil/attestation,
  saves bloqueados e idempotência foram mantidas.
- Gate visual captura git diff separadamente: falha de diff falha o job.

Revisão independente R3 real (/root/review_s3) de código e deltas; achados foram
corrigidos e revistos. Resultado final: NO_FINDINGS_WITH_GAPS. Integrações
preservaram alterações concorrentes de attendance (#279/#283) e todas as
assertions. Conflitos de histórico de squash eram somente assertions/documentação.
Não houve aprovação GitHub simulada ou certificação. CI verde é gate de merge.

Descoberta retém identidade/histórico limitado a500 filas por instalação, sem TTL
de exclusão de rotas auditadas. Diagnóstico local é o último estado limitado e
redigido, sem histórico ilimitado ou conteúdo de documentos/credenciais.
O instalador não oferece reset local de identidade após revogação.

## Limites da garantia e compatibilidade

Lease/fencing/journal protegem a tentativa executável por intenção e impedem
reenvio automático após possível submissão. Não há garantia física exactly-once
se driver/spooler não confirma papel. DELIVERY_UNCERTAIN exige inspeção e cópia
explicitamente autorizada e marcada. Abort ou spool ID não comprovam ausência/
presença de papel.

| Perfil | Evidência software | Hardware atual |
| --- | --- | --- |
| WindowsDriver Unicode | GDI separado de RAW, wrapping58/80, erro/abort e serviço Windows | NOT_RUN: fila USB/share e driver reais |
| ESC/POS ASCII | Golden bytes, transliteração explícita e controles limitados | NOT_RUN |
| PC860 | Acentos, envelope ESC t3,58/80, caracteres sem representação viram ? | NOT_RUN: confirmar tabela no modelo/conexão |
| PC860 corte completo | Comando exato, perfil separado opt-in | NOT_RUN: cutter não certificado |
| Bematech MP-4200 TH | Candidata WindowsDriver/perfil genérico, sem presumir protocolo proprietário | NOT_RUN: inventariar firmware/driver/interface |

QR/gaveta/buzzer/status não são habilitados. UNKNOWN é diagnóstico válido.
Perfis novos requerem agente0.5.0;0.3.0 não recebe esses claims.

## Gates externos / NO-GO

Rastreamento: [issue #285](https://github.com/procopio420/rodada/issues/285).

1. Operador Windows/bar: executar [S7](s7-pilot.md) com MP-4200 TH real, fotos de
   papel, acentos/largura/corte, pedido→fila→agente, duas máquinas e recuperação.
2. Publicador: certificado Authenticode/cadeia/timestamp; assinatura Valid no EXE/
   setup exatos, SHA256 e antivírus/SmartScreen no Windows alvo.
3. Reboot físico, USB/rede/spooler real; atualização/rollback entre versões distintas.
   Reinstalação e start/restart em VM não satisfazem esses casos.
4. Proprietário: autorização específica para publicar/deployar e ativar Venue.

Atualização manual controlada existe. Updater automático permanece desabilitado;
aceite depende de canal assinado, política de elevação/rollback e validação. A
tarefa continua aberta. Ambos os downloads referem a mesma distribuição canônica;
latest503 e availability=false até release aprovada. Não publicar UNSIGNED PILOT
como produção.

## Reprodução e handoff

- API: workflow API usa PostgreSQL17, check/drift e pytest, incluindo isolamento,
  pareamento/revogação, concorrência, idempotência e recuperação.
- Windows: workflow Printer Agent executa Ruff/mypy, testes, sessão0/ACL/DPAPI,
  build PyInstaller/Inno, install/reinstall/uninstall, SHA256 e inventário.
- Web: typecheck/build/auth/tenant e BFF real PG; gate focado
  `npm run test:visual -- printing.spec.ts` para caminhos de impressão/workflow.
- Landing: `python -m unittest discover -s scripts -p test_landing_marketing.py`
  e `python scripts/landing_visual_qa.py` no preview do workflow.
- Local:35 testes do agente/verificador, mypy strict11 arquivos, Ruff,
  render/diagnóstico, check/drift,6 estáticos, brand e typecheck/build PASS.
  Chromium local teve download truncado; provas de browser são do CI.
- KB: check_agent_kb e seus5 testes locais PASS antes da perda temporária do
  executor; o gate Knowledge Base valida novamente a consolidação final.

O template de piloto permanece NOT_RUN. READY_FOR_SIGNOFF do verificador confirma
completude/hashes, não autentica testemunho e nunca autoriza produção.
