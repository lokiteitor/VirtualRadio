export interface MusicTrack {
  id: string;
  owner_id: string;
  file_path: string;
  title: string | null;
  artist: string | null;
  album: string | null;
  duration: number | null;
  file_hash: string;
  created_at: string;
  updated_at: string;
}

/** Result of POST /music/scan reconciling the DB with the music folder. */
export interface MusicScanResult {
  added: number;
  removed: number;
  total: number;
}
