export interface EpisodeSettings {
  id: string;
  owner_id: string;
  station_id: string;
  song_count: number;
  news_count: number;
  commercial_count: number;
  caller_count: number;
  memories_per_caller: number;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface EpisodeSettingsInput {
  song_count?: number;
  news_count?: number;
  commercial_count?: number;
  caller_count?: number;
  memories_per_caller?: number;
  language?: string;
}
