<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { AppField } from "~/shared/ui";
import { toApiError } from "~/shared/api";
import { NEWS_CATEGORIES, NEWS_TONES } from "~/shared/config";
import { newsApi, useNewsStore, type NewsItem } from "~/entities/news-item";

const props = defineProps<{ item?: NewsItem | null }>();
const emit = defineEmits<{ saved: [item: NewsItem]; cancel: [] }>();

const store = useNewsStore();
const saving = ref(false);
const suggesting = ref(false);
const errors = ref<Record<string, string[]>>({});
const formError = ref("");

function blank() {
  return {
    headline: "",
    summary: "",
    full_script: "",
    category: NEWS_CATEGORIES[0]?.value ?? "",
    tone: NEWS_TONES[0]?.value ?? "",
    is_active: true,
  };
}
const form = reactive(blank());

watch(
  () => props.item,
  (n) => {
    if (n) {
      Object.assign(form, {
        headline: n.headline,
        summary: n.summary ?? "",
        full_script: n.full_script ?? "",
        category: n.category,
        tone: n.tone,
        is_active: n.is_active,
      });
    } else {
      Object.assign(form, blank());
    }
    errors.value = {};
    formError.value = "";
  },
  { immediate: true },
);

function payload() {
  return {
    headline: form.headline,
    summary: form.summary || null,
    full_script: form.full_script || null,
    category: form.category,
    tone: form.tone,
    is_active: form.is_active,
  };
}

async function suggest() {
  suggesting.value = true;
  formError.value = "";
  try {
    const s = await newsApi.suggest({ context: { category: form.category, tone: form.tone } });
    form.headline = s.headline || form.headline;
    form.summary = s.summary ?? "";
    form.full_script = s.full_script ?? "";
    form.category = s.category || form.category;
    form.tone = s.tone || form.tone;
  } catch (e) {
    formError.value = toApiError(e).message;
  } finally {
    suggesting.value = false;
  }
}

async function submit() {
  saving.value = true;
  errors.value = {};
  formError.value = "";
  try {
    const saved = props.item
      ? await store.update(props.item.id, payload())
      : await store.create(payload());
    if (!props.item) Object.assign(form, blank());
    emit("saved", saved);
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
  <div class="card-container">
    <h3>📢 {{ props.item ? "Editar Noticia" : "Crear Noticia Ficticia" }}</h3>
    <p class="form-desc">
      Inserta una noticia en el universo compartido. Los agentes de radio la comentarán en los
      próximos episodios de acuerdo a su personalidad.
    </p>

    <form class="app-form" @submit.prevent="submit">
      <button
        type="button"
        class="btn btn-secondary btn-block btn-ghost-primary"
        :disabled="suggesting"
        @click="suggest"
      >
        {{ suggesting ? "✨ Generando sugerencia..." : "✨ Sugerir Noticia con IA (Autocompletar)" }}
      </button>

      <AppField label="Titular Impactante" :error="errors.headline">
        <input v-model="form.headline" placeholder="Ej. Plaga de termitas devora tractor en segundos" required />
      </AppField>
      <AppField label="Breve Resumen" :error="errors.summary">
        <input v-model="form.summary" placeholder="Ej. El granjero reporta pérdida total del motor..." />
      </AppField>

      <div class="dual-row">
        <AppField label="Categoría" :error="errors.category">
          <select v-model="form.category">
            <option v-for="c in NEWS_CATEGORIES" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </AppField>
        <AppField label="Tono Periodístico" :error="errors.tone">
          <select v-model="form.tone">
            <option v-for="t in NEWS_TONES" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </AppField>
      </div>

      <AppField label="Guión Completo del Reportero (Será leído por TTS)" :error="errors.full_script">
        <textarea
          v-model="form.full_script"
          rows="5"
          placeholder="Escribe lo que el reportero dirá exactamente en el micrófono de noticias..."
        />
      </AppField>

      <label class="checkbox-row">
        <input v-model="form.is_active" type="checkbox" />
        <span>Noticia activa (disponible para los episodios)</span>
      </label>

      <p v-if="formError" class="alert alert-danger">{{ formError }}</p>

      <div class="form-buttons">
        <button v-if="props.item" type="button" class="btn btn-secondary" @click="emit('cancel')">Cancelar</button>
        <button type="submit" class="btn btn-primary btn-block" :disabled="saving">
          💾 {{ saving ? "Guardando..." : props.item ? "Actualizar" : "Registrar Noticia" }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped lang="scss">
.dual-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.checkbox-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-muted);
  cursor: pointer;
}
.checkbox-row input {
  width: auto;
  cursor: pointer;
}
.form-buttons {
  display: flex;
  gap: 10px;
}
</style>
