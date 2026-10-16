# Matriz de paridade UX2

Contrato: PR212 `ec26e26b164692b1e22e0fc1b7c7c45d401a7ca0`.
Capturas locais ignoradas: `apps/web/visual-artifacts/033/reference/`.
Referência estática não prova integração. Resultados ficam PENDING até comparação
com jornada real e revisão no mesmo SHA. Capturas desktop excluem o texto lateral
de laboratório da superfície operacional: requer aprovação antes de aceite de diferença.

| Tela/estado | Protótipo | Web | Android | Diferenças atuais | Resultado |
|---|---|---|---|---|---|
| Agora/Atendimentos | now-service | fila existente | Chamadas existente | Cabeçalho/nav/lista e destino task | PENDING |
| Agora/Entregas | alternância nowMode | lista existente | Prontos existente | Layout, estados e IDs/estação | PENDING |
| Mesas | tables | grade029 | grade029 | Medidas/tile/nav/header | PENDING |
| Mesa multi-Tab | table-multi-tab | diálogo029 | diálogo029 | Protótipo é contexto de página | PENDING |
| Comanda | tab | workspace029 | workspace029 | CTA/limite/status/hierarquia | PENDING |
| Cardápio/rascunho | catalog-draft | categorias/modais029 | categorias/modais029 | Referência usa lista/quantidades; adaptar fielmente | PENDING |
| Resumo opcional | review | Pedido atual existente | Pedido atual existente | Envio direto ainda ausente | PENDING |
| Pedido confirmado | order-confirmed | mensagem genérica | mensagem genérica | ID/estação/estado persistente | PENDING |
| Mais uma rodada | repeat | editor existente | editor existente | Layout e integração visual | PENDING |
| Envio incerto/recovery | cenário lostACK | intent existente | intent cifrada | Apresentação/resultados canônicos | PENDING |
| Conta/parcial/encerrar | jornadas settlement | BillSummary/POS | pagamentos nativos | Web companion exclui recebimento | PENDING |
| Limite/perfil | creditbar compact | DTO existente | DTO existente | Barra/projeção; ENFORCE até031 | PENDING |
| Liberação/limpeza | table release | mutations existentes | mutations existentes | Jornada visual/limpeza conforme missão | PENDING |

Diferenças exigidas por dados reais em avaliação: referência SIM substituída pelo
Order.id real; estação de OrderItem snapshot, jamais categoria; modo ENFORCE
atual, sem toggle WARN_ONLY antes031; dinheiro/terminal externo apenas após
recebimento observado, nenhum Pix/cartão fictício; sem rota/mapa otimizado fora033.
Nenhum épico concluído e nenhuma diferença intencional aprovada por esta matriz.
