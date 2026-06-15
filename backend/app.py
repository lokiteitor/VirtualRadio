import os
import uuid
import threading
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import json
from database import init_db, get_db_connection
from generator import ScriptGenerationEngine, call_llm
from audio_engine import AudioProductionEngine, STATIC_DIR, MUSIC_DIR
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Enable CORS for the frontend port (Nuxt typically runs on 3000)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Ensure DB is initialized
init_db()

# In-memory job tracker for asynchronous episode generation
jobs = {}

def run_generation_pipeline(job_id, station):
    """Background thread function to generate and compile an episode."""
    conn = get_db_connection()
    try:
        jobs[job_id]["status"] = "Planning Script..."
        script_engine = ScriptGenerationEngine(conn)
        
        # 1. Plan & Generate Script JSON
        ep_id, title, script_json = script_engine.generate_episode(station)
        jobs[job_id]["episode_id"] = ep_id
        
        # 2. Synthesize & Mix Audio
        jobs[job_id]["status"] = "Synthesizing Voices..."
        audio_engine = AudioProductionEngine(conn)
        
        # Syncing library just in case
        audio_engine.sync_music_library()
        
        jobs[job_id]["status"] = "Mixing Audio & FX..."
        audio_path, duration = audio_engine.compile_episode(ep_id)
        
        jobs[job_id]["status"] = "Completed"
        jobs[job_id]["duration"] = duration
        jobs[job_id]["audio_url"] = f"http://localhost:5000/{audio_path}"
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Generation job {job_id} failed:\n{error_details}")
        jobs[job_id]["status"] = "Failed"
        jobs[job_id]["error"] = str(e)
    finally:
        conn.close()

