import hashlib
import json
import uuid
from datetime import timedelta
from difflib import SequenceMatcher

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, Throttled, ValidationError

from modules.access.capabilities import has_capability, Capability
from modules.audit.models import AuditEvent
from modules.catalog.models import Product, ProductIcon, IconGeneration, IconGenerationRequest, normalize_product_name
from modules.catalog.style import STYLE_VERSION, STYLE_CONTRACT, product_context
from modules.catalog.generator import runtime_generator, validate_image
from modules.venue.models import Venue


def audit(product, event, actor=None, **metadata):
    return AuditEvent.objects.create(venue_id=product.venue_id, event_type=event,
        entity_type="ProductIcon", entity_id=str(product.icon.id),
        **(dict(actor_staff_id=actor.staff_id, actor_session_id=actor.session_id, device_id=actor.device_id) if actor else {}),
        metadata=metadata)


def authorize_station(session, station):
    capability = {"BAR": Capability.CATALOG_CREATE_BAR, "KITCHEN": Capability.CATALOG_CREATE_KITCHEN}.get(station)
    if not capability:
        raise ValidationError("Estação inválida.")
    if not (has_capability(session.membership, capability) or has_capability(session.membership, Capability.CATALOG_PRODUCT_CREATE)):
        raise PermissionDenied("Criação não autorizada nesta estação.")


@transaction.atomic
def resolve_or_create_product(*, actor, name, price_cents, session=None, station=None, fulfillment_station=None, description="", category=""):
    from modules.access.models import StaffSession
    session = session or StaffSession.objects.select_related("membership").get(pk=actor.session_id)
    station = station or fulfillment_station
    authorize_station(session, station)
    Venue.objects.select_for_update().get(pk=actor.venue_id)
    product, created = Product.objects.get_or_create(venue_id=actor.venue_id,
        normalized_name=normalize_product_name(name), defaults=dict(name=name.strip(), price_cents=price_cents,
        fulfillment_station=station, description=description, category=category))
    product.refresh_from_db()
    if created:
        job = product.icon.generations.first()
        job.created_by_id = actor.staff_id
        job.save(update_fields=["created_by"])
    audit(product, "catalog.product_created" if created else "catalog.product_resolved", actor)
    return product, created


def suggestions(venue_id, query):
    key = normalize_product_name(query)
    products = Product.objects.filter(venue_id=venue_id).select_related("availability", "icon")
    if not key:
        return list(products[:20])
    # Bounded fuzzy candidates; exact results always come first, including inactive products.
    exact = list(products.filter(normalized_name=key))
    partial = list(products.filter(normalized_name__contains=key).exclude(normalized_name=key)[:20])
    if len(exact) + len(partial) < 20:
        candidates = products.exclude(pk__in=[p.pk for p in exact + partial])[:500]
        fuzzy = sorted(((SequenceMatcher(None, key, p.normalized_name).ratio(), p) for p in candidates), key=lambda row: row[0], reverse=True)
        partial += [p for score, p in fuzzy if score >= .55]
    return (exact + partial)[:20]


@transaction.atomic
def enqueue_icon(*, product, actor=None, request_key=None, force=False):
    icon = ProductIcon.objects.select_for_update().get(product=product)
    context = product_context(product)
    fingerprint = hashlib.sha256(json.dumps([context, STYLE_VERSION], sort_keys=True).encode()).hexdigest()
    key = request_key or "auto:" + fingerprint
    existing = IconGenerationRequest.objects.filter(icon=icon, key=key).select_related("generation").first()
    if existing:
        return existing.generation
    equivalent = icon.generations.filter(revision=icon.revision, fingerprint=fingerprint, status__in=(["PENDING", "RUNNING"] if force else ["PENDING", "RUNNING", "READY"])).first()
    if equivalent and (not force or equivalent.status != "READY"):
        IconGenerationRequest.objects.create(icon=icon, key=key, generation=equivalent)
        return equivalent
    # Lock the Venue to serialize limits across products/operators in the same venue.
    Venue.objects.select_for_update().get(pk=product.venue_id)
    recent = IconGeneration.objects.filter(icon__product__venue_id=product.venue_id, created_at__gte=timezone.now()-timedelta(hours=1))
    if force and (recent.count() >= 60 or (actor and recent.filter(created_by_id=actor.staff_id).count() >= 20)):
        raise Throttled(detail="Limite de geração atingido. Tente mais tarde.")
    icon.revision += 1
    icon.status = "GENERATING"
    icon.error_code = ""
    icon.style_version = STYLE_VERSION
    icon.save(update_fields=["revision", "status", "error_code", "style_version", "updated_at"])
    job = IconGeneration.objects.create(icon=icon, fingerprint=fingerprint, request_key=key,
        revision=icon.revision, context=context, prompt=STYLE_CONTRACT + "\nSubject data: " + json.dumps(context, ensure_ascii=False),
        style_version=STYLE_VERSION, available_at=timezone.now(), created_by_id=actor.staff_id if actor else None)
    IconGenerationRequest.objects.create(icon=icon, key=key, generation=job)
    audit(product, "catalog.icon_enqueued", actor, job_id=str(job.id), style_version=STYLE_VERSION)
    return job


