# Quitação automática — evidência local

2026-10-17, branch codex/android-attendance-colors, base fb3ea55d; patch sem commit.

Ledger collect_payment e confirmação payment_provider chamam complete_paid_tab na transação, sob lock da Tab. Somente confirmação integral com preço/taxa válidos e sem pagamento pendente conclui. Auditoria tab.closed referencia Payment; webhook sem ator não impersona staff. Pagamento parcial, pendente ou taxa desatualizada mantém revisão aberta. Nenhuma ocupação liberada e produção confirmada preservada. API de listagem ativa e Android já filtram CLOSED; histórico é carregado sob demanda.

Validação executada em PostgreSQL descartável:
- 38 testes ledger/provider/concurrency PASS.
- 51 testes provider/tab operations/pricing: 49 PASS, dois cenários antigos de exceção pós-quitação precisaram preparar Tab reaberta. Os dois foram ajustados apenas na fixture e repetidos: 2 PASS. Não foi repetida integralmente a suite51 após essa mudança de fixture.
- Regressão real de taxa desatualizada altera bases por item mantendo total e confirma dinheiro sem fechar Tab: PASS na rodada51.
- Revisão independente R3: corrigido guard de taxa desatualizada; reavaliação sem novos achados. Revisão não executou testes e não constitui aprovação GitHub.
- git diff --check PASS, Django system check PASS. Sem alteração de schema/migration.

API local recarregada, ready200. Comanda de teste da captura foi fechada pelo botão normal Android após confirmar saldo zero; readback CLOSED, closed_at presente e um tab.closed. Nenhum novo pagamento registrado. Não há migração automática de outras Tabs antigas.

Não verificado: provedor real, perda real de resposta em dispositivo, aparelho físico e produção. Testes de provider são determinísticos; replay/concurrency locais não são homologação de fornecedor. Sem commit/push/merge/deploy. Próximo responsável: solicitante para aceite do fluxo local. Evidências de execução ignoradas em visual-artifacts/payment-completion-*.log.
