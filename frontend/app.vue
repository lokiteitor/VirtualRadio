<template>
  <div class="app-container">
    <!-- Meta Google Font Import -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

    <!-- Sidebar Navigation -->
    <aside class="sidebar">
      <div class="brand">
        <div class="logo-icon">
          <span class="pulse-ring"></span>
          📻
        </div>
        <div class="brand-text">
          <h1>VirtualRadio</h1>
          <span class="badge badge-glow">MVP PROTOTYPE</span>
        </div>
      </div>

      <nav class="nav-menu">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          class="nav-item"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          <span class="nav-icon">{{ tab.icon }}</span>
          <span class="nav-label">{{ tab.name }}</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <div class="server-status">
          <span class="status-indicator" :class="{ online: backendConnected }"></span>
          <span>API: {{ backendConnected ? 'CONECTADO' : 'DESCONECTADO' }}</span>
        </div>
        <p class="copyright">VirtualRadio v1.0 &copy; 2026</p>
      </div>
    </aside>

    <!-- Main Workspace -->
    <main class="main-content">
      <!-- Top header bar -->
      <header class="content-header">
        <div class="page-title">
          <h2>{{ currentTabName }}</h2>
          <p class="subtitle">{{ currentTabSubtitle }}</p>
        </div>
        <div class="quick-actions">
          <button class="btn btn-secondary btn-icon" @click="fetchInitialData" title="Refrescar datos">
            🔄 Sincronizar
          </button>
        </div>
      </header>

      <!-- TAB: STATIONS -->
      <section v-if="activeTab === 'stations'" class="tab-pane">
        <div class="stations-grid">
          <div 
            v-for="(info, name) in stationsInfo" 
            :key="name" 
            class="station-card"
            :style="{ '--card-accent': info.color }"
          >
            <div class="station-header">
              <div class="station-icon">{{ info.emoji }}</div>
              <div class="station-frequency">{{ info.freq }}</div>
            </div>
            <div class="station-body">
              <h3>{{ name }}</h3>
              <p class="description">{{ info.desc }}</p>
              <div class="station-meta">
                <span class="meta-item">🗣️ <strong>Locutor:</strong> {{ info.host }}</span>
                <span class="meta-item">🎭 <strong>Estilo:</strong> {{ info.style }}</span>
              </div>
            </div>
            <div class="station-footer">
              <button 
                class="btn btn-primary btn-block btn-generate" 
                @click="triggerGeneration(name)"
                :disabled="generating"
              >
                ⚡ Generar Episodio
              </button>
            </div>
          </div>
        </div>

        <!-- System Universe Summary Card -->
        <div class="universe-summary-card">
          <div class="summary-icon">🌌</div>
          <div class="summary-details">
            <h3>Universo Narrativo Compartido</h3>
            <p>
              Todos los episodios generados comparten el mismo lore. Las marcas comerciales creadas, las noticias archivadas y las llamadas telefónicas alimentan la memoria persistente de los personajes locales.
            </p>
            <div class="stats-row">
              <div class="stat-box">
                <span class="stat-value">{{ characters.length }}</span>
                <span class="stat-label">Personajes</span>
              </div>
              <div class="stat-box">
                <span class="stat-value">{{ news.length }}</span>
                <span class="stat-label">Noticias en Cola</span>
              </div>
              <div class="stat-box">
                <span class="stat-value">{{ commercials.length }}</span>
                <span class="stat-label">Comerciales</span>
              </div>
              <div class="stat-box">
                <span class="stat-value">{{ tracks.length }}</span>
                <span class="stat-label">Canciones</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- TAB: EPISODES -->
      <section v-if="activeTab === 'episodes'" class="tab-pane">
        <div v-if="episodes.length === 0" class="empty-state">
          <div class="empty-icon">🎧</div>
          <h3>No hay episodios generados</h3>
          <p>Ve a la pestaña de Estaciones y genera tu primer programa de radio personalizado.</p>
        </div>

        <div v-else class="episodes-container">
          <div class="episodes-list">
            <div 
              v-for="ep in episodes" 
              :key="ep.id" 
              class="episode-row"
              :class="{ active: selectedEpisode?.id === ep.id }"
              @click="selectEpisode(ep)"
            >
              <div class="ep-info">
                <span class="ep-badge">{{ ep.station }}</span>
                <h4>{{ ep.title }}</h4>
                <div class="ep-meta">
                  <span>📅 {{ formatDate(ep.created_at) }}</span>
                  <span>⏱️ {{ formatDuration(ep.duration) }}</span>
                </div>
              </div>
              <div class="ep-controls">
                <button 
                  class="btn btn-sm btn-circle btn-play" 
                  @click.stop="playEpisodeDirect(ep)"
                  title="Reproducir"
                >
                  ▶️
                </button>
                <button 
                  class="btn btn-sm btn-circle btn-danger" 
                  @click.stop="deleteEpisode(ep.id)"
                  title="Eliminar"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>

          <!-- Episode Viewer / Playback & Screenplay -->
          <div class="episode-viewer" v-if="selectedEpisode">
            <div class="viewer-header">
              <div class="station-pill">{{ selectedEpisode.station }}</div>
              <h3>{{ selectedEpisode.title }}</h3>
              <p class="meta">Generado el {{ formatDate(selectedEpisode.created_at) }} | Duración: {{ formatDuration(selectedEpisode.duration) }}</p>
            </div>

            <!-- Integrated Custom Audio Player -->
            <div class="custom-player">
              <div class="player-controls">
                <button class="player-btn" @click="togglePlay">
                  {{ isPlaying ? '⏸️ Pausar' : '▶️ Reproducir' }}
                </button>
                <div class="player-timeline">
                  <span class="time-label">{{ formatDuration(currentTime) }}</span>
                  <input 
                    type="range" 
                    min="0" 
                    :max="selectedEpisode.duration || 100" 
                    v-model="currentTime" 
                    @change="seekAudio"
                    class="player-slider"
                  >
                  <span class="time-label">{{ formatDuration(selectedEpisode.duration) }}</span>
                </div>
                <div class="player-volume">
                  🔊
                  <input type="range" min="0" max="1" step="0.1" v-model="volume" @input="updateVolume" class="volume-slider">
                </div>
              </div>

              <!-- Animated Equalizer simulation -->
              <div class="equalizer" :class="{ pulsing: isPlaying }">
                <span v-for="n in 15" :key="n" class="bar"></span>
              </div>
            </div>

            <!-- Screenplay / Script Timeline -->
            <div class="script-timeline">
              <h4>📜 Guión Narrativo del Episodio</h4>
              <div class="script-scroller">
                <div 
                  v-for="(seg, idx) in parsedScript" 
                  :key="idx" 
                  class="timeline-segment" 
                  :class="seg.type"
                >
                  <!-- Speech Type Segment -->
                  <template v-if="seg.type === 'speech'">
                    <div class="speaker-avatar" :class="seg.voice_id">
                      {{ getAvatarEmoji(seg.speaker) }}
                    </div>
                    <div class="speech-bubble">
                      <div class="bubble-header">
                        <span class="speaker-name">{{ seg.speaker }}</span>
                        <span class="segment-badge" :class="seg.effect || 'normal'">
                          {{ seg.effect === 'telephony' ? '📞 Llamada' : '🎙️ Mic' }}
                        </span>
                      </div>
                      <p class="speech-text">"{{ seg.text }}"</p>
                    </div>
                  </template>

                  <!-- Music Type Segment -->
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

                  <!-- FX Type Segment -->
                  <template v-else-if="seg.type === 'fx'">
                    <div class="fx-segment">
                      🎛️ EFECTO: <strong>{{ seg.fx_type }}</strong> (Static/Sweeper)
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
          <div class="episode-viewer empty" v-else>
            <div class="empty-icon">👈</div>
            <p>Selecciona un episodio de la lista para escucharlo y visualizar su guión narrativo.</p>
          </div>
        </div>
      </section>

      <!-- TAB: NEWS LIBRARY -->
      <section v-if="activeTab === 'news'" class="tab-pane">
        <div class="split-pane">
          <div class="left-list card-container">
            <div class="section-title-row">
              <h3>Biblioteca de Noticias</h3>
              <span class="badge">{{ news.length }} items</span>
            </div>
            <div class="news-list">
              <div 
                v-for="item in news" 
                :key="item.id" 
                class="news-card"
              >
                <div class="news-meta">
                  <span class="tag-badge">{{ item.category }}</span>
                  <span class="tone-badge">{{ item.tone }}</span>
                </div>
                <h4>{{ item.headline }}</h4>
                <p>{{ item.summary }}</p>
                <div class="full-script-preview">
                  <strong>Guión de Voz:</strong>
                  <p class="quote">"{{ item.full_script }}"</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Add News Form -->
          <div class="right-form card-container">
            <h3>📢 Crear Noticia Ficticia</h3>
            <p class="form-desc">Inserta una nueva noticia en el universo compartido. Los agentes de radio la comentarán en los próximos episodios de acuerdo a su personalidad.</p>
            
            <form @submit.prevent="createNews" class="app-form">
              <div class="form-group">
                <label>Titular Impactante</label>
                <input v-model="newNews.headline" placeholder="Ej. Plaga de termitas devora tractor en segundos" required>
              </div>
              <div class="form-group">
                <label>Breve Resumen</label>
                <input v-model="newNews.summary" placeholder="Ej. El granjero reporta pérdida total del motor..." required>
              </div>
              <div class="form-group">
                <label>Categoría</label>
                <select v-model="newNews.category">
                  <option value="Agricultura">🌾 Agricultura</option>
                  <option value="Transporte">🚛 Transporte</option>
                  <option value="Economía">💰 Economía</option>
                  <option value="Tecnología">📡 Tecnología</option>
                  <option value="Clima">🌩️ Clima</option>
                  <option value="Sucesos Extraños">👽 Sucesos Extraños</option>
                </select>
              </div>
              <div class="form-group">
                <label>Tono Periodístico</label>
                <select v-model="newNews.tone">
                  <option value="Sensacionalista">🔥 Sensacionalista</option>
                  <option value="Misterioso">🔮 Misterioso</option>
                  <option value="Absurdo">🤡 Absurdo</option>
                  <option value="Serio">👔 Serio</option>
                </select>
              </div>
              <div class="form-group">
                <label>Guión Completo del Reportero (Será leído por TTS)</label>
                <textarea 
                  v-model="newNews.full_script" 
                  rows="5" 
                  placeholder="Escribe lo que el reportero dirá exactamente en el micrófono de noticias..."
                  required
                ></textarea>
              </div>
              <button type="submit" class="btn btn-primary btn-block">
                💾 Registrar Noticia
              </button>
            </form>
          </div>
        </div>
      </section>

      <!-- TAB: COMMERCIALS -->
      <section v-if="activeTab === 'commercials'" class="tab-pane">
        <div class="split-pane">
          <!-- Brands and Commercial List -->
          <div class="left-list card-container">
            <div class="section-title-row">
              <h3>Comerciales Recurrentes</h3>
              <span class="badge">{{ commercials.length }} anuncios</span>
            </div>
            
            <div class="brands-list-horizontal">
              <div v-for="brand in brands" :key="brand.id" class="brand-pill-card">
                <h5>{{ brand.name }}</h5>
                <span class="slogan">"{{ brand.slogan }}"</span>
                <span class="industry-badge">{{ brand.industry }}</span>
              </div>
            </div>

            <div class="commercials-list">
              <div v-for="comm in commercials" :key="comm.id" class="comm-card">
                <div class="comm-header">
                  <h5>{{ comm.title }}</h5>
                  <span class="brand-tag">{{ comm.brand_name }}</span>
                </div>
                <p class="comm-script">"{{ comm.script }}"</p>
                <div class="comm-meta">
                  <span>⏱️ {{ comm.duration }}s</span>
                  <span>📁 Campaña: {{ comm.campaign }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Add Brand / Commercial Forms -->
          <div class="right-form-stack">
            <!-- Brand Form -->
            <div class="right-form card-container">
              <h3>🏭 Registrar Marca Ficticia</h3>
              <form @submit.prevent="createBrand" class="app-form">
                <div class="form-group">
                  <label>Nombre de la Empresa</label>
                  <input v-model="newBrand.name" placeholder="Ej. MegaTruck Parts" required>
                </div>
                <div class="form-group">
                  <label>Eslogan Corporativo</label>
                  <input v-model="newBrand.slogan" placeholder="Ej. Piezas baratas para viajes arriesgados" required>
                </div>
                <div class="form-group">
                  <label>Industria</label>
                  <input v-model="newBrand.industry" placeholder="Ej. Repuestos / Mecánica" required>
                </div>
                <div class="form-group">
                  <label>Descripción de Actividad</label>
                  <textarea v-model="newBrand.description" rows="2" placeholder="Describe qué vende la empresa..." required></textarea>
                </div>
                <button type="submit" class="btn btn-secondary btn-block">
                  💾 Guardar Marca
                </button>
              </form>
            </div>

            <!-- Commercial Form -->
            <div class="right-form card-container">
              <h3>📢 Crear Guión de Anuncio</h3>
              <form @submit.prevent="createCommercial" class="app-form">
                <div class="form-group">
                  <label>Seleccionar Marca</label>
                  <select v-model="newCommercial.brand_id" required>
                    <option v-for="b in brands" :key="b.id" :value="b.id">
                      {{ b.name }} ({{ b.industry }})
                    </option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Título del Anuncio</label>
                  <input v-model="newCommercial.title" placeholder="Ej. Oferta Neumáticos de Otoño" required>
                </div>
                <div class="form-group">
                  <label>Campaña</label>
                  <input v-model="newCommercial.campaign" placeholder="Ej. Lanzamiento 2026">
                </div>
                <div class="form-group">
                  <label>Guión del Locutor de Anuncios</label>
                  <textarea v-model="newCommercial.script" rows="3" placeholder="Redacta la locución publicitaria..." required></textarea>
                </div>
                <button type="submit" class="btn btn-primary btn-block">
                  💾 Guardar Anuncio
                </button>
              </form>
            </div>
          </div>
        </div>
      </section>

      <!-- TAB: CHARACTERS & MEMORY -->
      <section v-if="activeTab === 'characters'" class="tab-pane">
        <div class="characters-grid">
          <div 
            v-for="char in characters" 
            :key="char.id" 
            class="character-detail-card"
            @click="fetchMemories(char)"
          >
            <div class="char-header">
              <div class="char-avatar">{{ getAvatarEmoji(char.name) }}</div>
              <div class="char-title-meta">
                <h3>{{ char.name }}</h3>
                <span class="role-badge">{{ char.role }}</span>
              </div>
            </div>
            <div class="char-body">
              <p><strong>Personalidad:</strong> {{ char.personality }}</p>
              <p><strong>Afinidad Radial:</strong> {{ char.station_affinity }}</p>
              <p class="description">{{ char.description }}</p>
            </div>
            
            <!-- Narrative Memory segment inside character card -->
            <div class="char-memory-container">
              <h4>🧠 Memoria Narrativa Reciente</h4>
              <div v-if="characterMemories[char.id] === undefined" class="memory-loading">
                Haga clic para cargar recuerdos...
              </div>
              <div v-else-if="characterMemories[char.id].length === 0" class="memory-empty">
                No tiene recuerdos en la base de datos todavía.
              </div>
              <div v-else class="memory-list">
                <div 
                  v-for="mem in characterMemories[char.id]" 
                  :key="mem.id" 
                  class="memory-item"
                >
                  <span class="memory-date">🗓️ {{ formatDate(mem.created_at) }}</span>
                  <p class="memory-text">"{{ mem.memory }}"</p>
                  <span class="memory-ep" v-if="mem.episode_title">En: {{ mem.episode_title }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- TAB: MUSIC LIBRARY -->
      <section v-if="activeTab === 'music'" class="tab-pane">
        <div class="music-library-layout card-container">
          <div class="library-header-row">
            <div class="library-stats">
              <div class="stat-box">
                <span class="stat-value">{{ tracks.length }}</span>
                <span class="stat-label">Canciones Indexadas</span>
              </div>
              <div class="stat-box">
                <span class="stat-value">{{ formatDuration(totalMusicDuration) }}</span>
                <span class="stat-label">Duración Total</span>
              </div>
            </div>
            <div style="display: flex; gap: 12px; align-items: center;">
              <label class="btn btn-secondary btn-icon" style="cursor: pointer; margin: 0;">
                📤 {{ uploadingMusic ? 'Subiendo...' : 'Subir Archivo MP3' }}
                <input 
                  type="file" 
                  accept=".mp3" 
                  @change="handleMusicUpload" 
                  style="display: none;" 
                  :disabled="uploadingMusic || scanningMusic"
                >
              </label>

              <button 
                class="btn btn-primary btn-icon" 
                @click="scanMusicLibrary" 
                :disabled="scanningMusic || uploadingMusic"
              >
                <span v-if="scanningMusic">🔄 Escaneando...</span>
                <span v-else>🔍 Escanear Carpeta de Música</span>
              </button>
            </div>
          </div>

          <div class="music-table-wrapper">
            <table class="music-table">
              <thead>
                <tr>
                  <th>Título</th>
                  <th>Artista</th>
                  <th>Duración</th>
                  <th>Ubicación del Archivo</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in tracks" :key="t.id">
                  <td class="track-title">🎵 {{ t.title }}</td>
                  <td>{{ t.artist }}</td>
                  <td>{{ formatDuration(t.duration) }}</td>
                  <td class="file-path"><code>{{ t.file_path }}</code></td>
                </tr>
                <tr v-if="tracks.length === 0">
                  <td colspan="4" class="text-center">No hay archivos de música indexados. Haga clic en Escanear.</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Note about procedural generation -->
          <div class="alert alert-info">
            <strong>💡 Información de Prueba:</strong> Si tu carpeta de música local está vacía, el motor de producción generará automáticamente pistas de música chiptune sintéticas de prueba. ¡No requieres subir archivos para ensayar!
          </div>
        </div>
      </section>
    </main>

    <!-- Generation Pipeline Status Modal -->
    <div class="modal-overlay" v-if="generationJob">
      <div class="modal-card">
        <div class="modal-header">
          <h3>⚡ Pipeline de Generación por Agentes</h3>
          <span class="station-target">{{ generationJob.station }}</span>
        </div>
        <div class="modal-body">
          <p class="pipeline-desc">Los agentes de VirtualRadio están planificando, escribiendo y mezclando el nuevo programa en segundo plano...</p>
          
          <div class="pipeline-progress-bar">
            <div class="progress-fill" :style="{ width: pipelineProgressPercentage + '%' }"></div>
          </div>
          
          <div class="pipeline-steps">
            <div class="step-line" :class="{ active: currentJobStatusIndex >= 0, completed: currentJobStatusIndex > 0 }">
              <span class="step-bullet">1</span>
              <div class="step-info">
                <h5>Agente Planificador de Episodio (Planner)</h5>
                <p>Analiza el lore, selecciona canciones de la biblioteca, consulta personajes.</p>
              </div>
            </div>
            
            <div class="step-line" :class="{ active: currentJobStatusIndex >= 1, completed: currentJobStatusIndex > 1 }">
              <span class="step-bullet">2</span>
              <div class="step-info">
                <h5>Escritores Temáticos (Host, News, Commercial, Callers)</h5>
                <p>Los agentes colaboran para redactar los guiones con su voz y tono característico.</p>
              </div>
            </div>

            <div class="step-line" :class="{ active: currentJobStatusIndex >= 2, completed: currentJobStatusIndex > 2 }">
              <span class="step-bullet">3</span>
              <div class="step-info">
                <h5>Sintetizador de Voces Regionales (TTS)</h5>
                <p>Genera las narraciones usando los acentos correctos asignados a cada rol.</p>
              </div>
            </div>

            <div class="step-line" :class="{ active: currentJobStatusIndex >= 3, completed: currentJobStatusIndex > 3 }">
              <span class="step-bullet">4</span>
              <div class="step-info">
                <h5>Mezclador de Audio FX (Audio Engine)</h5>
                <p>Aplica filtros de teléfono, agrega sweeper estéreo, realiza el ducking musical.</p>
              </div>
            </div>
          </div>

          <div class="pipeline-console">
            <div class="console-header">LOGS DE EJECUCIÓN</div>
            <div class="console-body">
              <div class="console-line text-blue">> Inicializando agentes...</div>
              <div class="console-line text-green" v-if="currentJobStatusIndex >= 0">> [PlannerAgent] Planificando estructura para {{ generationJob.station }}</div>
              <div class="console-line text-green" v-if="currentJobStatusIndex >= 1">> [ScriptWriterAgent] Redactando comentarios humorísticos</div>
              <div class="console-line text-green" v-if="currentJobStatusIndex >= 2">> [VoiceSynthesisAgent] Compilando voz con locuciones gTTS</div>
              <div class="console-line text-green" v-if="currentJobStatusIndex >= 3">> [AudioMixerAgent] Realizando compresión de volumen y ducking</div>
              <div class="console-line text-yellow">> Estado Actual: {{ generationJob.status }}</div>
              <div class="console-line text-red" v-if="generationJob.status === 'Failed'">> ERROR: {{ generationJob.error }}</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button 
            class="btn btn-secondary" 
            @click="closeGenerationModal"
            :disabled="generationJob.status !== 'Completed' && generationJob.status !== 'Failed'"
          >
            {{ (generationJob.status === 'Completed' || generationJob.status === 'Failed') ? 'Cerrar' : 'Procesando...' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const API_BASE = 'http://localhost:5000/api'

// Tab definitions
const tabs = [
  { id: 'stations', name: 'Estaciones', icon: '📻', subtitle: 'Selecciona una estación de radio y genera episodios mediante IA colaborativa.' },
  { id: 'episodes', name: 'Episodios', icon: '🎧', subtitle: 'Escucha los episodios de radio generados y visualiza los guiones.' },
  { id: 'news', name: 'Noticias Compartidas', icon: '📰', subtitle: 'Gestiona la biblioteca de noticias ficticias que comparten las estaciones.' },
  { id: 'commercials', name: 'Comerciales', icon: '📢', subtitle: 'Registra marcas del universo y escribe sus guiones publicitarios.' },
  { id: 'characters', name: 'Personajes', icon: '👥', subtitle: 'Explora los perfiles de la vecindad y su memoria persistente.' },
  { id: 'music', name: 'Biblioteca Musical', icon: '🎵', subtitle: 'Administra tus archivos de audio musicales locales.' }
]

const activeTab = ref('stations')

const currentTabName = computed(() => {
  return tabs.find(t => t.id === activeTab.value)?.name || ''
})

const currentTabSubtitle = computed(() => {
  return tabs.find(t => t.id === activeTab.value)?.subtitle || ''
})

// Station UI details
const stationsInfo = {
  "AgroTalk FM": {
    freq: "95.2 FM",
    emoji: "🌾",
    host: "Clem",
    style: "Informativa Agrícola",
    desc: "Radio de debate centrada en la cosecha, precios de fertilizantes y chismes de tractor.",
    color: "#10b981" // Emerald
  },
  "Trucker News Radio": {
    freq: "104.8 FM",
    emoji: "🚛",
    host: "Diesel Dan",
    style: "Talk Radio Camionera",
    desc: "Noticias de autopistas, reportes de tráfico de larga distancia e historias del asfalto.",
    color: "#6b7280" // Gray/Steel
  },
  "SimNation News": {
    freq: "88.0 FM",
    emoji: "👔",
    host: "Audrey Vance",
    style: "Noticiero Formal",
    desc: "Boletines de simulación serios y objetivos sobre la economía regional e infraestructura.",
    color: "#3b82f6" // Blue
  },
  "WCTR Sim Edition": {
    freq: "99.1 FM",
    emoji: "👽",
    host: "Dick Brainwave",
    style: "Satírica / Conspiranoica",
    desc: "Teorías locas, llamadas telefónicas extravagantes y secretos alienígenas de los cultivos.",
    color: "#ec4899" // Hot Pink
  }
}

// Data Lists
const tracks = ref([])
const characters = ref([])
const news = ref([])
const commercials = ref([])
const brands = ref([])
const episodes = ref([])

const characterMemories = ref({}) // char_id -> memories list

// Selected states
const selectedEpisode = ref(null)
const backendConnected = ref(false)

// Forms Model
const newNews = ref({
  headline: '',
  summary: '',
  category: 'Agricultura',
  tone: 'Sensacionalista',
  full_script: ''
})

const newBrand = ref({
  name: '',
  slogan: '',
  industry: '',
  description: ''
})

const newCommercial = ref({
  brand_id: null,
  title: '',
  script: '',
  campaign: 'General',
  duration: 30
})

// Async Generation State
const generating = ref(false)
const generationJob = ref(null)
let jobPollingInterval = null
const scanningMusic = ref(false)
const uploadingMusic = ref(false)

const pipelineProgressPercentage = computed(() => {
  if (!generationJob.value) return 0
  const status = generationJob.value.status
  if (status.includes("Starting")) return 10
  if (status.includes("Planning")) return 30
  if (status.includes("Synthesizing")) return 60
  if (status.includes("Mixing")) return 85
  if (status === "Completed") return 100
  return 0
})

const currentJobStatusIndex = computed(() => {
  if (!generationJob.value) return -1
  const status = generationJob.value.status
  if (status.includes("Starting") || status.includes("Planning")) return 0
  if (status.includes("Synthesizing")) return 2
  if (status.includes("Mixing")) return 3
  if (status === "Completed") return 4
  return -1
})

// Audio Player variables
const audioInstance = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const volume = ref(0.8)

const totalMusicDuration = computed(() => {
  return tracks.value.reduce((acc, t) => acc + t.duration, 0)
})

const parsedScript = computed(() => {
  if (!selectedEpisode.value || !selectedEpisode.value.script_json) return []
  try {
    return JSON.parse(selectedEpisode.value.script_json)
  } catch (e) {
    return []
  }
})

// API Operations
const fetchInitialData = async () => {
  try {
    const [tracksRes, charsRes, newsRes, commsRes, brandsRes, epsRes] = await Promise.all([
      fetch(`${API_BASE}/music`),
      fetch(`${API_BASE}/characters`),
      fetch(`${API_BASE}/news`),
      fetch(`${API_BASE}/commercials`),
      fetch(`${API_BASE}/commercials/brands`),
      fetch(`${API_BASE}/episodes`)
    ])

    tracks.value = await tracksRes.json()
    characters.value = await charsRes.json()
    news.value = await newsRes.json()
    commercials.value = await commsRes.json()
    brands.value = await brandsRes.json()
    episodes.value = await epsRes.json()
    
    // Auto-select first brand for form
    if (brands.value.length > 0) {
      newCommercial.value.brand_id = brands.value[0].id
    }
    
    backendConnected.value = true
  } catch (e) {
    console.error("Connection to backend API failed:", e)
    backendConnected.value = false
  }
}

const scanMusicLibrary = async () => {
  scanningMusic.value = true
  try {
    const res = await fetch(`${API_BASE}/music/scan`, { method: 'POST' })
    const data = await res.json()
    tracks.value = data.tracks
    alert("¡Escaneo completo! Biblioteca sincronizada.")
  } catch (e) {
    alert("Error al escanear la biblioteca de música.")
  } finally {
    scanningMusic.value = false
  }
}

const handleMusicUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  if (!file.name.toLowerCase().endsWith('.mp3')) {
    alert("Solo se permiten archivos MP3.")
    return
  }
  
  uploadingMusic.value = true
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await fetch(`${API_BASE}/music/upload`, {
      method: 'POST',
      body: formData
    })
    const data = await res.json()
    if (res.ok) {
      tracks.value = data.tracks
      alert("¡Archivo subido e indexado exitosamente!")
    } else {
      alert("Error al subir archivo: " + data.error)
    }
  } catch (e) {
    console.error("Error uploading file", e)
    alert("Error al conectar con la API de subida.")
  } finally {
    uploadingMusic.value = false
    // Reset selection
    event.target.value = ''
  }
}

const fetchMemories = async (char) => {
  try {
    const res = await fetch(`${API_BASE}/characters/${char.id}/memories`)
    characterMemories.value[char.id] = await res.json()
  } catch (e) {
    console.error("Could not fetch character memories", e)
  }
}

const createNews = async () => {
  try {
    const res = await fetch(`${API_BASE}/news`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newNews.value)
    })
    if (res.ok) {
      const added = await res.json()
      news.value.unshift(added)
      // Reset form
      newNews.value = {
        headline: '',
        summary: '',
        category: 'Agricultura',
        tone: 'Sensacionalista',
        full_script: ''
      }
      alert("¡Noticia registrada exitosamente!")
    }
  } catch (e) {
    alert("Error al guardar noticia.")
  }
}

