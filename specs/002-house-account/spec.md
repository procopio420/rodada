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

## Fora de escopo

- score externo;
- reputação entre estabelecimentos;
- promoção automática de relationship;
- cobrança automática;
- pré-autorização.
