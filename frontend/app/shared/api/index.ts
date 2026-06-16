// Public API of the shared HTTP layer. All slices call useApi() — never $fetch
// directly — so JWT injection, the {data}/{error} contract and 401 handling stay
// centralized (see app/plugins/api.ts).
import type { Envelope } from "./types";

export { ApiError, toApiError } from "./types";
export type { Envelope, Meta, ApiErrorBody } from "./types";

type Query = Record<string, string | number | boolean | undefined | null>;

export function useApi() {
  const { $api } = useNuxtApp();

  return {
    /** GET returning the unwrapped data. */
    async get<T>(url: string, query?: Query): Promise<T> {
      const res = await $api<Envelope<T>>(url, { query });
      return res.data;
    },
    /** GET returning the full envelope (when meta is needed, e.g. total_duration). */
    async getWithMeta<T>(url: string, query?: Query): Promise<Envelope<T>> {
      return await $api<Envelope<T>>(url, { query });
    },
    async post<T>(url: string, body?: unknown): Promise<T> {
      const res = await $api<Envelope<T>>(url, { method: "POST", body: body as Record<string, unknown> });
      return res.data;
    },
    async put<T>(url: string, body?: unknown): Promise<T> {
      const res = await $api<Envelope<T>>(url, { method: "PUT", body: body as Record<string, unknown> });
      return res.data;
    },
    async del(url: string): Promise<void> {
      await $api(url, { method: "DELETE" });
    },
    /** POST multipart/form-data (file uploads). */
    async postForm<T>(url: string, form: FormData): Promise<T> {
      const res = await $api<Envelope<T>>(url, { method: "POST", body: form });
      return res.data;
    },
    /** Fetch binary content (e.g. authenticated episode audio) as a Blob. */
    async getBlob(url: string): Promise<Blob> {
      return await $api<Blob>(url, { responseType: "blob" });
    },
    /** Escape hatch: the raw ofetch instance (baseURL + auth applied). */
    raw: $api,
  };
}
