# Spec 034 — entrega consolidada para revisão

## Escopo

Padroniza a Gerência por tarefa: Agora, Operação, Financeiro, Cardápio e Gestão. Reutiliza tokens e componentes existentes, organiza Clientes, Impressão, Configuração, Alertas, Fechamento, Preços, Estornos e Relatórios. Melhora hierarquia, formulários, estados de leitura e retorno contextual com foco.

A manutenção encontrada durante os gates inclui leitores assíncronos com cleanup, seleção canônica por ID, reinício de busca por eventos, reconciliação da quantidade de remoção e do recibo, e relógio de estação. Os contratos de dinheiro, permissões, intenção e replay foram preservados. O executor E2E ganhou bloqueio conservador entre processos no Windows, mantendo a allowlist do banco descartável.

## Evidência anterior à reconciliação

Base `860b25d93da486d2416c6ddaccfdccd9605f8953` com o working tree consolidado no commit `8fc61618`:

- **296 testes compostos da Gerência passaram**, em 7,3 minutos: [relatório](composed-final-evidence.md).
- **59 testes do cliente passaram**, em 57,4 segundos: [relatório](guest-bootstrap-evidence.md).
- **13 integrações reais Web/API/PostgreSQL passaram**, em 1,8 minuto, num cluster descartável separado: [relatório](integration-focused-evidence.md).
- Seis testes do guard Windows e Ruff passaram. Build webpack, tipos, autenticação (4) e tenant (10) passaram nas rodadas documentadas.
- Lint global: 325 arquivos, zero erros e zero avisos na rodada de bootstrap do cliente.

Os relatórios incrementais preservam falhas e interrupções históricas. Os números acima não são uma execução única nem CI do commit posterior.

## Reconciliação com a main

Referência examinada: `origin/main@59ab4099`. As etapas iniciais da Spec 034 (#268, #269 e #270) já estavam integradas por squash. O merge desta referência ocorre somente na branch de trabalho.

Os conflitos de intenção foram resolvidos mantendo as extensões de navegação e evidência da Spec 034 e as funções novas de impressão da main: teste de destino AGENT, chave por tentativa, mensagem identificada e leitura canônica com resultado booleano. A manutenção da chave após readback falho foi preservada. Ações do destino ficam abaixo do título no celular para evitar compressão do nome.

A primeira rodada pós-reconciliação passou 72 testes. Uma regressão geométrica adicional reproduziu a compressão do título em 360 px; o ajuste responsivo tem validação própria registrada no fechamento do PR. Build e lint global também passaram antes desse ajuste final de CSS.

## Pendências

Conferência manual do operador ainda sem aprovação explícita. Impressora física não homologada. Integração executada é o recorte de 13 casos, não a suíte completa. Revisões independentes locais por slice não substituem a revisão autenticada R3. CI remota e revisão do commit final devem ser acompanhadas no PR.

**PR em rascunho; sem autorização de merge ou deploy.** Não declarar homologação ou release apenas pelos gates locais.

## Fechamento local após reconciliação

- 72 regressões passaram em 2 minutos antes do ajuste final de CSS.
- A nova regressão geométrica falhou antes da correção (título com largura zero em 360 px). Após corrigir o cabeçalho, 21 testes de impressão passaram em 37,3 segundos, incluindo asserção mobile, ampliação 200%, perfis e preservação da chave de teste após POST confirmado com readback falho.
- Build webpack e tipos passaram na versão reconciliada e após o ajuste de CSS. Lint global permaneceu em zero erros/avisos; lint do arquivo/teste final passou. Autenticação: 4 PASS; tenant: 10 PASS.
- Revisão independente local dos conflitos e do ajuste final: NO_FINDINGS_WITH_GAPS. O revisor não executou os testes; limites de hardware e review autenticado permanecem.
- Não foram repetidas as suítes de 296/59/13 casos na main reconciliada; seus relatórios continuam explicitamente vinculados à base anterior. A CI do PR deve validar o commit publicado.
