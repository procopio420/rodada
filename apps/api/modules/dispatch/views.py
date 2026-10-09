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
            .select_related("destination_table", "order_item__order__tab")
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


def _service_payload(task):
    return {
        "id": str(task.id), "task_type": task.task_type, "state": task.state,
        "destination_label": task.destination_label,
        "claimed_by_id": str(task.claimed_by_id) if task.claimed_by_id else None,
        "claimed_at": task.claimed_at, "created_at": task.created_at,
        "completed_at": task.completed_at,
        "age_seconds": max(0, int((timezone.now() - task.created_at).total_seconds())),
    }


class ServiceRequestQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = DispatchTask.objects.filter(
            venue_id=request.auth.venue_id,
            task_type__in=(DispatchTaskType.SERVICE_REQUEST, DispatchTaskType.BILL_REQUEST),
            state__in=(DispatchTaskState.OPEN, DispatchTaskState.CLAIMED),
        ).order_by("-priority", "created_at", "id")[:200]
        return Response({"results": [_service_payload(task) for task in tasks]})

    def post(self, request):
        from .serializers import StaffServiceRequestSerializer
        from .services import create_service_request
        serializer = StaffServiceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            task = create_service_request(actor=request.actor_context, **serializer.validated_data)
        except DispatchServiceError as error:
            return _error_response(error)
        return Response(_service_payload(task), status=200 if task._request_replay else 201)


class ServiceRequestClaimView(APIView):
    permission_classes = [IsAuthenticated]
    complete = False

    def post(self, request, task_id):
        from .services import update_service_request
        try:
            task = update_service_request(task_id=task_id, actor=request.actor_context, complete=self.complete)
        except DispatchServiceError as error:
            return _error_response(error)
        return Response(_service_payload(task))


class ServiceRequestCompleteView(ServiceRequestClaimView):
    complete = True
