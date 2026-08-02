"""Tests for SignatureRepository against a real (temp) SQLite database."""

from __future__ import annotations

from backend.app.models.signature import Signature
from backend.app.repositories.signature_repository import SignatureRepository
from shared.mechanic_shop_shared.enums import EntityType, SignerRole


def test_list_for_entity_scoped_and_ordered(db) -> None:
    repo = SignatureRepository(db)
    db.add(
        Signature(
            entity_type=EntityType.REPAIR_ORDER.value,
            entity_id=1,
            signer_role=SignerRole.CUSTOMER.value,
            signer_name="Jane Doe",
        )
    )
    db.add(
        Signature(
            entity_type=EntityType.REPAIR_ORDER.value,
            entity_id=2,
            signer_role=SignerRole.CUSTOMER.value,
            signer_name="Other Person",
        )
    )
    db.flush()

    signatures = repo.list_for_entity(EntityType.REPAIR_ORDER.value, 1)
    assert len(signatures) == 1
    assert signatures[0].signer_name == "Jane Doe"
