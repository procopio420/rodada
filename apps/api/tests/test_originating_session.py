from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from modules.access.models import StaffSession
from tests import test_access_api as fixture_module


class OriginatingSessionTests(TestCase):
    def setUp(self):
        fixture = fixture_module.StaffAuthAPITests()
        fixture.setUp()
        self.fixture = fixture
        self.client = fixture.client

    def test_same_session_accepts_provenance_and_new_session_cannot_adopt(self):
        original = self.fixture.login()
        replacement = self.fixture.login(installation_id="replacement-device")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {replacement['access_token']}",
            HTTP_X_RODADA_ORIGINATING_SESSION=original["session_id"])
        response = self.client.post("/tabs/", {"display_label": "must not exist"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "RECOVERY_SESSION_CHANGED")
        from modules.ordering.models import Tab
        self.assertFalse(Tab.objects.exists())
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {replacement['access_token']}",
            HTTP_X_RODADA_ORIGINATING_SESSION=replacement["session_id"])
        self.assertEqual(self.client.post("/tabs/", {"display_label": "authorized"}, format="json").status_code, 201)

    def test_revoked_or_expired_original_session_rejects_mutation(self):
        for expired in (False, True):
            original = self.fixture.login(installation_id=f"original-{expired}")
            session = StaffSession.objects.get(pk=original["session_id"])
            if expired:
                session.expires_at = timezone.now() - timedelta(seconds=1)
            else:
                session.revoked_at = timezone.now()
            session.save()
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {original['access_token']}",
                HTTP_X_RODADA_ORIGINATING_SESSION=original["session_id"])
            response = self.client.post("/tabs/", {"display_label": "rejected"}, format="json")
            self.assertEqual(response.status_code, 401)
        from modules.ordering.models import Tab
        self.assertFalse(Tab.objects.exists())
