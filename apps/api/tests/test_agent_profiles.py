"""S5 claim-to-agent byte parity and honest encoding, without paper certification."""

import base64
from unittest.mock import MagicMock

from django.test import TestCase
from rodada_printer_agent.transports import Transports

from modules.access.models import AgentCredential
from modules.documents_printing import agent_delivery
from modules.documents_printing.profiles import PROFILES, render_profile
from tests.test_agent_delivery import setup_delivery


class ProfileTests(TestCase):
    def test_profiles_widths_accents_and_control_envelope(self):
        _, _, _, agent, route, _, _, job = setup_delivery()
        agent.version = "0.5.0"
        agent.save(update_fields=["version"])
        credential = AgentCredential.objects.get(agent=agent).id
        for profile_id in PROFILES:
            for width in (58, 80):
                document = job.document
                document.snapshot["items"][0]["name"] = "Açúcar pão limão café 😀"
                content = render_profile(profile_id, document, width)
                if profile_id.startswith("escpos-pc860"):
                    assert "Açúcar pão limão café ?".encode("cp860") in content
                    assert content.endswith(b"\x1dV\x00") == profile_id.endswith("cut-v1")
                elif profile_id == "windows-driver-v1":
                    assert "Açúcar pão limão café 😀".encode() in content
                else:
                    assert b"Acucar pao limao cafe" in content
                text = content.decode("utf-8" if profile_id == "windows-driver-v1" else "cp860")
                assert max(map(len, text.splitlines()[1:-4])) <= (32 if width == 58 else 48)
        route.profile_id = "escpos-pc860-v1"
        route.save(update_fields=["profile_id"])
        claimed = agent_delivery.claim(agent, credential)["job"]
        assert claimed and claimed["profile_id"] == route.profile_id
        assert Transports(MagicMock()).prepare(claimed) == base64.b64decode(claimed["content"])

    def test_old_agent_cannot_claim_new_profile(self):
        _, _, _, agent, route, _, _, job = setup_delivery()
        route.profile_id = "escpos-pc860-v1"
        route.save(update_fields=["profile_id"])
        assert agent_delivery.claim(agent, AgentCredential.objects.get(agent=agent).id)["job"] is None
        job.refresh_from_db()
        assert job.state == "QUEUED" and job.attempt_count == 0
