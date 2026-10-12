# Minuta de Política de Privacidade — Rodada Atendimento (PT-BR)

> **DOCUMENTO PARA REVISÃO — NÃO PUBLICAR ANTES DE CONFIRMAR E COMPLETAR OS ITENS [VALIDAR].** Escopo: aplicativo Android Rodada Atendimento. É necessário refletir o comportamento efetivo do produto, backend e fornecedores em produção.

**Última atualização da minuta:** 12 de outubro de 2026

## 1. Quem somos e como entrar em contato

Rodada é uma plataforma para operação de estabelecimentos de alimentação e bebidas. O aplicativo Rodada Atendimento é utilizado por funcionários autorizados de cada estabelecimento.

**Responsável pelo aplicativo e contato de privacidade:** [VALIDAR: nome completo da pessoa física publicadora ou razão social futura, e-mail de suporte/privacidade, endereço ou outro contato exigido pela legislação aplicável].

O estabelecimento pode atuar como controlador dos dados de sua operação e de seus funcionários, e o operador da plataforma como prestador/operador em nome do estabelecimento, conforme contratos e práticas a validar. [VALIDAR: definir formalmente os papéis LGPD com assessoria jurídica].

## 2. Dados tratados

Conforme as funcionalidades efetivamente habilitadas, o aplicativo e seu serviço podem tratar:
- identificação do estabelecimento, identificação/nome/função do operador e informações de login e sessão;
- identificador aleatório da instalação, estado da autorização do dispositivo e dados técnicos básicos necessários para autenticação e segurança;
- pedidos, mesas, comandas, itens, valores, registros de pagamento e movimentações de caixa relacionados à atividade operacional;
- eventos de sincronização, erros e histórico mínimo necessário para evitar duplicações, fraude e assegurar a consistência de operações.

O PIN é transmitido para autenticação pela conexão com a API e não é salvo no armazenamento local. Os tokens da sessão e algumas intenções pendentes são cifrados no aparelho com chaves do Android Keystore; o backup do app está desabilitado. [VALIDAR: logs, telemetria, endereços IP e prazos reais no servidor].

**Pagamentos:** o app pode registrar valores/status e identificadores operacionais. **Não** deve capturar número completo do cartão ou PIN bancário; a captura segura em eventual integração Tap to Pay pertence ao fornecedor de pagamento. [VALIDAR: prestadores habilitados, fluxos reais e eventual SDK antes de lançar].

## 3. Finalidades

Autenticar operadores autorizados, possibilitar atendimento, comandas, pedidos e pagamentos por meio das funções autorizadas, prevenir repetição de operações, manter segurança, auditoria e suporte técnico e cumprir obrigações contratuais e legais aplicáveis.

## 4. Compartilhamento

Os dados podem ser tratados pela infraestrutura técnica da plataforma e, quando habilitados, por fornecedores de pagamentos e outros prestadores necessários à operação. [VALIDAR: listar categorias e prestadores reais, transferências internacionais, contratos e política de retenção].

Não usar esta minuta para afirmar ausência de compartilhamento sem a auditoria dos fluxos efetivos.

## 5. Armazenamento, segurança e retenção

O aplicativo usa comunicações HTTPS na versão de publicação, sessão local cifrada, controles de autenticação e restrição de acesso por estabelecimento. Os prazos de retenção e eventual transferência internacional dependem dos sistemas reais utilizados. [VALIDAR: prazos, países, procedimentos de exclusão, resposta a incidentes].

## 6. Direitos dos titulares

Titulares podem solicitar informações, correção, acesso e outros direitos previstos na Lei Geral de Proteção de Dados (LGPD), conforme as competências do estabelecimento e da plataforma, por [VALIDAR: canal de contato]. Solicitações de exclusão podem estar sujeitas a obrigações legais de manutenção de registros comerciais e fiscais.

## 7. Atualizações

Podemos atualizar esta política para refletir mudanças no produto, na legislação ou nos prestadores. A versão atualizada e sua data serão disponibilizadas no canal público de privacidade [VALIDAR: URL pública].

---

**Checklist de aprovação:** identidade/contato, controlador e operador LGPD, logs e retenção, fornecedores, hospedagem, pagamentos habilitados, direitos e canal do titular, URL acessível em HTTPS. Preparar página pública antes de declaração na Play Console.
