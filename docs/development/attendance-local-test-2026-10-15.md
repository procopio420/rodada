# Atendimento — ambiente local e comparação Web/Android

Data: 2026-10-15. Branch `codex/ux-teste-mobile`, HEAD
`54c57808cec0098be2934faa964dd6dd9cd5b41d`.
Contrato: `specs/029-attendance-mobile-design/spec.md` e sua evidência Android.
Escopo: retomar serviços existentes e conferir o port instalado; sem alterar
comportamento, banco, catálogo, regras financeiras ou publicar código.

## Ambiente retomado

- Web: `http://127.0.0.1:3000/attendance`, Next dev em `apps/web`.
- API: ASGI/Uvicorn em `http://127.0.0.1:8000`, readiness HTTP 200.
- Dispatcher: `manage.py dispatch_realtime`, processo separado.
- PostgreSQL: cluster existente em
  `$env:LOCALAPPDATA/Temp/rodada-ux-main-20261014-local/pgdata`, porta 55460,
  banco `rodada_ux_review`, role local `rodada`; autenticação loopback trust
  preexistente, sem alteração de permissões ou leitura de senha.
- Android: AVD `rodada-pixel10-api36`, serial `emulator-5556`, app
  `com.rodada.attendance/.MainActivity`; `adb reverse tcp:8000 tcp:8000`.
- PIDs API/dispatcher desta retomada: arquivo local ignorado
  `visual-artifacts/android-native-port/runtime.json`. Verificar processos
  reais antes de reutilizar PIDs; não interromper outras sessões.
- Nenhum reset, seed, migration, pedido confirmado ou pagamento executado.
  O cluster auxiliar `frontend-pilot-postgres` iniciado na tentativa anterior
  foi encerrado. O cluster correto acima permanece ativo.

## Receita de retomada

Conferir primeiro listeners/processos para reutilizar serviços existentes. Não
iniciar uma segunda instância nas mesmas portas. A partir da raiz, usar os
binários locais `visual-artifacts/demo-functional/postgres/pgsql/bin/pg_ctl.exe`
e `.venv/Scripts/python.exe`. Se o cluster acima não existir, parar e investigar;
não criar outro banco nem substituir dados para simular continuidade.

Para um cluster parado, `pg_ctl -D <pgdata acima> -l <diretório pai>/postgres.log
-o "-h 127.0.0.1 -p 55460" -w start` preserva os dados existentes. O log deve
ficar fora de pgdata para evitar conflito de leitura durante recuperação.

Ambiente dos dois processos Python: `POSTGRES_DB=rodada_ux_review`,
`POSTGRES_USER=rodada`, `POSTGRES_HOST=127.0.0.1`, `POSTGRES_PORT=55460`,
`POSTGRES_PASSWORD` vazio, `DJANGO_SETTINGS_MODULE=rodada_api.settings`,
`DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,10.0.2.2`, `PYTHONUTF8=1`.
Em `apps/api`, executar `python -m uvicorn rodada_api.asgi:application --host
127.0.0.1 --port 8000 --no-access-log` e, separadamente,
`python manage.py dispatch_realtime`. Não usar launcher que execute seed/migrate.

Em `apps/web`, com `RODADA_API_BASE_URL=http://127.0.0.1:8000`, executar
`node node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port 3000`.
O Next altera automaticamente `apps/web/next-env.d.ts` para `.next/dev/types`.
Abrir o AVD existente pelo SDK em `visual-artifacts/native-tools/sdk`, restaurar
o reverse e iniciar a Activity; não limpar dados/reinstalar sem necessidade.

## Conferência executada

| Critério | Resultado observado |
| --- | --- |
| APK instalado | SHA256 igual ao APK e manifest validados ontem |
| Seis arquivos centrais do port | SHA256 igual ao manifest local anterior |
| Dados/contexto | Mesmas três mesas e mesma comanda da Mesa 2 nas duas interfaces |
| Fluxo principal | Mesas → comanda → Cardápio / Pedido atual / Conta → retorno executado |
| Produto/preço | Mesmo produto, quantidade 1 e rascunho de 400 centavos nos dois |
| Saldo canônico | Permaneceu zero na Conta apesar do rascunho de 400 centavos |
| Escritas de domínio | Nenhum pedido/pagamento confirmado; item de conferência removido do draft |
| Android ONLINE | Confirmado na UI com API local; não prova entrega SSE de evento mutável |
| A/B/A real somente leitura | `NativeDraftReadbackTest`, opt-in `readOnlyLocal=true`: OK (1 test), sem skip |

O teste A/B/A compara os pedidos canônicos antes/depois e verifica identidade,
configurações e isolamento dos drafts. Log local:
`visual-artifacts/android-native-port/review-read-only-drafts.log`.
Capturas reais Android: `port-tables.png`, `port-cart.png` no mesmo diretório.
O ensaio não reexecutou build/JVM/lint/suíte visual integral: nenhum código de
produto foi alterado e o APK/código conferidos correspondem ao manifest anterior.

## Divergências confirmadas

| Prioridade | Diferença | Evidência e consequência |
| --- | --- | --- |
| P1 | Navegação por categoria | Web oferece filtros, ordenação e mapeamento de apresentação em `apps/web/lib/client/attendance-catalog.ts:173`. Android usa categorias originais ordenadas alfabeticamente e lista contínua em `AttendanceScreen.kt:550` e `:618`. No mesmo contexto, Web inicia em Cervejas; Android em Bebidas. Buscar/selecionar existe nos dois, mas explorar o catálogo exige navegação diferente. |
| P2 | Identidade visual do produto | Android desenha fallback em `AttendanceCatalogCard.kt:37`, sem carregar assets publicados. Web suporta ProductIcon publicado. Limitação já prevista na spec; não é paridade visual completa. |
| P2 | Hierarquia visual | Android e Web usam cabeçalhos, espaçamentos, botões e apresentação da revisão distintos. Capturas reais mostram o mesmo significado e valores, sem igualdade de pixels. |
| Escopo | Conta e pagamentos | Atendimento Web contém aviso fixo de teste sem pagamentos em `attendance-web.tsx:150`; Android preserva Pagar, Ajustar conta e outras operações. Nenhuma cobrança foi acionada. Não remover recursos/guardrails para fabricar igualdade. |

Decisão: **GO para teste humano local do fluxo principal**; **paridade global
Web/Android não aprovada**. A afirmação de que o port estava inteiramente igual
era ampla demais. Preservar o fluxo/contextos/recovery já implementados.
Próximo trabalho para paridade do catálogo: definir aceite de categorias e assets
na Spec029 antes de implementar a adaptação nativa; comparar o mesmo estado nas
duas plataformas e manter testes de rascunho, disponibilidade e sessão.

Não verificados nesta rodada: confirmação real de pedido, pagamentos, eventos SSE
mutáveis, indisponibilidade/replay real, TalkBack, teclado ampliado, aparelho físico,
suíte Web integral, CI, homologação ou produção. Sem commit/push/merge/deploy.
