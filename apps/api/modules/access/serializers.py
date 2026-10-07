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
