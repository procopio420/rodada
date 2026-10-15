# Landing — rodada.bar

Landing pública estática do Rodada. Segue `docs/design/system.md`, `docs/design/brand-v1.md` e a [Spec 030](../../specs/030-marketing-landing/spec.md). Usa as cópias oficiais de `apps/landing/brand/` e Archivo local, sem framework/analytics ou dependências JS remotas.

## Design atual — editorial, produto primeiro

- Hero com **H1 e CTAs HTML**, tipografia Archivo e fotografia **ilustrativa** do bar como suporte; não reutiliza cartaz com texto embutido no hero.
- `marketing/rodada-campanha-mobile.webp` é uma imagem de contexto recortada, originada de composição gerada por IA; o QR na ilustração **não funciona**.
- `marketing/rodada-campanha.jpg` continua sendo a peça de OpenGraph para compartilhamento, não o visual principal do site.
- Tour acessível de Atendimento → Bar → Gerência com imagens de fixture em `screens/`. É uma **demonstração visual**, não uma operação ao vivo; imagens podem diferir do build atual.
- Uma única melhoria JS local habilita tabs e CTA fixo após sair do hero. **Com JS desligado**, as três áreas do produto continuam visíveis, links comuns funcionam e não existe rastreamento.

## Rodar localmente

```sh
python3 -m http.server 8080 --directory apps/landing
```

Este comando serve o HTML, mas **não** copia a fonte. Para o pipeline de produção, usar contexto de build da raiz do repositório e `apps/landing/Dockerfile`: inclui Archivo, screens, marketing, brand e páginas legais. Nunca alterar demo/venue routing ao alterar landing.

## Gates

```sh
python3 scripts/verify-brand-v1.py
python3 -m unittest discover -s scripts -p test_landing_marketing.py -v
```

O GitHub Actions Landing Visual QA roda Chromium 320/360/375/390/430/768/820/1024/1440/1920, valida conteúdo, imagens, teclado no tour, estado do CTA e fallback sem JavaScript; salva PNGs/JSONs no artifact. Evidência de implementação em [auditoria](../../docs/design/landing-campaign-qa-2026-10-15.md).

## Publicação e limitações

Destino: `rodada.bar`. Merge e publicação são ações **separadas** sujeitas a autorização. Continuam pendentes Safari/Firefox físicos, leitor de tela, avaliação comercial das imagens/screenshot e autorização de uso de material real do piloto. Não afirmar métricas, clientes, pagamentos, homologação ou disponibilidade de features sem evidência.

Links de privacidade, termos e exclusão de conta devem permanecer públicos. Não adicionar analytics silenciosos nem formulários de captura sem escopo/consentimento.
