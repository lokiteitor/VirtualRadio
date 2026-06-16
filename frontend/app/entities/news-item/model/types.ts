export interface NewsItem {
  id: string;
  owner_id: string;
  headline: string;
  summary: string | null;
  full_script: string | null;
  category: string;
  tone: string;
  is_active: boolean;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface NewsItemInput {
  headline: string;
  summary?: string | null;
  full_script?: string | null;
  category: string;
  tone: string;
  is_active?: boolean;
  expires_at?: string | null;
}

/** Optional hint for the LLM /suggest endpoints ({ prompt, context }). */
export interface SuggestHint {
  prompt?: string;
  context?: Record<string, unknown>;
}
