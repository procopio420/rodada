"""HTTP contract for self-enrolled opt-in Guest Customer profiles."""
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .customer_identity import (
    INVALID_CREDENTIALS, claim_customer_tab, customer_context, login_customer,
    logout_customer, register_customer,
)
from .services import GuestAccessError
from .views import _error_response, _rate_limit, _session_token


class EnrollInput(serializers.Serializer):
    username = serializers.RegexField(regex=r"^[a-zA-Z0-9._-]{3,64}$", max_length=64)
    password = serializers.CharField(min_length=12, max_length=128, trim_whitespace=False)
    display_name = serializers.CharField(min_length=1, max_length=120, trim_whitespace=True)


class LoginInput(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=64)
    password = serializers.CharField(min_length=1, max_length=128, trim_whitespace=False)


class ClaimInput(serializers.Serializer):
    target_tab_id = serializers.UUIDField()


class CustomerRegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        limited = _rate_limit(request, "mutation")
        if limited:
            return limited
        serializer = EnrollInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            customer, token = register_customer(
                guest_token=_session_token(request), **serializer.validated_data,
            )
        except GuestAccessError as error:
            return _error_response(error)
        return Response({
            "authenticated": True, "display_name": customer.display_name,
            "customer_auth_token": token,
        }, status=201)


class CustomerLoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        limited = _rate_limit(request, "mutation")
        if limited:
            return limited
        serializer = LoginInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            customer, token = login_customer(
                guest_token=_session_token(request), **serializer.validated_data,
            )
        except GuestAccessError as error:
            return _error_response(error)
        if customer is None:
            return Response(
                {"code": "INVALID_CREDENTIALS", "message": INVALID_CREDENTIALS},
                status=401,
            )
        return Response({
            "authenticated": True, "display_name": customer.display_name,
            "customer_auth_token": token,
        })


class CustomerContextView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            result = customer_context(
                guest_token=_session_token(request),
                auth_token=request.headers.get("X-Customer-Session", ""),
            )
        except GuestAccessError as error:
            return _error_response(error)
        return Response(result)


class CustomerClaimView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        limited = _rate_limit(request, "mutation")
        if limited:
            return limited
        serializer = ClaimInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tab = claim_customer_tab(
                guest_token=_session_token(request),
                auth_token=request.headers.get("X-Customer-Session", ""),
                **serializer.validated_data,
            )
        except GuestAccessError as error:
            return _error_response(error)
        return Response({"tab_id": str(tab.id), "customer_linked": True})


class CustomerLogoutView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            logout_customer(
                guest_token=_session_token(request),
                auth_token=request.headers.get("X-Customer-Session", ""),
            )
        except GuestAccessError as error:
            return _error_response(error)
        return Response({"authenticated": False})
