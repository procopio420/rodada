# ADR 0016 — Ferramentas DEV usam a autorização operacional

Status: Accepted

A solicitação local de administrar staff não cria uma conta superusuária global.
Web e API habilitam a superfície somente por RODADA_DEVELOPER_TOOLS, false por
padrão. A API continua limitada ao Venue autenticado, staff.manage e PIN recente.
Provisionamento transacional idempotente serializa pelo Venue e registra replay
no evento de auditoria, sem PIN; fingerprint usa HMAC para não permitir ataque
offline ao PIN. Login global existente nunca é adotado automaticamente.
Remoção é revogação do vínculo, preservando referências operacionais/financeiras.
Não permitir remover/demover o último OWNER ativo nem remover a própria sessão.
O ambiente local mantém OWNER de desenvolvimento conhecido, sem modificar o papel
das contas operacionais Ana/Bia. Não publicar essa flag habilitada em produção.
