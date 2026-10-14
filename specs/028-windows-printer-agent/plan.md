# Plan — Spec 028 (Rodada Impressoras Windows)

**Status:** Proposed. Plano de execução incremental; nenhuma etapa implica autorização para merge, deploy ou alteração da produção.

## Baseline real

- API Django: modules.documents_printing.models/services/views/urls, PrinterEndpoint, StationPrinterBinding, ReceiptDocument, PrintJob e PrintAttempt. Preservar dedupe por origem/estação, leases/attempt_token e estados OUTPUT_READY / SPOOL_ACCEPTED / DELIVERY_UNCERTAIN.
- Bridge atual: tools/print-bridge/bridge.py, autenticado por staff session, para FILE, LAN e CUPS. Não substituí-lo sem migração e gate.
- Web Manage já existe: apps/web/app/manage/printing/page.tsx. Expandir, não criar painel concorrente.
- Landing está em apps/landing/ (estático Nginx); acrescentar downloads.html e rota/rewrite coerente, não mover a landing para Next desnecessariamente.
- Descoberta da Bematech por foto não revela como está conectada. Hardware real ainda não foi inventariado. Ver checklist docs/development/printing-hardware-checklist.md.

## Ordem de implementação por fatias verticais

### P0 — Contratos e ADR
- Trancar invariantes da Spec 015/ADR 0013; registrar matriz de decisões em ADR da 028.
- Definir API schemas de PrintAgent, PrintPairingRequest, credentials, DiscoveredPrinter e AgentPrinterRoute; migrações aditivas.
- Evitar depender de session token humano no Windows: autenticação de dispositivo em Access com escopo estrito, validade, rotação, revogação e Venue binding.
- Criar fixtures sintéticas de jobs e perfis, SEM dados reais de clientes.

### P1 — Serviço Windows e pareamento mínimo
- Agente Python autocontido para Windows 11 x64; comando de instalação/configuração de serviço e pequeno wizard/status.
- Windows service start/stop/restart, heartbeat e códigos de ativação de uso único; armazenar token em DPAPI + ACL de serviço.
- Manager aprova em Manage com print.manage. Testar brute-force, expiração, revogação, segunda tentativa e dois Venues.
- Backend registra device e libera apenas endpoints atribuídos. Agente NÃO usa StaffSession.

### P2 — Descoberta e transporte Windows
- Enumerator de filas WinSpool visíveis à identidade do serviço; confirmar USB, filas TCP/IP e compartilhadas.
- WindowsDriver para layout não-RAW (renderizar via Windows print API com driver instalado); WinRawSpoolAdapter para ESC/POS somente quando profile/teste permitem.
- EscPos driver atual é base, com capability opt-in, ASCII conservador inicialmente. Testes reais definem necessidade de BematechDriver.
- TCP LAN permite destinos privados, com descoberta limitada; validar IP/host local e conexão antes de marcar pronto.

### P3 — Roteamento multiagente e segurança
- AgentPrinterRoute por Venue/PrinterEndpoint, com configuração versionada e prioridade; registrar associação física explícita no Manage.
- Claim de um único agente por tentativa, vinculado a endpoint/route e attempt_token. Sem multiplex de impressão por browser e agente para o mesmo job.
- Leases expirados após possível envio => DELIVERY_UNCERTAIN, não redispatch. Falha comprovada pré-envio pode retry com a mesma identidade; outra rota só após regra segura.
- Simular agent A e B com mesma impressora de rede, duplicação de heartbeat, reinstalação/revogue, host offline e job em andamento.

### P4 — UI Manage + downloads
- Manage: lista agentes, aprovar código, impressoras encontradas, setor, driver/capabilities, papel, corte, status, diagnóstico, logs mínimos e revogação.
- Apresentar estados em camadas distintas (agent online, printer health, job spool, papel confirmado).
- Landing: rodada.bar/downloads, mesma URL estável do instalador que Manage consome, checksums, versão, requisitos e instruções. Controle de cache e rollback de versão.

