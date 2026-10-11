# Aceite
- [x] Agora não monta formulários de clientes ou ícones; detalhes sob Ver mais.
- [x] Cinco seções selecionáveis por link/hash, voltar/avançar; ações e retornos.
- [x] DEV indisponível sem flag; não autorizado recebe 403; Venue isolado.
- [x] Criação com PIN hash, replay idêntico único, payload diferente 409.
- [x] Remoção revoga acesso sem apagar histórico; própria conta/último OWNER protegidos.
- [x] UI não confirma mutation ambígua; mantém intenção/chave e reconsulta conflito.
- [x] Backup local legível e auditoria; zero Tabs abertas e filas antigas após limpeza.
- [x] Nenhum Payment novo/alterado pela limpeza; Products não alteram snapshots/preços.
- [x] Build/types, npm run test:visual e integração PostgreSQL aprovados.


Evidência local em 11/10/2026: API273fc83/Web2d932b3; build/TypeScript,
36 testes API/PostgreSQL, 209 testes visuais e 15 jornadas Web/API/PostgreSQL.
Web padrão sem flag: status false, página404, gateway403. Releitura da demo após
reinício confirmou zero comandas/filas abertas e igualdade dos 16 Payments.
Relatórios/logs em visual-artifacts/demo-functional/runtime/pilot-*.log e
apps/web/playwright-report/. Nenhuma baseline/tolerância alterada.

### Attendance refinement
- Opening a Tab presents the ordering workflow before its bill. Original subtotal is visible; financial details require Mais detalhes and retain exact cent values.
- Category filters and global accent-insensitive search preserve drafts and mandatory choices; unavailable items cannot be added.
- Unrecognized products remain discoverable; inactive items are absent from Attendance.
- POS retains its full financial summary. Responsive 360/390/430 checks and visual suite pass without baseline relaxation.

Attendance refinement evidence: production build/TypeScript passed; 213 visual cases passed without baseline relaxation, including 360/390/430 category/search/cart/bill tests; real PostgreSQL Attendance order-production-delivery-table lifecycle passed. Search normalization was additionally checked for accents and numeric units. No database/product/payment mutation was introduced.
