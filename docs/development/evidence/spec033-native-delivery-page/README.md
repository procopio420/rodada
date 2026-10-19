# E03 / E06 — página de entrega nativa

Produto fe7bf025 + bb136adb, ajuste visual final74643eb6. Base PR244 db62c7f9. Antes a entrega abria AlertDialog; agora é página Compose sob o header, com Back, contexto canônico, item/quantidade/estação, estado real e CTA explícita fixa no rodapé. Abrir e voltar não concluem nem assumem. PICKED_UP e READY seguem estados do backend; rival/ausência/estado alterado impedem ação indevida.

Capturas de referência: PR212 ec26e26b, viewDelivery, copiadas/inspecionadas no pacote Web docs/development/evidence/spec033-web-delivery-page. Fixtures pareadas Rafael/#1049/Mesa08/2Chopp na matriz Compose são visuais, não transações financeiras. Os dados reais continuam sendo lidos da API.

Fonte final74643eb6 corrige linha divisória adicional e título30sp em360dp conforme protótipo. Assemble/compilação da instrumentação PASS47s. JVM120/120 e lint final PASS3min. Matriz final **36 checks PASS**, 6 casos×360/390/430×fontes1/2, seis PNGs e logs adjacentes. Estado de tela preservado nos testes de abertura/Back, rival, tarefa ausente, produção alterada, operação ocupada e PICKED_UP. Nenhum teste sintético é apresentado como E2E real.

Revisão independente root do produto escrito por finish_native_required_release: achado P2 de estado de produção inferido pelo estado da tarefa corrigido com item_state canônico. Sem outro achado reproduzível no escopo examinado. Ajuste visual final74643eb6 pelo integrador recebeu SELF_REVIEW; comparação completa e nova revisão independente permanecem gates.

Jornada MainActivity com entrega em Tab CLOSED ainda NOT_ACCEPTED neste pacote: após retomada o emulador mostrou System UI ANR; reboot preservando dados em andamento. Não usar esses36 testes como prova de integração real. Motor de recuperação mantém lacunas registradas no spec android-delivery-page.md, corrigidas separadamente em86162c01/fc8d4c6b, que exige composição. Backend depende#218/#226 e contrato242. Aceite global, paridade final, TalkBack, aparelho físico e revisão GitHub continuam pendentes. Sem merge/deploy.
