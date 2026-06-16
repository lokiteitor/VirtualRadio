<script setup lang="ts">
import { computed, watch } from "vue";
import { formatDate, formatDuration, getAvatarEmoji } from "~/shared/lib";
import { usePlayEpisode } from "~/features/play-episode";
import type { Episode } from "~/entities/episode";

const props = defineProps<{ episode: Episode; stationName?: string; autoplay?: boolean }>();

const {
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
} = usePlayEpisode();

const segments = computed(() => props.episode.script_json ?? []);
const totalDuration = computed(() => duration.value || props.episode.duration || 0);

watch(
  () => props.episode.id,
  async () => {
    stop();
    await load(props.episode);
    if (props.autoplay && !error.value) await toggle();
  },
  { immediate: true },
);

function onSeek(event: Event) {
  seek(Number((event.target as HTMLInputElement).value));
}
function onVolume(event: Event) {
  setVolume(Number((event.target as HTMLInputElement).value));
}
function avatarClass(voiceId: string | null): string {
  return voiceId ?? "";
}
</script>

<template>
  <div class="episode-viewer">
    <div class="viewer-header">
      <div v-if="stationName" class="station-pill">{{ stationName }}</div>
      <h3>{{ episode.title }}</h3>
      <p class="meta">
        Generado el {{ formatDate(episode.created_at) }} | Duración: {{ formatDuration(episode.duration) }}
      </p>
    </div>

    <!-- Custom Audio Player -->
    <div class="custom-player">
      <div class="player-controls">
        <button class="player-btn" :disabled="loading || !!error" @click="toggle">
          <template v-if="loading">⏳ Cargando...</template>
          <template v-else>{{ isPlaying ? "⏸️ Pausar" : "▶️ Reproducir" }}</template>
        </button>
        <div class="player-timeline">
          <span class="time-label">{{ formatDuration(currentTime) }}</span>
          <input
            type="range"
            min="0"
            :max="totalDuration || 100"
            step="0.1"
            :value="currentTime"
            class="player-slider"
            @input="onSeek"
          />
          <span class="time-label">{{ formatDuration(totalDuration) }}</span>
        </div>
        <div class="player-volume">
          🔊
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            :value="volume"
            class="volume-slider"
            @input="onVolume"
          />
        </div>
      </div>

      <!-- Animated Equalizer -->
      <div class="equalizer" :class="{ pulsing: isPlaying }">
        <span v-for="n in 15" :key="n" class="bar" />
      </div>

      <p v-if="error" class="alert alert-danger">{{ error }}</p>
    </div>

    <!-- Screenplay / Script Timeline -->
    <div class="script-timeline">
      <h4>📜 Guión Narrativo del Episodio</h4>
      <div class="script-scroller">
        <div v-for="(seg, idx) in segments" :key="idx" class="timeline-segment" :class="seg.type">
          <!-- Speech -->
          <template v-if="seg.type === 'speech'">
            <div class="speaker-avatar" :class="avatarClass(seg.voice_id)">
              {{ getAvatarEmoji(seg.speaker) }}
            </div>
            <div class="speech-bubble">
              <div class="bubble-header">
                <span class="speaker-name">{{ seg.speaker }}</span>
                <span class="segment-badge" :class="seg.effect === 'telephony' ? 'telephony' : 'normal'">
                  {{ seg.effect === "telephony" ? "📞 Llamada" : "🎙️ Mic" }}
                </span>
              </div>
              <p class="speech-text">"{{ seg.text }}"</p>
            </div>
          </template>

          <!-- Music -->
          <template v-else-if="seg.type === 'music'">
            <div class="music-card">
              <span class="note-icon">🎵</span>
              <div class="music-details">
                <span class="music-label">SONANDO AHORA:</span>
                <span class="music-title">{{ seg.text }}</span>
              </div>
              <span class="fx-badge">🎚️ DUCKING ACTIVO</span>
            </div>
          </template>

          <!-- FX -->
          <template v-else-if="seg.type === 'fx'">
            <div class="fx-segment">
              🎛️ EFECTO: <strong>{{ seg.effect || "FX" }}</strong> (Static/Sweeper)
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.episode-viewer {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 30px;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}
.viewer-header {
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 20px;
}
.station-pill {
  display: inline-block;
  background-color: var(--bg-card);
  color: var(--primary);
  font-weight: 700;
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  margin-bottom: 10px;
}
.viewer-header h3 {
  font-size: 24px;
  margin-bottom: 6px;
}
.viewer-header .meta {
  font-size: 13px;
  color: var(--text-muted);
}

