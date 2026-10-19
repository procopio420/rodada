# Comparação UX2 — resultado observado

**Não há paridade exata aprovada.** Comparação feita com capturas do navegador do protótipo original, Web executável e capturas Compose identificadas por SHA. Nenhuma imagem foi redesenhada. Abra [o comparador lado a lado](index.html).

## Diferenças comprovadas

| Tela/estado | Protótipo | Web | Android | Diferenças | Resultado |
|---|---|---|---|---|---|
| Comanda | Marina56; histórico fictício | Mesmo cabeçalho/título/ações; fixture sem histórico canônico | Fixture histórica fa1a859f, sem shell | Histórico/estado não equivalentes impedem aceitar comparação funcional; espaçamento do saldo e separadores divergem | Parcial |
| Cardápio com1Chopp | 8produtos; draft14; limite200 | Mesmos produtos/valores | Fixture Água2; outra exposição/limite | Web adiciona aviso persistente acima do limite; a barra e os textos mudam de colunas para linhas, deslocando busca/lista. Native também reorganiza valores/perfil e usa outro tamanho de moeda | Diverge |
| Resumo opcional | 1Chopp14 | Mesmo item/valor | Fixture Água2 | Web mantém aviso de seleção e adiciona Editar/Descartar. Native usa cartão arredondado para destino, total em bloco vertical e outro espaçamento; falta shell na fixture | Diverge |
| Repetir rodada | 2Chopp+1Batata | Fixture Fritas; captura após interação com scroll interno | Editor nativo ainda sem par comparável neste pacote | Dados/scroll diferentes: não avaliar posição do título nem aceitar equivalência pela captura | Não comparável |
| Receber24 | Layout original pareado | Saldo e hierarquia próximos | E04 captura512b7edc: Ana24, semmesa, semshell | Caixa real acrescenta linha e desloca valor/CTA; Pix/Cartão indisponíveis; textos e referência canônica distintos. Android acrescenta explicação de capabilities, botão de terminal externo e seleção de caixa acima do valor, ampliando bastante a rolagem. Diferenças reais documentadas, não aprovadas implicitamente | Parcial/diverge |
| Agora/Mesas/Mesa/Conta | Referências novas nas4larguras | Pacote ainda sem capturas pareadas atuais desses estados | Pacote ainda sem MainActivity pareada | Falta evidência equivalente; não inferir paridade de testes | Pendente |
| Fonte2× | Referência específica ainda não alinhada | Não capturado neste recorte novo | Fixtures disponíveis em3larguras | Sem referência equivalente não há aceite de paridade em fonte ampliada | Pendente |

## Correções prioritárias de UX

1. Remover ou reposicionar feedback persistente de seleção para preservar a hierarquia e posição aprovadas no cardápio/resumo.
2. Ajustar a barra de limite para manter a mesma composição, tipografia e alinhamento nas mesmas larguras.
3. Alinhar cartão de destino, total, espaçamentos e ações do resumo Compose; comparar dentro do aplicativo completo.
4. Decidir a apresentação das ações reais adicionais (Caixa, editar/descartar, terminal externo) sem declarar aprovação por necessidade técnica.
5. Repetir rodada e demais filas/mesas precisam de mesma identidade, dados e scroll antes de qualquer aceite.

## Limites da comparação

Protótipo capturado novamente em360/390/430/1280, com navegação real pelas telas relevantes. Web de cardápio/resumo usa read models controlados com os mesmos8produtos/valores, não backend financeiro. Capturas Compose de Comanda/Cardápio/Resumo são históricas fa1a859f. Recebimento390 é512b7edc, fixture Ana24/semmesa e semshell; mesma quantia do par24, mas não mesma jornada/identidade. Valores divergentes de fixture não são classificados como bug financeiro. Capturas de pagamento preservam referência pareada24. Manifest contém SHAs, limites e hashes. Este pacote não substitui E2E PostgreSQL nem revisão R3 e não concede aceite de épico, GO ou homologação.
