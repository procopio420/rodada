# E06-02 — recibo durável do rehearsal API

Reusar integralmente IntegratedAttendanceRehearsal; não duplicar sua jornada nem
reduzir assertions. Runner opcional captura IDs sintéticos antes do rollback do
TestCase e só publica JSON após resultado terminal PASS. O recibo contém SHA/tree,
versões de ambiente, Venue/Table/occupancy/Tab/Order/item/task/Charge/Payment IDs,
estados e centavos; nunca PIN, token, cookie, texto de cliente ou credenciais.

Execução permitida apenas com PostgreSQL loopback, database lógico reservado
rodada033_evidence, TEST.NAME padrão e sem OPTIONS de conexão. DiscoverRunner
cria/destroi test_rodada033_evidence; não executar contra demo/produção. Arquivo
novo obrigatório: falha não sobrescreve recibo anterior nem publica sucesso.

O workflow API conserva o teste original também na suíte completa, usa o runner
no gate dirigido e anexa JSON apenas se o passo terminar com sucesso. Artefato é
prova API/DB; não é Web/Compose, rede, PSP ou homologação física. O resultado
terminal do workflow também deve ser consultado antes de declarar aceitação.
