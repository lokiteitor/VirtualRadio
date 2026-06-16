export interface Commercial {
  id: string;
  owner_id: string;
  brand_id: string;
  title: string;
  script: string;
  duration: number;
  campaign: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CommercialInput {
  brand_id: string;
  title: string;
  script: string;
  duration?: number;
  campaign?: string | null;
  is_active?: boolean;
}

/** Shape returned by /commercials/suggest (title/campaign/script only). */
export interface CommercialSuggestion {
  title: string | null;
  campaign: string | null;
  script: string | null;
}

/** Optional hint for the LLM /suggest endpoints ({ prompt, context }). */
export interface SuggestHint {
  prompt?: string;
  context?: Record<string, unknown>;
}
