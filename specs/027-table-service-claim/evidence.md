# Spec 027 — Implementação e evidências locais

Data: 13/10/2026. Branch: `impl/027-table-service-claim`.
Estado: implementação em validação; **não pronta para merge/homologação**.

## Código entregue

- Migração aditiva: responsável/horário nullable, versão inicial 0 e `ServiceCommand`. Nenhum backfill especulativo.
- `service/start/`, `tabs/open/` e `responsibility/claim/`: sessão/capability/Venue, locks, fingerprint de destino/conteúdo, resultado persistido e replay. Registros não expiram automaticamente. Falhas revertem intenção e efeitos na mesma transação.
- Start cria ocupação e responsável sem criar comanda, covers, cliente, pedido ou dinheiro. Open cria comanda/vínculo juntos; claim usa versão e transferência explícita. Mesmo responsável retorna no-op registrado na intenção, sem novo evento de responsabilidade.
- Associação legada usa Table antes de Occupancy/Tab para conviver com liberação e abertura contextual. APIs legadas preservadas.
- Projeção staff em lote: responsável, comandas abertas com ID/estado/hora/referência e aviso agregado de pedidos GUEST pendentes. Consulta não cresce por mesa; considera intervalo do vínculo atual e readiness canônico. Sem alteração de Dispatch ou ledger.
- Auditoria usa autoria/sessão/device existentes; eventos `occupancy.*` alimentam a outbox transacional. SSE invalida leitura, não confirma mutation.
- Web: início sem modal, abertura com nome opcional, seleção direta da comanda, confirmação de takeover, aviso de QR em Agora/Mesas, intenção congelada em localStorage e recuperação após reload. Pendência de outra sessão bloqueia nova intenção; drafts bloqueiam troca de contexto. BFF não libera pagamentos/caixa/estornos.
- Android: mesmos contratos, seleção por ID, abertura contextual, claim/takeover, aviso agregado no Agora e intenção cifrada vinculada à sessão original. Retry usa a mesma chave/conteúdo. Sair/trocar de comanda preserva draft; comandos pendentes bloqueiam outra intenção de mesa.

## Resultados locais (histórico anterior ao CI)

| Verificação | Resultado | Limite |
| --- | --- | --- |
| Suite completa API em SQLite | 555 passed, 45 skipped, 9 failed | As 9 falhas são testes existentes de concorrência que exigem PostgreSQL ou tentam corrida em SQLite. Não equivale a suite verde. Execução anterior aos últimos ajustes de UI e ao teste adicional de QR/ajudante. |
| Regressão focada: mesas, Spec 027, guest, operações de Tab, realtime, concorrência 027 | 60 passed, 7 skipped | 4 gates novos de PostgreSQL e 3 regressões PostgreSQL existentes pulados. Inclui QR real, claim, limpeza e revogação. |
| Spec 027 final, após teste de ajudante | 8 passed | API/serviços reais em SQLite; não prova locking PostgreSQL. |
| Django system check / migration drift | PASS / sem alterações detectadas | SQLite local. |
| Ruff dos novos serviços/projeção/testes | PASS | Não declara lint integral do repo. |
| Web typecheck / production build | PASS / PASS | Sem aprovação visual. |
| Web `npm run test:table-service` | 1 passed | Servidor Next real: 3 rotas operacionais exigem auth (401), 3 rotas financeiras rejeitadas (403). Não testa sessão autenticada nem rendering. |
| `npm run test:visual` focado | Bloqueado na inicialização do browser | 7 casos nem chegaram à aplicação. Chromium instalado, mas `socket() failed: Operation not permitted` no processo singleton. Nenhuma captura/baseline aprovada. |
| Android `testDebugUnitTest assembleDebug lintDebug` | Bloqueado antes de compilar | Wrapper inicialmente sem rede; distribuição obtida separadamente. Gradle não resolveu `com.android.application:9.4.0`. SDK/emulador não disponíveis. |
| PostgreSQL | Não executado | Binários obtidos, porém ambiente não permite mudar UID/grupos para executar servidor sem root. Gates devem rodar no CI PostgreSQL existente. |

Arquivos de teste:

