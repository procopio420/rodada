"""Apply a reviewed manifest to the preserved local demo, never a remote database.

Requires a PGDMP backup + matching SHA256 in the manifest. No deletion or payment
simulation. Run explicitly with --manifest ... --apply, after stopping writers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "apps/api"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rodada_api.settings")
import django
django.setup()
from django.db import connection, transaction
from django.conf import settings
from modules.access.models import StaffMember, VenueStaffMembership
from modules.access.context import ActorContext
from modules.audit.models import AuditEvent
from modules.audit.services import record_audit_event
from modules.ordering.local_test_reset import reset_test_tabs
from modules.ordering.models import Tab
from modules.catalog.models import Product
from modules.venue.models import Venue
from modules.hospitality.services import release_table, start_cleaning, complete_cleaning
from modules.hospitality.models import Table
from modules.management.alerts import evaluate_alerts

parser=argparse.ArgumentParser()
parser.add_argument("--manifest", type=Path, required=True)
parser.add_argument("--apply", action="store_true")
args=parser.parse_args()
db=connection.settings_dict
if not (settings.RODADA_DEVELOPER_TOOLS and db["NAME"]=="rodada_demo" and db["HOST"]=="127.0.0.1" and str(db["PORT"])=="55459"):
    raise SystemExit("Somente demo local explicitamente habilitada (rodada_demo/127.0.0.1:55459).")
manifest=json.loads(args.manifest.read_text(encoding="utf-8-sig"))
backup=Path(manifest["backup"])
if not backup.is_file() or backup.read_bytes()[:5] != b"PGDMP" or hashlib.sha256(backup.read_bytes()).hexdigest()!=manifest["backup_sha256"]:
    raise SystemExit("Backup não confere; nenhuma alteração aplicada.")
if set(manifest["venues"]) - {"bar-do-aderlan", "release-demo", "release-other"}:
    raise SystemExit("Venue fora do escopo local solicitado.")
print(json.dumps({"tabs":sum(len(rows) for rows in manifest["venues"].values()),"products":len(manifest["products"]),"apply":args.apply}))
if not args.apply: raise SystemExit(0)
results={}
with transaction.atomic():
    owner=StaffMember.objects.get(login_identifier="release-owner",is_active=True)
    for slug,ids in manifest["venues"].items():
        venue=Venue.objects.get(slug=slug)
        # Explicit bootstrap of the known local developer, no new person or PIN.
        member,created=VenueStaffMembership.objects.get_or_create(venue=venue,staff_member=owner,defaults={"role":"OWNER","created_by":owner})
        if member.role!="OWNER" or member.status!="ACTIVE": raise ValueError("Administrador local não autorizado.")
        actor=ActorContext(venue_id=venue.pk,staff_id=owner.pk,session_id=None,device_id=None)
        if created:
            record_audit_event(actor=actor,event_type="membership.local_developer_provisioned",entity_type="VenueStaffMembership",entity_id=str(member.pk),reason="Configuração DEV local solicitada",metadata={"source":"LOCAL_CLI","role":"OWNER"})
        if {str(pk) for pk in Tab.objects.filter(venue=venue).values_list("pk",flat=True)} != set(ids):
            raise ValueError("Comandas mudaram desde o manifesto; revisar antes de aplicar.")
        results[slug]=reset_test_tabs(tab_ids=ids,actor=actor)
        for table in Table.objects.filter(venue=venue):
            if table.status=="OCCUPIED":
                occupancy = table.occupancies.get(released_at__isnull=True)
                release_table(table_id=table.pk,actor=actor,expected_occupancy_id=occupancy.pk,expected_generation=occupancy.generation)
                table.refresh_from_db()
            if table.status=="DIRTY": start_cleaning(table_id=table.pk,actor=actor); table.refresh_from_db()
            if table.status=="CLEANING": complete_cleaning(table_id=table.pk,actor=actor)
        evaluate_alerts(venue)
    for row in manifest["products"]:
        product=Product.objects.select_for_update().get(pk=row["id"])
        if (product.name,product.active,product.price_cents)!=(row["old_name"],row["old_active"],row["price_cents"]): raise ValueError("Produto mudou desde o manifesto.")
        actor=ActorContext(venue_id=product.venue_id,staff_id=owner.pk,session_id=None,device_id=None)
        product.name=row["name"];product.active=row["active"];product.save()
        record_audit_event(actor=actor,event_type="catalog.local_test_cleanup",entity_type="Product",entity_id=str(product.pk),reason="Padronização/retirada de testes solicitada",metadata={"before":{"name":row["old_name"],"active":row["old_active"]},"after":{"name":product.name,"active":product.active},"price_cents":product.price_cents})
args.manifest.with_name("cleanup-result.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
print("Limpeza local concluída com histórico preservado.")
