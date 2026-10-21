"""Scoped v1 machine delivery and management-only route configuration."""

from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from . import agent_delivery
from .agent_views import AgentContractView, PrintManagerView, StrictInput


class DiscoveryView(AgentContractView):
    def post(self, request):
        class Printer(StrictInput):
            local_id = serializers.RegexField(r"^[^\x00-\x1f\x7f]+$", max_length=200)
            label = serializers.RegexField(r"^[^\x00-\x1f\x7f]+$", max_length=120)
            queue_name = serializers.RegexField(r"^[^\x00-\x1f\x7f]+$", max_length=240)
            transport = serializers.ChoiceField(choices=["WINDOWS_DRIVER", "TCP_LAN"])
            driver_name = serializers.CharField(max_length=120, allow_blank=True, default="")
            health = serializers.ChoiceField(
                choices=["UNKNOWN", "DEGRADED", "OFFLINE"], default="UNKNOWN"
            )

        class Input(StrictInput):
            protocol_version = serializers.ChoiceField(choices=[1])
            printers = Printer(many=True, max_length=100)

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(
            agent_delivery.discover(request.user, request.auth.id, data.validated_data["printers"])
        )


class InventoryView(PrintManagerView):
    def get(self, request):
        return Response(agent_delivery.inventory(request.auth))

    def post(self, request):
        class Input(StrictInput):
            id = serializers.UUIDField(required=False)
            endpoint_id = serializers.UUIDField()
            printer_id = serializers.UUIDField()
            printer_fingerprint = serializers.RegexField(r"^[0-9a-f]{64}$")
            expected_version = serializers.IntegerField(min_value=0)
            transport = serializers.ChoiceField(
                choices=["WINDOWS_DRIVER", "WINDOWS_RAW", "TCP_LAN"]
            )
            profile_id = serializers.ChoiceField(choices=list(agent_delivery.PROFILES))
            destination = serializers.CharField(max_length=240)
            port = serializers.IntegerField(min_value=1, max_value=65535, default=9100)
            enabled = serializers.BooleanField(default=False)
            raw_escpos_verified = serializers.BooleanField(default=False)

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            return Response(agent_delivery.save_route(request.auth, data.validated_data))
        except ModelValidationError as exc:
            raise ValidationError(exc.messages) from exc


class ClaimView(AgentContractView):
    def post(self, request):
        class Input(StrictInput):
            protocol_version = serializers.ChoiceField(choices=[1])

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        response = Response(agent_delivery.claim(request.user, request.auth.id))
        response["Cache-Control"] = "no-store"
        return response


class ResultView(AgentContractView):
    def post(self, request, job_id):
        class Input(StrictInput):
            attempt_token = serializers.UUIDField()
            route_id = serializers.UUIDField()
            route_version = serializers.IntegerField(min_value=1)
            outcome = serializers.ChoiceField(
                choices=["SPOOL_ACCEPTED", "DELIVERY_UNCERTAIN", "FAILED_RETRYABLE", "FAILED_FINAL"]
            )

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(
            agent_delivery.result(request.user, request.auth.id, job_id, data.validated_data)
        )
