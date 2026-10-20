# Spec034 S1a — comparação de Gestão

Antes: produto `e82d36c4`, planejamento `da644241`. Depois: branch
`codex/management-ux-gestao`, SHA de publicação no PR correspondente.
Fixture `tests/visual/fixtures.ts`, cenário normal, locale pt-BR, tempo congelado,
viewports360/390/430/1280 ×932. Não são dados operacionais nem evidência backend.

| Largura | Antes | Depois |
| --- | --- | --- |
| 360 | [Captura](before-360.png) | [Captura](after-360.png) |
| 390 | [Captura](before-390.png) | [Captura](after-390.png) |
| 430 | [Captura](before-430.png) | [Captura](after-430.png) |
| 1280 | [Captura](before-1280.png) | [Captura](after-1280.png) |

Mudança deliberada: painéis de botões são substituídos por seções e linhas com
descrição, ícone e avanço. Header compacta Atualizar/histórico com alvo44px.
As cinco rotas/grupos e estado de conexão permanecem; sem atualização de baseline
automatizado ou tolerância para fazer testes passarem.

Capturas full-page mantêm a navegação fixa na posição da viewport original;
para conferir a última linha em tela pequena é necessário rolar normalmente.
Zoom CSS200% foi testado separadamente; não equivale a leitura manual por leitor
de tela ou ensaio de zoom do navegador. Resultados e falhas estão no
[relatório da slice](../../../../specs/034-management-ux-standardization/s1a-evidence.md).
