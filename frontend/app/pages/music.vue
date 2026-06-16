<script setup lang="ts">
import { onMounted, ref } from "vue";
import { AppPageHeader, AppEmptyState } from "~/shared/ui";
import { NAV_ITEMS } from "~/shared/config";
import { formatDuration } from "~/shared/lib";
import { useMusicStore, type MusicTrack } from "~/entities/music-track";
import { UploadMusic } from "~/features/upload-music";

const nav = NAV_ITEMS.find((item) => item.id === "music")!;
const store = useMusicStore();
const error = ref("");

onMounted(() => store.fetchAll());

function clearError() {
  error.value = "";
}
function onError(message: string) {
  error.value = message;
}
async function onRemove(track: MusicTrack) {
  const name = track.title || track.file_path;
  if (confirm(`¿Eliminar "${name}" de tu biblioteca? Se borrará el archivo del disco.`)) {
    try {
      await store.remove(track.id);
    } catch {
      error.value = "No se pudo eliminar la pista.";
    }
  }
}
</script>

<template>
  <div>
    <AppPageHeader title="Biblioteca Musical" :subtitle="nav.subtitle" />

    <div class="music-library-layout card-container">
      <div class="library-header-row">
        <div class="library-stats">
          <div class="stat-box">
            <span class="stat-value">{{ store.count }}</span>
            <span class="stat-label">Canciones Indexadas</span>
          </div>
          <div class="stat-box">
            <span class="stat-value">{{ formatDuration(store.totalDuration) }}</span>
            <span class="stat-label">Duración Total</span>
          </div>
        </div>
        <UploadMusic @error="onError" @uploaded="clearError" @scanned="clearError" />
      </div>

      <p v-if="error" class="alert alert-danger">{{ error }}</p>

      <div v-if="store.items.length" class="music-table-wrapper">
        <table class="music-table">
          <thead>
            <tr>
              <th>Título</th>
              <th>Artista</th>
              <th>Duración</th>
              <th>Ubicación del Archivo</th>
              <th class="actions-col"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in store.items" :key="t.id">
              <td class="track-title">🎵 {{ t.title || "Sin título" }}</td>
              <td>{{ t.artist || "—" }}</td>
              <td>{{ formatDuration(t.duration) }}</td>
              <td class="file-path"><code>{{ t.file_path }}</code></td>
              <td class="actions-col">
                <button class="btn btn-danger btn-sm" title="Eliminar" @click="onRemove(t)">🗑️</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <AppEmptyState
        v-else-if="!store.loading"
        icon="🎵"
        title="No hay música indexada"
        message="Sube un archivo MP3 o escanea tu carpeta de música para empezar."
      />

      <div class="alert alert-info">
        <strong>💡 Información de Prueba:</strong> Si tu carpeta de música local está vacía, el motor de
        producción generará automáticamente pistas de música chiptune sintéticas de prueba. ¡No requieres
        subir archivos para ensayar!
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.music-library-layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.library-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 20px;
}
.library-stats {
  display: flex;
  gap: 16px;
}
.music-table-wrapper {
  overflow-x: auto;
}
.music-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}
.music-table th {
  padding: 12px 16px;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--text-muted);
  border-bottom: 2px solid var(--border-color);
}
.music-table td {
  padding: 16px;
  font-size: 14px;
  border-bottom: 1px solid var(--border-color);
}
.track-title {
  font-weight: 600;
}
.file-path {
  font-size: 12px;
}
.file-path code {
  font-family: "JetBrains Mono", monospace;
  color: var(--text-muted);
  word-break: break-all;
}
.actions-col {
  width: 1%;
  text-align: right;
  white-space: nowrap;
}
</style>
