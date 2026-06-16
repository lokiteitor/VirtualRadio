export const meta = {
  name: 'vr-backend-api',
  description: 'Build VirtualRadio API layer + integrations by cloning the Stations reference slice',
  phases: [
    { title: 'Resources', detail: 'CRUD+suggest resources cloned from Stations' },
    { title: 'Music+Episodes', detail: 'music library, episodes/jobs, audio serving' },
    { title: 'Integrations', detail: 'Gemini TTS client + pydub audio engine' },
  ],
}

const ROOT = '/home/ddelgado/git/lab/VirtualRadio/backend'
const PROTO = '/home/ddelgado/git/lab/VirtualRadio/prototipo/backend'

const CONTRACT = `
You are extending an existing Flask 3 + SQLAlchemy 2 + Marshmallow backend for "VirtualRadio".
Working directory: ${ROOT}

# ABSOLUTE RULES
- ONLY CREATE the new files listed in your task. NEVER edit shared/foundation files
  (app/__init__.py, app/routes/__init__.py, app/extensions.py, app/config, app/common/*,
  app/auth/*, app/models/*, app/repositories/base.py, app/schemas/common.py, the Stations
  files, requirements.txt, migrations). They are already correct.
- Blueprint auto-discovery: any module in app/routes/ exposing a module-level
  a module-level "bp" Blueprint is auto-registered under /api/v1. So your route
  paths must NOT include /api/v1 (e.g. use "/news", "/news/<id>", "/news/suggest").
- Mirror the EXACT patterns of the reference slice. READ these files FIRST and copy their style:
    app/schemas/station.py, app/repositories/station.py,
    app/controllers/station.py, app/routes/station.py
- Also READ for context: app/schemas/common.py (BaseSchema, load_or_422, SuggestRequestSchema),
  app/repositories/base.py (BaseRepository, scoped_query, coerce_uuid),
  app/common/responses.py (success/created/accepted/no_content),
  app/common/errors.py (NotFoundError, ConflictError, ValidationFailedError, ForbiddenError),
  app/auth/permissions.py (check_permission), app/integrations/llm_client.py
  (llm_client.complete_json(prompt, system) -> dict/list or None), and the models under app/models/.
- For the /suggest endpoints, PORT the fallback content from the prototype:
  ${PROTO}/app.py (functions suggest_station/suggest_news/suggest_brand/suggest_commercial/suggest_character).
  Always try llm_client.complete_json(...) first, then fall back to ported procedural templates.
- Response contract: success(data, meta) -> {"data":..., "meta":...}; never return bare dicts.
- Ownership: NEVER read owner_id from the body — BaseRepository.create sets it from the JWT.
  Accessing another user's resource must 404 (BaseRepository.get already does this).
- Enums: import from app.models.enums and serialize with marshmallow fields.Enum(EnumClass, by_value=True).
- Datetimes: fields.DateTime. UUIDs: fields.UUID.
- Controllers return plain serializable data; routes wrap with success()/created()/no_content().
- Decorate every route with @check_permission("<resource>", "<action>") matching the RBAC doc.
- Keep code clean, typed where the reference is, and import-safe (no import-time DB/network calls).

After writing, return the structured report (files created + notes + any blockers).
`

const REPORT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['unit', 'files_created', 'notes'],
  properties: {
    unit: { type: 'string' },
    files_created: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
    blockers: { type: 'string' },
  },
}

