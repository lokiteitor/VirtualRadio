import { useApi } from "~/shared/api";
import type { EpisodeSettings, EpisodeSettingsInput } from "../model/types";

/** Per-station episode script settings (1:1 sub-resource of a station). */
export const episodeSettingsApi = {
  get(stationId: string): Promise<EpisodeSettings> {
    return useApi().get<EpisodeSettings>(`/stations/${stationId}/episode-settings`);
  },
  update(stationId: string, input: EpisodeSettingsInput): Promise<EpisodeSettings> {
    return useApi().put<EpisodeSettings>(`/stations/${stationId}/episode-settings`, input);
  },
};
