export type SegmentType = "speech" | "music" | "fx";

export interface ScriptSegment {
  type: SegmentType;
  speaker: string | null;
  text: string | null;
  voice_id: string | null;
  effect: string | null;
  track_id: number | null;
  duration_seconds: number | null;
}

export interface Episode {
  id: string;
  owner_id: string;
  station_id: string;
  title: string;
  duration: number;
  script_json: ScriptSegment[];
  audio_path: string | null;
  created_at: string;
  updated_at: string;
}
