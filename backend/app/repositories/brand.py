"""Commercial brand repository."""
from __future__ import annotations

from app.models import CommercialBrand
from app.repositories.base import BaseRepository


class BrandRepository(BaseRepository):
    model = CommercialBrand


brand_repository = BrandRepository()
