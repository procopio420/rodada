# Rodada Android — auditoria visual executada em 13/10/2026

Piloto de referência: Bar do Aderlan. Dados desta execução: **exclusivamente fictícios**.
Código: `main@41e32d9853bc18ad08f136f5ead8bddc80afec77`, checkout dedicado em detached HEAD.

[Galeria local](evidence/android-visual-audit-2026-10-13/index.html) ·
[Montagem das cinco experiências](evidence/android-visual-audit-2026-10-13/five-experiences-montage.png) ·
[Manifesto](evidence/android-visual-audit-2026-10-13/manifest.json) ·
[Reprodução](evidence/android-visual-audit-2026-10-13/REPRODUCE.md) ·
[Plano em slices / Play Store](android-visual-audit-2026-10-13-slices.md).

## Escopo e grau de evidência

A auditoria abriu o APK nativo, navegou por controles reais, capturou PNGs originais e
os abriu no visualizador de imagens. **As cinco experiências foram executadas**:
mesas/comandas, cardápio, lançamento, acompanhamento e operação/pico. Os bloqueios de
observação de produto simples, remoção de item indisponível e saída com rascunho foram
capturados como problemas, sem implementar contorno no produto.

Isso é revisão visual local, não aceite de fidelidade integral, homologação no bar,
benchmark com garçom humano, validação de aparelho físico, provider ou release API37.
Build e testes complementam as imagens; não são sua substituição. Nenhuma correção de
produto/spec, commit, PR, push, merge, deploy ou publicação Play foi realizada.

Convenções: **M** = interação observada/executada; **S** = inspeção de código;
**H** = falha/atraso controlado pelo harness; **NM** = não medido. P0 exigiria evidência
suficiente de operação insegura ampla: nenhum P0 foi demonstrado. P1 afeta a operação
frequente ou a recuperação; P2 afeta apresentação/clareza localizada.

## Referência estabelecida e preservação

A pasta inicial `/home/lucas/projects/rodada` é um agrupador de worktrees, não a raiz
Git. O checkout `/home/lucas/projects/rodada/rodada` estava limpo em
`feat/pricing-adjustments-service-charge@79de2c36c901479fb8a83c1fcac60c3610d39b69`.
`git fetch origin main` atualizou a referência de c634726 para 41e32d9; criou-se o
worktree `/home/lucas/projects/rodada/android-visual-audit-2026-10-13` sem mudar os demais.
O SHA usado para compilar está em [environment.json](evidence/android-visual-audit-2026-10-13/environment.json), junto ao hash SHA256 do APK debug 0.1.0 / versionCode1.

**Spec 027 já integrada:** início em um toque, criação contextual de Tab, ownership e
botões de comandas homônimas foram vistos nesta execução. Não repetir o diagnóstico
antigo de comandas da mesa serem apenas texto ou de a ação global se chamar Pedir.
A ação atual é **Nova comanda**. O branding oficial também está integrado no pacote;
`verify-brand-v1.py` passou. A presença do pacote não significa que o header executado
use seu wordmark: o achado visual AV-09 é específico a essa apresentação.

Leituras: AGENTS raiz/Android, docs/agents/README.md, PROCEDURES.md e SKILLS.md; skills
locais rodada-android-compose, rodada-ui-design e rodada-pos-safety; princípios,
arquitetura, design system, brand-v1, prototype-integration, material-fidelity-review,
pixel-perfect-implementation-plan, `docs/design/spec023-review.md`, ux-friction-audit-2026-10-12 e README Android.
Documentos datados foram tratados como evidência dos seus próprios SHAs. Não alterados.

Specs identificadas pelo caminho completo:

- `specs/021-prototype-design-integration/spec.md`
- `specs/021-operational-ux-polish/spec.md`
- `specs/022-material-visual-fidelity/spec.md`
- `specs/022-full-product-implementation/spec.md`
- `specs/023-updated-prototype-visual-parity/spec.md`
- `specs/024-attendance-web/spec.md`
- `specs/024-venue-menu-import/spec.md`
- `specs/026-operational-ux-friction/spec.md`
- `specs/027-table-service-claim/spec.md`

Contratos adjacentes: `specs/001-core-pos/spec.md`,
`specs/003-dispatch/spec.md`, `specs/004-table-guest-ordering/spec.md`,
`specs/008-staff-auth-roles-devices/spec.md`, `specs/009-tab-operations/spec.md`,
`specs/010-product-modifiers-variants/spec.md` e
`specs/014-connectivity-degraded-operation/spec.md`.
Não existe pasta `.codegraph/` nesse worktree; CodeGraph não foi utilizado nem indexado.

## Ambiente e dados

Arch Linux, kernel CachyOS 6.18.6-2, x86_64; CPU AMD Ryzen 7 PRO 4750U / AMD-V.
JDK 17.0.2 completo com javac; Wrapper versionado Gradle 9.6.0; compile/target SDK 37 e
build-tools 37.0.0 preservados. Runtime documentado API 36 Google APIs x86_64 rev7,
Android 16, Emulator 37.2.12, KVM utilizável e SwiftShader. AVD exclusivo
`rodada-visual-audit-20261013` / emulator-5584. Confirmados boot 1, Package Manager,
Window Manager, instalação e abertura da MainActivity. Dois emuladores anteriores
foram preservados; somente um foi criado para esta missão.

