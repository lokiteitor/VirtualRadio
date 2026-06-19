import { ref } from "vue";
import { episodeApi, type Episode } from "~/entities/episode";

/**
 * Downloads the MP3 of an episode.
 *
 * GET /episodes/{id}/audio is authenticated, so a plain <a download href> would
 * 401. We fetch the MP3 as a Blob (Bearer token applied by useApi), build an
 * object URL, click a temporary <a> and revoke the URL right after.
 */
export function useDownloadEpisode() {
  const downloadingId = ref<string | null>(null);
  const error = ref("");

  function fileName(episode: Episode): string {
    const slug = (episode.title || "episodio")
      .normalize("NFKD")
      .replace(/[^\w\s-]/g, "")
      .trim()
      .replace(/\s+/g, "-")
      .slice(0, 60);
    return `Ep${episode.episode_number}_${slug || "episodio"}.mp3`;
  }

  async function download(episode: Episode, name?: string) {
    if (downloadingId.value) return;
    error.value = "";
    downloadingId.value = episode.id;
    let url: string | null = null;
    try {
      const blob = await episodeApi.audioBlob(episode.id);
      url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name ?? fileName(episode);
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch {
      error.value = "No se pudo descargar el audio del episodio.";
    } finally {
      if (url) URL.revokeObjectURL(url);
      downloadingId.value = null;
    }
  }

  return { downloadingId, error, download };
}
