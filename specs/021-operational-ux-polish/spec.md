# Spec 021 — Hierarquia operacional e revisão visual

## Comportamento e regras

- Bar/Cozinha mostram fila e passe antes da disponibilidade e Quick Catalog. Quantidades, produto e comanda permanecem completos; nomes de itens em produção usam a escala `text-lg`. Contadores representam linhas de OrderItem do snapshot, não pedidos nem unidades vendidas. Antes de snapshot não mostrar contagem medida.
- Tablet/desktop expandem a estação em duas colunas: produção e passe. Ordem de leitura e teclado permanece fila → passe → disponibilidade → cadastro. Mobile mantém coluna única.
- Gerência mantém divergências e estornos primeiro, depois pulso e produção. Conta da Casa fica na seção Gestão, após o contexto de caixa/salão. Não esconder alertas financeiros já existentes nem alterar controles/permissões.
- Comandas em `REQUIRES_ACTION` permanecem destacadas antes do pulso, com saldo/contexto e link para Gestão. A mudança de posição dos formulários não pode relegar atenção de limite ao final da tela.
- Estados de produção, caixa e indisponibilidade são rotulados em português com a mesma semântica compartilhada. READY não integra a contagem "em preparo" da Gerência; o passe tem contagem própria.
- Revisão visual local tem índice estático gerado em diretório ignorado com rota, viewport, estado, problema, status e antes/depois. Fixtures são evidência visual, nunca prova de integração. A aplicação real permanece acessível separadamente.
- Cliente usa ProductIcon com dimensão fixa, nome/estação em coluna e preço separado, com espaçamento e Button existentes. Ícone não cresce para ocupar o texto. Estados disabled preservam nome e preço legíveis.
- POS legado exibe indisponibilidade em texto e desabilita seleção do produto canonicamente indisponível. API permanece autoritativa na confirmação; não alterar intenção idempotente nem pedido já confirmado.

## Fora de escopo

Novas regras financeiras, autenticação, providers, métricas inferidas, transporte realtime, IA de ícones, substituição da identidade visual, funcionalidades Android sem toolchain e produção. Não criar rota de produto para galeria nem credenciais em HTML/capturas.

## Aceite

Ver acceptance.md. Contratos de domínio continuam nas specs 001/004/007/008/012/019/020.
