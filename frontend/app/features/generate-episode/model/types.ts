export type JobStatus =
  | "queued"
  | "planning"
  | "synthesizing"
  | "mixing"
  | "completed"
  | "failed";

export interface Job {
  id: string;
  owner_id?: string;
  station_id: string;
  episode_id: string | null;
  status: JobStatus;
  progress: number;
  error: string | null;
  created_at?: string;
  updated_at?: string;
  /** UI-only: the station name for display in the pipeline modal. */
  station_name?: string;
}
