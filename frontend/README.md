# VirtualRadio — Frontend

Panel de control web (SPA) para VirtualRadio: gestiona estaciones, noticias,
comerciales, personajes y música, dispara la generación de episodios por agentes
y reproduce los resultados. Construido con **Nuxt 4 + Vue 3 + Pinia + SASS** y
organizado con **Feature-Sliced Design (FSD)**.

## Stack

- **Bun** (runtime, gestor de paquetes y scripts)
- **Nuxt 4** (Vue 3, Composition API, `<script setup lang="ts">`, modo SPA `ssr: false`)
- **Pinia** (estado), **SASS** (tokens/diseño oscuro ámbar/púrpura migrado del prototipo)
- **TypeScript** estricto (typecheck con `vue-tsc`), **Playwright** (E2E)

## Arquitectura FSD

Dirección de dependencias: `pages → widgets → features → entities → shared`.
Cada slice expone su API pública por `index.ts`; nunca se importan archivos
internos de otro slice.

```
app/
├── pages/        login, index(estaciones), episodes, news, commercials, characters, music
├── widgets/      sidebar-nav, universe-summary, generation-pipeline-modal, episode-player
├── features/     auth-login, manage-{station,news,brand,commercial,character},
│                 generate-episode, upload-music, play-episode
├── entities/     session, station, episode, news-item, commercial, brand, character, music-track
├── shared/       api (cliente $fetch + JWT + {data}/{error} + blob audio), ui, lib, config, styles
├── layouts/      default (sidebar), auth (login)
├── middleware/   auth.global.ts (guarda de ruta)
└── plugins/      api.ts ($api), session.client.ts (restaura sesión)
```

## Configuración

`NUXT_PUBLIC_API_BASE` (ver `.env.example`) — URL base del backend, accesible
desde el navegador. Por defecto `http://localhost:5000/api/v1`. Nunca se
hardcodea: se lee de `runtimeConfig.public.apiBase`.

## Desarrollo

```bash
cd frontend
bun install
# Backend corriendo en :5000 (ver backend/README.md)
NUXT_PUBLIC_API_BASE=http://localhost:5000/api/v1 bun run dev   # http://localhost:3000
```

Build de producción y preview:

```bash
bun run build
node .output/server/index.mjs        # sirve la SPA (HOST/PORT configurables)
```

Calidad:

```bash
bun run typecheck      # vue-tsc, 0 errores
```

## Autenticación

JWT obtenido en `/login` (entidad `session`), persistido en `localStorage` y
adjuntado por `shared/api` en cada request. Un `401` limpia la sesión y redirige
a `/login`. El audio de los episodios se descarga como *blob* autenticado
(`getBlob`) porque el endpoint requiere el token.

## Pruebas E2E

`smoke.e2e.mjs` arranca un Chromium headless contra el stack vivo (frontend
:3000 + backend :5000) y valida: guarda → registro → estaciones sembradas →
navegación → generación de episodio (pipeline completo) → reproducción.

```bash
bunx playwright install chromium     # una vez
node smoke.e2e.mjs                    # con frontend + backend + worker corriendo
```

Estado verificado: `nuxt build` OK, `vue-tsc` sin errores, y 8/8 checks E2E en
verde contra el backend real (PostgreSQL + Redis + Celery).

## Docker

`Dockerfile` (imagen Bun) construye y sirve la SPA con el servidor Nitro
(`node .output/server/index.mjs`) en el puerto 3000.
