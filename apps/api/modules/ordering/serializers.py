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
    quantity = serializers.IntegerField(min_value=1, max_value=999)
    variant_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    modifier_option_ids = serializers.ListField(child=serializers.UUIDField(), required=False, default=list, max_length=100)
    special_instructions = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class OrderConfirmSerializer(serializers.Serializer):
    lines = OrderLineSerializer(many=True, allow_empty=False)
    idempotency_key = serializers.CharField(max_length=120)
