from rest_framework import serializers

from modules.ordering.serializers import OrderLineSerializer


class QrResolveSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=64)


class GuestTabCreateSerializer(serializers.Serializer):
    display_label = serializers.CharField(max_length=120, required=False, allow_blank=True)


class GuestOrderConfirmSerializer(serializers.Serializer):
    lines = OrderLineSerializer(many=True, allow_empty=False)
    idempotency_key = serializers.CharField(max_length=120)
