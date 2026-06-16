<script setup lang="ts">
import { onMounted, ref } from "vue";
import { NAV_ITEMS } from "~/shared/config";
import { useSessionStore } from "~/entities/session";

const session = useSessionStore();
const config = useRuntimeConfig();
const route = useRoute();
const connected = ref(false);

async function ping() {
  try {
    await $fetch("/health", { baseURL: config.public.apiBase as string });
    connected.value = true;
  } catch {
    connected.value = false;
  }
}

function isActive(to: string): boolean {
  return route.path === to;
}

onMounted(ping);
</script>

<template>
  <aside class="sidebar">
    <div class="brand">
      <div class="logo-icon">
        <span class="pulse-ring" />
        📻
      </div>
      <div class="brand-text">
        <h1>VirtualRadio</h1>
        <span class="badge badge-glow">v1.0</span>
      </div>
    </div>

    <nav class="nav-menu">
      <NuxtLink
        v-for="item in NAV_ITEMS"
        :key="item.id"
        :to="item.to"
        class="nav-item"
        :class="{ active: isActive(item.to) }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </NuxtLink>
    </nav>

    <div class="sidebar-footer">
      <div class="server-status">
        <span class="status-indicator" :class="{ online: connected }" />
        <span>API: {{ connected ? "CONECTADO" : "DESCONECTADO" }}</span>
      </div>
      <div class="user-row">
        <span class="user-name" :title="session.displayName">👤 {{ session.displayName }}</span>
        <button class="logout-btn" title="Cerrar sesión" @click="session.logout()">Salir</button>
      </div>
      <p class="copyright">VirtualRadio &copy; 2026</p>
    </div>
  </aside>
</template>

<style scoped lang="scss">
.sidebar {
  width: 260px;
  flex-shrink: 0;
  background-color: var(--bg-surface);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 24px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 40px;
}
.logo-icon {
  position: relative;
  font-size: 28px;
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid var(--primary);
  animation: pulse 2s infinite;
  opacity: 0;
}
@keyframes pulse {
  0% {
    transform: scale(0.95);
    opacity: 0.8;
  }
  100% {
    transform: scale(1.4);
    opacity: 0;
  }
}
.brand-text h1 {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #fff, #9ca3af);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 15px;
  font-weight: 500;
  text-align: left;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}
.nav-item:hover {
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
}
.nav-item.active {
  background: var(--bg-card);
  color: var(--primary);
  box-shadow: var(--shadow-sm);
  border-left: 3px solid var(--primary);
}
.nav-icon {
  font-size: 18px;
}
.sidebar-footer {
  margin-top: auto;
  border-top: 1px solid var(--border-color);
  padding-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.server-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
}
.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--danger);
  box-shadow: 0 0 8px var(--danger);
}
.status-indicator.online {
  background-color: var(--success);
  box-shadow: 0 0 8px var(--success);
}
.user-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.user-name {
  font-size: 12px;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.logout-btn {
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-family: inherit;
  flex-shrink: 0;
}
.logout-btn:hover {
  color: var(--danger);
  border-color: var(--danger);
}
.copyright {
  font-size: 11px;
  color: #4b5563;
}
@media (max-width: 720px) {
  .sidebar {
    width: 100%;
    flex-direction: row;
    flex-wrap: wrap;
    padding: 16px;
  }
  .brand {
    margin-bottom: 0;
  }
  .nav-menu {
    flex-direction: row;
    flex-wrap: wrap;
    flex-basis: 100%;
  }
  .sidebar-footer {
    margin-top: 0;
    border-top: none;
    padding-top: 0;
  }
}
</style>
