# Spec 028 — Rodada Impressoras: agente Windows, multiagente e compatibilidade

**Progresso:** S1 integrada no PR #149 e S2 integrada no PR #155 (974e0bc), ambas com autorização. S3 em implementação e validação; ver [contrato e evidências](s3-printing-mvp.md). S4–S7 pendentes. Sem instalador ou homologação física.
**Status:** S1/S2 merged; S3 implementation/testing in progress. S4–S7 pending; no public installer or physical certification.
**Owner:** Access (identidade de dispositivo), Documents/Printing (jobs e endpoints), Web Manage (configuração), Landing (downloads), local Windows agent.
**Extends:** Spec 015 Receipts/Printing; Specs 008 Access, 013 Venue Configuration, 014 Connectivity, 018 Notifications e 019 Station Routing; ADR 0013 Non-fiscal print delivery.
**Pilot:** Bar do Aderlan; hardware conhecido por foto: Bematech MP-4200 TH. Conexão real, driver, firmware e comandos suportados ainda não verificados.

## Objetivo e decisão de produto

Um único Rodada Impressoras para Windows permite instalar zero, um ou vários agentes por Venue e atribuir cada impressora física ao BAR, KITCHEN ou caixa/documentos do cliente, independentemente de USB local, TCP/IP na LAN ou compartilhamento Windows. O operador usa o Manage para configurar e diagnosticar. O agente inicia com Windows sem exigir navegador ou sessão de usuário logada.

Entrada pública no **rodada.bar/downloads** e contextual no **Manage > Impressoras > Adicionar computador** apontam para o MESMO instalador universal e release estável. Pareamento por código de uso único aprovado por usuário autenticado com capability print.manage (normalmente MANAGER/OWNER). Slug é conveniência de localização, nunca autorização; senha do gerente não é digitada nem persistida no agente.

## Invariantes herdadas da Spec 015 — não alterar

1. Pedido, pagamento, fila de produção e saldo canônicos continuam no banco; impressora nunca determina fulfillment nem confirma pagamento.
2. Renderizar apenas documento derivado de ordem confirmada ou recibo/conta válido; preservar snapshot/fingerprint, histórico imutável e label DOCUMENTO NÃO FISCAL.
3. Identidade do ticket inicial de produção é única entre endpoints. Reimpressão é explicitamente vinculada, auditada e marcada REIMPRESSÃO; não cria novo pedido ou preparo.
4. Fencing, lease, dedupe e idempotência da Spec 015 continuam no servidor. Rejeitar resultado tardio e dupla emissão concorrente.
5. Spool aceito, bytes transmitidos, status de rede e resposta de driver **não** provam papel impresso. Somente confirmação manual auditável pode marcar PRINTED na v1.
6. Após possível envio parcial, crash ou timeout ambíguo: DELIVERY_UNCERTAIN, sem retry automático e sem failover automático. Inspeção/reimpressão explícita.
7. Printer/agent offline não bloqueia confirmação de pedidos, KDS ou pagamentos. Nenhum ticket é gerado offline a partir de carrinho não confirmado.
8. Auto-fallback do KDS permanece separado, desabilitado até gate da Spec 015; instalar agente não habilita auto-fallback nem muda o modo de produção.
9. Isolamento por Venue em leitura, pareamento, claims, payload, logs, ações administrativas e revogação.
10. Não adicionar rota direta da nuvem para impressoras na LAN nem endpoint de entrada internet no Windows.

## Topologias suportadas

| Topologia | Comportamento | Limitação |
| --- | --- | --- |
| Impressoras Ethernet/Wi-Fi na LAN | Um agente no PC caixa descobre/configura e imprime em múltiplos IPs privados | PC agente e rede local precisam estar ativos |
| USB em PCs diferentes | Instalar agente em cada PC com USB local | USB inacessível se PC hospedeiro desligar |
| USB compartilhado pelo Windows | Um agente autorizado com permissão na fila compartilhada pode imprimir | Compartilhamento, credenciais e spooler do hospedeiro devem funcionar mesmo sem login |
| Misto USB/rede/share | Múltiplos agentes, diferentes rotas e destinos por setor | Mesmo dispositivo não recebe dupla emissão por dois agentes |
| Dois agentes enxergam mesma impressora de rede | Um endpoint lógico, várias rotas candidatas, uma rota ativa por job | Não deduzir identidade física apenas pelo nome; operador confirma associação |