PostgreSQL 17.11 em container `rodada-visual-audit-20261013`, bind 127.0.0.1:15483.
Banco `rodada_visual_audit`, sem volume/banco compartilhado. API real Django/DRF via
ASGI em 18081, dispatcher canônico e proxy local em 18080. APK debug usa propriedade
`rodadaApiBaseUrl=http://127.0.0.1:18080/` e adb reverse; release não foi alterado.
Companion Web em 13120 e referências locais em 13121. Python 3.12.13 em venv exclusivo.
PIN aleatório e tokens ficam em arquivos privados chmod 600 ignorados, nunca nas evidências.

Fixture `audit-aderlan-v1`: Venue Bar do Aderlan · DEMONSTRAÇÃO; operador fictício OWNER;
8 mesas iniciais, 7 comandas iniciais, dois Alex distintos e anônima na mesma ocupação;
Mesa 02 inicialmente disponível, Mesa 03 em limpeza, Mesa 04 fora de serviço, Mesa 06 com
pedido source GUEST e responsável nulo; catálogo 42 produtos/4 categorias, nomes extensos,
Bolinho indisponível, Hambúrguer com duas variantes e dois modificadores; Mesa 05 com
duas rodadas e estados Novo/Em preparo/Pronto; 6 entregas READY e 3 chamadas.
Novas Tabs/Orders desta auditoria foram criados por UI, não por imagem simulada.

Pedidos, ocupações, vínculos e produção da fixture usam serviços canônicos. Variantes,
configuração de catálogo, política de limite R$1.000 e os estados físicos iniciais são
fixtures explicitamente autoradas, não configuração homologada do Aderlan. SourceGUEST
foi preparado como dado de domínio: não se afirma autenticação por QR real nesta missão.
Nenhum recebimento ou pagamento foi criado para melhorar screenshot; recebido 0 é real.

## Matriz visual e estados

| Largura efetiva | PNG nativo | Density | Tamanho total | fontScale |
| --- | --- | --- | --- | --- |
| 360dp | 720×1688px | 320dpi / 2px por dp | 360×844dp | 1 e 2 |
| 390dp | 780×1688px | 320dpi / 2px por dp | 390×844dp | 1 e 2 |
| 430dp | 860×1688px | 320dpi / 2px por dp | 430×844dp | 1 e 2 |

A altura inclui chrome do sistema; não equivale a 844 dp livres para conteúdo.
FontScale 2 é a preferência de 200%; Android aplica escalonamento próprio. Nome de
arquivo sozinho não prova estado: o manifesto contém estado observado e observações.
Capturas durante interrupção do proxy estão rotuladas como cache/ambiente, não como
falha de autenticação ou cobertura normal aprovada. Mudanças de fonte deslocam o
índice de scroll; foram inspecionadas e feitas novas capturas com scroll efetivo.

| Experiência | Evidência principal | Cobertura/interação |
| --- | --- | --- |
| A Mesas/Tab | 004–008, 036–039 e matriz037 | Start1toque; anônima contextual; segunda Tab Mesa 02; homônimos; responsabilidade e estados físicos |
| B Cardápio | 009–023, 044/049 e complementos | Busca real, categorias, quantidade inline, duas configurações, edição de variante; item indisponível bloqueou remoção |
| C Lançamento | 013–028, 050–051 e recuperação | Três categorias, quantidade, observação em customizado, revisão parcial, POST/ACK real; nota simples inviável |
| D Acompanhamento | 029–030, 040–043 | Saldo/total/recebido separados; várias linhas, dois pedidos e estados; histórico depois do catálogo; saída com draft bloqueada |
| E Operação | 003,031–035,052 e recuperação | Pico controlado, fila READY/chamadas, claim real, navegação, pendência, perda/retorno |

Vazio: Tab recém-aberta com saldo0 (008/038) e busca sem resultado (041).
Loading, HTTP500 injetado, transporte interrompido, ACK retido e resposta perdida são
ensaios separados; ver manifesto e complementos abaixo. Não fabricar confirmação
local para esses estados. As captures027/051 mostram “Enviando pedido…”, enquanto028
mostra confirmação **após** resposta e releitura da API.

## Quatro fontes de verdade, separadas

| Fonte | O que comprova | Limite |
| --- | --- | --- |
| Intenção/spec | Tab distinta de Table/Occupancy, notas excepcionais, availability canônica, payload imutável, toque44dp, pico/exceção | Spec026 é guidance; não é implementação pronta |
| Protótipo executado | Hierarquia compacta, catálogo com ícones/quantidade, resumo contextual, tarefas no primeiro viewport | Dados, pagamento offline, PEGAR/ENTREGUE e SLA são simulações; não copiar regras |
| Código41e32d9 | Composables, tema, repos, guards, cifragem e pipeline de intenções | Código não prova jornada/dispositivo |
| APK/API executados | PNGs, ações, POSTs reais, Orders/Charges e recuperação observados | Emulador API 36 e fixture pequena; sem benchmark/GO do piloto |