// ---------------------------------------------------------------- Phase 1: resources
const RESOURCES = [
  {
    label: 'news',
    prompt: `Build the NEWS resource (model app.models.NewsItem, permission name "news").
Create: app/schemas/news.py, app/repositories/news.py, app/controllers/news.py, app/routes/news.py.
Input fields: headline(required,<=300), summary(nullable), full_script(nullable),
  category(NewsCategory enum, required), tone(NewsTone enum, required),
  is_active(bool, default true), expires_at(datetime, nullable).
Output: id, owner_id, all input fields, created_at, updated_at.
Endpoints (paths WITHOUT /api/v1):
  GET /news  -> list; supports query params is_active (bool) and category (NewsCategory). order by created_at desc.
  POST /news -> create (news:create)
  POST /news/suggest -> news:suggest (port suggest_news fallbacks; honor context.category/context.tone hints;
        coerce returned category/tone to valid enum values, else fallback)
  GET /news/<id> -> news:read ; PUT /news/<id> -> news:update ; DELETE /news/<id> -> news:delete (204)
Use marshmallow fields.Enum(NewsCategory, by_value=True) and fields.Enum(NewsTone, by_value=True).`,
  },
  {
    label: 'brands',
    prompt: `Build the BRANDS resource (model app.models.CommercialBrand, permission name "brand").
Create: app/schemas/brand.py, app/repositories/brand.py, app/controllers/brand.py, app/routes/brand.py.
Input: name(required,<=150), description(nullable), industry(nullable,<=100), slogan(nullable,<=255), is_active(bool default true).
Output: id, owner_id, all input fields, created_at, updated_at.
Endpoints: GET /brands (order by name asc), POST /brands, POST /brands/suggest (brand:suggest, port suggest_brand fallbacks),
  GET /brands/<id>, PUT /brands/<id>, DELETE /brands/<id> (204, cascades to commercials via DB).`,
  },
  {
    label: 'commercials',
    prompt: `Build the COMMERCIALS resource (model app.models.Commercial, permission name "commercial").
Create: app/schemas/commercial.py, app/repositories/commercial.py, app/controllers/commercial.py, app/routes/commercial.py.
Input: brand_id(UUID required), title(required,<=200), script(required), duration(float default 30),
  campaign(nullable,<=150), is_active(bool default true).
Output: id, owner_id, brand_id, title, script, duration, campaign, is_active, created_at, updated_at.
Endpoints:
  GET /commercials -> list; supports query param brand_id (UUID). order by created_at desc.
  POST /commercials -> create; MUST validate the brand exists and is owned by the user
    (use scoped_query(CommercialBrand) or a BrandRepository.get_or_none); 404 if not -> raise NotFoundError
    ("La marca indicada no existe o pertenece a otro usuario").
  POST /commercials/suggest -> commercial:suggest. Requires brand_id (from body or context); load the owned brand
    (404 if missing); port suggest_commercial fallbacks (brand-name based). Return title/campaign/script.
  GET /commercials/<id>, PUT /commercials/<id>, DELETE /commercials/<id> (204).`,
  },
  {
    label: 'characters',
    prompt: `Build the CHARACTERS resource (models app.models.Character and app.models.CharacterMemory, permission "character").
Create: app/schemas/character.py, app/repositories/character.py, app/controllers/character.py, app/routes/character.py.
Character input: name(required,<=150), role(nullable,<=150), description(nullable), personality(nullable), station_affinity(nullable).
Character output: id, owner_id, name, role, description, personality, station_affinity,
  first_appearance, last_appearance, created_at, updated_at.
CharacterMemory output schema: id, owner_id, character_id, episode_id(nullable), memory, importance, created_at, updated_at.
Endpoints:
  GET /characters (order by name asc), POST /characters, POST /characters/suggest (character:suggest, port suggest_character fallbacks),
  GET /characters/<id>, PUT /characters/<id>, DELETE /characters/<id> (204),
  GET /characters/<id>/memories -> permission character:read_memories. First load the owned character (404 if not),
    then return its memories (scoped_query(CharacterMemory) filtered by character_id, order by created_at desc) as a list.`,
  },
  {
    label: 'story-events',
    prompt: `Build the STORY EVENTS resource (model app.models.StoryEvent, permission name "story_event").
Create: app/schemas/story_event.py, app/repositories/story_event.py, app/controllers/story_event.py, app/routes/story_event.py.
Input: title(required,<=200), description(nullable), related_characters(nullable),
  status(StoryStatus enum, optional, default "active"), resolved_at(datetime nullable).
Output: id, owner_id, all input fields, created_at, updated_at.
Endpoints (NOTE the hyphen in the URL, NOT underscore):
  GET /story-events -> list; supports query param status (StoryStatus). order by created_at desc.
  POST /story-events, GET /story-events/<id>, PUT /story-events/<id>, DELETE /story-events/<id> (204).
There is NO suggest endpoint for story events. Use fields.Enum(StoryStatus, by_value=True).`,
  },
  {
    label: 'universe',
    prompt: `Build the UNIVERSE summary endpoint (permission name "universe", action "read").
Create ONLY: app/controllers/universe.py and app/routes/universe.py (no schema/repository needed).
Endpoint: GET /universe/summary -> success(counts).
counts is an object with integer fields, each a scoped count for the current user:
  stations, episodes, news_items, brands, commercials, characters, music_tracks, story_events.
Use scoped_query(Model).count() (import scoped_query from app.repositories.base) for each model
  (Station, Episode, NewsItem, CommercialBrand, Commercial, Character, MusicTrack, StoryEvent).
Route: @check_permission("universe", "read").`,
  },
]

