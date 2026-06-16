import { onScopeDispose, ref } from "vue";
import { episodeApi, type Episode } from "~/entities/episode";

/**
 * Drives playback of a single episode through a real <audio> element.
 *
 * GET /episodes/{id}/audio is authenticated, so a plain <audio src> would 401.
 * We fetch the MP3 as a Blob (Bearer token applied by useApi), build an object
 * URL and feed it to an HTMLAudioElement. The URL is revoked and listeners are
 * removed on stop() / when a new episode loads / on scope dispose.
 */
export function usePlayEpisode() {
  const isPlaying = ref(false);
  const currentTime = ref(0);
  const duration = ref(0);
  const volume = ref(0.8);
  const loading = ref(false);
  const error = ref("");

  let audio: HTMLAudioElement | null = null;
  let objectUrl: string | null = null;
  let loadedId: string | null = null;

  function onTimeUpdate() {
    if (audio) currentTime.value = audio.currentTime;
  }
  function onLoadedMeta() {
    if (audio && Number.isFinite(audio.duration)) duration.value = audio.duration;
  }
  function onEnded() {
    isPlaying.value = false;
    currentTime.value = 0;
  }

  function teardown() {
    if (audio) {
      audio.pause();
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("loadedmetadata", onLoadedMeta);
      audio.removeEventListener("ended", onEnded);
      audio.src = "";
      audio = null;
    }
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
      objectUrl = null;
    }
    loadedId = null;
  }

  /** Fetch the authenticated audio blob and prepare the <audio> element. */
  async function load(episode: Episode) {
    if (loadedId === episode.id && audio) return;
    teardown();
    isPlaying.value = false;
    currentTime.value = 0;
    duration.value = episode.duration ?? 0;
    error.value = "";
    loading.value = true;
    try {
      const blob = await episodeApi.audioBlob(episode.id);
      objectUrl = URL.createObjectURL(blob);
      audio = new Audio(objectUrl);
      audio.volume = volume.value;
      audio.addEventListener("timeupdate", onTimeUpdate);
      audio.addEventListener("loadedmetadata", onLoadedMeta);
      audio.addEventListener("ended", onEnded);
      loadedId = episode.id;
    } catch {
      error.value = "No se pudo cargar el audio del episodio.";
      teardown();
    } finally {
      loading.value = false;
    }
  }

  async function toggle() {
    if (!audio) return;
    if (isPlaying.value) {
      audio.pause();
      isPlaying.value = false;
    } else {
      try {
        await audio.play();
        isPlaying.value = true;
      } catch {
        error.value = "No se pudo reproducir el audio.";
        isPlaying.value = false;
      }
    }
  }

  function seek(t: number) {
    currentTime.value = t;
    if (audio) audio.currentTime = t;
  }

  function setVolume(v: number) {
    volume.value = v;
    if (audio) audio.volume = v;
  }

  function stop() {
    teardown();
    isPlaying.value = false;
    currentTime.value = 0;
  }

  onScopeDispose(teardown);

  return {
    isPlaying,
    currentTime,
    duration,
    volume,
    loading,
    error,
    load,
    toggle,
    seek,
    setVolume,
    stop,
  };
}
