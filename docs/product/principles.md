# Princípios de Produto

1. **Comanda é a unidade financeira.** Pedido pertence a uma Tab; mesa nunca substitui a comanda.
2. **Identity optional, Tab mandatory.** A comanda pode começar anônima e ganhar nome, perfil, sessão, QR ou NFC sem trocar de identidade financeira.
3. **Mesa não é identidade.** Uma mesa é contexto físico; uma ocupação pode ter várias comandas.
4. **Relacionamento antes de score.** A UX fala em conhecido, regular e da casa; não em score financeiro.
5. **Fricção proporcional ao risco.** Um regular não deve receber a mesma fricção de um visitante desconhecido.
6. **Cliente não precisa instalar app.** Guest ordering começa como PWA/web app instantânea.
7. **Login é opcional.** Um visitante deve conseguir consumir sem cadastro; perfil melhora continuidade e reconhecimento.
8. **CPF não é identidade básica.** Nome/apelido + contexto local deve bastar para começar.
9. **Múltiplas formas de acesso, uma só Tab.** Nome, Customer, guest session, código curto, QR e NFC resolvem a mesma entidade.
10. **QR de mesa identifica mesa, não conta.** Nunca expor IDs sequenciais como contrato público.
11. **Sessão guest é revogável.** Liberar/limpar a mesa invalida acessos da ocupação anterior.
12. **Staff mantém controle.** Guest ordering pode ser bloqueado sem bloquear pedidos do garçom/caixa.
13. **Limpeza é parte do giro.** Medir `DIRTY → CLEANING → AVAILABLE` como fluxo operacional.
14. **Parcial é normal.** Pagar parte não precisa encerrar a experiência.
15. **Pagamentos são ledger, não booleano.** Nunca modelar `paid=true` como verdade financeira suficiente.
16. **Exceções precisam ser fáceis, mas auditadas.** O bar continua humano.
17. **O sistema precisa sobreviver ao pico.** Operação degradada/offline/reconnect importa mais que feature bonita.
18. **Não virar ERP por reflexo.** Fiscal, estoque profundo, delivery e contabilidade precisam justificar a entrada no roadmap.
19. **O núcleo é nosso.** Rodada possui seu próprio PDV transacional; integrações não definem o domínio.
20. **Dispatch é produto.** Fila de trabalho, ownership, tempo e entrega são partes de primeira classe.
21. **Realtime não é fonte de verdade.** SSE atualiza as superfícies; PostgreSQL preserva consistência e HTTP confirma comandos.
22. **Medir o fluxo inteiro.** Pedido não termina quando é enviado: medir até ficar pronto, ser retirado, entregue e pago.
23. **Disponibilidade é operacional, não exclusão de catálogo.** “Acabou a fritas” não é o mesmo que desativar o produto administrativamente.
24. **Uma disponibilidade, todos os canais.** Cozinha/bar altera uma vez; staff, caixa e guest passam a respeitar a mesma verdade.
25. **Servidor decide se pode vender.** A UI pode esconder/desabilitar, mas a confirmação do pedido sempre revalida disponibilidade e preserva pedidos já confirmados.
26. **Medição não pode virar trabalho.** No happy path, o garçom não deve precisar tocar em “peguei”, “saí para entrega” ou “entreguei” só para alimentar telemetria. O sistema observa, infere e pede ação humana apenas para exceções ou correções.
27. **Inferência não é confirmação.** Todo marco inferido deve preservar origem, confiança e evidência suficiente para que métricas não tratem estimativa como fato confirmado.
