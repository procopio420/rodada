from django.test import Client, TestCase


class HealthTests(TestCase):
    def test_health_does_not_require_database_state(self):
        response = Client().get("/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_readiness_checks_database(self):
        response = Client().get("/ready/")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}
