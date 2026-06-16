import { defineStore } from "pinia";
import type { Envelope } from "~/shared/api";
import { sessionApi } from "../api/sessionApi";
import type { AuthTokens, Credentials, RegisterPayload, User } from "./types";

const ACCESS_KEY = "vr_access_token";
const REFRESH_KEY = "vr_refresh_token";
const USER_KEY = "vr_user";

interface SessionState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
}

export const useSessionStore = defineStore("session", {
  state: (): SessionState => ({
    accessToken: null,
    refreshToken: null,
    user: null,
  }),

  getters: {
    isAuthenticated: (state): boolean => !!state.accessToken,
    displayName: (state): string => state.user?.display_name || state.user?.email || "Usuario",
  },

  actions: {
    _apply(tokens: AuthTokens) {
      this.accessToken = tokens.access_token;
      this.refreshToken = tokens.refresh_token;
      this.user = tokens.user;
      this._persist();
    },

    _persist() {
      if (!import.meta.client) return;
      if (this.accessToken) localStorage.setItem(ACCESS_KEY, this.accessToken);
      if (this.refreshToken) localStorage.setItem(REFRESH_KEY, this.refreshToken);
      if (this.user) localStorage.setItem(USER_KEY, JSON.stringify(this.user));
    },

    restore() {
      if (!import.meta.client) return;
      this.accessToken = localStorage.getItem(ACCESS_KEY);
      this.refreshToken = localStorage.getItem(REFRESH_KEY);
      const rawUser = localStorage.getItem(USER_KEY);
      this.user = rawUser ? (JSON.parse(rawUser) as User) : null;
    },

    clear() {
      this.accessToken = null;
      this.refreshToken = null;
      this.user = null;
      if (import.meta.client) {
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
        localStorage.removeItem(USER_KEY);
      }
    },

    async login(creds: Credentials) {
      this._apply(await sessionApi.login(creds));
    },

    async register(payload: RegisterPayload) {
      this._apply(await sessionApi.register(payload));
    },

    async logout() {
      this.clear();
      await navigateTo("/login");
    },

    /** Renew the access token using the refresh token (refresh token in header). */
    async refresh(): Promise<boolean> {
      if (!this.refreshToken) return false;
      try {
        const config = useRuntimeConfig();
        const res = await $fetch<Envelope<{ access_token: string }>>("/auth/refresh", {
          baseURL: config.public.apiBase as string,
          method: "POST",
          headers: { Authorization: `Bearer ${this.refreshToken}` },
        });
        this.accessToken = res.data.access_token;
        this._persist();
        return true;
      } catch {
        this.clear();
        return false;
      }
    },
  },
});
