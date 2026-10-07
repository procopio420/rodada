from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import effective_capabilities
from modules.access.serializers import LoginSerializer, RefreshSerializer
from modules.access.services import (
    AccessServiceError,
    authenticate_staff,
    refresh_staff_session,
    revoke_session,
)


def _service_error_response(exc: AccessServiceError) -> Response:
    payload = {"code": exc.code, "message": exc.message}
    headers = {}
    if exc.retry_after_seconds is not None:
        retry_after = max(1, int(exc.retry_after_seconds))
        payload["retry_after_seconds"] = retry_after
        headers["Retry-After"] = str(retry_after)
    return Response(payload, status=exc.status_code, headers=headers)


class StaffLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = authenticate_staff(**serializer.validated_data)
        except AccessServiceError as exc:
            return _service_error_response(exc)
        return Response(payload, status=200)


class StaffRefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = refresh_staff_session(serializer.validated_data["refresh_token"])
        except AccessServiceError as exc:
            return _service_error_response(exc)
        return Response(payload, status=200)


class CurrentStaffView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = request.auth
        membership = session.membership
        device = session.device
        return Response(
            {
                "staff": {
                    "id": str(session.staff_member_id),
                    "display_name": session.staff_member.display_name,
                },
                "venue": {
                    "id": str(session.venue_id),
                    "slug": session.venue.slug,
                    "name": session.venue.name,
                },
                "membership": {
                    "id": str(membership.id),
                    "role": membership.role,
                    "status": membership.status,
                    "version": membership.version,
                },
                "capabilities": sorted(effective_capabilities(membership)),
                "session": {
                    "id": str(session.id),
                    "access_expires_at": session.access_expires_at,
                    "expires_at": session.expires_at,
                },
                "device": (
                    {
                        "id": str(device.id),
                        "trust_state": device.trust_state,
                        "platform": device.platform,
                        "friendly_label": device.friendly_label,
                    }
                    if device
                    else None
                ),
            }
        )


class StaffLockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        revoke_session(request.auth, "LOCKED")
        return Response(status=204)


class StaffLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        revoke_session(request.auth, "LOGOUT")
        return Response(status=204)
