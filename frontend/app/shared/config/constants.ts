export interface NavItem {
  id: string;
  label: string;
  icon: string;
  to: string;
  subtitle: string;
}

export const NAV_ITEMS: NavItem[] = [
  { id: "stations", label: "Estaciones", icon: "📻", to: "/", subtitle: "Selecciona una estación y genera episodios mediante el pipeline de agentes." },
  { id: "episodes", label: "Episodios", icon: "🎧", to: "/episodes", subtitle: "Escucha los episodios generados y visualiza sus guiones." },
  { id: "news", label: "Noticias", icon: "📰", to: "/news", subtitle: "Gestiona la biblioteca de noticias ficticias compartidas." },
  { id: "commercials", label: "Comerciales", icon: "📢", to: "/commercials", subtitle: "Registra marcas del universo y escribe sus guiones publicitarios." },
  { id: "characters", label: "Personajes", icon: "👥", to: "/characters", subtitle: "Explora los perfiles de la vecindad y su memoria persistente." },
  { id: "music", label: "Biblioteca Musical", icon: "🎵", to: "/music", subtitle: "Administra tus archivos de audio musicales." },
];

export interface Option {
  value: string;
  label: string;
}

export const NEWS_CATEGORIES: Option[] = [
  { value: "Agricultura", label: "🌾 Agricultura" },
  { value: "Transporte", label: "🚛 Transporte" },
  { value: "Economía", label: "💰 Economía" },
  { value: "Tecnología", label: "📡 Tecnología" },
  { value: "Clima", label: "🌩️ Clima" },
  { value: "Comunidad", label: "🏘️ Comunidad" },
  { value: "Política Local", label: "🏛️ Política Local" },
  { value: "Sucesos Extraños", label: "👽 Sucesos Extraños" },
];

export const NEWS_TONES: Option[] = [
  { value: "Serio", label: "👔 Serio" },
  { value: "Sensacionalista", label: "🔥 Sensacionalista" },
  { value: "Misterioso", label: "🔮 Misterioso" },
  { value: "Absurdo", label: "🤡 Absurdo" },
];

export const STORY_STATUSES: Option[] = [
  { value: "active", label: "🟢 Activo" },
  { value: "resolved", label: "✅ Resuelto" },
];

/** Job statuses from the backend pipeline, in order, mapped to UI step index. */
export const JOB_STATUS_STEP: Record<string, number> = {
  queued: 0,
  planning: 0,
  synthesizing: 2,
  mixing: 3,
  completed: 4,
  failed: -1,
};

export const JOB_STATUS_PROGRESS: Record<string, number> = {
  queued: 5,
  planning: 25,
  synthesizing: 55,
  mixing: 85,
  completed: 100,
  failed: 100,
};
