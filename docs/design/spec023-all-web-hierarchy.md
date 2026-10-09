# Spec023 — acabamento compartilhado das telas Web

Contrato6fcd10a, adaptação da demo3bedc92, código Web bdb29bf e código demo9789d41. Branch de revisão codex/spec023-management-hierarchy baseada em mainae416da; PR65 mantém a Gerência anterior e acrescenta esta slice. Original codex/ux-operational-polish permanece preservada. Não há merge na main/produção.

## Resultado e cobertura

OperationalHeading/OperationalIcon reutilizados em74 títulos/seções de23 arquivos; nível, texto, id, foco e nomes acessíveis mantidos. SVGs decorativos aria-hidden. Ícones existentes de identidade das estações e Fazer agora preservados sem duplicação; ProductIcon não é substituído. Cabeçalhos com separação, seção20px/subseção16px, título34px, sombras funcionais discretas sem acumular em painéis aninhados. Saldo e total têm hierarquia distinta em BillSummary, mantendo centavos/cálculos originais. Atendimento Web tem ícone+rótulo nos três destinos existentes. Fila e passe têm separadores e peso tipográfico maior; callbacks/estados/quantidades/personalizações não mudaram.

| Superfícies | Componente/cobertura |
|---|---|
| Entrada e sessão /staff | StaffAuthScreen; matriz6larguras, teclado/permissões e integração real |
| PDV /pos | OrderWorkspace; matriz6larguras/estados e pedidos/pagamentos/preços reais |
| Atendimento /attendance | AttendanceWeb;360/390/430, login/pedido/entrega/mesa/logout reais sem pagamentos |
| Bar/Cozinha | ProductionBoard; matriz6larguras/estados, V03 fixture/V04ações e disponibilidade reais |
| Cliente /guest/:token | GuestOrdering; matriz6larguras/estados, API de pedido/customização/rastreamento |
| Caixa/Gerência/Relatórios/Estornos | Matriz6larguras/estados e gates existentes; hash/seleção/adjacência preservados |
| /manage/catalog | CatalogCustomizationEditor;360/390 e testes existentes de variações/grupos/opções e API |
| /manage/pricing | Política/aprovações360/390/768 e integração comercial real |
| /manage/printing | Impressoras/trabalhos360/390/1280; estados de bridge honestos |
| /manage/alerts/:id e /manage/alerts/settings | Headings compartilhados; gates existentes de contexto/provenance/conflito em viewport móvel padrão390 |
| /receipt/:token | Moldura/contexto360/390/768, texto exato e erro410; não altera conteúdo canônico |
| /printing/jobs/:id | Moldura360/390/768, HTML/texto históricos idênticos, estado OUTPUT_READY sem alegar papel confirmado |
| / | Redirecionamento existente para /staff, sem mudança |

Matriz6:360/390/430/768/1280/1440. As subpáginas com cobertura mais estreita acima não são declaradas verificadas em seis larguras. Android não foi alterado; extensão solicitada aplicada às telas Web. Não há novas telas, ações, APIs, regras financeiras ou mudança de autenticação.

## Evidências e validação

[Antes/depois/viewport390](evidence/spec023-all-web/) usam a fixture visual existente; nomes/valores são dados de teste. [Inventário](evidence/spec023-all-web/heading-inventory.json), [hashes](evidence/spec023-all-web/sha256.json). Types/build passam; **193/193 visuais**, sem retries/skips; **8/8 realtime**, **11/11 integração API ASGI/PostgreSQL** em rodada atual. Reutilizados testes de Field/StatusBadge, primitive/reference, preços, impressão, customização e fluxos. Acrescentados seis casos só para molduras de recibo/documento sem cobertura anterior.

Primeira rodada193:190 passaram/3falhas nos novos testes de recibo, por seletor ambíguo que também encontrava o route-announcer. Seletor limitado ao main; assert de erro e remoção do conteúdo mantidos. Fixture de documento usa OUTPUT_READY (estado real) e exige mensagem papel não confirmado. Correção de teste/cores semânticas seguida de build e suíte completa193aprovada.

A comparação literal inteira Cozinha390×844 mede **17.5969%** de pixels diferentes da referência, [estatística](evidence/spec023-all-web/kitchen-literal-stats.json). Há composição operacional/dados diferentes já documentados e esta extensão de hierarquia; não representa equivalência total nem aprovação pixel-perfect. Referências, tolerâncias e baselines imutáveis. Testes das primitivas/Field/StatusBadge e pictograma Agora continuam com seus gates estritos. A estética acrescentada é uma extensão documentada, não reprodução literal de telas sem export.

## Ambiente e preservação

PostgreSQL55459 foi encontrado parado; serviço reaberto com **o mesmo diretório pgdata**, sem init/reset/migration/deleção. PostgreSQL realizou sua recuperação automática e voltou ready. Banco de testes anterior preservado como rodada_web_e2e_before_all_web_polish; rodada_web_e2e criado para esta rodada. Banco rodada_demo preservado. API/dispatcher da demo também encontrados parados, reabertos no mesmo checkout/banco. Não se infere causa da interrupção.

A adaptação demo-functional usa exclusivamente headings/ícones/CSS e composição da Gerência; preserva auth-gateway/session-refresh e backend. Não absorve novas rotas/contratos de Atendimento/alertas da main nessa base antiga. A branch principal cobre essas páginas da main. Adaptação validada em9789d41: typecheck/build, **173/173 visuais**, **4/4 testes session-refresh** e **10/10 integração real PostgreSQL** em portas8130/3130, banco exclusivo. Auth-gateway/session-refresh/rotas API e apps/api byte-idênticos ao872449a. Bar, Caixa e Gerência verificados read-only no navegador, com sessão existente carregada e Ao vivo nas superfícies operacionais. Não foram registrados pedidos ou pagamentos nesse banco de uso durante a conferência manual.

GO para revisão visual/uso demonstrativo das telas Web cobertas, condicionado aos limites de demo já existentes. Não homologa pagamento externo, impressora física, Android/dispositivo, produção ou paridade023total. Próximas pendências existentes: fonte/zoom global200% e safe areas/teclado nas páginas internas, fidelidade completa das regiões restantes e validação nativa. Sem funcionalidades novas por reflexo.

A demo continua em http://127.0.0.1:3119; API18764, dispatcher e PostgreSQL55459. Prévia completa main em http://localhost:3123 com API8123 e banco `rodada_web_e2e_main_all_web`, preservado da rodada11/11. Banco de testes da adaptação fica em `rodada_web_e2e`; nenhuma suite apontou para `rodada_demo`. Evidências públicas usam somente fixtures; não se publicam capturas/logs com nomes/identificadores do banco do usuário. CI remoto não substitui estes gates locais e é relatado separadamente.
