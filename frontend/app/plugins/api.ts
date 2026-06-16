// Centralized HTTP client provided as $api: base URL from runtimeConfig, JWT
// from the session store, and 401 -> clear session + redirect to /login.
import { useSessionStore } from "~/entities/session";

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig();

  const api = $fetch.create({
    baseURL: config.public.apiBase as string,

    onRequest({ options }) {
      const session = useSessionStore();
      if (session.accessToken) {
        const headers = new Headers(options.headers as HeadersInit | undefined);
        headers.set("Authorization", `Bearer ${session.accessToken}`);
        options.headers = headers;
      }
    },

    async onResponseError({ response }) {
      if (response.status === 401) {
        const session = useSessionStore();
        // Ignore 401s from the login/register calls themselves (no token yet).
        if (session.accessToken) {
          session.clear();
          await navigateTo("/login");
        }
      }
    },
  });

  return { provide: { api } };
});
