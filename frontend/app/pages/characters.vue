<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { AppPageHeader, AppEmptyState } from "~/shared/ui";
import { NAV_ITEMS } from "~/shared/config";
import {
  CharacterCard,
  characterApi,
  useCharacterStore,
  type Character,
  type CharacterMemory,
} from "~/entities/character";
import { CharacterForm } from "~/features/manage-character";

const store = useCharacterStore();
const editing = ref<Character | null>(null);
const memories = reactive<Record<string, CharacterMemory[]>>({});
const loadingMemories = ref<Set<string>>(new Set());

const nav = NAV_ITEMS.find((n) => n.id === "characters")!;

onMounted(() => store.fetchAll());

async function onLoadMemories(id: string) {
  if (memories[id] !== undefined || loadingMemories.value.has(id)) return;
  loadingMemories.value.add(id);
  try {
    memories[id] = await characterApi.memories(id);
  } finally {
    loadingMemories.value.delete(id);
  }
}

function onEdit(c: Character) {
  editing.value = c;
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

async function onRemove(c: Character) {
  if (confirm(`¿Eliminar a "${c.name}"? Se borrarán también sus recuerdos.`)) {
    await store.remove(c.id);
    delete memories[c.id];
    if (editing.value?.id === c.id) editing.value = null;
  }
}

function onSaved() {
  editing.value = null;
}
</script>

<template>
  <div>
    <AppPageHeader title="Personajes" :subtitle="nav.subtitle" />

    <div class="split-pane">
      <div class="card-container">
        <div class="section-title-row">
          <h3>Personajes del Universo</h3>
          <span class="badge">{{ store.items.length }} personajes</span>
        </div>

        <div v-if="store.items.length" class="characters-grid">
          <CharacterCard
            v-for="c in store.items"
            :key="c.id"
            :character="c"
            :memories="memories[c.id]"
            @load-memories="onLoadMemories"
            @edit="onEdit"
            @remove="onRemove"
          />
        </div>
        <AppEmptyState
          v-else-if="!store.loading"
          icon="👥"
          title="No hay personajes"
          message="Registra al primer habitante de la vecindad con el formulario de la derecha."
        />
      </div>

      <CharacterForm :character="editing" @saved="onSaved" @cancel="editing = null" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.characters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
}
</style>
