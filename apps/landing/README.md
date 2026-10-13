# Landing comercial — rodada.bar

Landing estática, sem dependências, em `apps/landing/index.html`.

## Identidade

A fonte de verdade é `docs/design/system.md`. Paleta e hierarquia foram reproduzidas com tokens semânticos canônicos. A landing não cria outra identidade. A fonte Archivo deve ser servida pelos assets compartilhados na integração final; há fallback de sistema até configurar esse asset.

## Executar localmente

Na raiz do repositório:

```sh
python3 -m http.server 8080 --directory apps/landing
```

Abra http://localhost:8080.

## Publicação

Deploy como site estático no Railway (ou hospedagem estática equivalente), com root `apps/landing`, sem afetar a demo atual. Configurar `rodada.bar` e redirecionar `www.rodada.bar` pelo Cloudflare.

## Antes de publicar

- Trocar os links `mailto:contato@rodada.bar` pelo WhatsApp comercial confirmado; o endereço de e-mail é apenas placeholder e não foi verificado.
- Substituir o mockup ilustrativo por screenshots reais e aprovadas do app.
- Integrar a fonte Archivo local e o logo/ícones oficiais dos assets compartilhados.
- Adicionar página de privacidade quando o conteúdo e o canal de captação estiverem definidos.
- Validar SEO, acessibilidade e responsividade em navegador real.
- Atualizar o README principal/contrato de domínios de `rodada.ai` para `rodada.bar` em mudança separada, após conferir rotas e migração planejadas.

Não há analytics nem formulário de coleta nesta versão.
