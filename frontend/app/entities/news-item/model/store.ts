import { defineStore } from "pinia";
import { newsApi, type NewsListQuery } from "../api/newsApi";
import type { NewsItem, NewsItemInput } from "./types";

export const useNewsStore = defineStore("news", {
  state: () => ({
    items: [] as NewsItem[],
    loading: false,
  }),

  actions: {
    async fetchAll(filters: NewsListQuery = {}) {
      this.loading = true;
      try {
        this.items = await newsApi.list(filters);
      } finally {
        this.loading = false;
      }
    },
    async create(input: NewsItemInput): Promise<NewsItem> {
      const created = await newsApi.create(input);
      this.items.unshift(created);
      return created;
    },
    async update(id: string, input: NewsItemInput): Promise<NewsItem> {
      const updated = await newsApi.update(id, input);
      const idx = this.items.findIndex((n) => n.id === id);
      if (idx >= 0) this.items[idx] = updated;
      return updated;
    },
    async remove(id: string) {
      await newsApi.remove(id);
      this.items = this.items.filter((n) => n.id !== id);
    },
  },
});
