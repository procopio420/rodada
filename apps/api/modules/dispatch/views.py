from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.dispatch.models import DispatchTask, DispatchTaskState, DispatchTaskType
from modules.dispatch.serializers import DeliveryCompleteSerializer, DispatchTaskSerializer
from modules.dispatch.services import DispatchServiceError, complete_delivery_task
from modules.dispatch.targets import StaffTargets, staff_tasks
from modules.hospitality.tab_display import tab_location_labels


def _error_response(error: DispatchServiceError) -> Response:
    payload = {"code": error.code, "message": error.message}
    if error.details:
        payload.update(error.details)
    return Response(payload, status=error.status_code)


def _task_payload(task: DispatchTask, *, current_locations=None, targets=None) -> dict:
    payload = DispatchTaskSerializer(task).data
    payload["task_type"] = task.task_type
    if current_locations is not None and task.order_item_id:
        # Prefer the current live placement while preserving the original task
        # snapshot for audit, retries and historical printouts.
        current = current_locations.get(str(task.order_item.order.tab_id))
        if current:
            payload["destination_label"] = current
        elif task.destination_table_id:
            payload["destination_label"] = "Sem mesa atual · confirmar destino"
    payload["age_seconds"] = (
        max(0, int((timezone.now() - task.ready_at).total_seconds())) if task.ready_at else 0
    )
    payload.update(_target_payload(task, targets))
    if task.order_item_id:
        payload.update(
            order_id=str(task.order_item.order_id),
            fulfillment_station=task.order_item.fulfillment_station_snapshot or None,
            item_state=task.order_item.state,
        )
    return payload


def _target_payload(task, targets=None):
    targets = targets or StaffTargets([task], venue_id=task.venue_id)
    return {"target_version": 1, "target": targets.target(task), "zone_id": targets.zone_id(task)}


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
        tasks = list(staff_tasks(tasks))
        targets = StaffTargets(tasks, venue_id=request.auth.venue_id)
        current, _ = tab_location_labels({task.order_item.order.tab_id for task in tasks if task.order_item_id})
        return Response({"results": [_task_payload(task, current_locations=current, targets=targets) for task in tasks]})


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


def _service_payload(task, *, targets=None):
    return {
        "id": str(task.id), "task_type": task.task_type, "state": task.state,
        "destination_label": task.destination_label,
        "claimed_by_id": str(task.claimed_by_id) if task.claimed_by_id else None,
        "claimed_at": task.claimed_at, "created_at": task.created_at,
        "completed_at": task.completed_at,
        "age_seconds": max(0, int((timezone.now() - task.created_at).total_seconds())),
        **_target_payload(task, targets),
    }


class ServiceRequestQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = DispatchTask.objects.filter(
            venue_id=request.auth.venue_id,
            task_type__in=(DispatchTaskType.SERVICE_REQUEST, DispatchTaskType.BILL_REQUEST),
            state__in=(DispatchTaskState.OPEN, DispatchTaskState.CLAIMED),
        ).order_by("-priority", "created_at", "id")[:200]
        tasks = list(staff_tasks(tasks))
        targets = StaffTargets(tasks, venue_id=request.auth.venue_id)
        return Response({"results": [_service_payload(task, targets=targets) for task in tasks]})

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


class DispatchTaskDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, task_id):
        task = staff_tasks(DispatchTask.objects.filter(
            pk=task_id, venue_id=request.auth.venue_id,
        )).first()
        if task is None:
            return Response({"code": "DISPATCH_TASK_NOT_FOUND"}, status=404)
        if task.task_type == DispatchTaskType.DELIVERY:
            current, _ = tab_location_labels([task.order_item.order.tab_id]) if task.order_item_id else ({}, {})
            return Response(_task_payload(task, current_locations=current))
        return Response(_service_payload(task))
