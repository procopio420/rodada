from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.capabilities import Capability
from modules.access.permissions import RequireCapability
from modules.access.services import AccessServiceError
from modules.venue.guest_policy import guest_policy_snapshot, set_global_guest_block
from modules.venue.models import Venue
from modules.venue.stations import StationChangeError


class GuestPolicyView(APIView):
    permission_classes = [IsAuthenticated, RequireCapability]
    required_capability = Capability.VENUE_CONFIGURE

    def get(self, request):
        return Response(guest_policy_snapshot(Venue.objects.get(pk=request.actor_context.venue_id)))

    def patch(self, request):
        class Input(serializers.Serializer):
            expected_version = serializers.IntegerField(min_value=1)
            blocked = serializers.BooleanField()
            reason = serializers.CharField(max_length=240, allow_blank=True, default="")

            def validate(self, data):
                if set(self.initial_data) - set(self.fields):
                    raise serializers.ValidationError("Configuração desconhecida.")
                return data
        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            return Response(set_global_guest_block(actor=request.actor_context, **data.validated_data))
        except (AccessServiceError, StationChangeError) as exc:
            return Response({"code": exc.code, "message": exc.message, **(exc.details or {})}, status=exc.status_code)
