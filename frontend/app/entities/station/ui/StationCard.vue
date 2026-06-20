<script setup lang="ts">
import type { Station } from "../model/types";

defineProps<{ station: Station; generating?: boolean }>();
const emit = defineEmits<{
  generate: [station: Station];
  edit: [station: Station];
  remove: [station: Station];
  settings: [station: Station];
  music: [station: Station];
}>();
</script>

<template>
  <div class="station-card" :style="{ '--card-accent': station.color || '#f59e0b' }">
    <div class="station-header">
      <div class="station-icon">{{ station.emoji || "📻" }}</div>
      <div class="station-frequency">{{ station.frequency || "—" }}</div>
    </div>
    <div class="station-body">
      <h3>{{ station.name }}</h3>
      <p class="description">{{ station.description }}</p>
      <div class="station-meta">
        <span class="meta-item">🗣️ <strong>Locutor:</strong> {{ station.host_name }}</span>
        <span class="meta-item">🎭 <strong>Personalidad:</strong> {{ station.personality }}</span>
      </div>
    </div>
    <div class="station-footer">
      <button class="btn btn-primary btn-block" :disabled="generating" @click="emit('generate', station)">
        ⚡ Generar Episodio
      </button>
      <div class="station-actions">
        <button class="btn btn-secondary btn-sm" @click="emit('edit', station)">✏️ Editar</button>
        <button class="btn btn-secondary btn-sm" @click="emit('settings', station)">⚙️ Guion</button>
        <button class="btn btn-secondary btn-sm" @click="emit('music', station)">🎵 Música</button>
        <button class="btn btn-secondary btn-sm" @click="emit('remove', station)">🗑️</button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.station-card {
  background: linear-gradient(135deg, var(--bg-surface), #151e33);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.station-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background-color: var(--card-accent);
}
.station-card:hover {
  transform: translateY(-5px);
  border-color: var(--card-accent);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}
.station-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.station-icon {
  font-size: 32px;
}
.station-frequency {
  font-family: "JetBrains Mono", monospace;
  font-weight: 700;
  font-size: 13px;
  color: var(--card-accent);
  background: rgba(255, 255, 255, 0.03);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
.station-body {
  flex: 1;
  margin-bottom: 24px;
}
.station-body h3 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 8px;
}
.station-body .description {
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 16px;
}
.station-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
}
.meta-item {
  color: #e5e7eb;
}
.station-footer {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.station-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
