# Dispatch integration contract

`DispatchTask` is persisted operational work. It never owns an order, a tab,
or financial state.

## READY hook

After `modules.ordering.services.transition_order_item` has persisted a
successful `READY` transition, invoke this inside its existing database
transaction:

```python
from modules.dispatch.services import ensure_delivery_task_for_ready_order_item

ensure_delivery_task_for_ready_order_item(item_id=item.id, actor=actor)
```

The hook is safe after command retries and at-least-once event delivery. It
returns the existing task for the same `OrderItem`; BAR and KITCHEN items from
the same Order remain independent tasks. It takes an immutable destination
snapshot from the active `TabOccupancyAssignment -> Table`, or stores an empty
destination when the Tab has no active physical placement.

Do not call it for a state other than `READY`. A delivery completion is handled
through `complete_delivery_task`, which atomically marks both the task and its
canonical `OrderItem` as delivered and is safe to retry.

## HTTP wiring

Include `modules.dispatch.urls` under `/dispatch/`:

- `GET /dispatch/delivery/` — open delivery queue for the authenticated venue.
- `POST /dispatch/delivery/<task_id>/complete/` — simple explicit completion
  action; repeated calls return the persisted completed task.
