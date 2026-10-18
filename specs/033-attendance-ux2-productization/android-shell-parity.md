# E01/E04/E06 — Shell nativo real e retorno contextual

Delta sobre PR234: Mesa e Comanda deixam de ser diálogos; o cabeçalho real do
Atendimento permanece na jornada. Mesas segue hierarquia Encontrar destino,
busca e comandas sem mesa visíveis. Mesa conserva seleção explícita por ID,
comandas da ocupação, saldo projetado canônico quando disponível, saída do grupo
e abertura contextual. Gestão adicional permanece em Opções da mesa; essa
extensão operacional requer aceite, não equivale à paridade global aprovada.

DIRTY apresenta Iniciar limpeza; somente CLEANING disponibiliza a mesa.
Antes o early return chamava conclusão diretamente para os dois estados.
Back/context/draft permanecem nos state holders existentes; nenhuma alteração
nos motores de pedido, pagamento, auth ou idempotência.

Fixture reprodutível local isolada: scripts/spec033-native-shell-fixture.py.
Tenant próprio, oito produtos, Marina/Mesa08, limite200 e pedido canônico56
confirmado pelo serviço de domínio; rascunho14 criado pela própria UI.
LiveAgoraUx2Test usa MainActivity, login e repositórios reais (opt-in).

Revisão R3 root encontrou descarte da localização canônica em target TAB;
corrigido bebcd273 preservando tableId/occupancyId/generation opcionais e
validando a ocupação vigente. Label nunca seleciona destino. READY de Tab
financeiramente encerrada continua impedindo liberação visual até resolução;
Ver entregas prontas apenas navega à fila, sem assumir/concluir a tarefa.
Uma entrega que chega com diálogo de liberação aberto desabilita confirmação.

Primeira jornada MainActivity real passou 360/390/430; evidência final sobre
bebcd273 passou117JVM/build/lint,12Compose e3jornadasAPI(360/390/430).
Gate aberto: revisão final dos resultados, CI e comparação
tríplice com o mesmo backend. Não aceita épico/AC global, piloto ou dispositivo.
