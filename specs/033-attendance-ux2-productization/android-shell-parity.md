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

Gate aberto: capturas matched360/390/430, revisão independente, CI e comparação
tríplice com o mesmo backend. Não aceita épico/AC global, piloto ou dispositivo.
