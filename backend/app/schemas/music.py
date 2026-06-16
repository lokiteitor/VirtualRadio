"""Music track response schema."""
from __future__ import annotations

from marshmallow import fields

from app.schemas.common import BaseSchema


class MusicTrackSchema(BaseSchema):
    id = fields.UUID(dump_only=True)
    owner_id = fields.UUID(dump_only=True)
    file_path = fields.Str()
    title = fields.Str(allow_none=True)
    artist = fields.Str(allow_none=True)
    album = fields.Str(allow_none=True)
    duration = fields.Float(allow_none=True)
    file_hash = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


music_track_schema = MusicTrackSchema()
music_tracks_schema = MusicTrackSchema(many=True)
