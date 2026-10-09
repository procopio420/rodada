"""HTTP views for the Cash domain.

Routes are deliberately not installed here: the integration layer owns the
public URL map.  See the module README-style route list in the final handoff.
"""

from datetime import date

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
from modules.cash.models import CashPoint, CashReviewStatus, CashShift, CashShiftStatus
from modules.venue.calendar import business_date as current_business_date
from rest_framework import serializers
from modules.cash.services import (
    CashServiceError,
    active_cash_shift,
    cash_close_preview,
    cash_shift_movements,
    cash_shift_position,
    close_cash_shift,
    create_cash_point,
    open_cash_shift,
    record_late_cash_correction,
    review_cash_discrepancy,
    start_cash_count,
    supply_cash,
    withdraw_cash,
)


def _error(error: CashServiceError) -> Response:
    return Response({"code": error.code, "message": error.message}, status=error.status_code)


def _shift_payload(shift, *, include_position=True) -> dict:
    payload = {
        "id": str(shift.id),
        "cash_point_id": str(shift.cash_point_id),
        "business_date": shift.business_date,
        "status": shift.status,
        "opening_float_cents": shift.opening_float_cents,
        "counted_amount_cents": shift.counted_amount_cents,
        "expected_amount_cents_snapshot": shift.expected_amount_cents_snapshot,
        "discrepancy_cents": shift.discrepancy_cents,
        "review_status": shift.review_status,
        "version": shift.version,
    }
    if include_position:
        payload.update(cash_shift_position(shift))
    return payload


def _movement_payload(movement) -> dict:
    return {
        "id": str(movement.id),
        "kind": movement.kind,
        "amount_cents": movement.amount_cents,
        "payment_id": str(movement.payment_id) if movement.payment_id else None,
        "refund_id": str(movement.refund_id) if movement.refund_id else None,
        "actor_id": str(movement.actor_id),
        "reason": movement.reason,
        "occurred_at": movement.occurred_at,
        "recorded_at": movement.recorded_at,
        "is_post_close_correction": movement.is_post_close_correction,
    }


class CashPointListView(APIView):
    """Selectable, venue-scoped drawers and their active shift if present."""

    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def get(self, request):
        points = CashPoint.objects.filter(venue_id=request.actor_context.venue_id, active=True).order_by("label")
        data = []
        for point in points:
            try:
                shift = active_cash_shift(cash_point_id=point.id, actor=request.actor_context)
            except CashServiceError as error:
                if error.code != "ACTIVE_CASH_SHIFT_REQUIRED":
                    return _error(error)
                shift = None
            # A discrepancy remains operational work after the drawer closes.
            # Return only the current pending review for this point so a native
            # cashier/manager can finish the canonical review without falling
            # back to a separate financial surface.
            pending_review_shift = (
                CashShift.objects.filter(
                    cash_point=point,
                    status=CashShiftStatus.CLOSED,
                    review_status=CashReviewStatus.PENDING,
                )
                .order_by("-closed_at", "-id")
                .first()
            )
            data.append(
                {
                    "id": str(point.id),
                    "label": point.label,
                    "active_shift": _shift_payload(shift) if shift else None,
                    "pending_review_shift": _shift_payload(pending_review_shift) if pending_review_shift else None,
                    "current_business_date": current_business_date(request.auth.venue),
                }
            )
        return Response({"results": data})


class CashPointCreateView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.VENUE_CONFIGURE

    def post(self, request):
        try:
            point = create_cash_point(
                label=request.data.get("label", ""),
                device_id=request.data.get("device_id"),
                actor=request.actor_context,
            )
        except CashServiceError as error:
            return _error(error)
        return Response({"id": str(point.id), "label": point.label, "active": point.active}, status=201)


class CashPointActiveShiftView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def get(self, request, cash_point_id):
        try:
            return Response(_shift_payload(active_cash_shift(cash_point_id=cash_point_id, actor=request.actor_context)))
        except CashServiceError as error:
            return _error(error)


class CashShiftOpenView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CASH_SHIFT_OPEN

    def post(self, request):
        try:
            business_date = request.data.get("business_date") or current_business_date(request.auth.venue)
            if isinstance(business_date, str):
                business_date = date.fromisoformat(business_date)
            shift = open_cash_shift(
                cash_point_id=request.data.get("cash_point_id"),
                opening_float_cents=int(request.data.get("opening_float_cents")),
                business_date=business_date,
                idempotency_key=request.data.get("idempotency_key", ""),
                actor=request.actor_context,
            )
        except (TypeError, ValueError):
            return Response({"code": "INVALID_CASH_SHIFT", "message": "Dados de abertura inválidos."}, status=400)
        except CashServiceError as error:
            return _error(error)
        return Response(_shift_payload(shift), status=201)


