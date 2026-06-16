<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { AppField } from "~/shared/ui";
import { toApiError } from "~/shared/api";
import { arrayToLines, linesToArray } from "~/shared/lib";
import { stationApi, useStationStore, type Station } from "~/entities/station";

const props = defineProps<{ station?: Station | null }>();
const emit = defineEmits<{ saved: [station: Station]; cancel: [] }>();

const store = useStationStore();
const saving = ref(false);
const suggesting = ref(false);
const errors = ref<Record<string, string[]>>({});
const formError = ref("");

function blank() {
  return {
    name: "",
    host_name: "",
    description: "",
    personality: "",
    frequency: "",
    emoji: "📻",
    color: "#d97706",
    intro_raw: "",
    outro_raw: "",
  };
}
const form = reactive(blank());

watch(
  () => props.station,
  (s) => {
    if (s) {
      Object.assign(form, {
        name: s.name,
        host_name: s.host_name ?? "",
        description: s.description ?? "",
        personality: s.personality ?? "",
        frequency: s.frequency ?? "",
        emoji: s.emoji ?? "📻",
        color: s.color ?? "#d97706",
        intro_raw: arrayToLines(s.intro_templates),
        outro_raw: arrayToLines(s.outro_templates),
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
    name: form.name,
    host_name: form.host_name || null,
    description: form.description || null,
    personality: form.personality || null,
    frequency: form.frequency || null,
    emoji: form.emoji || null,
    color: form.color || null,
    intro_templates: linesToArray(form.intro_raw),
    outro_templates: linesToArray(form.outro_raw),
  };
}

async function suggest() {
  suggesting.value = true;
  formError.value = "";
  try {
    const s = await stationApi.suggest({ context: { name: form.name || undefined } });
    form.name = s.name || form.name;
    form.host_name = s.host_name ?? "";
    form.description = s.description ?? "";
    form.personality = s.personality ?? "";
    form.frequency = s.frequency ?? "";
    form.emoji = s.emoji ?? "📻";
    form.color = s.color ?? "#d97706";
    form.intro_raw = arrayToLines(s.intro_templates ?? []);
    form.outro_raw = arrayToLines(s.outro_templates ?? []);
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
    const saved = props.station
      ? await store.update(props.station.id, payload())
      : await store.create(payload());
    if (!props.station) Object.assign(form, blank());
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
    <h3>📻 {{ props.station ? "Editar Emisora" : "Registrar Nueva Emisora" }}</h3>
    <p class="form-desc">
      Crea o ajusta una emisora. Define su locutor y las frases con las que abre y cierra cada programa.
    </p>

    <form class="app-form" @submit.prevent="submit">
      <button
        type="button"
        class="btn btn-secondary btn-block btn-ghost-primary"
        :disabled="suggesting"
        @click="suggest"
      >
        {{ suggesting ? "✨ Generando sugerencia..." : "✨ Sugerir Emisora con IA" }}
      </button>

      <AppField label="Nombre de la Emisora" :error="errors.name">
        <input v-model="form.name" placeholder="Ej. Radio Cumbia 98" required />
      </AppField>
      <AppField label="Locutor Principal" :error="errors.host_name">
        <input v-model="form.host_name" placeholder="Ej. El Primo Paco" />
      </AppField>

      <div class="triple-row">
        <AppField label="Frecuencia" :error="errors.frequency">
          <input v-model="form.frequency" placeholder="98.5 FM" />
        </AppField>
        <AppField label="Color">
          <input v-model="form.color" type="color" class="color-input" />
        </AppField>
        <AppField label="Emoji">
          <input v-model="form.emoji" class="emoji-input" placeholder="📻" />
        </AppField>
      </div>

      <AppField label="Personalidad del Locutor" :error="errors.personality">
        <input v-model="form.personality" placeholder="Ej. Entusiasta, habla de bailes de pueblo" />
      </AppField>
      <AppField label="Descripción / Estilo" :error="errors.description">
        <textarea v-model="form.description" rows="2" placeholder="Estilo musical o de contenido..." />
      </AppField>
      <AppField label="Plantillas de Apertura (una por línea)">
        <textarea v-model="form.intro_raw" rows="3" placeholder="¡Buenos días!&#10;Aquí Paco subiendo el volumen..." />
      </AppField>
      <AppField label="Plantillas de Cierre (una por línea)">
        <textarea v-model="form.outro_raw" rows="3" placeholder="¡Adiós!&#10;Paco se despide..." />
      </AppField>

      <p v-if="formError" class="alert alert-danger">{{ formError }}</p>

      <div class="form-buttons">
        <button v-if="props.station" type="button" class="btn btn-secondary" @click="emit('cancel')">Cancelar</button>
        <button type="submit" class="btn btn-primary btn-block" :disabled="saving">
          💾 {{ saving ? "Guardando..." : props.station ? "Actualizar" : "Guardar Emisora" }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped lang="scss">
.triple-row {
  display: grid;
  grid-template-columns: 1fr 80px 80px;
  gap: 10px;
}
.color-input {
  height: 42px;
  padding: 2px;
  cursor: pointer;
  width: 100%;
}
.emoji-input {
  text-align: center;
}
.form-buttons {
  display: flex;
  gap: 10px;
}
</style>
