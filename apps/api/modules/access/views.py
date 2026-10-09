from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability, effective_capabilities
from modules.access.serializers import (
    DeviceTrustUpdateSerializer,
    LoginSerializer,
    MembershipUpdateSerializer,
    ReauthenticateSerializer,
    RefreshSerializer,
    SessionRevokeSerializer,
    SwitchOperatorSerializer,
)
from modules.access.invalidation import relevant_invalidations
from modules.access.models import DeviceRegistration, StaffSession, VenueStaffMembership
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
from modules.access.services import (
    AccessServiceError,
    authenticate_staff,
    reauthenticate_staff,
    refresh_staff_session,
    revoke_session,
    revoke_session_admin,
    switch_operator,
    update_device_trust_admin,
    update_membership_admin,
)
from modules.audit.models import AuditEvent


def _service_error_response(exc: AccessServiceError) -> Response:
    payload = {"code": exc.code, "message": exc.message}
    if exc.details:
        payload.update(exc.details)
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


class StaffSwitchOperatorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SwitchOperatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = switch_operator(
                current_session=request.auth,
                **serializer.validated_data,
            )
        except AccessServiceError as exc:
            return _service_error_response(exc)
        return Response(payload, status=200)


class StaffReauthenticateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReauthenticateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = reauthenticate_staff(
                session=request.auth,
                **serializer.validated_data,
            )
        except AccessServiceError as exc:
            return _service_error_response(exc)
        return Response(payload, status=200)


def _membership_payload(membership):
    return {
        "id": str(membership.id),
        "staff": {
            "id": str(membership.staff_member_id),
            "display_name": membership.staff_member.display_name,
            "login_identifier": membership.staff_member.login_identifier,
        },
        "role": membership.role,
        "status": membership.status,
        "capability_overrides": membership.capability_overrides,
        "version": membership.version,
        "created_at": membership.created_at,
        "revoked_at": membership.revoked_at,
    }


def _device_payload(device):
    return {
        "id": str(device.id),
        "platform": device.platform,
        "friendly_label": device.friendly_label,
        "trust_state": device.trust_state,
        "first_seen_at": device.first_seen_at,
        "last_seen_at": device.last_seen_at,
        "revoked_at": device.revoked_at,
        "revocation_reason": device.revocation_reason,
    }


def _session_payload(session):
    return {
        "id": str(session.id),
        "staff": {
            "id": str(session.staff_member_id),
            "display_name": session.staff_member.display_name,
        },
        "device_id": str(session.device_id) if session.device_id else None,
        "issued_at": session.issued_at,
        "last_seen_at": session.last_seen_at,
        "access_expires_at": session.access_expires_at,
        "expires_at": session.expires_at,
        "revoked_at": session.revoked_at,
        "revocation_reason": session.revocation_reason,
        "superseded_at": session.superseded_at,
    }


class AccessManagementBaseView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.STAFF_MANAGE


class StaffMembershipListView(AccessManagementBaseView):
    def get(self, request):
        memberships = (
            VenueStaffMembership.objects.filter(venue=request.auth.venue)
            .select_related("staff_member")
            .order_by("staff_member__display_name", "id")
        )
        return Response({"results": [_membership_payload(item) for item in memberships]})


class StaffMembershipDetailView(AccessManagementBaseView):
    permission_classes = [
        IsAuthenticated,
        RequireCapability,
        RequireRecentReauthentication,
    ]

    def patch(self, request, membership_id):
        serializer = MembershipUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            membership = update_membership_admin(
                actor_session=request.auth,
                membership_id=membership_id,
                **serializer.validated_data,
            )
        except AccessServiceError as exc:
            return _service_error_response(exc)
        membership = VenueStaffMembership.objects.select_related("staff_member").get(pk=membership.pk)
        return Response(_membership_payload(membership))


class DeviceListView(AccessManagementBaseView):
    def get(self, request):
        devices = DeviceRegistration.objects.filter(venue=request.auth.venue).order_by(
            "-last_seen_at", "id"
        )
        return Response({"results": [_device_payload(item) for item in devices]})


class DeviceDetailView(AccessManagementBaseView):
    permission_classes = [
        IsAuthenticated,
        RequireCapability,
        RequireRecentReauthentication,
    ]

    def patch(self, request, device_id):
        serializer = DeviceTrustUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            device = update_device_trust_admin(
                actor_session=request.auth,
                device_id=device_id,
                **serializer.validated_data,
            )
        except AccessServiceError as exc:
            return _service_error_response(exc)
        return Response(_device_payload(device))


class SessionListView(AccessManagementBaseView):
    def get(self, request):
        sessions = (
            StaffSession.objects.filter(venue=request.auth.venue)
            .select_related("staff_member", "device")
            .order_by("-issued_at", "id")[:200]
        )
        return Response({"results": [_session_payload(item) for item in sessions]})


class SessionRevokeView(AccessManagementBaseView):
    permission_classes = [
        IsAuthenticated,
        RequireCapability,
        RequireRecentReauthentication,
    ]

    def post(self, request, session_id):
        serializer = SessionRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            target = revoke_session_admin(
                actor_session=request.auth,
                target_session_id=session_id,
                **serializer.validated_data,
            )
        except AccessServiceError as exc:
            return _service_error_response(exc)
        target = StaffSession.objects.select_related("staff_member", "device").get(pk=target.pk)
        return Response(_session_payload(target))


class AccessAuditListView(AccessManagementBaseView):
    def get(self, request):
        events = (
            AuditEvent.objects.filter(venue=request.auth.venue)
            .select_related("actor_staff", "actor_session", "device")
            .order_by("-occurred_at", "-id")[:200]
        )
        return Response(
            {
                "results": [
                    {
                        "id": str(event.id),
                        "event_type": event.event_type,
                        "entity_type": event.entity_type,
                        "entity_id": event.entity_id,
                        "actor_staff_id": (
                            str(event.actor_staff_id) if event.actor_staff_id else None
                        ),
                        "actor_session_id": (
                            str(event.actor_session_id) if event.actor_session_id else None
                        ),
                        "device_id": str(event.device_id) if event.device_id else None,
                        "reason": event.reason,
                        "metadata": event.metadata,
                        "occurred_at": event.occurred_at,
                    }
                    for event in events
                ]
            }
        )


class AccessInvalidationFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            after_id = max(0, int(request.query_params.get("after", "0")))
        except ValueError:
            after_id = 0

        events = list(
            relevant_invalidations(
                session=request.auth,
                after_id=after_id,
                limit=100,
            )
        )
        cursor = events[-1].id if events else after_id

        return Response(
            {
                "cursor": cursor,
                "results": [
                    {
                        "id": event.id,
                        "event_type": event.event_type,
                        "reason": event.reason,
                        "metadata": event.metadata,
                        "occurred_at": event.occurred_at,
                    }
                    for event in events
                ],
            }
        )
