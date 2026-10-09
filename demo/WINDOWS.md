# Demo Windows — execução integrada

## Uso

Alternativa local a demo/compose.yaml para Windows sem Docker/WSL: PostgreSQL17 portátil, API ASGI, dispatcher e Web. Sem serviço global ou alteração da demo SQLite anterior. PostgreSQL/API/Web escutam loopback. Android emulator usa http://10.0.2.2:18764/. Celular físico/LAN não configurados.

Pré-requisitos: PostgreSQL17 binários oficiais, Python3.12+ com apps/api[dev], Node22+ com npm ci e build Web. Use ambiente Python próprio ao reproduzir. ZIP: https://www.enterprisedb.com/download-postgresql-binaries. Versão 17.11-3, SHA256 medido localmente 4b8db0930c38f6ef845db919551dedda3b6b845aeb0927b3d79a6e8e9e4537cf; não é assinatura do fornecedor.

Na raiz, scripts/demo-start-windows.ps1 exige -PgBin, -Python, -Node e -StateDirectory com caminhos absolutos. StateDirectory deve ficar fora de arquivos versionados, por exemplo visual-artifacts/demo-functional/runtime; não usar banco de operação real. Recusa portas ocupadas, preserva pgdata e registra PIDs/logs locais. Após falha parcial, inspecionar runtime.json antes de repetir. Não reiniciar PostgreSQL durante testes, mesmo em bancos diferentes da instância.

Web http://127.0.0.1:3119/staff; API http://127.0.0.1:18764/ready/; PostgreSQL porta55459/banco rodada_demo. Use somente identidades demonstrativas provisionadas por seed_release_demo/seed_demo. Acesso e PIN devem permanecer nas orientações locais, não nos novos artefatos publicados. Toda declaração de dinheiro/terminal é MANUAL_TEST.

## Roteiro

1. Login; abrir /cash e turno caso necessário.
2. /pos: criar TESTE, selecionar produtos disponíveis e confirmar respeitando limite operacional. release-demo contém fixtures QA e opções propositalmente indisponíveis. Catálogo bar-do-aderlan é mais simples, com limite VISITOR R$30.
3. /bar e /kitchen: localizar sua comanda, Aceitar → Preparar → Pronto por item.
4. Android da mesma Venue: acompanhar Agora e concluir entrega pelo fluxo existente.
5. /pos: receber parcial, esperar atualização e reconsultar conta antes do próximo recebimento. Ajustar conta oferece preview/PIN para desconto/serviço. Serviço é explícito, não automático; política release-demo foi habilitada em 10% somente para teste, via configuração existente.
6. Receber restante, conferir saldo zero e fechar. Histórico → Ver conta / recibos mostra documento não fiscal; prévia/PDF não comprova papel.
7. Conferir /manage, /reports e /cash. Tentativas TESTE anteriores e história permanecem; não apagar para obter sucesso.

## Repetição

Reusar scripts/demo-full-shift.py --evidence CAMINHO_LOCAL.json, --verify e demo/reconcile.sql read-only. Verificar report antes de outros turnos alterarem agregado. Nada de SQL para ajustar saldo. Banco exclusivo rodada_web_e2e para browser; suites API usam outros bancos de teste, nunca rodada_demo. Não publicar banco, runtime, traces de sessão ou logs não saneados.

## Parar/reiniciar

Conferir runtime.json e CommandLine antes de parar somente os PIDs API/dispatcher/Web desta execução. PostgreSQL: pg_ctl -D CAMINHO_PGDATA -m fast -w stop preserva história. Reiniciar com mesmo StateDirectory e portas livres. Sem apagar volumes ou forçar Git. A demo anterior 3000/8000 continua independente.

Relatório: docs/development/demo-windows-evidence-2026-10-09.md.

Configure POSTGRES_PASSWORD localmente antes do launcher. Não colocar esse valor em comandos/documentos publicados. O banco existente exige a mesma senha usada no initdb; a senha não é redefinida pelo launcher.
