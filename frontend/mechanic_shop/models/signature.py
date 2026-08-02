"""Client-side signature data shape (typed-name acknowledgment)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Signature:
    id: int | None
    signer_role: str
    signer_name: str
    context: str | None = None
    signed_at: datetime | None = None

    @classmethod
    def from_api(cls, data: dict) -> Signature:
        return cls(
            id=data.get("id"),
            signer_role=data["signer_role"],
            signer_name=data["signer_name"],
            context=data.get("context"),
            signed_at=datetime.fromisoformat(data["signed_at"]) if data.get("signed_at") else None,
        )

    def to_create_payload(self) -> dict:
        return {
            "signer_role": self.signer_role,
            "signer_name": self.signer_name,
            "context": self.context,
        }
