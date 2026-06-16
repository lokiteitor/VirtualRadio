import { useApi } from "~/shared/api";
import type {
  Character,
  CharacterInput,
  CharacterMemory,
  SuggestHint,
} from "../model/types";

export const characterApi = {
  list(): Promise<Character[]> {
    return useApi().get<Character[]>("/characters");
  },
  get(id: string): Promise<Character> {
    return useApi().get<Character>(`/characters/${id}`);
  },
  create(input: CharacterInput): Promise<Character> {
    return useApi().post<Character>("/characters", input);
  },
  update(id: string, input: CharacterInput): Promise<Character> {
    return useApi().put<Character>(`/characters/${id}`, input);
  },
  remove(id: string): Promise<void> {
    return useApi().del(`/characters/${id}`);
  },
  /** Narrative memories for a character, newest first. */
  memories(id: string): Promise<CharacterMemory[]> {
    return useApi().get<CharacterMemory[]>(`/characters/${id}/memories`);
  },
  /** Non-persisted AI suggestion (backend reads context.name to force a name). */
  suggest(hint: SuggestHint = {}): Promise<CharacterInput> {
    return useApi().post<CharacterInput>("/characters/suggest", hint);
  },
};
