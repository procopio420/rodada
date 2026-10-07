from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.dispatch.models import DispatchTask, DispatchTaskState, DispatchTaskType
from modules.dispatch.serializers import DeliveryCompleteSerializer, DispatchTaskSerializer
from modules.dispatch.services import DispatchServiceError, complete_delivery_task


def _error_response(error: DispatchServiceError) -> Response:
    payload = {"code": error.code, "message": error.message}
    if error.details:
        payload.update(error.details)
    return Response(payload, status=error.status_code)


def _task_payload(task: DispatchTask) -> dict:
    payload = DispatchTaskSerializer(task).data
    payload["age_seconds"] = (
        max(0, int((timezone.now() - task.ready_at).total_seconds())) if task.ready_at else 0
    )
    return payload


class DeliveryQueueView(APIView):
    """Operational queue ordered by explicit priority then oldest READY work."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = (
            DispatchTask.objects.filter(
                venue_id=request.auth.venue_id,
                task_type=DispatchTaskType.DELIVERY,
                state__in=(DispatchTaskState.OPEN, DispatchTaskState.CLAIMED),
            )
            .select_related("destination_table", "order_item")
            .order_by("-priority", "ready_at", "created_at", "id")[:200]
        )
        return Response({"results": [_task_payload(task) for task in tasks]})


class DeliveryCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        serializer = DeliveryCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            task = complete_delivery_task(task_id=task_id, actor=request.actor_context)
        except DispatchServiceError as error:
            return _error_response(error)
        return Response(_task_payload(task), status=200)
