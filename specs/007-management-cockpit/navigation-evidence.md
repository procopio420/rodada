# Gerência — organização por tarefa

Data: 2026-10-18. Branch: `codex/management-navigation`; base examinada: `dbf3d5fa067009cd9a255035a092f8c39c4507ac`. Evidência local do delta de navegação, risco R2; sem publicação/merge.

## Diagnóstico e decisão

Inspeção da captura fornecida, página local real e fixtures do build anterior: o cabeçalho repetia a finalidade de Agora em todas as abas; Gestão misturava caixa/salão/configurações e repetia setup/preços presentes em Mais. Os acessos sem agrupamento podiam quebrar em várias linhas no telefone. Fricção P2 confirmada na organização; tempo humano de descoberta não medido.

| Tarefa | Destino principal | Mudança |
| --- | --- | --- |
| Ver exceções e pulso | Agora | Preserva alertas, riscos e atalhos contextuais |
| Atender, produzir e cuidar do salão | Operação | Mesas, limpeza/giro, comandas, Bar/Cozinha e entregas juntos |
| Conferir dinheiro e fechar | Financeiro | Caixa, fechamento, estornos, serviço/descontos/aprovações e relatórios juntos |
| Manter o cardápio | Cardápio | Produtos e variações/adicionais juntos |
| Configurar o estabelecimento | Gestão | Equipe/zonas, clientes, alertas, impressoras e acesso por grupos |

Alternativa considerada: manter Vendas/Gestão/Mais e apenas reordenar atalhos. Preservaria nomes antigos, mas manteria sobreposição e o destino genérico Mais. Cinco áreas por tarefa dão acesso direto a Cardápio e Financeiro; aliases vendas/mais preservam links antigos. A validação com operador real continua necessária.

## Implementação e invariantes

Metadados de título/descrição/ícone seguem a área selecionada. Links de acesso em painéis usam coluna e espaçamento existentes; cores, tipografia, SurfaceNav e alvos não mudam. Os retornos internos apontam à área de origem. Navegação por hash e retornos usam âncoras nativas: regressão reproduzida com Next Link concatenava o hash inicial ao retorno (`vendas#cardapio`); a jornada agora verifica URL e seleção corretas, incluindo voltar/avançar.

Sem alteração de API, leitura financeira, permissões, sessão, ledger, comandos de formulário ou regras de fechamento. Histórico segue ícone discreto e popup somente leitura, com revogação preservada. Mesas em limpeza mantém contador junto do salão. Páginas internas conservam formulários existentes.

## Validação

- Build Next e typecheck: PASS.
- Autenticação:4 testes Node PASS.
- Nova navegação:10 Playwright PASS; grupos/links nas cinco abas em360/390/430/1280px, legado vendas/mais, retorno de produto, voltar/avançar, fonte200%/teclado, loading/vazio/erro e avisos financeiros. Axe e alvos44px/overflow nos estados testados: PASS. Sem alegação de conformidade integral ou leitor de tela manual.
- Auditoria ESLint completa:23 diagnósticos legados;0 novos/fatais no delta (inclui teste novo). Web safety:0. Lint focado inicial de página/nav/teste: PASS; lint ampliado expõe4 diagnósticos legados em efeitos não alterados.
- KB:49 documentos/297 links/12 skills PASS; diff check PASS.
- Suite visual global executada com parada na primeira falha:1 FAIL em `attendance-catalog.spec.ts:15` pelo seletor antigo Contas;602 não executados. Bloqueio anterior fora deste delta; não é PASS global e nenhuma baseline/tolerância foi atualizada.
- Execução conjunta final:42 Playwright PASS em55.7s (navegação, histórico/extrato, alertas, paridade gerencial e retorno progressivo). Inclui geometria/raster do ícone Agora existente, sem atualização de baseline.

Capturas locais com a mesma fixture e larguras, antes/depois, em `visual-artifacts/management-navigation/`. Revisão de pixels incluiu Gestão antiga390 e Financeiro novo390; navegação real local confirmou agrupamento Financeiro e estado Ao vivo, sem mutations. Capturas usam fixture determinística; não são evidência de operação em produção. Tempos humanos e gestos de scroll não medidos.

## Limites e próximo gate

Alteração local implementada; testes globais bloqueados no Atendimento. Sem novo PR, push, merge, deploy ou escrita financeira. Próximo responsável: revisão do fluxo pelo mantenedor/operador e gate visual global após manutenção do teste adjacente. Preservadas alterações preexistentes fora do escopo.
