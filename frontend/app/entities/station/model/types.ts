export interface Station {
  id: string;
  owner_id: string;
  name: string;
  host_name: string | null;
  description: string | null;
  personality: string | null;
  frequency: string | null;
  emoji: string | null;
  color: string | null;
  intro_templates: string[];
  outro_templates: string[];
  created_at: string;
  updated_at: string;
}

export interface StationInput {
  name: string;
  host_name?: string | null;
  description?: string | null;
  personality?: string | null;
  frequency?: string | null;
  emoji?: string | null;
  color?: string | null;
  intro_templates?: string[];
  outro_templates?: string[];
}

/** Optional hint for the LLM /suggest endpoints ({ prompt, context }). */
export interface SuggestHint {
  prompt?: string;
  context?: Record<string, unknown>;
}
