"""Canonical commercial bill. Every effect and allocation is an immutable ledger fact."""

import hashlib
import json
import uuid
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Q

from modules.access.capabilities import Capability, has_capability
from modules.access.context import ActorContext
from modules.access.models import StaffSession
from modules.audit.services import record_audit_event
from modules.house_account.services import authorize, sync_attention
from modules.ledger.models import (
    AdjustmentAllocation,
    Charge,
    LedgerAdjustment,
    PaymentStatus,
    PricingApproval,
    PricingPolicy,
)
from modules.ledger.models import (
    AdjustmentKind as Kind,
)
from modules.ordering.models import Tab, TabState


@dataclass(frozen=True)
class PricingError(Exception):
    code: str
    message: str
    status_code: int = 409


CATEGORIES = ("gross", "discount", "courtesy", "correction", "service")
TREATMENTS = ("service_revenue", "service_pass_through")
SERVICE = (Kind.SERVICE_CHARGE, Kind.SERVICE_CHARGE_REDUCTION)
DISCOUNTS = (Kind.ITEM_DISCOUNT, Kind.TAB_DISCOUNT, Kind.COURTESY)


def percentage(basis, points):
    if type(basis) is not int or type(points) is not int or basis < 0 or not 0 <= points <= 10000:
        raise PricingError("INVALID_PERCENTAGE", "Percentual inválido.", 400)
    return (basis * points + 5000) // 10000


