# Integração dos protótipos da noite — KB

Contrato: [Spec 021](../../specs/021-prototype-design-integration/spec.md). Os ZIPs originais permanecem em `prototype/`; [manifesto](../../prototype/references/manifest.json) registra SHA-256, origem e entrada de cada export. O runtime DC/React dos exports é somente referência, não dependência de produção. As adaptações dos HTMLs importados trocam Google Fonts por fontes locais e usam sc-camel-src (binding já suportado pelo runtime) nas imagens interpoladas para impedir requests literais de {{...}} antes do mount; os originais permanecem nos ZIPs.

## Abrir e revisar

Na raiz: `python3 -m http.server 3101 --bind 127.0.0.1`. Abrir `http://127.0.0.1:3101/prototype/references/`. Evitar file:// nos exports DC. A referência anterior continua em `prototype/index.html`.

| Export | Conteúdo e destino | Contrato canônico |
| --- | --- | --- |
| Uma noite no bar | Atendimento, contas, pedidos, cobrança, overrides e Bar; fluxo simulado completo | Specs 001/002/003/006/009; Atendimento continua Android |
| Sistema Rodada | Paleta quente, papel para ação, tipos condensados, tempo/quantidade mono, linhas operacionais | Design system e tokens Web/protótipo |
| Tela da Cozinha | Resumo por produto → fila individual → passe; três colunas desktop | Cozinha e Bar conectados, Spec 021 |
| Modo pico | Prioridade, redução de ruído e ações grandes | Spec 003; não adiciona SLA, prioridade ou telemetria ao backend |
| Sem sinal → Sincronizado | Continuidade visual, pendência e recuperação contextual | Spec 014; simulação de envio não comprova confirmação |

## Decisões e diferenças intencionais

- A fila real mantém Aceitar → Preparar → Pronto conforme estado autorizado pela API. Não copia o botão Pronto que pula estados no demo. Resumo não dispara mutation em lote e não agrega entidades financeiras.
- Resumo soma quantidades de itens ainda em produção por nome snapshot; produtos de nomes iguais podem compartilhar somente a linha de leitura. IDs e ações individuais permanecem intactos.
- Tempo “Desde o pedido” vem de created_at. Tempo “No passe” vem de ready_at; campo ausente/inválido é explicitamente desconhecido. Não inferir ready_at de created_at. As rampas temporais dos demos dependem de futura política por Venue; não viram thresholds fixos em produção.
- Pegar/Levar/Entregue demonstram coordenação, não criam taps obrigatórios para métricas. Inferência requer source/confidence/provenance, e correções preservam fatos anteriores (Spec 003 / ADR 0009 de telemetria).
- Sem sinal permite leitura do último snapshot/drafts, nunca confirmação local de venda, disponibilidade ou pagamento. “Enviado” e “Sincronizado” não equivalem a confirmado sem resposta canônica, idempotência e reconciliação (Spec 014).
- Violeta representa contexto financeiro, madeira representa relacionamento. Erro/bloqueio continua danger; dinheiro próximo do limite preserva warning textual. Valores de R$30/80/200/500 no export são exemplos; API/política snapshottada permanece autoridade (Spec 002 / ADR 0011).
- Retratos e SVGs de produtos são dados demonstrativos preservados no export; nenhum é associado por nome a Customer/Product real. ProductIcon 1:1 e style contract continuam canônicos. Geração de IA adiada na Spec 020 permanece adiada.
- O artboard fixo de 1760 px/1280 px permanece referência desktop. O app real adapta hierarquia a 360–430 px, nomes longos, teclado, toque e foco visível.
- O Web recebe tokens e tipografia compartilhados em todas as superfícies. Atendimento usa RodadaTheme (paleta escura, Archivo local e raios 4/8 px), substituindo o tema Material padrão. Layout completo do Atendimento, pico e recovery é referência de evolução das specs existentes; não se declara paridade de fluxo/UI nativa nesta integração.

## Fontes e reprodução

Archivo variável (wdth/wght) e JetBrains Mono variável (wght) são distribuídas localmente em `prototype/fonts` e `apps/web/public/fonts`, com cópia empacotada para Atendimento em res/font e licenças em assets/licenses, com licenças OFL. Origem: google/fonts, diretórios ofl/archivo e ofl/jetbrainsmono. HTMLs de referência e Web não dependem de acesso a Google Fonts durante render.

Validação: `cd apps/web && npm run typecheck && npm run build && npm run test:visual`. A suíte verifica os cinco exports, compara o botão de produção diretamente ao Sistema Rodada importado (limite 0,1%, sem baseline novo), soma quantidades, timestamps e falhas individuais, além das superfícies adjacentes e primitives legadas. Android: `mise exec java@17.0.2 -- ./scripts/android-check.sh` (JDK 17 já instalado) executa unitários, assembleDebug e lintDebug. Screenshots de comparação em `visual-artifacts/` são evidência local, não arquivos de produto.

## Resultado registrado — 2026-10-08

Web: typecheck/build e **110 testes** passaram. Android: **20 testes JVM**, assembleDebug e lintDebug passaram com JDK 17 e Gradle Wrapper, em processo novo (`--no-daemon`). Importador reproduz exatamente todos os arquivos de referência; hashes originais e links da KB conferidos. [Relatório visual](visual-parity-audit.md) registra diferenças intencionais e a comparação de ação com 0 pixels diferentes.

## Caminho para o produto completo

O [plano de implementação](../architecture/full-product-implementation-plan.md) traduz os cinco exports em jornadas reais, contratos, PRs e gates de release. A [Spec 022](../../specs/022-full-product-implementation/spec.md) acompanha execução; a integração visual 021 não encerra o backlog operacional.

## Próxima entrega — paridade visual atualizada

O [plano pixel-perfect](pixel-perfect-implementation-plan.md) e a [Spec 023](../../specs/023-updated-prototype-visual-parity/spec.md) definem como alcançar fidelidade por tela/estado aos exports atualizados. A integração de tema/componentes não equivale a paridade completa; implementação e novos gates permanecem pendentes.