# ----------------- STATIC SERVING -----------------
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serves the generated episodes, voices, and music."""
    return send_from_directory(STATIC_DIR, filename)

# ----------------- MUSIC ENDPOINTS -----------------
@app.route('/api/music', methods=['GET'])
def get_music():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM music_tracks ORDER BY title ASC")
    tracks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(tracks)

@app.route('/api/music/scan', methods=['POST'])
def scan_music():
    conn = get_db_connection()
    try:
        engine = AudioProductionEngine(conn)
        engine.sync_music_library()
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM music_tracks ORDER BY title ASC")
        tracks = [dict(row) for row in cursor.fetchall()]
        return jsonify({"message": "Scan completed", "tracks": tracks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/music/upload', methods=['POST'])
def upload_music():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if not file.filename.lower().endswith('.mp3'):
        return jsonify({"error": "Only MP3 files are allowed"}), 400
        
    try:
        # Secure the filename to avoid directory traversal exploits
        filename = secure_filename(file.filename)
        dest_path = os.path.join(MUSIC_DIR, filename)
        file.save(dest_path)
        
        # Sync with database
        conn = get_db_connection()
        engine = AudioProductionEngine(conn)
        engine.sync_music_library()
        
        # Query updated list of tracks
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM music_tracks ORDER BY title ASC")
        tracks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            "message": f"File '{filename}' successfully uploaded and indexed.",
            "tracks": tracks
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------- CHARACTER ENDPOINTS -----------------
@app.route('/api/characters', methods=['GET', 'POST'])
def handle_characters():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute("SELECT * FROM characters ORDER BY name ASC")
        chars = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(chars)
        
    elif request.method == 'POST':
        data = request.json
        if not data or not data.get("name") or not data.get("role") or not data.get("description") or not data.get("personality"):
            conn.close()
            return jsonify({"error": "name, role, description and personality are required"}), 400
            
        try:
            cursor.execute(
                "INSERT INTO characters (name, role, description, personality, station_affinity) VALUES (?, ?, ?, ?, ?)",
                (data["name"], data["role"], data["description"], data["personality"], data.get("station_affinity", "WCTR Sim Edition"))
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM characters WHERE id = ?", (new_id,))
            new_char = dict(cursor.fetchone())
            conn.close()
            return jsonify(new_char), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"error": "A character with that name already exists"}), 400
        except Exception as e:
            conn.close()
            return jsonify({"error": str(e)}), 500

@app.route('/api/characters/suggest', methods=['POST'])
def suggest_character():
    data = request.json or {}
    name = data.get("name")
    
    system_instruction = (
        "You are a creative writer for a simulation radio station. "
        "Your task is to generate details for a fictional character who could be a caller or regular guest on a simulation radio show. "
        "You must return ONLY a JSON object with the following fields: 'name', 'role', 'description', 'personality', and 'station_affinity'. "
        "Do not include markdown formatting or block quotes in the outer response. Return pure valid JSON only."
    )
    
    prompt = (
        "Generate details for a fictional character fitting a simulation radio setting (rural, farming, truck logistics, or general simulation humor).\n"
    )
    if name:
        prompt += f"The character's name must be exactly '{name}'.\n"
    else:
        prompt += "Create a catchy, authentic-sounding character name.\n"
        
    prompt += (
        "The 'role' should be their profession or background (e.g. 'Granjero jubilado', 'Conductora de cisternas', 'Mecánico de tractores').\n"
        "The 'description' should be a 1-2 sentence description of who they are and why they call or listen to the radio.\n"
        "The 'personality' should specify their speech traits or core obsession (e.g. 'Paranoico, habla rápido', 'Tranquilo, pausado, reflexivo').\n"
        "The 'station_affinity' should be a comma-separated list of 1 or 2 stations they listen to. Choose from: ['AgroTalk FM', 'Trucker News Radio', 'SimNation News', 'WCTR Sim Edition']."
    )
    
    response_text = None
    try:
        response_text = call_llm(prompt, system_instruction)
        if response_text:
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                else:
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
            char_data = json.loads(clean_text)
            if name:
                char_data["name"] = name
            return jsonify(char_data)
    except Exception as e:
        print(f"Error calling LLM or parsing response: {e}. Falling back to template generation.")

    # Fallback characters
    fallbacks = [
        {
            "name": name or "Gertrudis",
            "role": "Criadora de cabras / Escéptica de la tecnología",
            "description": "Una señora de campo que llama constantemente para culpar a las antenas de 5G por la repentina agresividad de sus cabras de ordeño.",
            "personality": "Obsesiva, testaruda, habla con refranes distorsionados.",
            "station_affinity": "WCTR Sim Edition, AgroTalk FM"
        },
        {
            "name": name or "Rafa 'El Rápido'",
            "role": "Repartidor de paquetería express",
            "description": "Un joven ansioso que conduce una furgoneta de reparto y afirma que la gravedad funciona diferente en los caminos de tierra.",
            "personality": "Hiperactivo, habla extremadamente rápido, paranoico con los límites de velocidad.",
            "station_affinity": "Trucker News Radio"
        },
        {
            "name": name or "Ingeniero Fritz",
            "role": "Especialista en tractores alemanes",
            "description": "Un ingeniero perfeccionista obsesionado con la calibración de válvulas y la eficiencia del motor que llama para corregir los comentarios técnicos del locutor.",
            "personality": "Frío, meticuloso, condescendiente, excesivamente técnico.",
            "station_affinity": "SimNation News, AgroTalk FM"
        },
        {
            "name": name or "Clara 'La Sonámbula'",
            "role": "Conductora nocturna de cisternas",
            "description": "Una conductora de larga distancia que asegura ver castillos medievales flotando sobre la carretera a partir de las 3 AM.",
            "personality": "Soñadora, mística, habla en susurros cansados.",
            "station_affinity": "Trucker News Radio, WCTR Sim Edition"
        }
    ]
    import random
    selected_fallback = random.choice(fallbacks)
    if name:
        selected_fallback["name"] = name
        
    return jsonify(selected_fallback)

@app.route('/api/characters/<int:char_id>/memories', methods=['GET'])
def get_character_memories(char_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cm.*, e.title as episode_title 
        FROM character_memories cm
        LEFT JOIN episodes e ON cm.episode_id = e.id
        WHERE cm.character_id = ? 
        ORDER BY cm.created_at DESC
    """, (char_id,))
    memories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(memories)

