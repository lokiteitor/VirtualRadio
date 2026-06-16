export const meta = {
  name: 'vr-backend-pipeline',
  description: 'Build the VirtualRadio Celery generation pipeline + script agents, then verify/fix it',
  phases: [
    { title: 'Build', detail: 'agents package + generation task + maintenance tasks' },
    { title: 'Verify', detail: 'adversarial review of status transitions, fallback, scoping' },
  ],
}

const ROOT = '/home/ddelgado/git/lab/VirtualRadio/backend'
const PROTO = '/home/ddelgado/git/lab/VirtualRadio/prototipo/backend'

const INTERFACE = `
Working directory: ${ROOT}
This backend already has: models (app.models.*), owner-scoped repositories
(app.repositories.base.BaseRepository, scoped_query), the integrations
app.integrations.llm_client (complete/complete_json), app.integrations.tts_client
(get_tts_audio(text, role)->AudioSegment, apply_telephony_filter), and
app.integrations.audio_engine (ensure_fx_assets(), generate_mock_music(owner_id),
compile_episode(episode, tracks, synth_fn)->(relative_path, duration_seconds)).
Celery is wired: define tasks with celery.shared_task. Tasks run inside the Flask app context.

PORT the script logic from the prototype:
  ${PROTO}/generator.py  (STATIONS table, the big LLM prompt, and procedural_script)
  ${PROTO}/app.py        (run_generation_pipeline status flow)

# PINNED INTERFACE (every module must conform exactly)
app.services.agents.episode_assembly.build_episode(owner_id, station) -> dict with keys:
    title:        str
    script_json:  list[segment dict]  (segment = {type, speaker, text, voice_id, effect, track_id, duration_seconds})
    character_id: UUID | None         (the caller character that participated, for memory)
    caller_summary: str | None        (a one-line memory derived from the caller's lines)
    track_ids:    list[UUID]          (the ordered selected MusicTrack ids; script music segments use track_id = index into this list)
  build_episode orchestrates the agents:
    - episode_planner: picks up to 3 random owned MusicTrack rows, 1 active NewsItem, 1 active Commercial (+its brand),
      1 Character (+ up to 3 recent memories) using scoped_query(...). All queries filtered by owner_id.
    - news_agent / commercial_agent / character_agent / host_agent: produce their text/segments.
    - It first tries the LLM (llm_client.complete_json with the ported prompt) for a full script; on None/invalid it
      builds the script procedurally (port procedural_script). Either way returns the dict above.

app.tasks.generation.generate_episode_task  -- a @shared_task(name="tasks.generate_episode") taking a job_id (str).
  Flow (persist GenerationJob state at each step; statuses from app.models.enums.JobStatus):
    1. load the GenerationJob by id (return early if missing). status=PLANNING, progress=10, commit.
    2. load its Station (by station_id, owner-scoped). ensure media: audio_engine.ensure_fx_assets();
       audio_engine.generate_mock_music(job.owner_id).
    3. result = episode_assembly.build_episode(job.owner_id, station).
    4. create Episode(owner_id=job.owner_id, station_id=station.id, title=result["title"],
       script_json=result["script_json"]); commit; set job.episode_id = episode.id.
    5. status=SYNTHESIZING, progress=50, commit.
    6. status=MIXING, progress=75, commit. Resolve tracks = [MusicTrack rows for result["track_ids"] in order].
       rel_path, duration = audio_engine.compile_episode(episode, tracks, tts_client.get_tts_audio).
       episode.audio_path = rel_path; episode.duration = duration; commit.
    7. If result["character_id"]: append a CharacterMemory(owner_id, character_id, episode_id=episode.id,
       memory=result["caller_summary"] or "...", importance=5) and update that Character.last_appearance = now(); commit.
    8. status=COMPLETED, progress=100, commit.
    On ANY exception: rollback, set job.status=FAILED and job.error=str(exc), commit, and log the traceback.

app.tasks.maintenance:
    @shared_task(name="tasks.cleanup_old_jobs"): delete GenerationJob rows in status COMPLETED/FAILED whose updated_at is
      older than current_app.config["JOBS_RETENTION_DAYS"] days. Return the deleted count.
    @shared_task(name="tasks.archive_expired_news"): set is_active=False for NewsItem rows whose expires_at < now().
      Return the archived count.
  (These names MUST match the beat_schedule already configured in app/config/__init__.py.)

# RULES
- Tasks must NOT rely on flask_jwt_extended current_user (no request context in the worker); pass owner_id explicitly
  and query with db.session / .filter(Model.owner_id == owner_id) directly (do NOT use scoped_query in tasks).
- Use db.session from app.extensions. Import audio_engine/tts_client lazily inside functions if needed to avoid cycles.
- Be defensive: missing news/commercial/character must degrade to sensible defaults (see prototype defaults).
- Spanish, satirical tone preserved from the prototype.
`

const FILES_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['files_created', 'notes'],
  properties: {
    files_created: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
    blockers: { type: 'string' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['ok', 'issues_found', 'fixes_applied'],
  properties: {
    ok: { type: 'boolean' },
    issues_found: { type: 'array', items: { type: 'string' } },
    fixes_applied: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
}

phase('Build')
log('Building the generation pipeline subsystem (agents + tasks)')
const build = await agent(
  INTERFACE +
  '\n\n# YOUR TASK\nCreate ALL of these files, conforming exactly to the pinned interface:\n' +
  '  app/services/agents/episode_planner.py\n' +
  '  app/services/agents/news_agent.py\n' +
  '  app/services/agents/commercial_agent.py\n' +
  '  app/services/agents/character_agent.py\n' +
  '  app/services/agents/host_agent.py\n' +
  '  app/services/agents/episode_assembly.py\n' +
  '  app/tasks/generation.py\n' +
  '  app/tasks/maintenance.py\n' +
  'Read the prototype generator.py and audio_engine.py and the existing app/integrations modules and app/models first. ' +
  'Keep every module import-safe (no network/db at import time).',
  { label: 'pipeline-build', phase: 'Build', schema: FILES_SCHEMA }
)

phase('Verify')
log('Adversarially verifying the pipeline')
const verdict = await agent(
  INTERFACE +
  '\n\n# YOUR TASK (adversarial reviewer + fixer)\n' +
  'The pipeline files were just written. Read them all and adversarially verify against the pinned interface. ' +
  'Check specifically: (1) JobStatus transitions queued->planning->synthesizing->mixing->completed and the FAILED path with ' +
  'job.error set; (2) progress values 10/50/75/100; (3) Episode persisted with script_json and later audio_path+duration; ' +
  '(4) job.episode_id set; (5) tasks do NOT use current_user/scoped_query (owner_id passed explicitly); ' +
  '(6) build_episode returns ALL pinned keys incl track_ids, and music track_id indexes align with the tracks passed to ' +
  'compile_episode; (7) character memory written + last_appearance updated; (8) shared_task names exactly ' +
  '"tasks.generate_episode", "tasks.cleanup_old_jobs", "tasks.archive_expired_news"; (9) generate_episode_task symbol exists ' +
  '(the episodes route imports it); (10) LLM-failure procedural fallback always yields a valid script. ' +
  'FIX any issue you find by editing the files directly. Then byte-compile the touched files with ' +
  ROOT + '/.venv/bin/python -m compileall on the app/services and app/tasks dirs and report.',
  { label: 'pipeline-verify', phase: 'Verify', schema: VERDICT_SCHEMA }
)

return { build, verdict }
