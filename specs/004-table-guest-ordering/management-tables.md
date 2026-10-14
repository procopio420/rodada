# Gerência / Gestão / Mesas

Tela mobile-first em /manage/tables, acessível por Gestão. Permite configurar a quantidade de mesas para trabalhar, adicionar mesa identificada e retirar/reativar individualmente. Mostra total cadastrado, em uso, ocupadas (ocupação ativa), disponíveis e quantidade de comandas abertas por mesa. OPEN, REQUIRES_ACTION e SETTLING são abertas; CLOSED/CANCELLED não entram. Uma mesa ocupada com zero comandas continua ocupada.

Retirar significa OUT_OF_SERVICE, nunca apagar mesa, QR, vínculos, histórico ou contas. Apenas AVAILABLE sem ocupação ativa pode ser retirada; DIRTY/CLEANING/OCCUPIED são bloqueadas pelo backend. Reativação retorna AVAILABLE. Mudanças registram ator, horário e estados, incrementando access_generation. Quantidade-alvo inteira 0–500; redução requer IDs explicitamente selecionados e confirmação. Adição reutiliza mesas retiradas antes de cadastrar Mesa NN; nomes existentes são preservados. Novo cadastro mantém QR ordering DISABLED. Todas as mutations exigem venue.configure, isolamento Venue e transação/locks. Quantidade compara contagem esperada; estado individual compara estado esperado. Retry de alvo já satisfeito não cria duplicatas. Timeout não confirma sucesso: reconsultar estado; nenhuma repetição automática de cadastro por nome.

Estados: carregando, lista vazia, erro sem inventar zero, atualização indisponível conserva projeção e bloqueia edição, mutation em andamento impede dupla ação, resultado incerto exige conferência. Busca local por mesa, detalhes expansíveis com comandas; link de retorno a Gestão. Atualização periódica de leitura, sem mutations automáticas.

Fora de escopo: exclusão física, fechar/transferir comandas, liberar ocupação, limpeza automática, financeiro, QR público novo ou impressão.

Aceite: quantidade aumenta/reduz com seleção; ocupação e limpeza impedem redução; cross-Venue/STAFF rejeitados; replay não duplica; corrida ocupar/retirar mantém invariantes em PostgreSQL; contagem é da ocupação ativa; mobile 360/390/430, foco e alvos de 44 px.
