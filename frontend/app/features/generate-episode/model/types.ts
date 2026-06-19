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
  /** AI usage aggregates (cost auditing); populated when the job completes. */
  llm_calls: number;
  llm_tokens_in: number;
  llm_tokens_out: number;
  tts_calls: number;
  tts_cached: number;
  tts_tokens: number;
  created_at?: string;
  updated_at?: string;
  /** UI-only: the station name for display in the pipeline modal. */
  station_name?: string;
}

export type TraceKind = "llm" | "tts";

/** One audited AI call (LLM or TTS) made while generating an episode. */
export interface Trace {
  id: string;
  job_id: string;
  episode_id: string | null;
  kind: TraceKind;
  provider: string;
  model: string | null;
  tokens_in: number;
  tokens_out: number;
  total_tokens: number;
  cached: boolean;
  latency_ms: number;
  created_at?: string;
}