const createBrand = async () => {
  try {
    const res = await fetch(`${API_BASE}/commercials/brands`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newBrand.value)
    })
    const data = await res.json()
    if (res.ok) {
      brands.value.push(data)
      newCommercial.value.brand_id = data.id
      newBrand.value = { name: '', slogan: '', industry: '', description: '' }
      alert("¡Marca registrada exitosamente!")
    } else {
      alert("Error: " + data.error)
    }
  } catch (e) {
    alert("Error al guardar marca.")
  }
}

const createCommercial = async () => {
  try {
    const res = await fetch(`${API_BASE}/commercials`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newCommercial.value)
    })
    if (res.ok) {
      const added = await res.json()
      commercials.value.unshift(added)
      newCommercial.value.title = ''
      newCommercial.value.script = ''
      alert("¡Anuncio registrado exitosamente!")
    }
  } catch (e) {
    alert("Error al registrar anuncio.")
  }
}

const deleteEpisode = async (epId) => {
  if (!confirm("¿Seguro que deseas eliminar este episodio?")) return
  try {
    const res = await fetch(`${API_BASE}/episodes/${epId}`, { method: 'DELETE' })
    if (res.ok) {
      episodes.value = episodes.value.filter(e => e.id !== epId)
      if (selectedEpisode.value?.id === epId) {
        selectedEpisode.value = null
        stopAudio()
      }
    }
  } catch (e) {
    alert("Error al eliminar episodio.")
  }
}

