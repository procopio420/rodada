# ADR 0012 — Calendário operacional e leitura dos relatórios

Status: aceito. Data: 2026-10-08. Spec: [020](../../specs/020-web-operational-completion/spec.md).

## Decisão

Venue possui timezone IANA e hora de corte 0–23. Default de aplicação e banco 0 mantém compatibilidade, inclusive com inserções usando modelos históricos durante migrações. Business date é a data local após descontar a hora de corte; limites do intervalo usam o calendário local, respeitando horário de verão.

Caixa obtém a data no servidor quando o cliente não a informa. Turnos existentes mantêm sua data registrada. Mudança da política exige `venue.configure` e evento de auditoria com ator, horário, antes/depois. Ela reclassifica fatos nas consultas de relatório, sem reescrever turnos ou fatos financeiros.

Relatórios são leituras reconstruíveis dos modelos canônicos, sem tabelas de totais paralelas. Valores são inteiros em centavos. Somente pagamentos e estornos confirmados entram no recebimento; datas são de confirmação. Ajustes e vendas são separados, nomes de produtos vêm do snapshot. Exposição atual soma o valor positivo por Tab e é explicitamente distinguida do período histórico. Consultas simultâneas podem observar momentos diferentes; não há promessa de fotografia transacional ou projeção assíncrona nesta slice.

CSV deriva da mesma resposta exibida, explicita centavos e protege texto contra fórmulas. Falha de leitura mantém informação anterior sinalizada, sem substituir por zeros. Analytics avançado, métricas inferidas, fiscal e integração contábil precisam de suas specs próprias.
