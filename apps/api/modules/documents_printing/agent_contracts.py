"""Protocol v1 validation. No transport side effects or print authority."""

import ipaddress

from django.core.exceptions import ValidationError
from rest_framework import serializers

PROTOCOL_VERSION = 1
PRINT_SCOPE = "PRINT_AGENT_V1"
OPERATIONS = ("contract", "heartbeat", "discovery", "claim", "result")


def validate_destination(transport: str, destination: str, port: int) -> None:
    if not destination or any(ord(c) < 32 or ord(c) == 127 for c in destination):
        raise ValidationError("Invalid printer destination.")
    if transport == "TCP_LAN":
        try:
            address = ipaddress.ip_address(destination)
        except ValueError as exc:
            raise ValidationError("TCP destination must be a private literal IP.") from exc
        allowed = (
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
            ipaddress.ip_network("fc00::/7"),
        )
        if not any(address in network for network in allowed) or port != 9100:
            raise ValidationError("Only private LAN IPs on port 9100 are supported in v1.")
    elif transport not in ("WINDOWS_RAW", "WINDOWS_DRIVER", "WINDOWS_SHARED"):
        raise ValidationError("Unsupported transport.")


class ContractResponse(serializers.Serializer):
    protocol_version = serializers.IntegerField()
    agent_id = serializers.UUIDField()
    venue_id = serializers.UUIDField()
    scope = serializers.CharField()
    operations = serializers.ListField(child=serializers.CharField())
    delivery_enabled = serializers.BooleanField()
