import io
import tempfile

from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from modules.access.models import StaffMember, VenueStaffMembership
from modules.catalog.models import IconGeneration, Product, ProductIcon
from modules.catalog.services import run_icon_job
from modules.ordering.models import Tab
from modules.venue.models import Venue


class IconClosureTests(TestCase):
    @override_settings(
        RODADA_ICON_PROVIDER="http", RODADA_ICON_PROVIDER_URL="", RODADA_ICON_PROVIDER_KEY=""
    )
    def test_real_unconfigured_provider_exhausts_bounded_retries_without_blocking_orders(self):
        venue = Venue.objects.create(name="Icon test", slug="icon-closure")
        staff = StaffMember.objects.create(display_name="Manager", login_identifier="icon-closure")
        staff.set_pin("2468")
        staff.save()
        VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role="MANAGER")
        client = APIClient()
        login = client.post(
            "/auth/login/",
            {
                "venue_slug": venue.slug,
                "login_identifier": staff.login_identifier,
                "pin": "2468",
                "installation_id": "icon-test",
                "platform": "WEB",
            },
            format="json",
        )
        assert login.status_code == 200
        client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        created = client.post(
            "/catalog/resolve-or-create/",
            {
                "name": "Omelette",
                "price_cents": 900,
                "fulfillment_station": "KITCHEN",
            },
            format="json",
        )
        assert created.status_code == 201
        product = Product.objects.get()
        icon_id = product.icon.pk
        job_id = IconGeneration.objects.get().pk
        for _ in range(3):
            IconGeneration.objects.update(available_at=timezone.now())
            assert run_icon_job()
        assert not run_icon_job()
        product.refresh_from_db()
        job = IconGeneration.objects.get()
        assert job.pk == job_id and job.attempts == 3 and job.status == "FAILED"
        assert product.icon.status == "FAILED"
        assert product.active and product.availability.state == "AVAILABLE"
        tab = Tab.objects.create(venue=venue)
        confirmed = client.post(
            f"/tabs/{tab.pk}/orders/confirm/",
            {
                "idempotency_key": "provider-unconfigured",
                "lines": [{"product_id": str(product.pk), "quantity": 1}],
            },
            format="json",
        )
        assert confirmed.status_code == 201
        assert confirmed.json()["items"][0]["unit_price_cents"] == 900
        with tempfile.TemporaryDirectory() as storage, override_settings(MEDIA_ROOT=storage):
            import base64

            buffer = io.BytesIO()
            Image.new("RGBA", (128, 128), "white").save(buffer, "PNG")
            for body in (
                {
                    "action": "upload",
                    "mime": "image/png",
                    "image_base64": base64.b64encode(buffer.getvalue()).decode(),
                },
                {"action": "remove"},
            ):
                response = client.post(f"/catalog/products/{product.pk}/icon/", body, format="json")
                assert response.status_code == 200 and response.json()["icon"]["id"] == str(icon_id)
        assert ProductIcon.objects.count() == 1
