# Spec023 — configuração confirmada na fixture V03

A comparação V03 histórica fornecia nomes/quantidades/estados, mas nenhum
customization_snapshot. Depois do contrato de produção da Spec026, essas linhas
corretamente permanecem independentes. O export agrega por produto; portanto os
dados históricos não justificam comparar seu resumo agregado com linhas legadas.

Nesta revalidação, a fixture comum deve conter a configuração confirmada explícita
de cada linha: mesmo Product, estação, variante null, modificadores vazios e
instruções vazias. Preço test-only existente permanece fora do recorte. O adapter
troca somente a estação ao observar BAR. Não inventar fingerprint ou recibo de
comando e não habilitar mutations coletivas sem evidência canônica.

Aceite: resumo produz três grupos (Fritas4, Bolinho2, Calabresa2), enquanto a fila
conserva cinco Orders/seis OrderItems e cada ação individual. Teste de linhas
legadas continua separado e independente. Export/CSS/limiar0,1% ficam intactos;
metadata ilustrativa, cabeçalhos de conectividade e comandos diferentes permanecem
divergências explícitas. Essa correção da fixture não aprova paridade global.
