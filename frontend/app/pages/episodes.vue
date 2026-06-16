<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { AppPageHeader, AppEmptyState } from "~/shared/ui";
import { NAV_ITEMS } from "~/shared/config";
import { EpisodeRow, useEpisodeStore, type Episode } from "~/entities/episode";
import { useStationStore } from "~/entities/station";
import { EpisodePlayer } from "~/widgets/episode-player";

const store = useEpisodeStore();
const stationStore = useStationStore();
const selected = ref<Episode | null>(null);
const autoplay = ref(false);

onMounted(async () => {
  await Promise.all([store.fetchAll(), stationStore.fetchAll()]);
  if (!selected.value && store.items.length) selected.value = store.items[0] ?? null;
});

const stationNames = computed<Record<string, string>>(() => {
  const map: Record<string, string> = {};
  for (const s of stationStore.items) map[s.id] = s.name;
  return map;
});

function stationName(ep: Episode): string {
  return stationNames.value[ep.station_id] ?? "Emisora";
}

interface StationGroup {
  id: string;
  name: string;
  emoji: string;
  frequency: string;
  episodes: Episode[];
}

// Library grouped by station; episodes sorted newest-first by their number.
const groups = computed<StationGroup[]>(() => {
  const byStation = new Map<string, Episode[]>();
  for (const ep of store.items) {
    const list = byStation.get(ep.station_id) ?? [];
    list.push(ep);
    byStation.set(ep.station_id, list);
  }
  const result: StationGroup[] = [];
  for (const [stationId, eps] of byStation) {
    const s = stationStore.items.find((st) => st.id === stationId);
    result.push({
      id: stationId,
      name: s?.name ?? "Emisora",
      emoji: s?.emoji ?? "📻",
      frequency: s?.frequency ?? "",
      episodes: [...eps].sort((a, b) => b.episode_number - a.episode_number),
    });
  }
  result.sort((a, b) => a.name.localeCompare(b.name));
  return result;
});

function onSelect(ep: Episode) {
  autoplay.value = false;
  selected.value = ep;
}
function onPlay(ep: Episode) {
  autoplay.value = true;
  selected.value = ep;
}
async function onRemove(ep: Episode) {
  if (!confirm(`¿Eliminar el episodio "${ep.title}"? Esta acción no se puede deshacer.`)) return;
  await store.remove(ep.id);
  if (selected.value?.id === ep.id) {
    selected.value = store.items[0] ?? null;
  }
}

// Keep the selection valid if the list changes (e.g. after a delete + refetch).
watch(
  () => store.items,
  (items) => {
    if (selected.value && !items.some((e) => e.id === selected.value?.id)) {
      selected.value = items[0] ?? null;
    }
  },
);
</script>

<template>
  <div>
    <AppPageHeader title="Episodios" :subtitle="NAV_ITEMS[1]?.subtitle" />

    <AppEmptyState
      v-if="!store.items.length && !store.loading"
      icon="🎧"
      title="No hay episodios generados"
      message="Ve a la pestaña de Estaciones y genera tu primer programa de radio personalizado."
    />

    <div v-else class="episodes-container">
      <div class="episodes-list">
        <section v-for="g in groups" :key="g.id" class="station-group">
          <header class="group-header">
            <span class="group-emoji">{{ g.emoji }}</span>
            <span class="group-name">{{ g.name }}</span>
            <span v-if="g.frequency" class="group-freq">{{ g.frequency }}</span>
            <span class="group-count">{{ g.episodes.length }}</span>
          </header>
          <EpisodeRow
            v-for="ep in g.episodes"
            :key="ep.id"
            :episode="ep"
            :active="selected?.id === ep.id"
            @select="onSelect"
            @play="onPlay"
            @remove="onRemove"
          />
        </section>
      </div>

      <EpisodePlayer
        v-if="selected"
        :key="selected.id"
        :episode="selected"
        :station-name="stationName(selected)"
        :autoplay="autoplay"
      />
      <div v-else class="episode-viewer empty">
        <div class="empty-icon">👈</div>
        <p>Selecciona un episodio de la lista para escucharlo y visualizar su guión narrativo.</p>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.episodes-container {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 30px;
  align-items: start;
}
.episodes-list {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.station-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 2px 8px;
  border-bottom: 1px solid var(--border-color);
}
.group-emoji {
  font-size: 18px;
}
.group-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}
.group-freq {
  font-size: 11px;
  color: var(--text-muted);
}
.group-count {
  margin-left: auto;
  font-size: 11px;
  font-weight: 700;
  color: var(--primary);
  background: var(--primary-glow);
  padding: 2px 8px;
  border-radius: 999px;
}
.episode-viewer.empty {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-muted);
  min-height: 300px;
  gap: 12px;
}
.episode-viewer.empty .empty-icon {
  font-size: 40px;
}
</style>
