# E04/E06 — Liberação vinculada à ocupação confirmada

Contrato obrigatório da API: POST /hospitality/tables/{tableId}/release/
com expected_occupancy_id UUID e expected_generation inteiro positivo.
Ausente/parcial400; ocupação substituída409 STALE_OCCUPANCY, sem mutação.

TablesScreen já capturava ID/generation ao abrir a confirmação, mas o cliente
HTTP enviava objeto vazio. Agora um TableReleaseTarget imutável transporta esses
valores da confirmação por ViewModel/repository até o HTTP. Não reconsulta uma
ocupação B para preencher uma operação confirmada em A; não há fallback legado.
A guarda visual de ocupação, permissões, comandas abertas e entregas continua.

Depende da slice API ebd22333 (precondições obrigatórias). Não aceitar deploy
se o backend canônico ainda não fornece esse contrato. Revisão R3, testes
JVM/Compose e resposta canônica permanecem gates até evidência anexada.
