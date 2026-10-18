# Cardápio gerencial — categorias e edição

Data: 2026-10-18. Branch local `codex/management-navigation`, base `dbf3d5fa067009cd9a255035a092f8c39c4507ac`; delta ainda local, preservando a reorganização anterior. Risco máximo R3 por apresentação de capacidades de criação; backend/autenticação/ledger não alterados.

## Antes e depois

Antes havia duas ações idênticas + Item, destinadas a estações diferentes, e edição escondida em disclosure com select de todos os produtos. Agora Adicionar produto é único: a estação autorizada é escolhida dentro do QuickCatalog existente. Editar produto e ícone é botão normal e abre ActionDialog: categorias/Todos, busca, produtos em grade e formulário existente de nome/ícone.

Reutilizados tokens, ProductIcon, normalização/categorias e geometria do seletor do Bar. Estilos desse componente ficam em CSS Module para isolar a apresentação e carregar junto do fluxo, sem novas cores/medidas. Grade extensa usa linhas max-content, preservando nomes e ícones e rolagem interna. Voltar/Escape percorre as camadas; foco retorna ao produto escolhido e depois ao botão de edição. Polling não sobrescreve nome em digitação; gravação/leitura de arquivo trava retorno. Erro/retry, busca vazia e revogação de leitura permanecem explícitos na camada aplicável.

Criação mantém autocomplete-first, reutilização exata e resolve-or-create. Escolha de estação é restrita às capacidades retornadas pela sessão; API continua autoridade. Nome/ícone mantêm endpoints e validações; nenhuma geração ocorre ao navegar. Upload continua limitado a5MB no cliente e validado pelo servidor. Sem novos campos, edição financeira, API/migration, publicação ou alteração de dados reais durante validação.

## Evidência

- Build e typecheck: PASS.
- Revisão independente do delta encontrou P2 de foco ao voltar do segundo produto de Todos; corrigido com lastPicked e regressão nas quatro larguras. Revisão após correção: sem achados reproduzíveis restantes, com limites de execução indicados pelo revisor. Não é aprovação GitHub.
- Primeira execução:21 Playwright PASS (8 catálogo,10 navegação gerencial,3 QuickCatalog). Negativas adicionais de permissão/revogação e upload:2 PASS após adequar fixture ao formato real code/message da API.
- Execução com CSS Module:23 PASS (10 catálogo,3 QuickCatalog,10 seletor de disponibilidade do Bar). Após conferência real, a execução final somou15 PASS (12 editor, incluindo50 itens/nomes longos360/1280, e3 QuickCatalog), em18.2s. Revisão independente do delta CSS/classes/rótulo final: sem novos achados; não é aprovação GitHub.
- Auditoria ESLint:21 diagnósticos legados/0 novos ou fatais no delta; Web safety0. Diff check PASS.
- Gate visual global executado durante a iteração:1 FAIL no seletor legado Contas em attendance-catalog.spec.ts:15;612 não executados por parada na primeira falha. Não é PASS global; sem alteração de baseline/tolerância.
- Capturas antes/depois com fixtures equivalentes em360/390/430/1280px: `visual-artifacts/catalog-editor/`. Fonte200%, teclado/foco e axe nos estados testados; não equivale a leitor de tela ou aceite de operador real.
- Conferência em navegador local: botão único, categorias reais, grade e abertura do formulário selecionado, sem salvar produto/ícone ou gerar imagem. Catálogo real não foi usado como fixture de teste.

## Limites

Sem commit/push/PR novo, merge ou deploy. Nenhum achado P0/P1 aberto na revisão local; gate visual global permanece bloqueado no Atendimento. Próximo responsável: mantenedor/operador para avaliar a navegação e aceite de uso; retomada do gate global depende da manutenção adjacente. Sem alteração do checkpoint preexistente.
