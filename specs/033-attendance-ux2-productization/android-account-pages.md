# E04 Android — implementação incremental

Contrato: Spec033 E04-02..07 e protótipo PR212, páginas Conta e Recebimento.
Reutilizar Payment CASH/terminal externo, ledger, close e armazenamento cifrado.
Adicionar sequência durável com ID de Payment confirmado antes de Close, readback
entre operações e recuperação sem repetir recebimento confirmado. Campos opcionais
preservam envelopes antigos. Parcial mantém OPEN; fechamento não libera ocupação.
Pix segue a capability canônica; cartão não homologado permanece indisponível. Terminal
externo exige confirmação humana prévia e mantém o contrato canônico existente.

Gates pendentes: testes de falha/reinício/concorrência, R3 independente, comparação
360/390/430 dp e fontes ampliadas, dispositivo físico e homologação externa.
Nenhum critério integralmente aceito por este documento.

## Implementação parcial e revisão

- `3a3e17ce`: sequência real extraída em `settleReceipt`, reaproveitando operações
  existentes; checkpoint confirmado persistido antes de Close. `StartPayment` antigo
  permanece legível e não solicita fechamento automático.
- `8f831cc5`: páginas nativas substituem apresentação genérica da Conta/recebimento;
  draft continua fora do saldo, estados vêm de Tab/Payment canônicos.
- Revisão independente preliminar encontrou lacunas de validação do readback:
  `082b403b` exige ID/valor/método/CONFIRMED/não simulado; `076ba9ff` valida Tab,
  CLOSED e saldo zero antes de publicar o estado. Revisão final ainda pendente.
- Funcionalidades preexistentes de correção, restituição, precificação e operações
  da Tab continuam acessíveis nos detalhes (`0e5a5f4c`).
- CASH exige caixa com turno ativo; registro de terminal externo confirma apenas
  informação manual observada, sem disparar PSP. Pix segue capability canônica; SDK de cartão aguarda homologação. Sandbox Pix e
  Tap debug permanecem explicitamente marcados SIMULAÇÃO, sem afirmar dinheiro recebido. Essas diferenças operacionais
  frente ao protótipo devem ser explicitamente aprovadas no gate de paridade.
- Testes novos cobrem orchestration JVM e instrumentação opt-in com Django/PG real,
  mas sua existência não comprova execução. Resultados finais serão registrados
  após os processos terminarem e sempre associados ao SHA efetivamente compilado.