class CashShiftDetailView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def get(self, request, shift_id):
        try:
            preview = cash_close_preview(shift_id=shift_id, actor=request.actor_context)
            # The native client uses this endpoint to reconcile an operation after a
            # timeout/restart.  A close preview alone lacks the immutable shift
            # identity and cash-point context, so it cannot be parsed as the same
            # canonical snapshot returned by open/list endpoints.
            shift = CashShift.objects.get(pk=shift_id, cash_point__venue_id=request.actor_context.venue_id)
            payload = _shift_payload(shift)
            payload.update(preview)
            payload["movements"] = [
                _movement_payload(movement)
                for movement in cash_shift_movements(shift_id=shift_id, actor=request.actor_context)
            ]
            return Response(payload)
        except CashServiceError as error:
            return _error(error)


class CashShiftListView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.PAYMENT_COLLECT

    def get(self, request):
        class Query(serializers.Serializer):
            cash_point_id = serializers.UUIDField()
            offset = serializers.IntegerField(min_value=0, default=0)
        data = Query(data=request.query_params)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        rows = list(CashShift.objects.filter(venue_id=request.actor_context.venue_id,
            cash_point_id=values["cash_point_id"]).order_by("-opened_at", "-id")[values["offset"]:values["offset"] + 51])
        return Response({"results": [_shift_payload(row, include_position=False) for row in rows[:50]],
            "next_offset": values["offset"] + 50 if len(rows) > 50 else None,
            "current_business_date": current_business_date(request.auth.venue)})


class CashSupplyView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CASH_ADJUSTMENT_CREATE

    def post(self, request, shift_id):
        try:
            movement = supply_cash(
                shift_id=shift_id,
                amount_cents=int(request.data.get("amount_cents")),
                reason=request.data.get("reason", ""),
                idempotency_key=request.data.get("idempotency_key", ""),
                actor=request.actor_context,
            )
            return Response(_movement_payload(movement), status=201)
        except (TypeError, ValueError):
            return Response({"code": "INVALID_CASH_SUPPLY", "message": "Valor inválido."}, status=400)
        except CashServiceError as error:
            return _error(error)


class CashWithdrawalView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CASH_ADJUSTMENT_CREATE

    def post(self, request, shift_id):
        try:
            movement = withdraw_cash(
                shift_id=shift_id,
                amount_cents=int(request.data.get("amount_cents")),
                reason=request.data.get("reason", ""),
                idempotency_key=request.data.get("idempotency_key", ""),
                actor=request.actor_context,
                allow_negative_expected=bool(request.data.get("allow_negative_expected", False)),
            )
            return Response(_movement_payload(movement), status=201)
        except (TypeError, ValueError):
            return Response({"code": "INVALID_CASH_WITHDRAWAL", "message": "Valor inválido."}, status=400)
        except CashServiceError as error:
            return _error(error)


class CashCountStartView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CASH_SHIFT_OPEN

    def post(self, request, shift_id):
        try:
            return Response(_shift_payload(start_cash_count(shift_id=shift_id, actor=request.actor_context)))
        except CashServiceError as error:
            return _error(error)


class CashCloseView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CASH_SHIFT_OPEN

    def post(self, request, shift_id):
        try:
            shift = close_cash_shift(
                shift_id=shift_id,
                counted_amount_cents=int(request.data.get("counted_amount_cents")),
                review_threshold_cents=int(request.data.get("review_threshold_cents", 0)),
                expected_version=(
                    int(request.data["expected_version"])
                    if request.data.get("expected_version") is not None
                    else None
                ),
                actor=request.actor_context,
            )
            return Response(_shift_payload(shift))
        except (TypeError, ValueError):
            return Response({"code": "INVALID_CASH_COUNT", "message": "Contagem inválida."}, status=400)
        except CashServiceError as error:
            return _error(error)


class CashReviewView(APIView):
    # Accepting a discrepancy is a manager action with financial impact.
    # The server, rather than the cashier UI, owns the recent-PIN requirement.
    permission_classes = [IsAuthenticated, RequireCapability, RequireRecentReauthentication]
    required_capability = Capability.CASH_REVIEW

    def post(self, request, shift_id):
        try:
            return Response(
                _shift_payload(
                    review_cash_discrepancy(
                        shift_id=shift_id,
                        reason=request.data.get("reason", ""),
                        actor=request.actor_context,
                    )
                )
            )
        except CashServiceError as error:
            return _error(error)


class CashLateCorrectionView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CASH_REVIEW

    def post(self, request, shift_id):
        try:
            movement = record_late_cash_correction(
                shift_id=shift_id,
                amount_cents=int(request.data.get("amount_cents")),
                reason=request.data.get("reason", ""),
                idempotency_key=request.data.get("idempotency_key", ""),
                correction_of_id=request.data.get("correction_of_id"),
                actor=request.actor_context,
            )
            return Response(_movement_payload(movement), status=201)
        except (TypeError, ValueError):
            return Response({"code": "INVALID_LATE_CORRECTION", "message": "Correção inválida."}, status=400)
        except CashServiceError as error:
            return _error(error)
