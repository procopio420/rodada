# Plano — Spec 024

1. Obter PDF exportado do Canva com consentimento de compartilhamento; inventariar todos os produtos visíveis.
2. Criar CSV estrito, confrontar nomes, preços e categorias com o estabelecimento e atribuir estação explicitamente.
3. Executar importador Django `import_catalog_csv` como preview sem persistência.
4. Após conferência, aplicar de maneira transacional e reexecutar para confirmar idempotência.
5. Conferir Atendimento Android, Bar/Cozinha, Guest e Gerência contra dados canônicos.
6. Tratar placeholders de seed ausentes do cardápio por configuração administrativa explícita; preservar histórico.
7. Executar tests e smoke em PostgreSQL. Registrar evidências e limitações.

Não alterar a lógica monetária nem o ciclo de pedidos nesta spec.
