<script setup lang="ts">
import { onMounted, ref } from "vue";
import { AppPageHeader, AppEmptyState, AppModal } from "~/shared/ui";
import { NAV_ITEMS } from "~/shared/config";
import { StationCard, useStationStore, type Station } from "~/entities/station";
import { StationForm } from "~/features/manage-station";
import { EpisodeSettingsForm } from "~/features/manage-episode-settings";
import { StationMusicPanel } from "~/features/assign-station-music";
import { useGenerateEpisode } from "~/features/generate-episode";
import { GenerationPipelineModal } from "~/widgets/generation-pipeline-modal";
import { UniverseSummary } from "~/widgets/universe-summary";

const store = useStationStore();
const editing = ref<Station | null>(null);
const settingsFor = ref<Station | null>(null);
const musicFor = ref<Station | null>(null);
const { job, isOpen, start, close } = useGenerateEpisode();

onMounted(() => store.fetchAll());

function onGenerate(s: Station) {
  start(s.id, s.name);
}
function onEdit(s: Station) {
  editing.value = s;
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}
function onSettings(s: Station) {
  settingsFor.value = s;
}
function onMusic(s: Station) {
  musicFor.value = s;
}
async function onRemove(s: Station) {
  if (confirm(`¿Eliminar "${s.name}"? Se borrarán sus episodios y jobs asociados.`)) {
    await store.remove(s.id);
  }
}
function viewEpisode() {
  close();
  navigateTo("/episodes");
}
</script>

<template>
  <div>
    <AppPageHeader title="Estaciones" :subtitle="NAV_ITEMS.find((i) => i.id === 'stations')?.subtitle" />

    <div class="split-pane">
      <div class="card-container">
        <div class="section-title-row">
          <h3>Estaciones Disponibles</h3>
          <span class="badge">{{ store.items.length }} emisoras</span>
        </div>
        <div v-if="store.items.length" class="stations-grid">
          <StationCard
            v-for="s in store.items"
            :key="s.id"
            :station="s"
            :generating="isOpen"
            @generate="onGenerate"
            @edit="onEdit"
            @settings="onSettings"
            @music="onMusic"
            @remove="onRemove"
          />
        </div>
        <AppEmptyState
          v-else-if="!store.loading"
          icon="📻"
          title="No hay estaciones"
          message="Crea tu primera emisora con el formulario de la derecha."
        />
      </div>

      <StationForm :station="editing" @saved="editing = null" @cancel="editing = null" />
    </div>

    <UniverseSummary class="summary-spacer" />

    <GenerationPipelineModal
      v-if="isOpen && job"
      :job="job"
      @close="close"
      @view-episode="viewEpisode"
    />

    <AppModal
      v-if="settingsFor"
      :title="`⚙️ Guion · ${settingsFor.name}`"
      @close="settingsFor = null"
    >
      <EpisodeSettingsForm
        :station-id="settingsFor.id"
        :station-name="settingsFor.name"
        @saved="settingsFor = null"
        @cancel="settingsFor = null"
      />
    </AppModal>

    <AppModal
      v-if="musicFor"
      :title="`🎵 Música · ${musicFor.name}`"
      @close="musicFor = null"
    >
      <StationMusicPanel
        :station-id="musicFor.id"
        :station-name="musicFor.name"
        @saved="musicFor = null"
        @cancel="musicFor = null"
      />
    </AppModal>
  </div>
</template>

<style scoped lang="scss">
.stations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}
.summary-spacer {
  margin-top: 30px;
}
</style>
