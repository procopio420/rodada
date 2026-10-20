# S1a — entrada Gestão, 2026-10-19

## Escopo e baseline

Base documental `da644241efc6200da2cf5ebb68a32828393456b3`, produto herdado de
`e82d36c453d44c861b26f104afa39bcc8706814d`. Branch `codex/management-ux-gestao`.
Primeira implementação da Spec034: somente entrada `/manage#gestao`.

Componente `management-settings.tsx` mantém três grupos e cinco destinos com
linhas descritivas, ícones existentes, nome/descrição acessíveis e chevron.
CSS escopado compacta utilitários apenas em Gestão. DeveloperLink conserva seu
gate e destino. Nenhum endpoint, auth, money, cache ou mecanismo de conexão alterado.

Baseline determinístico: quatro testes `management task groups` PASS, capturando
cinco áreas em360/390/430/1280. Capturas antes preservadas antes da alteração.
Fixture de navegador existente, com tempo congelado e respostas controladas;
o estado de reconexão capturado não é alegação sobre servidor real.

## Verificações executadas e limites

- Build Next/webpack PASS; TypeScript do build e `tsc --noEmit` PASS.
- ESLint dos três arquivos TSX/teste alterados PASS.
- Primeira execução dirigida:18/18 testes de navegação/estados PASS, incluindo
  quatro novos casos com descrição acessível, alvo44px, teclado, axe, zoom200%
  e nenhuma mutation de API ao navegar pela entrada. Ajuste visual posterior
  apenas compacta a largura do Atualizar e retira foco artificial da captura;
  exige reexecução dirigida final antes de declarar o SHA completo validado.
- Navegador real conectado à API local: Gestão mostra Ao vivo; abrir Impressoras
  e retornar à Gestão executado sem gravações. Nenhum ensaio de impressão física.
- Suíte visual ampla iniciada com limite de cinco falhas para diagnóstico:
  falhas em `attendance-catalog.spec.ts`, fora dos arquivos/produto alterados.
  Resultado final e execução dirigida final devem ser acrescentados abaixo.

Revalidação intermediária após compactar o header:10 PASS/8 FAIL. Os oito
casos detectaram alvo de histórico abaixo44px causado por `width:auto` sobre o
botão de ícone. Correção: mínimo `--touch-min` no escopo dos utilitários de Gestão;
assertions foram preservadas. Essa execução não conta como PASS e fica registrada.

Suíte ampla:8 PASS/5 FAIL/676 NOT_RUN, interrompida por `--max-failures=5` em1,2min.
Quatro falhas procuram seletor legado “Outras comandas” em attendance-catalog;
uma mede28px em “Detalhes” da barra de limite de Atendimento. Nenhum desses
componentes foi alterado nesta slice; não foi executada contraprova no baseline
para atribuir causalidade. Gate global FAIL/incompleto, não aprovação global.

No ambiente, npm não está no PATH; o script `test:visual` é executado pelo pnpm
disponível (mesmo `playwright test` do package.json). Build usa `next build --webpack`;
Next dev com Turbopack não aceita junction externa de dependências. Prévia usa
webpack, sem modificar configuração do projeto ou reinstalar dependências.

## Aceite parcial e riscos

Reexecução final após mínimo44px:18/18 PASS31,5s, zero retries. Build webpack
final PASS; typecheck do build PASS. `tsc --noEmit` e ESLint focado finais PASS.
KB checker PASS49documentos/298links/12skills e diff whitespace PASS.
Capturas antes/depois em [galeria](../../docs/development/evidence/spec034-gestao/README.md).

R2 visual; revisão de autoria, sem alegar revisão independente. AC01/02/04/05/10
têm evidência dirigida parcial. AC03 não concluído: retorno de rota existe, mas
restauração explícita de foco/scroll ainda não foi implementada. AC06/07/08 fora
desta slice; AC09/11/12 dependem dos registros finais e da composição/review.
Leitor de tela manual, zoom de navegador200% (distinto do zoom CSS da fixture),
dispositivo físico, subpáginas e aceite de operador NOT_RUN.

Reversão proposta limita-se a componente, JSX de entrada e CSS escopado; nenhum
dado migrado ou intenção persistida alterada. Não há aprovação de produção.
