# VirtualRadio - Canvas de Planeación Técnica

## Estado del Proyecto

**Nombre:** VirtualRadio
**Objetivo:** Generador automatizado de estaciones de radio satíricas estilo WCTR para videojuegos de simulación.

**Estado Actual:** Planeación y diseño arquitectónico.

**Stack Tentativo:**

| Capa                    | Tecnología                |
| ----------------------- | ------------------------- |
| Frontend                | Nuxt 4 (Vuejs)            |
| Backend API             | Flask                     |
| Base de Datos           | Postgresql                |
| Procesamiento Asíncrono | Por definir               |
| IA (LLM)                | OpenRouter                |
| TTS                     | Gemini TTS preview        |
| Audio Engine            | FFmpeg + Pydub            |
| Almacenamiento          | Sistema de archivos local |
| Contenedores            | Docker                    |

---

# 1. Visión del Producto

VirtualRadio genera programas de radio completos a partir de una biblioteca musical local.

Cada episodio contiene:

* Introducción del locutor
* Presentación de canciones
* Comerciales ficticios
* Noticias ficticias
* Llamadas de oyentes
* Música seleccionada automáticamente
* Efectos de sonido y transiciones

El resultado final es un archivo de audio listo para reproducirse dentro de:

* Farming Simulator 25
* Euro Truck Simulator 2
* Otros simuladores compatibles

---

# 3. Arquitectura General

```text
Frontend (Nuxt 4)
        │
        ▼
   Flask Backend
        │
 ┌──────┼──────────────┐
 ▼      ▼              ▼

Postgres  Music Library  Episode Library

        │
        ▼

 Generation Pipeline

    1. Curator
    2. Script Writer
    3. Voice Synthesizer
    4. Audio Mixer
    5. Episode Exporter
```

---

# 4. Módulos del Sistema

## 4.1 Music Library Manager

### Responsabilidades

* Escaneo de carpetas
* Indexación de MP3
* Lectura de metadatos
* Prevención de duplicados

### Funcionalidades

* Escaneo de carpetas de música configuradas por el usuario
* Indexación automática de archivos MP3 detectados
* Extracción y actualización de metadatos (título, artista, álbum, duración)
* Detección y prevención de archivos duplicados mediante hash
* Sincronización de cambios entre el sistema de archivos y la base de datos

---

## 4.2 Script Generation Engine

### Responsabilidades

Generar contenido estructurado para radio.

### Tipos de contenido

* Intro
* Intermedios
* Comerciales
* Noticias
* Llamadas
* Cierre

---

## 4.3 Voice Synthesis Engine

### Responsabilidades

Convertir guiones a audio.

### Roles soportados

| Rol        | Voz        |
| ---------- | ---------- |
| Host       | Principal  |
| Co-host    | Secundaria |
| Caller     | Variable   |
| Commercial | Variable   |
| Reporter   | Variable   |

---

## 4.4 Audio Production Engine

### Responsabilidades

Construcción final del episodio.

### Procesos

#### Ducking

Reduce volumen musical durante diálogos.

#### Telefonía

Filtro bandpass para llamadas.

#### Radio FX

* Static
* Jingles
* Sweepers
* Identificadores de estación

#### Loudness

Normalización LUFS.

---

## 4.5 Episode Manager

### Responsabilidades

* Guardar episodios
* Catalogar episodios
* Reproducir episodios
* Exportar episodios

---

# 6. Arquitectura de Generación por Agentes

La generación de contenido no se realizará mediante una única llamada a un modelo de lenguaje. El sistema utilizará un pipeline de agentes especializados que colaboran para construir cada episodio.

## Objetivos

* Mejorar la calidad narrativa.
* Permitir reutilización de contenido.
* Reducir costos de generación.
* Facilitar la incorporación de nuevas estaciones.
* Mantener coherencia entre episodios.

## Pipeline General

```text
Episode Request
       │
       ▼

Episode Planner Agent
       │
       ├─────────────┬─────────────┬─────────────┐
       ▼             ▼             ▼             ▼

News Agent   Commercial Agent   Character Agent   Host Agent

       └─────────────┴─────────────┴─────────────┘
                         │
                         ▼

                Episode Assembly Agent
                         │
                         ▼

                    Script JSON
```

