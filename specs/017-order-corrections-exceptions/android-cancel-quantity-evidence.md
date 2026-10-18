# Cancelamento de lançamento indevido Android

Evidência local de 2026-10-17. Branch `codex/android-attendance-colors`, base `fb3ea55d`, patch sem commit.

Cancelar exige quantidade, motivo e PIN autorizado. Múltiplas unidades passam por revisão antes do envio. Intenção, chave e histórico são preservados. Itens pagos ou com responsabilidade transferida exigem fluxo próprio.

- PASS: 40 testes PostgreSQL de correções em banco descartável, incluindo parcial/integral, replay, concorrência, autorização, tenant, pagamento e dispatch.
- PASS: 99 testes JVM, assembleDebug, assembleDebugAndroidTest e lintDebug.
- PASS: dois testes Compose e quatro repetições em 360/390/430 dp e 360 dp com fonte 200%.
- PASS: Django check, nenhuma migration nova e diff sem erros de whitespace.
- Revisão independente: corrigidos dispatch órfão e tratamento HTTP de transferência; nova revisão sem achados, com lacunas abaixo.

Capturas locais ignoradas: `visual-artifacts/android-native-port/correction-final/`. APK instalado, API recarregada e ready200. Tela/fonte restauradas. Nenhum cancelamento financeiro na base compartilhada; sem commit/push/merge/deploy.

Não verificados: perda real de resposta em operação no dispositivo, TalkBack, aparelho físico e homologação em estabelecimento. Fixtures não comprovam produção. Próximo responsável: solicitante para aceite local.
