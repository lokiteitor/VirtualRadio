<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { AppModal } from "~/shared/ui";
import { useApi } from "~/shared/api";
import { JOB_STATUS_PROGRESS, JOB_STATUS_STEP } from "~/shared/config";
import type { Job, Trace } from "~/features/generate-episode";

const props = defineProps<{ job: Job }>();
const emit = defineEmits<{ close: []; viewEpisode: [episodeId: string] }>();

const stepIndex = computed(() => JOB_STATUS_STEP[props.job.status] ?? -1);
const progress = computed(() => JOB_STATUS_PROGRESS[props.job.status] ?? 0);
const isDone = computed(() => props.job.status === "completed" || props.job.status === "failed");
const isFailed = computed(() => props.job.status === "failed");

// AI usage auditing — aggregates come on the job; per-call detail is fetched once
// the job completes (the worker persists traces only at the end).
const api = useApi();
const traces = ref<Trace[]>([]);
const tracesLoaded = ref(false);
const ttsSynthesized = computed(() => props.job.tts_calls - props.job.tts_cached);

watch(
  () => props.job.status,
  async (status) => {
    if (status !== "completed" || tracesLoaded.value) return;
    tracesLoaded.value = true;
    try {
      traces.value = await api.get<Trace[]>(`/jobs/${props.job.id}/traces`);
    } catch {
      // best-effort: the audit detail is non-critical
    }
  },
  { immediate: true },
);

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

    <section v-if="job.status === 'completed'" class="audit">
      <div class="audit-header">🧾 Auditoría de costos (uso de IA)</div>
      <div class="audit-metrics">
        <div class="metric">
          <span class="metric-label">Llamadas LLM</span>
          <span class="metric-value">{{ job.llm_calls }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">Tokens LLM (in / out)</span>
          <span class="metric-value">{{ job.llm_tokens_in }} / {{ job.llm_tokens_out }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">Voces TTS sintetizadas</span>
          <span class="metric-value">{{ ttsSynthesized }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">TTS desde caché (sin costo)</span>
          <span class="metric-value">{{ job.tts_cached }} / {{ job.tts_calls }}</span>
        </div>
      </div>

      <details v-if="traces.length" class="audit-detail">
        <summary>Detalle por llamada ({{ traces.length }})</summary>
        <div class="audit-table-wrap">
          <table class="audit-table">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Proveedor</th>
                <th>Modelo</th>
                <th class="num">Tok. in</th>
                <th class="num">Tok. out</th>
                <th class="num">ms</th>
                <th>Caché</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in traces" :key="t.id">
                <td>{{ t.kind.toUpperCase() }}</td>
                <td>{{ t.provider }}</td>
                <td class="model">{{ t.model || "—" }}</td>
                <td class="num">{{ t.tokens_in }}</td>
                <td class="num">{{ t.tokens_out }}</td>
                <td class="num">{{ t.latency_ms }}</td>
                <td>{{ t.cached ? "✓" : "" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>
    </section>

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
.audit {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.audit-header {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.3px;
}
.audit-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}
.metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background-color: var(--bg-deep);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
}
.metric-label {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.metric-value {
  font-size: 16px;
  font-weight: 700;
  font-family: "JetBrains Mono", monospace;
}
.audit-detail summary {
  cursor: pointer;
  font-size: 11px;
  color: var(--text-muted);
}
.audit-table-wrap {
  margin-top: 8px;
  max-height: 180px;
  overflow-y: auto;
}
.audit-table {
  width: 100%;
  border-collapse: collapse;
  font-family: "JetBrains Mono", monospace;
  font-size: 10px;
}
.audit-table th,
.audit-table td {
  padding: 4px 6px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}
.audit-table th {
  color: var(--text-muted);
  font-weight: 700;
}
.audit-table .num {
  text-align: right;
}
.audit-table .model {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
