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
