# Inventário de dados e permissões — Play Console (revisar antes de enviar)

**Escopo do binário padrão:** `apps/attendance-android`, `sumupSdk=false`. Avaliação preliminar do código em 2026-10-12, **não** corresponde a declaração final sobre todo o backend e serviços de terceiros.

## Permissões declaradas

| Permissão | Motivo | Observação |
| --- | --- | --- |
| INTERNET | API de autenticação/atendimento | HTTPS obrigatório em release |
| ACCESS_NETWORK_STATE | Estados de conectividade | Sem localização |
| NFC | Futura possibilidade de Tap to Pay | Hardware marcado opcional; integração real não habilitada por este trabalho |
| ACCESS_LOCAL_NETWORK | Apenas manifest **debug**, para API de desenvolvimento | Não deve constar em release |

Sem permissões de localização, câmera, microfone, contatos, SMS ou armazenamento de mídia neste manifest. Confirmar no **manifest mesclado do AAB** e após inclusão de SDKs.

## Dados a verificar no questionário Data Safety

| Categoria provável | Evidência | Ação |
| --- | --- | --- |
| Identificadores de usuário/conta e estabelecimento | Login `venue_slug`, identificador de operador e sessão | Confirmar finalidade, retenção, visibilidade a terceiros e exclusão |
| Identificadores de dispositivo | UUID persistido por instalação | Confirmar categorização como Device or other IDs |
| Dados financeiros/transacionais | Valores, status de pagamentos, comandas e caixa | Confirmar quais categorias Play de 'Financial info' e 'App activity' se aplicam |
| Dados de operação e atendimento | Pedidos, mesas, itens, histórico | Verificar presença de dados de clientes e categorias apropriadas |
| Logs e dados técnicos no servidor | Requests, erros e auditoria; variam por deploy | Inspecionar efetivamente IP, user agent, event logs, observabilidade |
| Terceiros/SDKs | Gradle inclui bibliotecas Jetpack; SumUp só com opt-in | Reavaliar tudo ao ligar Paytime/SumUp, analytics, crash reporting |

A troca de dados app→API **pode contar como coleta** no formulário mesmo que não seja compartilhada com terceiros. Não declarar "nenhum dado coletado" sem auditoria. A seção Data Safety é dispensada enquanto o aplicativo estiver **exclusivamente na faixa internal**, mas será necessária para closed/open/production.

## Controles verificados na aplicação

- `android:allowBackup=false`.
- Tokens e intenções financeiras pendentes são armazenados cifrados com Android Keystore (conforme README Android).
- O PIN não é armazenado pelo cliente, mas trafega para autenticar no backend.
- Identidade de dispositivo em forma de UUID aleatório e revogável.
- Release sem permissões debug de acesso à rede local e com URL HTTPS exigida.

## Pendências que exigem decisão humana / ambiente

1. Auditar backend **implantado** e acordos com fornecedores; identificar controlador/operador, suboperadores, jurisdição e prazos de retenção.
2. Confirmar se solicitações de exclusão de conta são feitas pelo estabelecimento/gerente; se a Play exigir opção de exclusão externa, disponibilizar URL e processo.
3. Publicar política de privacidade final em domínio público e adicioná-la no Play Console e no app quando necessário.
4. Validar criptografia em trânsito, acesso de reviewers e declaração de conteúdo comercial.
5. Revisar novamente ao ativar SDK de pagamentos, crash reporting ou serviços de analytics.

Documentação oficial: https://support.google.com/googleplay/android-developer/answer/10787469?hl=pt-BR
