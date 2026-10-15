# Spec025 — correção da validação permanente de 15/10/2026

Referências: [NO-GO histórico PR187](https://github.com/procopio420/rodada/pull/187),
[correção PR189](https://github.com/procopio420/rodada/pull/189),
[issue130](https://github.com/procopio420/rodada/issues/130).
Gates1–3 homologados são preservados. Este gate trata a configuração permanente.

## Causa e contrato

O fluxo é Cloudflare → Railway ingress → Nginx `/api/*` → Next BFF → Django
loopback ASGI/Uvicorn. Nginx mantém o Host e apaga as três assertions externas
para APIs nativas; BFF cria outra assertion HMAC por Host/método/path/timestamp.
QR/refresh BFF usam paths internos canônicos com barra final, sem308.

Django rejeita um domínio inativo/desconhecido com421 antes do endpoint. O
`fetch` Node/Undici considera421 elegível a retry automático: destrói a conexão
e tenta reenviar o POST consumido. A reprodução local Uvicorn e a sonda privada
no runtime Node24.22.0/Django real obtiveram
`UND_ERR_REQ_CONTENT_LENGTH_MISMATCH`; catches BFF convertem essa exceção em503.
As exceções dos quatro requests históricos foram descartadas: não há stack
retrospectivo individual. A causa equivalente foi reproduzida no mesmo runtime,
mesmos hosts, métodos e endpoints, com assertions válidas e capacidades inválidas.
Não é prova de timeout, falha HMAC, Cloudflare ou redirect308.

O transporte corrigido usa body não reenviável e `duplex: half`, com
`Content-Length` calculado em bytes UTF-8 (DRF ignora stream sem esse tamanho).
Não altera421 para um erro auth genérico e não repete comandos. Falhas reais de
conexão continuam rejeições e503 no gateway; streams/cancelamento permanecem.

A spec original permitia404/421; o404 da raiz não demonstrou vazamento.
O contrato permanente foi explicitamente estreitado: Next valida o candidato a
Host antes de UI/manifest/BFF/auth/Guest e responde421/no-store para identidade
inativa/inexistente.403 HMAC e5xx não viram421. A validação Django continua após
o guard, inclusive na corrida de desativação. `skipTrailingSlashRedirect` evita
308 antes do guard; Web aceita ambas as formas, upstream mantém paths canônicos.
Assets `/_next/static`/`/_next/image` não carregam identidade e ficam fora do matcher.
Hosts de compatibilidade e API nativa mantêm contratos próprios (unknown raw400
por ALLOWED_HOSTS não equivale a421 BFF). Falha tardia de contexto durante render
não vira404: usa erro genérico, podendo resultar500 ou stream já iniciado.

## Evidências e reprodução

[Recibos sanitizados](../../specs/025-tenant-host-routing/evidence/permanent-fix-20261015/)
separam runtime anterior, candidato local, testes interrompidos/falhos e CI.
Sem PIN, QR, cookies, dumps, dados pessoais, valores financeiros ou fingerprints.

- `npm run test:tenant`: paths + transporte Node contra Uvicorn descartável.
  Requer Python com dependências API, configurável por `RODADA_TEST_PYTHON`.
- `npm run test:table-service`: Next real com autoridade descartável para falhas
 403/503/502, segundo lookup e corrida guard→421 sem replay; não é homologação API.
- `npm run test:integration`: Next+Django+PostgreSQL isolado `rodada_web_e2e`;
  fixture bloqueia qualquer DB remoto/operacional. A matriz troca A/B apenas
  nesse banco descartável e restaura seus domínios ao final.
- Readback operacional: executar fonte revisada de
  `scripts/spec025-gate3-preflight.py --expected-sha <sha>` por SSH privado
  (a imagem não inclui `/app/scripts`), e comparar positivamente flag=`true`
  e seed=`false` no runtime/processos. Consultas de integridade READ ONLY.

## Rollout e backout — somente após autorização

1. Conferir main/deployment, CI/revisão do candidato integrado e staged work.
2. Revalidar flagtrue/seedfalse/HMAC e PostgreSQL privado; nunca chamar seed,
   restore, provisioning QA ou mudar DNS/Cloudflare. Este fix não tem migrations.
3. Solicitar autorização explícita do merge/deploy para `rodada-web/demo`.
   Um PR aprovado não autoriza a aplicação automática de staged changes.
4. Acompanhar o deployment exato atéSUCCESS; readback SHA/flags antes/depois;
   repetir matriz HTTPS421 (sem seguir redirects), login Chromium protegido,
   refresh/cookies, módulos/SSE/logout-replay, QR existente autorizado e43 grupos.
5. Em falha de transporte/isolamento/saúde, interromper novas mutações, diagnosticar
   e aplicar somente backout aprovado. O build anterior7189c972 preserva seed-off,
   mas contém o defeito503; não o classificar saudável para negativos421.
   Manter seedfalse e não ativar QA. Contenção emergencial de isolamento confirmado
   segue o runbook; sem incidente confirmado, não desligar flag para obterPASS.

Validação pós-deploy do candidato: **NOT_RUN** até autorização e deployment real.
