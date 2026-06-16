<script setup lang="ts">
import { computed } from "vue";
import { AppModal } from "~/shared/ui";
import { JOB_STATUS_PROGRESS, JOB_STATUS_STEP } from "~/shared/config";
import type { Job } from "~/features/generate-episode";

const props = defineProps<{ job: Job }>();
const emit = defineEmits<{ close: []; viewEpisode: [episodeId: string] }>();

const stepIndex = computed(() => JOB_STATUS_STEP[props.job.status] ?? -1);
const progress = computed(() => JOB_STATUS_PROGRESS[props.job.status] ?? 0);
const isDone = computed(() => props.job.status === "completed" || props.job.status === "failed");
const isFailed = computed(() => props.job.status === "failed");

const STEPS = [
  { title: "Agente Planificador (Planner)", desc: "Analiza el lore, selecciona canciones y consulta personajes." },
  { title: "Escritores Temáticos (Host, News, Commercial, Callers)", desc: "Redactan los guiones con su voz y tono característico." },
  { title: "Sintetizador de Voces (TTS)", desc: "Genera las narraciones con la voz asignada a cada rol." },
  { title: "Mezclador de Audio FX", desc: "Aplica telefonía, sweepers y ducking; exporta el MP3 final." },
];
</script>

<template>
  <AppModal :title="'⚡ Pipeline de Generación por Agentes'" :closable="isDone" @close="emit('close')">
    <template #header-extra>
      <span class="station-target">{{ job.station_name || job.station_id }}</span>
    </template>

    <p class="pipeline-desc">Los agentes están planificando, escribiendo y mezclando el nuevo programa...</p>

    <div class="pipeline-progress-bar">
      <div class="progress-fill" :style="{ width: progress + '%' }" />
    </div>

    <div class="pipeline-steps">
      <div
        v-for="(step, i) in STEPS"
        :key="i"
        class="step-line"
        :class="{ active: stepIndex >= i, completed: stepIndex > i || job.status === 'completed' }"
      >
        <span class="step-bullet">{{ i + 1 }}</span>
        <div class="step-info">
          <h5>{{ step.title }}</h5>
          <p>{{ step.desc }}</p>
        </div>
      </div>
    </div>

    <div class="pipeline-console">
      <div class="console-header">LOGS DE EJECUCIÓN</div>
      <div class="console-body">
        <div class="console-line text-blue">&gt; Inicializando agentes...</div>
        <div v-if="stepIndex >= 0" class="console-line text-green">&gt; [PlannerAgent] Planificando estructura</div>
        <div v-if="stepIndex >= 2" class="console-line text-green">&gt; [VoiceSynthesisAgent] Compilando voces (TTS)</div>
        <div v-if="stepIndex >= 3" class="console-line text-green">&gt; [AudioMixerAgent] Ducking y mezcla final</div>
        <div class="console-line text-yellow">&gt; Estado: {{ job.status }} ({{ job.progress }}%)</div>
        <div v-if="isFailed" class="console-line text-red">&gt; ERROR: {{ job.error }}</div>
      </div>
    </div>

    <template #footer>
      <button
        v-if="job.status === 'completed' && job.episode_id"
        class="btn btn-primary"
        @click="emit('viewEpisode', job.episode_id)"
      >
        🎧 Ver episodio
      </button>
      <button class="btn btn-secondary" :disabled="!isDone" @click="emit('close')">
        {{ isDone ? "Cerrar" : "Procesando..." }}
      </button>
    </template>
  </AppModal>
</template>

<style scoped lang="scss">
.station-target {
  font-size: 11px;
  font-weight: 700;
  background-color: var(--primary-glow);
  color: var(--primary);
  padding: 2px 8px;
  border-radius: 4px;
}
.pipeline-desc {
  font-size: 13px;
  color: var(--text-muted);
}
.pipeline-progress-bar {
  height: 8px;
  background-color: var(--bg-deep);
  border-radius: 4px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  transition: width 0.3s ease;
}
.pipeline-steps {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.step-line {
  display: flex;
  gap: 16px;
  opacity: 0.3;
  transition: opacity 0.3s ease;
}
.step-line.active {
  opacity: 1;
}
.step-line.completed {
  opacity: 0.8;
}
.step-bullet {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}
.step-line.active .step-bullet {
  border-color: var(--primary);
  background-color: var(--primary-glow);
  color: var(--primary);
}
.step-line.completed .step-bullet {
  border-color: var(--success);
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--success);
}
.step-info h5 {
  font-size: 13px;
  font-weight: 700;
}
.step-info p {
  font-size: 11px;
  color: var(--text-muted);
}
.pipeline-console {
  background-color: #05070c;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}
.console-header {
  padding: 6px 12px;
  font-size: 9px;
  font-weight: 700;
  color: #4b5563;
  background-color: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--border-color);
  letter-spacing: 0.5px;
}
.console-body {
  padding: 12px;
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 120px;
  overflow-y: auto;
}
.text-blue {
  color: #60a5fa;
}
.text-green {
  color: #34d399;
}
.text-yellow {
  color: #fbbf24;
}
.text-red {
  color: #f87171;
}
</style>
