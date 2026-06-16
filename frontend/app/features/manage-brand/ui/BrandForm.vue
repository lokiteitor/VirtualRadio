<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { AppField } from "~/shared/ui";
import { toApiError } from "~/shared/api";
import { brandApi, useBrandStore, type Brand } from "~/entities/brand";

const props = defineProps<{ brand?: Brand | null }>();
const emit = defineEmits<{ saved: [brand: Brand]; cancel: [] }>();

const store = useBrandStore();
const saving = ref(false);
const suggesting = ref(false);
const errors = ref<Record<string, string[]>>({});
const formError = ref("");

function blank() {
  return {
    name: "",
    slogan: "",
    industry: "",
    description: "",
  };
}
const form = reactive(blank());

watch(
  () => props.brand,
  (b) => {
    if (b) {
      Object.assign(form, {
        name: b.name,
        slogan: b.slogan ?? "",
        industry: b.industry ?? "",
        description: b.description ?? "",
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
    slogan: form.slogan || null,
    industry: form.industry || null,
    description: form.description || null,
  };
}

async function suggest() {
  suggesting.value = true;
  formError.value = "";
  try {
    const s = await brandApi.suggest({ context: { name: form.name || undefined } });
    form.name = s.name || form.name;
    form.slogan = s.slogan ?? "";
    form.industry = s.industry ?? "";
    form.description = s.description ?? "";
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
    const saved = props.brand
      ? await store.update(props.brand.id, payload())
      : await store.create(payload());
    if (!props.brand) Object.assign(form, blank());
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
    <h3>🏭 {{ props.brand ? "Editar Marca" : "Registrar Marca Ficticia" }}</h3>
    <p class="form-desc">
      Crea una empresa del universo. Define su eslogan, industria y a qué se dedica.
    </p>

    <form class="app-form" @submit.prevent="submit">
      <button
        type="button"
        class="btn btn-secondary btn-block btn-ghost-primary"
        :disabled="suggesting"
        @click="suggest"
      >
        {{ suggesting ? "✨ Generando sugerencia..." : "✨ Sugerir Marca con IA (Autocompletar)" }}
      </button>

      <AppField label="Nombre de la Empresa" :error="errors.name">
        <input v-model="form.name" placeholder="Ej. MegaTruck Parts" required />
      </AppField>
      <AppField label="Eslogan Corporativo" :error="errors.slogan">
        <input v-model="form.slogan" placeholder="Ej. Piezas baratas para viajes arriesgados" />
      </AppField>
      <AppField label="Industria" :error="errors.industry">
        <input v-model="form.industry" placeholder="Ej. Repuestos / Mecánica" />
      </AppField>
      <AppField label="Descripción de Actividad" :error="errors.description">
        <textarea v-model="form.description" rows="2" placeholder="Describe qué vende la empresa..." />
      </AppField>

      <p v-if="formError" class="alert alert-danger">{{ formError }}</p>

      <div class="form-buttons">
        <button v-if="props.brand" type="button" class="btn btn-secondary" @click="emit('cancel')">Cancelar</button>
        <button type="submit" class="btn btn-secondary btn-block" :disabled="saving">
          💾 {{ saving ? "Guardando..." : props.brand ? "Actualizar Marca" : "Guardar Marca" }}
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
