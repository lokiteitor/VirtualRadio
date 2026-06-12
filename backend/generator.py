import json
import os
import random
import sqlite3
import requests
from datetime import datetime
from database import get_db_connection

# Try to get API keys from environment
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

STATIONS = {
    "AgroTalk FM": {
        "host_name": "Clem",
        "description": "Radio informativa y de opinión centrada en el mundo agrícola.",
        "personality": "Rustic, proud farmer, obsessed with fertilizer prices, machinery, and weather.",
        "intro_templates": [
            "¡Buenos días, agricultores! Aquí Clem en AgroTalk FM. Sacudan el barro de sus botas porque hoy tenemos un programa cargado de nitrógeno y verdades como puños.",
            "Bienvenidos de nuevo a AgroTalk FM, la única emisora que huele a estiércol fresco y trabajo duro. Soy Clem, y hoy hablaremos del precio de las cosechadoras."
        ],
        "outro_templates": [
            "Eso es todo por hoy en AgroTalk FM. Recuerden: si el tractor hace un ruido raro, pisen el acelerador más fuerte. Habló Clem, nos vemos en el campo.",
            "Clem se despide de AgroTalk FM. Vuelvan a sus tractores, rieguen sus plantas y vigilen a sus vecinos. ¡Hasta la próxima, labradores!"
        ]
    },
    "Trucker News Radio": {
        "host_name": "Diesel Dan",
        "description": "Estación de noticias y talk radio enfocada en el transporte de carga y la logística.",
        "personality": "Deep-voiced, road-weary, drinks too much coffee, speaks in trucker slang (10-4, copy that).",
        "intro_templates": [
            "Aquí Diesel Dan en la frecuencia de Trucker News Radio. Para todos los que devoran asfalto a esta hora, mantengan los ojos abiertos y la cafetera encendida.",
            "Saludos, nómadas de la carretera. Les habla Diesel Dan. Ajusten sus espejos, pongan quinta marcha y acompáñenme en este viaje de noticias y diésel."
        ],
        "outro_templates": [
            "Diesel Dan fuera. Mantengan las ruedas girando y los radares vigilados. Nos leemos en la próxima parada de camiones. 10-4.",
            "Eso es todo desde la cabina de Trucker News Radio. Conduzcan con cuidado y no coman los burritos de la estación de servicio de la salida 4. Corto y cierro."
        ]
    },
    "SimNation News": {
        "host_name": "Audrey Vance",
        "description": "Canal informativo general para simuladores.",
        "personality": "Crisp, professional, highly articulated news anchor, takes trivial simulation events extremely seriously.",
        "intro_templates": [
            "Muy buenas tardes. Les saluda Audrey Vance para SimNation News, transmitiendo las noticias más relevantes de la comunidad de simulación global.",
            "Bienvenidos a la emisión de SimNation News. Les acompaña Audrey Vance. Analizaremos en detalle el impacto del último parche de rendimiento y el estado de la economía local."
        ],
        "outro_templates": [
            "Gracias por su sintonía. Les ha informado Audrey Vance para SimNation News. Manténganse informados y sigan simulando con responsabilidad.",
            "Esto concluye nuestro boletín. Soy Audrey Vance. Recuerden que la realidad es solo otra simulación que no podemos reiniciar. Buenas noches."
        ]
    },
    "WCTR Sim Edition": {
        "host_name": "Richard 'Dick' Brainwave",
        "description": "Versión satírica inspirada en WCTR con teorías conspirativas y locura rural.",
        "personality": "Highly energetic, paranoid, believes the government is using crop circles to communicate with Martian cows, speaks in frantic bursts.",
        "intro_templates": [
            "¡DESPIERTEN, OVEJAS! Soy Dick Brainwave en WCTR Sim Edition. Hoy les revelaré cómo las corporaciones de tractores están insertando microchips en las semillas de trigo.",
            "¡Están escuchando la verdad cruda en WCTR Sim Edition con Dick Brainwave! ¿Es el GPS de su camión una sonda alienígena? Spoiler: ¡SÍ LO ES!"
        ],
        "outro_templates": [
            "La verdad está ahí fuera, pero probablemente esté censurada por el lobby del compost. Dick Brainwave se despide. ¡No miren directamente a los espantapájaros!",
            "¡Apaguen sus teléfonos! ¡Quemen sus manuales de conductor! Dick Brainwave les dice adiós desde el búnker de WCTR. ¡Ellos nos están escuchando!"
        ]
    }
}

