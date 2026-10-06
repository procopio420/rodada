# Princípios de Produto

1. **Relacionamento antes de score.** A UX fala em conhecido, regular e da casa; não em score financeiro.
2. **Fricção proporcional ao risco.** Um regular não deve receber a mesma fricção de um visitante desconhecido.
3. **Cliente não precisa de app.** O MVP é staff-first.
4. **CPF não é identidade básica.** Nome/apelido + contexto local deve bastar para começar.
5. **Mesa não é identidade.** Conta pertence a pessoa/grupo; localização é contexto mutável.
6. **Parcial é normal.** Pagar parte não precisa encerrar a experiência.
7. **Pagamentos são ledger, não booleano.** Nunca modelar `paid=true` como verdade financeira suficiente.
8. **Exceções precisam ser fáceis, mas auditadas.** O bar continua humano.
9. **O sistema precisa sobreviver ao pico.** Operação degradada/offline/reconnect importa mais que feature bonita.
10. **Não virar ERP por reflexo.** Fiscal, estoque profundo, delivery e contabilidade precisam justificar a entrada no roadmap.
11. **O núcleo é nosso.** Rodada possui seu próprio PDV transacional; integrações não definem o domínio.
12. **Dispatch é produto.** Fila de trabalho, ownership, tempo e entrega são partes de primeira classe.
13. **Realtime não é fonte de verdade.** WebSocket acelera a operação; PostgreSQL preserva consistência.
14. **Medir o fluxo inteiro.** Pedido não termina quando é enviado: medir até ficar pronto, ser retirado, entregue e pago.
