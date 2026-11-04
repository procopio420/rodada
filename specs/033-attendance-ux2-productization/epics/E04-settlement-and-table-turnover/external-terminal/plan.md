# Plano — terminal externo Web

Base: 7d4168376c386e07e7387de3d34de2fa4294bd77; branch codex/pilot-stage3-external-card.

1. Contrato/aceite antes do código; reusar PosCashReceipt e endpoint financeiro.
2. Schema3 discriminado EXTERNAL_TERMINAL sem caixa; preservar CASH schema1/2.
3. BFF valida por método; UI usa seleção e confirmação externa explícita.
4. Integração PostgreSQL: parcial/integral, misto CASH, lost ACK/readback,
   reload, mudança de sessão, capability negada e métodos/campos proibidos.
5. Visual completo, responsive/a11y 360/390/430; build/types/auth/tenant;
   revisão independente R3 com diff e SHA. Evidência sanitizada, NO-GO produção.
