"""Foundation read contract; no pairing, inventory writes or delivery in S1."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.agent_credentials import PrintAgentAuthentication

from .agent_contracts import PRINT_SCOPE, PROTOCOL_VERSION, ContractResponse


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
                    "operations": ["contract"],
                    "delivery_enabled": False,
                }
            ).data
        )
