# Spec 034 — Gerência: UX por tarefa e padronização visual

**Estado:** PROPOSTA DOCUMENTAL, 2026-10-19. Implementação e aceite visual não iniciados.
**Base examinada:** `main@e82d36c453d44c861b26f104afa39bcc8706814d`.

## Objetivo e usuários

Evoluir a Gerência Web/PWA para uma experiência coesa, agradável e orgânica,
reconhecível como Rodada e alinhada aos princípios da UX 2.0. Gerentes precisam
identificar exceções durante o serviço, consultar financeiro fora do pico e
encontrar configurações sem explorar uma coleção de módulos.

O recorte inicial é Gestão. A direção se estende às cinco áreas e suas páginas
internas em etapas independentes. Não pressupõe refazer funcionalidades existentes.

## Fontes e precedência

- [Spec 007](../007-management-cockpit/spec.md) e seu [aceite](../007-management-cockpit/acceptance.md): intenção e navegação da Gerência.
- [Design system](../../docs/design/system.md), [marca](../../docs/design/brand-v1.md) e [princípios](../../docs/product/principles.md): identidade e interação.
- [Direção UX 2.0](../../docs/design/ux-2-0/README.md): tarefas, contexto e densidade; o protótipo de Atendimento não é uma referência pixel a pixel para Gerência.
- [Spec 033](../033-attendance-ux2-productization/spec.md): frente adjacente de Atendimento, sem transferir seu ownership para esta spec.
- [Baseline e escopo](baseline.md), [plano](plan.md), [tarefas](tasks.md) e [aceite](acceptance.md).

Spec 034 complementa a apresentação da Spec 007; dinheiro, acesso, idempotência,
calendário operacional, domínio e regras existentes continuam sob seus contratos.
Conflitos descobertos exigem registro e decisão, nunca alteração silenciosa.

## Antes e depois propostos

Gestão hoje agrupa links em painéis com botões secundários de mesma ênfase.
Proposta: seções leves com linhas de navegação inteiras, título, descrição curta,
ícone coerente e indicador de avanço. Menos bordas aninhadas, ritmo consistente
e hierarquia entre tarefa, explicação e ação. “Orgânico” significa continuidade,
espaço e formas dos tokens existentes; não novas ilustrações ou decoração.

Preservar Agora / Operação / Financeiro / Cardápio / Gestão, links diretos e
aliases `vendas` e `mais`. Não criar uma sexta aba nem um segundo menu global.
Cabeçalho identifica a tarefa; ações utilitárias são compactas e têm nome acessível.
Atualizar e histórico não competem visualmente com a tarefa principal.
Freshness permanece verdadeiro, mesmo quando a área contém apenas navegação.

## Categorias e fluxos

| Área | Trabalho principal | Direção proposta |
| --- | --- | --- |
| Agora | Identificar e abrir exceção | Alertas acionáveis antes de pulso; fatos e próxima ação visíveis |
| Operação | Localizar gargalo e abrir contexto | Produção/entrega e salão com resumos e destinos claros, sem listas extensas abertas por padrão |
| Financeiro | Escolher revisão, caixa ou consulta | Separar grupos de tarefas; valores canônicos, pendências e confirmações preservados |
| Cardápio | Criar ou editar produto | Manter uma criação e o editor por categorias; harmonizar página, estados e retorno |
| Gestão | Encontrar configuração ou acesso | Estabelecimento e pessoas; configurações da operação; acesso |

Fluxo inicial: Gestão → linha de destino → tarefa interna → Voltar à Gestão,
restaurando foco na origem e posição quando aplicável. Setup mantém mesas,
zonas e equipe; não inventar acesso de pessoas independente sem endpoint existente.
Sessão continua no fluxo `/staff`; não expandir permissões ou autoexecutar logout.
Página interna compartilhada preserva o retorno contextual de outros módulos.

## Design e arquitetura

Reutilizar `appShell`, navegação gerencial, `OperationalIcon`, heading, campos,
botões, diálogos e notice existentes. Extrair linha de navegação/padrão gerencial
apenas após inventariar reutilização. CSS fica sob escopo da Gerência; revisar
impacto em consumidores compartilhados. Documentar novos padrões aprovados no
design system no PR de implementação; esta proposta não cria tokens.

Paleta noturna, âmbar de seleção, papel para conteúdo; Archivo e JetBrains Mono
para valores. Usar escala 4/8/12/16/20/24/32, raios e estados semânticos existentes.
Sem gradientes, glassmorphism, sombras ornamentais ou indicadores fictícios.
Mobile em uma coluna; desktop pode expandir grupos quando leitura e ordem de
teclado permanecem equivalentes. Não impor alturas fixas que cortem fonte ampliada.

## Estados e recuperação obrigatórios

| Estado | Apresentação e ação |
| --- | --- |
| Inicial/carregando | Status nomeado e espaço estável; sem contadores zero presumidos |
| Vazio confirmado | Explicação específica, ação existente quando autorizada |
| Sucesso de leitura | Conteúdo e contexto reais; nenhuma confirmação de escrita ao navegar |
| Atualizando | Preservar contexto e edição, indicar atualização sem simular offline |
| Desatualizado/offline | Último estado identificado e tentativa de reconexão; sem inventar “Ao vivo” |
| Erro parcial/total | Escopo e retry visíveis; nunca publicar soma parcial como completa |
| Sem permissão/revogada | Acesso explícito; dados protegidos tratados pelo fluxo existente, retorno ao login quando exigido |
| Gravação/busy | Ação e navegação conflitante bloqueadas, anúncio acessível |
| ACK pendente/timeout | Conservar intenção/chave/contexto; verificar readback, não repetir mutation por navegação |
| Erro de validação/conflito | Erro junto ao campo/contexto e decisão explícita; conservar entrada válida |
| Sucesso de escrita | Somente readback canônico; feedback e retorno/foco previsíveis |
| Reload/expiração/retorno | Preservar recuperação existente; não prometer drafts persistidos que o módulo não possui |

## Acessibilidade e casos extremos

Links navegam; botões executam ações. Linha inteira tem um único alvo, sem botões
aninhados. Ícones decorativos não duplicam leitura; ícones sem texto têm nome.
Foco visível, ordem lógica, landmarks e headings; Escape/Back fecham apenas a
camada superior permitida e restauram foco. Estados anunciados sem repetição a
cada polling. Alvos >=44px, ações operacionais conforme design system.

Validar 360/390/430/1280px, fonte/zoom 200%, texto longo, listas extensas,
teclado, safe areas e preferência de movimento reduzido. Rodapé não cobre ações,
mensagens ou foco; sem scroll horizontal da página. Cor nunca é o único estado.

## Invariantes, limites e autorização

Navegação não cria mesa/comanda, pedido, pagamento, aprovação ou alteração de
configuração. Manter Tab distinta de TableOccupancy, saldo em centavos, API
autoritativa, Venue, capabilities, reauth, validações, ledger e auditoria.
Pendente, pago, cancelado e inferido não ganham semântica nova por estética.

Fora do escopo: implementar Spec 031/032, relatórios/métricas novos, novos
cadastros/endpoints, migration, política de limite, impressão física, Android,
troca de marca, auth/BFF, deploy, merge e alteração de CI/baselines para mascarar falhas.

Autorizado nesta entrega: planejar e publicar PR documental. As etapas seguintes
são backlog proposto, sem declaração de UX aprovada ou implantação.