- `apps/api/tests/test_table_service.py`: start/replay/conflito, rollback de vínculo, comanda contextual, homônimos, claim/no-op/takeover, isolamento, generation/customer, projeção sem N+1, QR DIRECT real/replay/readiness/claim/revogação/nova geração e pedido de ajudante sem transferir responsabilidade.
- `apps/api/tests/test_table_service_concurrency.py`: start/start, mesma intenção concorrente, claim/claim e release/open, com conexões separadas e requisito PostgreSQL.
- `apps/web/tests/visual/table-service.spec.ts`: 360/390/430 px, start/open com resposta perdida/reload, payload congelado, seleção contextual e QR/claim agregado. Criados, **não executados com browser funcional**.
- `apps/web/tests/table-service-gateway.test.mjs`: isolamento HTTP da allowlist; integrado ao workflow Web depois do build.
- `apps/attendance-android/app/src/test/java/com/rodada/attendance/operations/TableServiceRecoveryTest.kt`: roundtrip da intenção congelada; **não executado**.
- `apps/attendance-android/app/src/androidTest/java/com/rodada/attendance/operations/TableServiceNavigationTest.kt`: um toque, nome opcional, homônimos e bloqueio de mutation pendente; fixture de callbacks, **não executada**. Não substitui kill/restart real.

## Contratos e revisão

Permissões: `table.manage` para start/claim; `tab.open` para abertura contextual. Ownership não confere capability financeira nem exclusividade de pedido. Customer precisa de Relationship do Venue. Dados de ownership não aparecem no contexto guest testado. Nenhuma mutation de cobrança foi adicionada ao companion.

Locks: intenção → Table → Occupancy → Tab. Replay consulta resultado antes de revalidar ciclo encerrado, mas passa pela autenticação/capability atual da API. A resposta persistida é histórica; clientes atualizam a projeção canônica após confirmar.

## Validação executada no CI

| Gate | Resultado | Referência |
| --- | --- | --- |
| PostgreSQL completo, incluindo as quatro corridas novas | **605 passed, sem skips** | Job 115459274212 / run 38444508565, código backend `e23a3dd` (inalterado nas correções posteriores) |
| Web visual/responsivo/acessibilidade completo | **236 passed** | Run 38446240857, `bca0b4b` |
| Spec 027 Web focado: retry/reload e QR/claim em 360/390/430 px | **4 passed** | Mesmo run, antes da suite completa |
| Web BFF/API em PostgreSQL | **16 passed** | Mesmo run |
| Android JVM, debug APK, AAB smoke e lint | **PASS** | Run 38445576387; também run 38446241010 |
| Android Spec 027 navegação por ID, abertura opcional e bloqueio de pendência | **2 testes instrumentados PASS** | Job 115462947280; fixture de callbacks, não transação backend |
| Android intenção cifrada de abertura contextual após force-stop/offline/reinício | **PASS** | Mesmo job: record de TableService verificado junto aos três estágios do teste de persistência |
| Android queda real de POST após commit e corte físico do uplink | **PASS** | Run 38445576415; também 38446240405. Prova pedido/charge existentes; não equivale a POST de start/open de mesa |
| Turno isolado com PostgreSQL e restart | **PASS** | Runs 38445576109 / 38446240247, roteiro existente; não cobre todos os refinamentos de mesa novos |
| Docker/Nginx, páginas Web e API direta | **PASS** | Run 38447188457, merge `3a5d98b` |

A primeira execução de alguns jobs falhou por quota ECR; os jobs afetados usam agora mirror público da imagem oficial. Instrumentação teve import inválido corrigido. Os quatro casos Web revelaram retry desabilitado pela própria intenção pendente e uma fixture de covers ausente; corrigidos antes dos resultados PASS acima. Nenhum baseline visual foi relaxado.

A main avançou durante a validação com API direta via Nginx. Integração resolveu colisões de `/manage`, `/cash`, `/refunds` e páginas guest com famílias API, preservando `/auth/login/` sem redirect de POST. O smoke test do container completo aprovou o merge. Os workflows ainda repetem checks automaticamente em novos heads; resultados acima identificam o código efetivamente testado.

## Refinamentos de 13/10 — em validação

