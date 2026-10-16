# Spec 032 — Entrada QR híbrida, retirada no bar e recuperação da jornada

**Status: PROPOSTA / NÃO IMPLEMENTADA.** Contrato de produto aprovado para elaboração em 16/10/2026. Este documento não altera o comportamento instalado, nem certifica pagamentos/segurança em campo.

## Objetivo

Entregar uma experiência contínua do primeiro QR à saída: o cliente pode iniciar o consumo sem garçom, consumir em mesa fixa/improvisada ou sem mesa, receber um código de retirada visual, consultar sua própria comanda, pagar quando houver meio habilitado e sair sem devolver tag. O operador só age quando agrega valor ou resolve exceção.

**JTBD:** cliente quer começar/pedir/retirar/pagar em poucos passos; garçom quer abrir mesas improvisadas e atender sem cadastro; bartender quer achar a bebida pelo código em segundos; caixa quer comprovar cobrança sem confundir ficha e dinheiro.

## Relacionamento com contratos existentes

- `specs/004-table-guest-ordering/`: Table, TableOccupancy, GuestSession, token opaco, revogação e política de guest; manter invariantes.
- `specs/009-tab-operations/`: movimentos de localização, transferências e divisão de responsabilidade sem reescrever ledger.
- `specs/014-connectivity-degraded-operation/`: efeitos de timeout, retomada e idempotência.
- `specs/015-receipts-printing-fallbacks/`: ticket impresso como fallback, não prova de pagamento por si só.
- `specs/026-operational-ux-friction/` e `specs/029-attendance-mobile-design/`: UX task-first.
- Issue #146: TabIdentifier/código/QR de Tab/NFC (dependência técnica; não duplicar como nova entidade financeira).
- PR #211 / Spec 031: feedback opcional do cliente sobre **entrega ao consumidor na mesa**. Retirada no balcão desta spec tem evento/modalidade próprios; compartilhar provenance e filosofia, não misturar conceitos.
- PR #212: protótipo Atendimento UX 2.0, laboratório separado; não assumir que já foi implementado ou aceito.

## Invariantes não negociáveis

1. Order pertence a Tab; Table nunca possui ledger. Ocupação pode ter 0..N Tabs; Tab pode não ter mesa.
2. **QR de mesa, QR geral, tag física, código FG84 e sessão guest NÃO são credenciais financeiras intercambiáveis.** QR público resolve contexto; acesso sensível requer autorização de sessão/tab.
3. Venue delimita tudo, inclusive busca de código, binding de tag, eventos realtime e acesso cross-host.
4. Código de retirada é **localizador público**, não segredo, prova de pagamento, autorização para cancelar, pagar ou visualizar comanda de terceiros.
5. Emitir direito de retirada exige Order canônico com `fulfillment_mode=PICKUP` e `release_basis` elegível: pagamento confirmado por fonte canônica OU lançamento em Tab de consumo a prazo expressamente autorizado e dentro de limite. Dinheiro/Tap externo só é registrado após confirmação do caixa autorizado. Nunca tratar Pix pendente/timeout como pago.
6. Confirmação de retirada é opcional no fluxo de balcão comum; ausência de marcação é `UNKNOWN`, jamais `DELIVERED` comprovado. Políticas de maior risco podem exigir validação por staff; comunicar isso antes da compra.
7. Mudança de modo/horário não altera pedidos aceitos, nem seu destino ou forma de cobrança. Modo é resolvido/snapshot no momento da confirmação do pedido.
8. Pagamento ou fechamento de Tab não libera TableOccupancy. Liberação física é evento separado, sem exceção implícita.
9. Toda mutação usa autorização, audit trail, idempotência/replay, concorrência segura e readback canônico.

## F1 — Mesa existente / mesa improvisada / tags

