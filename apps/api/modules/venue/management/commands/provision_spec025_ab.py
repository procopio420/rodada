"""Safely stage two isolated Spec 025 QA tenants in a shared Railway database.

No public exposure occurs on provision; activation is a separate explicit step.
Do not use this to load transactional or payment fixtures.
"""

import os
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, connection, transaction
from django.utils import timezone

from modules.access.invalidation import AccessInvalidationType, publish_access_invalidation
from modules.access.models import (
    MembershipStatus,
    StaffMember,
    StaffRole,
    StaffSession,
    VenueStaffMembership,
)
from modules.audit.models import AuditEvent
from modules.guest_access.models import GuestSession
from modules.hospitality.models import GuestOrderingMode, Table
from modules.venue.models import Venue, VenueDomain


QA_VENUES = (
    {
        "slug": "spec025-qa-a",
        "name": "Spec025 QA A — test only",
        "host": "e2ea.rodada.bar",
        "login": "spec025-qa-a-owner",
        "env_pin": "RODADA_SPEC025_A_PIN",
    },
    {
        "slug": "spec025-qa-b",
        "name": "Spec025 QA B — test only",
        "host": "e2eb.rodada.bar",
        "login": "spec025-qa-b-owner",
        "env_pin": "RODADA_SPEC025_B_PIN",
    },
)


