<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { AppField } from "~/shared/ui";
import { VOICES } from "~/shared/config";
import { toApiError } from "~/shared/api";
import { characterApi, useCharacterStore, type Character } from "~/entities/character";

const props = defineProps<{ character?: Character | null }>();
const emit = defineEmits<{ saved: [character: Character]; cancel: [] }>();

const store = useCharacterStore();
const saving = ref(false);
const suggesting = ref(false);
const errors = ref<Record<string, string[]>>({});
const formError = ref("");

function blank() {
  return {
    name: "",
    role: "",
    station_affinity: "",
    personality: "",
    description: "",
    voice: "",
  };
}
const form = reactive(blank());

watch(
  () => props.character,
  (c) => {
    if (c) {
      Object.assign(form, {
        name: c.name,
        role: c.role ?? "",
        station_affinity: c.station_affinity ?? "",
        personality: c.personality ?? "",
        description: c.description ?? "",
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
    name: form.name,
    role: form.role || null,
    station_affinity: form.station_affinity || null,
    personality: form.personality || null,
    description: form.description || null,
    voice: form.voice || null,
  };
}

async function suggest() {
  suggesting.value = true;
  formError.value = "";
  try {
    const c = await characterApi.suggest({ context: { name: form.name || undefined } });
    form.name = c.name || form.name;
    form.role = c.role ?? "";
    form.station_affinity = c.station_affinity ?? "";
    form.personality = c.personality ?? "";
    form.description = c.description ?? "";
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
    const saved = props.character
      ? await store.update(props.character.id, payload())
      : await store.create(payload());
    if (!props.character) Object.assign(form, blank());
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
    <h3>👥 {{ props.character ? "Editar Personaje" : "Registrar Personaje de la Vecindad" }}</h3>
    <p class="form-desc">
      Define un nuevo habitante de la comunidad. Los locutores podrán llamarlo por teléfono o
      comentarlo en sus historias.
    </p>

    <form class="app-form" @submit.prevent="submit">
      <button
        type="button"
        class="btn btn-secondary btn-block btn-ghost-primary"
        :disabled="suggesting"
        @click="suggest"
      >
        {{ suggesting ? "✨ Generando sugerencia..." : "✨ Sugerir Personaje con IA (Autocompletar)" }}
      </button>

      <AppField label="Nombre del Personaje" :error="errors.name">
        <input v-model="form.name" placeholder="Ej. Pedro 'El Mecánico'" required />
      </AppField>
      <AppField label="Rol / Ocupación" :error="errors.role">
        <input v-model="form.role" placeholder="Ej. Mecánico local de tractores" />
      </AppField>
      <AppField label="Afinidad Radial (Emisoras, separadas por coma)" :error="errors.station_affinity">
        <input v-model="form.station_affinity" placeholder="Ej. AgroTalk FM, WCTR Sim Edition" />
      </AppField>
      <AppField label="Personalidad / Rasgos de Habla" :error="errors.personality">
        <input v-model="form.personality" placeholder="Ej. Gruñón, habla lento, obsesionado con bujías" />
      </AppField>
      <AppField label="Voz del Personaje (llamadas)" :error="errors.voice">
        <select v-model="form.voice">
          <option value="">Voz por defecto</option>
          <option v-for="v in VOICES" :key="v.value" :value="v.value">{{ v.label }}</option>
        </select>
      </AppField>
      <AppField label="Descripción / Trasfondo" :error="errors.description">
        <textarea
          v-model="form.description"
          rows="3"
          placeholder="Describe brevemente su historia personal o relación con otros..."
        />
      </AppField>

      <p v-if="formError" class="alert alert-danger">{{ formError }}</p>

      <div class="form-buttons">
        <button v-if="props.character" type="button" class="btn btn-secondary" @click="emit('cancel')">
          Cancelar
        </button>
        <button type="submit" class="btn btn-primary btn-block" :disabled="saving">
          💾 {{ saving ? "Guardando..." : props.character ? "Actualizar" : "Guardar Personaje" }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped lang="scss">
.form-buttons {
  display: flex;
  gap: 10px;
}
</style>
