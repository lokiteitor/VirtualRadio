import { useApi } from "~/shared/api";
import type { Envelope } from "~/shared/api";
import type { MusicTrack, MusicScanResult } from "../model/types";

export const musicApi = {
  /** GET /music returning the full envelope (meta has count + total_duration). */
  listWithMeta(): Promise<Envelope<MusicTrack[]>> {
    return useApi().getWithMeta<MusicTrack[]>("/music");
  },
  /** POST /music/upload as multipart with the "file" field. */
  upload(file: File): Promise<MusicTrack> {
    const form = new FormData();
    form.append("file", file);
    return useApi().postForm<MusicTrack>("/music/upload", form);
  },
  /** POST /music/scan to reconcile the library with disk. */
  scan(): Promise<MusicScanResult> {
    return useApi().post<MusicScanResult>("/music/scan");
  },
  remove(id: string): Promise<void> {
    return useApi().del(`/music/${id}`);
  },
};
