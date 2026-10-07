from rest_framework import serializers


class DeliveryCompleteSerializer(serializers.Serializer):
    """Explicitly empty: completion is retry-safe by task identity."""


class DispatchTaskSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    state = serializers.CharField(read_only=True)
    priority = serializers.IntegerField(read_only=True)
    destination_label = serializers.CharField(read_only=True)
    destination_table_id = serializers.UUIDField(read_only=True, allow_null=True)
    order_item_id = serializers.UUIDField(read_only=True, allow_null=True)
    ready_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    completed_by_id = serializers.UUIDField(read_only=True, allow_null=True)
    completion_source = serializers.CharField(read_only=True)
