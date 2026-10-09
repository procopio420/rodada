# Integração da branch de trabalho — 09/10/2026

Pedido: incorporar a main atual à branch de trabalho, preservando os dois históricos e validando a base antes de continuar desenvolvimento.

## Bases e escopo

- Branch: `codex/ux-operational-polish`, inicialmente em `9557ae8`.
- Main incorporada: `1dfdf8a62bd98a4d48cc87b2079b3b2842b7a02a`.
- Merge normal, sem rebase, force-push, merge na main ou deployment.
- Contratos preservados: Specs 020, 021-operational-ux-polish, 022-material-visual-fidelity e 006; planos recebidos em 021-prototype-design-integration, 022-full-product-implementation e 023 permanecem identificados por seus caminhos completos.

## Resolução revisada

Os seis conflitos eram de apresentação: AttendanceScreen, RodadaTheme, globals.css, production-board, design system e CSS do protótipo.

O layout validado da branch permanece: cabeçalho de 72 px, colunas 420/restante/340 no desktop, agrupamento por Product ID, transições individuais e PICKED_UP separado de READY. A main acrescenta referências importadas, pagamento integrado/simulado e políticas existentes; esses fluxos foram preservados sem substituir repositories ou ledger.

O passe usa ready_at e mostra explicitamente “Tempo não informado” quando ausente. Os novos testes da main usam a identidade do Product e os seletores da composição integrada. Fixtures continuam restritas aos testes; a soma é verificada exatamente. Nenhum limiar visual foi aumentado e nenhum screenshot atual virou baseline novo.

Fonts locais WOFF2 e faces Android já validadas são mantidas; assets TTF importados pela main continuam disponíveis para os exports. Tokens e variante buttonWork da main são compartilhados com o Web. Licenças originais são preservadas, inclusive espaços finais existentes. As cópias byte a byte idênticas de Archivo-OFL.txt/archivo-OFL.txt foram consolidadas no caminho existente archivo-OFL.txt: dois nomes diferentes somente por maiúsculas causavam estado local alterado no Windows.

## Validação local

- Web typecheck e build: passaram.
- Visual/acessibilidade: matriz completa de 135 casos executada; 134 passaram inicialmente. O único erro era a expectativa antiga do rótulo do passe. Após alinhar a expectativa ao contrato da main, os três casos relacionados passaram, incluindo geometria e identidade, soma/transição individual e comparação da referência atualizada.
- Os sete gates legados de primitives e o botão da nova referência passaram sem afrouxar limites; o botão atualizado mediu 0 pixels diferentes.
- Cozinha inspecionada em 390 e 1280 px, com nomes, ações e informações de tempo visíveis.
- Integração real Web/BFF/Django: cinco fluxos passaram em banco SQLite descartável. Houve um lock transitório de SQLite em uma leitura guest, seguido de recuperação; isso não é prova de concorrência PostgreSQL.
- Android: 28 testes JVM, assembleDebug e lintDebug passaram no build padrão, sem SDK privado.
- API: 203 casos aprovados e sete ignorados no ambiente SQLite. A execução completa aprovou 198; os cinco testes HTTP bloqueados pelo socket do sandbox passaram na reexecução específica fora dele.
- Django check passou e makemigrations --check --dry-run não encontrou alterações.

## Limites e próximo trabalho

Esta integração não afirma paridade integral, homologação física, pagamento live ou execução dos casos PostgreSQL. A Spec 023 conserva suas pendências. Para novas tarefas, partir desta branch sincronizada, conferir origin/main antes da primeira alteração e preservar mudanças locais antes de qualquer integração.

## Atualização seletiva das entregas recentes

Após autorização para atualizar a mesma branch com as entregas recentes necessárias, foram integradas:

- `feat/tab-operations` em `dc3c706dcd49a0b6e2d9af6116cecff44f015477`: correções de transferências, responsabilidade nos relatórios e rejeições Android; merge `9cd6d65`.
- `feat/operational-realtime` em `1c5f928e474f145dc39d7f0e320c1ec98f38a9c7`: Spec 014, outbox transacional, SSE autenticado, replay, fallback de leituras e cache seguro; merge `56cd02a`.
- `feat/product-modifiers-variants` em `4add70edbf61e7bd5efcfae665ef9995c5f67962`: Spec 010, configuração gerencial, seleção guest/Android, validação/preço canônico e snapshots imutáveis na produção.

Os heads das três entregas tinham API/Web/Android aprovados no GitHub. A nova combinação recebeu validação local própria. Um novo fetch antes da publicação confirmou os mesmos heads e a main em `1dfdf8a`.

Não foi feita integração indiscriminada das demais branches: documentação antiga já incorporada por squash, pesquisas fora do núcleo e ampliação de provider IA do Quick Catalog não são necessárias a esta base; IA continua adiada. Correções específicas de geração/regeneração nessa branch permanecem fora deste merge e podem ser avaliadas na ativação do provider.

### Compatibilidade entre as entregas

- Mantidos fontes/assets, layout da estação, identidade Product/Order, chips, transições individuais, tempo do passe e itens em entrega. Nenhum arquivo da base `feabbe7` foi excluído.
- CustomizationText acompanha o snapshot confirmado nos tickets, passe e entrega; POS/Guest preservam ProductIcon e sua apresentação existente, junto aos novos controles de revisão.
- Eventos de configuração e disponibilidade das variantes/adicionais invalidam o catálogo de todos os Products afetados, inclusive grupos compartilhados. O envelope público não copia metadata de auditoria. Teste cobre Products compartilhados e visibilidade staff/guest; o fluxo real verifica indisponibilidade no seletor guest sem atualização manual.
- O banco SQLite descartável dos testes usa transações IMMEDIATE e WAL: evita conflito de upgrade de lock entre comandos e o publicador. Isso não muda a configuração de produção nem substitui os testes PostgreSQL.

### Validação da combinação

- Web: typecheck/build aprovados; 141 testes visuais/acessibilidade aprovados, sem alterar baselines ou limites; captura de cozinha personalizada em 390 px inspecionada.
- Realtime client: oito testes aprovados, incluindo chunks, replay, fallback e revogação.
- Web/BFF/API ASGI: seis fluxos reais aprovados com banco descartável; a primeira execução revelou locks SQLite, corrigidos somente no harness de teste antes da execução completa aprovada.
- Android: 38 testes JVM, assembleDebug e lintDebug aprovados.

Para ativar realtime num ambiente implantado, seguir `docs/development/operational-realtime.md`: servidor ASGI, dispatcher supervisionado, retenção e proxy compatível com SSE. Esta atualização entrega código integrado; não executa deployment, configura provider IA ou homologa dispositivo físico. Casos de concorrência PostgreSQL não foram executados localmente nesta atualização.
