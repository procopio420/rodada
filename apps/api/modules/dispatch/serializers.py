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
    product_name = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    tab_label = serializers.SerializerMethodField()

    def get_product_name(self, task):
        return task.order_item.product_name_snapshot if task.order_item_id else ""

    def get_quantity(self, task):
        return task.order_item.quantity if task.order_item_id else 0

    def get_tab_label(self, task):
        if not task.order_item_id:
            return ""
        return task.order_item.order.tab.display_label
