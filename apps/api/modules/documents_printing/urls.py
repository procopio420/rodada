from django.urls import path

from .agent_views import (
    AgentActivateView,
    AgentContractView,
    AgentHeartbeatView,
    AgentRevokeView,
    AgentsEnabledView,
    AgentsView,
    PairingApproveView,
    PairingInspectView,
    PairingStartView,
    PairingStatusView,
)
from .kds_views import KdsDetectorView, KdsHealthView, KdsHeartbeatView
from .views import (
    BridgeClaimView,
    BridgeResultView,
    DocumentView,
    EndpointsView,
    JobsView,
    JobView,
    ReceiptTokenView,
)

urlpatterns = [
    path("agents/v1/", AgentsView.as_view()),
    path("agents/v1/enabled/", AgentsEnabledView.as_view()),
    path("agents/v1/pairing/start/", PairingStartView.as_view()),
    path("agents/v1/pairing/status/", PairingStatusView.as_view()),
    path("agents/v1/pairing/inspect/", PairingInspectView.as_view()),
    path("agents/v1/pairing/approve/", PairingApproveView.as_view()),
    path("agents/v1/<uuid:agent_id>/revoke/", AgentRevokeView.as_view()),
    path("agents/v1/me/activate/", AgentActivateView.as_view()),
    path("agents/v1/me/heartbeat/", AgentHeartbeatView.as_view()),
    path("agents/v1/me/contract/", AgentContractView.as_view()),
    path("kds/", KdsHealthView.as_view()),
    path("kds/<str:station>/heartbeat/", KdsHeartbeatView.as_view()),
    path("kds/<str:station>/detector/", KdsDetectorView.as_view()),
    path("documents/", DocumentView.as_view()),
    path("documents/<uuid:document_id>/", DocumentView.as_view()),
    path("documents/<uuid:document_id>/share/", ReceiptTokenView.as_view()),
    path("endpoints/", EndpointsView.as_view()),
    path("jobs/", JobsView.as_view()),
    path("jobs/<uuid:job_id>/", JobView.as_view()),
    path("bridge/claim/", BridgeClaimView.as_view()),
    path("bridge/jobs/<uuid:job_id>/result/", BridgeResultView.as_view()),
]

