"""Signature schemas (typed-name acknowledgment, not a drawn image)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from shared.mechanic_shop_shared.enums import SignerRole


class SignatureCreate(BaseModel):
    signer_role: SignerRole
    signer_name: str
    context: str | None = None


class SignatureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    signer_role: str
    signer_name: str
    context: str | None
    signed_at: datetime
