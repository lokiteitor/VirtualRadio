<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { AppEmptyState } from "~/shared/ui";
import { toApiError } from "~/shared/api";
import { stationApi } from "~/entities/station";
import { musicApi, type MusicTrack } from "~/entities/music-track";

const props = defineProps<{ stationId: string; stationName?: string }>();
const emit = defineEmits<{ saved: []; cancel: [] }>();

const loading = ref(true);
const saving = ref(false);
const formError = ref("");

const library = ref<MusicTrack[]>([]);
const selected = ref<Set<string>>(new Set());

const allSelected = computed(
  () => library.value.length > 0 && selected.value.size === library.value.length,
);

onMounted(async () => {
  try {
    const [lib, assigned] = await Promise.all([
      musicApi.listWithMeta(),
      stationApi.getMusic(props.stationId),
    ]);
    library.value = lib.data;
    selected.value = new Set(assigned.map((t) => t.id));
  } catch (e) {
    formError.value = toApiError(e).message;
  } finally {
    loading.value = false;
  }
});

function toggle(id: string) {
  const next = new Set(selected.value);
  next.has(id) ? next.delete(id) : next.add(id);
  selected.value = next;
}

function toggleAll() {
  selected.value = allSelected.value
    ? new Set()
    : new Set(library.value.map((t) => t.id));
}

function fmtDuration(seconds: number | null): string {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

async function submit() {
  saving.value = true;
  formError.value = "";
  try {
    await stationApi.setMusic(props.stationId, [...selected.value]);
    emit("saved");
  } catch (e) {
    formError.value = toApiError(e).message;
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div>
    <p class="form-desc">
      Elige qué canciones de tu biblioteca puede reproducir esta emisora. Si no marcas
      ninguna, la estación usa <strong>toda la biblioteca</strong> sin filtrar.
    </p>

    <p v-if="loading" class="loading-note">Cargando biblioteca…</p>

    <AppEmptyState
      v-else-if="!library.length"
      icon="🎵"
      title="No hay música"
      message="Sube canciones en la sección Música para poder asignarlas a la emisora."
    />

    <form v-else class="app-form" @submit.prevent="submit">
      <div class="list-header">
        <span class="count">{{ selected.size }} / {{ library.length }} seleccionadas</span>
        <button type="button" class="btn btn-secondary btn-sm" @click="toggleAll">
          {{ allSelected ? "Quitar todas" : "Seleccionar todas" }}
        </button>
      </div>

      <ul class="track-list">
        <li
          v-for="t in library"
          :key="t.id"
          class="track-row"
          :class="{ active: selected.has(t.id) }"
          @click="toggle(t.id)"
        >
          <input type="checkbox" :checked="selected.has(t.id)" @click.stop="toggle(t.id)" />
          <div class="track-info">
            <span class="track-title">{{ t.title || "Sin título" }}</span>
            <span class="track-artist">{{ t.artist || "Artista desconocido" }}</span>
          </div>
          <span class="track-duration">{{ fmtDuration(t.duration) }}</span>
        </li>
      </ul>

      <p v-if="formError" class="alert alert-danger">{{ formError }}</p>

      <div class="form-buttons">
        <button type="button" class="btn btn-secondary" @click="emit('cancel')">Cancelar</button>
        <button type="submit" class="btn btn-primary btn-block" :disabled="saving">
          💾 {{ saving ? "Guardando..." : "Guardar Selección" }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped lang="scss">
.form-desc {
  color: var(--text-muted);
  font-size: 13px;
  margin-bottom: 16px;
}
.loading-note {
  color: var(--text-muted);
  font-size: 13px;
}
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.list-header .count {
  color: var(--text-muted);
  font-size: 13px;
}
.track-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 340px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}
.track-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.15s ease;
}
.track-row:last-child {
  border-bottom: none;
}
.track-row:hover {
  background: rgba(255, 255, 255, 0.03);
}
.track-row.active {
  background: rgba(245, 158, 11, 0.08);
}
.track-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}
.track-title {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.track-artist {
  font-size: 12px;
  color: var(--text-muted);
}
.track-duration {
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
  color: var(--text-muted);
}
.form-buttons {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}
</style>
