import { useApi } from "~/shared/api";
import type {
  Commercial,
  CommercialInput,
  CommercialSuggestion,
  SuggestHint,
} from "../model/types";

export const commercialApi = {
  list(query?: { brand_id?: string }): Promise<Commercial[]> {
    return useApi().get<Commercial[]>("/commercials", query);
  },
  get(id: string): Promise<Commercial> {
    return useApi().get<Commercial>(`/commercials/${id}`);
  },
  create(input: CommercialInput): Promise<Commercial> {
    return useApi().post<Commercial>("/commercials", input);
  },
  update(id: string, input: CommercialInput): Promise<Commercial> {
    return useApi().put<Commercial>(`/commercials/${id}`, input);
  },
  remove(id: string): Promise<void> {
    return useApi().del(`/commercials/${id}`);
  },
  /**
   * Non-persisted AI suggestion. The backend requires an owned brand
   * (read from context.brand_id) and returns { title, campaign, script }.
   */
  suggest(hint: SuggestHint = {}): Promise<CommercialSuggestion> {
    return useApi().post<CommercialSuggestion>("/commercials/suggest", hint);
  },
};
