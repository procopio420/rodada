"""Authenticated, venue-scoped correction proposals and decisions."""
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
from modules.cash.models import CashCorrectionRequest, CashShift
from modules.cash.correction_approval import (
    CashCorrectionError, correction_payload, decide_cash_correction, request_cash_correction,
)


class StrictInput(serializers.Serializer):
    def validate(self, attrs):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError({"code": "UNKNOWN_FIELD", "message": "Campo desconhecido."})
        return attrs


def _error(error):
    return Response({"code": error.code, "message": error.message}, status=error.status_code)


class CashCorrectionShiftView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.CASH_ADJUSTMENT_CREATE

    def get(self, request, shift_id):
        shift = get_object_or_404(CashShift, pk=shift_id, venue_id=request.actor_context.venue_id)
        rows = CashCorrectionRequest.objects.filter(shift=shift).select_related("shift__cash_point").order_by("-requested_at", "-id")
        return Response({"results": [correction_payload(row) for row in rows]})

    def post(self, request, shift_id):
        class Input(StrictInput):
            amount_cents = serializers.IntegerField(min_value=-2_000_000_000, max_value=2_000_000_000)
            reason = serializers.CharField(max_length=240, trim_whitespace=True, allow_blank=False)
            idempotency_key = serializers.CharField(max_length=120, trim_whitespace=True, allow_blank=False)
            correction_of_id = serializers.UUIDField(required=False, allow_null=True)

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            row, created = request_cash_correction(
                shift_id=shift_id, actor=request.actor_context, **data.validated_data
            )
            return Response(correction_payload(row), status=201 if created else 200)
        except CashCorrectionError as error:
            return _error(error)


class CashCorrectionManagementView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.MANAGEMENT_REPORTS_READ

    def get(self, request):
        class Query(StrictInput):
            business_date = serializers.DateField()

        query = Query(data=request.query_params)
        query.is_valid(raise_exception=True)
        rows = CashCorrectionRequest.objects.filter(
            shift__venue_id=request.actor_context.venue_id,
            shift__business_date=query.validated_data["business_date"],
        ).select_related("shift__cash_point").order_by("-requested_at", "-id")
        return Response({"results": [correction_payload(row) for row in rows]})


class CashCorrectionDecisionView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability, RequireRecentReauthentication]
    required_capability = Capability.CASH_REVIEW

    def post(self, request, request_id):
        class Input(StrictInput):
            expected_version = serializers.IntegerField(min_value=1)
            decision = serializers.ChoiceField(choices=("APPROVED", "REJECTED"))
            reason = serializers.CharField(max_length=240, trim_whitespace=True, allow_blank=False)

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            row = decide_cash_correction(
                request_id=request_id, actor=request.actor_context, **data.validated_data
            )
            return Response(correction_payload(row))
        except CashCorrectionError as error:
            return _error(error)
