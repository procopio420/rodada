from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from modules.ordering.models import Tab


class RestoreRehearsalCommandsTests(TestCase):
    def test_fixture_is_idempotent_and_verifies_cross_domain_history(self):
        output = StringIO()

        call_command("seed_restore_rehearsal", stdout=output)
        call_command("verify_restore", stdout=output)
        call_command("seed_restore_rehearsal", stdout=output)

        self.assertEqual(
            Tab.objects.filter(display_label="Restore history").count(),
            1,
        )
        self.assertIn("RESTORE VERIFIED", output.getvalue())
