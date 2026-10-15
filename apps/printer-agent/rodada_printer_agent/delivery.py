"""One in-flight attempt journal, never an offline queue or replay mechanism."""

import time
from typing import Any

from .transports import Transports
from .worker import Api, InstallationState, StateStore


class DeliveryCycle:
    def __init__(self, transports: Transports):
        self.transports = transports

    def acknowledge(self, api: Api, state: InstallationState, store: StateStore) -> bool:
        pending = state.pending_result
        if not pending:
            return True
        store.save(state)
        response = api.post(
            "me/jobs/" + str(pending["job_id"]) + "/result/",
            {key: value for key, value in pending.items() if key != "job_id"},
            state.credential,
        )
        if not isinstance(response.get("accepted"), bool):
            raise TypeError("Invalid result acknowledgment.")
        # Rejected fenced/expired results must not be replayed physically either.
        state.pending_result = {}
        store.save(state)
        return True

    def tick(self, api: Api, state: InstallationState, store: StateStore, enabled: bool) -> None:
        # Always reconcile an interrupted/uncertain attempt before another claim.
        self.acknowledge(api, state, store)
        api.post(
            "me/discovery/",
            {"protocol_version": 1, "printers": self.transports.inventory()},
            state.credential,
        )
        if not enabled:
            return
        requested_at = time.monotonic()
        response = api.post("me/claim/", {"protocol_version": 1}, state.credential)
        job: dict[str, Any] | None = response.get("job")
        if job is None:
            return
        # No persistent document or local print queue. Only the fenced result survives.
        pending = {
            key: job[key] for key in ("job_id", "attempt_token", "route_id", "route_version")
        }
        pending["outcome"] = "DELIVERY_UNCERTAIN"
        state.pending_result = pending
        store.save(state)  # Mandatory before any potentially side-effectful transport.
        ttl = job.get("lease_seconds")
        if type(ttl) is not int or not 0 <= ttl <= 60:
            raise ValueError("Invalid bounded claim TTL.")
        deadline = requested_at + ttl
        try:
            content = self.transports.prepare(job)
        except (ValueError, KeyError, TypeError):
            pending["outcome"] = "FAILED_FINAL"
        else:
            if time.monotonic() < deadline:
                pending["outcome"] = self.transports.submit(
                    job, content, deadline=deadline
                ).outcome.value
        store.save(state)
        self.acknowledge(api, state, store)