// ---------------------------------------------------------------- Phase 2: music + episodes/jobs
const MUSIC = {
  label: 'music',
  prompt: `Build the MUSIC LIBRARY resource (model app.models.MusicTrack, permission name "music").
Create: app/schemas/music.py, app/repositories/music.py, app/controllers/music.py, app/routes/music.py.
Use mutagen for MP3 metadata/duration (from mutagen import File as MutagenFile; or mutagen.mp3.MP3) and hashlib for MD5.
The user's music folder is os.path.join(current_app.config["MEDIA_ROOT"], "music", str(owner_id)). Create it if missing.
MusicTrack output: id, owner_id, file_path, title, artist, album, duration, file_hash, created_at, updated_at.
Endpoints:
  GET /music -> music:read. Return list ordered by title asc. meta MUST include {"count": N, "total_duration": <sum of durations>}.
  POST /music/upload -> music:upload. multipart/form-data field "file"; reject non-.mp3 (422 ValidationFailedError);
     secure_filename; save into the user's music folder; compute MD5; if (owner_id,file_hash) already exists -> 409 ConflictError;
     extract title/artist/album/duration via mutagen (fallbacks: title from filename, artist None, duration from MP3 info.length);
     persist MusicTrack; return 201 created(track).
  POST /music/scan -> music:scan. Walk the user's music folder: add new .mp3 files (skip ones whose hash already exists),
     remove DB rows whose file no longer exists on disk. Return success({"added": a, "removed": r, "total": t}).
  DELETE /music/<id> -> music:delete. 404 if not owned; delete the DB row AND the file from disk (best-effort). Return 204.
file_path stored should be the absolute path on disk. Keep all FS ops resilient (wrap os.remove in try/except).`,
}

const EPISODES = {
  label: 'episodes-jobs',
  prompt: `Build the EPISODES and JOBS resources (models app.models.Episode, app.models.GenerationJob, app.models.Station).
Create: app/schemas/episode.py, app/schemas/job.py, app/repositories/episode.py, app/repositories/job.py,
        app/controllers/episode.py, app/controllers/job.py, app/routes/episode.py, app/routes/job.py.
Permissions: episodes use "episode", jobs use "job".
Episode output schema: id, owner_id, station_id, title, duration, script_json (a list of segment dicts -> use
  fields.List(fields.Dict()) or fields.Raw), audio_path(nullable), created_at, updated_at.
Job output schema: id, owner_id, station_id, episode_id(nullable), status (fields.Enum(JobStatus, by_value=True)),
  progress (int), error(nullable), created_at, updated_at.
Endpoints:
  GET /episodes -> episode:read. Optional query param station_id (UUID) filter. order by created_at desc.
  GET /episodes/<id> -> episode:read. Return the episode incl parsed script_json.
  DELETE /episodes/<id> -> episode:delete. 404 if not owned; delete DB row AND its MP3 file from disk
     (absolute path = os.path.join(MEDIA_ROOT, episode.audio_path) when audio_path set). Return 204.
  GET /episodes/<id>/audio -> episode:read. Owner check (404). If no audio_path or file missing -> 404
     ApiError. Otherwise stream the MP3 with Range support: use flask.send_file(abs_path, mimetype="audio/mpeg",
     conditional=True) so Range requests yield 206. (send_file with conditional=True handles Range + 206 automatically.)
  POST /episodes/generate -> episode:generate. Body {station_id}. Validate the station is owned (404 with message
     "La estación indicada no existe o pertenece a otro usuario"). Create a GenerationJob (status queued, progress 0)
     for that station/owner, commit. Then enqueue the Celery task by LAZY import inside the function:
        from app.tasks.generation import generate_episode_task
        generate_episode_task.delay(str(job.id))
     Wrap the enqueue in try/except so a missing broker does not 500 the request (log a warning).
     Return 202 accepted(job_dump) using app.common.responses.accepted and the Job schema.
  GET /jobs/<id> -> job:read. Return the job (404 if not owned).
Use BaseRepository subclasses. For the station ownership check, use scoped_query(Station) or a small StationRepository import
  (you may import app.repositories.station.station_repository).`,
}

