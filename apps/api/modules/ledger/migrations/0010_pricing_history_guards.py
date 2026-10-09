from django.db import migrations


def backfill(apps, schema_editor):
    Adjustment = apps.get_model("ledger", "LedgerAdjustment")
    Charge = apps.get_model("ledger", "Charge")
    Allocation = apps.get_model("ledger", "AdjustmentAllocation")
    for fact in Adjustment.objects.all().iterator():
        charge = Charge.objects.filter(order_item_id=fact.order_item_id).first()
        if charge:
            Adjustment.objects.filter(pk=fact.pk).update(basis_cents=charge.amount_cents)
            Allocation.objects.create(adjustment_id=fact.pk, charge_id=charge.pk,
                                      basis_cents=charge.amount_cents, amount_cents=fact.amount_cents)


def guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute('''
        CREATE FUNCTION pricing_immutable_fact() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'Pricing facts are append-only'; END $$;
        CREATE TRIGGER pricing_adjustment_immutable BEFORE UPDATE OR DELETE ON ledger_ledgeradjustment
            FOR EACH ROW EXECUTE FUNCTION pricing_immutable_fact();
        CREATE TRIGGER pricing_allocation_immutable BEFORE UPDATE OR DELETE ON ledger_adjustmentallocation
            FOR EACH ROW EXECUTE FUNCTION pricing_immutable_fact();
        CREATE FUNCTION pricing_allocation_exact() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE fact_id uuid; expected bigint; actual bigint;
        BEGIN
            IF TG_TABLE_NAME = 'ledger_ledgeradjustment' THEN fact_id := NEW.id;
            ELSE fact_id := NEW.adjustment_id; END IF;
            SELECT amount_cents INTO expected FROM ledger_ledgeradjustment WHERE id = fact_id;
            SELECT COALESCE(SUM(amount_cents), 0) INTO actual FROM ledger_adjustmentallocation WHERE adjustment_id = fact_id;
            -- Legacy cancellation paths have no allocation yet; their known item effect remains canonical.
            IF EXISTS (SELECT 1 FROM ledger_ledgeradjustment WHERE id = fact_id AND request_fingerprint <> '')
               AND actual <> expected THEN RAISE EXCEPTION 'Adjustment allocations must sum exactly'; END IF;
            RETURN NULL;
        END $$;
        CREATE CONSTRAINT TRIGGER pricing_adjustment_exact AFTER INSERT ON ledger_ledgeradjustment
            DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION pricing_allocation_exact();
        CREATE CONSTRAINT TRIGGER pricing_allocation_exact AFTER INSERT ON ledger_adjustmentallocation
            DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION pricing_allocation_exact();
    ''')


def unguard(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute('''
        DROP TRIGGER pricing_allocation_exact ON ledger_adjustmentallocation;
        DROP TRIGGER pricing_adjustment_exact ON ledger_ledgeradjustment;
        DROP TRIGGER pricing_allocation_immutable ON ledger_adjustmentallocation;
        DROP TRIGGER pricing_adjustment_immutable ON ledger_ledgeradjustment;
        DROP FUNCTION pricing_allocation_exact();
        DROP FUNCTION pricing_immutable_fact();
    ''')


class Migration(migrations.Migration):
    dependencies = [("ledger", "0009_adjustmentallocation_pricingapproval_pricingpolicy_and_more")]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop), migrations.RunPython(guards, unguard)]
