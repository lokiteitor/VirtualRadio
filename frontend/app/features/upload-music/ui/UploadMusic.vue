<script setup lang="ts">
import { ref } from "vue";
import { toApiError } from "~/shared/api";
import { useMusicStore } from "~/entities/music-track";

const emit = defineEmits<{ error: [message: string]; uploaded: []; scanned: [] }>();

const store = useMusicStore();
const fileInput = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const scanning = ref(false);

function pickFile() {
  fileInput.value?.click();
}

async function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  input.value = ""; // allow re-selecting the same file later
  if (!file) return;

  if (!file.name.toLowerCase().endsWith(".mp3")) {
    emit("error", "Solo se permiten archivos .mp3");
    return;
  }

  uploading.value = true;
  try {
    await store.upload(file);
    emit("uploaded");
  } catch (e) {
    emit("error", toApiError(e).message);
  } finally {
    uploading.value = false;
  }
}

async function scan() {
  scanning.value = true;
  try {
    await store.scan();
    emit("scanned");
  } catch (e) {
    emit("error", toApiError(e).message);
  } finally {
    scanning.value = false;
  }
}
</script>

<template>
  <div class="upload-music">
    <input
      ref="fileInput"
      type="file"
      accept=".mp3"
      class="hidden-input"
      :disabled="uploading || scanning"
      @change="onFileChange"
    />
    <button
      type="button"
      class="btn btn-secondary"
      :disabled="uploading || scanning"
      @click="pickFile"
    >
      {{ uploading ? "📤 Subiendo..." : "📤 Subir MP3" }}
    </button>
    <button
      type="button"
      class="btn btn-primary"
      :disabled="scanning || uploading"
      @click="scan"
    >
      {{ scanning ? "🔄 Escaneando..." : "🔍 Escanear Carpeta" }}
    </button>
  </div>
</template>

<style scoped lang="scss">
.upload-music {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.hidden-input {
  display: none;
}
</style>