Referências abertas em Chromium com fontes locais: prototype/index.html e os cinco
exports de prototype/references/ (night, system, kitchen, peak, connectivity), mais
material-reference. Night foi navegado por estados de Agora, busca, abertura,
localização e catálogo; referências de conexão são apresentações estáticas.
[Comparações](evidence/android-visual-audit-2026-10-13/index.html) identificam explicitamente
HTML simulado vs Android real. Mesas não possui export literal equivalente; o mapa
ilustrativo é contexto visual, não requisito de implementar floorplan.

Os dados dos exports e da fixture não são idênticos. As montagens reduzem PNG nativo
em50% para exibição de390dp/390CSSpx, mantendo originais. **Nenhum percentual de
pixel-perfect é reivindicado**, nenhuma baseline histórica foi alterada.

## Achados reproduzidos

Base dos paths Android: `apps/attendance-android/app/src/main/java/com/rodada/attendance/`.
Todos os PNGs citados estão em `docs/design/evidence/android-visual-audit-2026-10-13/`.
Critérios abaixo são propostas para próximas slices, não correções realizadas.

### AV-01 — P1: item indisponível fica preso no rascunho

1. Tela/componente: catálogo selecionado / controles de quantidade.
2. M: Suco no draft → disponibilidadeUNAVAILABLE via API → Atualizar. Produto,
   botão − e confirmar ficam disabled; draft impede sair. `enabled=false` foi
   conferido no controle clicável, não na glyph de texto.
3. Esperado: remover intenção local inválida, manter outros itens e revalidar API.
   `specs/001-core-pos/spec.md`, `specs/010-product-modifiers-variants/spec.md`,
   `specs/026-operational-ux-friction/spec.md`.
4. Prova: 018/021 e022-360/430; reproduzir conforme sequência acima.
5. Impacto: garçom fica sem caminho para continuar pedido quando produto acaba.
6. Severidade P1; não demonstrou venda indevida: confirmação estava bloqueada.
7. Recomendar permitir−/remover local mesmo UNAVAILABLE; aumento/envio continuam guardados.
8. Paths prováveis: operations/AttendanceScreen.kt, OperationsViewModel.kt.
9. Testes: Compose com availability mudando e várias linhas; API rejeita item stale;
   intenção já submetida continua congelada e não pode ser “editada” por esse controle.
10. Aceite: em 360/390/430/font1/2, remover item inválido em uma ação, total recalculado,
    demais linhas preservadas; zero mutação em pedido confirmado.

### AV-02 — P1: revisão mostra total, mas esconde linhas fora da busca

1. Tela/componente: TabWorkspace / resumo de envio.
2. M: após Cerveja2×, Fritas, Suco e duas configurações de Hambúrguer, busca Suco
   mostra 1 produto e total 6 unidades/R$ 129. Confirmar não abre conferência completa.
3. Esperado: conferir cada linha, quantidade, customização/nota e destino antes do POST;
   `specs/001-core-pos/spec.md`, `specs/010-product-modifiers-variants/spec.md`,
   `specs/023-updated-prototype-visual-parity/spec.md` e `specs/026-operational-ux-friction/spec.md`.
4. Prova: 016/017/024, ref-night-6, compare-lancamento; repetir as buscas.
5. Impacto: precisa lembrar itens ocultos ou refazer buscas; maior risco de revisar
   quantidade/configuração errada. Não foi demonstrado pedido diferente do payload.
6. P1.
7. Recomendar resumo persistente e revisão expansível usando o mesmo cart; não criar
   outro cart ou intenção, nem exigir confirmações financeiras adicionais.
8. Paths: operations/AttendanceScreen.kt (TabWorkspace/OrderCart), OperationsViewModel.kt.
   S: OrderCart existe, mas não é chamado na tela atual.
9. Testes: 3 categorias, 2 configurações, busca ativa, edição/remover, fonte 200% e pending.
10. Aceite: todas as 5 linhas/6 unidades e R$ 129 revisáveis sem percorrer 42 produtos;
    confirmação envia exatamente essa composição/destino/UUID.

### AV-03 — P1: não há observação para produto simples

1. Tela/componente: seleção/edição do catálogo simples.
2. M: Suco/Cerveja adicionam diretamente e oferecem −/+, sem Editar ou Pedido especial.
   Hambúrguer abre sheet e aceita notas/edição. A tentativa do caso simples ficou inviável.
3. Esperado: notas excepcionais permitidas mesmo sem variant/modifier;
   `specs/010-product-modifiers-variants/spec.md` (invariante 10 e ergonomia).
