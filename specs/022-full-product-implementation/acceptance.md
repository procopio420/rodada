# Aceite verificável

## Planejamento entregue

- [x] Documento versionado identifica implementação existente, gaps, sequência, dependências e PRs concretos.
- [x] Mapeamento inclui os cinco exports e todas as Specs 001–021.
- [x] Gates distinguem piloto reduzido, produto completo e produção; IA adiada e dependências externas explícitas.

## Produto — ainda não validado

- [ ] G0: contratos/fixtures e auditoria detalhada dos critérios existentes completos (R01/R02).
- [ ] G1: rollback, replay, snapshot em gap, perda de resposta, revogação e reconnect sem duplicação/vazamento.
- [ ] G2: turno piloto completo em staging/device, com múltiplas Tabs, parcial, disponibilidade concorrente, correção e fechamento conciliado.
- [ ] G3: dispatch sem medição obrigatória, provenance/correção, financeiro completo, guest/admin/gerência e provider real homologados.
- [ ] G4: carga/rede/device, segurança, backups/restore, observabilidade, treinamento e rollback ensaiados.
- [ ] Todas as superfícies passam revisão mobile-first/adjacente e checks de UI; diferenças da referência têm justificativa de domínio, sem baseline que esconda regressão.
- [ ] Todos os critérios aplicáveis das specs de domínio têm evidência datada e limites; nenhuma conclusão por scaffolding, mock ou checkbox antigo.

Evidências deverão registrar ambiente, versões, comandos/testes, fixtures e resultado. A validação documental atual não marca nenhum gate de produto como concluído.

## Aceite parcial — demo Windows

Serviços/banco anteriores preservados; PostgreSQL real dedicado e migrations/check sem drift; ASGI/dispatcher/Web acessíveis. Turno idempotente, produção, parcial, fechamento, exceção e restart com saldo conciliado. Pricing/recibos reais; UI/Android separados de script HTTP. Sem afrouxar testes/referências. GO/condicional/NO-GO com SHA e limites; NOT_RUN explícito; publicação saneada sem merge.

Resultado parcial: GO CONDICIONAL, conforme [evidência Windows](../../docs/development/demo-windows-evidence-2026-10-09.md). Não marca gates globais/físicos como concluídos.
