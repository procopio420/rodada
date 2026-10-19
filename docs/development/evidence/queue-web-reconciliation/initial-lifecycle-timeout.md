# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - alert [ref=e2]
  - main [ref=e3]:
    - generic [ref=e4]:
      - img "Rodada" [ref=e5]
      - button "Opções do atendimento" [disabled] [ref=e6] [cursor=pointer]:
        - generic [ref=e7]: Web E2E — test only
        - generic [ref=e8]: test-manager
    - article [ref=e12]:
      - region "Mesa Attendance test" [ref=e13]:
        - button "Voltar" [disabled] [ref=e14]:
          - generic [ref=e15]: ‹
          - text: Voltar
        - generic [ref=e16]: Salão
        - generic [ref=e17]:
          - heading "Mesa Attendance test" [level=1] [ref=e18]
          - generic [ref=e19]: 0 aberta(s)
        - paragraph [ref=e20]: Ocupada
        - status [ref=e21]: Operação confirmada.
        - heading "Comandas desta mesa" [level=2] [ref=e23]
        - paragraph [ref=e24]: Nenhuma comanda ativa nesta ocupação.
        - heading "Saída do grupo" [level=2] [ref=e26]
        - button "Grupo saiu · Liberar mesa" [disabled] [ref=e27] [cursor=pointer]
        - paragraph [ref=e28]: A mesa passará para Aguardando limpeza e o QR desta ocupação perderá o acesso.
        - button "＋ Abrir nova comanda" [disabled] [ref=e29] [cursor=pointer]
        - group [ref=e30]:
          - generic "Opções da mesa" [ref=e31] [cursor=pointer]
          - generic [ref=e32]:
            - paragraph [ref=e33]: Sem responsável
            - button "Assumir atendimento" [disabled] [ref=e34]
          - button "Organizar mesa Attendance test" [disabled] [ref=e35]
```