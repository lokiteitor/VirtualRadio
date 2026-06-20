"""Per-station music selection request schema.

The response reuses :class:`MusicTrackSchema` (the assigned tracks are returned
with their full metadata); only the input — a list of track ids — needs its own
schema here.
"""
from __future__ import annotations

from marshmallow import fields

from app.schemas.common import BaseSchema


class StationMusicInputSchema(BaseSchema):
    # Full replacement of the station's selection; an empty list clears it
    # (the station then falls back to the owner's whole library).
    track_ids = fields.List(fields.UUID(), required=True)


station_music_input_schema = StationMusicInputSchema()
