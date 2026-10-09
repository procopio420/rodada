# Aceite verificável

- A1: em Bar/Cozinha, fila e passe precedem catálogo no DOM e na tela; primeiro item/ação de fila normal visível sem scroll a 360×800. Quantidade e nome completos, target >=44 px.
- A2: snapshot normal/lotado mostra contadores de itens por região; erro inicial/carregamento não apresenta zero confirmado. Estados anteriores e revalidação permanecem.
- A3: em 768×1024, 1280×800 e 1440×900, produção e passe estão lado a lado; 360×800, 390×844, 430×932 não têm overflow. Axe e foco passam.
- A4: Gerência mostra exceções, inclusive comandas REQUIRES_ACTION, e pulso antes de Conta da Casa; Gestão ainda dá acesso a seus controles. Itens READY não contam como em preparo, e rótulos canônicos disponíveis estão em português.
- A5: nove superfícies Web têm imagens nos seis viewports, estados existentes e índice ignorado para antes/depois. Comparação equivalente de primitives permanece <=0,1%; não aceitar baseline para ocultar regressão.
- A6: typecheck/build/test:visual/test:integration passam. Integração usa Django/BFF reais e confirma estados, permissões e persistência; SQLite local não é evidência de concorrência PostgreSQL.
- A7: API/Web locais acessíveis e URLs documentadas; bloqueios PostgreSQL/Android explicitados se ausentes. Sem simular provider ou instalar UI Web no lugar do Android.
- A8: Cliente mantém ícone 58×58 px, conteúdo separado e preço legível em seis viewports, inclusive nomes longos/disabled. POS não permite selecionar item indisponível; disponibilidade retorna após reativação real na API.
