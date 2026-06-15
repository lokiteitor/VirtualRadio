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
    
    # Create Stations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        host_name TEXT,
        description TEXT,
        personality TEXT,
        frequency TEXT,
        emoji TEXT,
        color TEXT,
        intro_templates TEXT, -- JSON array of strings
        outro_templates TEXT, -- JSON array of strings
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

    # Seed default stations
    cursor.execute("SELECT COUNT(*) FROM stations")
    if cursor.fetchone()[0] == 0:
        import json
        default_stations = [
            ("AgroTalk FM", "Clem", "Radio de debate centrada en la cosecha, precios de fertilizantes y chismes de tractor.", "Rustic, proud farmer, obsessed with fertilizer prices, machinery, and weather.", "95.2 FM", "🌾", "#10b981",
             json.dumps([
                 "¡Buenos días, agricultores! Aquí Clem en AgroTalk FM. Sacudan el barro de sus botas porque hoy tenemos un programa cargado de nitrógeno y verdades como puños.",
                 "Bienvenidos de nuevo a AgroTalk FM, la única emisora que huele a estiércol fresco y trabajo duro. Soy Clem, y hoy hablaremos del precio de las cosechadoras."
             ]),
             json.dumps([
                 "Eso es todo por hoy en AgroTalk FM. Recuerden: si el tractor hace un ruido raro, pisen el acelerador más fuerte. Habló Clem, nos vemos en el campo.",
                 "Clem se despide de AgroTalk FM. Vuelvan a sus tractores, rieguen sus plantas y vigilen a sus vecinos. ¡Hasta la próxima, labradores!"
             ])),
             
            ("Trucker News Radio", "Diesel Dan", "Noticias de autopistas, reportes de tráfico de larga distancia e historias del asfalto.", "Deep-voiced, road-weary, drinks too much coffee, speaks in trucker slang (10-4, copy that).", "104.8 FM", "🚛", "#6b7280",
             json.dumps([
                 "Aquí Diesel Dan en la frecuencia de Trucker News Radio. Para todos los que devoran asfalto a esta hora, mantengan los ojos abiertos y la cafetera encendida.",
                 "Saludos, nómadas de la carretera. Les habla Diesel Dan. Ajusten sus espejos, pongan quinta marcha y acompáñenme en este viaje de noticias y diésel."
             ]),
             json.dumps([
                 "Diesel Dan fuera. Mantengan las ruedas girando y los radares vigilados. Nos leemos en la próxima parada de camiones. 10-4.",
                 "Eso es todo desde la cabina de Trucker News Radio. Conduzcan con cuidado y no coman los burritos de la estación de servicio de la salida 4. Corto y cierro."
             ])),
             
            ("SimNation News", "Audrey Vance", "Boletines de simulación serios y objetivos sobre la economía regional e infraestructura.", "Crisp, professional, highly articulated news anchor, takes trivial simulation events extremely seriously.", "88.0 FM", "👔", "#3b82f6",
             json.dumps([
                 "Muy buenas tardes. Les saluda Audrey Vance para SimNation News, transmitiendo las noticias más relevantes de la comunidad de simulación global.",
                 "Bienvenidos a la emisión de SimNation News. Les acompaña Audrey Vance. Analizaremos en detalle el impacto del último parche de rendimiento y el estado de la economía local."
             ]),
             json.dumps([
                 "Gracias por su sintonía. Les ha informado Audrey Vance para SimNation News. Manténganse informados y sigan simulando con responsabilidad.",
                 "Esto concluye nuestro boletín. Soy Audrey Vance. Recuerden que la realidad es solo otra simulación que no podemos reiniciar. Buenas noches."
             ])),
             
            ("WCTR Sim Edition", "Richard 'Dick' Brainwave", "Teorías locas, llamadas telefónicas extravagantes y secretos alienígenas de los cultivos.", "Highly energetic, paranoid, believes the government is using crop circles to communicate with Martian cows, speaks in frantic bursts.", "99.1 FM", "👽", "#ec4899",
             json.dumps([
                 "¡DESPIERTEN, OVEJAS! Soy Dick Brainwave en WCTR Sim Edition. Hoy les revelaré cómo las corporaciones de tractores están insertando microchips en las semillas de trigo.",
                 "¡Están escuchando la verdad cruda en WCTR Sim Edition con Dick Brainwave! ¿Es el GPS de su camión una sonda alienígena? Spoiler: ¡SÍ LO ES!"
             ]),
             json.dumps([
                 "La verdad está ahí fuera, pero probablemente esté censurada por el lobby del compost. Dick Brainwave se despide. ¡No miren directamente a los espantapájaros!",
                 "¡Apaguen sus teléfonos! ¡Quemen sus manuales de conductor! Dick Brainwave les dice adiós desde el búnker de WCTR. ¡Ellos nos están escuchando!"
             ]))
        ]
        cursor.executemany(
            "INSERT INTO stations (name, host_name, description, personality, frequency, emoji, color, intro_templates, outro_templates) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            default_stations
        )

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
