import { defineStore } from "pinia";
import { brandApi } from "../api/brandApi";
import type { Brand, BrandInput } from "./types";

export const useBrandStore = defineStore("brand", {
  state: () => ({
    items: [] as Brand[],
    loading: false,
  }),

  getters: {
    byId: (state) => {
      const map = new Map<string, Brand>();
      for (const b of state.items) map.set(b.id, b);
      return map;
    },
  },

  actions: {
    async fetchAll() {
      this.loading = true;
      try {
        this.items = await brandApi.list();
      } finally {
        this.loading = false;
      }
    },
    async create(input: BrandInput): Promise<Brand> {
      const created = await brandApi.create(input);
      this.items.push(created);
      return created;
    },
    async update(id: string, input: BrandInput): Promise<Brand> {
      const updated = await brandApi.update(id, input);
      const idx = this.items.findIndex((b) => b.id === id);
      if (idx >= 0) this.items[idx] = updated;
      return updated;
    },
    async remove(id: string) {
      await brandApi.remove(id);
      this.items = this.items.filter((b) => b.id !== id);
    },
  },
});
