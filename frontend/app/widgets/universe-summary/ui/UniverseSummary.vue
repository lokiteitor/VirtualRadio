<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useApi } from "~/shared/api";

interface UniverseSummaryData {
  stations: number;
  episodes: number;
  news_items: number;
  brands: number;
  commercials: number;
  characters: number;
  music_tracks: number;
  story_events: number;
}

const summary = ref<UniverseSummaryData | null>(null);

async function load() {
  try {
    summary.value = await useApi().get<UniverseSummaryData>("/universe/summary");
  } catch {
    summary.value = null;
  }
}

const STATS: { key: keyof UniverseSummaryData; label: string }[] = [
  { key: "characters", label: "Personajes" },
  { key: "news_items", label: "Noticias" },
  { key: "commercials", label: "Comerciales" },
  { key: "music_tracks", label: "Canciones" },
  { key: "episodes", label: "Episodios" },
  { key: "story_events", label: "Eventos" },
];

onMounted(load);
defineExpose({ load });
</script>

<template>
  <div class="universe-summary-card">
    <div class="summary-icon">🌌</div>
    <div class="summary-details">
      <h3>Universo Narrativo Compartido</h3>
      <p>
        Todos los episodios comparten el mismo lore. Las marcas, noticias y llamadas alimentan la memoria
        persistente de los personajes locales.
      </p>
      <div class="stats-row">
        <div v-for="stat in STATS" :key="stat.key" class="stat-box">
          <span class="stat-value">{{ summary ? summary[stat.key] : "—" }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.universe-summary-card {
  background: linear-gradient(135deg, #1d1b38, #13122c);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: var(--radius-lg);
  padding: 30px;
  display: flex;
  gap: 24px;
  align-items: center;
  box-shadow: 0 10px 30px rgba(139, 92, 246, 0.1);
}
.summary-icon {
  font-size: 48px;
  background: rgba(139, 92, 246, 0.1);
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(139, 92, 246, 0.3);
  flex-shrink: 0;
}
.summary-details h3 {
  font-size: 20px;
  margin-bottom: 8px;
}
.summary-details p {
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 20px;
  max-width: 800px;
}
.stats-row {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
}
</style>
