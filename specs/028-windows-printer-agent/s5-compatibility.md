# S5 — explicit compatibility profiles

Registry separates canonical document layout from protocol encoding and transport.
Legacy WindowsDriver (Unicode GDI) and ASCII ESC/POS retain exact v1 bytes. Add
ESC/POS PC860 (ESC t 3), with separate cut-OFF and full-cut variants. Unsupported
characters become `?` explicitly in PC860; ASCII is an explicitly selected
transliteration fallback. Widths stay 32 columns/58 mm and 48 columns/80 mm.

RAW approval applies to the selected profile, connection, encoding and cut setting;
a profile change requires renewed physical attestation in Manage. Profile names
never imply certification. Bematech MP-4200 TH remains a hardware candidate using
WindowsDriver or a physically tested generic ESC/POS profile, not a certified new
vendor protocol. QR, drawer, buzzer and status commands remain unsupported.

Only agent 0.5.0 can claim new profiles; 0.3.0 retains legacy profiles only. Unknown
profiles or unexpected controls fail before transport entry. Server and standalone
agent enforce the same bounded command envelope. Tests compare actual claim bytes
with agent validation, Portuguese accents, 58/80 layouts, explicit replacement,
cut OFF/ON and injection rejection. Physical profile matrix remains S7 NO-GO.

Manage keeps the explicit RAW toggle and exposes encoding/cut profiles only in
that mode. Changing the profile clears physical attestation; saving requires its
renewal. Synthetic integration tests verify the reset and persisted profile at
360/390/430/1280px, without claiming those clicks certify hardware.
