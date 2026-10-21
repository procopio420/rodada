# Manutenção — consulta inicial do catálogo

2026-10-20, branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`, alterações locais acumuladas, sem commit/push/publicação. Recorte R2 limitado ao GET inicial de CatalogCustomizationEditor; outros módulos fora do write set.

## Problema e correção

ESLint herdado apontava set-state-in-effect no loader chamado pelo efeito. Loader era usado somente no carregamento inicial. Substituído por consulta externa no efeito, atualização nos callbacks assíncronos e cleanup que ignora respostas após desmontagem, sem timer artificial/supressão. URL/query e mensagens de erro da API preservadas. Rejeição de transporte agora exibe mensagem explícita; antes ficava sem alerta. Select/command/save/availability intactos.

## Evidência executada

- Regressão network antes do código:1FAIL, sem mensagem esperada.
- ESLint do componente e teste:PASS. Build webpack/typecheck:PASS.
-26casos compostos:24regressões PASS e2novos FAIL por seletor de teste ambíguo (alerta do framework e alerta do produto). Escopo corrigido para main, sem enfraquecer mensagem/ausência de escrita/pageerror. Rerun somente dos2casos:2PASS4,1s.
-26casos distintos cobertos ao combinar as execuções; não declarar26PASS numa mesma execução. Regressões incluem quatro larguras, formulários, seleção e disponibilidade.
- Erro500 preserva mensagem da API; falha de rede mostra orientação de conexão/atualização, select mantém somente placeholder e não há formulário gravável, POST ou pageerror. API interceptada: não comprova integração real.
-2capturas de erro e hashes de fontes/imagens em [evidências](../../docs/development/evidence/spec034-catalog-read/). Inspecionada captura de rede390. Não houve alteração de layout.
- Lint dos seis módulos anteriormente afetados:6erros restantes, em pricing15,printing24,setup44,refunds55,house-account108/115. Catálogo deixou de constar. Contagem7→6, sem supressão.
- Revisão do autor R2, diffcheck PASS. Nenhuma revisão independente nova deste loader; revisão de UI anterior não cobre a mudança. Suíte global/integração real/manual não repetidas. NO-GO release/piloto permanece.

Próximo responsável: manutenção técnica em recorte próprio dos erros restantes, com testes e reviewR3 quando tocar auth/financeiro/dados/recovery. Padronização visual continua entregue, não reabrir redesign.
