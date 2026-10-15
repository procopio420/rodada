"""S2 polling lifecycle only. No spooler, claims or local work queue."""

import secrets
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

from .client import AgentHttpError

VERSION = "0.3.0"


@dataclass
class InstallationState:
    installation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proof: str = field(default_factory=lambda: "rpp_" + secrets.token_urlsafe(32), repr=False)
    request_id: str = ""
    credential: str = field(default="", repr=False)
    code: str = ""
    expires_at: str = ""
    activated: bool = False
    authorization_lost: bool = False
    pending_result: dict[str, Any] = field(default_factory=dict, repr=False)


class StateStore(Protocol):
    def load(self) -> InstallationState: ...
    def save(self, state: InstallationState) -> None: ...
    def diagnostic(self, data: dict[str, str]) -> None: ...


class Api(Protocol):
    def post(self, path: str, body: dict[str, Any], token: str = "") -> dict[str, Any]: ...


class Delivery(Protocol):
    def tick(
        self, api: Api, state: InstallationState, store: StateStore, enabled: bool
    ) -> None: ...


class Worker:
    def __init__(self, store: StateStore, api: Api, delivery: Delivery | None = None):
        self.store, self.api, self.delivery = store, api, delivery
        self.state = store.load()
        self.store.save(self.state)  # Persist identity/proof before the first network call.

    def publish(self, state: str) -> None:
        self.store.diagnostic(
            {
                "state": state,
                "code": self.state.code,
                "expires_at": self.state.expires_at,
                "version": VERSION,
            }
        )

    def tick(self, label: str) -> None:
        state = self.state
        if state.authorization_lost:
            self.publish("AUTHORIZATION_LOST")
            return
        try:
            if not state.credential:
                if not state.request_id:
                    data = self.api.post(
                        "pairing/start/",
                        {
                            "installation_id": state.installation_id,
                            "label": label,
                            "proof": state.proof,
                        },
                    )
                    state.request_id, state.code = str(data["request_id"]), str(data["code"])
                    state.expires_at = str(data["expires_at"])
                    self.store.save(state)
                response = self.api.post(
                    "pairing/status/", {"request_id": state.request_id, "proof": state.proof}
                )
                if response.get("state") != "APPROVED":
                    self.publish("PENDING_PAIRING")
                    return
                state.credential = str(response["credential"])
                if not state.credential.startswith("rpa_") or len(state.credential) != 47:
                    raise ValueError("Invalid credential response.")
                self.store.save(state)  # Crash/response loss never loses the only credential.
            if not state.activated:
                # Retry durable persistence even after an earlier save failure.
                self.store.save(state)
                self.api.post("me/activate/", {}, state.credential)
                state.activated = True
                state.code, state.expires_at, state.proof = "", "", ""
                self.store.save(state)
            data = self.api.post(
                "me/heartbeat/", {"protocol_version": 1, "version": VERSION}, state.credential
            )
            if data.get("protocol_version") != 1 or not isinstance(
                data.get("delivery_enabled"), bool
            ):
                raise ValueError("Unsupported service contract.")
            if self.delivery is not None:
                self.delivery.tick(self.api, state, self.store, data["delivery_enabled"])
            self.publish("ONLINE")
        except AgentHttpError as exc:
            if exc.status == 401 or (exc.status == 409 and not state.credential):
                state.credential, state.proof, state.code = "", "", ""
                state.authorization_lost = True
                self.store.save(state)
                self.publish("AUTHORIZATION_LOST")
            elif exc.status == 410 and not state.credential:
                # Expired code: retry start with the original installation/proof.
                state.request_id, state.code, state.expires_at = "", "", ""
                self.store.save(state)
                self.publish("PAIRING_RETRY")
            else:
                self.publish("UNAVAILABLE")
        except (OSError, ValueError, TypeError, KeyError):
            self.publish("OFFLINE")