## Agentes Iniciales

### Episode Planner Agent

Responsable de:

* Seleccionar la estación.
* Determinar duración objetivo.
* Seleccionar canciones.
* Definir estructura del episodio.
* Solicitar contenido a los demás agentes.

### News Agent

Responsable de:

* Generar boletines de noticias.
* Crear reportajes especiales.
* Generar titulares.
* Mantener continuidad temática.

Las noticias generadas se almacenan en una biblioteca reutilizable.

### Commercial Agent

Responsable de:

* Crear nuevas marcas ficticias.
* Generar campañas publicitarias.
* Generar variantes de anuncios existentes.
* Mantener coherencia de marca.

Los comerciales generados se almacenan en una biblioteca reutilizable.

### Character Agent

Responsable de:

* Gestionar personajes recurrentes.
* Generar llamadas de oyentes.
* Mantener memoria narrativa.
* Crear relaciones entre personajes.

### Host Agent

Responsable de:

* Introducciones.
* Transiciones.
* Comentarios editoriales.
* Presentaciones de canciones.

### Episode Assembly Agent

Responsable de:

* Integrar contenido generado.
* Construir el JSON final del episodio.
* Validar consistencia narrativa.
* Resolver referencias cruzadas.

---

# 7. Flujo de Generación

## Paso 1

Seleccionar canciones.

## Paso 2

Construir contexto.

Ejemplo:

```text
Canción 1
Canción 2
Canción 3

Personalidad:
Conspiranoico

Duración:
60 min
```

## Paso 3

Generar guión.

## Paso 4

Validar JSON.

## Paso 5

Generar voces.

## Paso 6

Aplicar efectos.

## Paso 7

Construir timeline.

## Paso 8

Exportar MP3 final.

## Paso 9

Registrar episodio.

---

# 8. Configuración de Estaciones

## Estilos Iniciales

### AgroTalk FM

Radio informativa y de opinión centrada en el mundo agrícola. Incluye noticias ficticias y reales inspiradas en Farming Simulator, entrevistas a agricultores, análisis de maquinaria, reportes de cosechas, tendencias del mercado y debates sobre tecnologías agrícolas.

### Trucker News Radio

Estación de noticias y talk radio enfocada en el transporte de carga y la logística. Presenta reportes inspirados en Euro Truck Simulator, novedades de rutas, regulaciones de transporte, entrevistas a camioneros, estado del tráfico y segmentos de opinión.

### SimNation News

Canal informativo general para simuladores. Combina noticias sobre Farming Simulator, Euro Truck Simulator y otros juegos de simulación, con análisis, reportajes especiales y comentarios de expertos ficticios.

### WCTR Sim Edition

Versión satírica inspirada en WCTR. Mezcla noticias absurdas, teorías conspirativas sobre la industria agrícola y del transporte, llamadas de oyentes extravagantes y comerciales ficticios.

### Radio Rural 24

Formato de noticias continuas con boletines periódicos, clima, precios de cultivos, novedades de maquinaria y cobertura de eventos agrícolas.

### Highway Talk Network

Programa de entrevistas y debate para conductores de larga distancia. Incluye llamadas de oyentes, historias de carretera, análisis de la industria logística y segmentos de actualidad.

### Custom

Definido por usuario. Puede configurarse para generar una radio informativa, de noticias, entrevistas, opinión o talk radio basada en Farming Simulator, Euro Truck Simulator u otras temáticas personalizadas.

---

# 9. Funcionalidades Pospuestas

Las capacidades de streaming y emisión continua quedan fuera del alcance del MVP y se evaluarán en futuras fases del proyecto según las necesidades y prioridades de desarrollo.

---

# 10. Sistema de Personajes

### Biblioteca de Personajes Recurrentes

```text
Nombre
Rol
Estación asociada
Descripción
Frecuencia de aparición
Relaciones con otros personajes
```

### Noticias

```text
Presentador
Tono informativo
Nivel de sensacionalismo
Temática principal
```