def allocate(amount, bases):
    """Signed proportional allocation; half cents cannot be lost or duplicated."""
    bases = {str(key): value for key, value in bases.items() if value > 0}
    total = sum(bases.values())
    if not total:
        if amount:
            raise PricingError("NO_ELIGIBLE_BASIS", "Sem consumo elegível.")
        return {}
    magnitude, sign = abs(amount), -1 if amount < 0 else 1
    shares = {key: magnitude * value // total for key, value in bases.items()}
    order = sorted(bases, key=lambda key: (-(magnitude * bases[key] % total), key))
    for key in order[: magnitude - sum(shares.values())]:
        shares[key] += 1
    return {key: sign * value for key, value in shares.items()}


def category(adjustment):
    kind = adjustment.reverses.kind if adjustment.kind == Kind.REVERSAL else adjustment.kind
    if kind in SERVICE:
        return "service"
    if kind in (Kind.COURTESY, Kind.COURTESY_REPLACEMENT):
        return "courtesy"
    if kind in (Kind.ITEM_DISCOUNT, Kind.TAB_DISCOUNT):
        return "discount"
    return "correction"


def components(tab):
    from modules.tab_operations.models import TabTransferLine

    charges = Charge.objects.filter(
        Q(tab=tab) | Q(transfer_lines__transfer__destination_tab=tab)
    ).distinct()
    result = {str(c.id): dict.fromkeys((*CATEGORIES, *TREATMENTS), 0) for c in charges}
    for charge in charges:
        if charge.tab_id == tab.id:
            result[str(charge.id)]["gross"] = charge.amount_cents
    # Legacy entries without allocation remain exactly the original item effects.
    for adjustment in tab.ledger_adjustments.select_related("reverses").filter(
        allocations__isnull=True
    ):
        if adjustment.order_item_id:
            key = str(Charge.objects.get(order_item_id=adjustment.order_item_id).id)
            if key in result:
                result[key][category(adjustment)] += adjustment.amount_cents
    for line in AdjustmentAllocation.objects.filter(adjustment__tab=tab).select_related(
        "adjustment__reverses"
    ):
        key = str(line.charge_id)
        result.setdefault(key, dict.fromkeys((*CATEGORIES, *TREATMENTS), 0))[
            category(line.adjustment)
        ] += line.amount_cents
        if category(line.adjustment) == "service":
            snapshot = line.adjustment.policy_snapshot
            split = snapshot.get("service_allocations", {}).get(key)
            if split is None:
                field = (
                    "service_revenue"
                    if snapshot.get("service_treatment") == "REVENUE"
                    else "service_pass_through"
                )
                split = {field: line.amount_cents}
            for field in TREATMENTS:
                result[key][field] += split.get(field, 0)
    for line in TabTransferLine.objects.filter(
        Q(transfer__source_tab=tab) | Q(transfer__destination_tab=tab)
    ).select_related("transfer"):
        sign = 1 if line.transfer.destination_tab_id == tab.id else -1
        values = line.components or {"gross": line.amount_cents}
        key = str(line.source_charge_id)
        result.setdefault(key, dict.fromkeys((*CATEGORIES, *TREATMENTS), 0))
        for field in (*CATEGORIES, *TREATMENTS):
            result[key][field] += sign * values.get(field, 0)
        if "service_revenue" not in values and "service_pass_through" not in values:
            result[key]["service_pass_through"] += sign * values.get("service", 0)
    return result


def net_consumption(values):
    return sum(values.get(field, 0) for field in CATEGORIES if field != "service")


def commercial_summary(tab):
    rows = components(tab)
    sums = {field: sum(row[field] for row in rows.values()) for field in CATEGORIES}
    latest = (
        tab.ledger_adjustments.filter(kind=Kind.SERVICE_CHARGE)
        .order_by("-created_at", "-id")
        .first()
    )
    stale = False
    if latest:
        from modules.tab_operations.models import TabTransferLine

        expected_bases = {
            str(line.charge_id): line.basis_cents for line in latest.allocations.all()
        }
        for line in TabTransferLine.objects.filter(
            Q(transfer__source_tab=tab) | Q(transfer__destination_tab=tab),
            transfer__committed_at__gt=latest.created_at,
        ).select_related("transfer"):
            sign = 1 if line.transfer.destination_tab_id == tab.id else -1
            key = str(line.source_charge_id)
            expected_bases[key] = expected_bases.get(key, 0) + sign * net_consumption(
                line.components or {"gross": line.amount_cents}
            )
        current_bases = {key: net_consumption(row) for key, row in rows.items()}
        stale = any(
            expected_bases.get(key, 0) != current_bases.get(key, 0)
            for key in set(expected_bases) | set(current_bases)
        )
    if not latest and sums["service"]:
        from modules.tab_operations.models import TabTransferLine

        inherited = (
            TabTransferLine.objects.filter(transfer__destination_tab=tab)
            .select_related("transfer")
            .order_by("-transfer__committed_at")
            .first()
        )
        if inherited:
            anchor = inherited.transfer.committed_at
            stale = (
                tab.charges.filter(created_at__gt=anchor).exists()
                or tab.ledger_adjustments.exclude(kind__in=SERVICE)
                .filter(created_at__gt=anchor)
                .exists()
            )
    return {
        "original_subtotal_cents": sums["gross"],
        "discounts_cents": -sums["discount"],
        "courtesy_cents": -sums["courtesy"],
        "corrections_cents": sums["correction"],
        "net_consumption_cents": sum(net_consumption(row) for row in rows.values()),
        "service_charge_cents": sums["service"],
        "payable_cents": sum(sums.values()),
        "service_assessment_stale": stale,
    }


def assert_settleable(tab):
    if commercial_summary(tab)["service_assessment_stale"]:
        raise PricingError(
            "SERVICE_REASSESSMENT_REQUIRED",
            "Atualize a taxa de serviço antes de receber ou fechar.",
        )


def policy_data(policy):
    return {
        field.name: getattr(policy, field.name)
        for field in policy._meta.fields
        if field.name != "venue"
    }


def get_policy(venue_id):
    return PricingPolicy.objects.get_or_create(venue_id=venue_id)[0]


def fingerprint(data):
    # Version is a concurrency precondition, not a new financial intention on retry.
    return hashlib.sha256(
        json.dumps(
            {k: v for k, v in data.items() if k != "expected_version"}, sort_keys=True, default=str
        ).encode()
    ).hexdigest()


def locked_tab(tab_id, actor):
    tab = Tab.objects.select_for_update().filter(pk=tab_id, venue_id=actor.venue_id).first()
    if not tab:
        raise PricingError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    return tab


def eligibility(tab, data):
    from modules.tab_operations.services import payment_blocker

    if tab.state not in (TabState.OPEN, TabState.REQUIRES_ACTION):
        raise PricingError("TAB_NOT_OPEN", "Comanda não está aberta.")
    if tab.version != data["expected_version"]:
        raise PricingError("VERSION_CONFLICT", "A comanda mudou. Confira novamente.")
    blocker = payment_blocker(tab, confirmed=False)
    if blocker:
        raise PricingError(*blocker)


def proposal(tab, data, policy):
    kind = data["kind"]
    values = components(tab)
    bases = {key: net_consumption(row) for key, row in values.items()}
    if any(value < 0 for value in bases.values()):
        raise PricingError("INVALID_LEDGER_BASIS", "Consumo exige reconciliação.")
    scope = "CHARGE" if data.get("charge_id") else "TAB"
    if scope == "CHARGE":
        key = str(data["charge_id"])
        if key not in bases:
            raise PricingError("CHARGE_NOT_FOUND", "Consumo não pertence à comanda.", 404)
        bases = {key: bases[key]}
    basis = sum(bases.values())
    calculation = data.get("calculation_type", "FIXED")
    value = data.get("value", 0)
    reverses = None
    if kind in DISCOUNTS:
        if kind == Kind.ITEM_DISCOUNT and scope != "CHARGE":
            raise PricingError("CHARGE_REQUIRED", "Selecione o item.", 400)
        if kind == Kind.TAB_DISCOUNT and scope != "TAB":
            raise PricingError("TAB_SCOPE_REQUIRED", "Desconto de comanda não aceita item.", 400)
        amount = percentage(basis, value) if calculation == "PERCENTAGE" else value
        if amount <= 0 or amount > basis:
            raise PricingError(
                "DISCOUNT_EXCEEDS_BASIS", "Desconto deve ser positivo e limitado ao consumo."
            )
        if amount > percentage(basis, policy.maximum_discount_basis_points):
            raise PricingError("POLICY_MAXIMUM_EXCEEDED", "Desconto excede o máximo configurado.")
        amount = -amount
        allocations = allocate(amount, bases)
    elif kind == Kind.SERVICE_CHARGE:
        scope, calculation = "TAB", "PERCENTAGE"
        bases = {key: net_consumption(row) for key, row in values.items()}
        basis = sum(bases.values())
        value = data.get("value", policy.service_basis_points)
        if not policy.service_enabled or not 0 <= value <= policy.service_max_basis_points:
            raise PricingError("SERVICE_POLICY_REQUIRED", "Taxa não permitida pela política.")
        amount = percentage(basis, value)
        allocations = allocate(amount, bases)
    elif kind == Kind.SERVICE_CHARGE_REDUCTION:
        scope, calculation = "TAB", "FIXED"
        bases = {key: row["service"] for key, row in values.items()}
        basis = sum(bases.values())
        if value <= 0 or value > basis:
            raise PricingError("REDUCTION_EXCEEDS_SERVICE", "Redução excede a taxa ativa.")
        amount = -value
        allocations = allocate(amount, bases)
    elif kind == Kind.REVERSAL:
        reverses = tab.ledger_adjustments.filter(
            pk=data.get("adjustment_id"), request_fingerprint__gt=""
        ).first()
        if not reverses or reverses.kind in (Kind.REVERSAL, Kind.SERVICE_CHARGE):
            raise PricingError("ADJUSTMENT_NOT_REVERSIBLE", "Use redução para remover serviço.")
        if LedgerAdjustment.objects.filter(reverses=reverses).exists():
            raise PricingError("ALREADY_REVERSED", "Ajuste já revertido.")
        from modules.tab_operations.models import TabTransferLine

        if TabTransferLine.objects.filter(
            source_charge_id__in=reverses.allocations.values("charge_id"),
            transfer__committed_at__gt=reverses.created_at,
        ).exists():
            raise PricingError(
                "TRANSFERRED_ADJUSTMENT", "Ajuste transferido exige correção de responsabilidade."
            )
        if (
            reverses.kind == Kind.SERVICE_CHARGE_REDUCTION
            and tab.ledger_adjustments.filter(
                kind=Kind.SERVICE_CHARGE, created_at__gt=reverses.created_at
            ).exists()
        ):
            raise PricingError(
                "SUPERSEDED_SERVICE", "Redução pertence a avaliação anterior; atualize o serviço."
            )
        amount = -reverses.amount_cents
        allocations = {
            str(line.charge_id): -line.amount_cents for line in reverses.allocations.all()
        }
        basis, calculation, value, scope = reverses.basis_cents, "DERIVED", 0, reverses.scope
        # Reversing a reduction must not restore more service than originally assessed.
    else:
        raise PricingError("INVALID_KIND", "Ajuste inválido.", 400)
    return {
        "kind": kind,
        "scope": scope,
        "calculation_type": calculation,
        "requested_value": value,
        "basis_cents": basis,
        "amount_cents": amount,
        "allocations": allocations,
        "reverses": reverses,
    }


def requires_approval(actor, proposal, policy):
    session = StaffSession.objects.select_related("membership__staff_member").get(
        pk=actor.session_id
    )
    if has_capability(session.membership, Capability.DISCOUNT_OVERRIDE):
        return False
    kind = proposal["kind"]
    if kind in (Kind.COURTESY, Kind.REVERSAL):
        return True
    if kind == Kind.SERVICE_CHARGE_REDUCTION:
        if not policy.service_opt_out and policy.service_removal_requires_manager:
            return True
        return not policy.service_opt_out and not has_capability(
            session.membership, Capability.PAYMENT_COLLECT
        )
    if kind == Kind.SERVICE_CHARGE:
        return proposal["requested_value"] != policy.service_basis_points or not has_capability(
            session.membership, Capability.PAYMENT_COLLECT
        )
    threshold = (
        policy.cashier_discount_basis_points
        if has_capability(session.membership, Capability.PAYMENT_COLLECT)
        else policy.staff_discount_basis_points
    )
    return abs(proposal["amount_cents"]) > percentage(proposal["basis_cents"], threshold)


def validate_settlement(tab, proposal, policy, data):
    from modules.ledger.services import totals

    before = totals(tab)
    refresh = before["service_charge_cents"] if proposal["kind"] == Kind.SERVICE_CHARGE else 0
    effect = proposal["amount_cents"] - refresh
    after = before["payable_cents"] + effect
    if after < 0 or after < before["payments_cents"] - before["refunds_cents"]:
        raise PricingError(
            "SETTLEMENT_CORRECTION_REQUIRED", "Estorne o excedente antes de ajustar o consumo."
        )
    paid = tab.payments.filter(status__in=PaymentStatus.confirmed_money_values()).exists()
    if paid and not policy.allow_post_payment:
        raise PricingError("POST_PAYMENT_DISABLED", "Política não permite ajuste após pagamento.")
    if (
        proposal["kind"] in (Kind.COURTESY, Kind.REVERSAL)
        or paid
        or (proposal["kind"] == Kind.SERVICE_CHARGE_REDUCTION and not policy.service_opt_out)
    ):
        if not data.get("reason_code"):
            raise PricingError("REASON_REQUIRED", "Informe o motivo.", 400)
    return {
        "before_payable_cents": before["payable_cents"],
        "after_payable_cents": after,
        "after_remaining_cents": after - before["payments_cents"] + before["refunds_cents"],
        "effect_cents": effect,
    }


@transaction.atomic
def preview(*, tab_id, data, actor):
    authorize(actor, Capability.TAB_OPEN)
    tab = locked_tab(tab_id, actor)
    eligibility(tab, data)
    get_policy(actor.venue_id)
    policy = PricingPolicy.objects.select_for_update().get(venue_id=actor.venue_id)
    proposed = proposal(tab, data, policy)
    result = validate_settlement(tab, proposed, policy, data)
    return {
        **result,
        "basis_cents": proposed["basis_cents"],
        "allocations": proposed["allocations"],
        "approval_required": requires_approval(actor, proposed, policy),
        "version": tab.version,
        "policy_version": policy.version,
    }


def write_fact(tab, proposal, data, actor, policy, *, approver=None, key=None, response=None):
    allocations = proposal["allocations"]
    charge = Charge.objects.get(pk=data["charge_id"]) if data.get("charge_id") else None
    fact_id = uuid.uuid4()
    response = {"adjustment_id": str(fact_id), **(response or {})}
    current = components(tab)
    snapshot = policy_data(policy)
    if proposal["kind"] in SERVICE or (
        proposal["kind"] == Kind.REVERSAL and category(proposal["reverses"]) == "service"
    ):
        treatment = (
            "service_revenue" if policy.service_treatment == "REVENUE" else "service_pass_through"
        )
        splits = {}
        for charge_id, amount in allocations.items():
            if proposal["kind"] == Kind.SERVICE_CHARGE:
                splits[charge_id] = {treatment: amount}
            elif proposal["kind"] == Kind.REVERSAL:
                original = (
                    proposal["reverses"]
                    .policy_snapshot.get("service_allocations", {})
                    .get(charge_id)
                )
                if original is None:
                    original_field = (
                        "service_revenue"
                        if proposal["reverses"].policy_snapshot.get("service_treatment")
                        == "REVENUE"
                        else "service_pass_through"
                    )
                    original = {original_field: -amount}
                splits[charge_id] = {field: -value for field, value in original.items()}
            else:
                splits[charge_id] = allocate(
                    amount, {field: current[charge_id].get(field, 0) for field in TREATMENTS}
                )
        snapshot["service_allocations"] = splits
    fact = LedgerAdjustment.objects.create(
        id=fact_id,
        tab=tab,
        order_item=charge.order_item if charge else None,
        kind=proposal["kind"],
        scope=proposal["scope"],
        calculation_type=proposal["calculation_type"],
        requested_value=proposal["requested_value"],
        basis_cents=proposal["basis_cents"],
        amount_cents=proposal["amount_cents"],
        reverses=proposal.get("reverses"),
        idempotency_key=key or data["idempotency_key"],
        reason_code=data.get("reason_code", ""),
        reason_text=data.get("reason_text", ""),
        created_by_id=actor.staff_id,
        approved_by_id=approver.staff_id if approver else None,
        request_fingerprint=fingerprint(data),
        policy_snapshot=snapshot,
        response=response or {},
    )
    allocation_bases = {
        charge_id: max(
            0,
            current.get(charge_id, {}).get("service", 0)
            if proposal["kind"] == Kind.SERVICE_CHARGE_REDUCTION
            else net_consumption(current.get(charge_id, {})),
        )
        for charge_id in allocations
    }
    if proposal.get("reverses"):
        allocation_bases = {
            str(line.charge_id): line.basis_cents for line in proposal["reverses"].allocations.all()
        }
    AdjustmentAllocation.objects.bulk_create(
        [
            AdjustmentAllocation(
                adjustment=fact,
                charge_id=key,
                amount_cents=amount,
                basis_cents=allocation_bases[key],
            )
            for key, amount in allocations.items()
        ]
    )
    record_audit_event(
        actor=approver or actor,
        event_type="adjustment.reversed" if fact.kind == Kind.REVERSAL else "adjustment.created",
        entity_type="LedgerAdjustment",
        entity_id=str(fact.id),
        reason=fact.reason_code,
        metadata={
            "tab_id": str(tab.id),
            "kind": fact.kind,
            "basis_cents": fact.basis_cents,
            "amount_cents": fact.amount_cents,
            "requested_by": str(actor.staff_id),
            "approved_by": str(approver.staff_id) if approver else None,
            "allocations": allocations,
        },
    )
    return fact


@transaction.atomic
def apply(*, tab_id, data, actor, approver=None):
    authorize(actor, Capability.TAB_OPEN)
    tab = locked_tab(tab_id, actor)
    get_policy(actor.venue_id)
    policy = PricingPolicy.objects.select_for_update().get(venue_id=actor.venue_id)
    pending = PricingApproval.objects.filter(
        tab=tab, idempotency_key=data["idempotency_key"]
    ).first()
    if pending and (
        pending.request_fingerprint != fingerprint(data)
        or pending.requested_by_id != actor.session_id
    ):
        raise PricingError("IDEMPOTENCY_CONFLICT", "Chave reservada por outra solicitação.")
    proposed = None
    existing = tab.ledger_adjustments.filter(idempotency_key=data["idempotency_key"]).first()
    if existing:
        if existing.request_fingerprint != fingerprint(data):
            raise PricingError("IDEMPOTENCY_CONFLICT", "Chave já usada para outro ajuste.")
        proposed = {
            "kind": existing.kind,
            "requested_value": existing.requested_value,
            "amount_cents": existing.amount_cents,
            "basis_cents": existing.basis_cents,
        }
    else:
        if approver and pending and pending.preview["policy_version"] != policy.version:
            raise PricingError(
                "POLICY_VERSION_CONFLICT", "Política mudou. Solicite uma nova aprovação."
            )
        eligibility(tab, data)
        proposed = proposal(tab, data, policy)
    needs = requires_approval(actor, proposed, policy)
    if approver:
        if approver.venue_id != actor.venue_id:
            raise PricingError("APPROVER_VENUE_MISMATCH", "Aprovação inválida.", 403)
        authorize(approver, Capability.DISCOUNT_OVERRIDE, privileged=True)
    elif needs:
        raise PricingError("APPROVAL_REQUIRED", "Este ajuste exige aprovação da gerência.", 403)
    elif has_capability(
        StaffSession.objects.select_related("membership__staff_member")
        .get(pk=actor.session_id)
        .membership,
        Capability.DISCOUNT_OVERRIDE,
    ):
        authorize(actor, Capability.DISCOUNT_OVERRIDE, privileged=True)
    if existing:
        return existing.response
    result = validate_settlement(tab, proposed, policy, data)
    if needs and not data.get("reason_code"):
        raise PricingError("REASON_REQUIRED", "Informe o motivo para aprovação.", 400)
    from modules.house_account.services import financial_position

    if (
        result["after_remaining_cents"] > financial_position(tab)["effective_limit_cents"]
        and result["effect_cents"] > 0
    ):
        raise PricingError(
            "SPENDING_LIMIT_EXCEEDED", "Taxa/ajuste excede o limite. Autorize o limite primeiro."
        )
    if proposed["kind"] == Kind.SERVICE_CHARGE:
        service = {key: row["service"] for key, row in components(tab).items() if row["service"]}
        if service:
            reduction = {
                "kind": Kind.SERVICE_CHARGE_REDUCTION,
                "scope": "TAB",
                "calculation_type": "DERIVED",
                "requested_value": sum(service.values()),
                "basis_cents": sum(service.values()),
                "amount_cents": -sum(service.values()),
                "allocations": {k: -v for k, v in service.items()},
            }
            write_fact(
                tab,
                reduction,
                data,
                actor,
                policy,
                approver=approver,
                key=f"refresh:{hashlib.sha256(data['idempotency_key'].encode()).hexdigest()}",
            )
    response = {**result, "version": tab.version + 1}
    fact = write_fact(tab, proposed, data, actor, policy, approver=approver, response=response)
    tab.version += 1
    tab.save(update_fields=["version"])
    sync_attention(tab, approver or actor)
    return {"adjustment_id": str(fact.id), **response}


@transaction.atomic
def request_approval(*, tab_id, data, actor):
    authorize(actor, Capability.TAB_OPEN)
    locked_tab(tab_id, actor)
    existing = PricingApproval.objects.filter(
        tab_id=tab_id, idempotency_key=data["idempotency_key"]
    ).first()
    if existing:
        if (
            existing.request_fingerprint != fingerprint(data)
            or existing.requested_by_id != actor.session_id
        ):
            raise PricingError("IDEMPOTENCY_CONFLICT", "Solicitação já usada.")
        return {"approval_id": str(existing.id), **existing.preview}
    result = preview(tab_id=tab_id, data=data, actor=actor)
    if not data.get("reason_code"):
        raise PricingError("REASON_REQUIRED", "Informe o motivo para aprovação.", 400)
    approval, _ = PricingApproval.objects.get_or_create(
        tab_id=tab_id,
        idempotency_key=data["idempotency_key"],
        defaults={
            "requested_by_id": actor.session_id,
            "request_fingerprint": fingerprint(data),
            "command": json.loads(json.dumps(data, default=str)),
            "preview": result,
        },
    )
    if (
        approval.request_fingerprint != fingerprint(data)
        or approval.requested_by_id != actor.session_id
    ):
        raise PricingError("IDEMPOTENCY_CONFLICT", "Solicitação já usada.")
    record_audit_event(
        actor=actor,
        event_type="pricing.approval_required",
        entity_type="PricingApproval",
        entity_id=str(approval.id),
        metadata=result,
    )
    return {"approval_id": str(approval.id), **approval.preview}


@transaction.atomic
def approve(*, approval_id, actor):
    authorize(actor, Capability.DISCOUNT_OVERRIDE, privileged=True)
    approval = PricingApproval.objects.filter(pk=approval_id, tab__venue_id=actor.venue_id).first()
    if not approval:
        raise PricingError("APPROVAL_NOT_FOUND", "Solicitação não encontrada.", 404)
    locked_tab(approval.tab_id, actor)
    approval = PricingApproval.objects.select_for_update().get(pk=approval_id)
    if (
        not approval.adjustment_id
        and approval.preview["policy_version"] != get_policy(actor.venue_id).version
    ):
        raise PricingError(
            "POLICY_VERSION_CONFLICT", "Política mudou. Solicite uma nova aprovação."
        )
    requester = ActorContext.from_session(approval.requested_by)
    result = apply(tab_id=approval.tab_id, data=approval.command, actor=requester, approver=actor)
    if not approval.adjustment_id:
        approval.adjustment = LedgerAdjustment.objects.get(
            tab_id=approval.tab_id, idempotency_key=approval.idempotency_key
        )
        approval.save(update_fields=["adjustment"])
    return result


def refund_preview(tab, charge_id):
    from modules.ledger.services import totals

    values = components(tab).get(str(charge_id))
    if values is None:
        raise PricingError("CHARGE_NOT_FOUND", "Consumo não encontrado.", 404)
    service = values["service"] if get_policy(tab.venue_id).service_refundable else 0
    ledger = totals(tab)
    consumption = net_consumption(values)
    return {
        "net_consumption_cents": consumption,
        "service_refundable_cents": service,
        "maximum_refund_cents": max(
            0, min(consumption + service, ledger["payments_cents"] - ledger["refunds_cents"])
        ),
        "requires_payment_selection": True,
    }