4. Prova: 017 versus 015; Web executado em web-nota-produto-simples-390.
5. Impacto: pedido “molho separado”/instrução de serviço não consegue acompanhar item simples.
6. P1.
7. Recomendar Editar para qualquer linha; manter quick-add de um toque e reutilizar sheet.
8. Paths: operations/AttendanceScreen.kt, ProductCustomization.kt.
9. Testes: produto sem schema, nota trim/500 caracteres, quantidade 2, edição antes de POST;
   snapshot canônico e mesma nota após readback/replay.
10. Aceite: quick-add continua 1 toque; nota acessível por ação contextual e preservada na
    linha certa sem inventar preço/modificador.

### AV-04 — P1: rascunho bloqueia interrupção e retorno

1. Tela/componente: ←Comandas / navegação de TabWorkspace.
2. M: tocar ←Comandas com draft não saiu nem abriu decisão; banner manda confirmar/remover.
   Não houve perda silenciosa; houve bloqueio explícito da troca de contexto.
3. Esperado: retorno contextual com draft preservado, ou bloqueio claramente comunicado
   no próprio controle; guidance `specs/026-operational-ux-friction/spec.md` e `specs/014-connectivity-degraded-operation/spec.md`.
4. Prova:019/020; criar qualquer linha e tocar Voltar. Ensaio sair/retornar com draft
   não submetido foi **bloqueado pelo produto**, não marcado PASS.
5. Impacto: chamada urgente ou outra mesa exige concluir/desmontar intenção local.
6. P1.
7. Recomendar drafts por Tab e retomada explícita; comandos já submetidos mantêm freeze,
   session/venue/ator/destino/UUID. Contrato da nova navegação precisa ser fechado antes de implementar.
8. Paths: operations/AttendanceScreen.kt, OperationsViewModel.kt, PendingMutationIntentStore.kt.
9. Testes: alternância A/B, homônimos, app restart, outra sessão, draft inválido e pending.
10. Aceite: sair/retornar restaura linhas/quantidades/notas da mesma Tab; resultado
    desconhecido nunca é adotado por outra Tab/sessão nem cria UUID novo.

### AV-05 — P1: Pico mantém entregas fora do primeiro viewport

1. Tela/componente: TabList / fila Agora/Pico.
2. M: 6 READY + 3 chamadas + 1 QR; primeiro viewport tem QR, texto e começo das chamadas,
   sem entrega. Pico diz “Só entregas”, mas continua mostrando chamadas. Foram executados
   **2 gestos automatizados** até a primeira entrega (390/font1), registrados em trace.
3. Esperado: próxima tarefa/prioridade/idade escaneáveis; `specs/003-dispatch/spec.md`,
   `specs/022-material-visual-fidelity/spec.md`, `specs/023-updated-prototype-visual-parity/spec.md` e `specs/027-table-service-claim/spec.md` (não esconder QR relevante).
4. Prova:031/032/033, ref-peak-0; ativar Pico na fixture intacta.
5. Impacto: esforço para localizar pronto; piora com fonte 200% e volume. Não inferir atraso/SLA.
6. P1.
7. Recomendar compactar QR e integrar filas/prioridade com tipos claros; ajustar copy;
   preservar provenance. **Não adicionar PEGUEI/ENTREGUE obrigatórios para métricas.**
8. Paths: operations/AttendanceScreen.kt, ServiceRequest.kt/DTOs, API dispatch queries se contrato requer.
9. Testes: 6/12 READY, chamadas/prioridades/idades desconhecidas, QR sem responsável,
   outra pessoa claim, stale e fonte 200%; sem mutations de entrega pelo render.
10. Aceite: em 390/font1, primeira tarefa real e próxima ação no viewport inicial;
    metas de 360/font2 precisam desenho validado, sem esconder informação crítica.

### AV-06 — P1: fonte 200% recorta “Nova comanda”; teclado invade header

1. Tela/componente: AttendanceNavigation / insets de busca.
2. M: em 360/390/430/font2, botão central mostra “Nova comand” com último caractere
   cortado. Com IME real em 390/font1, header foi panado por trás da barra de status.
3. Esperado: texto completo, alvos ≥44 dp, scroll/foco/insets;
   `specs/023-updated-prototype-visual-parity/spec.md`, `specs/027-table-service-claim/spec.md` e docs/design/system.md.
4. Prova:037-font200 e 026; repetir configuração e focar Buscar no catálogo.
5. Impacto: ação central mal legível e contexto sobreposto; não reduzir a fonte escolhida.
6. P1.
7. Recomendar medir conteúdo contra ancestral que aplica clip, adaptar largura/altura
   da ação e consumir IME sem panar identidade para a barra do sistema.
8. Paths: ui/AttendanceNavigation.kt, ui/AuthApp.kt, operations/AttendanceScreen.kt.
9. Testes: label real “Nova\ncomanda”,3 larguras/font1/2, pai/clipping e IME; screenshot
   do app conectado. O teste existente de label real falhou por clipping vertical; manter a reprovação e verificar também contenção no pai.
10. Aceite: cada glyph e linha dentro do botão/área útil, sem sobreposição de status/nav/IME,
    ações/foco acessíveis; callbacks e busy preservados.

