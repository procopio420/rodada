# Protected first-owner provisioning

Use an empty independently approved database. This is a one-time operator action,
never startup automation. No existing administrative provisioning command exists;
existing Venue/StaffMember/membership/AuditEvent contracts support this bootstrap.
Run `python manage.py shell` interactively through protected deployment access and paste
below. Do not put PINs in command arguments, environment dumps or committed files.
Enter owner-approved names/slug and operator/change reference at prompts.

```python
from getpass import getpass
from django.db import transaction
from modules.venue.models import Venue
from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.audit.models import AuditEvent
slug = input("Approved Venue slug: ").strip()
name = input("Venue name: ").strip()
identifier = input("Owner login: ").strip()
owner_name = input("Owner name: ").strip()
reference = input("Operator/change reference: ").strip()
pin = getpass("Owner PIN: ")
if pin != getpass("Confirm PIN: ") or not pin.isdigit() or not 4 <= len(pin) <= 12 or pin in {"0420", "1234", "2468", "1357"} or not reference:
    raise ValueError("Invalid private PIN or missing audit reference")
with transaction.atomic():
    if Venue.objects.filter(slug=slug).exists() or StaffMember.objects.filter(login_identifier=identifier).exists():
        raise ValueError("Existing identity: refuse bootstrap; use authenticated management")
    venue = Venue(slug=slug, name=name, guest_mutations_blocked=True)
    venue.full_clean(); venue.save()
    staff = StaffMember(display_name=owner_name, login_identifier=identifier)
    staff.set_pin(pin); staff.full_clean(); staff.save()
    VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role=StaffRole.OWNER)
    AuditEvent.objects.create(venue=venue, actor_staff=staff, event_type="access.owner_bootstrapped",
                             metadata={"provisioning_reference": reference})
del pin
```

This creates no catalog, customer, Tab, order, payment or fabricated history; restart
never resets credentials. Owner then logs in normally and configures staff, limits,
business date, stations, cash point and tables through existing authenticated management
contracts. Import only owner-approved catalog with existing `import_catalog_csv`.
Guest ordering starts blocked until QR/session acceptance. Protected operator access and
bootstrap audit reference are mandatory. Backend CLI is an administrator trust boundary.

Secure startup enables provisioning; it does not certify production hosting. Independently
verify actual HTTPS/deployed SHA, encrypted off-host backup/restore/media retention,
Android network recovery, printers, owner/accountant fiscal contingency and PSP status.
No real merchant environment was contacted for this implementation.
