from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    venue_slug = serializers.SlugField(max_length=80)
    login_identifier = serializers.CharField(max_length=120)
    pin = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)
    installation_id = serializers.CharField(max_length=255, write_only=True, trim_whitespace=False)
    platform = serializers.CharField(max_length=32)
    friendly_label = serializers.CharField(max_length=120, required=False, allow_blank=True)


class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(max_length=512, write_only=True, trim_whitespace=False)


class SwitchOperatorSerializer(serializers.Serializer):
    login_identifier = serializers.CharField(max_length=120)
    pin = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)


class ReauthenticateSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)


class MembershipUpdateSerializer(serializers.Serializer):
    expected_version = serializers.IntegerField(min_value=1)
    role = serializers.ChoiceField(
        choices=("STAFF", "CASHIER", "MANAGER", "OWNER"),
        required=False,
    )
    status = serializers.ChoiceField(
        choices=("ACTIVE", "SUSPENDED", "REVOKED"),
        required=False,
    )
    reason = serializers.CharField(max_length=240, required=False, allow_blank=True)

    def validate(self, attrs):
        if "role" not in attrs and "status" not in attrs:
            raise serializers.ValidationError("Informe role e/ou status.")
        return attrs


class DeviceTrustUpdateSerializer(serializers.Serializer):
    trust_state = serializers.ChoiceField(choices=("TRUSTED", "REVOKED"))
    reason = serializers.CharField(max_length=240, required=False, allow_blank=True)


class SessionRevokeSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=240, required=False, allow_blank=True)
