# Fluxo — Pagamento Parcial

Exemplo:

```text
Consumo confirmado: R$ 178
Pagamentos:         R$   0
Exposição:          R$ 178
Limite:             R$ 150
```

Sistema marca a conta como `REQUIRES_ACTION`.

Funcionário recebe R$ 100 por Pix/dinheiro/cartão e registra/confirma.

```text
Consumo:            R$ 178
Pagamentos:         R$ 100
Exposição:          R$  78
```

A mesma tab continua aberta.

Não existe necessidade de fechar e reabrir a conta.
