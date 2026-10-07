from rest_framework.exceptions import APIException, AuthenticationFailed, PermissionDenied


class AccessUnauthorized(APIException):
    status_code = 401
    default_code = "AUTH_REQUIRED"

    def __init__(self, code: str, message: str, **extra):
        super().__init__(
            detail={"code": code, "message": message, **extra},
            code=code,
        )


class AccessAuthenticationFailed(AuthenticationFailed):
    def __init__(self, code: str, message: str, **extra):
        detail = {"code": code, "message": message, **extra}
        super().__init__(detail=detail, code=code)


class AccessPermissionDenied(PermissionDenied):
    def __init__(self, code: str, message: str, **extra):
        detail = {"code": code, "message": message, **extra}
        super().__init__(detail=detail, code=code)


class AccessThrottled(APIException):
    status_code = 429
    default_code = "AUTH_THROTTLED"

    def __init__(self, retry_after_seconds: int):
        super().__init__(
            detail={
                "code": "AUTH_THROTTLED",
                "message": "Muitas tentativas. Tente novamente em instantes.",
                "retry_after_seconds": retry_after_seconds,
            },
            code=self.default_code,
        )
