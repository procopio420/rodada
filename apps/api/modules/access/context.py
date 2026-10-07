from dataclasses import dataclass

from modules.access.models import StaffSession


@dataclass(frozen=True)
class ActorContext:
    venue_id: object
    staff_id: object
    session_id: object
    device_id: object | None

    @classmethod
    def from_session(cls, session: StaffSession) -> "ActorContext":
        return cls(
            venue_id=session.venue_id,
            staff_id=session.staff_member_id,
            session_id=session.id,
            device_id=session.device_id,
        )

    def audit_kwargs(self) -> dict:
        return {
            "venue_id": self.venue_id,
            "actor_staff_id": self.staff_id,
            "actor_session_id": self.session_id,
            "device_id": self.device_id,
        }
