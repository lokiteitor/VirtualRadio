<script setup lang="ts">
defineProps<{ title?: string }>();
</script>

<template>
  <div class="card-container">
    <h3 v-if="title" class="app-card-title">{{ title }}</h3>
    <slot />
  </div>
</template>

<style scoped lang="scss">
.app-card-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 12px;
}
</style>
