from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.audit.services import record_audit_event
from modules.catalog.models import AvailabilityState, ProductAvailability
from modules.catalog.queries import catalog_for_venue
from modules.catalog.serializers import product_payload


class ProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "results": [
                    product_payload(product)
                    for product in catalog_for_venue(venue_id=request.auth.venue_id)
                ]
            }
        )


class ProductAvailabilityView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CATALOG_AVAILABILITY_MANAGE_STATION

    def post(self, request, product_id):
        state = request.data.get("state")
        if state not in AvailabilityState.values:
            return Response(
                {"code": "INVALID_AVAILABILITY", "message": "Disponibilidade inválida."}, status=400
            )
        availability = (
            ProductAvailability.objects.select_related("product")
            .filter(product_id=product_id, product__venue_id=request.actor_context.venue_id)
            .first()
        )
        if not availability:
            return Response(
                {"code": "PRODUCT_NOT_FOUND", "message": "Produto não encontrado."}, status=404
            )
        before = availability.state
        availability.state, availability.version, availability.changed_by_id = (
            state,
            availability.version + 1,
            request.actor_context.staff_id,
        )
        availability.save(update_fields=["state", "version", "changed_by", "changed_at"])
        record_audit_event(
            actor=request.actor_context,
            event_type="product.availability_changed",
            entity_type="Product",
            entity_id=str(product_id),
            metadata={"before": before, "after": state},
        )
        return Response(
            {"product_id": str(product_id), "state": state, "version": availability.version}
        )


import base64
import binascii
from pathlib import PurePosixPath

from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny

from modules.catalog.models import Product, ProductIcon
from modules.catalog.serializers import QuickProductInput, icon_payload
from modules.catalog.services import (
    audit,
    enqueue_icon,
    replace_icon,
    resolve_or_create_product,
    suggestions,
)


class ProductSuggestView(APIView):
    def get(self, request):
        query = request.query_params.get("q", "")[:160]
        return Response(
            {"results": [product_payload(p) for p in suggestions(request.auth.venue_id, query)]}
        )


class ProductResolveView(APIView):
    def post(self, request):
        data = QuickProductInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        product, created = resolve_or_create_product(
            session=request.auth,
            actor=request.actor_context,
            name=values["name"],
            price_cents=values["price_cents"],
            station=values["fulfillment_station"],
            description=values["description"],
            category=values["category"],
        )
        return Response(
            {"product": product_payload(product), "created": created},
            status=201 if created else 200,
        )


class ProductEditView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CATALOG_ICON_MANAGE

    def patch(self, request, product_id):
        with transaction.atomic():
            product = (
                Product.objects.select_for_update()
                .filter(pk=product_id, venue_id=request.auth.venue_id)
                .first()
            )
            if not product:
                raise Http404
            data = QuickProductInput(data=request.data, partial=True)
            data.is_valid(raise_exception=True)
            before = product_payload(product)
            for key, value in data.validated_data.items():
                setattr(product, key, value)
            try:
                with transaction.atomic():
                    product.save()
            except IntegrityError:
                raise ValidationError("Já existe um produto com este nome.")
            if product.icon.source != "UPLOADED" and any(
                k in data.validated_data
                for k in ("name", "description", "category", "fulfillment_station")
            ):
                enqueue_icon(product=product, actor=request.actor_context)
            audit(
                product,
                "catalog.product_edited",
                request.actor_context,
                before=before,
                after=product_payload(product),
            )
            return Response(product_payload(product))


class ProductIconManageView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CATALOG_ICON_MANAGE

    def post(self, request, product_id):
        product = Product.objects.filter(pk=product_id, venue_id=request.auth.venue_id).first()
        if not product:
            raise Http404
        action = request.data.get("action")
        if action == "regenerate":
            key = request.data.get("idempotency_key")
            if not isinstance(key, str) or not 1 <= len(key) <= 100:
                raise ValidationError("Informe uma chave de idempotência.")
            job = enqueue_icon(
                product=product,
                actor=request.actor_context,
                request_key="manual:" + key,
                force=True,
            )
            product.refresh_from_db()
            return Response({"icon": icon_payload(product), "job_id": str(job.id)}, status=202)
        if action == "remove":
            replace_icon(product=product, actor=request.actor_context)
        elif action == "upload":
            raw = request.data.get("image_base64", "")
            mime = request.data.get("mime")
            if (
                not isinstance(raw, str)
                or len(raw) > 7 * 1024 * 1024
                or mime not in ("image/png", "image/jpeg", "image/webp")
            ):
                raise ValidationError("Imagem inválida. Use PNG, JPEG ou WebP até 5 MB.")
            try:
                content = base64.b64decode(raw, validate=True)
                replace_icon(
                    product=product, actor=request.actor_context, content=content, mime=mime
                )
            except (ValueError, binascii.Error) as exc:
                raise ValidationError(str(exc))
        else:
            raise ValidationError("Ação inválida.")
        product.refresh_from_db()
        return Response({"icon": icon_payload(product)})


class PublishedIconAssetView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, icon_id, filename):
        icon = ProductIcon.objects.filter(pk=icon_id).first()
        if (
            not icon
            or not icon.published_asset
            or PurePosixPath(icon.published_asset).name != filename
        ):
            raise Http404
        try:
            response = FileResponse(
                default_storage.open(icon.published_asset, "rb"), content_type="image/png"
            )
        except FileNotFoundError:
            raise Http404
        response["Cache-Control"] = "public, max-age=31536000, immutable"
        response["X-Content-Type-Options"] = "nosniff"
        return response