# ----------------- NEWS LIBRARY ENDPOINTS -----------------
@app.route('/api/news', methods=['GET', 'POST'])
def handle_news():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute("SELECT * FROM news_items ORDER BY created_at DESC")
        news = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(news)
        
    elif request.method == 'POST':
        data = request.json
        if not data or not data.get("headline") or not data.get("full_script"):
            conn.close()
            return jsonify({"error": "Headline and script are required"}), 400
            
        cursor.execute(
            "INSERT INTO news_items (headline, summary, full_script, category, tone) VALUES (?, ?, ?, ?, ?)",
            (data["headline"], data.get("summary", ""), data["full_script"], data.get("category", "General"), data.get("tone", "Informative"))
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM news_items WHERE id = ?", (new_id,))
        new_item = dict(cursor.fetchone())
        conn.close()
        return jsonify(new_item), 201

@app.route('/api/news/suggest', methods=['POST'])
def suggest_news():
    data = request.json or {}
    category = data.get("category")
    tone = data.get("tone")
    
    system_instruction = (
        "You are a creative writer for a simulation radio station. "
        "Your task is to generate a fictional news item for the game world (e.g. Farming Simulator, Euro Truck Simulator, etc.). "
        "You must return ONLY a JSON object with the following fields: 'headline', 'summary', 'category', 'tone', and 'full_script'. "
        "Do not include markdown formatting or block quotes in the outer response. Return pure valid JSON only."
    )
    
    prompt = (
        "Generate a fictional news item. "
        "The category should be one of: ['Agricultura', 'Transporte', 'Economía', 'Tecnología', 'Clima', 'Sucesos Extraños']. "
        "The tone should be one of: ['Sensacionalista', 'Misterioso', 'Absurdo', 'Serio']. "
    )
    if category:
        prompt += f"Use the category '{category}'. "
    if tone:
        prompt += f"Use the tone '{tone}'. "
        
    prompt += (
        "The 'headline' should be catchy and fitting the tone. "
        "The 'summary' should be a 1-sentence overview. "
        "The 'full_script' should be a 3-5 sentence complete script for a radio news reporter, ready to be read aloud (via Text-to-Speech)."
    )
    
    response_text = None
    try:
        response_text = call_llm(prompt, system_instruction)
        if response_text:
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                else:
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
            news_data = json.loads(clean_text)
            if "category" not in news_data or not news_data["category"]:
                news_data["category"] = category or "General"
            if "tone" not in news_data or not news_data["tone"]:
                news_data["tone"] = tone or "Informative"
            return jsonify(news_data)
    except Exception as e:
        print(f"Error calling LLM or parsing response: {e}. Falling back to template generation.")

    # Fallback to templates if LLM fails or keys are missing
    fallbacks = [
        {
            "headline": "¡Vacas locas hackean la central lechera!",
            "summary": "Un grupo de vacas modificadas cibernéticamente ha tomado el control de los dispensadores automatizados.",
            "category": "Sucesos Extraños",
            "tone": "Absurdo",
            "full_script": "Atención residentes de la zona rural. Informamos sobre una situación inusual en la Central Lechera Cooperativa. Varias vacas equipadas con implantes experimentales han hackeado el sistema de ordeño automático y ahora exigen un aumento del diez por ciento en su ración diaria de alfalfa orgánica. La policía local aconseja no acercarse a los establos y evitar el contacto visual con cualquier rumiante que lleve luces LED parpadeantes."
        },
        {
            "headline": "Embote de proporciones épicas en la Ruta 66",
            "summary": "Un camión cargado de patitos de goma gigantes vuelca bloqueando los tres carriles principales.",
            "category": "Transporte",
            "tone": "Sensacionalista",
            "full_script": "Última hora desde las carreteras. El tráfico está completamente paralizado en la Ruta Sesenta y Seis tras el vuelco de un mega-remolque de la empresa MegaHaul. El vehículo transportaba una carga experimental de patos de gama gigantes para parques acuáticos. Miles de patos amarillos de dos metros de altura bloquean ahora ambos sentidos de circulación. Varios camioneros informan que es imposible avanzar y que algunos están usando los patos como sillones inflables improvisados en mitad del asfalto."
        },
        {
            "headline": "Las lechugas gigantes amenazan la economía local",
            "summary": "Una supercosecha de lechugas mutantes desploma los precios del mercado regional.",
            "category": "Economía",
            "tone": "Serio",
            "full_script": "Buenos días. Informamos del colapso inminente del mercado agrícola. La introducción de un nuevo fertilizante experimental ha producido una cosecha de lechugas gigantes, cada una del tamaño de una casa pequeña. Aunque los agricultores celebraron el tamaño al principio, el exceso de oferta ha destruido el valor del vegetal. En el mercado local, una lechuga ahora se intercambia por medio centavo de TractorCoin. Se aconseja a los productores compostar el excedente antes de que las lechugas comiencen a rodar cuesta abajo hacia el pueblo."
        },
        {
            "headline": "Avistamiento de OVNIs sobre los silos de grano",
            "summary": "Misteriosas luces verdes en forma de espiral aparecen sobre los silos del pueblo.",
            "category": "Sucesos Extraños",
            "tone": "Misterioso",
            "full_script": "Misterio en los cielos rurales. Anoche, múltiples residentes reportaron un patrón de luces verdes en espiral flotando sobre los silos principales del pueblo. Según testigos presenciales, las luces permanecieron estáticas durante diez minutos antes de emitir un zumbido agudo y desaparecer instantáneamente hacia el norte. La agencia de seguridad nacional no ha emitido comentarios, pero los ufólogos locales sugieren que los visitantes espaciales podrían estar extremadamente interesados en las reservas de trigo de esta temporada."
        }
    ]
    import random
    options = [f for f in fallbacks if (not category or f["category"] == category) and (not tone or f["tone"] == tone)]
    if not options:
        options = [f for f in fallbacks if (not category or f["category"] == category)]
    if not options:
        options = [f for f in fallbacks if (not tone or f["tone"] == tone)]
    if not options:
        options = fallbacks
        
    selected_fallback = random.choice(options)
    # Overwrite category and tone if they were requested explicitly
    if category:
        selected_fallback["category"] = category
    if tone:
        selected_fallback["tone"] = tone
        
    return jsonify(selected_fallback)

# ----------------- COMMERCIAL ENDPOINTS -----------------
@app.route('/api/commercials', methods=['GET', 'POST'])
def handle_commercials():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute("""
            SELECT c.*, b.name as brand_name, b.slogan as brand_slogan, b.description as brand_desc 
            FROM commercials c 
            JOIN commercial_brands b ON c.brand_id = b.id 
            ORDER BY c.created_at DESC
        """)
        comms = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(comms)
        
    elif request.method == 'POST':
        data = request.json
        if not data or not data.get("brand_id") or not data.get("script") or not data.get("title"):
            conn.close()
            return jsonify({"error": "brand_id, title and script are required"}), 400
            
        cursor.execute(
            "INSERT INTO commercials (brand_id, title, script, duration, campaign) VALUES (?, ?, ?, ?, ?)",
            (data["brand_id"], data["title"], data["script"], data.get("duration", 30.0), data.get("campaign", "General"))
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.execute("""
            SELECT c.*, b.name as brand_name, b.slogan as brand_slogan 
            FROM commercials c 
            JOIN commercial_brands b ON c.brand_id = b.id 
            WHERE c.id = ?
        """, (new_id,))
        new_comm = dict(cursor.fetchone())
        conn.close()
        return jsonify(new_comm), 201

@app.route('/api/commercials/suggest', methods=['POST'])
def suggest_commercial():
    data = request.json or {}
    brand_id = data.get("brand_id")
    if not brand_id:
        return jsonify({"error": "brand_id is required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM commercial_brands WHERE id = ?", (brand_id,))
    brand_row = cursor.fetchone()
    conn.close()
    
    if not brand_row:
        return jsonify({"error": "Brand not found"}), 404
        
    brand = dict(brand_row)
    
    system_instruction = (
        "You are a creative writer for a simulation radio station. "
        "Your task is to generate a fictional commercial advertisement for a given brand. "
        "You must return ONLY a JSON object with the following fields: 'title', 'campaign', and 'script'. "
        "Do not include markdown formatting or block quotes in the outer response. Return pure valid JSON only."
    )
    
    prompt = (
        f"Generate a fictional commercial advertisement for the following brand:\n"
        f"Name: {brand['name']}\n"
        f"Industry: {brand.get('industry', 'Other')}\n"
        f"Slogan: {brand.get('slogan', '')}\n"
        f"Description: {brand.get('description', '')}\n\n"
        "The 'title' should be a catchy title for the advertisement.\n"
        "The 'campaign' should be a short name for this ad campaign.\n"
        "The 'script' should be a 3-5 sentence radio commercial script ready to be read by an announcer (via Text-to-Speech), "
        "keeping the tone energetic, fitting the brand, and including the brand slogan."
    )
    
    response_text = None
    try:
        response_text = call_llm(prompt, system_instruction)
        if response_text:
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                else:
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
            comm_data = json.loads(clean_text)
            return jsonify(comm_data)
    except Exception as e:
        print(f"Error calling LLM or parsing response: {e}. Falling back to template generation.")

    brand_name = brand["name"].lower()
    fallback_script = f"¿Buscas lo mejor en {brand.get('industry', 'el sector')}? {brand['name']} es la respuesta. {brand.get('description', '')} Recuerda nuestro lema: '{brand.get('slogan', '')}'. ¡No esperes más y visítanos hoy mismo!"
    fallback_title = f"Promo Especial {brand['name']}"
    fallback_campaign = "Campaña General"
    
    if "agrofuel" in brand_name:
        fallback_title = "AgroFuel Máxima Potencia"
        fallback_campaign = "Lanzamiento"
        fallback_script = "¿Cansado de que tu tractor eche humo negro al subir una colina de dos grados? Cámbiate a AgroFuel Max. Formulado con residuos de patata orgánica para darte pura potencia. AgroFuel: porque tus cultivos no se van a cosechar solos, y tu motor tampoco debería quejarse. Recuerda: ¡Mantén tu tractor rugiendo como un tigre cafeinado!"
    elif "megahaul" in brand_name:
        fallback_title = "Conductores MegaHaul al Volante"
        fallback_campaign = "Reclutamiento 2026"
        fallback_script = "¿Te gusta el café? ¿Te gusta mirar el asfalto durante setenta y dos horas seguidas? MegaHaul Logistics está contratando. Ofrecemos sueldo competitivo y un termo de café gratis. MegaHaul: si cabe, lo llevamos; si no cabe, lo arrastramos."
    elif "farmnet" in brand_name:
        fallback_title = "FarmNet Velocidad Rural Extrema"
        fallback_campaign = "Promo de Verano"
        fallback_script = "¿Se avecina tormenta? Despídete de tu internet. Pero en los días soleados, experimenta la velocidad de FarmNet. Conectándote al mundo, eventualmente. Es mejor que hablar con tus vacas."
    elif "tractorcoin" in brand_name:
        fallback_title = "El Hype de TractorCoin"
        fallback_campaign = "Revolución Cripto"
        fallback_script = "¿Por qué invertir en oro cuando puedes invertir en TractorCoin? La única criptomoneda minada al operar tu cosechadora a las tres de la mañana. TractorCoin: ara tus ahorros y siémbralos en suelo digital."
        
    return jsonify({
        "title": fallback_title,
        "campaign": fallback_campaign,
        "script": fallback_script
    })

@app.route('/api/brands/suggest', methods=['POST'])
def suggest_brand():
    data = request.json or {}
    name = data.get("name")
    
    system_instruction = (
        "You are a creative writer for a simulation radio station. "
        "Your task is to generate details for a fictional company/brand. "
        "You must return ONLY a JSON object with the following fields: 'name', 'slogan', 'industry', and 'description'. "
        "Do not include markdown formatting or block quotes in the outer response. Return pure valid JSON only."
    )
    
    prompt = "Generate details for a fictional company/brand fitting a simulation setting (rural, farming, truck logistics, or general simulation humor).\n"
    if name:
        prompt += f"The company name must be exactly '{name}'.\n"
    else:
        prompt += "Create a catchy company name.\n"
        
    prompt += (
        "The 'slogan' should be a funny corporate slogan.\n"
        "The 'industry' should be a single word or short phrase (e.g. 'Agricultura', 'Transporte', 'Tecnología', 'Alimentos', 'Cosméticos').\n"
        "The 'description' should be a 1-2 sentence description of what the company does, matching the absurd humor of the game universe."
    )
    
    response_text = None
    try:
        response_text = call_llm(prompt, system_instruction)
        if response_text:
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                else:
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
            brand_data = json.loads(clean_text)
            if name:
                brand_data["name"] = name
            return jsonify(brand_data)
    except Exception as e:
        print(f"Error calling LLM or parsing response: {e}. Falling back to template generation.")

    # Fallback brands
    fallbacks = [
        {
            "name": name or "GigaFertilizer",
            "slogan": "Si no brilla en la oscuridad, no es nuestro fertilizante.",
            "industry": "Agricultura",
            "description": "Fabricantes del fertilizante número uno enriquecido con uranio de baja intensidad para acelerar la madurez de los tomates."
        },
        {
            "name": name or "Sleepless Logistics",
            "slogan": "Dormir es para aficionados, entregar es nuestro destino.",
            "industry": "Transporte",
            "description": "Una empresa de mensajería urgente que obliga a sus conductores a beber cinco litros de café por turno para garantizar entregas en tiempo récord."
        },
        {
            "name": name or "Cabras.Net",
            "slogan": "La red de fibra óptica impulsada por ganado caprino.",
            "industry": "Tecnología",
            "description": "Ofrecemos internet de banda ancha rural conectando rúters directamente a los cuernos de cabras montesas en puntos de alta elevación."
        },
        {
            "name": name or "Sodapop Sim",
            "slogan": "El refresco con sabor a combustible sintético.",
            "industry": "Bebidas",
            "description": "Una bebida gaseosa sumamente energizante que sabe sospechosamente a diésel pero que mantiene a los camioneros despiertos."
        }
    ]
    import random
    selected_fallback = random.choice(fallbacks)
    if name:
        selected_fallback["name"] = name
        
    return jsonify(selected_fallback)

@app.route('/api/commercials/brands', methods=['GET', 'POST'])
def handle_brands():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute("SELECT * FROM commercial_brands ORDER BY name ASC")
        brands = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(brands)
        
    elif request.method == 'POST':
        data = request.json
        if not data or not data.get("name") or not data.get("description"):
            conn.close()
            return jsonify({"error": "name and description are required"}), 400
            
        try:
            cursor.execute(
                "INSERT INTO commercial_brands (name, description, industry, slogan) VALUES (?, ?, ?, ?)",
                (data["name"], data["description"], data.get("industry", "Other"), data.get("slogan", ""))
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM commercial_brands WHERE id = ?", (new_id,))
            new_brand = dict(cursor.fetchone())
            conn.close()
            return jsonify(new_brand), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"error": "A brand with that name already exists"}), 400

@app.route('/api/stations', methods=['GET', 'POST'])
def handle_stations():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute("SELECT * FROM stations ORDER BY name ASC")
        rows = cursor.fetchall()
        conn.close()
        
        stations_dict = {}
        for row in rows:
            stations_dict[row["name"]] = {
                "freq": row["frequency"],
                "emoji": row["emoji"],
                "host": row["host_name"],
                "style": row["personality"],
                "desc": row["description"],
                "color": row["color"],
                "intro_templates": json.loads(row["intro_templates"] or "[]"),
                "outro_templates": json.loads(row["outro_templates"] or "[]")
            }
        return jsonify(stations_dict)
        
    elif request.method == 'POST':
        data = request.json
        if not data or not data.get("name") or not data.get("host_name") or not data.get("description") or not data.get("personality"):
            conn.close()
            return jsonify({"error": "name, host_name, description and personality are required"}), 400
            
        try:
            intro = data.get("intro_templates") or [
                f"¡Hola a todos! Bienvenidos a {data['name']} con {data['host_name']}.",
                f"Estás en sintonía de {data['name']}. Aquí {data['host_name']} transmitiendo en vivo."
            ]
            outro = data.get("outro_templates") or [
                f"Eso es todo por hoy en {data['name']}. Se despide {data['host_name']}.",
                f"¡Nos vemos en la próxima transmisión de {data['name']}! Adiós."
            ]
            
            cursor.execute(
                "INSERT INTO stations (name, host_name, description, personality, frequency, emoji, color, intro_templates, outro_templates) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (data["name"], data["host_name"], data["description"], data["personality"], data.get("frequency", "99.9 FM"), data.get("emoji", "📻"), data.get("color", "#d97706"), json.dumps(intro), json.dumps(outro))
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM stations WHERE id = ?", (new_id,))
            row = dict(cursor.fetchone())
            conn.close()
            
            new_station = {
                "freq": row["frequency"],
                "emoji": row["emoji"],
                "host": row["host_name"],
                "style": row["personality"],
                "desc": row["description"],
                "color": row["color"],
                "intro_templates": json.loads(row["intro_templates"] or "[]"),
                "outro_templates": json.loads(row["outro_templates"] or "[]")
            }
            return jsonify(new_station), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"error": "A station with that name already exists"}), 400
        except Exception as e:
            conn.close()
            return jsonify({"error": str(e)}), 500

@app.route('/api/stations/suggest', methods=['POST'])
def suggest_station():
    data = request.json or {}
    name = data.get("name")
    
    system_instruction = (
        "You are a creative writer for a simulation radio station. "
        "Your task is to generate details for a new fictional radio station. "
        "You must return ONLY a JSON object with the following fields: 'name', 'host_name', 'description', 'personality', 'frequency', 'emoji', 'color', 'intro_templates', and 'outro_templates'. "
        "Do not include markdown formatting or block quotes in the outer response. Return pure valid JSON only."
    )
    
    prompt = (
        "Generate details for a new fictional radio station fitting a simulation setting (rural, farming, truck logistics, or general simulation humor).\n"
    )
    if name:
        prompt += f"The station name must be exactly '{name}'.\n"
    else:
        prompt += "Create a catchy, authentic-sounding radio station name.\n"
        
    prompt += (
        "The 'host_name' should be a single name for the announcer.\n"
        "The 'description' should be a 1-sentence description of the radio station style.\n"
        "The 'personality' should specify the announcer's speech traits or obsession (e.g. 'Rustic, proud farmer...', 'Paranoid...').\n"
        "The 'frequency' should be a random FM frequency (e.g. '102.4 FM').\n"
        "The 'emoji' should be a single matching emoji.\n"
        "The 'color' should be a hex color code (e.g. '#10b981').\n"
        "The 'intro_templates' should be a list of 2 strings representing radio introductions spoken by the announcer.\n"
        "The 'outro_templates' should be a list of 2 strings representing radio outro lines spoken by the announcer."
    )
    
    response_text = None
    try:
        response_text = call_llm(prompt, system_instruction)
        if response_text:
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                else:
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
            station_data = json.loads(clean_text)
            if name:
                station_data["name"] = name
            return jsonify(station_data)
    except Exception as e:
        print(f"Error calling LLM or parsing response: {e}. Falling back to template generation.")

    # Fallback station
    fallbacks = [
        {
            "name": name or "Radio Tequila 100",
            "host_name": "Pancho",
            "description": "Estación de música ranchera y debates sobre la fermentación del agave.",
            "personality": "Cheerful, enthusiastic, loves Mexican folk music and spicy food.",
            "frequency": "100.5 FM",
            "emoji": "🌵",
            "color": "#d97706",
            "intro_templates": [
                "¡Ajúa! Bienvenidos a Radio Tequila Cien. Les saluda su compa Pancho. ¡Afínquense que hoy viene música de la buena!",
                "Aquí Pancho reportándose en la cabina de Radio Tequila Cien. Pónganse cómodos y disfruten del mariachi."
            ],
            "outro_templates": [
                "¡Eso fue todo en Radio Tequila Cien! Pancho les dice adiós. ¡Salud y nos vemos!",
                "Nos vamos, pero volveremos con más picante y música mexicana. Pancho fuera."
            ]
        },
        {
            "name": name or "Space Rock FM",
            "host_name": "Nova",
            "description": "Estación espacial de rock progresivo y sonidos cósmicos.",
            "personality": "Calm, cosmic traveler, believes the stars are vibrating at high rock frequencies.",
            "frequency": "108.0 FM",
            "emoji": "🚀",
            "color": "#8b5cf6",
            "intro_templates": [
                "Transmitiendo desde la órbita baja de la simulación. Les habla Nova para Space Rock FM. Ajusten sus auriculares espaciales.",
                "Bienvenidos a la órbita sónica de Space Rock FM. Nova al micrófono. El viaje comienza ahora."
            ],
            "outro_templates": [
                "Nova apaga el transmisor cósmico por hoy. Sigan viajando por el espacio profundo de la música.",
                "Esto es todo desde la constelación del rock. Corto y cierro desde Space Rock FM."
            ]
        }
    ]
    import random
    selected_fallback = random.choice(fallbacks)
    if name:
        selected_fallback["name"] = name
        
    return jsonify(selected_fallback)

# ----------------- EPISODE ENDPOINTS -----------------
@app.route('/api/episodes', methods=['GET'])
def get_episodes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM episodes ORDER BY created_at DESC")
    episodes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(episodes)

@app.route('/api/episodes/<int:ep_id>', methods=['DELETE'])
def delete_episode(ep_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Find path to delete MP3
    cursor.execute("SELECT audio_path FROM episodes WHERE id = ?", (ep_id,))
    res = cursor.fetchone()
    if res and res["audio_path"]:
        file_path = os.path.join(BACKEND_DIR, res["audio_path"])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error removing episode file: {e}")
                
    cursor.execute("DELETE FROM episodes WHERE id = ?", (ep_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Episode {ep_id} deleted successfully"})

@app.route('/api/episodes/generate', methods=['POST'])
def generate_episode_api():
    """Triggers asynchronous episode generation."""
    data = request.json or {}
    station = data.get("station", "WCTR Sim Edition")
    
    # Verify station exists
    conn = get_db_connection()
    try:
        from generator import ScriptGenerationEngine
        script_engine = ScriptGenerationEngine(conn)
        stations = script_engine.get_stations()
    finally:
        conn.close()
        
    if station not in stations:
        return jsonify({"error": f"Invalid station. Must be one of: {list(stations.keys())}"}), 400
        
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "Starting...",
        "station": station,
        "episode_id": None,
        "error": None
    }
    
    # Spin up background thread
    # SQLite connection is created inside the thread to satisfy single-thread requirements
    t = threading.Thread(target=run_generation_pipeline, args=(job_id, station))
    t.start()
    
    return jsonify({"job_id": job_id, "status": "Queued"})

@app.route('/api/jobs/<string:job_id>', methods=['GET'])
def get_job_status(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(jobs[job_id])

# ----------------- SERVER BOOT -----------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
