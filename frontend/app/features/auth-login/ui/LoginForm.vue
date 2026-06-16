<script setup lang="ts">
import { reactive, ref } from "vue";
import { AppField } from "~/shared/ui";
import { toApiError } from "~/shared/api";
import { useSessionStore } from "~/entities/session";

const session = useSessionStore();
const mode = ref<"login" | "register">("login");
const loading = ref(false);
const error = ref("");
const form = reactive({ email: "", password: "", display_name: "" });

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    if (mode.value === "login") {
      await session.login({ email: form.email, password: form.password });
    } else {
      await session.register({
        email: form.email,
        password: form.password,
        display_name: form.display_name || undefined,
      });
    }
    await navigateTo("/");
  } catch (e) {
    error.value = toApiError(e).message;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-card">
    <div class="login-brand">
      <div class="logo">📻</div>
      <h1>VirtualRadio</h1>
      <p>Genera radio satírica para tus simuladores</p>
    </div>

    <div class="mode-tabs">
      <button :class="{ active: mode === 'login' }" @click="mode = 'login'">Iniciar sesión</button>
      <button :class="{ active: mode === 'register' }" @click="mode = 'register'">Crear cuenta</button>
    </div>

    <form class="app-form" @submit.prevent="submit">
      <AppField label="Email">
        <input v-model="form.email" type="email" placeholder="tu@email.com" required autocomplete="email" />
      </AppField>
      <AppField label="Contraseña">
        <input
          v-model="form.password"
          type="password"
          placeholder="••••••••"
          required
          minlength="8"
          :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
        />
      </AppField>
      <AppField v-if="mode === 'register'" label="Nombre visible (opcional)">
        <input v-model="form.display_name" type="text" placeholder="Tu nombre" autocomplete="name" />
      </AppField>

      <p v-if="error" class="alert alert-danger">{{ error }}</p>

      <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
        <span v-if="loading">Procesando...</span>
        <span v-else>{{ mode === "login" ? "Entrar" : "Registrarme" }}</span>
      </button>
    </form>
  </div>
</template>

<style scoped lang="scss">
.login-card {
  width: 400px;
  max-width: 100%;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 36px;
  box-shadow: var(--shadow-lg);
}
.login-brand {
  text-align: center;
  margin-bottom: 28px;
}
.login-brand .logo {
  font-size: 40px;
}
.login-brand h1 {
  font-size: 24px;
  font-weight: 800;
  margin-top: 8px;
}
.login-brand p {
  color: var(--text-muted);
  font-size: 13px;
  margin-top: 4px;
}
.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  background: var(--bg-deep);
  padding: 4px;
  border-radius: var(--radius-md);
}
.mode-tabs button {
  flex: 1;
  background: none;
  border: none;
  color: var(--text-muted);
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.mode-tabs button.active {
  background: var(--bg-card);
  color: var(--primary);
}
</style>
