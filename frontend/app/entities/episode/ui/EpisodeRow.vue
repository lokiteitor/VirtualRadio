<script setup lang="ts">
import { formatDate, formatDuration } from "~/shared/lib";
import type { Episode } from "../model/types";

defineProps<{ episode: Episode; stationName?: string; active?: boolean }>();
const emit = defineEmits<{
  select: [episode: Episode];
  play: [episode: Episode];
  remove: [episode: Episode];
}>();
</script>

<template>
  <div class="episode-row" :class="{ active }" @click="emit('select', episode)">
    <div class="ep-info">
      <span v-if="stationName" class="ep-badge">{{ stationName }}</span>
      <h4>{{ episode.title }}</h4>
      <div class="ep-meta">
        <span>📅 {{ formatDate(episode.created_at) }}</span>
        <span>⏱️ {{ formatDuration(episode.duration) }}</span>
      </div>
    </div>
    <div class="ep-controls">
      <button class="btn btn-sm btn-circle" title="Reproducir" @click.stop="emit('play', episode)">▶️</button>
      <button class="btn btn-sm btn-circle btn-danger" title="Eliminar" @click.stop="emit('remove', episode)">
        🗑️
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.episode-row {
  background-color: var(--bg-card);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.episode-row:hover {
  background-color: var(--bg-input);
  border-color: rgba(255, 255, 255, 0.05);
}
.episode-row.active {
  border-color: var(--primary);
  background: linear-gradient(90deg, var(--bg-input), #1e253c);
}
.ep-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}
.ep-badge {
  font-size: 9px;
  font-weight: 700;
  color: var(--primary);
  background: var(--primary-glow);
  padding: 2px 6px;
  border-radius: 4px;
  align-self: flex-start;
}
.ep-info h4 {
  font-size: 14px;
  font-weight: 600;
}
.ep-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: var(--text-muted);
}
.ep-controls {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
</style>
