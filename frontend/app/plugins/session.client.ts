// Restore the persisted session from localStorage before route guards run.
import { useSessionStore } from "~/entities/session";

export default defineNuxtPlugin(() => {
  useSessionStore().restore();
});
