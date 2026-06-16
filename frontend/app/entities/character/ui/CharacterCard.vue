<script setup lang="ts">
import { formatDate, getAvatarEmoji } from "~/shared/lib";
import type { Character, CharacterMemory } from "../model/types";

defineProps<{ character: Character; memories?: CharacterMemory[] }>();
const emit = defineEmits<{
  loadMemories: [id: string];
  edit: [character: Character];
  remove: [character: Character];
}>();
</script>

<template>
  <div class="character-detail-card" @click="emit('loadMemories', character.id)">
    <div class="char-header">
      <div class="char-avatar">{{ getAvatarEmoji(character.name) }}</div>
      <div class="char-title-meta">
        <h3>{{ character.name }}</h3>
        <span v-if="character.role" class="role-badge">{{ character.role }}</span>
      </div>
      <div class="char-actions">
        <button class="btn btn-secondary btn-sm" @click.stop="emit('edit', character)">✏️</button>
        <button class="btn btn-secondary btn-sm" @click.stop="emit('remove', character)">🗑️</button>
      </div>
    </div>

    <div class="char-body">
      <p v-if="character.personality">
        <strong>Personalidad:</strong> {{ character.personality }}
      </p>
      <p v-if="character.station_affinity">
        <strong>Afinidad Radial:</strong> {{ character.station_affinity }}
      </p>
      <p v-if="character.description" class="description">{{ character.description }}</p>
    </div>

    <div class="char-memory-container">
      <h4>🧠 Memoria Narrativa Reciente</h4>
      <div v-if="memories === undefined" class="memory-loading">
        Haga clic para cargar recuerdos...
      </div>
      <div v-else-if="memories.length === 0" class="memory-empty">
        No tiene recuerdos en la base de datos todavía.
      </div>
      <div v-else class="memory-list">
        <div v-for="mem in memories" :key="mem.id" class="memory-item">
          <span class="memory-date">🗓️ {{ formatDate(mem.created_at) }}</span>
          <p class="memory-text">"{{ mem.memory }}"</p>
          <span v-if="mem.episode_id" class="memory-ep">Importancia: {{ mem.importance }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.character-detail-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.character-detail-card:hover {
  transform: translateY(-2px);
  border-color: var(--secondary);
}
.char-header {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 16px;
}
.char-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}
.char-title-meta {
  flex: 1;
  min-width: 0;
}
.char-title-meta h3 {
  font-size: 18px;
}
.role-badge {
  display: inline-block;
  font-size: 10px;
  background-color: rgba(139, 92, 246, 0.1);
  color: #a78bfa;
  border: 1px solid rgba(139, 92, 246, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  margin-top: 4px;
}
.char-actions {
  display: flex;
  gap: 6px;
}
.char-body {
  font-size: 13px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 20px;
}
.char-body .description {
  color: var(--text-muted);
  line-height: 1.4;
  margin-top: 4px;
}
.char-memory-container {
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
}
.char-memory-container h4 {
  font-size: 12px;
  color: var(--secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}
.memory-loading,
.memory-empty {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
}
.memory-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.memory-item {
  background-color: var(--bg-card);
  padding: 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  position: relative;
}
.memory-date {
  font-size: 9px;
  color: var(--text-muted);
}
.memory-text {
  margin-top: 2px;
  line-height: 1.4;
}
.memory-ep {
  font-size: 9px;
  color: var(--secondary);
  font-weight: 600;
  display: block;
  margin-top: 4px;
}
</style>
