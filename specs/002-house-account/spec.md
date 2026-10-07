# Spec 002 — Conta da Casa

**Status:** Draft

## Objetivo

Adicionar identidade, relacionamento e política de exposição ao Core POS.

## Histórias

- buscar/criar Customer rapidamente;
- definir Relationship `VISITOR | KNOWN | REGULAR | HOUSE | RESTRICTED`;
- herdar operating limit ao abrir Tab;
- mostrar exposure e percentual utilizado;
- mover Tab para `REQUIRES_ACTION` ao atingir limite;
- receber parcial sem fechar Tab;
- permitir override temporário de limite por manager;
- manter histórico entre visitas;
- alterar Relationship sem retroagir tabs abertas.

## Política demo

| Relationship | Limite |
|---|---:|
| Visitor | R$ 30 |
| Known | R$ 80 |
| Regular | R$ 200 |
| House | R$ 500 |
| Restricted | R$ 0 |

## Regras de operação

- o limite é capturado na abertura da Tab e não muda se o Relationship mudar depois;
- Tab anônima herda a política `VISITOR` do Venue;
- confirmar consumo que faça a exposição atingir ou ultrapassar o limite é permitido, mas move a Tab para `REQUIRES_ACTION`;
- `REQUIRES_ACTION` bloqueia novos pedidos até pagamento reduzir a exposição abaixo do limite ou manager conceder override;
- pagamento parcial abaixo do limite devolve a Tab para `OPEN`, sem fechá-la;
- override é temporário na Tab, exige manager/owner e registra ator, valor anterior, valor novo, horário e motivo opcional;
- limites e valores financeiros são inteiros em centavos.

## Fora de escopo

- score externo;
- reputação entre estabelecimentos;
- promoção automática de relationship;
- cobrança automática;
- pré-autorização.
