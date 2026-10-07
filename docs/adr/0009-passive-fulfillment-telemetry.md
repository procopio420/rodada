# ADR 0009 — Telemetria passiva de retirada e entrega

**Status:** Accepted for product direction  
**Date:** 2026-10-06

## Contexto

O modelo de fulfillment precisa medir `READY -> PICKED_UP -> DELIVERED`, mas exigir que o garçom confirme cada transição adiciona fricção exatamente no horário de pico.

Esse desenho cria dois problemas:

1. o funcionário trabalha para alimentar o sistema;
2. a métrica parece precisa, mas depende de cliques esquecidos/atrasados e pode ser pior que uma boa estimativa.

## Decisão

Rodada adota **telemetria passiva com correção por exceção**.

- `READY` continua sendo um evento explícito da estação de preparo.
- `PICKED_UP` e `DELIVERED` podem ser inferidos.
- O happy path não exige confirmação manual do garçom.
- Todo milestone preserva proveniência e, quando inferido, `confidence`.
- Ação humana corrige exceções; não confirma repetidamente que o normal aconteceu.

O sistema pode combinar tempo, contexto de task/run e sinais opcionais de presença.

A primeira integração física preferida é BLE no passe/cozinha, seguida por presença por Zone. Beacon/tag por mesa é opcional e só entra quando o ganho de precisão justificar manutenção.

## Modelo conceitual

```text
FulfillmentMilestone
  order_item_id
  kind: PICKED_UP | DELIVERED
  occurred_at
  source: MANUAL | INFERRED | CORRECTED
  confidence?        # obrigatório para INFERRED
  staff_member_id?
  inference_version?
  evidence_summary?
  supersedes_id?
```

O milestone é o registro auditável da observação/decisão. `OrderItem.state` continua útil para operação, mas uma transição automática deve ser rastreável até seu milestone.

## Consequências

### Positivas

- menos taps no pico;
- telemetria mais honesta;
- possibilidade de medir gargalo do passe e deslocamento;
- hardware pode melhorar precisão sem virar dependência do PDV;
- correções ajudam a calibrar regras futuras.

### Trade-offs

- eventos inferidos possuem incerteza;
- BLE exige calibração por ambiente/dispositivo;
- precisão por mesa custa mais operação de hardware;
- dashboards precisam distinguir confirmado de inferido.

## Guardrails

- sem GPS indoor como requisito;
- sem tracking preciso/contínuo como requisito;
- sem câmeras/visão computacional para identificar pessoas neste slice;
- sem transformar telemetria em ranking individual de funcionário sem spec própria;
- sinais brutos devem ter retenção mínima necessária;
- falha do sensor nunca bloqueia o serviço.

## Alternativas rejeitadas

### Botão obrigatório “peguei” + “entreguei”

Rejeitado por criar fricção operacional e gerar timestamps artificiais quando o clique ocorre atrasado.

### Não medir retirada/entrega

Rejeitado porque perde informação essencial para entender gargalo do passe e qualidade do atendimento.

### Beacon em toda mesa desde o início

Rejeitado como requisito inicial. A estratégia começa por passe e Zones; precisão por mesa é incremental.
