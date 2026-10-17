# E04 Android — implementação incremental

Contrato: Spec033 E04-02..07 e protótipo PR212, páginas Conta e Recebimento.
Reutilizar Payment CASH/terminal externo, ledger, close e armazenamento cifrado.
Adicionar sequência durável com ID de Payment confirmado antes de Close, readback
entre operações e recuperação sem repetir recebimento confirmado. Campos opcionais
preservam envelopes antigos. Parcial mantém OPEN; fechamento não libera ocupação.
Pix e cartão não homologados permanecem indisponíveis nesta apresentação. Terminal
externo exige confirmação humana prévia e mantém o contrato canônico existente.

Gates pendentes: testes de falha/reinício/concorrência, R3 independente, comparação
360/390/430 dp e fontes ampliadas, dispositivo físico e homologação externa.
Nenhum critério integralmente aceito por este documento.
