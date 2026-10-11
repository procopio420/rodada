# Rodada — coesão e preparo do próximo teste

Recorte da Spec025 sobre `codex/ux-operational-polish`, após integração de main
`ddf889a`. O foco é terminar o núcleo operacional para um teste supervisionado.
Este documento complementa o diagnóstico de 10/10; não encerra outras specs.

## Pronto neste recorte

| Frente | Resultado utilizável |
|---|---|
| Gerência | Uma seção por vez: Agora, Operação, Vendas, Gestão e Mais. Agora prioriza exceções, comandas abertas e exposição. Informações auxiliares em Ver mais; links diretos e histórico voltar/avançar. |
| Cadastros | Cardápio/nomes e clientes em páginas próprias, com retorno à Gerência. Edição de nome usa a API existente e preserva os snapshots dos pedidos. |
| DEV | `/dev/staff`: listar/criar operador, alterar função, suspender, reativar e remover acesso. Nome/login/PIN/função são fornecidos pelo desenvolvedor. Remoção revoga sessões e conserva identidade/histórico; protege a própria conta e o último proprietário ativo. |
| Segurança DEV | Desabilitado por padrão no Web e API. Flag explícita, Venue da sessão, `staff.manage`, PIN recente, versão/conflitos e criação idempotente. PIN nunca retornado/auditado ou armazenado no navegador. |
| Novos testes | PDV esconde comandas encerradas por padrão; histórico permanece acessível. Nenhum operador fictício foi criado no banco da demo. |
| Cardápio local | Unidades legíveis (ex.: Brahma 600 ml), marcas/receitas/preços preservados. Itens QA e placeholders genéricos desativados. Bar e ambiente de desenvolvimento têm 143 produtos ativos do cardápio fotografado. |

As páginas atuais permitem testar pedidos internos e guest, indisponibilidade,
preparo no Bar/Cozinha, entrega, mesas, caixa, cobrança manual, conta da casa,
variações/adicionais, relatórios e recibos. Isso não comprova integração externa
ou uso físico no estabelecimento.

## Limpeza aplicada somente à demo local

- Backup completo PostgreSQL em `visual-artifacts/demo-functional/backups/2026-10-11-pilot-cleanup/`, formato custom, inventário legível e SHA256 conferido. Backup/manifesto ficam locais, fora do Git.
- 13 comandas antigas permanecem no histórico: três abertas foram encerradas; zero abertas após execução.
- 11 itens antigos e suas 11 tarefas pendentes foram cancelados com ator/motivo/timestamps, sem inventar entrega concluída. Filas operacionais vazias.
- Saldo restante de teste R$96,00 dispensado por ajustes `LOCAL_TEST_RESET`, sem registrar recebimento. Os 16 registros de Payment ficaram exatamente iguais.
- Sessões guest antigas revogadas; ocupações liberadas e mesas pelo ciclo canônico de limpeza. QR físico preservado, com geração de visita atualizada.
- 39 produtos existentes padronizados/desativados; 12 retirados da venda, incluindo seis QA e seis placeholders nos dois Venues. Preços e snapshots anteriores preservados.
- O usuário de desenvolvimento existente recebeu vínculo OWNER local no Bar do Aderlan, auditado; Ana/Bia conservaram funções e PINs.

O utilitário `scripts/reset-local-tests.py` exige flag DEV, banco local/porta
exatos, backup válido e manifesto sem novas comandas. Não existe endpoint de
reset público. Restauração do backup exige parar os serviços e revisar o destino;
não substituir um banco que já recebeu novos testes sem essa revisão.

## O que falta finalizar para o piloto, em ordem

| Prioridade | Tarefa objetiva | Quem / critério de conclusão |
|---|---|---|
| 1 | Confirmar cardápio fotografado: nomes duvidosos, preços, embalagens, BAR/KITCHEN e escolhas obrigatórias como batata/mandioca. | Erick com Aderlan; Lucas configura o contrato necessário. Pedidos têm opção e preço corretos, sem suposições. |
| 2 | Preparar equipe real, funções, mesas/zonas e caixas do estabelecimento. | Erick/Lucas. Cada operador entra e executa somente sua função; contas de ensaio não viram credenciais do cliente. |
| 3 | Fazer um turno supervisionado completo: abrir comanda, pedido interno/QR, indisponibilidade, preparo, entrega, parcial, fechamento, revisão de caixa e liberação de mesa. | Ambos, nos aparelhos previstos. Conferir saldo e filas na API após cada exceção relevante. |
| 4 | Completar contexto/navegação das chamadas: identificar Table/Occupancy/Tab canônicos, tratar várias comandas e localização liberada. | Lucas: referências autorizadas; Erick: ação de abrir o contexto correto. Nunca resolver pelo apelido da mesa. |
| 5 | Completar recovery após resultado financeiro ambíguo ou troca de sessão: consulta canônica e revisão auditada. | Lucas: contrato/reconciliação; Erick: interface. Nenhuma repetição de pagamento sem verificar o resultado anterior. |
| 6 | Publicar ambiente do piloto com HTTPS, verificar rede/aparelhos e preparar procedimento de suporte. | Ambos. Executar o turno no ambiente que o cliente usará, incluindo perda/retorno de conexão. |