O mesmo PrinterEndpoint lógico pode usar rotas físicas diferentes. Não fundir impressoras descobertas por fingerprint heurística sem confirmação; servidor aplica ownership exclusivo de cada tentativa.

## Domínio aditivo (não recriar os modelos já implementados)

- **PrintAgent**: id UUID; venue_id somente após aprovação; vínculo com DeviceRegistration/estado de revogação em Access; nome amigável; instalação_id; platform=WINDOWS; versão; created/paired/last_seen/revoked; estado PENDING_PAIRING, ONLINE, STALE, OFFLINE, REVOKED derivado de heartbeat e autorização. Agente é uma máquina, não StaffSession.
- **PrintPairingRequest**: código de exibição de alta entropia (armazenar hash); proof_secret efêmero somente no instalador; solicitação não associada até aprovação; created/expiry/consumed; tentativas e rate limit; 10 min, single use; approval com ator, Venue e trilha de auditoria.
- **AgentCredential**: credencial opaca de serviço, escopo limitado a descoberta/heartbeat/claim/result das impressoras autorizadas daquele Venue; só hash no servidor; rotação e revogação imediata; sem permissão de gerência, pedidos, staff ou pagamentos. Proteção local via DPAPI (machine scope) e ACL apenas serviço/administradores.
- **DiscoveredPrinter**: observação do agente (id local estável quando disponível, nome, porta/queue, transport, metadados não secretos, driver/versão, capacidades declaradas e última detecção). Uma observação não é PrinterEndpoint nem prova física de suporte.
- **AgentPrinterRoute**: vincula PrinterEndpoint existente a PrintAgent + identificador local de instalação + transport + profile + prioridade/active flag. Rota ativa controlada centralmente e validada antes de claim. Configuração versionada/auditada (CAS).
- **PrinterProfile**: profile_id, protocol/render_mode, largura 58/80, colunas efetivas, encoding/code page, cut mode, line endings, image support, status commands. Capabilities: SUGGESTED, VERIFIED_BY_TEST ou UNSUPPORTED; detecção nunca habilita automaticamente comandos perigosos.
- **PrintAgentEvent/AgentHealth**: observações de heartbeat e eventos diagnósticos com retenção limitada; não incluem conteúdo de pedido nem tokens.

Reusar ReceiptDocument, PrinterEndpoint, StationPrinterBinding, PrintJob e PrintAttempt existentes. Migrar campos/enums de modo aditivo. Rotas de Bridge legadas LAN/CUPS/FILE continuam operacionais e isoladas durante rollout; nova autenticação não pode aceitar sessão de staff no endpoint de serviço e vice-versa.

## Fluxo de pareamento

1. Instalar EXE universal, serviço Windows com início automático e UI local pequena (sem login). Serviço gera identidade local e segredo efêmero; API devolve código legível e prazo.
2. Tela mostra código, expiração e link para **manage.rodada.bar/manage/printing**. Não obriga informar slug; slug apenas pode pré-filtrar contexto visual no site.
3. Gerente autentica pelo fluxo atual e usa print.manage. Escolhe explicitamente Venue quando tem múltiplos vínculos, digita código, confere nome/host e aprova.
4. API faz aprovação atômica, consome código apenas uma vez, grava auditoria e emite credencial de escopo restrito ao agente vinculado a esse Venue. O agente só recebe por polling autenticado com proof_secret efêmero; o código sozinho não resgata credencial.
5. Agente guarda credencial via DPAPI/ACL protegida, inicia heartbeat e inventário. Manage mostra computador, versão, impressoras detectadas e botões Testar, Configurar, Revogar.
6. Revogação invalida claims/result/heartbeat imediatamente e apaga/suspende configuração local de autenticação na próxima comunicação; reinstalação requer novo pareamento. Desparear não apaga histórico de jobs/attempts.

Mitigações: código de alta entropia, TTL 10 min, limite de tentativas/IP/instalação/usuário, confirmação contextual do PC, protection proof-of-possession, HTTPS exclusivo, proteção contra brute-force e replay, auditoria de aprovação/troca de Venue, e nenhuma credencial em URL, logs, printouts ou QR público.

## Descoberta, protocolos e transportes

Separar completamente: **documento canônico -> layout/renderização -> driver/protocol -> transporte físico -> resultado normalizado**.

