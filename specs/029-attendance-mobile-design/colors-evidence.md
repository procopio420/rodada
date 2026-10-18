# Cores do Atendimento Android — evidência local

Data: 2026-10-16. Branch: `codex/android-attendance-colors`, base `ae960d59`.
Alterações locais, sem commit ou publicação nesta etapa.

## Resultado

Controles nativos reutilizam o fundo marrom, bordas quentes, preenchimento âmbar
de contexto/seleção/rascunho e foco do Web. A mistura usa canais sRGB, como o
`color-mix(in srgb, ...)` da referência. A mesa ocupada conserva faixa azul e
recebe a borda âmbar; os demais estados conservam suas cores semânticas.
Não foram alteradas regras, callbacks, disponibilidade ou confirmação financeira.

Arquivos: `RodadaTheme.kt`, `AttendanceHeader.kt`, `AttendanceNavigation.kt`,
`TablesScreen.kt`, `AttendanceScreen.kt`, `AttendanceCatalogCard.kt`,
`CategoryCatalog.kt` e `ProductCustomization.kt`, sob o módulo Android.
Contrato atualizado nesta spec e em `docs/design/system.md`.

## Validação executada

- PASS: assembleDebug, assembleDebugAndroidTest, 97 testes unitários e lintDebug.
- PASS: 13 testes Compose existentes antes e depois, incluindo catálogo,
  quantidade, workspace, mesas e bloqueio financeiro quando desatualizado.
- PASS: build Web e dois testes visuais focados de referência a 390px
  (categorias/quantidade e jornada de mesas/popup). Web não foi modificado.
- PASS: `git diff --check`.
- PASS: quatro testes Compose por largura de 360/390/430dp; 360dp com fonte
  a 200%. Capturas conferidas; tamanho, densidade, fonte e animações restaurados.
  APK atualizado instalado e MainActivity reaberta após a matriz.
- Contraste calculado: Paper/Control 13,77:1; Paper/seleção âmbar 10,90:1;
  Paper/contexto âmbar 13,30:1; Ink/Paper 15,75:1. Não representa auditoria
  completa de acessibilidade ou de todos os estados desabilitados.

Capturas e logs locais ignorados pelo Git:
`visual-artifacts/android-native-port/colors/{before,after}/rodada-critical-evidence/`
e `colors-*.log` no diretório pai. Referências Web recém-executadas em
`apps/web/visual-artifacts/029/{categories,unified}/`, arquivos de 390px.
As capturas anteriores de outras larguras não constituem evidência desta rodada.

## Limites

Aceite restrito às cores e regressões locais. Não certifica igualdade geométrica
Web/Compose, TalkBack, dispositivo físico ou produção. A indicação inicial
DESATUALIZADO do app é uma condição de sincronização separada; não foi ocultada
nem usada como indicação da versão instalada. Sem escrita de pedidos/pagamentos,
seed, reset, alterações de banco ou publicação nesta etapa. Próximo responsável:
teste visual do solicitante no APK local; revisão de código antes de eventual PR.
