<script setup lang="ts">
defineProps<{ title: string; subtitle?: string }>();
</script>

<template>
  <header class="content-header">
    <div class="page-title">
      <h2>{{ title }}</h2>
      <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
    </div>
    <div class="quick-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped lang="scss">
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  gap: 16px;
  flex-wrap: wrap;
}
.page-title h2 {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin-bottom: 4px;
}
.page-title .subtitle {
  color: var(--text-muted);
  font-size: 14px;
  max-width: 700px;
}
</style>
