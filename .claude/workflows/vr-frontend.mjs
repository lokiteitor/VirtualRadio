export const meta = {
  name: 'vr-frontend',
  description: 'Build VirtualRadio frontend verticals (entity+feature+page) by cloning the Stations slice',
  phases: [{ title: 'Verticals', detail: 'one agent per resource: entity + feature(s) + page' }],
}

const FE = '/home/ddelgado/git/lab/VirtualRadio/frontend'
const BE = '/home/ddelgado/git/lab/VirtualRadio/backend'
const PROTO = '/home/ddelgado/git/lab/VirtualRadio/prototipo/frontend/app.vue'

const CONTRACT = `
You are extending an existing Nuxt 4 + Pinia + SASS frontend organized with Feature-Sliced Design (FSD).
Frontend root: ${FE}  (Nuxt srcDir is ${FE}/app ; import alias "~" -> ${FE}/app)

# ABSOLUTE RULES
- ONLY CREATE the new files listed in your task. NEVER edit shared/foundation files
  (app/app.vue, app/shared/**, app/plugins/**, app/middleware/**, app/layouts/**, nuxt.config.ts,
  app/entities/session/**, app/entities/station/**, app/features/manage-station/**,
  app/features/generate-episode/**, app/widgets/**, app/pages/index.vue, app/pages/login.vue).
  Exception: you MAY create new widget folders that your task explicitly assigns to you.
- FSD layering (import only from lower layers): pages -> widgets -> features -> entities -> shared.
  Each slice exposes a public API via index.ts; import other slices ONLY through their index.ts
  (e.g. import { useApi } from "~/shared/api"; import { StationCard } from "~/entities/station").
- READ the reference Stations vertical FIRST and mirror its structure/patterns EXACTLY:
    app/entities/station/{model/types.ts,api/stationApi.ts,model/store.ts,ui/StationCard.vue,index.ts}
    app/features/manage-station/ui/StationForm.vue   (form + AI suggest + 422 error mapping)
    app/pages/index.vue                              (page composition)
- READ the shared contract you must use:
    app/shared/api/index.ts  -> useApi(): get<T>(url,query) | getWithMeta<T> | post<T> | put<T> | del |
       postForm<T>(url, FormData) | getBlob(url) ; also { ApiError, toApiError } for error handling.
    app/shared/ui/index.ts   -> AppCard, AppPageHeader, AppModal, AppEmptyState, AppBadge, AppField.
    app/shared/lib/index.ts  -> formatDate, formatDuration, getAvatarEmoji, linesToArray, arrayToLines.
    app/shared/config/index.ts -> NAV_ITEMS, NEWS_CATEGORIES, NEWS_TONES, STORY_STATUSES, Option.
    app/shared/styles/global.scss -> reusable classes: .btn(.btn-primary/.btn-secondary/.btn-danger/
       .btn-block/.btn-sm/.btn-circle/.btn-ghost-primary), .card-container, .split-pane, .section-title-row,
       .badge(.badge-glow), .app-form, .form-group, .form-desc, .empty-state, .alert(.alert-info/.alert-danger),
       .stat-box/.stat-value/.stat-label, .text-center. SCSS _variables.scss/_mixins.scss are AUTO-INJECTED
       into every <style lang="scss"> (you can use var(--primary) etc. directly).
- MATCH THE BACKEND CONTRACT EXACTLY. Read the relevant backend controller(s) and route(s) under
    ${BE}/app/controllers/ and ${BE}/app/routes/  to confirm field names, query params and especially the
    /suggest request body shape (SuggestRequest is { prompt?, context? }; controllers read specific context keys).
    All responses are the envelope { data, meta }; useApi() already unwraps data.
- PORT THE VISUAL STYLE for your tab from the prototype monolith (migrate the relevant CSS classes into your
  components' scoped <style lang="scss">, using the design tokens): ${PROTO}
- Spanish UI text, dark theme. Vue 3 <script setup lang="ts">, strict types (no implicit any).
- Pages use definePageMeta only if needed (default layout is automatic). Add an AppPageHeader at the top.
- Forms: clone StationForm's pattern — reactive form, AI suggest button (btn-ghost-primary), submit via the
  entity store, map 422 ApiError.details to per-field errors via AppField :error.

After writing, return the structured report.
`

const REPORT = {
  type: 'object',
  additionalProperties: false,
  required: ['vertical', 'files_created', 'notes'],
  properties: {
    vertical: { type: 'string' },
    files_created: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
    blockers: { type: 'string' },
  },
}

