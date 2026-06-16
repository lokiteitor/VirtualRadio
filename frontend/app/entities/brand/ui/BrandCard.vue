<script setup lang="ts">
import type { Brand } from "../model/types";

defineProps<{ brand: Brand }>();
</script>

<template>
  <div class="brand-pill-card">
    <h5>{{ brand.name }}</h5>
    <span v-if="brand.slogan" class="slogan">"{{ brand.slogan }}"</span>
    <span v-if="brand.industry" class="industry-badge">{{ brand.industry }}</span>
  </div>
</template>

<style scoped lang="scss">
.brand-pill-card {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 160px;
}
.brand-pill-card h5 {
  font-size: 13px;
}
.brand-pill-card .slogan {
  font-size: 10px;
  font-style: italic;
  color: var(--text-muted);
}
.industry-badge {
  font-size: 8px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.05);
  align-self: flex-start;
  padding: 1px 4px;
  border-radius: 3px;
  color: var(--primary);
}
</style>
