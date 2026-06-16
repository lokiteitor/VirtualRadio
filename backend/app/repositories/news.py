"""News repository."""
from __future__ import annotations

from app.models import NewsItem
from app.repositories.base import BaseRepository


class NewsRepository(BaseRepository):
    model = NewsItem


news_repository = NewsRepository()
