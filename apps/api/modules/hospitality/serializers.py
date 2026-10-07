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


class OccupyTableSerializer(serializers.Serializer):
    tab_id = serializers.UUIDField(required=False)


class AssignTabSerializer(serializers.Serializer):
    tab_id = serializers.UUIDField()


class GuestOrderingBlockSerializer(serializers.Serializer):
    blocked = serializers.BooleanField()