### Comerciales Recurrentes

```text
Marca ficticia
Producto
Eslogan
Universo compartido
Frecuencia de aparición
```

---

# 11. Biblioteca Compartida de Noticias

Las noticias no se generan para un episodio específico.

Se generan como contenido independiente reutilizable por múltiples estaciones.

## Objetivos

* Reducir llamadas al LLM.
* Crear sensación de mundo compartido.
* Permitir que diferentes estaciones comenten el mismo evento desde perspectivas distintas.

## Entidad NewsItem

```text
id
headline
summary
full_script
category
tone
created_at
expires_at
is_active
```

## Categorías Iniciales

* Agricultura
* Transporte
* Economía
* Tecnología
* Clima
* Comunidad
* Política Local
* Sucesos Extraños

## Ciclo de Vida

```text
Generación
    ↓
Biblioteca
    ↓
Selección por estaciones
    ↓
Presentación en episodios
    ↓
Archivado
```

## Ejemplo

Una noticia sobre:

"Escasez mundial de neumáticos para tractores"

puede aparecer en:

* AgroTalk FM
* Trucker News Radio
* SimNation News
* WCTR Sim Edition

Cada estación la presentará con su propio estilo narrativo.

---

# 12. Biblioteca Compartida de Comerciales

Los comerciales pertenecen al universo compartido de VirtualRadio.

No se generan específicamente para cada episodio.

## Objetivos

* Crear reconocimiento de marca.
* Reducir costos de generación.
* Construir continuidad narrativa.

## Entidad CommercialBrand

```text
id
name
description
industry
slogan
created_at
is_active
```

## Entidad Commercial

```text
id
brand_id
title
script
duration
campaign
created_at
is_active
```

## Ejemplos

### AgroFuel

Combustible para maquinaria agrícola.

### MegaHaul Logistics

Empresa ficticia de transporte.

### FarmNet

Proveedor ficticio de internet rural.

### TractorCoin

Criptomoneda absurda para agricultores.

## Reutilización

Los anuncios podrán:

* Repetirse entre episodios.
* Tener múltiples versiones.
* Evolucionar mediante campañas.
* Referenciar eventos del universo compartido.

---

# 13. Sistema de Memoria Narrativa

El universo de VirtualRadio mantiene continuidad entre episodios.

Los personajes, marcas y eventos pueden reaparecer y evolucionar con el tiempo.

## Objetivos

* Crear sensación de emisora real.
* Generar familiaridad con personajes.
* Construir historias de largo plazo.
* Permitir running gags.

## Entidad Character

```text
id
name
role
description
personality
station_affinity
first_appearance
last_appearance
```

## Entidad CharacterMemory

```text
id
character_id
memory
importance
episode_id
created_at
```

## Entidad StoryEvent

```text
id
title
description
related_characters
status
created_at
resolved_at
```

## Ejemplos

### Episodio 3

Juan compra un tractor usado.

### Episodio 8

Juan llama para quejarse del tractor.

### Episodio 16

Juan vende el tractor y culpa a una conspiración.

## Running Gags

El sistema podrá almacenar elementos recurrentes.

Ejemplos:

* Un tractor que siempre se descompone.
* Un camionero que siempre se pierde.
* Una marca ficticia demandada constantemente.
* Teorías conspirativas recurrentes.

---

# 14. Universo Compartido

Todos los elementos narrativos pertenecen a un mismo universo persistente.

## Componentes Compartidos

* Noticias
* Personajes
* Comerciales
* Empresas ficticias
* Eventos históricos
* Running gags

## Beneficios

* Mayor inmersión.
* Menor costo de generación.
* Mayor coherencia narrativa.
* Sensación de emisoras conectadas entre sí.

---

# 15. Prioridades del MVP

## Incluido

* Biblioteca musical
* Generación por agentes
* Biblioteca de noticias
* Biblioteca de comerciales
* Personajes recurrentes
* Memoria narrativa
* Exportación de episodios
* Múltiples estaciones

## Pospuesto

* Streaming continuo
* Emisión 24/7
* Clonación de voz
* Generación en tiempo real
* Integración Icecast
