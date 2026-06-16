import { defineStore } from "pinia";
import { commercialApi } from "../api/commercialApi";
import type { Commercial, CommercialInput } from "./types";

export const useCommercialStore = defineStore("commercial", {
  state: () => ({
    items: [] as Commercial[],
    loading: false,
  }),

  actions: {
    async fetchAll(query?: { brand_id?: string }) {
      this.loading = true;
      try {
        this.items = await commercialApi.list(query);
      } finally {
        this.loading = false;
      }
    },
    async create(input: CommercialInput): Promise<Commercial> {
      const created = await commercialApi.create(input);
      this.items.unshift(created);
      return created;
    },
    async update(id: string, input: CommercialInput): Promise<Commercial> {
      const updated = await commercialApi.update(id, input);
      const idx = this.items.findIndex((c) => c.id === id);
      if (idx >= 0) this.items[idx] = updated;
      return updated;
    },
    async remove(id: string) {
      await commercialApi.remove(id);
      this.items = this.items.filter((c) => c.id !== id);
    },
  },
});
