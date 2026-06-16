<script setup lang="ts">
import { formatDuration } from "~/shared/lib";
import type { Commercial } from "../model/types";

defineProps<{ commercial: Commercial; brandName?: string }>();
const emit = defineEmits<{ edit: [commercial: Commercial]; remove: [commercial: Commercial] }>();
</script>

<template>
  <div class="comm-card">
    <div class="comm-header">
      <h5>{{ commercial.title }}</h5>
      <span class="brand-tag">{{ brandName || "Marca" }}</span>
    </div>
    <p class="comm-script">"{{ commercial.script }}"</p>
    <div class="comm-footer">
      <div class="comm-meta">
        <span>⏱️ {{ formatDuration(commercial.duration) }}</span>
        <span v-if="commercial.campaign">📁 Campaña: {{ commercial.campaign }}</span>
      </div>
      <div class="comm-actions">
        <button class="btn btn-secondary btn-sm" @click="emit('edit', commercial)">✏️</button>
        <button class="btn btn-secondary btn-sm" @click="emit('remove', commercial)">🗑️</button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.comm-card {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 20px;
}
.comm-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  align-items: center;
  gap: 12px;
}
.comm-header h5 {
  font-size: 15px;
}
.brand-tag {
  background-color: var(--primary-glow);
  color: var(--primary);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}
.comm-script {
  font-style: italic;
  font-size: 13px;
  color: #e5e7eb;
  line-height: 1.5;
  margin-bottom: 12px;
}
.comm-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.comm-meta {
  display: flex;
  gap: 16px;
  font-size: 11px;
  color: var(--text-muted);
  flex-wrap: wrap;
}
.comm-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
</style>
