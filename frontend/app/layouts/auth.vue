<template>
  <div class="auth-shell">
    <slot />
  </div>
</template>

<style scoped lang="scss">
.auth-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background:
    radial-gradient(circle at 20% 20%, rgba(245, 158, 11, 0.08), transparent 40%),
    radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.08), transparent 40%),
    var(--bg-deep);
}
</style>
