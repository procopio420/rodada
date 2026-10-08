# Spec 022 — Fidelidade ao material visual fornecido

## Intenção

Pedido explícito de 08/10/2026: reproduzir os cinco HTMLs fornecidos (Sistema, Cozinha, Uma noite no bar, Sem sinal e Modo pico). Eles são referências de apresentação; dados, ações simuladas e textos instrutivos exportados não são contratos de domínio. Esta spec substitui a restrição de identidade e o layout desktop de duas colunas da spec 021.

## Comportamento e regras

- O sistema compartilhado adota os neutros quentes, Archivo variável condensada, JetBrains Mono, botões papel/ink, badges retangulares e divisórias do material. Fontes são locais, com licença, sem dependência de Google Fonts em runtime.
- Cozinha desktop usa cabeçalho de 72px e três áreas: total por Product, itens em ordem cronológica e passe. Em 1280px, colunas 420 / restante / 340px. Bar usa a mesma linguagem e agregação. Mobile empilha as áreas sem cortar informação ou controles.
- Agregação usa Product ID, nunca aproximação de nomes. Soma somente itens ainda em preparo. Chips mostram as comandas reais. API retorna product_id e order_id como projeção aditiva; continua respeitando Venue e estados confirmados.
- PICKED_UP fica na seção Em entrega, separado do passe READY e da agregação de preparo. Sem identidade do responsável na projeção, mostrar apenas retirada registrada; não copiar o avatar/nome do mockup.
- Cada botão mantém a transição individual autorizada (Aceitar → Preparar → Pronto). Não implementar conclusão em lote nem pular estados para imitar o botão do mockup.
- Idade deriva do timestamp real: criação no preparo, ready_at no passe quando disponível. Não há SLA configurado nesta slice: sem medidor de meta, atraso inferido, equipamento, cliente ou responsável inventado.
- Cadastro/disponibilidade continuam acessíveis depois do painel principal. Falha de atualização mantém último snapshot e pausa mutations até recuperação.
- POS/Guest/Caixa/Gerência compartilham tipografia e controles. POS passa a reutilizar ProductIcon, inclusive no catálogo. Assets existentes continuam ligados ao Product; assets do material são referência, não atribuição automática por fuzzy matching.
- Dois assets fornecidos (Fritas/Brahma) são publicados estaticamente e atribuídos explicitamente aos Products somente no banco descartável da revisão local, com source PROVIDED_REFERENCE e auditoria. Nenhuma rotina de produção resolve nomes para assets ou substitui ícones existentes. UI aceita HTTPS e os caminhos locais restritos desse catálogo estático; HTTP fica restrito a loopback de revisão.
- Referências originais ficam versionadas em prototype/material-reference para inspeção/comparação, sem incluir seu runtime na aplicação.
- Offline/Pico e o roteiro são referências da superfície Android; esta slice não cria filas financeiras locais, sincronização fictícia, claims ou pagamentos simulados. Lacunas ficam explícitas na revisão.
- Android adota o tema compartilhado, fontes locais e filas planas de entregas/comandas. Agora mostra contagem real de entregas e abertura de comanda na navegação inferior, mantendo Mesas/Caixa acessíveis. Entrega usa a ação existente Entregue; não rotular como Pegar uma mutation que conclui entrega. Conexão não validada aparece em banner de atenção; não afirmar ações sincronizadas por contagem simulada. Mudança visual não altera repositories/intenções financeiras.
- Modo pico nativo é um filtro visual de Agora: mostra entregas reais em idade decrescente e mantém +Pedir/Contas acessíveis. Não cria atraso, chamados, lote/rodada ou claim. Desativar restaura a lista completa. Contagem sempre acompanha o snapshot e a conectividade existentes.

## Fora de escopo

Novo domínio de dispatch, SLA, inferência de entrega, queue offline genérica, provider financeiro, identidade fictícia, migração de atendimento nativo para web, geração de ícones em render e deployment.

## Aceite

Ver acceptance.md. Pixel perfect só pode ser declarado para regiões equivalentes efetivamente medidas; diferenças funcionais devem ser registradas.
