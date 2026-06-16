import { defineStore } from "pinia";
import { musicApi } from "../api/musicApi";
import type { MusicTrack, MusicScanResult } from "./types";

export const useMusicStore = defineStore("music-track", {
  state: () => ({
    items: [] as MusicTrack[],
    totalDuration: 0,
    count: 0,
    loading: false,
  }),

  actions: {
    async fetchAll() {
      this.loading = true;
      try {
        const { data, meta } = await musicApi.listWithMeta();
        this.items = data;
        this.count = Number(meta.count ?? data.length);
        this.totalDuration = Number(meta.total_duration ?? 0);
      } finally {
        this.loading = false;
      }
    },
    async upload(file: File): Promise<MusicTrack> {
      const created = await musicApi.upload(file);
      await this.fetchAll();
      return created;
    },
    async scan(): Promise<MusicScanResult> {
      const result = await musicApi.scan();
      await this.fetchAll();
      return result;
    },
    async remove(id: string) {
      await musicApi.remove(id);
      await this.fetchAll();
    },
  },
});
