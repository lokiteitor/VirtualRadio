export interface Character {
  id: string;
  owner_id: string;
  name: string;
  role: string | null;
  description: string | null;
  personality: string | null;
  station_affinity: string | null;
  voice: string | null;
  first_appearance: string;
  last_appearance: string;
  created_at: string;
  updated_at: string;
}

export interface CharacterInput {
  name: string;
  role?: string | null;
  description?: string | null;
  personality?: string | null;
  station_affinity?: string | null;
  voice?: string | null;
}

export interface CharacterMemory {
  id: string;
  owner_id: string;
  character_id: string;
  episode_id: string | null;
  memory: string;
  importance: number;
  created_at: string;
  updated_at: string;
}

/** Optional hint for the LLM /suggest endpoints ({ prompt, context }). */
export interface SuggestHint {
  prompt?: string;
  context?: Record<string, unknown>;
}
