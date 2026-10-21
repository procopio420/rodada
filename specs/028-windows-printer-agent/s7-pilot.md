# S7 — protocolo executável de homologação (NÃO EXECUTADO)

Responsáveis externos: operador do bar + mantenedor Windows; autorização de rollout
exclusiva do proprietário. Status inicial: **NO-GO físico e de distribuição stable**.
CI testa software/VM; não representa papel, reinício físico nem antivírus do bar.

## Preparação

1. Usar Venue de homologação isolado, cardápio sintético e nenhum pagamento real.
   Não usar seed/reset na demo compartilhada ou na operação do bar.
2. Inventariar PC/Windows build/arquitetura, conta do serviço, modelo/serial/firmware,
   portas/cabos, driver/versão, largura nominal e área imprimível. Registrar foto da
   etiqueta e topologia. MP-4200 TH é candidata, não VERIFIED.
3. Registrar commit da API/Web/agente, SHA256 do setup e dependências, perfil exato,
   modo de produção deliberado e IDs dos agentes/rotas. Nunca registrar tokens/PIN,
   proof de pareamento, dados de clientes ou conteúdo de pedidos reais.
4. Confirmar impressora sob a identidade LocalService/NT SERVICE, sem sessão do
   operador. Instalar driver manualmente se necessário; não presumir fila do usuário.
5. Manter contingência KDS/browser/PDF e instalador anterior aprovado. Não ativar
   OPTIONAL_MIRROR nem AUTO_FALLBACK como efeito do teste. Começar ON_DEMAND.

## Ensaio e evidências obrigatórias

| Cenário (chave no manifesto) | Ação física | Resultado / evidência requerida |
| --- | --- | --- |
| pairing | Instalar, abrir status, aprovar código no Manage; tentar reutilizar/expirar código | Só a instalação correta recebe acesso; sem slug/PIN local; screenshot sem segredos |
| station_routing | Confirmar pedido sintético misto Bar/Cozinha, imprimir conta do Caixa | Cada setor recebe só seus itens, conta não fiscal; fotos ligadas aos job/attempt IDs; sem alteração de ledger pelo print |
| accents_width_cut | Testar açúcar/pão/limão/café, modificadores/remoções/nota longa e cópia, 58/80 apenas onde suportado | Foto com régua/largura, texto legível; REIMPRESSÃO; confirmar tabela PC860; corte apenas no perfil testado; registrar substituições `?` |
| connection_loss | Desconectar internet antes e durante envio e antes de ACK | Pré-envio comprovado pode retry; envio ambíguo vira UNCERTAIN, nenhuma segunda via automática; logs de job/tokens + papel contado |
| computer_restart | Reiniciar sem login durante tentativa; repetir em idle | Serviço inicia em sessão0; journal reconcilia sem reenviar documento; Windows Event Viewer + API + contagem física |
| printer_disconnect | Desligar/desconectar USB/LAN, retirar papel, reconectar | KDS/pedidos seguem; fila persiste; não presumir USB em outro PC; recuperação sem duplicata |
| duplicate_job | Repetir mesma intenção e resposta perdida | Um job/tentativa executável por intenção; um original físico; nova cópia só autorizada e marcada |
| two_agents | Dois PCs com rotas explicitamente associadas ao mesmo endpoint LAN, polling simultâneo | Um token de execução e um original; desautorizar A não autoriza B a repetir tentativa em voo |
| printer_replacement | Alterar fila/driver; trocar destino com job em voo | Descoberta invalida rota/attestation; gerente revisa nova fila; versão antiga da tentativa preservada; não redirecionar bytes |
| revocation | Revogar PC antes do claim e durante envio | Novos heartbeat/discovery/claims/results negados; envio em voo fica incerto se necessário; outro Venue não lê histórico |
| spooler_failure | Parar/reiniciar spooler, simular driver bloqueado/erro parcial | Diagnóstico e UNCERTAIN conservador; abort é limpeza, não prova de ausência de papel; uninstall/upgrade recusam serviço preso |
| operator_recovery | Operador segue roteiro abaixo sem comandos técnicos | Identifica PC/fila/job, confere papel, autoriza cópia só após inspeção; registrar observações e aceite |
| upgrade_rollback | Atualizar de versão aprovada distinta, falhar startup e voltar pacote aprovado | Serviço parado antes de trocar, mesmo installation_id/journal, credencial protegida, nenhum replay físico; evidência das duas versões |

Cada cenário registra PASS/FAIL/NOT_RUN, operador/data/ambiente, expectativa,
observação, job/attempt/route/version e arquivos com hash SHA256. Não converter
simulação em PHYSICAL. Cenário não aplicável requer justificativa e revisão humana;
o verificador conservador não concede aceite automático para N/A.

## Recuperação para o operador

1. Abra Gerência → Impressoras. Diferencie PC conectado, fila desconhecida/offline,
   trabalho aceito no spool e papel confirmado. Abra Rodada Impressoras para ver
   código/estado se o PC estiver desconectado.
2. Confira energia, cabo, papel e fila do Windows. Não apague ProgramData nem
   reinstale para “limpar” uma tentativa incerta. Não desconecte vários destinos
   para provocar uma troca automática.
3. Se DELIVERY_UNCERTAIN: confira papel, fila e cozinha/bar. Só então cancele ou
   autorize REIMPRESSÃO com motivo. Não gere novo pedido para obter outro papel.
4. Se fila/driver mudou: reconfigure/revise no Manage e teste o perfil físico.
   Se o serviço não para: interrompa upgrade/uninstall e solicite suporte; mantenha KDS.
5. Revogação remove autorização, não histórico. Novo pareamento após revogação
   requer procedimento administrativo seguro preservando evidência da tentativa.

## Gates de release e GO/NO-GO

- Authenticode: mantenedor com certificado de code signing assina setup e executável;
  conferir `Get-AuthenticodeSignature` = Valid, cadeia/publicador esperado, timestamp
  e SHA256 do binário exato. Assinar não prova aprovação física.
- Antivírus/SmartScreen: validar pacote final no Windows alvo, registrar versão de
  definições, resultado e fluxo de instalação. Não orientar desabilitar proteção.
- Publicação: ambos os entry points precisam resolver o mesmo artefato estável
  assinado/checksum; verificar downloads e Manage após deploy especificamente autorizado.
- GO operacional somente após todos os cenários aplicáveis com evidência real,
  contingência/rollback testados, nenhum crítico aberto e sign-off do responsável.
- Autorização do proprietário para rollout é gate separado; este PR não a concede.

Copiar `pilot/evidence-template.json` para um diretório de evidências autorizado,
preencher com fatos e arquivos redigidos, e executar:

```sh
PYTHONPATH=apps/printer-agent python -m rodada_printer_agent.pilot caminho/evidence.json
```

Exit1 / NO_GO lista lacunas. READY_FOR_SIGNOFF significa apenas completude/hashes,
nunca autenticação do depoimento, assinatura validada ou autorização de produção.
O template versionado deve continuar NOT_RUN; nunca preenchê-lo com PASS sintético.
