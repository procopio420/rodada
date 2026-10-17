# Correções de apresentação Compose — Spec033

Referência: PR212, `prototype/ux-2-0/index.html` em `ec26e26b164692b1e22e0fc1b7c7c45d401a7ca0`. Comparação anterior: PR231.

Delta de apresentação:

- Cardápio: referência de consumo em duas colunas (usado/referência e capacidade), legenda e projeção na mesma linha, perfil Regular e ação em âmbar. Mantidos valores canônicos e bloqueios existentes.
- Resumo: destino com acento lateral, total horizontal; editar configuração aparece somente quando produto aceita variantes/modificadores.
- Recebimento: caixa único aberto continua selecionado por seu ID canônico; seu metadado fica abaixo do valor e ações. Vários caixas ainda exigem seleção explícita. Terminal externo e condições ficam em divulgação secundária após as ações; avisos de simulação Pix aparecem quando relevantes.

Fixtures de apresentação: Marina/Mesa08, exposição56/limite200/draft14 com os mesmos oito produtos do protótipo; recebimento Marina/Mesa08/saldo24. ID da Tab é uma fixture explícita, não inferido da mesa. Capturas de teste Compose são isoladas e não provam shell, API ou liquidação real. Diferenças de referência canônica e indisponibilidade de PSP não estão implicitamente aprovadas.

Validação e capturas serão registradas após a execução. Sem aparelho físico, sem aceite global de paridade, sem merge/deploy.
