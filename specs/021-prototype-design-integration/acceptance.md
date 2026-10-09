# Aceite
- A1: cinco referências abrem via servidor HTTP, assets e runtime locais; manifesto identifica ZIP/hash/entrada.
- A2: Web e referência legada compartilham cores/fontes/controle primário; comparação visual de primitives equivalentes passa sem aceitar baseline novo.
- A3: resumo soma quantidades apenas em produção; fila/passe precedem catálogo e três colunas aparecem no desktop, sem overflow em 360–430 px.
- A4: transição individual envia endpoint/estado existente, loading impede repetição e falha nunca inventa sucesso; passe sem ready_at não mostra idade fabricada.
- A5: KB registra fontes, limites da simulação e mapping para specs; specs de offline/telemetria/financeiro permanecem autoridade.
- A6: Atendimento utiliza RodadaTheme em vez do MaterialTheme padrão; build debug e testes JVM passam. Paridade visual nativa completa requer revisão física separada.

## Evidência Web

A1–A5 verificados em 2026-10-08: typecheck/build e 110 testes visuais passam. Botão de produção: 0% de diferença; Cozinha completa: auditoria de diferenças intencionais em [relatório](../../docs/design/visual-parity-audit.md). Hashes do manifesto e links da KB verificados.

A6 verificado: 20 testes JVM passaram, assembleDebug e lintDebug concluíram com sucesso. Comando final: `cd apps/attendance-android && mise exec java@17.0.2 -- ./gradlew --no-daemon testDebugUnitTest assembleDebug lintDebug`. O port mantém suporte a API 26; a flag windowLightNavigationBar (API 27) foi removida, preservando o tema escuro compatível. Licenças são assets empacotados.