// Trigger Agentic Episode Generation
const triggerGeneration = async (stationName) => {
  generating.value = true
  try {
    const res = await fetch(`${API_BASE}/episodes/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ station: stationName })
    })
    const data = await res.json()
    if (res.ok) {
      generationJob.value = {
        id: data.job_id,
        station: stationName,
        status: 'Queued',
        error: null
      }
      // Start polling status
      pollJobStatus()
    } else {
      alert("Error al iniciar generación: " + data.error)
      generating.value = false
    }
  } catch (e) {
    alert("Error al conectar con la API de generación.")
    generating.value = false
  }
}

const pollJobStatus = () => {
  jobPollingInterval = setInterval(async () => {
    if (!generationJob.value) return
    try {
      const res = await fetch(`${API_BASE}/jobs/${generationJob.value.id}`)
      const data = await res.json()
      generationJob.value.status = data.status
      generationJob.value.error = data.error
      
      if (data.status === 'Completed') {
        clearInterval(jobPollingInterval)
        generating.value = false
        // Refresh episodes list
        const epsRes = await fetch(`${API_BASE}/episodes`)
        episodes.value = await epsRes.json()
        
        // Auto-select the newly generated episode
        if (data.episode_id) {
          const newEp = episodes.value.find(e => e.id === data.episode_id)
          if (newEp) selectEpisode(newEp)
        }
      } else if (data.status === 'Failed') {
        clearInterval(jobPollingInterval)
        generating.value = false
      }
    } catch (e) {
      console.error("Error polling job status", e)
    }
  }, 1000)
}

const closeGenerationModal = () => {
  generationJob.value = null
}

// Player Operations
const selectEpisode = (ep) => {
  stopAudio()
  selectedEpisode.value = ep
  // Pre-load characters memories if they appear in script
  try {
    const script = JSON.parse(ep.script_json)
    const callerNode = script.find(s => s.speaker === 'Caller')
    // We can fetch Silas, Juan, Cynthia, Big Rig Bob if they called
    if (callerNode) {
      // Find matching char object
      const charObj = characters.value.find(c => ep.title.includes(c.name) || callerNode.text.includes(c.name) || ep.script_json.includes(c.name))
      if (charObj) {
        fetchMemories(charObj)
      }
    }
  } catch (e) {}
}

const playEpisodeDirect = (ep) => {
  selectEpisode(ep)
  setTimeout(() => {
    togglePlay()
  }, 100)
}

const togglePlay = () => {
  if (!selectedEpisode.value) return
  
  if (!audioInstance.value) {
    // Flask serves file at static/... relative to backend.
    // Flask backend runs on port 5000
    const url = `http://localhost:5000/${selectedEpisode.value.audio_path}`
    audioInstance.value = new Audio(url)
    
    // Event listeners
    audioInstance.value.addEventListener('timeupdate', () => {
      currentTime.value = audioInstance.value.currentTime
    })
    
    audioInstance.value.addEventListener('ended', () => {
      isPlaying.value = false
      currentTime.value = 0
    })
    
    audioInstance.value.volume = volume.value
  }
  
  if (isPlaying.value) {
    audioInstance.value.pause()
    isPlaying.value = false
  } else {
    audioInstance.value.play().then(() => {
      isPlaying.value = true
    }).catch(e => {
      console.error("Audio playback blocked or failed:", e)
      alert("Error al reproducir el archivo de audio. ¿El backend está sirviendo el MP3?")
    })
  }
}

const stopAudio = () => {
  if (audioInstance.value) {
    audioInstance.value.pause()
    audioInstance.value = null
  }
  isPlaying.value = false
  currentTime.value = 0
}

const seekAudio = () => {
  if (audioInstance.value) {
    audioInstance.value.currentTime = currentTime.value
  }
}

const updateVolume = () => {
  if (audioInstance.value) {
    audioInstance.value.volume = volume.value
  }
}

// Helpers
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('es-ES', { 
    hour: '2-digit', 
    minute: '2-digit', 
    day: '2-digit', 
    month: 'short' 
  })
}