### Drivers (capability-based)

1. **ESC/POS genérico**: comandos declarados por profile e previamente testados; reutilizar renderer da 015 como base (v1 segura translitera ASCII e cut OFF). Ao habilitar code page suportada, testar acentos; comandos de corte, gaveta, buzzer, QR e status são opt-in, nunca presumidos.
2. **Bematech MP-4200 TH**: primeiro profile homologável. Testar ESC/POS e ESC/Bematech *no hardware real*; implementar driver dedicado somente se testes comprovarem diferenças. Foto/modelo não certifica protocolo.
3. **WindowsDriver**: usar driver instalado + Windows Print Spooler para renderizar/gerar job (GDI/raster conforme driver e largura). Diferenciar modo EMF/GDI de **RAW**: RAW só para impressora/queue comprovadamente compatível; enviar ESC/POS arbitrário via driver gráfico é proibido.
4. **Fabricante/SDK**: novos adapters quando ESC/POS + WindowsDriver não cobrirem requisito testado.

### Transportes

- **Windows spooler local**: enumerar filas do computador acessíveis ao serviço, USB e dispositivos instalados; APIs Windows para submissão/consulta e ID local do spool. Estado SPOOL_ACCEPTED não equivale a papel.
- **Windows shared queue**: fila compartilhada via Windows Print Spooler; descobrir apenas filas acessíveis ao contexto real do serviço. Não presumir que filas instaladas só no perfil do usuário sejam visíveis a LocalSystem.
- **TCP LAN**: IP privado/endereço local autorizado + porta 9100 configurável; descoberta mDNS/WSD quando disponível, sem varredura ampla automática; DNS rebinding, redirecionamento para internet e portas arbitrárias rejeitados. Sem acesso LAN pela API Railway.
- **Serial/COM**: fora do MVP, extensível.
- **Bluetooth**: fora do MVP Windows; Android é escopo separado da 015.

Descoberta sugerida não cria jobs nem ativa rotas sem confirmação no Manage. Botão impressão de teste usa payload diagnóstico explicitamente autorizado e destinatário já vinculado; não conta como pedido.

## Roteamento e jobs

- Bindings BAR/KITCHEN continuam do PrinterEndpoint lógico; documentos de cliente podem usar destino de caixa/receipt sem vincular estação.
- AgentPrinterRoute define **quem pode entregar** o endpoint. O servidor aplica (Venue, endpoint, agent, route, config_version) em cada claim; nunca aceitar endpoint_ids arbitrários não vinculados a esse agent.
- Tentar apenas rotas com agente elegível/online e capacidade validada. Heartbeat do agente separado de saúde real da impressora; UNKNOWN é valor legítimo.
- Uma tentativa de PrintJob fica atribuída a um único agente até concluir ou expirar o lease. Em recuperação de lease após envio possivelmente iniciado, marcar DELIVERY_UNCERTAIN e **não** trocar agente automaticamente.
- Failover automático permitido apenas para falha comprovadamente **pré-envio**, mantendo a mesma intenção lógica e respeitando o fencing; no MVP preferir troca manual auditada em caso de dúvida.
- Para impressão de cozinha/bar ao confirmar pedidos, respeitar modos explicitamente configurados pela 015 (DISABLED, ON_DEMAND, AUTO_FALLBACK, OPTIONAL_MIRROR). Rodada Impressoras não cria trigger próprio. OPTIONAL_MIRROR só após habilitação deliberada por Venue e teste de produção.
- Todas as mudanças de binding/rota são CAS + auditoria; mudança durante job em voo não redireciona bytes já enviados. Retorno tardio não cria segunda impressão.

## Contrato de API proposto (paths versionados sob /printing/agents/)

- POST /pairing/start/ — sem sessão staff, limited; retorna código, proof/session e validade somente ao dispositivo solicitante.
- GET /pairing/status/ — espera aprovação com proof da instalação, nunca permite autorização com o código público.
- POST /pairing/approve/ — staff autenticado com print.manage, Venue server-side, código + confirmação do dispositivo.
- GET / — manager lista agentes e status/versão (escopo Venue).
- POST /{id}/revoke/ — gerente revoga, exige razão quando apropriado.
- POST /me/heartbeat/ — credencial de agente; versão, estado e telemetria mínima.
- PUT /me/discovery/ — catálogo declarado com versão/identidade de impressoras, validado e sanitizado.
- POST /me/claim/ — claim atômico, server-side route binding, lease/fencing; retorna payload aprovado para driver e rota.
- POST /me/jobs/{job_id}/result/ — reporta attempt_token, route e outcome normalizado; replays idempotentes.
- POST /routes/ e PATCH /routes/{id}/ — print.manage, CAS, audita vínculo/prioridade/profile; change version.
- POST /endpoints/{id}/test/ — print.manage e endpoint vinculado; teste não financeiro, não produz Order.

