from django.db import migrations


def seed(apps, schema_editor):
    Venue = apps.get_model("venue", "Venue")
    Policy = apps.get_model("house_account", "VenueRelationshipPolicy")
    Tab = apps.get_model("ordering", "Tab")
    Charge = apps.get_model("ledger", "Charge")
    Adjustment = apps.get_model("ledger", "LedgerAdjustment")
    Payment = apps.get_model("ledger", "Payment")
    Refund = apps.get_model("ledger", "Refund")
    AuditEvent = apps.get_model("audit", "AuditEvent")
    from django.db.models import Sum

    database = schema_editor.connection.alias
    for venue_id in Venue.objects.using(database).values_list("id", flat=True).iterator():
        for kind, limit in {
            "VISITOR": 3000,
            "KNOWN": 8000,
            "REGULAR": 20000,
            "HOUSE": 50000,
            "RESTRICTED": 0,
        }.items():
            Policy.objects.using(database).get_or_create(
                venue_id=venue_id, kind=kind, defaults={"limit_cents": limit}
            )

    def total(model, **filters):
        return (
            model.objects.using(database).filter(**filters).aggregate(v=Sum("amount_cents"))["v"]
            or 0
        )

    for tab in Tab.objects.using(database).filter(state__in=["OPEN", "REQUIRES_ACTION"]).iterator():
        exposure = (
            total(Charge, tab_id=tab.id)
            + total(Adjustment, tab_id=tab.id)
            - total(
                Payment, tab_id=tab.id, status__in=["CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED"]
            )
            + total(Refund, payment__tab_id=tab.id, status="CONFIRMED")
        )
        reasons = ["OTHER_ACTION_REQUIRED"] if tab.state == "REQUIRES_ACTION" else []
        if exposure >= tab.operating_limit_cents:
            reasons.append("SPENDING_LIMIT")
        if reasons:
            before = tab.state
            tab.state = "REQUIRES_ACTION"
            tab.action_reasons = reasons
            tab.save(using=database, update_fields=["state", "action_reasons"])
            AuditEvent.objects.using(database).create(
                venue_id=tab.venue_id,
                event_type="tab.house_policy_migrated",
                entity_type="Tab",
                entity_id=str(tab.id),
                metadata={
                    "source": "MIGRATION",
                    "previous_state": before,
                    "state": tab.state,
                    "action_reasons": reasons,
                    "operating_limit_cents": tab.operating_limit_cents,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("house_account", "0001_initial"),
        ("audit", "0001_initial"),
        ("ordering", "0003_tab_action_reasons_tab_customer_and_more"),
        ("ledger", "0006_remove_ledgeradjustment_ledger_adjustment_cancellation_negative_and_more"),
    ]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
