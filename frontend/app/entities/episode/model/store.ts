import { defineStore } from "pinia";
import { episodeApi } from "../api/episodeApi";
import type { Episode } from "./types";

export const useEpisodeStore = defineStore("episode", {
  state: () => ({
    items: [] as Episode[],
    loading: false,
  }),

  actions: {
    async fetchAll(query: { station_id?: string } = {}) {
      this.loading = true;
      try {
        this.items = await episodeApi.list(query);
      } finally {
        this.loading = false;
      }
    },
    async remove(id: string) {
      await episodeApi.remove(id);
      this.items = this.items.filter((e) => e.id !== id);
    },
  },
});
