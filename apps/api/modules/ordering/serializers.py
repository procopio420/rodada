from rest_framework import serializers


class TabCreateSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField(required=False, allow_null=True)
    display_label = serializers.CharField(
        max_length=120,
        required=True,
        allow_blank=False,
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


class ProductionBatchLineSerializer(serializers.Serializer):
    item_id = serializers.UUIDField()
    expected_state = serializers.ChoiceField(choices=("NEW", "ACCEPTED", "PREPARING"))
    quantity = serializers.IntegerField(min_value=1, max_value=999)
    snapshot_fingerprint = serializers.RegexField(r"^[a-f0-9]{64}$")


class ProductionBatchSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(max_length=120)
    station = serializers.ChoiceField(choices=("BAR", "KITCHEN"))
    target_state = serializers.ChoiceField(choices=("PREPARING", "READY"))
    lines = ProductionBatchLineSerializer(many=True, allow_empty=False, max_length=50)

    def validate_lines(self, value):
        if len({line["item_id"] for line in value}) != len(value):
            raise serializers.ValidationError("Selecione cada linha uma única vez.")
        return value
