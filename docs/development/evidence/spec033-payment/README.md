# Pagamento UX2 — comparação parcial

Protótipo ec26e26b, Web05f5c25a. Capturas reais do navegador em360/390/430/1280,
viewport844, fonte1x. No protótipo percorreu-se Mesas→08→Marina→Conta→Receber,
registrou-se somente na simulação parcial32 para obter saldo24 e reabriu-seReceber.
Web usa API mock para pixels determinísticos; os testes PostgreSQL separados
comprovam comportamento financeiro real. Não confundir as duas evidências.

| Tela/estado | Protótipo | Web | Android | Diferenças | Resultado |
|---|---|---|---|---|---|
| Receber24 integral | prototype-{width}.png | web-{width}.png | Pendente | Referência canônica, headerreal, Caixa aberto, Pix/cartão indisponíveis, retirada de simulação | Paridade parcial, não aceita |
| Fechamento concorrente com form aberto | Não simulado | Regressão UI PASS; Back preservado; zeroPaymentPOST | Pendente | Estado canônico adicional necessário | Funcional Web validado, não aceiteépico |

Os hashes e SHAs estão no manifest.json. As diferenças necessárias ao backend não
constituem aprovação visual implícita. Falta aceite explícito, mesmo estado no
Compose e fonte2x dessa página. Não marcar E04 concluído com estas capturas.
