from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
from modules.cash.models import DailyClose, DailyCloseReview, CashMovement
from modules.cash.daily_close import DailyCloseError, generate_daily_close, review_daily_close


def close_payload(close):
    review = DailyCloseReview.objects.filter(close=close).first()
    # Facts recorded after the immutable snapshot remain separate. They never
    # masquerade as edits to its signed expected/count/discrepancy observations.
    # Compare committed identity to the snapshot, rather than wall-clock time:
    # a correction may commit after its MVCC boundary but before generated_at.
    corrections = list(CashMovement.objects.filter(shift__venue=close.venue,
        shift__business_date=close.business_date, is_post_close_correction=True
        ).exclude(pk__in=close.snapshot['facts']['movement_ids']).order_by('recorded_at', 'id').values(
            'id', 'shift_id', 'amount_cents', 'occurred_at', 'recorded_at', 'reason', 'actor_id'))
    return dict(id=str(close.id), business_date=close.business_date, version=close.version,
        generated_at=close.generated_at, status='REVIEWED' if review else close.status,
        original=close.snapshot, fingerprint=close.fingerprint,
        review=None if not review else dict(reviewed_by=str(review.reviewed_by_id),
            reviewed_at=review.reviewed_at, reason=review.reason), post_close_adjustments=corrections,
        corrected_cash_delta_cents=sum(row['amount_cents'] for row in corrections))


def _error(error):
    return Response(dict(code=error.code, message=error.message), status=error.status_code)


class StrictInput(serializers.Serializer):
    def validate(self, attrs):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError('Campo desconhecido.')
        return attrs


class DailyCloseListView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.MANAGEMENT_REPORTS_READ

    def get(self, request):
        class Query(StrictInput):
            business_date = serializers.DateField()
        query = Query(data=request.query_params)
        query.is_valid(raise_exception=True)
        rows = DailyClose.objects.filter(venue_id=request.actor_context.venue_id,
            business_date=query.validated_data['business_date']).order_by('-version')
        return Response(dict(results=[close_payload(row) for row in rows]))

    def post(self, request):
        self.required_capability = Capability.CASH_REVIEW
        RequireCapability().has_permission(request, self)
        RequireRecentReauthentication().has_permission(request, self)
        class Input(StrictInput):
            business_date = serializers.DateField()
            idempotency_key = serializers.CharField(max_length=120)
        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            close = generate_daily_close(day=data.validated_data['business_date'],
                idempotency_key=data.validated_data['idempotency_key'], actor=request.actor_context)
        except DailyCloseError as error:
            return _error(error)
        return Response(close_payload(close), status=201)


class DailyCloseDetailView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.MANAGEMENT_REPORTS_READ

    def get(self, request, close_id):
        close = get_object_or_404(DailyClose, pk=close_id, venue_id=request.actor_context.venue_id)
        return Response(close_payload(close))


class DailyCloseReviewView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability, RequireRecentReauthentication]
    required_capability = Capability.CASH_REVIEW

    def post(self, request, close_id):
        class Input(StrictInput):
            expected_version = serializers.IntegerField(min_value=1)
            reason = serializers.CharField(max_length=240)
        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            close = review_daily_close(close_id=close_id, actor=request.actor_context, **data.validated_data)
        except DailyCloseError as error:
            return _error(error)
        return Response(close_payload(close))
