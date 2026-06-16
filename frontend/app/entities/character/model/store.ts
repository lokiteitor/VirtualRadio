import { defineStore } from "pinia";
import { characterApi } from "../api/characterApi";
import type { Character, CharacterInput } from "./types";

export const useCharacterStore = defineStore("character", {
  state: () => ({
    items: [] as Character[],
    loading: false,
  }),

  actions: {
    async fetchAll() {
      this.loading = true;
      try {
        this.items = await characterApi.list();
      } finally {
        this.loading = false;
      }
    },
    async create(input: CharacterInput): Promise<Character> {
      const created = await characterApi.create(input);
      this.items.push(created);
      return created;
    },
    async update(id: string, input: CharacterInput): Promise<Character> {
      const updated = await characterApi.update(id, input);
      const idx = this.items.findIndex((c) => c.id === id);
      if (idx >= 0) this.items[idx] = updated;
      return updated;
    },
    async remove(id: string) {
      await characterApi.remove(id);
      this.items = this.items.filter((c) => c.id !== id);
    },
  },
});
