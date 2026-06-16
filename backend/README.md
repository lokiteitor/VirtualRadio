# VirtualRadio — Backend

API REST (Flask 3) + pipeline de generación de episodios de radio satírica para
simuladores. Implementa el contrato de `specs/openapi.yaml` y la arquitectura de
`docs/backend/`.

## Stack

- **Python 3.12**, Flask 3 (application factory + blueprints autodescubiertos)
- **PostgreSQL 18** (SQLAlchemy 2.0 + Flask-Migrate/Alembic; IDs `uuidv7()` nativos)
- **Redis 8** + **Celery 5** (broker/result + Celery Beat; pipeline asíncrono)
- **Marshmallow** (validación), **Flask-JWT-Extended** (JWT), **argon2** (hashing)
- **FFmpeg + pydub** (motor de audio), **mutagen** (metadatos MP3)
- Integraciones IA con degradación elegante: **Gemini / OpenRouter** (LLM) y
  **Gemini TTS** (voz), con **fallback procedural** — todo funciona sin claves.

## Arquitectura (capas)

```
app/
├── routes/        Blueprints por recurso (autodescubiertos: cualquier `bp` -> /api/v1)
├── controllers/   Orquestación request -> validación -> repos -> serialización
├── services/      Lógica de negocio + agents/ (Planner, News, Commercial, Character, Host, Assembly)
├── repositories/  Acceso a datos con scoped_query (aislamiento por owner_id)
├── models/        Modelos SQLAlchemy + enums + mixins (UUIDv7, timestamps, ownership)
├── schemas/       Marshmallow (request/response)
├── integrations/  llm_client, tts_client, audio_engine
├── tasks/         Celery (generación + mantenimiento/beat)
├── seeds/         Catálogo de roles + universo por defecto por usuario
├── auth/          Callbacks JWT + check_permission (RBAC scope `own`)
├── common/        Envoltorio {data,meta} / {error}, manejadores de error, logging JSON
└── config/        Configuración por entorno
```

Contrato de respuestas: éxito `{"data": ..., "meta": {...}}`; error
`{"error": {"code", "message", "details"}}`. Todas las rutas (salvo `auth` y
`health`) requieren `Authorization: Bearer <access_token>` y filtran por
`owner_id` del token (acceso a recursos ajenos → **404**).

## Ejecutar con Docker (recomendado)

```bash
cd backend
cp .env.example .env          # ajusta secretos / claves IA si las tienes
docker compose up --build
```

Levanta `db` (Postgres 18), `redis` (8), `api` (Gunicorn) y `worker`
(Celery + Beat). El servicio `api` aplica migraciones y siembra el catálogo de
roles al arrancar (`flask db upgrade && flask seed-roles`). La API queda en
`http://localhost:5000/api/v1`.

## Ejecutar en local (sin Docker)

Requiere un Postgres 18 y un Redis accesibles (puedes levantarlos con
`docker compose up -d db redis`).

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export FLASK_APP=wsgi:app
export DATABASE_URL="postgresql+psycopg://virtualradio:virtualradio@localhost:5432/virtualradio"
export REDIS_URL="redis://localhost:6379/0"
export MEDIA_ROOT=/tmp/vrmedia
export PYTHONPATH=$(pwd)

.venv/bin/flask db upgrade          # crea el esquema (12 tablas, 4 enums)
.venv/bin/flask seed-roles          # catálogo de roles (USER, SUPER_ADMIN ref.)
.venv/bin/flask --app wsgi:app run --port 5000          # API
# en otra terminal (mismas env vars):
.venv/bin/celery -A celery_worker.celery_app worker --beat --loglevel=info
```

CLI útil: `flask seed-demo <email>` crea un usuario demo con universo sembrado.

## Variables de entorno

Ver `.env.example`. Claves opcionales: `GEMINI_API_KEY`, `OPENROUTER_API_KEY`
(LLM para `/suggest` y guiones) y `GEMINI_TTS_MODEL` (voz). Sin claves, el
sistema usa contenido procedural y voz sintética, generando episodios válidos.

> Producción: usa un `JWT_SECRET_KEY`/`SECRET_KEY` largo (≥32 bytes).

## Flujo de generación

`POST /episodes/generate {station_id}` → encola un `GenerationJob` (202) →
el worker ejecuta el pipeline (planning → synthesizing → mixing → completed)
y persiste el estado; haz *polling* en `GET /jobs/{id}`. El audio MP3 se sirve
en `GET /episodes/{id}/audio` (soporta `Range` → 206). Si la biblioteca musical
del usuario está vacía, se sintetizan e indexan 3 pistas chiptune de prueba.

## Pruebas / smoke tests

Con Postgres + Redis arriba y las env vars anteriores:

```bash
.venv/bin/python tests/smoke_e2e.py     # 41 checks: auth, CRUD, suggest, generación, audio, aislamiento
# Path async (requiere un worker corriendo):
.venv/bin/python tests/smoke_async.py   # encola por Redis y espera al worker
```

Estado verificado: migración aplica en Postgres 18, `flask db check` limpio
(modelos ↔ migración), 41/41 checks E2E en verde y pipeline asíncrona real OK.
