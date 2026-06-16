<script setup lang="ts">
import { SidebarNav } from "~/widgets/sidebar-nav";
</script>

<template>
  <div class="app-shell">
    <SidebarNav />
    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<style scoped lang="scss">
.app-shell {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 40px;
  overflow-y: auto;
}
@media (max-width: 720px) {
  .app-shell {
    flex-direction: column;
  }
  .main-content {
    padding: 20px;
  }
}
</style>
