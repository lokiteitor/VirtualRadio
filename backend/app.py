import os
import uuid
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from database import init_db, get_db_connection
from generator import ScriptGenerationEngine
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
@app.route('/api/characters', methods=['GET'])
def get_characters():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters ORDER BY name ASC")
    chars = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(chars)

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
    from generator import STATIONS
    if station not in STATIONS:
        return jsonify({"error": f"Invalid station. Must be one of: {list(STATIONS.keys())}"}), 400
        
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
