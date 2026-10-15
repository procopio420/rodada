"""Foundation read contract; no pairing, inventory writes or delivery in S1."""

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.agent_credentials import PrintAgentAuthentication, revoke_agent
from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability

from . import agent_delivery, pairing
from .agent_contracts import PRINT_SCOPE, PROTOCOL_VERSION, ContractResponse
from .models import PrintAgent


class AgentContractView(APIView):
    authentication_classes = (PrintAgentAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(
            ContractResponse(
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "agent_id": request.user.id,
                    "venue_id": request.user.venue_id,
                    "scope": PRINT_SCOPE,
                    "operations": ["contract", "activate", "heartbeat"]
                    + (["discovery", "claim", "result"] if request.user.version == "0.3.0" else []),
                    "delivery_enabled": agent_delivery.delivery_enabled(request.user),
                }
            ).data
        )


class StrictInput(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError({"non_field_errors": ["Unexpected input fields."]})
        return super().to_internal_value(data)


class PairingStartInput(StrictInput):
    installation_id = serializers.UUIDField()
    label = serializers.RegexField(r"^[^\x00-\x1f\x7f]+$", max_length=120)
    proof = serializers.RegexField(r"^rpp_[A-Za-z0-9_-]{43}$", trim_whitespace=False)


class PairingStatusInput(StrictInput):
    request_id = serializers.UUIDField()
    proof = serializers.RegexField(r"^rpp_[A-Za-z0-9_-]{43}$", trim_whitespace=False)


class CodeInput(StrictInput):
    code = serializers.RegexField(r"^[A-Za-z2-7]{16}$")


class ApproveInput(CodeInput):
    installation_id = serializers.UUIDField()


class AnonymousPairingView(APIView):
    def get_authenticate_header(self, request):
        return "PairingProof"

    authentication_classes = ()
    permission_classes = (AllowAny,)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.headers.get("Authorization"):
            raise PermissionDenied("Pairing bootstrap does not accept staff/service tokens.")
        pairing.enforce_throttle("pairing-ip:" + request.META.get("REMOTE_ADDR", "unknown"), 120)


class PairingStartView(AnonymousPairingView):
    def post(self, request):
        pairing.enforce_throttle("pairing-start:" + request.META.get("REMOTE_ADDR", "unknown"), 20)
        data = PairingStartInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(pairing.start_pairing(**data.validated_data), status=201)


class PairingStatusView(AnonymousPairingView):
    def post(self, request):
        data = PairingStatusInput(data=request.data)
        data.is_valid(raise_exception=True)
        pairing.enforce_throttle("pairing-status:" + str(data.validated_data["request_id"]), 90)
        response = Response(pairing.pairing_status(**data.validated_data))
        response["Cache-Control"] = "no-store"
        return response


class PrintManagerView(APIView):
    permission_classes = (RequireCapability,)
    required_capability = Capability.PRINT_MANAGE

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method != "GET":
            pairing.enforce_throttle("pairing-manager:" + str(request.auth.staff_member_id), 60)


class PairingInspectView(PrintManagerView):
    def post(self, request):
        data = CodeInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(pairing.inspect_pairing(session=request.auth, **data.validated_data))


class PairingApproveView(PrintManagerView):
    def post(self, request):
        data = ApproveInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(pairing.approve_pairing(session=request.auth, **data.validated_data))


class AgentsView(PrintManagerView):
    def get(self, request):
        agents = (
            PrintAgent.objects.filter(venue_id=request.auth.venue_id)
            .select_related("device")
            .order_by("created_at")
        )
        return Response(
            {
                "enabled": request.auth.venue.print_agents_enabled,
                "results": [
                    {
                        "id": str(agent.id),
                        "installation_id": str(agent.installation_id),
                        "label": agent.label,
                        "state": agent.state,
                        "version": agent.version,
                        "last_seen_at": agent.last_seen_at,
                        "revoked_at": agent.revoked_at,
                    }
                    for agent in agents[:100]
                ],
            }
        )


class AgentsEnabledView(PrintManagerView):
    def post(self, request):
        class Input(StrictInput):
            enabled = serializers.BooleanField()

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(pairing.set_enabled(session=request.auth, **data.validated_data))


class AgentRevokeView(PrintManagerView):
    def post(self, request, agent_id):
        get_object_or_404(PrintAgent, id=agent_id, venue_id=request.auth.venue_id)

        class Input(StrictInput):
            reason = serializers.CharField(max_length=240)

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        revoke_agent(agent_id=agent_id, session=request.auth, **data.validated_data)
        return Response({"revoked": True})


class AgentActivateView(AgentContractView):
    def post(self, request):
        return Response(pairing.activate(request.user, request.auth.id))


class AgentHeartbeatView(AgentContractView):
    def post(self, request):
        class Input(StrictInput):
            protocol_version = serializers.ChoiceField(choices=[1])
            version = serializers.RegexField(r"^[A-Za-z0-9.+_-]{1,64}$")

        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(
            pairing.heartbeat(request.user, data.validated_data["version"], request.auth.id)
        )