Nomes detalhados a confirmar na implementação para consistência com /printing/bridge/ e gateway Web já existentes. Nunca expor endpoint de claim/resposta de agente ao browser como se fosse staff-auth.

## UI e distribuição

- **rodada.bar/downloads**: Windows download, requisitos, versão, checksum SHA-256, release notes, assinatura/publicador e orientação de pareamento. Link fixo /downloads/rodada-impressoras/windows/latest resolve para release estável assinada; sem redirect a artefato mutável desconhecido.
- **Manage > Impressoras > Adicionar computador**: link para mesmo release; código de pareamento; PCs online/offline; impressoras descobertas; configurar setor/papel/profile/corte; envio de teste; erros e reimpressão.
- Mostrar separadamente: agente online, dispositivo inferido acessível, fila/spool aceitou, operador confirmou papel; nunca exibir 'Impresso' por uma simples resposta da rede.
- A UI/branding seguem design system atual, sem painel paralelo obrigatório na máquina. UI Windows expõe código, estado, logs redigidos, atualização e diagnóstico; serviço funciona sem janela aberta.
- **Windows 11 x64** alvo recomendado; Windows 10 x64 somente best effort e mediante risco de suporte/EOL explicitado. Versão exata e compatibilidade documentadas no instalador. Serviço instala/atualiza com privilégio administrativo, não requer admin para operação. Não instalar drivers de fabricantes silenciosamente.

## Build, segurança e operação

- Código em apps/printer-agent, empacotamento isolado do Django no Windows; reutilizar contratos e golden fixtures, não importar indiscriminadamente a API Django no executável.
- Python 3.12+ no desenvolvimento; artefato autocontido com dependências vendorizadas. Serviço com identidade Windows de menor privilégio viável e acesso real à fila. Instalador repetível, desinstalador limpo, logs locais limitados/sem PII.
- Workflow Windows GitHub Actions: lint + unit + build + instalação/desinstalação em VM + hash/SBOM + publicação em release. Publicação para público requer assinatura Authenticode válida, proveniência verificável e teste de antivírus/SmartScreen. Sem certificado: somente artefato de piloto explicitamente não homologado.
- Atualização controlada: canal stable, pacote íntegro/assinado, nunca executar payload remoto não verificado; concluir ou isolar tentativas em voo antes de trocar versão, rollback compatível; migrações de config reversíveis quando possível.
- Métricas: agentes por Venue, heartbeat, tentativas e estados, tempo até spool, uncertain jobs, taxa de reimpressão, versão por agente. Eventos de segurança e audit retidos conforme política.
- Sem segredo/staff PIN no log, env de processo ou argumentos; no Windows preferir DPAPI + ACL, no backend hashes de credenciais, rotação/revogação.
- Testes usam Venue/DB de teste, simulador spool/TCP e artefatos sintéticos. Nenhum job de teste usa pagamentos reais.

## Fora de escopo

- Fiscal (NFC-e/NF-e/SAT), gaveta de dinheiro e pagamento via impressora.
- Print-server no Railway com acesso direto à LAN, compartilhamento via internet, zeroconf irrestrito.
- Garantia física de papel entregue baseada só em spooler/status de rede.
- Auto-KDS fallback sem completar gate 015; geração de ticket diretamente no agente sem Order confirmado.
- Suporte universal irrestrito a qualquer impressora; compatibilidade declarada por profile e homologação.
- Android/Bluetooth; macOS/Linux agents; fila offline de novos pedidos no agente.

## Critério de liberação do piloto

Uma Bematech MP-4200 TH real (conexão ainda a investigar), um PC Windows real e uma alternativa de impressão de contingência devem passar os casos da acceptance.md, com registro do modelo/driver/firmware, bytes/test pages, erros/reconexão e aceite operacional do Aderlan. CI verde não substitui papel real.
