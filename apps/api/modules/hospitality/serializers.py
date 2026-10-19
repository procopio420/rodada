from rest_framework import serializers

from modules.hospitality.models import GuestOrderingMode


class TableCreateSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=80)
    guest_ordering_mode = serializers.ChoiceField(
        choices=GuestOrderingMode.choices, required=False, default=GuestOrderingMode.DISABLED
    )

    def validate_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Label da mesa é obrigatório.")
        return value


class ZoneCreateSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=80)

    def validate_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Nome da zona é obrigatório.")
        return value


class TableLocationSerializer(serializers.Serializer):
    zone_id = serializers.UUIDField(allow_null=True)


class OccupyTableSerializer(serializers.Serializer):
    tab_id = serializers.UUIDField(required=False)


class AssignTabSerializer(serializers.Serializer):
    tab_id = serializers.UUIDField()


class GuestOrderingBlockSerializer(serializers.Serializer):
    blocked = serializers.BooleanField()


class PartySizeSerializer(serializers.Serializer):
    covers_count = serializers.IntegerField(min_value=1, max_value=2147483647)
    expected_version = serializers.IntegerField(min_value=0)
    idempotency_key = serializers.CharField(max_length=128)
    reason = serializers.CharField(max_length=500, required=False, default="", allow_blank=True)


class ServiceStartSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(max_length=128)


class ServiceStartOpenTabSerializer(ServiceStartSerializer):
    display_label = serializers.CharField(max_length=120)

    def validate_display_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Nome da comanda é obrigatório.")
        return value


class ContextualTabSerializer(ServiceStartSerializer):
    expected_generation = serializers.IntegerField(min_value=1)
    display_label = serializers.CharField(
        max_length=120, required=False, default="", allow_blank=True
    )
    customer_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class ResponsibilityClaimSerializer(ServiceStartSerializer):
    expected_responsibility_version = serializers.IntegerField(min_value=0)
    mode = serializers.ChoiceField(choices=["CLAIM_UNASSIGNED", "TAKE_OVER"])


class TableInventorySerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    expected_status = serializers.ChoiceField(
        choices=["AVAILABLE", "OCCUPIED", "DIRTY", "CLEANING", "OUT_OF_SERVICE"]
    )


class TableCountSerializer(serializers.Serializer):
    target_count = serializers.IntegerField(min_value=0, max_value=500)
    expected_count = serializers.IntegerField(min_value=0)
    retire_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list, max_length=500
    )


class TableReleaseSerializer(serializers.Serializer):
    expected_occupancy_id = serializers.UUIDField()
    expected_generation = serializers.IntegerField(min_value=1)
