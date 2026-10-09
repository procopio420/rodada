# ADR 0015 — Coordenação de refresh da sessão Web

**Status:** Accepted for the single-process demo

## Contexto

A API rotaciona access/refresh e invalida o par anterior. Leituras concorrentes do BFF após expiração reutilizavam o mesmo refresh: uma retornava200 e as demais401, apagando os cookies recém-renovados. Isso foi reproduzido com oito requests e PostgreSQL real.

## Decisão

Coordenar por digest SHA-256 do refresh em memória global do processo Web, compartilhada por route bundles. Requisições simultâneas compartilham a Promise; resultado bem-sucedido fica disponível cinco segundos para requests enviados antes do Set-Cookie. Capacidade máxima256, sem persistência/log de tokens, com remoção de resultados expirados e falhas. Refresh HTTP tem timeout10s; capacidade esgotada/indisponibilidade devolve503 preservando cookies.

Rejeição de access por expiração ou rotação permite uma renovação/retry antes de devolver erro. A API revalida cada request, inclusive após revogação; sucesso de refresh não concede autorização por si. Backend, duração de sessão, capacidades, CSRF e cookies HttpOnly/SameSite/Secure permanecem canônicos.

## Consequências e limites

Esta decisão corrige a demo Next em um único processo. Não prova coordenação de vários processos/replicas: o deployment distribuído exige uma coordenação compartilhada equivalente antes de seu aceite. A janela curta contém credenciais só em memória e não prolonga validade da API. Não se repete mutation que já recebeu sucesso nem se cria fallback permissivo.
