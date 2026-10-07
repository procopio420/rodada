from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from dispatch.models import DispatchEvent, DispatchTask
from dispatch.services import claim_task, complete_task, create_run
from pos.models import ServicePoint, Tab, Venue, Zone
from pos.views import actor_for, command


def task_data(task):
    age = int((timezone.now() - task.created_at).total_seconds())
    severity = "CRITICAL" if age >= 720 else "HIGH" if age >= 480 else "MEDIUM" if age >= 180 else "NORMAL"
    return {"id": task.id, "type": task.type, "state": task.state, "priority": task.priority, "note": task.note,
        "tab_id": task.tab_id, "order_item_id": task.order_item_id, "service_point": task.service_point.code if task.service_point else None,
        "zone": task.zone.name if task.zone else None, "claimed_by": task.claimed_by.display_name if task.claimed_by else None,
        "created_at": task.created_at, "claimed_at": task.claimed_at, "done_at": task.done_at, "age_seconds": age, "severity": severity}


@api_view(["GET", "POST"])
@command
def tasks(request):
    if request.method == "GET":
        venue = Venue.objects.get(pk=request.query_params.get("venue_id", 1)); actor_for(request, venue)
        rows = DispatchTask.objects.filter(venue=venue).exclude(state__in=[DispatchTask.State.DONE, DispatchTask.State.CANCELLED]).select_related("service_point", "zone", "claimed_by")
        return Response([task_data(row) for row in rows])
    tab = Tab.objects.select_related("venue", "service_point__zone").get(pk=request.data["tab_id"]); actor = actor_for(request, tab.venue)
    kind = request.data.get("type", DispatchTask.Type.SERVICE_REQUEST)
    if kind not in {DispatchTask.Type.SERVICE_REQUEST, DispatchTask.Type.BILL_REQUEST, DispatchTask.Type.EXCEPTION}: raise ValidationError("Invalid manual task type.")
    task = DispatchTask.objects.create(venue=tab.venue, tab=tab, service_point=tab.service_point, zone=tab.service_point.zone if tab.service_point else None,
        type=kind, priority=int(request.data.get("priority", 0)), note=request.data.get("note", ""))
    from dispatch.services import emit
    emit(task, "task.created", {"staff_id": actor.id}); return Response(task_data(task), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@command
def claim(request, task_id):
    task = DispatchTask.objects.get(pk=task_id); return Response(task_data(claim_task(task_id, actor_for(request, task.venue))))


@api_view(["POST"])
@command
def done(request, task_id):
    task = DispatchTask.objects.get(pk=task_id); return Response(task_data(complete_task(task_id, actor_for(request, task.venue))))


@api_view(["GET"])
@command
def events(request):
    venue = Venue.objects.get(pk=request.query_params.get("venue_id", 1)); actor_for(request, venue)
    rows = DispatchEvent.objects.filter(venue=venue, id__gt=int(request.query_params.get("after", 0))).order_by("id")[:200]
    return Response([{"id": e.id, "task_id": e.task_id, "kind": e.kind, "payload": e.payload, "created_at": e.created_at} for e in rows])


@api_view(["GET", "POST"])
@command
def zones(request):
    venue = Venue.objects.get(pk=request.data.get("venue_id", 1) if request.method == "POST" else request.query_params.get("venue_id", 1)); actor = actor_for(request, venue)
    if request.method == "POST":
        if not actor.can_manage_finance: raise PermissionDenied("Only managers can configure zones.")
        zone = Zone.objects.create(venue=venue, name=request.data["name"]); return Response({"id": zone.id, "name": zone.name, "active": zone.active}, status=201)
    return Response([{"id": z.id, "name": z.name, "active": z.active} for z in venue.zones.all()])


@api_view(["POST"])
@command
def configure_zone(request, zone_id):
    zone = Zone.objects.select_related("venue").get(pk=zone_id); actor = actor_for(request, zone.venue)
    if not actor.can_manage_finance: raise PermissionDenied("Only managers can configure zones.")
    if "name" in request.data: zone.name = request.data["name"].strip()
    if "active" in request.data: zone.active = bool(request.data["active"])
    zone.save(update_fields=["name", "active"])
    return Response({"id": zone.id, "name": zone.name, "active": zone.active})


@api_view(["POST"])
@command
def create_point(request):
    venue = Venue.objects.get(pk=request.data.get("venue_id", 1)); actor = actor_for(request, venue)
    if not actor.can_manage_finance: raise PermissionDenied("Only managers can configure service points.")
    point = ServicePoint.objects.create(venue=venue, zone=Zone.objects.get(pk=request.data["zone_id"], venue=venue), code=request.data["code"].strip())
    return Response({"id": point.id, "code": point.code, "zone": point.zone.name, "active": point.active}, status=201)


@api_view(["POST"])
@command
def configure_point(request, point_id):
    point = ServicePoint.objects.select_related("venue").get(pk=point_id); actor = actor_for(request, point.venue)
    if not actor.can_manage_finance: raise PermissionDenied("Only managers can configure service points.")
    if "zone_id" in request.data: point.zone = Zone.objects.get(pk=request.data["zone_id"], venue=point.venue)
    if "active" in request.data: point.active = bool(request.data["active"])
    point.save(update_fields=["zone", "active"]); return Response({"id": point.id, "zone": point.zone.name, "active": point.active})


@api_view(["POST"])
@command
def runs(request):
    venue = Venue.objects.get(pk=request.data.get("venue_id", 1)); actor = actor_for(request, venue); zone = Zone.objects.get(pk=request.data["zone_id"], venue=venue)
    run = create_run(venue, zone, actor, request.data["task_ids"]); return Response({"id": run.id, "zone": zone.name, "task_ids": list(run.tasks.values_list("id", flat=True))}, status=201)
