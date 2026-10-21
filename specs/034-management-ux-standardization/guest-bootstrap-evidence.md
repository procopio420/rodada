# Manutenção global — bootstrap do cliente

2026-10-21. Branch codex/management-ux-alerts, base HEAD860b25d93da486d2416c6ddaccfdccd9605f8953;working tree acumulado sem commit/push/merge/deploy. R3, pedido/recoveryguest.

GuestOrdering separa leitura bootstrap de aplicação. Preserva GETcontext para intenção pendente e POSTqr/resolve caso contrário;chavelegada é removida e autorização continua em cookie. Callback inicial e resposta do catálogo verificam atividade. Retrymanual mantém loading/notice. Cache é aplicado depois que bootstrap resolve;loading bloqueia interação enquanto pendente. Receipt/erro são reconciliados por token/Tab no próprio render. Fórmulas, comandos de pedido, carrinho e journal/replay intactos.

Build webpack/typecheck/lint focado/diff check PASS. Auth4PASS e tenant10PASS. Lint global PASS:325arquivos/0erros/0avisos;JSON visual-artifacts/spec034-global-lint-after-guest-bootstrap.json. Os10erros globais adicionais identificados após manutenção gerencial estão eliminados (mais os7originais do recorte acompanhado).

Revisão independente local:NO_FINDINGS_WITH_GAPS. Limites:resposta tardia da consulta de receipt após troca de contexto permanece herdada;cleanup protege bootstrap/catalog, não todas consultas concorrentes. Cache não aparece durante bootstrap pendente; não inferir experiência offline idêntica nesse intervalo. APIs interceptadas e gateway não provam integração real,ledger/deduplicação ou isolamento completo entreVenues. Sem teste novo que apenas espelhe implementação. Reviewautenticado da composição REVIEW_BLOCKED.

Próximo responsável:concluir validação visual composta antes interrompida;lint está limpo nesta rodada. CI/integração real/manual/homologação continuam pendentes;NO-GOrelease/piloto. Preservar patches. Hashes docs/development/evidence/spec034-guest-bootstrap/SOURCE-SHA256SUMS.

Resultado visual final:59PASS57,4s nas5suítes guest (catálogo,navegação,order-intent,quantidades,repeat). Cobertura:lostresponse/reload/rawpayload/recoverysemQRresolveadicional,recusa de escopoVenue/session/table/occupancy/generation/Tab,revogação,storageinválido/writefailure,limite99,customização,repetição com preço atual e bloqueios. Mobile360/390/430 e navegação1280 incluídos. Nenhum teste falhou nesta rodada.