### AV-07 — P1: expiração operacional expõe erro técnico ao garçom

1. Tela/componente: refresh operacional / modal Atenção.
2. M: após ~15 min, GET dispatch/requests,payments/capabilities,tabs recebeu 401;
   modal ACCESS_TOKEN_EXPIRED apareceu. SSE depois recebeu 401 e refresh 200.
3. Esperado: refresh rotativo transparente para operações autorizadas; recusar revogação
   real sem replay indevido. `specs/008-staff-auth-roles-devices/spec.md`, `specs/014-connectivity-degraded-operation/spec.md`.
4. Prova:045-auth-expirado-w360-f200 e auth-expiry-transport.json. Causa sugerida por S:
   AuthRepository trata AuthApiException, cliente operacional lança OperationsApiException.
   Isso é hipótese de fronteira a reproduzir em teste, não diagnóstico exaustivo.
5. Impacto: aviso de implementação interrompe atendimento; pode aparentar erro de rede.
6. P1.
7. Recomendar boundary de erro/auth comum e refresh serializado com retry seguro;
   não suprimir 401/403 nem ampliar sessão para “resolver”.
8. Paths: auth/AuthRepository.kt, operations/OperationsHttpClient.kt,
   realtime/OperationalRealtime.kt e guards de sessão.
9. Testes: TTL curto em fixture, leituras/mutation com token expirado, duas requests,
   refresh rotativo/revogado, originating-session e recuperação de Order congelado.
10. Aceite: expiração ordinária revalida sem modal técnico ou novo login; revogação
    limpa acesso; mutation conservaUUID/payload. SEMSINAL de043b/044/046 foi causado
    **pelo proxy parado** e não serve como prova adicional desse bug.

### AV-08 — P1: Contas não desambigua homônimos nem oferece busca

1. Tela/componente: lista globalContas.
2. M: doisAlex com R$0 aparecem idênticos; sem referência/mesa/horário ou campo de busca.
   EmMesas, Spec027 exibe referências distintas e botões utilizáveis: preservar melhoria.
3. Esperado: escolha daTab inequívoca; `specs/026-operational-ux-friction/spec.md`, `specs/027-table-service-claim/spec.md` e princípioTab≠Table.
4. Prova:039 versus004/037; abrirContas e rolar atéAlex.
5. Impacto: seleção baseada em posição; precisa navegar aMesas para conferir identidade.
6. P1.
7. Recomendar busca nome/código/mesa e referência estável/mesa na linha e no detalhe;
   nunca resolver identidade por nome ou transferir ledger.
8. Paths: operations/AttendanceScreen.kt (TabList), modelos/DTOs deTab eprojection API.
9. Testes:homônimos/anônimas, localização mutável, paginação, busca efont200.
10. Aceite: duasTabs de mesmo nome/saldo continuam distinguíveis na lista e detalhe;
    selecionar referênciaBcarregaIDB, não primeira ocorrência do label.

### AV-09 — P2: branding integrado não é usado no header; identidade visual incompleta

1. Tela/componente: header/login/catalog/balance.
2. M: header“● rodada” é tipográfico; login“Rodada Atendimento”; catálogo semProductIcon;
   preços/saldo usamArchivo no lugar de mono. Nomes longos ficam completos, mas uma
   linha de produto ocupa várias linhas/labelsBAR/KITCHEN técnicos.
3. Esperado: curvas oficiaisassets/brand/v1, Archivo/JetBrainsMono, ProductIcon/fallback e
   semântica de estados. docs/design/brand-v1.md, system.md e specs021/022/023.
4. Prova:001/009/014/030 ecomparações. `verify-brand-v1.py` passou: pacote vetorial
   existe; não afirmar quebranding está ausente da main.
5. Impacto: reconhecimento/escaneabilidade piores e baixa densidade. Publicação de
   ProductIcon não foi ensaiada; ausência do espaço/fallback foi observada.
6. P2.
7. Recomendar consumir artwork oficial, números mono ecomponentes canônicos;
   não redesenhar logo nem criar identidade específica do Android.
8. Paths: operations/AttendanceScreen.kt (Header), ui/AuthApp.kt, ui/RodadaTheme.kt,
   operations/CatalogProductButton.kt eassets/resdrawables jáexistentes.
9. Testes:wordmarkoriginal, fallback/assetpublicado/failed, códigos humanos,
   contrastes/estadosselected/disabled e nome longo em3 larguras/font1/2.
10. Aceite: artwork vem doSVGvetorialoficial; identidade1:1deProduct compartilhada;
    preço legívelmonoesemântica canônica, sem aumentar trabalho no pico.

### AV-10 — P2: histórico não distingue rodadas por número/data

1. Tela/componente: Pedidos confirmados.
2. M: dois blocos intitulados“Pedido”; linhas/estados estão presentes, mas sem número,
   hora ou atalhoHistórico/Novo pedido. Para inspecionar sem42produtos, usou-se busca
   sem match, contorno documentado e não comportamento esperado.