- Mesa cadastrada: abrir atendimento sem perguntar de novo pelo QR. O vínculo físico permanece enquanto a mesa existir e a tag continuar atribuída.
- `Adicionar mesa`: criar Table imediatamente, com label/Zone/posição conforme contrato atual. Depois mostrar somente `Vincular QR` (ler tag disponível) ou `Agora não`. A mesa sem QR funciona para staff e tem indicador discreto `Sem QR` com ação contextual de vincular depois.
- Definir registro `PhysicalTag` pré-provisionado por Venue com token aleatório opaco, estado `UNASSIGNED | ASSIGNED | RETIRED` e histórico de atribuições; tag reutilizável só admite **uma associação ativa** por vez. QR legado `Table.public_token` continua válido durante migração; resolver distingue tag atribuída, tag livre e QR legado sem expor IDs internos.
- Transferência de tag já vinculada exige confirmação explícita, permissão do operador, versão/CAS e auditoria. QR associado nunca troca de mesa silenciosamente; remoção/desmonte não encerra ocupação nem altera Tab/Order/Charge.
- Mesa sem QR, tag danificada, câmera sem permissão, etiqueta offline, QR inválido ou leitura cruzada de Venue têm caminho de recuperação sem impedir trabalho interno.
- NFC opcional/futuro, conforme #146, não depende de UID simples como identidade confiável.

## F2 — Cliente chega e abre a mesa

- Scan do QR físico resolve Venue + Table. **Scan sozinho é navegação**, não bloqueia mesa. Guest vê cardápio e CTA `Começar nesta mesa` se `AVAILABLE` e política permitir.
- CTA cria ou se associa **atomicamente** à ocupação guest ativa, com sessão provisória curta sem pedidos e token vinculado a `generation`. A ocupação é aberta pelo cliente, sem aprovação de garçom.
- Provisório sem pedido e sem interação presencial confirmada pode expirar/ser liberado automaticamente, com política segura e observabilidade; nunca expirar se houver Order, Charge, Payment pendente, Tab com exposição, chamada ou atendimento aceito. Evitar criar múltiplas ocupações no duplo clique/scans simultâneos.
- Outro cliente que escaneia mesa ocupada entra na experiência da mesa, mas recebe **a própria sessão e Tab privada** por padrão. Compartilhar Tab exige convite/claim deliberado autorizado, não a posse do QR da Table.
- Mesa `DIRTY/CLEANING/OUT_OF_SERVICE`: não iniciar pedidos; feedback `Mesa indisponível; chame a equipe`; oferecer cardápio read-only quando política permitir.
- QR fotografado é risco real não resolvido apenas por token de sessão: aplicar rate limit, detecção/anomalias, limites de exposição e emergency block pelo staff; configuração de maior risco pode pedir verificação adicional. Não alegar prova criptográfica de presença física com QR estático.

## F3 — QR geral e continuidade de Tab

- QR geral do Venue abre cardápio/fluxo sem Table/Occupancy: `Pedir para retirar`, `Minha conta` (se sessão autorizada), sem exigir cadastro/CPF.
- Usuário com Tab ativa na sessão reconhecida vê `Continuar minha comanda` como ação primária. Não criar nova Tab silenciosamente ao trocar QR de mesa ↔ QR geral.
- Tab reconhecida pode trocar localização por fluxo seguro; separar `Onde estou` de `Como recebo`. Mudança de Table usa Spec 009 e valida ocupação/versões.
- Guest desconhecido abre Tab anônima explícita, sem permissão implícita para aderir a Tab de outra pessoa.
- Sessão entre QR geral e QR de mesa mantém intenção/draft por Venue e Tab; recupera contexto se usuário retornar por outra entrada, nunca compartilha uma sessão privada por inferência de mesa.

## F4 — Pedido, autorização, produção e retirada

