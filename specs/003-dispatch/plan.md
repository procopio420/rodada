# Plan — Spec 003

1. Zone + ServicePoint completos.
2. DispatchTask e fila operacional derivada de `READY`.
3. WebSocket/event feed.
4. UX de pico: fila de atenção sem exigir claim/pickup/delivery manual.
5. Modelo de FulfillmentMilestone com `source`, `confidence` e provenance.
6. Inferência P0 por contexto/tempo com semântica explícita de baixa confiança.
7. Adapter de sinais de presença; primeiro alvo é o passe/cozinha.
8. Inferência de `READY -> PICKED_UP` por presença/saída do passe.
9. Zone presence e inferência de deslocamento até o destino.
10. Correções por exceção e trilha de auditoria.
11. DeliveryRun manual/assistido por Zone.
12. métricas separando `MANUAL`, `INFERRED` e `CORRECTED`.
13. dashboard de pico e análise de qualidade da inferência.
