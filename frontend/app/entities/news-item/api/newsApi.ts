import { useApi } from "~/shared/api";
import type { NewsItem, NewsItemInput, SuggestHint } from "../model/types";

/** Query filters accepted by GET /news (is_active & category). */
export interface NewsListQuery {
  [key: string]: string | number | boolean | undefined | null;
  is_active?: boolean;
  category?: string;
}

export const newsApi = {
  list(query: NewsListQuery = {}): Promise<NewsItem[]> {
    return useApi().get<NewsItem[]>("/news", query);
  },
  get(id: string): Promise<NewsItem> {
    return useApi().get<NewsItem>(`/news/${id}`);
  },
  create(input: NewsItemInput): Promise<NewsItem> {
    return useApi().post<NewsItem>("/news", input);
  },
  update(id: string, input: NewsItemInput): Promise<NewsItem> {
    return useApi().put<NewsItem>(`/news/${id}`, input);
  },
  remove(id: string): Promise<void> {
    return useApi().del(`/news/${id}`);
  },
  /** Non-persisted AI suggestion (backend reads context.category & context.tone). */
  suggest(hint: SuggestHint = {}): Promise<NewsItem> {
    return useApi().post<NewsItem>("/news/suggest", hint);
  },
};
