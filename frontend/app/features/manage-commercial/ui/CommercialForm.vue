<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { AppField } from "~/shared/ui";
import { VOICES } from "~/shared/config";
import { toApiError } from "~/shared/api";
import { useBrandStore } from "~/entities/brand";
import {
  commercialApi,
  useCommercialStore,
  type Commercial,
} from "~/entities/commercial";

const props = defineProps<{ commercial?: Commercial | null }>();
const emit = defineEmits<{ saved: [commercial: Commercial]; cancel: [] }>();

const store = useCommercialStore();
const brandStore = useBrandStore();
const saving = ref(false);
const suggesting = ref(false);
const errors = ref<Record<string, string[]>>({});
const formError = ref("");

function blank() {
  return {
    brand_id: "",
    title: "",
    campaign: "",
    script: "",
    duration: 30,
    voice: "",
  };
}
const form = reactive(blank());

watch(
  () => props.commercial,
  (c) => {
    if (c) {
      Object.assign(form, {
        brand_id: c.brand_id,
        title: c.title,
        campaign: c.campaign ?? "",
        script: c.script,
        duration: c.duration,
        voice: c.voice ?? "",
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
    brand_id: form.brand_id,
    title: form.title,
    campaign: form.campaign || null,
    script: form.script,
    duration: Number(form.duration) || 30,
    voice: form.voice || null,
  };
}

async function suggest() {
  if (!form.brand_id) {
    formError.value = "Selecciona una marca antes de generar la sugerencia.";
    return;
  }
  suggesting.value = true;
  formError.value = "";
  try {
    const s = await commercialApi.suggest({ context: { brand_id: form.brand_id } });
    form.title = s.title ?? "";
    form.campaign = s.campaign ?? "";
    form.script = s.script ?? "";
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
    const saved = props.commercial
      ? await store.update(props.commercial.id, payload())
      : await store.create(payload());
    if (!props.commercial) Object.assign(form, blank());
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
    <h3>📢 {{ props.commercial ? "Editar Anuncio" : "Crear Guión de Anuncio" }}</h3>
    <p class="form-desc">
      Escribe la locución publicitaria de una marca. La IA necesita una marca seleccionada para sugerir el guión.
    </p>

    <form class="app-form" @submit.prevent="submit">
      <button
        type="button"
        class="btn btn-secondary btn-block btn-ghost-primary"
        :disabled="suggesting || !form.brand_id"
        @click="suggest"
      >
        {{ suggesting ? "✨ Generando sugerencia..." : "✨ Sugerir Comercial con IA (Autocompletar)" }}
      </button>

      <AppField label="Seleccionar Marca" :error="errors.brand_id">
        <select v-model="form.brand_id" required>
          <option value="" disabled>Elige una marca...</option>
          <option v-for="b in brandStore.items" :key="b.id" :value="b.id">
            {{ b.name }}{{ b.industry ? ` (${b.industry})` : "" }}
          </option>
        </select>
      </AppField>
      <AppField label="Título del Anuncio" :error="errors.title">
        <input v-model="form.title" placeholder="Ej. Oferta Neumáticos de Otoño" required />
      </AppField>

      <div class="duo-row">
        <AppField label="Campaña" :error="errors.campaign">
          <input v-model="form.campaign" placeholder="Ej. Lanzamiento 2026" />
        </AppField>
        <AppField label="Duración (s)" :error="errors.duration">
          <input v-model.number="form.duration" type="number" min="1" step="1" />
        </AppField>
      </div>

      <AppField label="Voz del Anuncio" :error="errors.voice">
        <select v-model="form.voice">
          <option value="">Voz por defecto</option>
          <option v-for="v in VOICES" :key="v.value" :value="v.value">{{ v.label }}</option>
        </select>
      </AppField>

      <AppField label="Guión del Locutor de Anuncios" :error="errors.script">
        <textarea v-model="form.script" rows="3" placeholder="Redacta la locución publicitaria..." required />
      </AppField>

      <p v-if="formError" class="alert alert-danger">{{ formError }}</p>

      <div class="form-buttons">
        <button v-if="props.commercial" type="button" class="btn btn-secondary" @click="emit('cancel')">Cancelar</button>
        <button type="submit" class="btn btn-primary btn-block" :disabled="saving">
          💾 {{ saving ? "Guardando..." : props.commercial ? "Actualizar Anuncio" : "Guardar Anuncio" }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped lang="scss">
.duo-row {
  display: grid;
  grid-template-columns: 1fr 100px;
  gap: 10px;
}
.form-buttons {
  display: flex;
  gap: 10px;
}
</style>