Lucas publicou o [plano das quatro lacunas](four-track-gap-closure-plan-2026-10-11.md)
em `ddf889a`: recuperação, configuração segura de estações, fechamento diário
auditável e contingência de impressão. É planejamento, sem código novo nesse
commit. Para finalizar esses pacotes, seguir os aceites desse documento; não
confundir fechamento de uma gaveta com fechamento diário do estabelecimento.

## Problemas/limites que exigem atenção

- Recovery financeiro e contexto completo das chamadas continuam incompletos. A nova área DEV não fecha essas pendências.
- Criar operadores agora funciona na ferramenta local; provisionamento seguro no ambiente do cliente ainda exige definição operacional. Não habilitar a flag DEV publicamente.
- Configuração ampla de Venue/estações ainda não tem contrato completo. Não criar tela genérica de configuração antes da spec/API correspondente.
- DailyClose auditável de Venue e bloqueio seguro de mudança de estação têm lacunas próprias. Heartbeat KDS/AUTO_FALLBACK ainda precisa ser concluído e testado; deixar impressão automática de contingência desabilitada até esses gates.
- Há recibo/PDF e fluxos de registro manual, mas maquininhas, provider, impressora física, NFC/sensores e jornadas Android em aparelhos reais exigem validação própria. Não impedir o ensaio básico conectado por essas integrações.
- Relatórios conservam fatos financeiros antigos do ensaio; limpeza de filas não transforma o banco em histórico comercial real. Ajustes de teste são identificados, não pagamentos.
- Padronização do CSV não muda receitas nem homologa preços. O seed reconhece apenas a grafia antiga exata de unidades; duas identidades com as duas grafias exigem revisão, sem mesclagem automática.

## Uso local

Gerência `http://127.0.0.1:3119/manage`; equipe DEV
`http://127.0.0.1:3119/dev/staff`; cardápio em `/manage/products`.
Usar o operador de desenvolvimento existente no Venue desejado. Confirmar as
alterações de equipe com o PIN do operador autenticado, não com o PIN novo.
No iniciador Windows, `-DeveloperTools` habilita explicitamente Web/API;
sem esse parâmetro a ferramenta permanece desabilitada.

## Evidências

Código validado: API `273fc83`, Web `2d932b3`, integrado ao plano do Lucas `ddf889a`.
- Build/TypeScript: aprovados; Django check e migrations: sem alterações pendentes.
- API/PostgreSQL: **36 testes passaram** (equipe/autorizações, limpeza e seed/CSV).
- Web visual completo: **209 passaram**, incluindo 360/390/430, navegação/histórico,
  resposta perdida DEV, nomes longos, contraste e falha de transporte na edição.
- Integração Web/API/PostgreSQL: **15 jornadas passaram**; operador criado fez login,
  papel mudou, remoção revogou sessão; pedidos/caixa/estornos/recibos preservados.
- Web com DEV desabilitado por padrão: status false, página404 e gateway403.
- Após reinício da demo: releitura verificou zero comandas/filas abertas e os 16
  Payments exatamente iguais ao inventário anterior. Backup PGDMP e índice legíveis.

Na máquina Windows foi usado o CLI Playwright do projeto (`node
node_modules/@playwright/test/cli.js test`), equivalente ao script
`npm run test:visual`; integração acrescenta `--config playwright.integration.config.ts`.
Logs locais: `visual-artifacts/demo-functional/runtime/pilot-{api,visual,integration}.log`.
Capturas/relatórios ficam em `visual-artifacts/` e `apps/web/playwright-report/`.
Sem alteração de baseline/tolerância, sem merge na main ou deploy nesta entrega.
