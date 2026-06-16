import { onScopeDispose, ref } from "vue";
import { toApiError, useApi } from "~/shared/api";
import type { Job } from "./types";

const POLL_MS = 1000;

/** Triggers episode generation and polls the job until it finishes. */
export function useGenerateEpisode() {
  const api = useApi();
  const job = ref<Job | null>(null);
  const isOpen = ref(false);
  const error = ref("");
  let timer: ReturnType<typeof setInterval> | null = null;

  function stopPolling() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  function poll() {
    stopPolling();
    timer = setInterval(async () => {
      if (!job.value) return;
      try {
        const data = await api.get<Job>(`/jobs/${job.value.id}`);
        job.value = { ...data, station_name: job.value.station_name };
        if (data.status === "completed" || data.status === "failed") stopPolling();
      } catch {
        // transient error — keep polling
      }
    }, POLL_MS);
  }

  async function start(stationId: string, stationName: string) {
    error.value = "";
    try {
      const created = await api.post<Job>("/episodes/generate", { station_id: stationId });
      job.value = { ...created, station_name: stationName };
      isOpen.value = true;
      poll();
    } catch (e) {
      error.value = toApiError(e).message;
      throw e;
    }
  }

  function close() {
    isOpen.value = false;
    job.value = null;
    stopPolling();
  }

  onScopeDispose(stopPolling);

  return { job, isOpen, error, start, close };
}
