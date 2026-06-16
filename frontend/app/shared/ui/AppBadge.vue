<script setup lang="ts">
withDefaults(defineProps<{ glow?: boolean }>(), { glow: false });
</script>

<template>
  <span class="badge" :class="{ 'badge-glow': glow }"><slot /></span>
</template>
