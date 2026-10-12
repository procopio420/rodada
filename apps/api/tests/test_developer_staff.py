from django.test import override_settings
from modules.access.models import StaffMember, StaffSession, VenueStaffMembership
from modules.audit.models import AuditEvent
from tests.test_access_management import AccessManagementAPITests


@override_settings(RODADA_DEVELOPER_TOOLS=True)
class DeveloperStaffTests(AccessManagementAPITests):
    def payload(self, **changes):
        return {"display_name": "Test operator", "login_identifier": "new.operator",
                "pin": "7319", "role": "STAFF", "idempotency_key": "test-create-one", **changes}

    def create(self, **changes):
        self.reauth_owner()
        return self.client.post("/developer/staff/", self.payload(**changes), format="json")

    @override_settings(RODADA_DEVELOPER_TOOLS=False)
    def test_disabled_by_default_even_for_owner(self):
        response=self.create()
        assert response.status_code == 403
        assert response.json()["code"] == "DEVELOPER_TOOLS_DISABLED"
        assert not StaffMember.objects.filter(login_identifier="new.operator").exists()

    def test_recent_pin_required_and_manager_cannot_provision(self):
        self.bearer(self.owner_tokens["access_token"])
        assert self.client.post("/developer/staff/", self.payload(), format="json").json()["code"] == "REAUTH_REQUIRED"
        tokens=self.client.post("/auth/login/", {"venue_slug":self.venue.slug,"login_identifier":self.manager.login_identifier,"pin":"2222","installation_id":"manager-dev-test","platform":"WEB"},format="json").json()
        self.bearer(tokens["access_token"])
        assert self.client.get("/developer/staff/").status_code == 403
        assert self.client.post("/developer/staff/",self.payload(),format="json").status_code == 403

    def test_normalized_login_idempotency_secrets_and_real_login(self):
        first=self.create(login_identifier="NEW.Operator")
        assert first.status_code == 201,first.json()
        second=self.create(login_identifier="new.operator")
        assert second.status_code == 201
        assert first.json()["id"] == second.json()["id"]
        assert StaffMember.objects.filter(login_identifier="new.operator").count() == 1
        member=StaffMember.objects.get(login_identifier="new.operator")
        assert member.pin_hash != "7319" and member.check_pin("7319")
        audit=AuditEvent.objects.get(event_type="staff.developer_created")
        assert "pin" not in audit.metadata and "7319" not in str(first.json())
        assert self.create(display_name="Changed").json()["code"] == "IDEMPOTENCY_CONFLICT"
        assert self.create(idempotency_key="other-key").json()["code"] == "LOGIN_ALREADY_EXISTS"
        login=self.client.post("/auth/login/",{"venue_slug":self.venue.slug,"login_identifier":"new.operator","pin":"7319","installation_id":"new-dev-test","platform":"WEB"},format="json")
        assert login.status_code == 200,login.json()

    def test_remove_preserves_identity_and_revokes_session(self):
        created=self.create().json()
        login=self.client.post("/auth/login/",{"venue_slug":self.venue.slug,"login_identifier":"new.operator","pin":"7319","installation_id":"remove-dev-test","platform":"WEB"},format="json").json()
        self.reauth_owner()
        result=self.client.post(f'/developer/staff/{created["id"]}/', {"expected_version":created["version"]},format="json")
        assert result.status_code == 200 and result.json()["status"] == "REVOKED"
        assert StaffMember.objects.filter(login_identifier="new.operator").exists()
        assert StaffSession.objects.filter(membership_id=created["id"],revoked_at__isnull=False).exists()
        self.bearer(login["access_token"])
        assert self.client.get("/auth/me/").status_code in (401,403)

    def test_self_removal_and_stale_version_are_rejected(self):
        self.reauth_owner()
        own=self.client.post(f'/developer/staff/{self.owner_membership.pk}/',{"expected_version":1},format="json")
        assert own.json()["code"] == "SELF_REMOVAL_FORBIDDEN"
        created=self.create().json()
        stale=self.client.post(f'/developer/staff/{created["id"]}/',{"expected_version":99},format="json")
        assert stale.json()["code"] == "VERSION_CONFLICT"

    def test_last_owner_and_venue_isolation(self):
        from modules.access.services import update_membership_admin, AccessServiceError
        # Service invariant also applies if a non-OWNER has an explicit admin capability.
        manager_session=StaffSession.objects.create(venue=self.venue,staff_member=self.manager,membership=self.manager_membership,expires_at=self.owner.sessions.first().expires_at)
        try:
            update_membership_admin(actor_session=manager_session,membership_id=self.owner_membership.pk,expected_version=1,status="REVOKED")
            assert False,"Last owner removed"
        except AccessServiceError as exc:
            assert exc.code == "LAST_OWNER_REQUIRED"
        outsider=VenueStaffMembership.objects.create(venue=self.other_venue,staff_member=self.staff)
        self.reauth_owner()
        assert self.client.post(f'/developer/staff/{outsider.pk}/',{"expected_version":1},format="json").status_code == 404
        assert str(outsider.pk) not in str(self.client.get("/developer/staff/").json())
