# Spec 021 — Integração dos protótipos da noite

## Objetivo e comportamento
Integrar os cinco exports ZIP em `prototype/` como referências executáveis e rastreáveis; incorporar sua linguagem visual ao sistema compartilhado e à aplicação Web conectada. A KB é a documentação versionada em `docs/`.

- Preservar ZIPs originais, extrair cada export com assets/runtime locais e oferecer índice navegável separado da referência legada.
- Paleta quente, ações primárias papel creme, atenção âmbar, estados textuais, relacionamento madeira e dinheiro violeta; tokens iguais no Web e protótipo legado.
- Atendimento Android recebe RodadaTheme com paleta escura compartilhada, fontes locais e raios 4/8 px; mantém fluxos nativos existentes.
- Archivo variável para texto/títulos, JetBrains Mono para relógios/quantidades, fontes locais sem dependência de rede no render.
- Cozinha/Bar priorizam resumo das quantidades em produção, fila individual e passe antes de disponibilidade/cadastro. Desktop usa três colunas operacionais; mobile empilha sem cortar nomes/ações.
- Resumo inclui somente NEW/ACCEPTED/PREPARING; READY/PICKED_UP/DELIVERED/CANCELLED não compõem quantidades a preparar. Resumo é somente leitura. Cada mudança continua individual e usa a transição canônica já existente; sem confirmação em lote ou salto NEW → READY.
- Relógio de produção usa created_at; passe usa ready_at. Sem ready_at, exibir “Tempo não informado”, nunca inventar idade do passe. Falha preserva snapshot e pausa ações, com aviso explícito.

## Regras e decisões de integração
Specs de domínio prevalecem sobre simulações. Offline não confirma pedido/pagamento; retorno da rede só representa sincronização após confirmação canônica. Pegar/Entregue nos demos não introduzem taps obrigatórios. Limites e tempos de alerta dos demos são exemplos, não configuração do Venue. Assets de exemplo não são associados automaticamente a Products ou Customers reais.

## Fora de escopo
Portar o runtime exportado para produção; substituir Atendimento nativo por Web; novo ledger, filas offline, bulk mutations, regras financeiras, thresholds de SLA ou telemetria inferida. O fluxo interativo completo permanece referência navegável; funcionalidades futuras continuam nas specs 002/003/014.

## Critérios de aceite
Ver [acceptance.md](acceptance.md).
