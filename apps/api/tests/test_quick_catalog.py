import base64
import io
import json
import tempfile
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from django.db import connection, connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient
from modules.access.capabilities import Capability
from modules.access.context import ActorContext
from modules.access.models import StaffMember, StaffRole, StaffSession, VenueStaffMembership
from modules.catalog.generator import GeneratedAsset, HttpIconGenerator, validate_image
from modules.catalog.models import Product, ProductIcon, IconGeneration, IconGenerationRequest
from modules.catalog.services import (
    enqueue_icon,
    replace_icon,
    resolve_or_create_product,
    run_icon_job,
    suggestions,
)
from modules.venue.models import Venue


def image_bytes(size=(128, 128)):
    buffer = io.BytesIO()
    Image.new("RGBA", size, (242, 193, 78, 255)).save(buffer, "PNG")
    return buffer.getvalue()


class DeterministicGenerator:
    """Test-only fixture; runtime never imports this generator."""

    def __init__(self):
        self.calls = []

    def generate(self, **payload):
        self.calls.append(payload)
        return GeneratedAsset(image_bytes(), "test-only", "fixture", {"images": 1})


class QuickCatalogTests(TestCase):
    def setUp(self):
        self.storage = tempfile.TemporaryDirectory()
        self.addCleanup(self.storage.cleanup)
        setting = override_settings(MEDIA_ROOT=self.storage.name)
        setting.enable()
        self.addCleanup(setting.disable)
        self.venue = Venue.objects.create(name="Bar", slug="quick")
        self.staff = StaffMember.objects.create(display_name="Ana", login_identifier="quick-ana")
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.staff, role=StaffRole.MANAGER
        )
        self.session = StaffSession.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            membership=self.membership,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.actor = ActorContext.from_session(self.session)
        self.client = APIClient()
        self.staff.set_pin("2468")
        self.staff.save(update_fields=["pin_hash"])
        login = self.client.post(
            "/auth/login/",
            {
                "venue_slug": "quick",
                "login_identifier": "quick-ana",
                "pin": "2468",
                "installation_id": "quick-test",
                "platform": "WEB",
            },
            format="json",
        )
        assert login.status_code == 200
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.data["access_token"])
        self.generator = DeterministicGenerator()

    def create(self, name="Água gelada", station="BAR", price=500):
        return resolve_or_create_product(
            session=self.session, actor=self.actor, name=name, station=station, price_cents=price
        )

    def test_exact_normalized_match_reuses_product_icon_and_all_configuration(self):
        p, _ = self.create()
        identity = p.icon.id
        p.active = False
        p.save()
        second, created = self.create("  AGUA   GELADA  ", "KITCHEN", 999)
        assert not created and second.id == p.id and second.icon.id == identity
        assert (
            second.price_cents == 500 and second.fulfillment_station == "BAR" and not second.active
        )
        assert (
            Product.objects.count()
            == ProductIcon.objects.count()
            == IconGeneration.objects.count()
            == 1
        )

    def test_fuzzy_suggestions_never_merge_and_are_venue_scoped(self):
        p, _ = self.create("Cerveja 350 ml")
        assert p in suggestions(self.venue.id, "Cerveja 355 ml")
        second, created = self.create("Cerveja 355 ml")
        assert created and p.id != second.id
        other = Venue.objects.create(name="Outro", slug="other")
        assert not suggestions(other.id, "Cerveja")

    def test_station_creation_and_icon_management_permissions(self):
        self.membership.role = StaffRole.STAFF
        self.membership.capability_overrides = {"allow": [Capability.CATALOG_CREATE_BAR]}
        self.membership.save()
        data = {"name": "Omelete", "price_cents": 900, "fulfillment_station": "KITCHEN"}
        assert (
            self.client.post("/catalog/resolve-or-create/", data, format="json").status_code == 403
        )
        assert not Product.objects.exists()
        data["fulfillment_station"] = "BAR"
        response = self.client.post("/catalog/resolve-or-create/", data, format="json")
        assert response.status_code == 201
        assert (
            self.client.post(
                f"/catalog/products/{response.data['product']['id']}/icon/",
                {"action": "remove"},
                format="json",
            ).status_code
            == 403
        )

    def test_creation_never_calls_provider_and_timeout_keeps_sellable_product(self):
        with patch.object(
            HttpIconGenerator, "generate", side_effect=TimeoutError("secret")
        ) as provider:
            p, created = self.create()
            assert created and provider.call_count == 0
            assert p.icon.status == "GENERATING"
            for _ in range(3):
                IconGeneration.objects.update(available_at=timezone.now())
                run_icon_job()
        p.refresh_from_db()
        assert p.active and p.availability.state == "AVAILABLE" and p.icon.status == "FAILED"
        job = p.icon.generations.get()
        assert job.attempts == 3 and job.error == "TimeoutError" and not run_icon_job()

    def test_deduplication_and_privacy_allowlist(self):
        p, _ = self.create()
        first = enqueue_icon(product=p)
        assert enqueue_icon(product=p).id == first.id
        run_icon_job(self.generator)
        assert not run_icon_job(self.generator) and len(self.generator.calls) == 1
        payload = self.generator.calls[0]
        assert set(payload["context"]) == {"name", "description", "category", "station"}
        assert payload["style_version"] == "rodada-icon-v1"
        p.refresh_from_db()
        assert p.icon.status == "READY" and p.icon.published_asset
        assert p.icon.generations.get().provider == "test-only"

    def test_regeneration_retains_asset_and_alias_is_idempotent_after_completion(self):
        p, _ = self.create()
        run_icon_job(self.generator)
        p.refresh_from_db()
        original = p.icon.published_asset
        first = enqueue_icon(product=p, actor=self.actor, request_key="manual:a", force=True)
        alias = enqueue_icon(product=p, actor=self.actor, request_key="manual:b", force=True)
        assert first.id == alias.id
        p.refresh_from_db()
        assert p.icon.published_asset == original and p.icon.status == "GENERATING"
        run_icon_job(self.generator)
        assert (
            enqueue_icon(product=p, actor=self.actor, request_key="manual:b", force=True).id
            == first.id
        )
        assert (
            len(self.generator.calls) == 2
            and IconGenerationRequest.objects.filter(icon=p.icon).count() == 3
        )

    def test_failed_regeneration_keeps_published_asset(self):
        p, _ = self.create()
        run_icon_job(self.generator)
        p.refresh_from_db()
        original = p.icon.published_asset
        enqueue_icon(product=p, actor=self.actor, request_key="manual:failure", force=True)
        with patch.object(HttpIconGenerator, "generate", side_effect=TimeoutError):
            for _ in range(3):
                IconGeneration.objects.filter(status="PENDING").update(available_at=timezone.now())
                run_icon_job()
        p.refresh_from_db()
        assert p.icon.published_asset == original and p.icon.status == "FAILED"

    def test_upload_and_reset_fence_inflight_jobs(self):
        p, _ = self.create()

        def upload(**kwargs):
            replace_icon(product=p, actor=self.actor, content=image_bytes(), mime="image/png")
            return self.generator.generate(**kwargs)

        run_icon_job(SimpleNamespace(generate=upload))
        p.refresh_from_db()
        assert p.icon.source == "UPLOADED"
        enqueue_icon(product=p, actor=self.actor, request_key="manual:reset", force=True)

        def reset(**kwargs):
            replace_icon(product=p, actor=self.actor)
            return self.generator.generate(**kwargs)

        run_icon_job(SimpleNamespace(generate=reset))
        p.refresh_from_db()
        assert p.icon.published_asset == "" and p.icon.status == "NONE"

    def test_validated_upload_and_public_asset_retrieval(self):
        p, _ = self.create()
        path = f"/catalog/products/{p.id}/icon/"
        for content, mime in [
            (b"not image", "image/png"),
            (image_bytes(), "image/jpeg"),
            (image_bytes((128, 256)), "image/png"),
        ]:
            assert (
                self.client.post(
                    path,
                    {
                        "action": "upload",
                        "mime": mime,
                        "image_base64": base64.b64encode(content).decode(),
                    },
                    format="json",
                ).status_code
                == 400
            )
        response = self.client.post(
            path,
            {
                "action": "upload",
                "mime": "image/png",
                "image_base64": base64.b64encode(image_bytes()).decode(),
            },
            format="json",
        )
        assert response.status_code == 200
        public = APIClient()
        asset = public.get(response.data["icon"]["published_asset_url"])
        assert asset.status_code == 200 and asset["Content-Type"] == "image/png"
        assert b"".join(asset.streaming_content) == validate_image(image_bytes())
        assert (
            public.get(
                response.data["icon"]["published_asset_url"].replace(".png", "-evil.png")
            ).status_code
            == 404
        )

    def test_edits_preserve_icon_and_uploaded_assets(self):
        p, _ = self.create()
        identity = p.icon.id
        response = self.client.patch(
            f"/catalog/products/{p.id}/",
            {"name": "Água mineral", "price_cents": 750},
            format="json",
        )
        assert response.status_code == 200 and response.data["icon"]["id"] == str(identity)
        p.refresh_from_db()
        assert p.normalized_name == "agua mineral" and p.icon.generations.count() == 2
        self.create("Omelete")
        assert (
            self.client.patch(
                f"/catalog/products/{p.id}/", {"name": "omelete"}, format="json"
            ).status_code
            == 400
        )
        replace_icon(product=p, actor=self.actor, content=image_bytes(), mime="image/png")
        count = IconGeneration.objects.count()
        self.client.patch(f"/catalog/products/{p.id}/", {"description": "Sem gás"}, format="json")
        assert IconGeneration.objects.count() == count

    def test_suggestions_show_shared_product_details(self):
        p, _ = self.create()
        row = self.client.get("/catalog/suggestions/?q=AGUA").data["results"][0]
        assert row["id"] == str(p.id) and row["icon"]["id"] == str(p.icon.id)
        assert (
            row["price_cents"] == 500
            and row["fulfillment_station"] == "BAR"
            and row["availability"] == "AVAILABLE"
        )

    def test_guest_staff_reference_and_ordering_survive_ai_failure(self):
        from modules.guest_access.services import (
            resolve_table_qr,
            create_or_get_guest_tab,
            confirm_guest_order,
        )
        from modules.hospitality.models import Table, GuestOrderingMode

        p, _ = self.create()
        with patch.object(HttpIconGenerator, "generate", side_effect=TimeoutError):
            run_icon_job()
        table = Table.objects.create(
            venue=self.venue, label="Q", guest_ordering_mode=GuestOrderingMode.DIRECT
        )
        resolution = resolve_table_qr(public_token=table.public_token)
        create_or_get_guest_tab(session_token=resolution.token)
        order = confirm_guest_order(
            session_token=resolution.token,
            lines=[{"product_id": p.id, "quantity": 1}],
            idempotency_key="ai-failed-order",
        )
        assert order.items.get().product_id == p.id
        run_icon_job(
            self.generator
        )  # pending backoff remains; use a manual upload to publish deterministically
        replace_icon(product=p, actor=self.actor, content=image_bytes(), mime="image/png")
        staff = self.client.get("/catalog/products/").data["results"][0]
        guest = (
            APIClient()
            .get("/guest/catalog/", HTTP_X_GUEST_SESSION=resolution.token)
            .data["results"][0]
        )
        assert staff["icon"] == guest["icon"] and guest["icon"]["published_asset_url"]

    def test_real_gateway_adapter_and_no_fake_runtime_fallback(self):
        with override_settings(RODADA_ICON_PROVIDER_URL="", RODADA_ICON_PROVIDER_KEY=""):
            with pytest.raises(RuntimeError):
                HttpIconGenerator().generate(
                    context={}, prompt="", style_version="", idempotency_key=""
                )
        payload = {
            "image_base64": base64.b64encode(image_bytes()).decode(),
            "provider": "gateway",
            "model": "real-model",
        }
        with override_settings(
            RODADA_ICON_PROVIDER_URL="https://provider.example/generate",
            RODADA_ICON_PROVIDER_KEY="secret",
        ):
            with patch("urllib.request.urlopen") as http:
                http.return_value.__enter__.return_value.read.return_value = json.dumps(
                    payload
                ).encode()
                result = HttpIconGenerator().generate(
                    context={"name": "Omelete"},
                    prompt="contract",
                    style_version="rodada-icon-v1",
                    idempotency_key="job",
                )
                assert http.call_args.args[0].get_header("Idempotency-key") == "job"
                assert result.provider == "gateway" and result.content == validate_image(
                    image_bytes()
                )

    def test_manager_rate_limit(self):
        p, _ = self.create()
        run_icon_job(self.generator)
        for index in range(19):
            enqueue_icon(product=p, actor=self.actor, request_key=f"manual:{index}", force=True)
            run_icon_job(self.generator)
        response = self.client.post(
            f"/catalog/products/{p.id}/icon/",
            {"action": "regenerate", "idempotency_key": "blocked"},
            format="json",
        )
        assert response.status_code == 429


class ConcurrentCatalogTests(TransactionTestCase):
    def test_postgres_concurrent_creation_and_worker_transaction_boundary(self):
        if connection.vendor != "postgresql":
            pytest.skip("Requires PostgreSQL; covered in PostgreSQL CI")
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        venue = Venue.objects.create(name="Concurrent", slug="concurrent")
        barrier = Barrier(2)

        def create(name):
            connections.close_all()
            barrier.wait()
            with transaction.atomic():
                product, _ = Product.objects.get_or_create(
                    venue_id=venue.id,
                    normalized_name="agua",
                    defaults={"name": name, "price_cents": 500, "fulfillment_station": "BAR"},
                )
                result = product.id
            connections.close_all()
            return result

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(create, ["Água", " AGUA "]))
        assert results[0] == results[1]
        assert (
            Product.objects.count()
            == ProductIcon.objects.count()
            == IconGeneration.objects.count()
            == 1
        )
        fake = DeterministicGenerator()

        def generate(**payload):
            assert not connection.in_atomic_block
            return fake.generate(**payload)

        assert run_icon_job(SimpleNamespace(generate=generate)) and len(fake.calls) == 1
