# VirtualRadio - Canvas de Planeación Técnica

VirtualRadio es un generador automatizado de estaciones de radio satíricas (estilo WCTR de GTA) para videojuegos de simulación como *Farming Simulator 25*, *Euro Truck Simulator 2* y similares.

Este repositorio contiene el prototipo técnico completo (MVP) con una interfaz web en Nuxt y un servidor de procesamiento en Flask.

---

## 🛠️ Stack Tecnológico Implementado

*   **Frontend**: Nuxt 3/4 (Vue.js) en modo Single-Page Application (SPA).
*   **Backend API**: Flask (Python 3.12).
*   **Base de Datos**: SQLite (como alternativa a Postgresql para facilitar pruebas de desarrollo local con cero configuración).
*   **Procesamiento Asíncrono**: Cola de procesamiento concurrente basada en hilos (`threading.Thread`) en Flask.
*   **Audio Engine**: FFmpeg + Pydub.
*   **Voice Synthesis (TTS)**: gTTS (Google Text-To-Speech) con acentos regionales dinámicos (España para locutor, Colombia para oyentes, México para comerciales, etc.).
*   **Generación de Guiones**: Pipeline de Agentes (Episode Planner, News, Commercial, Character, Host, Assembly) con soporte híbrido para LLMs reales (Gemini / OpenRouter) y un motor de respaldo procedural autónomo.

---

## 🚀 Cómo Iniciar el Prototipo

El proyecto incluye un script automatizado `start.sh` que se encarga de crear el entorno virtual de Python, instalar dependencias de backend y frontend, y arrancar ambos servidores.

1.  **Asegurar que FFmpeg está instalado** (ya está preinstalado en este entorno).
2.  **Dar permisos e iniciar**:
    ```bash
    chmod +x start.sh
    ./start.sh
    ```
3.  **Acceder a la aplicación**:
    *   **Panel de Control (Nuxt)**: [http://localhost:3000](http://localhost:3000)
    *   **API del Backend (Flask)**: [http://localhost:5000](http://localhost:5000)

*(Opcional)* Si deseas usar generación de IA real en lugar del motor de plantillas humorísticas procedurales, exporta tu clave de API antes de iniciar:
```bash
export GEMINI_API_KEY="tu_clave_api"
# o
export OPENROUTER_API_KEY="tu_clave_api"
```

---

## 📦 Características del MVP Incluidas

*   **Music Library**: Escaneo de metadatos, cálculo de hashes MD5 contra duplicados y sincronización automática.
*   **Generación de Audio Sintético**: Si tu biblioteca musical está vacía, el motor sintetizará 3 temas chiptune (*synth_pastoral*, *synth_highway*, *synth_ambient*) para habilitar pruebas inmediatas.
*   **Pipeline de Agentes**: Generación estructurada de diálogos humorísticos de locución, reporteros de noticias, patrocinadores comerciales y llamadas telefónicas.
*   **Efectos de Radio (DSP)**:
    *   *Ducking*: Reducción automática del volumen de la música de fondo durante diálogos.
    *   *Telephony Filter*: Filtro de llamada telefónica (pasabanda de 300Hz-3kHz) para oyentes.
    *   *Sweepers & Radio Hum*: Estática de fondo y sweeps sintetizados para unir música y voz.
*   **Memoria Narrativa**: SQLite guarda las llamadas e interacciones de los personajes (*Juan*, *Silas*, etc.) para generar continuidad narrativa en futuros episodios.
*   **Reproductor de Audio y Guiones**: Escucha los episodios directamente en la web y sigue el timeline con burbujas de diálogo estilo screenplay.

---

## 📂 Estructura del Proyecto

*   [`start.sh`](file:///home/ddelgado/git/lab/VirtualRadio/start.sh): Lanzador integrado de servidores.
*   [`backend/`](file:///home/ddelgado/git/lab/VirtualRadio/backend):
    *   [`app.py`](file:///home/ddelgado/git/lab/VirtualRadio/backend/app.py): Servidor Flask, enrutamientos REST y cola de trabajos.
    *   [`database.py`](file:///home/ddelgado/git/lab/VirtualRadio/backend/database.py): Esquemas SQLite y siembra de datos.
    *   [`generator.py`](file:///home/ddelgado/git/lab/VirtualRadio/backend/generator.py): Motor de agentes de guiones y fallback procedural.
    *   [`audio_engine.py`](file:///home/ddelgado/git/lab/VirtualRadio/backend/audio_engine.py): Sintetizador de voz, generador de pistas y mezclador final.
*   [`frontend/`](file:///home/ddelgado/git/lab/VirtualRadio/frontend):
    *   [`app.vue`](file:///home/ddelgado/git/lab/VirtualRadio/frontend/app.vue): Interfaz completa de Single-Page Application en Nuxt.

Para ver los detalles técnicos y decisiones arquitectónicas, consulta la [Documentación Completa del Prototipo](file:///home/ddelgado/.gemini/antigravity-cli/brain/42bde156-69dc-487a-a11d-5d29b6445f54/prototype_documentation.md).