### P5 — Release engineering
- GitHub Actions windows runner: lint + tests + build PyInstaller (ou empacotador escolhido após spike) + instalador Inno Setup/WiX + install/uninstall smoke + artefatos/SHA256.
- Definir política de assinatura Authenticode, publicação immutable release e manifesto de atualização assinado. Nunca linkar release não assinado como stable pública.
- Auto-update segura em modo idle/quiescente, com roll-back e compatibilidade de protocolo versionada. Atualizar não pode perder jobs em voo.

### P6 — Certificação do Aderlan
- Inventário da conexão real/driver do MP-4200 TH e outros modelos, spooler local e rede do bar.
- Testes no Windows real: impressão de teste, comandas BAR/KITCHEN, acentos, observações extensas, corte se suportado, duas vias, páginas 80/58 conforme hardware, papel ausente e spooler parado.
- Rodar turno simulado completo sem pagamento real, Wi-Fi instável, PC reiniciado e duas máquinas tentando alcançar mesmo endpoint.
- Go/no-go documentado por modelo e modo; modo não certificado fica desabilitado ou com disclaimer de compatibilidade.

## Isolamento de ownership

- Backend Access: lifecycle agent credential, DeviceRegistration e pairing approval.
- Backend Documents/Printing: rotas, claims, status, renderers e reprints. Nenhum novo valor financeiro.
- Windows Agent: driver/transport, descoberta, spool e telemetria; sem decisões sobre pedidos.
- Web Manage: pairing/associação/diagnóstico e permissões; apenas rotas backend autorizadas.
- Landing: downloads de artefatos publicados e instruções.
- CI/Release: empacotamento/testes/assinatura.

## Estratégia de teste

| Gate | Critério mínimo |
| --- | --- |
| Unit | Formatação/golden 58/80, controles sanitizados, driver fallback, encoding, logs sem token |
| API | autenticacao dedicada, Venue scoping, permissions, race, replay, attempt fencing, CAS/revoke |
| Windows CI | enumerar spooler mock, worker service lifecycle, install/uninstall, RAW vs GDI, queue ACL |
| Contrato | Renderização backend -> payload agente versionado -> resultado idempotente |
| End-to-end simulado | pedido confirmado -> station endpoint -> route -> agente -> spool fake -> state SPOOL_ACCEPTED |
| Fault injection | segunda máquina, sem internet, crash antes/durante/depois do spool, token revogado, IP inválido |
| Hardware | MP-4200 TH real + documentação/fotos de conexão e saída física verificada |

## Rollout e rollback

1. Feature flag por Venue para agents e routing. Manter endpoints BROWSER/FILE/NETWORK/CUPS legados enquanto piloto valida.
2. Primeiro um agente com impressora de teste; só depois ativar produção ON_DEMAND em BAR/KITCHEN.
3. OPTIONAL_MIRROR não é ativado por esta spec; requer decisão explícita do estabelecimento e fluxo comprovado.
4. Desativar flag/agente não remove documentos, jobs, reprints ou auditoria; preservar recuperação e fallback browser/PDF.
5. Revogação de agente faz sistema parar novos claims; jobs em voo ficam incertos se há chance de papel.
6. Registrar versão exata do commit, instalador, SHA e evidência física no piloto.

## Dependências e perguntas a responder em homologação

- Quantas impressoras existem no Aderlan? São USB, LAN ou compartilhadas?
- Driver da MP-4200 TH suporta modo RAW ESC/POS no Windows instalado? Se não, qual modo de render pela fila?
- Quais filas são visíveis ao serviço Windows sem login? Há credenciais para compartilhamento?
- Produção desejada: tickets automáticos OPTIONAL_MIRROR por estação ou somente ON_DEMAND inicialmente?
- Tipo de largura/corte/papel e capacidade de status real de cada impressora?
