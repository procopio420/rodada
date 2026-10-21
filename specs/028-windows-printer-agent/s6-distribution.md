# S6 — distribution implementation, public release blocked

One universal Windows x64 installer bundles Python and pywin32 with PyInstaller.
Inno Setup installs per-machine under Program Files, provisions LocalService +
service SID, autostart and DPAPI, and adds the optional status UI shortcut. No
slug or manager password. Setup stops the service before replacing binaries;
upgrades/repair preserve protected identity and pending result journal. Uninstall
stops/removes service and binaries but retains protected state for recovery.

The CI artifact is explicitly UNSIGNED PILOT, never a public stable release.
CI must build, install, start in session 0, stop, reinstall preserving identity,
and uninstall. Generate checksums and dependency inventory for the artifact.
Signing, antivirus/SmartScreen, actual Windows reboot, rollback across distinct
versions and hardware remain external gates. No unattended downloader executes
an unverified update; controlled manual upgrade only until those gates pass.

Public /downloads and Manage both reference the canonical
https://rodada.bar/downloads/rodada-impressoras/windows/latest. While no signed,
hardware-approved stable artifact exists that URL returns 503, and the page
explains unavailability instead of presenting an unsigned executable as stable.
The release manifest records availability=false. Future stable publication must
atomically replace manifest + immutable signed artifact after owner authorization.
This implementation does not publish, deploy or enable a Venue.

## Test page contract

Manager-only POST /printing/endpoints/{id}/test/ with a UUID idempotency key creates
an immutable DIAGNOSTIC_TEST document through the existing PrintJob queue. It
creates no Tab, Order, charge or payment. ReceiptDocument permits null Tab ONLY
for this diagnostic kind via a database constraint; all customer/production
receipt documents continue to require their existing Tab. Test text clearly says
TESTE / NÃO PREPARAR and exercises Portuguese accents. Venue isolation, enabled
assigned routes, existing claim/fencing/result semantics and job audit apply.
Manage preserves the test key after response loss. Reverse migration requires
retaining diagnostic history (export/forward fix); null diagnostic documents must
not be silently attached to a customer Tab merely to downgrade the schema.
