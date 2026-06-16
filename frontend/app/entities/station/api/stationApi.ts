import { useApi } from "~/shared/api";
import type { Station, StationInput, SuggestHint } from "../model/types";

export const stationApi = {
  list(): Promise<Station[]> {
    return useApi().get<Station[]>("/stations");
  },
  get(id: string): Promise<Station> {
    return useApi().get<Station>(`/stations/${id}`);
  },
  create(input: StationInput): Promise<Station> {
    return useApi().post<Station>("/stations", input);
  },
  update(id: string, input: StationInput): Promise<Station> {
    return useApi().put<Station>(`/stations/${id}`, input);
  },
  remove(id: string): Promise<void> {
    return useApi().del(`/stations/${id}`);
  },
  /** Non-persisted AI suggestion (backend reads context.name to force a name). */
  suggest(hint: SuggestHint = {}): Promise<StationInput> {
    return useApi().post<StationInput>("/stations/suggest", hint);
  },
};
