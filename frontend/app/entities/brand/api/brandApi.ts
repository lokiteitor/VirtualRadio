import { useApi } from "~/shared/api";
import type { Brand, BrandInput, SuggestHint } from "../model/types";

export const brandApi = {
  list(): Promise<Brand[]> {
    return useApi().get<Brand[]>("/brands");
  },
  get(id: string): Promise<Brand> {
    return useApi().get<Brand>(`/brands/${id}`);
  },
  create(input: BrandInput): Promise<Brand> {
    return useApi().post<Brand>("/brands", input);
  },
  update(id: string, input: BrandInput): Promise<Brand> {
    return useApi().put<Brand>(`/brands/${id}`, input);
  },
  remove(id: string): Promise<void> {
    return useApi().del(`/brands/${id}`);
  },
  /** Non-persisted AI suggestion (backend reads context.name to force a name). */
  suggest(hint: SuggestHint = {}): Promise<Brand> {
    return useApi().post<Brand>("/brands/suggest", hint);
  },
};