class Command(BaseCommand):
    help = "Read-only audit or controlled staging/activation/backout of Spec 025 QA tenants"

    def add_arguments(self, parser):
        parser.add_argument(
            "--operation", choices=("inspect", "provision", "activate", "deactivate"),
            default="inspect",
        )
        parser.add_argument(
            "--apply", action="store_true",
            help="Required for any write. Default is always dry-run.",
        )
        parser.add_argument(
            "--backup-reference", default="",
            help="Nonsecret ID of a separately verified backup (provision/activate only).",
        )
        parser.add_argument(
            "--logical-backup-verified", action="store_true",
            help="Operator attests the exact logical archive was restored and verified separately.",
        )
        parser.add_argument(
            "--edge-confirmed", action="store_true",
            help="Operator confirms both public TLS and trusted ingress were independently checked.",
        )

    def _inspect(self):
        for spec in QA_VENUES:
            venue = Venue.objects.filter(slug=spec["slug"]).first()
            alias = VenueDomain.objects.filter(hostname=spec["host"]).first()
            staff = StaffMember.objects.filter(login_identifier=spec["login"]).first()
            self.stdout.write(
                f'{spec["host"]}: venue={"present" if venue else "absent"} '
                f'domain={"active" if alias and alias.is_active else "inactive" if alias else "absent"} '
                f'verified={bool(alias and alias.is_verified)} '
                f'operator={"present" if staff else "absent"}'
            )

    @staticmethod
    def _check_protected_identity(spec, *, require_staff=True):
        # These reserved identifiers can never be claimed from another Venue.
        venue = Venue.objects.select_for_update(nowait=True, no_key=True).filter(slug=spec["slug"]).first()
        if venue and venue.name != spec["name"]:
            raise CommandError(f'REFUSE: existing QA slug has unexpected identity: {spec["slug"]}')
        alias = VenueDomain.objects.select_for_update(nowait=True, no_key=True).filter(hostname=spec["host"]).first()
        if alias and (not venue or alias.venue_id != venue.id):
            raise CommandError(f'REFUSE: hostname is already owned: {spec["host"]}')
        staff = StaffMember.objects.select_for_update(nowait=True, no_key=True).filter(
            login_identifier=spec["login"]
        ).first()
        if staff and require_staff:
            memberships = list(
                VenueStaffMembership.objects.select_for_update(nowait=True, no_key=True).filter(staff_member=staff)
            )
            if not venue or len(memberships) != 1 or memberships[0].venue_id != venue.id:
                raise CommandError(f'REFUSE: operator identifier already owned: {spec["login"]}')
            if memberships[0].role != StaffRole.MANAGER or memberships[0].status == MembershipStatus.REVOKED:
                raise CommandError(f'REFUSE: QA membership drift: {spec["login"]}')
        return venue, alias, staff

    def _check_backup(self, reference, *, logical_verified=False):
        if reference.startswith("logical-sha256:"):
            if not logical_verified or not re.fullmatch(r"logical-sha256:[0-9a-f]{64}", reference):
                raise CommandError(
                    "A verified logical backup requires its exact lowercase SHA-256 "
                    "and --logical-backup-verified after an independent restore check."
                )
            return
        if not reference.startswith("railway-backup:") or len(reference) < 24:
            raise CommandError(
                "A verified Railway backup ID must be supplied as "
                "--backup-reference railway-backup:<ID>; this command cannot verify backups."
            )

    @staticmethod
    def _lock_namespace():
        # Missing rows cannot be locked. Serialize this command's lifecycle,
        # then also validate every actual get_or_create result against outsiders.
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                ["rodada:spec025:qa-bootstrap"],
            )

    @transaction.atomic
    def _provision(self):
        self._lock_namespace()
        pins = {}
        for spec in QA_VENUES:
            value = os.environ.get(spec["env_pin"], "")
            if not 6 <= len(value) <= 12 or not value.isascii() or not value.isdecimal():
                raise CommandError(
                    f'{spec["env_pin"]} must be a private 6-12 digit PIN (not printed).'
                )
            pins[spec["slug"]] = value
        if len(set(pins.values())) != len(QA_VENUES):
            raise CommandError("QA PINs must be distinct (values are not printed).")

        # Preflight both identities before creating any row.
        for spec in QA_VENUES:
            self._check_protected_identity(spec)

        for spec in QA_VENUES:
            venue, created = Venue.objects.select_for_update(nowait=True, no_key=True).get_or_create(
                slug=spec["slug"],
                defaults={"name": spec["name"], "guest_mutations_blocked": True},
            )
            if venue.name != spec["name"]:
                raise CommandError(f'REFUSE: existing QA slug has unexpected identity: {spec["slug"]}')
            alias, _ = VenueDomain.objects.get_or_create(
                hostname=spec["host"],
                defaults={
                    "venue": venue, "is_active": False, "is_verified": False,
                },
            )
            if alias.venue_id != venue.id:
                raise CommandError(f'REFUSE: hostname reassigned: {spec["host"]}')
            staff, new_staff = StaffMember.objects.select_for_update(nowait=True, no_key=True).get_or_create(
                login_identifier=spec["login"],
                defaults={"display_name": "Spec025 QA Operator"},
            )
            if new_staff:
                staff.set_pin(pins[spec["slug"]])
                staff.save(update_fields=["pin_hash"])
            else:
                # A competing non-bootstrap transaction may have claimed this
                # login after preflight. Never adopt it or grant a new membership.
                self._check_protected_identity(spec)
            VenueStaffMembership.objects.get_or_create(
                venue=venue, staff_member=staff,
                defaults={"role": StaffRole.MANAGER, "status": MembershipStatus.SUSPENDED},
            )
            Table.objects.get_or_create(
                venue=venue, label="QA 01",
                defaults={"guest_ordering_mode": GuestOrderingMode.DISABLED},
            )
            if created:
                AuditEvent.objects.create(
                    venue=venue,
                    event_type="qa.spec025_provisioned",
                    entity_type="Venue",
                    entity_id=str(venue.id),
                    metadata={"hostname": spec["host"], "purpose": "isolation-qa"},
                )
        self.stdout.write(self.style.SUCCESS(
            "QA venues provisioned; existing state preserved. New domains are "
            "inactive/unverified, new managers suspended and new guest access blocked. "
            "No payment facts were generated."
        ))
        self._inspect()

    @transaction.atomic
    def _set_active(self, active):
        self._lock_namespace()
        # Nothing is created or reassigned in activate/deactivate.
        for spec in QA_VENUES:
            venue, alias, staff = self._check_protected_identity(
                spec, require_staff=active,
            )
            if not venue or not alias:
                raise CommandError(f'REFUSE: QA venue is not provisioned: {spec["slug"]}')
            if active and (
                not staff or not VenueStaffMembership.objects.filter(
                    venue=venue, staff_member=staff, role=StaffRole.MANAGER,
                    status__in=(MembershipStatus.ACTIVE, MembershipStatus.SUSPENDED),
                ).exists()
            ):
                raise CommandError(f'REFUSE: QA manager not active: {spec["slug"]}')

        for spec in QA_VENUES:
            venue = Venue.objects.get(slug=spec["slug"])
            alias = VenueDomain.objects.get(hostname=spec["host"])
            updates = []
            if alias.is_active != active:
                alias.is_active = active
                updates.append("is_active")
            if active and not alias.is_verified:
                alias.is_verified = True
                updates.append("is_verified")
            if updates:
                alias.save(update_fields=updates + ["updated_at"])
                AuditEvent.objects.create(
                    venue=venue,
                    event_type="qa.spec025_domain_activated" if active
                    else "qa.spec025_domain_deactivated",
                    entity_type="VenueDomain",
                    entity_id=str(alias.id),
                    metadata={"hostname": spec["host"]},
                )
            members = VenueStaffMembership.objects.select_for_update(nowait=True, no_key=True).filter(venue=venue)
            if active:
                # Reactivation is deliberately narrow: other suspended operators
                # require a separate, explicit access-management decision.
                members = members.filter(staff_member__login_identifier=spec["login"])
            # Aliases are stopped first even if membership was already suspended.
            for member in members.exclude(status=MembershipStatus.REVOKED):
                desired = MembershipStatus.ACTIVE if active else MembershipStatus.SUSPENDED
                if member.status != desired:
                    member.status = desired
                    member.version += 1
                    member.save(update_fields=["status", "version"])
                    publish_access_invalidation(
                        staff_member_id=member.staff_member_id, venue_id=venue.id,
                        event_type=AccessInvalidationType.MEMBERSHIP_CHANGED,
                        reason="Spec025 QA activation" if active else "Spec025 QA containment",
                    )
            if not active:
                if not venue.guest_mutations_blocked:
                    venue.guest_mutations_blocked = True
                    venue.guest_policy_version += 1
                    venue.save(update_fields=["guest_mutations_blocked", "guest_policy_version"])
                GuestSession.objects.filter(
                    table__venue=venue, revoked_at__isnull=True
                ).update(
                    revoked_at=timezone.now(), revoked_reason="Spec025 QA containment",
                )
                for session in StaffSession.objects.select_for_update(nowait=True, no_key=True).filter(
                    venue=venue, revoked_at__isnull=True
                ):
                    session.revoked_at = timezone.now()
                    session.revocation_reason = "Spec025 QA containment"
                    session.save(update_fields=["revoked_at", "revocation_reason"])
                    publish_access_invalidation(
                        session=session, event_type=AccessInvalidationType.SESSION_REVOKED,
                        reason="Spec025 QA containment",
                    )
        self.stdout.write(self.style.SUCCESS(
            "QA aliases ACTIVE (guest operations remain blocked until separately approved)" if active
            else "QA aliases disabled; QA memberships suspended; sessions revoked"
        ))

    def handle(self, *args, **options):
        operation = options["operation"]
        if operation == "inspect" or not options["apply"]:
            self._inspect()
            if operation != "inspect":
                self.stdout.write(f"DRY RUN: operation {operation} not executed")
            return

        if operation in ("provision", "activate"):
            self._check_backup(
                options["backup_reference"], logical_verified=options["logical_backup_verified"],
            )
        if operation == "activate" and not options["edge_confirmed"]:
            raise CommandError("Activation requires --edge-confirmed after real TLS/ingress proof.")

        try:
            if operation == "provision":
                self._provision()
            elif operation == "activate":
                self._set_active(True)
            elif operation == "deactivate":
                self._set_active(False)
        except OperationalError as error:
            # Auth may lock session/membership before identity rows. Never wait
            # in the opposite order or SKIP LOCKED and report partial containment.
            # The inner atomic operation has fully rolled back before this error.
            if getattr(error.__cause__, "sqlstate", None) == "55P03":
                raise CommandError(
                    "REFUSE: QA access operation in progress; no changes committed. "
                    "Retry after it completes; containment has NOT succeeded."
                ) from None
            raise
