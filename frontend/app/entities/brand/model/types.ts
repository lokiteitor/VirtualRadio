export interface Brand {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  industry: string | null;
  slogan: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BrandInput {
  name: string;
  description?: string | null;
  industry?: string | null;
  slogan?: string | null;
  is_active?: boolean;
}

/** Optional hint for the LLM /suggest endpoints ({ prompt, context }). */
export interface SuggestHint {
  prompt?: string;
  context?: Record<string, unknown>;
}
