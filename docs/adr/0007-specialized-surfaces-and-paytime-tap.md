# ADR 0007 — Superfícies especializadas e Paytime Tap on Phone

**Status:** Accepted  
**Date:** 2026-10-06

## Contexto

Rodada começou com uma única aplicação web/PWA cobrindo staff, bar, cozinha, guest e owner. Conforme o produto foi ganhando dispatch, table ops, guest ordering e pagamentos, essa abordagem passou a empurrar responsabilidades muito diferentes para a mesma superfície.

O requisito de pagamento também ficou mais claro: no atendimento, o celular do garçom deve ser ao mesmo tempo terminal operacional e terminal contactless. O happy path não pode exigir uma maquininha separada nem mandar o usuário para outro aplicativo.

As alternativas de Tap on Phone foram avaliadas com foco em:

- SDK incorporável no nosso aplicativo;
- operação white-label;
- múltiplos estabelecimentos e múltiplos aparelhos;
- capacidade de manter o domínio provider-neutral;
- modelo compatível com software house/partner e futura monetização sobre pagamentos.

## Decisão

### 1. Rodada passa a ter superfícies especializadas

Cada função operacional possui uma aplicação/superfície focada:

| App | Tecnologia alvo | Foco |
| --- | --- | --- |
| **Rodada Atendimento** | Android nativo — Kotlin + Jetpack Compose | garçom/caixa móvel, Tab, pedidos, mapa/atendimento e cobrança |
| **Rodada Cozinha** | Web/PWA | fila de produção, preparo e disponibilidade |
| **Rodada Bar** | Web/PWA | fila de bebidas, preparo e disponibilidade |
| **Rodada Cliente** | Web/PWA | QR, Tab autorizada, pedido, acompanhamento e pagamento |
| **Rodada Gerência** | Web responsiva | configuração, operação ao vivo, equipe e relatórios |

Isso não cria cinco backends nem cinco domínios. Todas as superfícies usam a mesma API, o mesmo modelo de domínio e os mesmos contratos.

Não devemos recriar um frontend único e apenas esconder módulos por permissão quando as necessidades de interação são materialmente diferentes.

### 2. Atendimento é Android nativo

**Rodada Atendimento será implementado em Kotlin + Jetpack Compose.**

Tap on Phone é uma capacidade central do app e justifica integração direta com NFC, lifecycle Android e SDKs financeiros. O projeto não deve depender de React Native/WebView + bridge para executar a parte crítica de pagamentos.

Compartilhamos semântica, tokens e contratos com as superfícies web; não forçamos compartilhamento de componentes de UI entre Compose e React.

### 2A. BYOD por padrão e hardware reaproveitado no piloto

No piloto do Bar do Aderlan, o modelo operacional padrão é:

| Pessoa/estação | Dispositivo | Superfície |
| --- | --- | --- |
| Garçons | Celular Android pessoal, quando disponível e adequado | Rodada Atendimento |
| Caixa/gerência | Computador já existente no caixa | Rodada Caixa e Gerência |
| Cozinha e bar | Computador já existente na produção | Rodada Cozinha e Rodada Bar, em views/abas distintas ou simultâneas |
| Cliente | Próprio celular, sem instalar app | Rodada Cliente via QR/PWA |

Não exigir aquisição de celulares, computadores ou terminais de cartão adicionais como condição de entrada no piloto. A implantação deve verificar conectividade, ergonomia e capacidade dos equipamentos existentes. Prever alternativa para funcionário que não possa ou não deseje usar celular pessoal, bem como contingência para bateria, rede ou aparelho indisponível.

**Identidade é de pessoa, não de aparelho.** No Atendimento Android, após login válido, registrar automaticamente a instalação sem aprovação do gerente; `UNTRUSTED` não bloqueia operações normais autorizadas. `TRUSTED` fica reservado a capacidades específicas de terminais compartilhados, como troca rápida de operador. `REVOKED` invalida sessões daquela instalação, enquanto bloquear o funcionário requer revogar sua membership.

Registrar a instalação não significa acesso a dados privados do celular, rastreamento do funcionário ou gestão MDM do dispositivo. Habilitar Tap on Phone exige verificação e eventual autorização **separadas pelo PSP**, sem prejudicar uso normal de pedidos em celulares sem NFC.

### 3. Paytime é o primeiro provider de Tap on Phone

O primeiro adapter do MVP será:

```text
TapToPayProvider
      |
      v
PaytimeTapProvider
      |
      v
Paytime Tap on Phone SDK
```

O SDK será incorporado diretamente no Rodada Atendimento.

Happy path:

```text
Tab
→ Pagar
→ valor/método
→ Aproximação
→ Paytime SDK dentro do Rodada
→ NFC do próprio aparelho
→ confirmação/reconciliação backend
→ saldo da Tab atualizado
```

O garçom não redigita o valor em outro equipamento e não precisa abrir outro aplicativo.

### 4. Paytime não entra no domínio central

A decisão é **provider inicial, não exclusividade arquitetural**.

O backend e o Atendimento dependem de portas/capabilities próprias. Provider-specific IDs, erros e estados são traduzidos pelo adapter.

Devemos conseguir ter no futuro, por configuração de Venue:

```text
Venue A → Paytime
Venue B → outro provider
Venue C → Paytime
```

sem alterar o modelo de Tab/Charge/Payment nem redesenhar o fluxo principal do garçom.

### 5. Confirmação financeira continua server-side

Callback local do SDK não é sozinho fonte de verdade.

Timeout ou perda de conectividade depois do envio pode produzir `CONFIRMATION_PENDING`. O Rodada reconcilia com provider/webhook/API antes de liberar retry equivalente.

## Consequências

### Positivas

- experiência de cobrança integrada ao atendimento;
- nenhum hardware de maquininha adicional no happy path;
- stack nativa adequada para NFC e SDKs financeiros;
- cada superfície fica menor e mais específica;
- backend/domínio continuam únicos;
- troca/adição de provider não exige reescrever o núcleo financeiro;
- abre caminho para uma camada futura de **Rodada Payments**.

### Custos

- Android passa a ter codebase própria;
- design system precisa ter implementação equivalente em Compose e Web;
- contratos de API ganham ainda mais importância;
- homologação/certificação do SDK Paytime entra na entrega do app Android;
- BYOD exige política operacional e alternativa para quem não usar aparelho pessoal, além de Wi-Fi confiável e contingência.

## Não decidido por esta ADR

- markup/MDR comercial final do Rodada;
- split marketplace;
- roteamento automático por taxa/adquirente;
- adquirência própria;
- iOS para staff;
- fiscal.

Esses assuntos exigem decisão/spec própria quando entrarem no roadmap.
