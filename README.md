# VirtualRadio

**VirtualRadio** es un generador automatizado de estaciones de radio satíricas (estilo
WCTR de GTA) para videojuegos de simulación como *Farming Simulator 25*, *Euro Truck
Simulator 2* y similares. Un usuario define su propio "universo" — estaciones, noticias,
marcas y comerciales, personajes con memoria narrativa y una biblioteca musical — y la
aplicación genera episodios completos: un guión estructurado y un MP3 mezclado con voces
sintéticas sobre música, listo para reproducir.

Este repositorio es un **monorepo** con dos aplicaciones desplegables más el contrato y la
documentación de diseño:

| Carpeta | Qué es |
| --- | --- |
| [`backend/`](backend/) | API REST (Flask 3) + pipeline de generación asíncrono (Celery). Ver [`backend/README.md`](backend/README.md). |
| [`frontend/`](frontend/) | Panel de control web SPA (Nuxt 4 + Bun, Feature-Sliced Design). Ver [`frontend/README.md`](frontend/README.md). |
| [`specs/openapi.yaml`](specs/openapi.yaml) | Contrato **OpenAPI 3.1** (API v1.0.0) que implementa el backend. |
| [`docs/`](docs/) | Documentación de arquitectura (C4, esquema de BD, RBAC, planes) — fuente de verdad del diseño. |

---

## 🛠️ Stack tecnológico

**Backend** — Python 3.12 · Flask 3.1 · **PostgreSQL 18** (SQLAlchemy 2.0 +
Flask-Migrate/Alembic, IDs `uuidv7()` nativos) · **Redis 8 + Celery 5** (pipeline
asíncrono + Beat) · Flask-JWT-Extended (JWT, argon2) · Marshmallow (validación) ·
**FFmpeg + pydub** (motor de audio) · **google-genai** (Gemini LLM + TTS, vía Vertex AI
con ADC o API key) con **fallback procedural**.

**Frontend** — **Bun** · **Nuxt 4** (Vue 3, Composition API, SPA `ssr: false`) · Pinia ·
SASS · TypeScript (typecheck con `vue-tsc`) · Playwright (E2E). Arquitectura
**Feature-Sliced Design** (`pages → widgets → features → entities → shared`).

---

## 🚀 Inicio rápido (Docker, recomendado)

El `docker-compose.yml` vive dentro de [`backend/`](backend/) y construye también el
frontend, por lo que **debe ejecutarse desde esa carpeta**:

```bash
cd backend
cp .env.example .env          # ajusta secretos / claves de IA si las tienes (opcional)
docker compose up --build
```

Esto levanta toda la pila: `db` (Postgres 18) · `redis` (8) · `api` (Gunicorn) ·
`worker` (Celery + Beat) · `frontend` (Nuxt). El servicio `api` aplica las migraciones y
siembra el catálogo de roles al arrancar (`flask db upgrade && flask seed-roles`).

| Servicio | URL |
| --- | --- |
| Panel de control (Nuxt) | http://localhost:3000 |
| API del backend (base `/api/v1`) | http://localhost:5000/api/v1 |
| PostgreSQL / Redis | `localhost:5432` / `localhost:6379` |

> **La IA es opcional.** Sin `GEMINI_API_KEY` / `OPENROUTER_API_KEY` (ni Vertex AI), el
> sistema sigue generando episodios válidos mediante un motor procedural y voz sintética;
> si la biblioteca musical del usuario está vacía, sintetiza pistas chiptune de prueba.
> Para usar IA real, configura las claves en `backend/.env` (o Vertex AI con `GEMINI_USE_VERTEX`
> + ADC). Detalles en [`backend/README.md`](backend/README.md).

Para ejecutar cada aplicación por separado (entorno local sin Docker, pruebas, etc.),
consulta el README de cada subproyecto.

---

## 🎙️ Cómo funciona

1. El usuario inicia sesión en el panel y define su **universo**: estaciones (con locutor
   y personalidad), noticias, marcas y comerciales, personajes con memoria narrativa y una
   biblioteca musical. Al registrarse se siembra un universo por defecto.
2. Dispara la generación de un episodio: `POST /episodes/generate {station_id}` encola un
   `GenerationJob` y responde **202**.
3. El worker de Celery ejecuta el **pipeline de agentes** (Episode Planner → News →
   Commercial → Character → Host → Assembly), avanzando el estado del job
   `planning → synthesizing → mixing → completed`. Cada agente intenta el LLM y cae a
   contenido procedural si no hay respuesta.
4. El frontend hace *polling* en `GET /jobs/{id}` y muestra el progreso.
5. El motor de audio (FFmpeg + pydub) compila el MP3 con efectos de radio (ducking,
   filtro telefónico de 300 Hz–3 kHz para llamadas, sweepers/estática). El episodio se
   sirve en `GET /episodes/{id}/audio` con soporte de `Range` (206) y se reproduce en el
   navegador con una línea de tiempo tipo guión.

Toda la información pertenece al usuario autenticado (`owner_id` derivado del JWT); el
acceso a recursos ajenos devuelve **404** (se oculta su existencia).

---

## 📂 Estructura del proyecto

```
VirtualRadio/
├── backend/        API Flask 3 + Celery (capas: routes → controllers → services/agents → repositories → models)
│   ├── app/        Paquete de la aplicación (factory, blueprints autodescubiertos bajo /api/v1)
│   ├── migrations/ Migraciones Alembic
│   ├── tests/      Smoke tests E2E (scripts Python, requieren Postgres + Redis)
│   └── docker-compose.yml   Pila completa (db, redis, api, worker, frontend)
├── frontend/       SPA Nuxt 4 (Feature-Sliced Design)
│   └── app/        pages · widgets · features · entities · shared · layouts · middleware · plugins
├── docs/           Documentación de arquitectura
│   ├── backend/    arquitectura, base-de-datos, rbac, plan de implementación
│   └── frontend/   arquitectura, plan de implementación
├── specs/
│   └── openapi.yaml   Contrato de la API (OpenAPI 3.1)
├── CLAUDE.md       Guía para Claude Code
└── README.md
```

---

## 📚 Documentación

- [`backend/README.md`](backend/README.md) — stack, comandos, capas, pipeline de
  generación, RBAC y variables de entorno del backend.
- [`frontend/README.md`](frontend/README.md) — arquitectura FSD, autenticación, configuración
  y pruebas del frontend.
- [`docs/`](docs/) — decisiones de arquitectura, esquema de base de datos y RBAC.
- [`specs/openapi.yaml`](specs/openapi.yaml) — contrato HTTP completo (Health, Auth,
  Stations, Episodes, Jobs, Music, News, Brands, Commercials, Characters, Story Events,
  Universe).