3. Esperado: histórico escaneável e acesso contextual à próxima ação;
   `specs/001-core-pos/spec.md`, `specs/023-updated-prototype-visual-parity/spec.md` e `specs/026-operational-ux-friction/spec.md`.
4. Prova:040/041/042 e043. EstadosNovo/Em preparo/Pronto foram executados com dadoscanônicos.
5. Impacto: reconstruir qual rodada é anterior e rolar entre financeiros/menu/histórico.
6. P2.
7. Recomendar número/horário canônicos, configurações separadas e atalhos dentro daTab.
8. Paths: operations/AttendanceScreen.kt, TabDetail/OrderDTOs emOperationsHttpClient.kt.
9. Testes:duasrodadas com itens iguais, modificadores, histórico longo e estadosmudando.
10. Aceite: operador identifica cadaOrder e sua ordem sem memorizar; total/recebido/saldo
    continuam separados e derivadosdaAPI, não recalculados só comlinhas visíveis.

### AV-11 — P2: feedback de envio mistura estados e pede “Entendi”

1. Tela/componente: modalEnviando / fila local.
2. M: enquantoONLINE, modal“Enviando pedido…” e fila“AGUARDANDO CONEXÃO” coexistem;
   envio econfirmação são dialogscomEntendi, não progresso contextual.
3. Esperado: pendingACK≠offline, confirmação só apósAPI; `specs/014-connectivity-degraded-operation/spec.md` eAndroidAGENTS.
4. Prova:027versus028; after_delay18 noPOSTreal.
5. Impacto: mensagem contraditória e interrupção de tela. Sucesso não foi otimista.
6. P2.
7. Recomendar status não modal junto daintenção, usarestadoPENDING=Enviando,
   CHECKING=Verificando eACTION_REQUIRED=Revisão; erro precisa próximaação.
8. Paths: operations/OrderRecoveryPolicy.kt, OrderSubmissionStatus.kt,
   AttendanceScreen.kt eOperationsViewModel.kt.
9. Testes:ACKlento, timeoutapóscommit,500,4xxterminal,restart eoffline.
10. Aceite: duranteesperaONLINE nãoalegafaltaderede; nuncaexibesucessoantesdoACK/readback;
    fecharfeedbacknãoapagaouduplicacomando.

## Comparação com Atendimento Web executado

A Web foi aberta em Chromium local em390×844CSSpx, autenticada na mesmafixture/API,
sem mocksdeAPI. Agora/Mesas/Contas, organização deMesa01, seleção deRodadas, buscaÁgua,
quick-add e edição de produtosimples foram navegados. Capturas web-*-loaded/web-draft
são fullpage: sua alturaPNG é extensão do documento, **não** viewport humano.
Capturas web-agora/web-mesas iniciais preservam loading como estado separado.

Melhorias observadas naWeb: categorias acionáveis, busca, ProductIconfallback eEditarnota
emproduto simples. Limitesobservados: header longo/bannerde“Teste sempagamentos”,
listaabertainteira antesdacomandaselecionada, histórico entrepedidoatualecatálogo;
nenhuma equivalênciavisual completaaoAndroid ouaoproto. AWebnãoébaselinecorretapordefinição.
Nãoexecutadosnesta comparação:pagamentos,correções,providersoujornadaWebdepersistência/reload.

## Medições, estimativas e metas

| Jornada realmente executada | M | Limite |
| --- | --- | --- |
| Mesa 02 disponível → iniciar atendimento | 1toquede negócio | Exclui localizarMesa por scroll |
| Ocupaçãoativa → Tabanônima | 2: Nova comanda + Abrir e pedir | Zerocampos obrigatórios; abertura levouaworkspacefinanceiro |
| Cerveja1→2 | 1 no+ | Quantidadeinline observada |
| Trêsprodutosdecategoriasdistintas | 3seleções +3buscas +1ajustedequantidade | Acertosporbusca, não teste de chipsdecategoria; rolagemseparada |
| ModoPico topo → primeiraentrega | 2 gestosautomatizadosdescroll | Fixture6READY/3chamadas/1QR; font1/390 |
| Claim de chamada | 1ação | API retornouVocêestáresponsável; não concluiuentrega |
| Sair deTab comdraft | 1tentativa bloqueada | Não inventar jornada deretorno bem-sucedida |

`interaction-trace.jsonl` registra eventosdeautomação, inclusive tentativas deharness;
apenasjourneysdelimitadas servem para contagem. Foco/digitação/teclas e duração detool
não foramconvertidos em tempo detrabalho. **Tempo humano=NM**, sembenchmark percentuais.
Metas futuras: revisão completa sem catálogo longo, remoçãoinválida1ação, primeiratarefa
visível, busca+seleção para homônimo. São critériospropostos, não ganhos medidos.

## Testes e limites de aceite

