import { defineStore } from "pinia";
import { stationApi } from "../api/stationApi";
import type { Station, StationInput } from "./types";

export const useStationStore = defineStore("station", {
  state: () => ({
    items: [] as Station[],
    loading: false,
  }),

  actions: {
    async fetchAll() {
      this.loading = true;
      try {
        this.items = await stationApi.list();
      } finally {
        this.loading = false;
      }
    },
    async create(input: StationInput): Promise<Station> {
      const created = await stationApi.create(input);
      this.items.push(created);
      return created;
    },
    async update(id: string, input: StationInput): Promise<Station> {
      const updated = await stationApi.update(id, input);
      const idx = this.items.findIndex((s) => s.id === id);
      if (idx >= 0) this.items[idx] = updated;
      return updated;
    },
    async remove(id: string) {
      await stationApi.remove(id);
      this.items = this.items.filter((s) => s.id !== id);
    },
  },
});
