"""Development-only seeded Django instance, never an ordinary configured database.

Use --sqlite for a disposable local fallback, or --postgres with a pre-created
dedicated rodada_ux_review database. Both options are explicit.
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument("--sqlite", action="store_true")
mode.add_argument("--postgres", action="store_true")
args = parser.parse_args()
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))
os.environ["DJANGO_SETTINGS_MODULE"] = "rodada_api.settings"

from django.conf import settings

with tempfile.TemporaryDirectory(prefix="rodada-ux-review-") as directory:
    if args.sqlite:
        settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(Path(directory) / "review.sqlite3")}}
    elif settings.DATABASES["default"]["NAME"] != "rodada_ux_review":
        raise RuntimeError("Use only the dedicated rodada_ux_review PostgreSQL database")
    settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
    settings.DEBUG = False
    import django
    django.setup()
    from django.core.management import call_command
    call_command("migrate", verbosity=0)
    call_command("seed_demo", verbosity=0)
    # Explicit authored assignment in this disposable review fixture, never a name resolver.
    from modules.catalog.models import ProductIcon, Product
    from modules.audit.models import AuditEvent
    for name, asset in (("Fritas", "material-fries"), ("Brahma 600ml", "material-brahma")):
        product = Product.objects.get(venue__slug="bar-do-aderlan", name=name)
        ProductIcon.objects.update_or_create(product=product, defaults={"source": "PROVIDED_REFERENCE", "status": "READY", "published_asset_url": f"http://127.0.0.1:3000/product-icons/{asset}.svg", "style_version": "provided-reference-v1", "error_code": ""})
        AuditEvent.objects.create(venue=product.venue, event_type="product.icon_reference_assigned", entity_type="Product", entity_id=str(product.id), metadata={"source": "PROVIDED_REFERENCE", "asset": asset, "context": "disposable UX review fixture"})
    print("Isolated UX review API: http://127.0.0.1:8000 (demo data only)", flush=True)
    call_command("runserver", "127.0.0.1:8000", use_reloader=False, verbosity=0)
