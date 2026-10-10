# Spec023 — estorno nativo e gates finais10/10/2026

Recorte independente na branch isolada codex/spec023-next, main45c4742, PR68. Contratos em spec/plano/tasks/aceite antes do código. Não importa PR61/69/70, não merge/deploy. Referências e tolerâncias originais preservadas.

## Diferença e correção

RefundDialog real360/font200 cortava advertência e PIN, com decisões sobrepostas: [baseline falho e screenshot](evidence/spec023-refund/before). Componente aplica o mesmo padrão já aprovado em PaymentDialog: conteúdo rolável, decisões verticais quando fonte>1.3, Cancelar≥44dp. Fonte normal conserva footer horizontal. Command, flagsvalid/busy, autorização/PIN, motivo trim, caixa e idempotency key conservados. Nenhuma mudança API/ledger.

[Checks estruturados](evidence/spec023-refund/checks.json): 51unit, build/lint;9 testes instrumentados×6=54, zero skips/failures/errors. API36, density160,360/390/430×844/fontes100/200%, IME real. Teste do estorno exige valor300centavos, pagamento original/ponto, motivo trim, PIN recebido no callback e limpo após submit, confirmação bloqueada sem PIN e idempotency key estável ao repetir o mesmo comando. Fixture somente androidTest; screenshot antes de digitar PIN. Capturas repetidas exigem bytes idênticos sem máscaras/tolerância.

[Revisão de tickets](spec023-tickets-review.md): candidata descartada por piorar a diferença integral. Código de apresentação Web preservado. Gates Web finais types/build12auth/realtime197visuais13PostgreSQL aprovados. Testes de permissões agora exigem ambos avisos; recibo aguarda resposta final depois do308 antes de verificar expiração/ausência do documento. Tentativas de integração conservadas em bancos próprios55523, sem reset/drop. Serviços anteriores encontrados parados; apenas cluster próprio/API8144/dispatcher foram abertos, banco demonstrativo55459 intocado.

## Reprodução

Runtime Android e emulador separado rodada-v05-api36, serialemulator-5572, density160/font1ou2/w×844/show_ime_with_hard_keyboard1; scripts/android-navigation-check.ps1 exige9casos atuais e remove somente XML gerado antigo. Para UI real: build API10.0.2.2:8144, servidor com DJANGO_ALLOWED_HOSTS incluindo10.0.2.2, PostgreSQL55523/rodada_demo e dispatcher. O primeiro login recebeuHTML por variável ALLOWED_HOSTS errada no servidor de teste; corrigido para o nome existente DJANGO_ALLOWED_HOSTS, sem alteração produto/settings. Sem publicação de traces/PIN/tokens.

scripts/spec023-native-demo.py --out docs/design/evidence/spec023-refund/native: login,tab,order,payment-guard,cash-open,payment-open,refund,refund-repay,cash-close. Todos pagamentos manuais de teste. Estorno requer Tab aberta; o roteiro payment-open conserva esse estado, sem reabrir uma Tab histórica. Readback separado scripts/spec023-native-refund-readback.py é somente leitura e exige55523, rodada_demo e diretório de evidência deste worktree.

## Limites

Hardware e provider NÃO EXECUTADOS; sem produção. Fonte200% valida shell/catálogo/pagamento/login/estorno, não toda jornada interna. Paridade integral ainda aberta, especialmente diferenças funcionais de tickets/conectividade/metadados sem contrato equivalente. Não confundir teste instrumentado de callbacks com serviço financeiro; readback da jornada real é registrado separadamente ao concluir.

Versão Web de revisão em http://127.0.0.1:3154, API8144 e PostgreSQL55523, somente fixtures de teste preservadas. Nenhum dado do banco demonstrativo é carregado nessa revisão. O roteiro real identificou uma suposição incorreta: após estorno confirmado, o formulário permanece aberto com PIN limpo. Foi lido no banco um único Refund CONFIRMED300 antes de retomar; refund-return fecha somente o formulário pelo controle existente, sem reenviar dinheiro. Esta execução conserva o comportamento de fechamento do formulário; não tratar Cancelar depois da confirmação como reversão do estorno.

## Readback da jornada real concluída

[Readback](evidence/spec023-refund/native/native-refund-readback.json) e [capturas nativas](evidence/spec023-refund/native):1Order/charges600, pagamento original600 PARTIALLY_REFUNDED preservado, recebimento adicional300 CONFIRMED,1Refund CONFIRMED300 ligado ao original. Ator/timestamp e exatamente1evento payment.refunded confirmados;1CashMovement CASH_REFUND−300; Tab CLOSED/exposição0, caixa CLOSED/esperado600/contado600/diferença0. Nenhum ajuste ou provider. Estoque/produção não foram inventados; produto QA Wrong item é fixture existente. UI API36 e banco PostgreSQL real, sem hardware.

Contratos122e890, correção Android29a70bb, testes Web9563358. Instrumentação/lint locais, CI Android somenteunit/build; Web integra PostgreSQL na CI. Evidências desta execução não reclassificam screenshots/protocolos de commits antigos. Publicação final conserva a branch original6e2f4ca, main45c4742 e PR68 rascunho; sem merge/force push/deploy.
