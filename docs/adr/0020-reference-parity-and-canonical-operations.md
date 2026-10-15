# ADR0020 — Referência visual e operações canônicas

Status: aceito para a integração das Specs023/024; não aprova paridade integral.

## Contexto

O export da Cozinha contém resumo por produto, informações ilustrativas de cliente,
SLA e comandos coletivos que não correspondem ao contrato operacional vigente.
Itens legados sem configuração confirmada não podem ser agregados por nome.
O snapshot confirmado distingue produto, estação, variante, modificadores e notas.

## Decisão

Usar a fixture comum V03 com snapshots explícitos equivalentes para comparar as
mesmas quantidades/configurações. Manter separado o teste de itens legados, sem
snapshot. Conservar ações individuais e comandos coletivos exclusivamente quando
há evidência canônica do lote/configuração previsto pela Spec026.

Preservar no produto conectividade real, destinos conhecidos e dados auditáveis.
Não criar cliente, recibo, SLA, telemetria ou comando para reproduzir conteúdo
ilustrativo. Preservar o export literal, fontes, CSS e gate integral de0,1%.
Adaptações para fonte200%, teclado e toque seguem os contratos acessíveis já
documentados; não constituem igualdade HTML↔Compose.

## Consequências e aceite

Os contratos dos exports e as comparações de controles equivalentes podem passar
enquanto a composição integral falha. A medição atual V03 é11,7785%, superior ao
limite0,1%; esse gate permanece FAIL. Header3,2357%, resumo13,0527%,
tickets16,1446%, passe6,7094%. Dados equivalentes e capturas repetidas estáveis
não tornam o layout equivalente. A tentativa anterior de tipografia foi descartada
por piorar o resultado; não se reaplica como correção presumida.

A conclusão visual integral requer referência executável compatível com os
contratos de produto ou uma nova spec que aprove mudanças reais de comportamento.
Este ADR registra a prioridade do domínio e a divergência, sem elevar tolerâncias,
aprovar baseline ou marcar023 global concluída.
