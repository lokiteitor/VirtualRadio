import { useApi } from "~/shared/api";
import type { Episode } from "../model/types";

export const episodeApi = {
  list(query: { station_id?: string } = {}): Promise<Episode[]> {
    return useApi().get<Episode[]>("/episodes", query);
  },
  get(id: string): Promise<Episode> {
    return useApi().get<Episode>(`/episodes/${id}`);
  },
  remove(id: string): Promise<void> {
    return useApi().del(`/episodes/${id}`);
  },
  /** Authenticated audio download (Bearer token required; returns a Blob). */
  audioBlob(id: string): Promise<Blob> {
    return useApi().getBlob(`/episodes/${id}/audio`);
  },
};
