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
