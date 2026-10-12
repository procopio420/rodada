"""Opt-in local staff tools; normal Venue capability/session rules still apply."""
import hashlib
import hmac
import json

from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from modules.access.errors import AccessPermissionDenied
from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
from modules.access.services import AccessServiceError, update_membership_admin, _audit
from modules.access.views import (
    StaffMembershipListView, StaffMembershipDetailView, _membership_payload,
    _service_error_response,
)
from modules.audit.models import AuditEvent
from modules.venue.models import Venue


class RequireDeveloperTools(BasePermission):
    def has_permission(self, request, view):
        if not getattr(settings, "RODADA_DEVELOPER_TOOLS", False):
            raise AccessPermissionDenied("DEVELOPER_TOOLS_DISABLED", "Área DEV desabilitada neste ambiente.")
        return True


class StaffCreateSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=120)
    login_identifier = serializers.RegexField(r"^[a-zA-Z0-9_.-]+$", max_length=120)
    pin = serializers.RegexField(r"^[0-9]{4,12}$", write_only=True, trim_whitespace=False)
    role = serializers.ChoiceField(choices=StaffRole.values)
    idempotency_key = serializers.CharField(max_length=120)

    def validate_login_identifier(self, value):
        return value.strip().casefold()


@transaction.atomic
def create_staff(*, actor_session, data):
    # Also serializes updates/removals, so the last OWNER cannot disappear in a race.
    Venue.objects.select_for_update().get(pk=actor_session.venue_id)
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        json.dumps(data, sort_keys=True).encode(), hashlib.sha256,
    ).hexdigest()
    existing = AuditEvent.objects.filter(
        venue_id=actor_session.venue_id, event_type="staff.developer_created",
        actor_staff_id=actor_session.staff_member_id,
        metadata__idempotency_key=data["idempotency_key"],
    ).first()
    if existing:
        if not hmac.compare_digest(existing.metadata["fingerprint"], signature):
            raise AccessServiceError("IDEMPOTENCY_CONFLICT", "Esta tentativa já foi usada com outros dados.", 409)
        return VenueStaffMembership.objects.select_related("staff_member").get(
            pk=existing.metadata["membership_id"], venue_id=actor_session.venue_id,
        )
    if StaffMember.objects.filter(login_identifier__iexact=data["login_identifier"]).exists():
        raise AccessServiceError("LOGIN_ALREADY_EXISTS", "Login já cadastrado. Consulte a equipe; não crie outra identidade.", 409)
    try:
        with transaction.atomic():
            staff = StaffMember(display_name=data["display_name"], login_identifier=data["login_identifier"])
            staff.set_pin(data["pin"])
            staff.save()
    except IntegrityError as exc:
        raise AccessServiceError("LOGIN_ALREADY_EXISTS", "Login já cadastrado.", 409) from exc
    membership = VenueStaffMembership.objects.create(
        venue=actor_session.venue, staff_member=staff, role=data["role"],
        created_by=actor_session.staff_member,
    )
    _audit(venue=actor_session.venue, event_type="staff.developer_created", actor_session=actor_session,
           metadata={"membership_id": str(membership.pk), "target_staff_id": str(staff.pk),
                     "role": membership.role, "idempotency_key": data["idempotency_key"],
                     "fingerprint": signature})
    return membership


class DeveloperStaffListView(StaffMembershipListView):
    permission_classes = [IsAuthenticated, RequireCapability, RequireDeveloperTools]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.request.method == "POST":
            permissions.append(RequireRecentReauthentication())
        return permissions

    def post(self, request):
        serializer = StaffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            member = create_staff(actor_session=request.auth, data=serializer.validated_data)
        except AccessServiceError as exc:
            return _service_error_response(exc)
        return Response(_membership_payload(member), status=201)


class DeveloperStaffDetailView(StaffMembershipDetailView):
    permission_classes = [IsAuthenticated, RequireCapability, RequireDeveloperTools, RequireRecentReauthentication]

    def post(self, request, membership_id):
        class RemoveSerializer(serializers.Serializer):
            expected_version = serializers.IntegerField(min_value=1)
        serializer = RemoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            member = update_membership_admin(
                actor_session=request.auth, membership_id=membership_id,
                expected_version=serializer.validated_data["expected_version"],
                status="REVOKED", reason="Remoção de acesso pela área DEV",
            )
        except AccessServiceError as exc:
            return _service_error_response(exc)
        return Response(_membership_payload(member))
