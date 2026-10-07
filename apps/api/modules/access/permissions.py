from rest_framework.permissions import BasePermission

from modules.access.capabilities import has_capability
from modules.access.errors import AccessAuthenticationFailed, AccessPermissionDenied
from modules.access.models import StaffSession


class RequireCapability(BasePermission):
    def has_permission(self, request, view):
        session = getattr(request, "auth", None)
        if not isinstance(session, StaffSession):
            raise AccessAuthenticationFailed("AUTH_REQUIRED", "Autenticação de staff necessária.")

        capability = getattr(view, "required_capability", None)
        if not capability:
            raise RuntimeError("RequireCapability requires view.required_capability")

        if not has_capability(session.membership, capability):
            raise AccessPermissionDenied(
                "CAPABILITY_REQUIRED",
                "Ação não autorizada para este operador.",
                capability=capability,
            )
        return True
