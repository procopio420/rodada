# Preparação da conferência manual —2026-10-21

Branch codex/management-ux-alerts, baseHEAD860b25d93da486d2416c6ddaccfdccd9605f8953. Nenhum código deproduto alterado nesta etapa;semcommit/push/merge/deploy.

## Runtime observado

Serviços inicialmente parados. Cluster correto retomado conforme docs/development/attendance-local-test-2026-10-15.md; banco existente rodada_local_sync_20261019 confirmado por consulta de metadados,porta55460,rolelocalrodada. Uma tentativa inicial iniciou cluster auxiliar frontend-pilot-postgres;role não correspondia, então esse processo próprio foi encerrado antes da retomada correta. Sem seed/reset/migration ou alteração de catálogo/dinheiro/permissões.

API do checkout principal em apps/api:Uvicorn127.0.0.1:8000,sessão97838,PID29988;dispatcher separado sessão66229. Web deste worktree apps/web:Nextdevwebpack127.0.0.1:3001,sessão27690. Revalidar processos antes de reutilizarIDs. Ambiente API usaPOSTGRES_DB=rodada_local_sync_20261019,POSTGRES_USER=rodada,POSTGRES_HOST=127.0.0.1,POSTGRES_PORT=55460,POSTGRES_PASSWORD vazio para trustloopbackpreexistente,DJANGO_SETTINGS_MODULE=rodada_api.settings;WebRODADA_API_BASE_URL=http://127.0.0.1:8000. Não criar chaves ou inferir credenciais.

HTTP observado:API/ready/200 (banco pronto);Web/manage/customers200 e/manage200;BFF/api/venue/context200;/api/auth/me401 em requisição semcookie,como esperado. Tentativa de rota/health/ready retornou404;rota correta/ready/confirmada no código. HTTP200 não prova autenticação nem carregamento das listas de negócio.

Não houve inspeção manual autenticada nova nesta etapa:automação do navegador havia sido bloqueada pela política da ferramenta,sem contorno por outra superfície. Usuário pode conferir no navegador já aberto usando sessão própria;se expirada,login normal/staff. Não pedir nem armazenarPIN.

## Roteiro proposto ao operador

1.Clientes/manage/customers:busca,leitura de limites/histórico e comportamento do voltar;evitar salvar alterações apenas para inspeção.
2.Gestão/manage#gestao:navegação e retorno contextual;mobile e desktop.
3.Impressão/manage/printing:hierarquia,destinos e trabalhos;sem disparar reimpressão real por testevisual.
4.Configuração/manage/setup:mesas,equipe e estado deAtendimentopelasmesas;sem ativar/desativar ou criar dados apenas para inspeção.

Registrar aprovação/achados reais quando houver retorno do operador. Leitor de tela,zoomnativo/dispositivo,integraçãoreal,CI e reviewautenticado pendentes;NO-GOrelease/piloto. Testes296PASS e lint0 da etapa anterior permanecem evidência automatizada separada.
