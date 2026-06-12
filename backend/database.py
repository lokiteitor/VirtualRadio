import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "virtual_radio.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Music Tracks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS music_tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        title TEXT,
        artist TEXT,
        album TEXT,
        duration REAL,
        file_hash TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create News Items table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        headline TEXT,
        summary TEXT,
        full_script TEXT,
        category TEXT,
        tone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        is_active INTEGER DEFAULT 1
    )
    """)
    
    # Create Commercial Brands table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS commercial_brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT,
        industry TEXT,
        slogan TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1
    )
    """)
    
    # Create Commercials table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS commercials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER,
        title TEXT,
        script TEXT,
        duration REAL,
        campaign TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (brand_id) REFERENCES commercial_brands(id)
    )
    """)
    
    # Create Characters table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        role TEXT,
        description TEXT,
        personality TEXT,
        station_affinity TEXT,
        first_appearance TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_appearance TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create Character Memories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS character_memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        character_id INTEGER,
        memory TEXT,
        importance INTEGER DEFAULT 5,
        episode_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (character_id) REFERENCES characters(id)
    )
    """)
    
    # Create Story Events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS story_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        related_characters TEXT, -- comma-separated character IDs or names
        status TEXT DEFAULT 'active', -- 'active', 'resolved'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP
    )
    """)
    
    # Create Episodes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS episodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        station TEXT,
        duration REAL,
        script_json TEXT, -- complete JSON script
        audio_path TEXT, -- path to MP3 relative to static
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Insert seed data if tables are empty
    seed_data(cursor)
    
    conn.commit()
    conn.close()

def seed_data(cursor):
    # Seed default commercial brands
    cursor.execute("SELECT COUNT(*) FROM commercial_brands")
    if cursor.fetchone()[0] == 0:
        brands = [
            ("AgroFuel", "Diésel de alto rendimiento y biocombustible para maquinaria agrícola. Huele a victoria y purín orgánico.", "Agricultura", "Mantén tu tractor rugiendo como un tigre cafeinado."),
            ("MegaHaul Logistics", "Megaempresa de transporte de carga a través de estados, sin importar las leyes de tránsito o el sueño del conductor.", "Transporte", "Si cabe, lo llevamos. Si no cabe, lo arrastramos."),
            ("FarmNet", "Proveedor de internet rural de alta latencia y dependiente del clima. Funciona con una compleja red de palomas y cercas de alambre.", "Tecnología", "Conectándote al mundo, eventualmente."),
            ("TractorCoin", "La criptomoneda agrícola líder. Respaldada por sacos de grano reales y promesas de lluvia futura.", "Finanzas", "¡Ara tus ahorros y siémbralos en suelo digital!")
        ]
        cursor.executemany(
            "INSERT INTO commercial_brands (name, description, industry, slogan) VALUES (?, ?, ?, ?)",
            brands
        )
        
        # Seed default commercials
        cursor.execute("SELECT id, name FROM commercial_brands")
        brand_ids = {row["name"]: row["id"] for row in cursor.fetchall()}
        
        commercials = [
            (brand_ids["AgroFuel"], "AgroFuel Máxima Potencia", "¿Cansado de que tu tractor eche humo negro al subir una colina de dos grados? Cámbiate a AgroFuel Max. Formulado con 40% de residuos de patata orgánica y 60% de pura potencia. AgroFuel: porque tus cultivos no se van a cosechar solos, y tu motor tampoco debería quejarse.", 30.0, "Campaña de Lanzamiento"),
            (brand_ids["MegaHaul Logistics"], "Se Buscan Conductores MegaHaul", "¡Atención conductores! ¿Te gusta el café? ¿Te gusta mirar el asfalto durante 72 horas seguidas? MegaHaul Logistics está contratando. Ofrecemos sueldo competitivo, un termo de café gratis y una flota de camiones con frenos dudosos. MegaHaul: entregamos porque literalmente no nos queda otra opción.", 35.0, "Reclutamiento 2026"),
            (brand_ids["FarmNet"], "FarmNet Velocidad Rural", "¿Se avecina tormenta? ¡Despídete de tu internet! Pero en los días soleados, experimenta la velocidad extrema de hasta 50 Kilobytes por segundo con FarmNet. ¡Descarga un correo electrónico en menos de diez minutos! FarmNet: es mejor que hablar con tus vacas.", 25.0, "Promo de Verano"),
            (brand_ids["TractorCoin"], "El Hype de TractorCoin", "¿Por qué invertir en oro cuando puedes invertir en TractorCoin? La única criptomoneda minada al operar tu cosechadora a las 3 de la mañana. Mientras tus vecinos duermen, tú ganas trigo digital. TractorCoin: la agricultura de rendimiento ahora es literal. El rendimiento pasado no garantiza la supervivencia del cultivo.", 30.0, "Revolución Cripto")
        ]
        cursor.executemany(
            "INSERT INTO commercials (brand_id, title, script, duration, campaign) VALUES (?, ?, ?, ?, ?)",
            commercials
        )

    # Seed default characters
    cursor.execute("SELECT COUNT(*) FROM characters")
    if cursor.fetchone()[0] == 0:
        characters = [
            ("Juan", "Granjero / Conspiranoico", "Un agricultor local que cree que el reporte del clima es una transmisión gubernamental de control mental y que su cosechadora lo espía.", "Paranoico, habla rápido, acento rural", "AgroTalk FM, WCTR Sim Edition"),
            ("Silas el Viejo", "Guardabosques Retirado / Cascarrabias", "Un anciano gruñón que odia las autopistas, los camiones, la juventud y que está seguro de haber visto un OVNI en los campos de trigo en el 94.", "Gruñón, lento, voz rasposa", "AgroTalk FM, Radio Rural 24"),
            ("Bob el Camionero", "Camionero de Larga Distancia", "Un camionero filosófico con 40 años de ruta que habla de la carretera como si fuera un ser vivo. Escribe poesía en paradas de camiones.", "Voz profunda, tranquilo, reflexivo, cansado", "Trucker News Radio, Highway Talk Network"),
            ("Cynthia", "Ex-suburbana / Entusiasta de lo Orgánico", "Se mudó de la ciudad para iniciar una cooperativa de lavanda bio-dinámica y llama a las radios a quejarse del ruido de tractores a las 5 AM.", "Esnob, dramática, habla rápido", "WCTR Sim Edition, SimNation News")
        ]
        cursor.executemany(
            "INSERT INTO characters (name, role, description, personality, station_affinity) VALUES (?, ?, ?, ?, ?)",
            characters
        )

        # Seed default memories
        cursor.execute("SELECT id, name FROM characters")
        char_ids = {row["name"]: row["id"] for row in cursor.fetchall()}
        
        memories = [
            (char_ids["Juan"], "Le compró un tractor usado de dudosa calidad a Silas que grita cuando lo pones en reversa.", 5, None),
            (char_ids["Silas el Viejo"], "Reclama que Juan le debe dos cajas de sidra por la compra del tractor.", 4, None),
            (char_ids["Bob el Camionero"], "Afirma haber visto una patata gigante brillante en la ruta, la cual cree que está relacionada con las teorías de Juan.", 6, None)
        ]
        cursor.executemany(
            "INSERT INTO character_memories (character_id, memory, importance, episode_id) VALUES (?, ?, ?, ?)",
            memories
        )

    # Seed default news items
    cursor.execute("SELECT COUNT(*) FROM news_items")
    if cursor.fetchone()[0] == 0:
        news = [
            ("Escasez de neumáticos de tractor en la región", 
             "Una repentina escasez de neumáticos gigantes ha dejado varados a los agricultores, obligando a algunos a usar bloques gigantes de queso o barriles como ruedas.",
             "Buenos días. Nuestra historia principal: la junta agrícola regional ha declarado estado de emergencia. Un barco de carga que transportaba cincuenta mil neumáticos de tractor de alta resistencia ha atracado misteriosamente en el país equivocado, dejando a los distribuidores vacíos. Tiempos desesperados requieren medidas desesperadas; el agricultor local Juan fue visto ayer conduciendo su cosechadora equipada con cuatro enormes ruedas de queso Cheddar curado. El queso funcionó sorprendentemente bien en el barro, aunque atrajo a una bandada de cuervos que terminó retrasándolo.",
             "Agricultura", "Sensacionalista"),
             
            ("Niebla misteriosa cierra la autopista principal",
             "Una densa niebla de color rosa de origen desconocido se ha asentado sobre la Ruta 9, deteniendo el tráfico. Los conductores reportan oír música de arpa dentro de ella.",
             "Atención conductores de la Autopista 9: se aconseja buscar rutas alternativas. Una extraña y brillante niebla rosa ha cubierto un tramo de diez millas de la autopista. La policía estatal informa que la visibilidad es cero y los camiones están estacionados en los arcenes. Curiosamente, varios camioneros, incluido Bob el Camionero, han llamado afirmando que la niebla huele a mermelada de fresa y reproduce música suave de arpa cuando bajas las ventanillas. El Departamento de Agricultura investiga si esto se debe a un derrame en la fábrica de mermelada cercana.",
             "Transporte", "Misterioso"),
             
            ("La fiebre de TractorCoin invade los campos",
             "Los agricultores abandonan los cultivos tradicionales para minar TractorCoin, una criptomoneda generada al conducir cosechadoras en complejos patrones geométricos.",
             "¿Es el trigo digital el futuro del campo? Los campos locales muestran extraños círculos de cultivo, pero los investigadores aclaran que no son extraterrestres, sino mineros de TractorCoin. Mediante cosechadoras con piloto automático guiadas por GPS, los agricultores ganan TractorCoin realizando maniobras geométricas en los campos de trigo. Los críticos advierten que esto destruye la producción real de alimentos, pero los defensores argumentan que un TractorCoin vale tres cabras y una carretilla usada. El mercado sigue siendo volátil.",
             "Economía", "Satírico")
        ]
        cursor.executemany(
            "INSERT INTO news_items (headline, summary, full_script, category, tone) VALUES (?, ?, ?, ?, ?)",
            news
        )

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