Executados: JDK/javac/SDK/KVM/boot/PackageManager/WindowManager/Activity;
GradleWrapper `testDebugUnitTest assembleDebug lintDebug` —63testes, zerofalhas/skips,
build/lintpassaram; `assembleDebugAndroidTest` também compilou.
APIcheck e `makemigrations --check --dry-run` passaram;
pytestPostgreSQL dos5arquivosordering/customization/table_service/concurrency —44PASS,
zerofalhas/skips; verify-brand-v1PASS. Logs/XML emchecks/.

Os resultados de force-stop/replay e teste instrumentado focado estão no complemento
final abaixo. Não executar suíte instrumentada completa, todos os gates Web, API26/37,
aparelhofísico, TalkBack, fornecedor/pagamento/fiscal ou testecomgarçom não podevirarPASS.
O teclado real do emulador foi aberto; inspeção de foco/insets complementa, não certifica
acessibilidade completa. Contraste/largura detargets sãoamostras, nãoavaliaçãoWCAGglobal.

## Ocorrências de ambiente preservadas na evidência

- A primeira tentativa comnohup não deixou emuladorvivo; executadoemforeground.
- Bootdemorou a registrarPackageManager/WindowManager; nãoforamtratadoscomoappparado.
- APIrunserverWSGI foi trocada porASGI+dispatcher paraSSE; ONLINEvalidado depois.
- DumpsUIparalelos interferiram; automaçãopassouaserial econtrolesclicáveis, nãoglyphs.
- Proxyparou comexit143; upstream18081continuou200. Artefatos043b/044/046 mostram
  cache/perda desse ambiente, explicitamente rotulados. Depoishealth/reverse/readback
  eONLINE048revalidaram oapp; não declararestadosafetadoscomoparidadenormalaprovada.
- Seekempáginarolada apósfontScale usou direçãoruim; helperpassouareverternofim e
  abortaremmodal. Scrollsdesseerro nãoforamusadoscomomediçãohumana.

## Complemento final e handoff

Ver manifesto, ensaios canônicos e instruções de reprodução para resultados finais.
Esta auditoria mantém achados abertos e snapshots originais. O próximo responsável é
engenharia Android/API conforme as slices propostas; decisão de fidelidade/release
permanece **NO-GO**, com cinco experiências capturadas, gates complementares aprovados e reprovação instrumentada registrada.

### AV-12 — P1: reinício offline não oferece retomada da sessão existente

1. Tela/componente: AuthApp / restauração após force-stop.
2. M/H: o servidor confirmou a intenção, ACK foi retido, app encerrado e reverse
   removido. Novo processo mostrou formulário de login e erro de conexão, sem a
   pendência acessível. Isso não provou perda do registro cifrado: o replay online
   posterior confirmou sua conservação.
3. Esperado: distinguir sessão existente que precisa revalidar de novo login;
   recuperação segura sem orientar criação de nova intenção/sessão. Contratos:
   `specs/014-connectivity-degraded-operation/spec.md` e
   `specs/008-staff-auth-roles-devices/spec.md`. Não conceder novo login offline.
4. Prova:052; restabelecer reverse e reabrir sem digitar PIN produziu053/054/059.
5. Impacto: operador vê login em vez de estado de recuperação e pode acreditar
   que precisa autenticar novamente enquanto há pedido de resultado desconhecido.
6. P1 de orientação/continuidade, **sem perda/duplicação demonstrada**.
7. Recomendar tela de revalidação/retomar sessão existente com próxima ação segura;
   política de cache/autorização precisa ser explícita antes de alterar comportamento.
8. Paths: auth/AuthRepository.kt, AuthViewModel.kt, ui/AuthApp.kt,
   operations/PendingMutationIntentStore.kt.
9. Testes: processo novo offline, resposta perdida, mesma sessão/ator, sessão
   revogada e outro login; nenhum privilégio baseado apenas em cache.
10. Aceite: retorno online revalida a sessão e reconcilia a mesma intenção;
    offline explica pendência/limite e não induz novo pedido. Zero novo Order/Charge.

### AV-13 — P2: Agora mostra zero antes da primeira leitura

1. Tela/componente: contadores de Agora durante carregamento/recovery.
2. M:053 mostrou“0 PRONTOS / 0 CONTAS” enquantoVERIFICANDO, mas a fixture possuía6/9;
   054 mostrou6/9 após leitura. Não era fila vazia confirmada.
3. Esperado: desconhecido/carregando antes do snapshot, último estado com timestamp
   depois; `docs/design/system.md` e `specs/014-connectivity-degraded-operation/spec.md`.
4. Prova:053→054; iniciar novo processo com primeira leitura lenta.
5. Impacto: pode sugerir ausência de trabalho enquanto a consulta ainda não terminou.
6. P2.
7. Recomendar placeholder/loading para contagem ainda não medida, sem inventar cache.
8. Paths: operations/AttendanceScreen.kt eOperationsUiState/lastSyncedAtMillis.
9. Testes: primeira leitura atrasada, erro inicial, vazio canônico e snapshot antigo.
10. Aceite: contagem numérica só aparece com snapshot confirmado; vazio e loading
    são visualmente distintos. Nenhuma mutation depende de zero local fictício.

