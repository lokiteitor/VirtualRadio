<script setup lang="ts">
defineProps<{ icon?: string; title?: string; message?: string }>();
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon">{{ icon || "📭" }}</div>
    <h3 v-if="title">{{ title }}</h3>
    <p v-if="message">{{ message }}</p>
    <slot />
  </div>
</template>
