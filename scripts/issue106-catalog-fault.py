#!/usr/bin/env python3
"""Apply a real catalog fault to the guarded fixture; read-only proof after Compose."""
import json, os, subprocess, sys
from pathlib import Path
from cross_surface_fixture import require_disposable_database, require_connected_database, database_instance_identity
require_disposable_database()
os.environ.setdefault("DJANGO_SETTINGS_MODULE","rodada_api.settings")
import django
django.setup()
from django.db import connection
from modules.catalog.models import ProductAvailability
from modules.ordering.models import Tab, Order
from modules.ledger.models import Charge, Payment
require_connected_database(connection)
f=json.loads(Path(os.environ["RODADA_POST_DROP_FIXTURE"]).read_text())
assert f["database_instance_id"]==database_instance_identity(connection)
if sys.argv[1]=="revoke":
    from django.db import transaction
    from modules.access.models import StaffSession
    from modules.access.services import revoke_session
    with transaction.atomic():
        session=StaffSession.objects.get(pk=os.environ["RODADA_REVOKED_SESSION_ID"],venue_id=f["venue_id"],staff_member__login_identifier="android-post-drop-operator")
        revoke_session(session,"ISSUE106_DISPOSABLE_TEST")
elif sys.argv[1] in ("unavailable","restore"):
    availability=ProductAvailability.objects.get(product_id=f["kitchen_product_id"],product__venue_id=f["venue_id"])
    availability.state="UNAVAILABLE" if sys.argv[1]=="unavailable" else "AVAILABLE"
    availability.version+=1;availability.save(update_fields=["state","version","changed_at"])
else:
    tab=Tab.objects.get(display_label=os.environ["RODADA_COMPOSE_TAB_LABEL"],venue_id=f["venue_id"])
    assert not Order.objects.filter(tab=tab).exists()
    assert not Charge.objects.filter(tab=tab).exists() and not Payment.objects.filter(tab=tab).exists()
    original=json.loads(Path("artifacts/android-compose-order.json").read_text())
    assert original["database_instance_id"]==f["database_instance_id"]
    assert Order.objects.filter(pk=original["original_order_id"],tab_id=original["original_tab_id"]).count()==1
    assert {str(c.pk) for c in Charge.objects.filter(tab_id=original["original_tab_id"])}==set(original["charge_ids"])
    assert sum(Charge.objects.filter(tab_id=original["original_tab_id"]).values_list("amount_cents",flat=True))==1700
    prefix=os.environ.get("RODADA_CATALOG_PROOF_PREFIX","android-catalog")
    assert prefix in ("android-catalog","android-offline-conflict","android-offline-revocation")
    if prefix=="android-offline-revocation":
        from modules.access.models import StaffSession
        from modules.audit.models import AuditEvent
        session=StaffSession.objects.get(pk=os.environ["RODADA_REVOKED_SESSION_ID"],venue_id=f["venue_id"])
        assert session.revoked_at and session.revocation_reason=="ISSUE106_DISPOSABLE_TEST"
        assert AuditEvent.objects.filter(actor_session_id=session.pk,event_type="auth.session_revoked").count()==1
        assert "NATIVE_REVOKED_GET_POST_REFRESH_SSE_DENIED; NEW_LOGIN_REVIEW_ONLY" in Path(f"artifacts/{prefix}-instrumentation.txt").read_text()
    Path(f"artifacts/{prefix}-sql.json").write_text(json.dumps({"sha":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),"database_instance_id":f["database_instance_id"],"venue_id":f["venue_id"],"tab_id":str(tab.pk),"status":"PASS","orders":0,"charges":0,"payments":0,"native_ui":"production MainActivity Compose","revoked_session_id":os.environ.get("RODADA_REVOKED_SESSION_ID"),"fault":"session revoked before pending replay; native GET/POST/refresh/SSE denied; new login review-only" if prefix=="android-offline-revocation" else "offline pending intent then product change and ACTION_REQUIRED" if os.environ.get("RODADA_COMPOSE_OFFLINE_CATALOG")=="true" else "product made unavailable after cart before confirm"},indent=2)+"\n")
print("PASS: guarded catalog fault stage",sys.argv[1])
