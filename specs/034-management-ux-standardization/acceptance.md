# Aceite — Spec 034

**Estado original do planejamento:** NOT_RUN. Evidências incrementais de S1a/S1b
estão nos relatórios próprios; nenhum aceite global é declarado por esta tabela.
Fixtures controladas são evidência visual, não prova de integração/produção.

S1b cobre cabeçalho/retorno nas quatro rotas de configuração; AC03 tem evidência
de foco e navegação, mas não aprovação de todos os bloqueios/recovery dos módulos.

| ID | Critério verificável | Evidência exigida na implementação |
| --- | --- | --- |
| AC01 | Cinco áreas e aliases existentes continuam abrindo o destino correto; recarregar, Back/Forward e link direto mantêm título/seleção coerentes | Regressão de navegação e percurso real |
| AC02 | Gestão conserva setup, clientes, alertas, impressoras e sessão; cada linha tem um único link, título compreensível e descrição específica quando útil | Inspeção de destinos, screenshot e teclado |
| AC03 | Abrir/voltar de configuração restaura área e foco na origem; confirmação bloqueante mantém contexto e impede saída indevida | Percurso positivo e negativo por rota tocada |
| AC04 | Layout usa tokens/primitives existentes e CSS gerencial escopado; ícones/tipos/raios/ritmo coerentes com uma superfície adjacente | Diff de estilos, inventário e comparação visual |
| AC05 | Ações utilitárias identificáveis e secundárias; status de rede não muda por estética nem some quando há risco | Nome acessível, leitura/reconexão/erro e captura |
| AC06 | Agora preserva alertas críticos e ação contextual antes de resumos; Operação mantém destinos e distingue informação indisponível de zero | Fixture com exceções, volume alto e erro parcial |
| AC07 | Financeiro preserva centavos, saldo, calendário, estados, permissões, reauth e recuperação; navegar não emite comando nem cria pagamento | Negativos e, se tocado fluxo financeiro, integração Django/PostgreSQL + review R3 |
| AC08 | Cardápio mantém criação única e edição existente, seleção/busca/draft e proteção contra polling; navegar não grava produto | Regressões editor/QuickCatalog e erro/busy |
| AC09 | Cada rota tocada cobre loading/vazio/erro/stale/revogação; mutações cobrem pending/timeout/readback sem segundo envio acidental | Matriz por rota e testes pertinentes, sem asserts enfraquecidos |
| AC10 | 360/390/430/1280 e zoom/fonte200% sem ação cortada/encoberta, scroll horizontal ou alvo <44px; foco e leitura lógica, ícones nomeados | Pixels e hit areas, teclado, axe e leitor de tela; limites manuais explícitos |
| AC11 | Comparação antes/depois usa mesmo fixture/estado/papel/viewport; testes focados, typecheck/build/lint e test:visual executados | Manifest por SHA, logs sanitizados e falhas históricas preservadas |
| AC12 | Cada slice tem diff restrito, review proporcional e evidência por critério; reversão da UI não muda dados; sem claim de ganho/produção não medido | Checklist de PR, estratégia de rollback e decisão qualificada |

## Aceite humano de UX

Após S1, percorrer encontrar impressoras, configurar alerta e retornar à Gestão.
Após S2–S4, percorrer abrir uma exceção, localizar revisão de fechamento e editar
um produto. Usar ambiente descartável para qualquer gravação. Registrar resultado,
obstáculos e opinião do avaliador sem publicar identidade/dados pessoais.
Tempo e número de ações só serão comparados se medidos no mesmo cenário.
Aceite visual não é homologação financeira, de hardware ou de estabelecimento.
