from rest_framework import serializers


class TabCreateSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField(required=False, allow_null=True)
    display_label = serializers.CharField(
        max_length=120,
        required=False,
        allow_blank=True,
    )


class OrderLineSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class OrderConfirmSerializer(serializers.Serializer):
    lines = OrderLineSerializer(many=True, allow_empty=False)
    idempotency_key = serializers.CharField(max_length=120)