// ---------------------------------------------------------------- Phase 3: integrations
const TTS = {
  label: 'tts_client',
  prompt: `Create app/integrations/tts_client.py: a Gemini TTS client with caching and graceful degradation.
READ ${PROTO}/audio_engine.py (get_tts_audio, apply_telephony_filter) for the caching/telephony reference.
Requirements:
- Public API:
    get_tts_audio(text: str, role: str) -> pydub.AudioSegment   # synthesize (or load from cache)
    apply_telephony_filter(segment) -> AudioSegment             # bandpass 300-3000 Hz (high_pass_filter(300).low_pass_filter(3000))
- Cache: hash = md5(f"{text.strip()}_{role}"). Binary lives at MEDIA_ROOT/vox/vox_<hash>.mp3. If the file exists, load and return it.
  Maintain a Redis index "tts:{hash}" -> path using redis.from_url(current_app.config["REDIS_URL"]); wrap ALL redis use in
  try/except so missing Redis never breaks synthesis (filesystem cache is the source of truth).
- Synthesis path when GEMINI_API_KEY is set: call the Gemini TTS model (config GEMINI_TTS_MODEL) generateContent endpoint with
  responseModalities ["AUDIO"] and a prebuilt voice per role (define ROLE_VOICES dict for host/caller/reporter/commercial, e.g.
  host->"Charon", reporter->"Kore", caller->"Puck", commercial->"Fenrir"). The response returns base64-encoded PCM in
  candidates[0].content.parts[0].inlineData.data (signed 16-bit little-endian, 24000 Hz, mono). Decode base64, build
  AudioSegment(data, sample_width=2, frame_rate=24000, channels=1), export to the cache mp3, and return it.
- Fallback (no key, or ANY error/exception): return a soft synthetic clip sized to the text (like the prototype:
  a -30dB 100ms Sine(440) beep + silence sized by word count at ~3 words/sec, min 500ms). Never raise.
- Empty/blank text -> return AudioSegment.silent(duration=500).
- Read MEDIA_ROOT/REDIS_URL/GEMINI_API_KEY/GEMINI_TTS_MODEL from current_app.config (fallback to os.environ when no app context).
- Ensure the vox directory exists before writing. Keep imports light; do not call the network at import time.`,
}

const AUDIO = {
  label: 'audio_engine',
  prompt: `Create app/integrations/audio_engine.py: the pydub/FFmpeg audio production engine.
READ ${PROTO}/audio_engine.py thoroughly and PORT it to this codebase (paths come from MEDIA_ROOT, not a static/ dir).
Directory layout under MEDIA_ROOT: music/<owner_id>/ , vox/ , fx/ , episodes/ . Provide ensure_dirs(owner_id=None).
Public API the pipeline will use:
  - ensure_fx_assets() -> generate fx/static_hum.mp3 and fx/sweeper.mp3 if missing (port generate_fx_assets).
  - generate_mock_music(owner_id) -> if the user's music/<owner_id>/ folder has no mp3s, synthesize 3 chiptune tracks
       (synth_pastoral.mp3, synth_highway.mp3, synth_ambient.mp3) into it (port generate_synth_track + the 3 track defs).
       Return the list of created file paths.
  - compile_episode(episode, tracks, synth_fn) -> (relative_audio_path, duration_seconds)
       * episode: the Episode model (has .id and .script_json list of segments).
       * tracks: ordered list of the user's MusicTrack rows (for resolving music segment track_id by index).
       * synth_fn: callable(text, role)->AudioSegment for speech (pass app.integrations.tts_client.get_tts_audio).
       Walk segments (speech/music/fx) exactly like the prototype compile_episode: for speech synthesize via synth_fn,
       apply telephony filter (use tts_client.apply_telephony_filter) + crackle when effect=="telephony", else overlay
       static hum; for music resolve the file by track_id index (fallback to a random owned track or silence), slice ~40s,
       fade in/out, overlay a sweeper at the start; for fx append sweeper/static. Normalize the final mix, export to
       MEDIA_ROOT/episodes/<episode.id>.mp3, and RETURN ("episodes/<episode.id>.mp3", duration_seconds).
  Import tts_client lazily inside compile_episode to avoid import cycles. Read MEDIA_ROOT from current_app.config
  (fallback os.environ). Keep import-time side-effect free (no dir creation at import).`,
}

// ============================================================ run
phase('Resources')
log('Phase 1: cloning ' + RESOURCES.length + ' resources from the Stations template')

const all = await parallel([
  ...RESOURCES.map((r) => () =>
    agent(CONTRACT + '\n\n# YOUR TASK\n' + r.prompt, {
      label: r.label, phase: 'Resources', schema: REPORT_SCHEMA,
    })
  ),
  () => agent(CONTRACT + '\n\n# YOUR TASK\n' + MUSIC.prompt, {
    label: MUSIC.label, phase: 'Music+Episodes', schema: REPORT_SCHEMA,
  }),
  () => agent(CONTRACT + '\n\n# YOUR TASK\n' + EPISODES.prompt, {
    label: EPISODES.label, phase: 'Music+Episodes', schema: REPORT_SCHEMA,
  }),
  () => agent(CONTRACT + '\n\n# YOUR TASK\n' + TTS.prompt, {
    label: TTS.label, phase: 'Integrations', schema: REPORT_SCHEMA,
  }),
  () => agent(CONTRACT + '\n\n# YOUR TASK\n' + AUDIO.prompt, {
    label: AUDIO.label, phase: 'Integrations', schema: REPORT_SCHEMA,
  }),
])

const ok = all.filter(Boolean)
log('Completed ' + ok.length + '/' + all.length + ' units')
return {
  units: ok,
  blockers: ok.filter((u) => u && u.blockers).map((u) => ({ unit: u.unit, blockers: u.blockers })),
}