def run_icon_job(generator=None):
    now = timezone.now()
    with transaction.atomic():
        # Venue lock also caps automatic provider work to 60 starts/hour per venue.
        job = IconGeneration.objects.filter(Q(status="PENDING", available_at__lte=now) | Q(status="RUNNING", lease_until__lt=now)).order_by("available_at").first()
        if not job:
            return False
        Venue.objects.select_for_update().get(pk=job.icon.product.venue_id)
        if IconGeneration.objects.filter(icon__product__venue_id=job.icon.product.venue_id, status__in=["RUNNING", "READY"], lease_until__gte=now-timedelta(hours=1)).count() >= 60:
            IconGeneration.objects.filter(pk=job.pk, status="PENDING").update(available_at=now+timedelta(minutes=1))
            return False
        token = uuid.uuid4()
        claimed = IconGeneration.objects.filter(pk=job.pk).filter(Q(status="PENDING", available_at__lte=now) | Q(status="RUNNING", lease_until__lt=now)).update(
            status="RUNNING", claim_token=token, lease_until=now+timedelta(minutes=5), attempts=F("attempts")+1)
        if not claimed:
            return True
        job.refresh_from_db()
    # Network/image work must never hold a Product creation transaction or row lock.
    try:
        result = (generator or runtime_generator()).generate(context=job.context, prompt=job.prompt,
            style_version=job.style_version, idempotency_key=str(job.id))
        content = validate_image(result.content)
        path = default_storage.save(f"catalog/icons/{job.icon_id}/{job.id}.png", ContentFile(content))
        with transaction.atomic():
            icon = ProductIcon.objects.select_for_update().get(pk=job.icon_id)
            current = IconGeneration.objects.select_for_update().get(pk=job.id)
            if current.claim_token != token:
                default_storage.delete(path)
                return True
            current.status, current.asset = "READY", path
            current.provider, current.model, current.usage = result.provider, result.model, result.usage
            current.error = ""
            current.save()
            if icon.revision == job.revision:
                icon.published_asset, icon.source, icon.status = path, "AI_GENERATED", "READY"
                icon.published_asset_url, icon.error_code = "", ""
                icon.save()
                audit(icon.product, "catalog.icon_published", job_id=str(job.id), asset=path)
            else:
                audit(icon.product, "catalog.icon_candidate_obsolete", job_id=str(job.id))
    except Exception as exc:
        # Store only the exception class; provider errors can contain credentials/payloads.
        with transaction.atomic():
            icon = ProductIcon.objects.select_for_update().get(pk=job.icon_id)
            current = IconGeneration.objects.select_for_update().get(pk=job.id)
            if current.claim_token != token:
                return True
            current.error = type(exc).__name__
            current.status = "PENDING" if current.attempts < 3 else "FAILED"
            current.available_at = timezone.now()+timedelta(seconds=30 * 2**current.attempts)
            current.save()
            if current.status == "FAILED" and icon.revision == job.revision:
                icon.status = "FAILED"
                icon.error_code = current.error
                icon.save()
            audit(icon.product, "catalog.icon_generation_failed", job_id=str(job.id), attempt=current.attempts, error=current.error)
    return True


@transaction.atomic
def replace_icon(*, product, actor, content=None, mime=None):
    validated = validate_image(content, mime) if content is not None else None
    icon = ProductIcon.objects.select_for_update().get(product=product)
    icon.revision += 1  # In-flight jobs cannot overwrite an upload/reset.
    icon.published_asset = default_storage.save(f"catalog/icons/{icon.id}/{uuid.uuid4()}.png", ContentFile(validated)) if validated else ""
    icon.source, icon.status = ("UPLOADED", "READY") if validated else ("NONE", "NONE")
    icon.published_asset_url, icon.error_code = "", ""
    icon.save()
    audit(product, "catalog.icon_uploaded" if validated else "catalog.icon_removed", actor, asset=icon.published_asset)
    return icon
