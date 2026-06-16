import { fileURLToPath } from "node:url";

// Absolute path to the SCSS tokens/mixins so they can be auto-injected into
// every component <style lang="scss"> block (pure @use, emits no CSS).
const stylesDir = fileURLToPath(new URL("./app/shared/styles", import.meta.url));

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-01-01",
  // Authenticated control panel: render client-side (SPA) to simplify JWT handling.
  ssr: false,
  devtools: { enabled: false },
  modules: ["@pinia/nuxt"],
  css: ["~/shared/styles/global.scss"],
  runtimeConfig: {
    public: {
      // Base URL of the VirtualRadio backend API (never hardcoded in code).
      apiBase: "http://localhost:5000/api/v1",
    },
  },
  app: {
    head: {
      title: "VirtualRadio",
      link: [
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap",
        },
      ],
    },
  },
  vite: {
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@use "${stylesDir}/_variables.scss" as *;\n@use "${stylesDir}/_mixins.scss" as *;\n`,
        },
      },
    },
  },
});