const formatDuration = (secs) => {
  if (!secs) return '0:00'
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m}:${s < 10 ? '0' : ''}${s}`
}

const getAvatarEmoji = (speaker) => {
  if (!speaker) return '🎙️'
  if (speaker.includes('Clem') || speaker.includes('Host')) return '👨‍🌾'
  if (speaker.includes('Dan') || speaker.includes('Rig')) return '🚛'
  if (speaker.includes('Audrey') || speaker.includes('Reporter')) return '👩‍💼'
  if (speaker.includes('Dick') || speaker.includes('Brainwave')) return '👽'
  if (speaker.includes('Silas')) return '👴'
  if (speaker.includes('Juan')) return '🧑‍🌾'
  if (speaker.includes('Cynthia')) return '💁‍♀️'
  if (speaker.includes('Commercial')) return '📢'
  return '🎙️'
}

onMounted(() => {
  fetchInitialData()
})

onBeforeUnmount(() => {
  stopAudio()
  if (jobPollingInterval) clearInterval(jobPollingInterval)
})
</script>

<style>
/* CSS Reset and Design Tokens */
:root {
  --bg-deep: #0b0f19;
  --bg-surface: #131b2e;
  --bg-card: #1e2942;
  --bg-input: #1a233a;
  --border-color: rgba(255, 255, 255, 0.06);
  --text-primary: #f3f4f6;
  --text-muted: #9ca3af;
  
  --primary: #f59e0b;       /* Amber */
  --primary-glow: rgba(245, 158, 11, 0.15);
  --secondary: #8b5cf6;     /* Purple */
  --success: #10b981;       /* Emerald */
  --danger: #ef4444;        /* Crimson Red */
  
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
  
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 20px;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background-color: var(--bg-deep);
  color: var(--text-primary);
  font-family: 'Outfit', sans-serif;
  overflow-x: hidden;
  height: 100vh;
}

code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85em;
  color: #a78bfa;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: var(--bg-deep);
}
::-webkit-scrollbar-thumb {
  background: var(--bg-card);
  border-radius: var(--radius-sm);
}
::-webkit-scrollbar-thumb:hover {
  background: var(--primary);
}

.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* Sidebar Styling */
.sidebar {
  width: 260px;
  background-color: var(--bg-surface);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 40px;
}

.logo-icon {
  position: relative;
  font-size: 28px;
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid var(--primary);
  animation: pulse 2s infinite;
  opacity: 0;
}

@keyframes pulse {
  0% {
    transform: scale(0.95);
    opacity: 0.8;
  }
  100% {
    transform: scale(1.4);
    opacity: 0;
  }
}

.brand-text h1 {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #fff, #9ca3af);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  letter-spacing: 0.5px;
  display: inline-block;
}

.badge-glow {
  background: rgba(245, 158, 11, 0.1);
  color: var(--primary);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 15px;
  font-weight: 500;
  text-align: left;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--bg-card);
  color: var(--primary);
  box-shadow: var(--shadow-sm);
  border-left: 3px solid var(--primary);
}

.nav-icon {
  font-size: 18px;
}

.sidebar-footer {
  margin-top: auto;
  border-top: 1px solid var(--border-color);
  padding-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.server-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--danger);
  box-shadow: 0 0 8px var(--danger);
}

.status-indicator.online {
  background-color: var(--success);
  box-shadow: 0 0 8px var(--success);
}

.copyright {
  font-size: 11px;
  color: #4b5563;
}

/* Main Content area */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 40px;
  overflow-y: auto;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-title h2 {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin-bottom: 4px;
}

.page-title .subtitle {
  color: var(--text-muted);
  font-size: 14px;
}

/* General Layout helpers & components */
.card-container {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 30px;
  box-shadow: var(--shadow-sm);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  border-radius: var(--radius-md);
  padding: 12px 24px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(135deg, var(--primary), #d97706);
  color: #000;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.3);
}

.btn-primary:disabled {
  background: #4b5563;
  color: #9ca3af;
  box-shadow: none;
  transform: none;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-input);
}

.btn-danger {
  background: var(--danger);
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-block {
  width: 100%;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  padding: 0;
}

/* Station Grid Styling */
.stations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.station-card {
  background: linear-gradient(135deg, var(--bg-surface), #151e33);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.station-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background-color: var(--card-accent);
}

.station-card:hover {
  transform: translateY(-5px);
  border-color: var(--card-accent);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}

.station-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.station-icon {
  font-size: 32px;
}

.station-frequency {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 13px;
  color: var(--card-accent);
  background: rgba(255, 255, 255, 0.03);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.station-body {
  flex: 1;
  margin-bottom: 24px;
}

.station-body h3 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 8px;
}

.station-body .description {
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 16px;
}

.station-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
}

.meta-item {
  color: #e5e7eb;
}

.universe-summary-card {
  background: linear-gradient(135deg, #1d1b38, #13122c);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: var(--radius-lg);
  padding: 30px;
  display: flex;
  gap: 24px;
  align-items: center;
  box-shadow: 0 10px 30px rgba(139, 92, 246, 0.1);
}

.summary-icon {
  font-size: 48px;
  background: rgba(139, 92, 246, 0.1);
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.summary-details h3 {
  font-size: 20px;
  margin-bottom: 8px;
}

.summary-details p {
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 20px;
  max-width: 800px;
}

.stats-row {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
}

.stat-box {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 800;
  color: var(--secondary);
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Episodes Panel */
.episodes-container {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 30px;
  align-items: start;
  height: calc(100vh - 200px);
}

.episodes-list {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  overflow-y: auto;
  max-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.episode-row {
  background-color: var(--bg-card);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.episode-row:hover {
  background-color: var(--bg-input);
  border-color: rgba(255, 255, 255, 0.05);
}

.episode-row.active {
  border-color: var(--primary);
  background: linear-gradient(90deg, var(--bg-input), #1e253c);
}

.ep-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ep-badge {
  font-size: 9px;
  font-weight: 700;
  color: var(--primary);
  background: var(--primary-glow);
  padding: 2px 6px;
  border-radius: 4px;
  align-self: flex-start;
}

.ep-info h4 {
  font-size: 14px;
  font-weight: 600;
}

.ep-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: var(--text-muted);
}

.ep-controls {
  display: flex;
  gap: 8px;
}

.episode-viewer {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 30px;
  display: flex;
  flex-direction: column;
  max-height: 100%;
  overflow-y: auto;
}

.episode-viewer.empty {
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
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
}

.player-btn:active {
  transform: scale(0.98);
}

.player-timeline {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.time-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
}

.player-slider {
  flex: 1;
  accent-color: var(--primary);
  height: 4px;
  border-radius: 2px;
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

/* Stagger animation delay on equalizer bars */
.equalizer.pulsing .bar:nth-child(2n) { animation-duration: 0.5s; }
.equalizer.pulsing .bar:nth-child(3n) { animation-duration: 0.9s; }
.equalizer.pulsing .bar:nth-child(4n) { animation-duration: 0.6s; }
.equalizer.pulsing .bar:nth-child(5n) { animation-duration: 1.1s; }

@keyframes bounce {
  0% { height: 2px; }
  100% { height: 28px; }
}

/* Screenplay Timeline */
.script-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  overflow: hidden;
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

.speaker-avatar.host { border-color: var(--primary); }
.speaker-avatar.caller { border-color: var(--secondary); }
.speaker-avatar.reporter { border-color: var(--success); }
.speaker-avatar.commercial { border-color: #8be4fc; }

.speech-bubble {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 0 var(--radius-md) var(--radius-md) var(--radius-md);
  padding: 16px;
  flex: 1;
}

.bubble-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
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

/* Music Segment Card in screenplay */
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
}

.music-details {
  flex: 1;
  display: flex;
  flex-direction: column;
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
}

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

/* Split Pane Layout (News, Commercials) */
.split-pane {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 30px;
  align-items: start;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 12px;
}

.news-list, .commercials-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
  padding-right: 8px;
}

.news-card, .comm-card {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 20px;
}

.news-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.tag-badge {
  background-color: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.tone-badge {
  background-color: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
  border: 1px solid rgba(139, 92, 246, 0.3);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.news-card h4 {
  font-size: 16px;
  margin-bottom: 8px;
}

.news-card p {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
  margin-bottom: 12px;
}

.full-script-preview {
  background-color: var(--bg-deep);
  border-radius: var(--radius-sm);
  padding: 12px;
  font-size: 12px;
}

.full-script-preview .quote {
  font-style: italic;
  color: #d1d5db;
  margin-top: 4px;
}

/* Forms styling */
.form-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 20px;
  line-height: 1.5;
}

.app-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: #d1d5db;
}

.app-form input, .app-form select, .app-form textarea {
  background-color: var(--bg-input);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  font-family: inherit;
  font-size: 14px;
}

.app-form input:focus, .app-form select:focus, .app-form textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-glow);
}

/* Commercial horizontal brand scroll */
.brands-list-horizontal {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 12px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
}

.brand-pill-card {
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 160px;
}

.brand-pill-card h5 {
  font-size: 13px;
}

.brand-pill-card .slogan {
  font-size: 10px;
  font-style: italic;
  color: var(--text-muted);
}

.industry-badge {
  font-size: 8px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.05);
  align-self: flex-start;
  padding: 1px 4px;
  border-radius: 3px;
  color: var(--primary);
}

.comm-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  align-items: center;
}

.brand-tag {
  background-color: var(--primary-glow);
  color: var(--primary);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.comm-script {
  font-style: italic;
  font-size: 13px;
  color: #e5e7eb;
  line-height: 1.5;
  margin-bottom: 12px;
}

.comm-meta {
  display: flex;
  gap: 16px;
  font-size: 11px;
  color: var(--text-muted);
}

.right-form-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Characters Section */
.characters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
}

.character-detail-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.character-detail-card:hover {
  transform: translateY(-2px);
  border-color: var(--secondary);
}

.char-header {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 16px;
}

.char-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.char-title-meta h3 {
  font-size: 18px;
}

.role-badge {
  font-size: 10px;
  background-color: rgba(139, 92, 246, 0.1);
  color: #a78bfa;
  border: 1px solid rgba(139, 92, 246, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
}

.char-body {
  font-size: 13px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 20px;
}

.char-body .description {
  color: var(--text-muted);
  line-height: 1.4;
  margin-top: 4px;
}

.char-memory-container {
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
}

.char-memory-container h4 {
  font-size: 12px;
  color: var(--secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.memory-loading, .memory-empty {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
}

.memory-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.memory-item {
  background-color: var(--bg-card);
  padding: 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  position: relative;
}

.memory-date {
  font-size: 9px;
  color: var(--text-muted);
}

.memory-text {
  margin-top: 2px;
  line-height: 1.4;
}

.memory-ep {
  font-size: 9px;
  color: var(--secondary);
  font-weight: 600;
  display: block;
  margin-top: 4px;
}

/* Music Library Table */
.music-library-layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.library-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 20px;
}

.music-table-wrapper {
  overflow-x: auto;
}

.music-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.music-table th {
  padding: 12px 16px;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--text-muted);
  border-bottom: 2px solid var(--border-color);
}

.music-table td {
  padding: 16px;
  font-size: 14px;
  border-bottom: 1px solid var(--border-color);
}

.track-title {
  font-weight: 600;
}

.file-path {
  font-size: 12px;
}

.text-center {
  text-align: center;
}

.alert {
  padding: 16px;
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.5;
}

.alert-info {
  background-color: rgba(59, 130, 246, 0.1);
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

/* Modal Overlay */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  width: 600px;
  max-width: 90%;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  padding: 24px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  font-size: 18px;
}

.station-target {
  font-size: 11px;
  font-weight: 700;
  background-color: var(--primary-glow);
  color: var(--primary);
  padding: 2px 8px;
  border-radius: 4px;
}

.modal-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
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
  box-shadow: 0 0 8px var(--primary-glow);
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
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 120px;
  overflow-y: auto;
}

.console-line {
  line-height: 1.4;
}

.text-blue { color: #60a5fa; }
.text-green { color: #34d399; }
.text-yellow { color: #fbbf24; }
.text-red { color: #f87171; }

.modal-footer {
  padding: 24px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
}
</style>