- Mover comanda nos dois clientes reutiliza MOVE_LOCATION da Spec 009, com capability tab.move, versão da Tab, origem/destino explícitos e intenção durável. Gateway rejeita outros kinds e campos financeiros.
- Android usa Nova comanda na ação global; teste instrumentado adicional conserva medidas e verifica clipping. O fixture Pedir do protótipo permanece como referência histórica, com a extensão de texto testada separadamente.
- Rollout por Venue começa desativado, com comando gerencial auditado, CAS e replay. Rollback preserva replays anteriores e fluxos legados. Não houve ativação de estabelecimento real.
- Web persiste Tab, linhas/personalizações, chave e payload antes de confirmar. Reload recupera o mesmo pedido; sessões diferentes e storage indisponível bloqueiam envio.
- Ensaio API específico com duas Tabs (QR + staff), pedido de ajudante e movimento para outra mesa: PASS local, junto a 11 testes Spec 027. Ownership, IDs, guest e ledger preservados.
- Novo ensaio Android real start/open: proxy após commit → força encerramento → leitura offline da intenção cifrada → replay original → SQL exatamente uma ocupação/Tab, sem efeito financeiro. Implementado no CI; ainda não declarar PASS sem execução.
- Local: typecheck/build/gateway PASS; migrações sem drift. Playwright não executou: Chromium ausente e download retornou arquivo truncado. Navegador/Android/PostgreSQL serão conferidos no CI deste head.

Pendente externo: observação do piloto no Aderlan e medição before/after real, sem inventar tempos, erros ou baseline. Os novos ensaios automatizados não são evidência dessa observação.

## Publicação

Publicação autorizada pelo usuário em 13/10. Branch `impl/027-table-service-claim` publicada pelo conector GitHub (Git CLI sem credencial de escrita) e PR #107 aberto como draft: https://github.com/procopio420/rodada/pull/107. O bloqueio anterior foi resolvido pela autorização explícita.

Os resultados anteriores acima identificam seus heads; os novos refinamentos exigem nova execução dos gates.

Sem deploy, sem dados/contas reais, sem homologação declarada.

## CI dos refinamentos — head e39245d

- API PostgreSQL completo: PASS, run 38450361554.
- Web completo (incluindo 7 cenários Spec 027 e integração real): PASS, run 38450361733.
- Android JVM/APK/AAB: PASS, job 115479378772.
- Android POST start/open com perda de resposta após commit, force-stop/offline e replay/SQL: PASS, run 38450364117, job 115479387024. Corte de uplink de pedido também PASS.
- Turno isolado existente: PASS, run 38450361953. Docker/Nginx: PASS, run 38450361743.
- Android persistência e três cenários de mesas (incluindo mover): PASS no job 115479379501. Navegação falhou por clipping horizontal: alinhamento central em largura intrínseca introduzia limites fracionários para Pedir e Nova comanda. Correção mantém alinhamento original da referência Pedir e reserva largura disponível da linha/coluna para Nova comanda; repetir gate e testar 360/390/430 com fonte 1.5 antes de PASS.

## Integração da main — head 83e3d79

A main 8afd120 foi integrada preservando cardápio inline/categorias, status de envio de pedido, domínios e política de workflows sob demanda. A migração de rollout foi movida para 0009, após 0008_venue_domain. Local: 26 testes de mesas/rollout/domínios PASS, build/typecheck e drift PASS.

Android integrado: PASS, run 38478836744, jobs 115576142388 e 115576142687. O runner aprovou persistência em três processos, três testes de mesas, três testes de navegação e Nova comanda em 360/390/430 px com fonte 1.5. A correção de largura resolveu o clipping sem relaxar a asserção. Docker integrado: PASS, run 38478836754. A exceção temporária para executar o gate neste PR foi removida após PASS; recuperação pesada segue sob demanda, conforme política da main.

Fechamento da integração 83e3d79: API PostgreSQL **623 passed** (run 38478836755 / job 115576142310); Web **7 focados + 239 visuais + 16 integrações reais PASS** (run 38478836740 / job 115576141892). Todos os gates integrados aprovaram. O commit de fechamento altera somente documentação e agendamento de workflow, sem mudança de código de produto ou testes.

## Integração da Spec 025 / KB — main 60a9555

Depois do gate 83e3d79, a main recebeu o gateway/ingress multitenant da Spec 025. Integração preserva contexto assinado, cookies host-only e headers sanitizados; regex explícita mantém páginas Web e acrescenta família venue. Fixture de dois Venues conserva rollout ligado apenas no Venue de teste. Migração de rollout passa a 0011, após lifecycle de VenueDomain 0010. Revalidar API/Web/Docker neste novo head; não confundir PASS anterior com este merge.
