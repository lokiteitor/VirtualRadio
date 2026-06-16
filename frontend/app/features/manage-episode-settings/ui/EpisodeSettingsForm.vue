<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { AppField } from "~/shared/ui";
import { LANGUAGES } from "~/shared/config";
import { toApiError } from "~/shared/api";
import { episodeSettingsApi } from "~/entities/episode-settings";

const props = defineProps<{ stationId: string; stationName?: string }>();
const emit = defineEmits<{ saved: []; cancel: [] }>();

const loading = ref(true);
const saving = ref(false);
const errors = ref<Record<string, string[]>>({});
const formError = ref("");

const form = reactive({
  song_count: 3,
  news_count: 1,
  commercial_count: 1,
  caller_count: 1,
  memories_per_caller: 3,
  language: "es",
});

onMounted(async () => {
  try {
    const s = await episodeSettingsApi.get(props.stationId);
    form.song_count = s.song_count;
    form.news_count = s.news_count;
    form.commercial_count = s.commercial_count;
    form.caller_count = s.caller_count;
    form.memories_per_caller = s.memories_per_caller;
    form.language = s.language;
  } catch (e) {
    formError.value = toApiError(e).message;
  } finally {
    loading.value = false;
  }
});

function payload() {
  return {
    song_count: Number(form.song_count),
    news_count: Number(form.news_count),
    commercial_count: Number(form.commercial_count),
    caller_count: Number(form.caller_count),
    memories_per_caller: Number(form.memories_per_caller),
    language: form.language,
  };
}

async function submit() {
  saving.value = true;
  errors.value = {};
  formError.value = "";
  try {
    await episodeSettingsApi.update(props.stationId, payload());
    emit("saved");
  } catch (e) {
    const err = toApiError(e);
    if (err.status === 422) errors.value = err.details as Record<string, string[]>;
    else formError.value = err.message;
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div>
    <p class="form-desc">
      Define la estructura de cada episodio de esta emisora: cuántas canciones, noticias,
      comerciales y llamadas incluir. Las canciones siempre suenan completas.
    </p>

    <p v-if="loading" class="loading-note">Cargando ajustes…</p>

    <form v-else class="app-form" @submit.prevent="submit">
      <div class="settings-grid">
        <AppField label="Canciones" :error="errors.song_count">
          <input v-model.number="form.song_count" type="number" min="0" max="10" />
        </AppField>
        <AppField label="Noticias" :error="errors.news_count">
          <input v-model.number="form.news_count" type="number" min="0" max="5" />
        </AppField>
        <AppField label="Comerciales" :error="errors.commercial_count">
          <input v-model.number="form.commercial_count" type="number" min="0" max="5" />
        </AppField>
        <AppField label="Llamadas" :error="errors.caller_count">
          <input v-model.number="form.caller_count" type="number" min="0" max="5" />
        </AppField>
        <AppField label="Recuerdos por llamada" :error="errors.memories_per_caller">
          <input v-model.number="form.memories_per_caller" type="number" min="0" max="10" />
        </AppField>
      </div>

      <AppField label="Idioma del programa" :error="errors.language">
        <select v-model="form.language">
          <option v-for="l in LANGUAGES" :key="l.value" :value="l.value">{{ l.label }}</option>
        </select>
      </AppField>

      <p v-if="formError" class="alert alert-danger">{{ formError }}</p>

      <div class="form-buttons">
        <button type="button" class="btn btn-secondary" @click="emit('cancel')">Cancelar</button>
        <button type="submit" class="btn btn-primary btn-block" :disabled="saving">
          💾 {{ saving ? "Guardando..." : "Guardar Ajustes" }}
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
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 14px;
}
.form-buttons {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}
</style>
