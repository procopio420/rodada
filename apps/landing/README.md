# Landing — rodada.bar

A landing estática em `apps/landing/index.html` usa os tokens de `docs/design/system.md` e as artes oficiais de `docs/design/brand-v1.md`.

Os SVGs em `apps/landing/brand/` são cópias exatas dos canônicos em `assets/brand/v1/`, validadas por `python3 scripts/verify-brand-v1.py`. O Dockerfile copia a fonte Archivo já versionada no app web (sem CDN e sem adicionar família diferente).

## Prévia local

```sh
python3 -m http.server 8080 --directory apps/landing
```

Abra http://localhost:8080. Para fonte exata, execute o container de produção: o Docker copia `apps/web/public/fonts/archivo.woff2` para `/fonts/` na landing; o servidor local simples não copia fontes.

## Deploy

Use contexto de build da **raiz do monorepo** e o Dockerfile `apps/landing/Dockerfile`. Não alterar a demo Railway na publicação da landing. Domínio público `rodada.bar` (com `www` redirecionado via Cloudflare).

## Pendências

- Validar SEO, acessibilidade, favicon e responsividade em browser real.
- Trocar representação conceitual por screenshot real e aprovado quando houver.
- Atualizar referências históricas a `rodada.ai` em contrato de domínios separado, após revisão das rotas.

Sem analytics nem formulário de captação nesta versão.
