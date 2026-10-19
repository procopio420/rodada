# E06-06 — histórico nativo por geração de sessão

Baseline composição bc07c3f6. `loadTabHistory` compara somente a chave de sessão capturada com a chave atual; A→B→A volta a satisfazer essa igualdade e permite que sucesso/falha antigos encerrem o carregamento do histórico atual. Um caller com sessão diferente da carregada também pode começar a leitura e publicar sob a chave capturada.

Reutilizar `FinancialResponseFence` e `sessionActionGuard` da slice PR256, com validação antes/depois do I/O e da publicação. Sessão diferente não inicia transporte nem busy; A→B/A→B→A invalida a resposta antiga, preservando a leitura atual. História continua sob demanda e somente leitura; não alterar catálogo, paginação, permissões de reabertura, saldo ou backend.

Aceite desta regressão: callbacks sucesso/falha antigos não alteram histórico/erro/loading após troca de sessão; leitura atual termina normalmente. JVM da fronteira não substitui ensaio ViewModel/API real com leituras suspensas. Nenhum AC global fechado sem evidências e revisão R3 independente. Integração financeira em main e outros tipos de callback seguem gates próprios.