const VERTICALS = [
  {
    label: 'news',
    prompt: `Build the NEWS vertical.
Backend: ${BE}/app/controllers/news.py + routes/news.py (resource "news"). Prototype tab: "TAB: NEWS LIBRARY".
Create:
  app/entities/news-item/model/types.ts   (NewsItem: id, owner_id, headline, summary|null, full_script|null,
     category, tone, is_active, expires_at|null, created_at, updated_at ; NewsItemInput ; SuggestHint)
  app/entities/news-item/api/newsApi.ts    (list(query?: {is_active?, category?}), get, create, update, remove,
     suggest(hint))  -- GET /news supports is_active & category query params.
  app/entities/news-item/model/store.ts    (items, loading, fetchAll(filters?), create, update, remove)
  app/entities/news-item/ui/NewsCard.vue   (category + tone badges, headline, summary, full_script quote; emits edit/remove)
  app/entities/news-item/index.ts
  app/features/manage-news/ui/NewsForm.vue (headline, summary, full_script textarea, category <select> from NEWS_CATEGORIES,
     tone <select> from NEWS_TONES, is_active checkbox; AI suggest sends { context: { category, tone } } -- VERIFY in news.py;
     create/edit via store)
  app/features/manage-news/index.ts
  app/pages/news.vue  (split-pane: left list of NewsCard with edit/remove, right NewsForm; AppPageHeader using NAV_ITEMS find id==='news')`,
  },
  {
    label: 'commercials',
    prompt: `Build the COMMERCIALS + BRANDS vertical (one page shows both).
Backend: ${BE}/app/controllers/brand.py, commercial.py + their routes. Prototype tab: "TAB: COMMERCIALS".
Create entities:
  app/entities/brand/{model/types.ts (Brand: id,owner_id,name,description|null,industry|null,slogan|null,is_active,timestamps; BrandInput),
     api/brandApi.ts (list,get,create,update,remove,suggest), model/store.ts, ui/BrandCard.vue (pill: name, slogan, industry), index.ts}
  app/entities/commercial/{model/types.ts (Commercial: id,owner_id,brand_id,title,script,duration,campaign|null,is_active,timestamps; CommercialInput),
     api/commercialApi.ts (list(query?:{brand_id?}),get,create,update,remove,suggest), model/store.ts, ui/CommercialCard.vue, index.ts}
Create features:
  app/features/manage-brand/ui/BrandForm.vue (name, slogan, industry, description; suggest sends { context: { name } } -- VERIFY in brand.py) + index.ts
  app/features/manage-commercial/ui/CommercialForm.vue (brand_id <select> from brand store, title, campaign, script, duration;
     AI suggest REQUIRES a selected brand -- READ commercial.py to confirm whether brand_id goes in body or context, and match exactly) + index.ts
Create page:
  app/pages/commercials.vue (left: horizontal brand pills + commercials list, resolving each commercial's brand NAME from the brand
     store by brand_id since the API returns only brand_id; right: BrandForm then CommercialForm stacked; AppPageHeader)`,
  },
  {
    label: 'characters',
    prompt: `Build the CHARACTERS vertical (with narrative memories).
Backend: ${BE}/app/controllers/character.py + routes/character.py. Prototype tab: "TAB: CHARACTERS & MEMORY".
Create:
  app/entities/character/model/types.ts (Character: id,owner_id,name,role|null,description|null,personality|null,
     station_affinity|null,first_appearance,last_appearance,created_at,updated_at ; CharacterInput ; CharacterMemory:
     id,owner_id,character_id,episode_id|null,memory,importance,created_at,updated_at)
  app/entities/character/api/characterApi.ts (list,get,create,update,remove,suggest(hint), memories(id) -> GET /characters/{id}/memories)
  app/entities/character/model/store.ts (items, loading, fetchAll, create, update, remove)
  app/entities/character/ui/CharacterCard.vue (avatar via getAvatarEmoji(name), name, role badge, personality, station_affinity,
     description, and a memory section; emits loadMemories(id)/edit/remove; accepts a memories prop to render)
  app/entities/character/index.ts
  app/features/manage-character/ui/CharacterForm.vue (name, role, station_affinity, personality, description; suggest sends
     { context: { name } } -- VERIFY in character.py) + index.ts
  app/pages/characters.vue (left: grid of CharacterCard, clicking a card lazy-loads its memories via characterApi.memories and
     passes them in; right: CharacterForm; AppPageHeader)`,
  },
  {
    label: 'music',
    prompt: `Build the MUSIC LIBRARY vertical.
Backend: ${BE}/app/controllers/music.py + routes/music.py. Prototype tab: "TAB: MUSIC LIBRARY".
Note: GET /music returns meta { count, total_duration } -> use useApi().getWithMeta. Upload is multipart field "file"
(use useApi().postForm with FormData). Scan is POST /music/scan. Delete is DELETE /music/{id}.
Create:
  app/entities/music-track/model/types.ts (MusicTrack: id,owner_id,file_path,title|null,artist|null,album|null,duration|null,
     file_hash,created_at,updated_at)
  app/entities/music-track/api/musicApi.ts (listWithMeta() -> {data,meta}, upload(file: File), scan(), remove(id))
  app/entities/music-track/model/store.ts (items, totalDuration, count, loading, fetchAll, upload, scan, remove)
  app/entities/music-track/index.ts
  app/features/upload-music/ui/UploadMusic.vue (a hidden file input styled as a button "Subir MP3" calling store.upload,
     plus a "Escanear Carpeta" button calling store.scan; reject non-.mp3; show busy state) + index.ts
  app/pages/music.vue (AppPageHeader; stats row: tracks count + total duration via formatDuration; the UploadMusic actions;
     a table of tracks (title, artist, duration, file_path in <code>) with a delete button per row; empty state; the alert-info
     note about auto-generated chiptune mock music when the library is empty)`,
  },
  {
    label: 'episodes',
    prompt: `Build the EPISODES vertical (catalog + custom player + script timeline).
Backend: ${BE}/app/controllers/episode.py + routes/episode.py + schemas/episode.py. Prototype tab: "TAB: EPISODES".
IMPORTANT - authenticated audio: GET /episodes/{id}/audio requires the Bearer token, so a plain <audio src> will 401.
Fetch the audio with useApi().getBlob(\`/episodes/\${id}/audio\`) then URL.createObjectURL(blob) for the <audio> element;
revokeObjectURL on cleanup.
Create:
  app/entities/episode/model/types.ts (Episode: id,owner_id,station_id,title,duration,script_json: ScriptSegment[],
     audio_path|null,created_at,updated_at ; ScriptSegment: type:'speech'|'music'|'fx', speaker|null, text|null, voice_id|null,
     effect|null, track_id|null, duration_seconds|null)
  app/entities/episode/api/episodeApi.ts (list(query?:{station_id?}), get(id), remove(id), audioBlob(id) -> useApi().getBlob)
  app/entities/episode/model/store.ts (items, loading, fetchAll, remove)
  app/entities/episode/ui/EpisodeRow.vue (station handled by parent; title, formatDate(created_at), formatDuration(duration);
     emits select/play/remove)
  app/entities/episode/index.ts
  app/features/play-episode/model/usePlayEpisode.ts (composable: load(episode) fetches the audio blob -> object URL ->
     HTMLAudioElement; reactive isPlaying/currentTime/duration/volume; toggle()/seek(t)/setVolume(v)/stop(); revoke URL +
     remove listeners on stop and onScopeDispose) + index.ts
  app/widgets/episode-player/ui/EpisodePlayer.vue (props: episode; uses usePlayEpisode; custom player controls (play/pause,
     timeline range bound to currentTime+seek, volume), an animated equalizer that pulses while playing, and a script timeline
     rendering each script_json segment: speech -> avatar (getAvatarEmoji(speaker)) + speech bubble with a telephony/mic badge;
     music -> music card "SONANDO AHORA"; fx -> fx segment. PORT these styles from the prototype.) + index.ts
  app/pages/episodes.vue (AppPageHeader; if no episodes -> AppEmptyState; else two columns: left list of EpisodeRow (show the
     station name resolved from the station entity store by station_id), right the EpisodePlayer for the selected episode;
     delete with confirm)`,
  },
]

phase('Verticals')
log('Building ' + VERTICALS.length + ' frontend verticals in parallel')

const results = await parallel(
  VERTICALS.map((v) => () =>
    agent(CONTRACT + '\n\n# YOUR VERTICAL\n' + v.prompt, {
      label: v.label, phase: 'Verticals', schema: REPORT,
    })
  )
)

const ok = results.filter(Boolean)
log('Completed ' + ok.length + '/' + VERTICALS.length + ' verticals')
return {
  verticals: ok,
  blockers: ok.filter((u) => u && u.blockers).map((u) => ({ vertical: u.vertical, blockers: u.blockers })),
}