## Resultado final dos ensaios e estado deixado

**Não duplicação comprovada no recorte executado:**

- Primeiro pedido UI: 5 linhas/6 unidades, R$ 129. ACK retido 18 s causou 201 → retry 200;
  mesma chave e SHA256 do payload; um Order, 5 Charges somando 12.900 centavos.
- Segundo pedido UI, Mesa 05: uma Cerveja de R$ 12. Antes do force-stop, PostgreSQL
  já tinha um Order/uma Charge de 1.200 centavos. O app não recebeu aquele ACK.
- Novo processo offline mostrou o bloqueio AV-12. Após restaurar reverse e reabrir
  **sem novo PIN/login**, houve replay 200 do mesmo payload/UUID. O banco permaneceu
  com um Order e uma Charge; UI mostrou R$ 112 na Tab que tinha R$ 100 (059).
- JSONs: `canonical-first-confirmed.json`, `canonical-after-commit.json`,
  `canonical-after-replay.json`; nenhum contém credencial. UUID é intenção de
  negócio, não access token. Não foi executado pagamento ou settlement.
- Erro 500 no catálogo foi injetado pelo proxy (055); retirada da falha e leitura
  canônica recuperaram ONLINE (056). Não atribuir essa falha ao Django real.
- 057 é o **splash nativo de inicialização**, com símbolo oficial, capturado antes
  de o conteúdo aparecer; não chamá-lo de screenshot da lista carregada ou do
  spinner deTabs. O estágio de consulta/reconciliação do app está em 053.

**Gate instrumentado reprovado:** APK androidTest compilou; o teste existente
`com.rodada.attendance.ui.AttendanceNavigationTest#productionNewTabLabelFitsAndOpensOnce`,
em 360 dp/320 dpi/fontScale 2/API 36, executou 1 teste e falhou 1, sem skip:
**“Vertical text clipping: Nova\ncomanda”**. Log original em
`checks/navigation-instrumented-w360-f200.log`. Confirma AV-06; nenhum limiar/teste foi
alterado e nenhuma correção foi realizada. O exit code do adb não substituiu a
inspeção de FAILURES no resultado de instrumentação.

Dependências criadas/instaladas: venv Python isolado (`uv`, sem pip global),
Django 5.2.18, DRF 3.18.3, psycopg 3.3.6, cryptography 46.0.7, uvicorn 0.54.0,
Pillow 12.3.0, pytest 8.4.2, pytest-django 4.14.0 e demais versões no freeze entregue;
`npm ci` instalou 36 pacotes locais (Next 16.3.8, React 19.3.0, Playwright 1.58.2 etc.).
Container PostgreSQL 17.11 e AVD próprios foram criados. JDK, SDK/platform/buildtools,
Emulator/KVM, Docker/Node/Chromium já existiam e foram reutilizados; nenhum apt/sudo,
rebaixamento de versão ou alteração de virtualização/permissão global foi necessário.
A ausência de pip no venv não foi bloqueio: instalação e controle foram feitos com uv.

Locale do AVD é o default en-US (datas de recovery podem aparecer em formato americano);
Web/refs usam pt-BR. Isso é explicitado no ambiente, não confundir datas textuais com
business date homologada. Idades da fixture avançaram durante a auditoria: não são SLA,
atraso de produção real ou tempo de um garçom.

Arquivos novos somente: este relatório, plano em slices e pasta de evidências/harness.
Metadados gerados pelo install/build Web nos arquivos já versionados foram restaurados
byte a byte ao HEAD deste checkout inicialmente limpo. Nenhuma alteração rastreada
no produto ficou pendente; outros worktrees e dados preexistentes foram preservados.

Serviços da auditoria deixam-se prontos para nova inspeção: PostgreSQL 15483,
API 18081, dispatcher, proxy 18080 (controle `{}`), Web 13120, referências/galeria 13121
em localhost e único AVD próprio emulator-5584. Configuração de exibição está em
390 dp/fontScale 1, reverse 18080 ativo e APK debug instalado. A lista final e health
estão em `services-final.json`. Comandos exatos/dependências em REPRODUCE.md/checks/.

Concluído o **escopo de auditoria visual local das cinco experiências**, com bloqueios
capturados e limites acima. **Produto visual/release: NO-GO** até resolver os P1 e
repetir os gates; paridade global, hardware/provider/Play e matriz completa de exceções
em todas as larguras continuam fora do aceite. Exceções de rede foram aprofundadas em 390 dp;
a matriz 360/390/430 × font 1/2 cobre composição/jornadas, não todos os cruzamentos possíveis.

Conferência da entrega: galeria aberta no Chromium/Playwright, 140 imagens, filtro funcional e PNG original carregado (720×1688). Todos os links locais da galeria existem. Registro de inspeção com hashes em `inspection-journal.json`; serviços tiveram health revalidado em `services-final.json`. App deixado ONLINE, MainActivity aberta, 390 dp/320 dpi/fontScale 1.
