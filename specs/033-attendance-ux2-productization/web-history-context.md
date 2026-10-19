# E01/E06 — preserve history origin after main composition

Regression in composition02d63ae8: the history controller and main's read-only
history are retained, but the UX2 history trigger does not capture its focus or
replace the previous contextual origin. After an Agora task, closing history
can return to Agora rather than its initiating Mesas list.

Preserve the existing history action in the UX2 Mesas heading. Record that
trigger as returnFocus and explicitly set its origin to the Mesas list; clear
the preceding task's navigation provenance. Do not claim/complete tasks or
change Tab, Order, ledger, authentication or payment behavior.

Regression proof: Agora task → table choice → Back → Mesas → History → inspect
closed Tab → Back, at360/390/430px. Return to Mesas, restore trigger focus, retain
read-only detail/no close action, zero non-GET requests. Migrate the existing
three history tests without removing their previous assertions. Browser fixtures
prove navigation/accessibility only, not integrated financial or global acceptance.
