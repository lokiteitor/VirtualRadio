# RBAC Backend – VirtualRadio

## **Proyecto:** VirtualRadio

**Versión:** 1.0

**Fecha:** 2026-06-15

## 📋 Tabla de Contenidos

1. [Estructura de Permisos](#estructura-de-permisos)
2. [Definición de Roles del Sistema](#definición-de-roles-del-sistema)
3. [Permisos por Recurso](#permisos-por-recurso)
4. [Implementación de Scopes](#implementación-de-scopes)
5. [Middleware y Validaciones](#middleware-y-validaciones)
6. [Pendientes / Riesgos](#pendientes--riesgos)
7. [Casos de Uso por Endpoint](#casos-de-uso-por-endpoint)

---

## Estructura de Permisos

VirtualRadio es una aplicación multiusuario donde **cada usuario es dueño de sus propios datos**. El modelo se mantiene deliberadamente simple: un único rol de sistema (`USER`) y un único scope efectivo (`own`). No existen roles administrativos ni acceso entre usuarios en esta versión.

### Formato Base

```
resource:action:scope
```

**Componentes:**

- **Resource**: Recurso del dominio (ej. stations, episodes, characters, news)
- **Action**: Operación (create, read, update, delete, generate, upload, suggest, etc.)
- **Scope**: Alcance del permiso (en este sistema, siempre `own`)

### Ejemplos

```text
station:read:own
episode:generate:own
news:update:own
```

### Scopes Disponibles

| Scope    | Descripción        | Regla de Filtro    |
| -------- | ------------------ | ------------------ |
| all      | Acceso total (no usado en esta versión) | Sin filtro |
| assigned | Recursos asignados (no usado en esta versión) | Regla por relación |
| own      | Recursos propios   | `owner_id = current_user.id` |

> En VirtualRadio **solo se utiliza el scope `own`**. Los scopes `all` y `assigned` se documentan por compatibilidad con la plantilla y posibles extensiones futuras.

---

## Definición de Roles del Sistema

### Tabla `roles`

```sql
CREATE TABLE roles (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  code VARCHAR(50) NOT NULL,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  is_system_role BOOLEAN NOT NULL DEFAULT false,
  permissions JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uq_roles_code ON roles(code);
```

> Nota: en esta versión el rol es único y constante. La tabla `roles` se incluye por consistencia con la plantilla, pero la asignación de rol al usuario es implícita (`USER` por defecto). No se modela una relación `users` ↔ `roles` configurable.

### Roles Base

#### SUPER_ADMIN

```json
{
  "code": "SUPER_ADMIN",
  "permissions": ["*:*:*"]
}
```

**Reglas:**

- Bypass completo de validaciones
- Puede administrar roles del sistema

> **No aplicado en VirtualRadio v1.0.** Se documenta como referencia. No existe ningún usuario con este rol en esta versión.

---

#### USER

```json
{
  "code": "USER",
  "name": "Usuario",
  "description": "Usuario propietario de su propio universo de datos. Acceso exclusivo a sus recursos (scope own).",
  "is_system_role": true,
  "permissions": [
    "station:create:own", "station:read:own", "station:update:own", "station:delete:own", "station:suggest:own",
    "episode:read:own", "episode:generate:own", "episode:delete:own",
    "job:read:own",
    "universe:read:own",
    "music:read:own", "music:upload:own", "music:scan:own", "music:delete:own",
    "news:create:own", "news:read:own", "news:update:own", "news:delete:own", "news:suggest:own",
    "brand:create:own", "brand:read:own", "brand:update:own", "brand:delete:own", "brand:suggest:own",
    "commercial:create:own", "commercial:read:own", "commercial:update:own", "commercial:delete:own", "commercial:suggest:own",
    "character:create:own", "character:read:own", "character:update:own", "character:delete:own", "character:suggest:own", "character:read_memories:own",
    "story_event:create:own", "story_event:read:own", "story_event:update:own", "story_event:delete:own"
  ]
}
```

---

## Permisos por Recurso

### Estaciones

**Tabla:** `stations`

| Permiso               | SUPER_ADMIN | USER |
| --------------------- | ------------ | ----- |
| station:create:own    | ✅            | ✅     |
| station:read:own      | ✅            | ✅     |
| station:update:own    | ✅            | ✅     |
| station:delete:own    | ✅            | ✅     |
| station:suggest:own   | ✅            | ✅     |

### Endpoints

- `GET /api/v1/stations` → `station:read:own`
- `POST /api/v1/stations` → `station:create:own`
- `POST /api/v1/stations/suggest` → `station:suggest:own`
- `PUT /api/v1/stations/{id}` → `station:update:own`
- `DELETE /api/v1/stations/{id}` → `station:delete:own`

### Episodios

**Tabla:** `episodes` / `generation_jobs`

| Permiso               | SUPER_ADMIN | USER |
| --------------------- | ------------ | ----- |
| episode:read:own      | ✅            | ✅     |
| episode:generate:own  | ✅            | ✅     |
| episode:delete:own    | ✅            | ✅     |
| job:read:own          | ✅            | ✅     |

### Endpoints

- `GET /api/v1/episodes` → `episode:read:own`
- `GET /api/v1/episodes/{id}` → `episode:read:own`
- `POST /api/v1/episodes/generate` → `episode:generate:own`
- `DELETE /api/v1/episodes/{id}` → `episode:delete:own`
- `GET /api/v1/jobs/{id}` → `job:read:own`

### Biblioteca Musical

**Tabla:** `music_tracks`

| Permiso             | SUPER_ADMIN | USER |
| ------------------- | ------------ | ----- |
| music:read:own      | ✅            | ✅     |
| music:upload:own    | ✅            | ✅     |
| music:scan:own      | ✅            | ✅     |
| music:delete:own    | ✅            | ✅     |

### Endpoints

- `GET /api/v1/music` → `music:read:own`
- `POST /api/v1/music/upload` → `music:upload:own`
- `POST /api/v1/music/scan` → `music:scan:own`
- `DELETE /api/v1/music/{id}` → `music:delete:own`

### Noticias

**Tabla:** `news_items`

| Permiso            | SUPER_ADMIN | USER |
| ------------------ | ------------ | ----- |
| news:create:own    | ✅            | ✅     |
| news:read:own      | ✅            | ✅     |
| news:update:own    | ✅            | ✅     |
| news:delete:own    | ✅            | ✅     |
| news:suggest:own   | ✅            | ✅     |

### Endpoints

- `GET /api/v1/news` → `news:read:own`
- `POST /api/v1/news` → `news:create:own`
- `POST /api/v1/news/suggest` → `news:suggest:own`
- `PUT /api/v1/news/{id}` → `news:update:own`
- `DELETE /api/v1/news/{id}` → `news:delete:own`

### Marcas y Comerciales

**Tabla:** `commercial_brands` / `commercials`

| Permiso                | SUPER_ADMIN | USER |
| ---------------------- | ------------ | ----- |
| brand:create:own       | ✅            | ✅     |
| brand:read:own         | ✅            | ✅     |
| brand:update:own       | ✅            | ✅     |
| brand:delete:own       | ✅            | ✅     |
| brand:suggest:own      | ✅            | ✅     |
| commercial:create:own  | ✅            | ✅     |
| commercial:read:own    | ✅            | ✅     |
| commercial:update:own  | ✅            | ✅     |
| commercial:delete:own  | ✅            | ✅     |
| commercial:suggest:own | ✅            | ✅     |

### Endpoints

- `GET /api/v1/brands` → `brand:read:own`
- `POST /api/v1/brands` → `brand:create:own`
- `POST /api/v1/brands/suggest` → `brand:suggest:own`
- `PUT /api/v1/brands/{id}` → `brand:update:own`
- `DELETE /api/v1/brands/{id}` → `brand:delete:own`
- `GET /api/v1/commercials` → `commercial:read:own`
- `POST /api/v1/commercials` → `commercial:create:own`
- `POST /api/v1/commercials/suggest` → `commercial:suggest:own`
- `PUT /api/v1/commercials/{id}` → `commercial:update:own`
- `DELETE /api/v1/commercials/{id}` → `commercial:delete:own`

### Personajes

**Tabla:** `characters` / `character_memories`

| Permiso                      | SUPER_ADMIN | USER |
| ---------------------------- | ------------ | ----- |
| character:create:own         | ✅            | ✅     |
| character:read:own           | ✅            | ✅     |
| character:update:own         | ✅            | ✅     |
| character:delete:own         | ✅            | ✅     |
| character:suggest:own        | ✅            | ✅     |
| character:read_memories:own  | ✅            | ✅     |

### Endpoints

- `GET /api/v1/characters` → `character:read:own`
- `POST /api/v1/characters` → `character:create:own`
- `POST /api/v1/characters/suggest` → `character:suggest:own`
- `PUT /api/v1/characters/{id}` → `character:update:own`
- `DELETE /api/v1/characters/{id}` → `character:delete:own`
- `GET /api/v1/characters/{id}/memories` → `character:read_memories:own`

### Eventos Narrativos (Story Events)

**Tabla:** `story_events`

| Permiso                  | SUPER_ADMIN | USER |
| ------------------------ | ------------ | ----- |
| story_event:create:own   | ✅            | ✅     |
| story_event:read:own     | ✅            | ✅     |
| story_event:update:own   | ✅            | ✅     |
| story_event:delete:own   | ✅            | ✅     |

### Endpoints

- `GET /api/v1/story-events` → `story_event:read:own`
- `POST /api/v1/story-events` → `story_event:create:own`
- `PUT /api/v1/story-events/{id}` → `story_event:update:own`
- `DELETE /api/v1/story-events/{id}` → `story_event:delete:own`

### Universo (Resumen)

**Tablas:** agregados de lectura sobre el universo del usuario (conteos)

| Permiso             | SUPER_ADMIN | USER |
| ------------------- | ------------ | ----- |
| universe:read:own   | ✅            | ✅     |

### Endpoints

- `GET /api/v1/universe/summary` → `universe:read:own` (conteos de estaciones, noticias, comerciales, personajes, pistas, etc.)

### Autenticación

Los endpoints de autenticación no pasan por `check_permission` (no requieren un permiso de rol):

- `POST /api/v1/auth/register` → público (alta de usuario y siembra de su universo)
- `POST /api/v1/auth/login` → público; emite access token + refresh token (JWT)
- `POST /api/v1/auth/refresh` → requiere un **refresh token** válido; emite un nuevo access token

---

## Implementación de Scopes

### Scope `all`

```python
# No utilizado en VirtualRadio v1.0 (reservado para futuros roles administrativos)
```

### Scope `assigned`

| Recurso | Regla de Asignación |
| ------- | ------------------- |
| (ninguno) | No utilizado en esta versión |

```python
# No utilizado en VirtualRadio v1.0
```

### Scope `own`

| Recurso | Regla de Propiedad |
| ------- | ------------------ |
| stations | `stations.owner_id = current_user.id` |
| episodes | `episodes.owner_id = current_user.id` |
| generation_jobs | `generation_jobs.owner_id = current_user.id` |
| music_tracks | `music_tracks.owner_id = current_user.id` |
| news_items | `news_items.owner_id = current_user.id` |
| commercial_brands | `commercial_brands.owner_id = current_user.id` |
| commercials | `commercials.owner_id = current_user.id` |
| characters | `characters.owner_id = current_user.id` |
| character_memories | `character_memories.owner_id = current_user.id` |
| story_events | `story_events.owner_id = current_user.id` |

```python
# Lógica own (Flask + SQLAlchemy)
def scoped_query(model):
    return model.query.filter(model.owner_id == current_user.id)

# Al crear un recurso, se fija el propietario automáticamente
def create(model_cls, **data):
    obj = model_cls(owner_id=current_user.id, **data)
    db.session.add(obj)
    db.session.commit()
    return obj
```

---

## Middleware y Validaciones

```python
# Decorador aplicado a cada endpoint (Flask + Flask-JWT-Extended)
@jwt_required()
@check_permission("station", "read", "own")
def list_stations():
    ...
```

`check_permission(resource, action, scope)`:
1. Verifica que el JWT sea válido y el usuario esté activo (`users.is_active`).
2. Comprueba que el permiso `resource:action:own` esté en el rol `USER`.
3. Inyecta el filtro `owner_id = current_user.id` en la consulta (scope `own`).
4. En operaciones sobre un recurso concreto, devuelve **404** (no 403) si el recurso existe pero pertenece a otro usuario, para no revelar su existencia.

**Reglas especiales:**

- No existe `SUPER_ADMIN` en esta versión: ningún usuario puede ver datos de otro.
- El propietario (`owner_id`) se asigna **siempre desde el token**, nunca desde el body del request.
- Las operaciones de escritura validan ownership antes de actualizar/eliminar.

---

## Pendientes / Riesgos

- **Ampliación a multi-rol** (p. ej. `ADMIN` para soporte) queda fuera de alcance; requeriría introducir el scope `all` y una relación `users` ↔ `roles`.
- **Compartir recursos entre usuarios** (universos colaborativos) requeriría el scope `assigned` y una tabla de asignaciones.
- **Riesgo de fuga de datos** si algún endpoint olvida aplicar `scoped_query`; mitigación: helper centralizado obligatorio + tests que verifican aislamiento por `owner_id`.
- **Asignación de `owner_id` desde el body**: prohibido; debe ignorarse cualquier `owner_id` entrante y tomarse del JWT.

---

## Casos de Uso por Endpoint

| Endpoint  | Rol   | Permiso             | Resultado |
| --------- | ----- | ------------------- | --------- |
| GET /api/v1/stations | USER | station:read:own | ✅ Solo sus estaciones |
| POST /api/v1/episodes/generate | USER | episode:generate:own | ✅ Encola job propio |
| GET /api/v1/jobs/{id} (job de otro usuario) | USER | job:read:own | ❌ 404 Not Found |
| DELETE /api/v1/episodes/{id} (episodio propio) | USER | episode:delete:own | ✅ Elimina y borra MP3 |
| DELETE /api/v1/episodes/{id} (episodio de otro) | USER | episode:delete:own | ❌ 404 Not Found |
| GET /api/v1/characters/{id}/memories (propio) | USER | character:read_memories:own | ✅ |

---

**Última actualización:** 2026-06-15  **Versión:** 1.0
