# Critérios verificáveis

- A1: Arquivos originais e assets disponíveis como referência executável; fontes locais carregam offline.
- A2: Button principal equivalente ao `.btn` da Cozinha em 116×56px tem diferença <= 0,1% (mesmo browser/fontes/texto), sem editar baseline original para passar.
- A3: Desktop 1280px tem cabeçalho 72px e colunas 420/520/340; mobile 360/390/430 e tablet 768 não têm overflow, controles <44px ou violações WCAG AA.
- A4: Agregação usa IDs, quantidades corretas, exclui passe e mantém nomes longos. Ações continuam por OrderItem e erro pausa mutations.
- A5: API expõe Product/Order IDs somente dos itens confirmados do Venue autenticado; teste verifica projeção e isolamento.
- A6: Matriz visual das nove superfícies/estados, typecheck/build e integração real passam. Galeria distingue material, fixture e API real.
- A7: Revisão lista fidelidade medida e lacunas (Android, SLA, equipamento, dispatch e offline), sem afirmar paridade total sem evidência.
