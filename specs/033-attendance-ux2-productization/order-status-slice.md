# E02-02/03 — projeção e confirmação persistente Web

Contrato: PR216/spec033 `619c2718`, baseline PR a publicar, PR212 `ec26e26b`.
Escopo: expor snapshot de estação já persistido em OrderItem no readback existente;
cartão de último pedido confirmado no workspace usando ID/status/linhas históricos.
Sem nova intenção, endpoint, mutation, rota inferida de categoria ou ledger.

Antes: mensagem temporária genérica; histórico apenas na Conta; DTO omitindo
fulfillment_station_snapshot. Depois: confirmação continua visível ao abrir Tab,
mesmo após reload; produção por estação somente do readback canônico, com estado
desatualizado explícito. Valor desconhecido nunca significa READY.

Paridade do cartão segue order-status da PR212. A comanda completa e Compose
continuam pendentes: este slice não conclui E02/AC04 nem paridade global.
Referência SIM substituída pelo Order.id canônico completo, sem criar numeração
fictícia. A projeção aditiva preserva vazio legado como destino desconhecido.
Risco R2 (leitura/UI); testar snapshot histórico após mudança de catálogo e replay,
readback real, refresh/TabA/B e estados desconhecidos antes de recomendar integração.

## Evidência local — implementação 5c4eaef6

- PostgreSQL16 descartável exclusivo localhost55634:21 testes ordering foundation
  PASS; regressões novas falharam por campo ausente antes do patch e passaram
  após projeção. check e makemigrations --check PASS; sem migration.
- Web typecheck, build, auth4/4, tenant10/10 PASS.
- Playwright visual focado8/8 PASS em360/390/430/1280, incluindo dois cenários
  de resposta antiga reproduzidos na revisão e corrigidos por epoch de leitura.
- Revisão independente `/root/review_status_final` em5c4eaef6:
  NO_FINDINGS_WITH_GAPS, reproduziu8/8 PASS. Sem aprovação GitHub autenticada.
- Integração anterior21d886e9:11/11 PASS, incluindo4 jornadas reais de
  pedido2estações/reload e7 recovery staff/guest. Reexecução no5c4eaef6 em curso.
- Primeira reexecução não iniciou devido fixture residual(web-e2e já existente).
  DB exclusiva foi limpa com guard host/porta/nome; não houve escrita compartilhada.

Paridade observada: cartão usa geometria e cores da referência, mas tela da
comanda ainda é029(modal/categorias), diferente da página033. Resultado global
**PENDING**, sem alegação de paridadeE02. Capturas locais em
apps/web/visual-artifacts/033; aparelho físico eCompose fora deste slice.
