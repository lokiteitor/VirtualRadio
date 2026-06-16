<script setup lang="ts">
defineProps<{ label: string; error?: string | string[] | null }>();

function firstError(error?: string | string[] | null): string | null {
  if (!error) return null;
  return Array.isArray(error) ? error[0] ?? null : error;
}
</script>

<template>
  <div class="form-group">
    <label>{{ label }}</label>
    <slot />
    <span v-if="firstError(error)" class="field-error">{{ firstError(error) }}</span>
  </div>
</template>
