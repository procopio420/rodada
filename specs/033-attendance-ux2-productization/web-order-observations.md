# E06-05 — observador Web de confirmação

Recorte cliente do contrato `client-observations.md` (PR297). Sem UI nova.
Instrumentar somente pedidos Attendance UX2: intenção depois de sessionStorage
verificado e resultado da tentativa lógica; CONFIRMED depois do readback exato.
Mesmo UUID/payload/guards/retirada da intenção e mensagens de erro. Recuperação
usa hash da intenção original e UUID novo de tentativa; duração monotônica não
atravessa reload. POS legado não recebe versão UX2 artificial.

Transporte independente: no máximo oito observações em andamento, sem fila
persistida, retry ou await de venda; hash SHA256 assíncrono, prazo1500ms. Falhas
são descartadas. BFF dedicado com destino fixo, CSRF e origem assinada existentes,
body limitado8KiB, somente access cookie atual: nunca refresh/set/clear cookie.
Backend exige Venue/sessão original; trocar cookie não reatribui observação.
Testar endpoint quebrado, replay, readback ausente, schema emitido sem payload,
CSRF, ausência/expiração de acesso e inexistência de refresh em background.