/* Custom Audio Player */
.custom-player {
  background-color: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 20px;
  margin-bottom: 30px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.player-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.player-btn {
  background-color: var(--primary);
  color: black;
  border: none;
  font-weight: 700;
  padding: 10px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  transition: transform 0.2s ease;
  white-space: nowrap;
}
.player-btn:active {
  transform: scale(0.98);
}
.player-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.player-timeline {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 200px;
}
.time-label {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: var(--text-muted);
}
.player-slider {
  flex: 1;
  accent-color: var(--primary);
  height: 4px;
  border-radius: 2px;
  cursor: pointer;
}
.player-volume {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}
.volume-slider {
  width: 60px;
  accent-color: var(--primary);
  cursor: pointer;
}

/* Simulated Audio Equalizer */
.equalizer {
  display: flex;
  align-items: flex-end;
  height: 30px;
  gap: 3px;
  justify-content: center;
}
.equalizer .bar {
  width: 4px;
  background-color: var(--primary);
  height: 2px;
  transition: height 0.1s ease;
  border-radius: 2px;
}
.equalizer.pulsing .bar {
  animation: bounce 0.8s ease infinite alternate;
}
.equalizer.pulsing .bar:nth-child(2n) {
  animation-duration: 0.5s;
}
.equalizer.pulsing .bar:nth-child(3n) {
  animation-duration: 0.9s;
}
.equalizer.pulsing .bar:nth-child(4n) {
  animation-duration: 0.6s;
}
.equalizer.pulsing .bar:nth-child(5n) {
  animation-duration: 1.1s;
}
@keyframes bounce {
  0% {
    height: 2px;
  }
  100% {
    height: 28px;
  }
}

/* Screenplay Timeline */
.script-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  overflow: hidden;
}
.script-timeline h4 {
  font-size: 16px;
  font-weight: 700;
}
.script-scroller {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 8px;
}
.timeline-segment {
  display: flex;
  gap: 16px;
}
.speaker-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}
.speaker-avatar.host {
  border-color: var(--primary);
}
.speaker-avatar.caller {
  border-color: var(--secondary);
}
.speaker-avatar.reporter {
  border-color: var(--success);
}
.speaker-avatar.commercial {
  border-color: #8be4fc;
}
.speech-bubble {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 0 var(--radius-md) var(--radius-md) var(--radius-md);
  padding: 16px;
  flex: 1;
  min-width: 0;
}
.bubble-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 8px;
}
.speaker-name {
  font-weight: 700;
  font-size: 13px;
}
.segment-badge {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
}
.segment-badge.telephony {
  background-color: rgba(139, 92, 246, 0.15);
  color: var(--secondary);
  border: 1px solid rgba(139, 92, 246, 0.3);
}
.segment-badge.normal {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
}
.speech-text {
  font-size: 14px;
  line-height: 1.5;
  color: #e5e7eb;
}

/* Music Segment Card */
.music-card {
  display: flex;
  align-items: center;
  background: linear-gradient(90deg, #1b263e, #131b2e);
  border: 1px dashed rgba(245, 158, 11, 0.4);
  border-radius: var(--radius-md);
  padding: 16px;
  width: 100%;
  gap: 16px;
}
.note-icon {
  font-size: 24px;
  background: rgba(245, 158, 11, 0.1);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.music-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.music-label {
  font-size: 9px;
  color: var(--primary);
  font-weight: 700;
}
.music-title {
  font-weight: 600;
  font-size: 14px;
}
.fx-badge {
  font-size: 9px;
  font-weight: 800;
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--primary);
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

/* FX Segment */
.fx-segment {
  background-color: rgba(255, 255, 255, 0.02);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
  text-align: center;
  padding: 12px;
  width: 100%;
  font-size: 12px;
  color: var(--text-muted);
}
</style>
