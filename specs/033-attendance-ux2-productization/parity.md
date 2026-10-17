# Matriz de paridade UX2

Contrato: PR212 `ec26e26b164692b1e22e0fc1b7c7c45d401a7ca0`.
Capturas locais ignoradas: `apps/web/visual-artifacts/033/reference/`.
Referência estática não prova integração. Resultados ficam PENDING até comparação
com jornada real e revisão no mesmo SHA. Capturas desktop excluem o texto lateral
de laboratório da superfície operacional: requer aprovação antes de aceite de diferença.

| Tela/estado | Protótipo | Web | Android | Diferenças atuais | Resultado |
|---|---|---|---|---|---|
| Agora/Atendimentos | now-service | Shell #221; conexão de ações contextuais em correção | Shell e readback exato; matriz nativa em execução | Integração/retorno e revisão de pixels completos | PENDING |
| Agora/Entregas | alternância nowMode | Fila separada #221; projeções #218/#222/#226 | Fila tipada; ownership depende #226 | Jornada READY/entrega e pares mesmos estados | PENDING |
| Mesas | tables | Página/tiles em #224 | Grade legada; novo recorte em implementação | Paridade Compose e regressões antigas | PENDING |
| Mesa multi-Tab | table-multi-tab | Contexto de página #224 | Diálogo legado; alvo canônico implementado | Layout Compose e Back | PENDING |
| Comanda | tab | Página/CTA/barra em #224 | Página fiel em implementação | Mesma jornada Web/Compose e fonte ampliada | PENDING |
| Cardápio/rascunho | catalog-draft | Lista/quantidade/envio direto #224 | Recorte nativo em implementação, motor reutilizado | Pixels/rascunho/foco/fontes por plataforma | PENDING |
| Resumo opcional | review | Página opcional #224; testes reais quatro larguras | Superfície legada ainda requer adaptação | Paridade e regressão completa | PENDING |
| Pedido confirmado | order-confirmed | #219/#224: ID/estação/estado reais persistentes | Motor existente; nova apresentação pendente | Evidência nativa pareada e reinício | PENDING |
| Mais uma rodada | repeat | Página #224 com zero para excluir e envio único | Editor existente; adaptação visual em curso | Paridade nativa e rascunho prévio | PENDING |
| Envio incerto/recovery | cenário lostACK | #224: POST commit/ACK perdido/reload/payload igual em PG | Stores026/029 reutilizados; piloto de recuperação pendente | Restart/forçar parada e matriz de falhas conjunta | PENDING |
| Conta/parcial/encerrar | jornadas settlement | #225: página manual CASH, recovery Payment/Close e readback | Pagamentos existentes; página fiel ainda pendente | Caixa canônico, métodos não homologados indisponíveis; diferenças sem aprovação | PENDING |
| Limite/perfil | creditbar compact | #224: compacto/expandido e projeção; nove testes em página real | Campo canônico de perfil omitido no parser; correção em implementação | ENFORCE atual até031; paridade Compose | PENDING |
| Liberação/limpeza | table release | #225: DIRTY→CLEANING→AVAILABLE; PG com atores/horários | Operações existentes; jornada visual conjunta pendente | Release/Guest e limpeza nativa no mesmo ensaio | PENDING |

Capturas de pagamento pareadas e versionadas em
[PR225 — evidências](https://github.com/procopio420/rodada/tree/impl/033-web-account/docs/development/evidence/spec033-payment).
Protótipo ec26e26b e Web05f5c25a, saldo2400,360/390/430/1280, fonte1x.
Manifest registra hashes e diferenças; são paridade parcial, não aceite visual.
Referências iniciais ignoradas acima são históricas e não substituem esse pacote.

Revisões financeiras independentes: código anterior e correção de fechamento
concorrente receberam NO_FINDINGS_WITH_GAPS, sem aprovação GitHub/piloto. Testes
adicionais reais Attendance cobrem selected=null/reload, storage da faseconfirmed,
Close503/ACK perdido e keepOpen após consumo concorrente/callback indisponível.
Suítes ainda não comprovam todos os aceites, estados e plataformas.

Diferenças exigidas por dados reais em avaliação: referência SIM substituída pelo
Order.id real; estação de OrderItem snapshot, jamais categoria; modo ENFORCE
atual, sem toggle WARN_ONLY antes031; dinheiro/terminal externo apenas após
recebimento observado, nenhum Pix/cartão fictício; sem rota/mapa otimizado fora033.
Nenhum épico concluído e nenhuma diferença intencional aprovada por esta matriz.
