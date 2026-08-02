"""Shop header info for printable documents.

Deliberately minimal: sourced from plain env-overridable ``Settings``
fields, not a database table. A real shop-settings table + Settings screen
(shop info, labor rate, tax rates, invoice numbering) is Phase 3/4 scope --
``invoice_pdf.py`` takes this small value object so swapping in a real
settings table later requires no change to the renderer itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.config import Settings


@dataclass
class ShopInfo:
    name: str
    address: str
    phone: str
    email: str

    @classmethod
    def from_settings(cls, settings: Settings) -> ShopInfo:
        return cls(
            name=settings.shop_name,
            address=settings.shop_address,
            phone=settings.shop_phone,
            email=settings.shop_email,
        )
