from rest_framework.authentication import BaseAuthentication, get_authorization_header

from modules.access.context import ActorContext
from modules.access.errors import AccessAuthenticationFailed, AccessPermissionDenied
from modules.access.services import AccessServiceError, session_for_access_token


class StaffBearerAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if parts[0].lower() != self.keyword or len(parts) != 2:
            raise AccessAuthenticationFailed("AUTH_REQUIRED", "Authorization Bearer inválido.")

        try:
            raw_token = parts[1].decode("utf-8")
        except UnicodeError as exc:
            raise AccessAuthenticationFailed("AUTH_REQUIRED", "Token de acesso inválido.") from exc

        if not raw_token.startswith("rat_"):
            raise AccessAuthenticationFailed("AUTH_REQUIRED", "Token de staff inválido.")

        try:
            session = session_for_access_token(raw_token)
        except AccessServiceError as exc:
            if exc.status_code == 403:
                raise AccessPermissionDenied(exc.code, exc.message) from exc
            raise AccessAuthenticationFailed(exc.code, exc.message) from exc

        request.actor_context = ActorContext.from_session(session)
        return session.staff_member, session

    def authenticate_header(self, request):
        return "Bearer"
