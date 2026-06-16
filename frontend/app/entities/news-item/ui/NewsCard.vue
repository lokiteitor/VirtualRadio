<script setup lang="ts">
import type { NewsItem } from "../model/types";

defineProps<{ item: NewsItem }>();
const emit = defineEmits<{ edit: [item: NewsItem]; remove: [item: NewsItem] }>();
</script>

<template>
  <div class="news-card">
    <div class="news-meta">
      <span class="tag-badge">{{ item.category }}</span>
      <span class="tone-badge">{{ item.tone }}</span>
      <span v-if="!item.is_active" class="inactive-badge">Inactiva</span>
    </div>
    <h4>{{ item.headline }}</h4>
    <p v-if="item.summary">{{ item.summary }}</p>
    <div v-if="item.full_script" class="full-script-preview">
      <strong>Guión de Voz:</strong>
      <p class="quote">"{{ item.full_script }}"</p>
    </div>
    <div class="news-actions">
      <button class="btn btn-secondary btn-sm" @click="emit('edit', item)">✏️ Editar</button>
      <button class="btn btn-secondary btn-sm" @click="emit('remove', item)">🗑️</button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.news-card {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 20px;
  transition: border-color 0.2s ease;
}
.news-card:hover {
  border-color: var(--primary);
}
.news-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}
.tag-badge {
  background-color: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}
.tone-badge {
  background-color: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
  border: 1px solid rgba(139, 92, 246, 0.3);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}
.inactive-badge {
  background-color: rgba(148, 163, 184, 0.15);
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.3);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}
.news-card h4 {
  font-size: 16px;
  margin-bottom: 8px;
}
.news-card p {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
  margin-bottom: 12px;
}
.full-script-preview {
  background-color: var(--bg-deep);
  border-radius: var(--radius-sm);
  padding: 12px;
  font-size: 12px;
}
.full-script-preview .quote {
  font-style: italic;
  color: #d1d5db;
  margin-top: 4px;
  margin-bottom: 0;
}
.news-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 14px;
}
</style>