- Cada Order registra modalidade `AT_TABLE | PICKUP` (e localização de entrega snapshot), independente de FulfillmentStation `BAR | KITCHEN`. Pode coexistir no mesmo Venue durante mudança do modo bar/balada, inclusive pedido misto dividido em grupos de preparo/retirada.
- Na confirmação, API revalida disponibilidade, política guest, Tab, exposure, modalidade e base de liberação. Um pedido não fica pronto para retirada antes da regra financeira/autorização aplicável.
- Para cada **grupo de retirada** (pickup unit), emitir código humano como `FG84`, único entre códigos ativos no Venue, com índice e revogação sob concorrência. Evitar caracteres ambíguos (0/O, 1/I). Código pode ser reutilizado após janela segura de quarentena, nunca enquanto houver chance operacional de colisão ativa.
- Cliente vê código em destaque, itens daquele grupo, estado `Recebido → Preparando → Pronto para retirar → Retirada informada`, local de retirada, aviso `Mostre este código no balcão`. Sem credencial, o código não revela preço, saldo, dados pessoais ou pagamento.
- Bar recebe o mesmo código, itens e estado; busca rápida por código, foco nos prontos, ações de exceção sob demanda. Bartender compara visualmente e entrega; **não exige scanner nem botão de entrega**.
- `Já retirei` do cliente e `Entregue` do bartender são **opcionais**, com `source=GUEST_DECLARED | STAFF_CONFIRMED | INFERRED | UNKNOWN`, atores/horários distintos e histórico imutável. Uma observação do cliente não vira comprovação de staff.
- Permitir grupos de retirada e retirada parcial real, com linhas/quantidades remanescentes; não marcar o Order inteiro como entregue ao retirar apenas parte. Para operação de pico, UI não deve impor edição por item no happy path.
- Após tempo configurável, códigos não resolvidos saem da fila principal para `Aguardando verificação` pesquisável; expiração visual **não altera** financeiro nem prova retirada.
- Reapresentação de código: staff consegue consultar status/sinais de retirada, com indicação explícita de incerteza quando ninguém confirmou; ações de contestação/correção auditadas. Confirmar visualmente código NÃO é proteção contra fotografia/copiar ficha: modos antifraude proporcionais por Venue/valor devem existir sem impor scanner no padrão.

## F5 — Pagamento, encerramento e liberação

- Na Tab, mostrar o saldo canônico devido ao participante autorizado, permitir pagamentos parciais/conta compartilhada conforme contratos do Ledger, e diferenciar `Pagamento iniciado`, `Aguardando confirmação`, `Confirmado`, `Não concluído`.
- `Já paguei` nunca altera Payment; resultado autoritativo é backend/provedor ou caixa com permissão e prova externa.
- Em QR geral, comanda sem mesa pode encerrar sem recolher tag física. Em mesa, `Paguei minha parte` encerra apenas responsabilidade financeira/Tab elegível e não libera mesa automaticamente.
- Encerramento da TableOccupancy e `AVAILABLE` seguem lifecycle físico `OCCUPIED → DIRTY → CLEANING → AVAILABLE`; equipe é dona da liberação salvo política futura com prova explícita de saída. Sem popup obrigatório ao cliente depois de pagar.
- Toda mudança de mesa ou de pedido mantém rastreabilidade de onde **deveria** ser entregue vs. onde está hoje.

## F6 — Retorno e falhas

- Reabrir navegador no mesmo dispositivo: recuperar sessão/autorização por armazenamento seguro e validar canonical readback. Link privado opcional de retorno com token opaco revogável, nunca o FG84 sozinho.
- Se cliente perde celular: caixa consegue localizar pedido sem revelar dados sensíveis, recuperar comprovante/ficha física e reemitir acesso sob autorização, auditando e revogando credencial anterior quando necessário.
- Offline no cliente: cardápio cacheado pode ser exibido como desatualizado; não anunciar envio, pagamento ou retirada concluídos sem ACK canônico. Intent persistida usa mesma idempotency key no retry.
- Double click, ACK perdido, timeout pós-commit, QR revogado, Venue errado, sessão expirada, saldo insuficiente, pedido já entregue, tag concorrente e dois operadores devem produzir resultado canônico estável + ação de recuperação legível.

## Fora de escopo

- Exigir app/CPF/login, hardware NFC obrigatório, localização GPS/BLE como prova de presença, pagamento provider novo, bypass fiscal, dinâmica de preços, fidelidade, descontos, mapa 2D novo, reconhecimento facial ou detecção infalível de fraude.
- `FG84` não é código de claim de Tab e não concede leitura de ledger.
- Não tocar em produção real, demo compartilhada, deploy ou pagamentos reais nesta spec.

## Tensão de produto explicitada

A experiência desejada de autoabertura por QR estático **não elimina** pedidos remotos maliciosos nem reutilização fraudulenta de códigos. A especificação não promete prevenção perfeita: aplica limitação proporcional, contingência operacional e fallback configurável sem aprovação obrigatória no fluxo padrão.
