/** Format an ISO date-time as a short localized string. */
export function formatDate(dateStr?: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "short",
  });
}

/** Format seconds as m:ss. */
export function formatDuration(secs?: number | null): string {
  if (!secs || secs < 0) return "0:00";
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s < 10 ? "0" : ""}${s}`;
}

/** Pick an avatar emoji for a speaker/character name. */
export function getAvatarEmoji(speaker?: string | null): string {
  if (!speaker) return "🎙️";
  if (speaker.includes("Clem") || speaker.includes("Host")) return "👨‍🌾";
  if (speaker.includes("Dan") || speaker.includes("Rig") || speaker.includes("Bob")) return "🚛";
  if (speaker.includes("Audrey") || speaker.includes("Reporter")) return "👩‍💼";
  if (speaker.includes("Dick") || speaker.includes("Brainwave")) return "👽";
  if (speaker.includes("Silas")) return "👴";
  if (speaker.includes("Juan")) return "🧑‍🌾";
  if (speaker.includes("Cynthia")) return "💁‍♀️";
  if (speaker.includes("Commercial")) return "📢";
  return "🎙️";
}

/** Split a textarea value into a trimmed, non-empty list of lines. */
export function linesToArray(raw?: string | null): string[] {
  if (!raw) return [];
  return raw
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

/** Join a list of lines back into a textarea value. */
export function arrayToLines(items?: string[] | null): string {
  return (items ?? []).join("\n");
}