def call_llm(prompt, system_instruction):
    """
    Tries to call Gemini or OpenRouter LLM APIs.
    Falls back to None if keys are missing or requests fail.
    """
    if GEMINI_API_KEY:
        try:
            # Simple Gemini API call using requests
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"System Instruction: {system_instruction}\n\nUser Request: {prompt}"}]}
                ]
            }
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Gemini API failed: {e}. Falling back...")
            
    if OPENROUTER_API_KEY:
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "google/gemini-2.5-flash",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ]
            }
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"OpenRouter API failed: {e}. Falling back...")
            
    return None

class ScriptGenerationEngine:
    def __init__(self, db_conn):
        self.conn = db_conn

    def get_random_tracks(self, limit=3):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM music_tracks ORDER BY RANDOM() LIMIT ?", (limit,))
        tracks = cursor.fetchall()
        if not tracks:
            # Generate mock track data if library is empty
            return [
                {"id": 1, "title": "Stardew Valley Country Road", "artist": "The Pixels", "duration": 180.0, "file_path": "mock_1.mp3"},
                {"id": 2, "title": "Highway to Trucking", "artist": "Overdrive", "duration": 210.0, "file_path": "mock_2.mp3"},
                {"id": 3, "title": "Combine Harvester Blues", "artist": "The Silos", "duration": 195.0, "file_path": "mock_3.mp3"}
            ]
        return [dict(track) for track in tracks]

    def get_news_item(self, station):
        cursor = self.conn.cursor()
        # Find active news items
        cursor.execute("SELECT * FROM news_items WHERE is_active = 1 ORDER BY RANDOM() LIMIT 1")
        news = cursor.fetchone()
        if not news:
            return {
                "headline": "Clima Extremo Amenaza Cosechas",
                "summary": "Una lluvia de sapos de goma ha ralentizado los tractores en la zona este.",
                "full_script": "Los sapos rebotan en el parabrisas y dificultan la labranza.",
                "category": "Clima",
                "tone": "Absurdo"
            }
        return dict(news)

    def get_commercial(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.*, b.name as brand_name, b.slogan as brand_slogan, b.description as brand_desc 
            FROM commercials c 
            JOIN commercial_brands b ON c.brand_id = b.id 
            WHERE c.is_active = 1 AND b.is_active = 1
            ORDER BY RANDOM() LIMIT 1
        """)
        comm = cursor.fetchone()
        if not comm:
            return {
                "brand_name": "AgroFuel",
                "title": "AgroFuel Max",
                "script": "¡Usa AgroFuel y tu tractor volará!",
                "duration": 30.0
            }
        return dict(comm)

    def get_character_and_memories(self, station):
        cursor = self.conn.cursor()
        # Select characters that might fit the station
        cursor.execute("SELECT * FROM characters")
        all_chars = [dict(c) for c in cursor.fetchall()]
        if not all_chars:
            return None, []
            
        # Try to filter by station affinity
        matching_chars = [c for c in all_chars if station in c["station_affinity"] or "WCTR" in c["station_affinity"]]
        selected_char = random.choice(matching_chars) if matching_chars else random.choice(all_chars)
        
        # Fetch their memories
        cursor.execute("SELECT * FROM character_memories WHERE character_id = ? ORDER BY created_at DESC LIMIT 3", (selected_char["id"],))
        memories = [dict(m) for m in cursor.fetchall()]
        
        return selected_char, memories

    def save_character_memory(self, character_id, memory_text, episode_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO character_memories (character_id, memory, episode_id) VALUES (?, ?, ?)",
            (character_id, memory_text, episode_id)
        )
        cursor.execute(
            "UPDATE characters SET last_appearance = CURRENT_TIMESTAMP WHERE id = ?",
            (character_id,)
        )

    def generate_episode(self, station, duration_mins=15):
        if station not in STATIONS:
            station = "WCTR Sim Edition"
            
        station_info = STATIONS[station]
        host_name = station_info["host_name"]
        
        # 1. Episode Planner Agent
        tracks = self.get_random_tracks(limit=3)
        news_item = self.get_news_item(station)
        commercial = self.get_commercial()
        character, memories = self.get_character_and_memories(station)
        
        episode_title = f"{station} - Episodio {random.randint(100, 999)}"
        
        # Build prompt for LLM or procedural generation
        # Let's try calling LLM first
        llm_success = False
        script_json = None
        
        prompt = f"""
        Generate a complete audio show script for the fictional radio station "{station}".
        Host Name: {host_name}
        Host Personality: {station_info['personality']}
        
        Content elements to include:
        1. News Item: Headline: "{news_item['headline']}". Summary: "{news_item['summary']}". The host or a reporter should present this news with the station's characteristic tone.
        2. Commercial: Brand: "{commercial['brand_name']}". Product script to read: "{commercial['script']}".
        3. Caller Interaction:
           Caller Name: {character['name'] if character else 'Anon'}
           Caller Role/Description: {character['description'] if character else 'A listener'}
           Caller Personality: {character['personality'] if character else 'Excited'}
           Caller Memories/Context: {[m['memory'] for m in memories] if memories else 'None'}
           Create a funny phone dialogue where this caller calls the station. The caller should mention or reference their memories. The host responds.
        4. Play 3 songs (Music segments). Introduce each song.
        
        Generate the output strictly as a JSON list of segments. Do not include markdown code block formatting like ```json ... ```, just the raw JSON.
        Each segment must have:
        - "type": "speech", "music", or "fx"
        - "speaker": "Host", "Caller", "Reporter", "Commercial_Voice", or null (for music/fx)
        - "text": The spoken text or script, or song title for music
        - "voice_id": "host", "caller", "reporter", "commercial", or null
        - "effect": "telephony" (for callers), "ducking" (for speech during music), or null
        - "track_id": The index of the song (0, 1, or 2) if type is music, otherwise null.
        - "duration_seconds": estimate duration (speech ~ 150 words per minute).
        
        Songs to include:
        - Song 0: "{tracks[0]['title']}" by {tracks[0]['artist']}
        - Song 1: "{tracks[1]['title']}" by {tracks[1]['artist']}
        - Song 2: "{tracks[2]['title']}" by {tracks[2]['artist']}
        """
        
        system_instruction = "You are a professional script writer for a satirical radio generator. You write funny, immersive radio scripts and output them strictly in JSON format."
        
        llm_response = call_llm(prompt, system_instruction)
        if llm_response:
            try:
                # Clean code blocks if present
                clean_text = llm_response.strip()
                if clean_text.startswith("```"):
                    clean_text = clean_text.split("```")[1]
                    if clean_text.startswith("json"):
                        clean_text = clean_text[4:]
                script_json = json.loads(clean_text)
                llm_success = True
                print("LLM successfully generated the script.")
            except Exception as e:
                print(f"Error parsing LLM JSON: {e}. Falling back to procedural generation.")
                
        if not llm_success:
            # Procedural script generator (Highly detailed fallback!)
            script_json = self.procedural_script(station, host_name, tracks, news_item, commercial, character, memories)
            
        # Save episode to DB to get its ID
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO episodes (title, station, duration, script_json, audio_path) VALUES (?, ?, ?, ?, ?)",
            (episode_title, station, 0.0, json.dumps(script_json), "")
        )
        episode_id = cursor.lastrowid
        
        # Save character memory if character was involved
        if character:
            # Generate a new memory based on the interaction
            # Let's extract caller dialogues to summarize the interaction
            caller_lines = [seg["text"] for seg in script_json if seg.get("speaker") == "Caller"]
            if caller_lines:
                summary_memory = f"Llamó a {station} para hablar sobre: {caller_lines[0][:100]}..."
                self.save_character_memory(character["id"], summary_memory, episode_id)
                
        self.conn.commit()
        return episode_id, episode_title, script_json

    def procedural_script(self, station, host_name, tracks, news_item, commercial, character, memories):
        """Generates a high-quality satirical script procedurally based on template structures."""
        segments = []
        
        # Intro
        intro_text = random.choice(STATIONS[station]["intro_templates"])
        intro_text += f" Hoy escucharemos buena música, como a {tracks[0]['artist']} con su temazo '{tracks[0]['title']}'. Pero primero, ¡vamos a la música!"
        segments.append({
            "type": "speech",
            "speaker": "Host",
            "text": intro_text,
            "voice_id": "host",
            "effect": None,
            "duration_seconds": 15
        })
        
        # Song 1
        segments.append({
            "type": "music",
            "speaker": None,
            "text": f"{tracks[0]['title']} - {tracks[0]['artist']}",
            "voice_id": None,
            "effect": None,
            "track_id": 0,
            "duration_seconds": 45  # Play short preview snippet for prototype
        })
        
        # Transition & News
        transition_news = f"Ah, ¡qué gran tema de {tracks[0]['artist']}! De vuelta al micrófono, soy {host_name}. Vamos directo con las noticias de la hora. Nos reportan lo siguiente..."
        segments.append({
            "type": "speech",
            "speaker": "Host",
            "text": transition_news,
            "voice_id": "host",
            "effect": None,
            "duration_seconds": 10
        })
        
        # News Report
        news_reporter_script = f"Reportando para {station}, soy el Corresponsal Virtual. {news_item['full_script']}"
        segments.append({
            "type": "speech",
            "speaker": "Reporter",
            "text": news_reporter_script,
            "voice_id": "reporter",
            "effect": None,
            "duration_seconds": 25
        })
        
        # Host reaction to news
        host_reaction = ""
        if station == "WCTR Sim Edition":
            host_reaction = "¡Lo sabía! ¡El Cheddar gigante es solo la fase uno del plan espacial alienígena! No se dejen engañar. Vamos a unos patrocinadores rápidos..."
        elif station == "AgroTalk FM":
            host_reaction = "Increíble. Cuidado con los neumáticos, amigos. No queremos que terminen usando queso para labrar el campo. Escuchemos este mensaje comercial..."
        elif station == "Trucker News Radio":
            host_reaction = "Vaya lío en la carretera. Pink fog y arpas... Suena a que alguien fumó algo raro en la gasolinera. Ojo al parche, camioneros. Y ahora, publicidad."
        else:
            host_reaction = "Un reporte preocupante para nuestra economía agrícola. Volvemos tras una breve pausa comercial."
            
        segments.append({
            "type": "speech",
            "speaker": "Host",
            "text": host_reaction,
            "voice_id": "host",
            "effect": None,
            "duration_seconds": 12
        })
        
        # Commercial
        segments.append({
            "type": "speech",
            "speaker": "Commercial_Voice",
            "text": f"Patrocinador de hoy: {commercial['brand_name']}. {commercial['script']}",
            "voice_id": "commercial",
            "effect": None,
            "duration_seconds": 20
        })
        
        # Song 2 intro
        segments.append({
            "type": "speech",
            "speaker": "Host",
            "text": f"De regreso. Y ahora es momento de relajarnos un poco con buena música en el dial. Aquí tienen a {tracks[1]['artist']} interpretando '{tracks[1]['title']}'. ¡Disfrútenla!",
            "voice_id": "host",
            "effect": None,
            "duration_seconds": 10
        })
        
        # Song 2
        segments.append({
            "type": "music",
            "speaker": None,
            "text": f"{tracks[1]['title']} - {tracks[1]['artist']}",
            "voice_id": None,
            "effect": None,
            "track_id": 1,
            "duration_seconds": 45
        })
        
        # Caller segment intro
        segments.append({
            "type": "speech",
            "speaker": "Host",
            "text": f"¡Qué buen ritmo! Soy {host_name} y abrimos las líneas telefónicas. Tenemos una llamada al aire. Hola, ¿quién habla?",
            "voice_id": "host",
            "effect": None,
            "duration_seconds": 8
        })
        
        # Caller interaction
        char_name = character["name"] if character else "Silas"
        char_personality = character["personality"] if character else "Grumpiest"
        
        caller_script = ""
        host_response = ""
        
        if char_name == "Juan":
            caller_script = "¡Clem! ¡Soy Juan! Te llamo desde la cabina del tractor. ¡Están volando helicópteros negros sobre mi plantación de remolachas! ¡Y el tractor me está dando descargas eléctricas cada vez que sintonizo tu programa! ¡Hay un complot en las ondas!"
            host_response = "Tranquilo, Juan. Asegúrate de envolver el radiador en papel de aluminio, eso debería cortar la señal espía. ¡Gracias por llamar!"
        elif char_name == "Old Man Silas":
            caller_script = "¡Hola! ¿Es aquí donde uno se queja del ruido de los camiones? Ese tarado de Juan pasó con su tractor haciendo un ruido infernal a las cuatro de la mañana. ¡Y me debe dos cajas de sidra! ¡Díselo por la radio, Clem!"
            host_response = "Mensaje recibido, Silas. Juan, si estás escuchando, págale la sidra al viejo Silas. Vamos a evitar guerras vecinales."
        elif char_name == "Big Rig Bob":
            caller_script = "Buenas noches, emisora. Habla Big Rig Bob. Estoy cruzando el desfiladero y la noche está muy despejada. Solo quería mandar un saludo a los muchachos de la ruta. Y ojo con la niebla rosa de la autopista 9, ¡parece que se mueve sola!"
            host_response = "Gracias, Bob. Conduce con cuidado y mantén ese camión estable. Un saludo de vuelta para ti."
        elif char_name == "Cynthia":
            caller_script = "¡Hola! Llamo porque el gallo mecánico del vecino no para de sonar y mi lavanda orgánica está estresada. ¡El estrés de las plantas reduce su aroma un quince por ciento! Alguien tiene que intervenir."
            host_response = "Entendido, Cynthia. Haremos un llamado a los dueños de aves mecánicas para que calmen sus sensores. Gracias por tu reporte."
        else:
            caller_script = "Hola, hola. Solo llamaba para reportar que mi tractor va perfecto gracias a AgroFuel. Saludos a toda la audiencia."
            host_response = "¡Eso es lo que nos gusta escuchar! Gracias por llamar, amigo."
            
        segments.append({
            "type": "speech",
            "speaker": "Caller",
            "text": caller_script,
            "voice_id": "caller",
            "effect": "telephony",
            "duration_seconds": 20
        })
        
        segments.append({
            "type": "speech",
            "speaker": "Host",
            "text": host_response,
            "voice_id": "host",
            "effect": None,
            "duration_seconds": 12
        })
        
        # Song 3 intro
        segments.append({
            "type": "speech",
            "speaker": "Host",
            "text": f"Interesante llamada. Es hora de la última canción del bloque de hoy. Con ustedes, {tracks[2]['artist']} y '{tracks[2]['title']}'. Regresamos para la despedida.",
            "voice_id": "host",
            "effect": None,
            "duration_seconds": 10
        })
        
        # Song 3
        segments.append({
            "type": "music",
            "speaker": None,
            "text": f"{tracks[2]['title']} - {tracks[2]['artist']}",
            "voice_id": None,
            "effect": None,
            "track_id": 2,
            "duration_seconds": 45
        })
        
        # Outro
        outro_text = random.choice(STATIONS[station]["outro_templates"])
        segments.append({
            "type": "speech",
            "speaker": "Host",
            "text": outro_text,
            "voice_id": "host",
            "effect": None,
            "duration_seconds": 12
        })
        
        return segments

if __name__ == "__main__":
    # Test script generation
    conn = get_db_connection()
    engine = ScriptGenerationEngine(conn)
    ep_id, title, script = engine.generate_episode("AgroTalk FM")
    print(f"Generated episode: {title}")
    print(json.dumps(script[:3], indent=2))
    conn.close()
