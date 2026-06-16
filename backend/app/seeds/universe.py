"""Seed a user's default narrative universe on registration.

Ported from the prototype seed data: 4 stations, 4 brands + commercials,
4 characters + memories and 3 news items, all scoped to the owner. Objects are
added and flushed; the caller owns the surrounding transaction (commit).
"""
from __future__ import annotations

import uuid

from app.extensions import db
from app.models import (
    Character,
    CharacterMemory,
    Commercial,
    CommercialBrand,
    NewsItem,
    Station,
)
from app.models.enums import GeminiVoice, NewsCategory, NewsTone

_STATIONS = [
    {
        "name": "AgroTalk FM",
        "host_name": "Clem",
        "description": "Radio de debate centrada en la cosecha, precios de fertilizantes y chismes de tractor.",
        "personality": "Rustic, proud farmer, obsessed with fertilizer prices, machinery, and weather.",
        "host_voice": GeminiVoice.ALGIEBA,
        "reporter_voice": GeminiVoice.KORE,
        "frequency": "95.2 FM",
        "emoji": "🌾",
        "color": "#10b981",
        "intro_templates": [
            "¡Buenos días, agricultores! Aquí Clem en AgroTalk FM. Sacudan el barro de sus botas porque hoy tenemos un programa cargado de nitrógeno y verdades como puños.",
            "Bienvenidos de nuevo a AgroTalk FM, la única emisora que huele a estiércol fresco y trabajo duro. Soy Clem, y hoy hablaremos del precio de las cosechadoras.",
        ],
        "outro_templates": [
            "Eso es todo por hoy en AgroTalk FM. Recuerden: si el tractor hace un ruido raro, pisen el acelerador más fuerte. Habló Clem, nos vemos en el campo.",
            "Clem se despide de AgroTalk FM. Vuelvan a sus tractores, rieguen sus plantas y vigilen a sus vecinos. ¡Hasta la próxima, labradores!",
        ],
    },
    {
        "name": "Trucker News Radio",
        "host_name": "Diesel Dan",
        "description": "Noticias de autopistas, reportes de tráfico de larga distancia e historias del asfalto.",
        "personality": "Deep-voiced, road-weary, drinks too much coffee, speaks in trucker slang (10-4, copy that).",
        "host_voice": GeminiVoice.CHARON,
        "reporter_voice": GeminiVoice.IAPETUS,
        "frequency": "104.8 FM",
        "emoji": "🚛",
        "color": "#6b7280",
        "intro_templates": [
            "Aquí Diesel Dan en la frecuencia de Trucker News Radio. Para todos los que devoran asfalto a esta hora, mantengan los ojos abiertos y la cafetera encendida.",
            "Saludos, nómadas de la carretera. Les habla Diesel Dan. Ajusten sus espejos, pongan quinta marcha y acompáñenme en este viaje de noticias y diésel.",
        ],
        "outro_templates": [
            "Diesel Dan fuera. Mantengan las ruedas girando y los radares vigilados. Nos leemos en la próxima parada de camiones. 10-4.",
            "Eso es todo desde la cabina de Trucker News Radio. Conduzcan con cuidado y no coman los burritos de la estación de servicio de la salida 4. Corto y cierro.",
        ],
    },
    {
        "name": "SimNation News",
        "host_name": "Audrey Vance",
        "description": "Boletines de simulación serios y objetivos sobre la economía regional e infraestructura.",
        "personality": "Crisp, professional, highly articulated news anchor, takes trivial simulation events extremely seriously.",
        "host_voice": GeminiVoice.VINDEMIATRIX,
        "reporter_voice": GeminiVoice.DESPINA,
        "frequency": "88.0 FM",
        "emoji": "👔",
        "color": "#3b82f6",
        "intro_templates": [
            "Muy buenas tardes. Les saluda Audrey Vance para SimNation News, transmitiendo las noticias más relevantes de la comunidad de simulación global.",
            "Bienvenidos a la emisión de SimNation News. Les acompaña Audrey Vance. Analizaremos en detalle el impacto del último parche de rendimiento y el estado de la economía local.",
        ],
        "outro_templates": [
            "Gracias por su sintonía. Les ha informado Audrey Vance para SimNation News. Manténganse informados y sigan simulando con responsabilidad.",
            "Esto concluye nuestro boletín. Soy Audrey Vance. Recuerden que la realidad es solo otra simulación que no podemos reiniciar. Buenas noches.",
        ],
    },
    {
        "name": "WCTR Sim Edition",
        "host_name": "Richard 'Dick' Brainwave",
        "description": "Teorías locas, llamadas telefónicas extravagantes y secretos alienígenas de los cultivos.",
        "personality": "Highly energetic, paranoid, believes the government is using crop circles to communicate with Martian cows, speaks in frantic bursts.",
        "host_voice": GeminiVoice.FENRIR,
        "reporter_voice": GeminiVoice.PUCK,
        "frequency": "99.1 FM",
        "emoji": "👽",
        "color": "#ec4899",
        "intro_templates": [
            "¡DESPIERTEN, OVEJAS! Soy Dick Brainwave en WCTR Sim Edition. Hoy les revelaré cómo las corporaciones de tractores están insertando microchips en las semillas de trigo.",
            "¡Están escuchando la verdad cruda en WCTR Sim Edition con Dick Brainwave! ¿Es el GPS de su camión una sonda alienígena? Spoiler: ¡SÍ LO ES!",
        ],
        "outro_templates": [
            "La verdad está ahí fuera, pero probablemente esté censurada por el lobby del compost. Dick Brainwave se despide. ¡No miren directamente a los espantapájaros!",
            "¡Apaguen sus teléfonos! ¡Quemen sus manuales de conductor! Dick Brainwave les dice adiós desde el búnker de WCTR. ¡Ellos nos están escuchando!",
        ],
    },
]

_BRANDS = [
    {
        "name": "AgroFuel",
        "description": "Diésel de alto rendimiento y biocombustible para maquinaria agrícola. Huele a victoria y purín orgánico.",
        "industry": "Agricultura",
        "slogan": "Mantén tu tractor rugiendo como un tigre cafeinado.",
        "commercial": {
            "title": "AgroFuel Máxima Potencia",
            "script": "¿Cansado de que tu tractor eche humo negro al subir una colina de dos grados? Cámbiate a AgroFuel Max. Formulado con 40% de residuos de patata orgánica y 60% de pura potencia. AgroFuel: porque tus cultivos no se van a cosechar solos, y tu motor tampoco debería quejarse.",
            "duration": 30.0,
            "voice": GeminiVoice.ZEPHYR,
            "campaign": "Campaña de Lanzamiento",
        },
    },
    {
        "name": "MegaHaul Logistics",
        "description": "Megaempresa de transporte de carga a través de estados, sin importar las leyes de tránsito o el sueño del conductor.",
        "industry": "Transporte",
        "slogan": "Si cabe, lo llevamos. Si no cabe, lo arrastramos.",
        "commercial": {
            "title": "Se Buscan Conductores MegaHaul",
            "script": "¡Atención conductores! ¿Te gusta el café? ¿Te gusta mirar el asfalto durante 72 horas seguidas? MegaHaul Logistics está contratando. Ofrecemos sueldo competitivo, un termo de café gratis y una flota de camiones con frenos dudosos. MegaHaul: entregamos porque literalmente no nos queda otra opción.",
            "duration": 35.0,
            "voice": GeminiVoice.SULAFAT,
            "campaign": "Reclutamiento 2026",
        },
    },
    {
        "name": "FarmNet",
        "description": "Proveedor de internet rural de alta latencia y dependiente del clima. Funciona con una compleja red de palomas y cercas de alambre.",
        "industry": "Tecnología",
        "slogan": "Conectándote al mundo, eventualmente.",
        "commercial": {
            "title": "FarmNet Velocidad Rural",
            "script": "¿Se avecina tormenta? ¡Despídete de tu internet! Pero en los días soleados, experimenta la velocidad extrema de hasta 50 Kilobytes por segundo con FarmNet. ¡Descarga un correo electrónico en menos de diez minutos! FarmNet: es mejor que hablar con tus vacas.",
            "duration": 25.0,
            "voice": GeminiVoice.LAOMEDEIA,
            "campaign": "Promo de Verano",
        },
    },
    {
        "name": "TractorCoin",
        "description": "La criptomoneda agrícola líder. Respaldada por sacos de grano reales y promesas de lluvia futura.",
        "industry": "Finanzas",
        "slogan": "¡Ara tus ahorros y siémbralos en suelo digital!",
        "commercial": {
            "title": "El Hype de TractorCoin",
            "script": "¿Por qué invertir en oro cuando puedes invertir en TractorCoin? La única criptomoneda minada al operar tu cosechadora a las 3 de la mañana. Mientras tus vecinos duermen, tú ganas trigo digital. TractorCoin: la agricultura de rendimiento ahora es literal. El rendimiento pasado no garantiza la supervivencia del cultivo.",
            "duration": 30.0,
            "voice": GeminiVoice.SCHEDAR,
            "campaign": "Revolución Cripto",
        },
    },
]

_CHARACTERS = [
    {
        "name": "Juan",
        "role": "Granjero / Conspiranoico",
        "description": "Un agricultor local que cree que el reporte del clima es una transmisión gubernamental de control mental y que su cosechadora lo espía.",
        "personality": "Paranoico, habla rápido, acento rural",
        "station_affinity": "AgroTalk FM, WCTR Sim Edition",
        "voice": GeminiVoice.ORUS,
        "memory": ("Le compró un tractor usado de dudosa calidad a Silas que grita cuando lo pones en reversa.", 5),
    },
    {
        "name": "Silas el Viejo",
        "role": "Guardabosques Retirado / Cascarrabias",
        "description": "Un anciano gruñón que odia las autopistas, los camiones, la juventud y que está seguro de haber visto un OVNI en los campos de trigo en el 94.",
        "personality": "Gruñón, lento, voz rasposa",
        "station_affinity": "AgroTalk FM, Radio Rural 24",
        "voice": GeminiVoice.GACRUX,
        "memory": ("Reclama que Juan le debe dos cajas de sidra por la compra del tractor.", 4),
    },
    {
        "name": "Bob el Camionero",
        "role": "Camionero de Larga Distancia",
        "description": "Un camionero filosófico con 40 años de ruta que habla de la carretera como si fuera un ser vivo. Escribe poesía en paradas de camiones.",
        "personality": "Voz profunda, tranquilo, reflexivo, cansado",
        "station_affinity": "Trucker News Radio, Highway Talk Network",
        "voice": GeminiVoice.SADALTAGER,
        "memory": ("Afirma haber visto una patata gigante brillante en la ruta, la cual cree que está relacionada con las teorías de Juan.", 6),
    },
    {
        "name": "Cynthia",
        "role": "Ex-suburbana / Entusiasta de lo Orgánico",
        "description": "Se mudó de la ciudad para iniciar una cooperativa de lavanda bio-dinámica y llama a las radios a quejarse del ruido de tractores a las 5 AM.",
        "personality": "Esnob, dramática, habla rápido",
        "station_affinity": "WCTR Sim Edition, SimNation News",
        "voice": GeminiVoice.AOEDE,
        "memory": None,
    },
]

_NEWS = [
    {
        "headline": "Escasez de neumáticos de tractor en la región",
        "summary": "Una repentina escasez de neumáticos gigantes ha dejado varados a los agricultores, obligando a algunos a usar bloques gigantes de queso o barriles como ruedas.",
        "full_script": "Buenos días. Nuestra historia principal: la junta agrícola regional ha declarado estado de emergencia. Un barco de carga que transportaba cincuenta mil neumáticos de tractor de alta resistencia ha atracado misteriosamente en el país equivocado, dejando a los distribuidores vacíos. Tiempos desesperados requieren medidas desesperadas; el agricultor local Juan fue visto ayer conduciendo su cosechadora equipada con cuatro enormes ruedas de queso Cheddar curado. El queso funcionó sorprendentemente bien en el barro, aunque atrajo a una bandada de cuervos que terminó retrasándolo.",
        "category": NewsCategory.AGRICULTURA,
        "tone": NewsTone.SENSACIONALISTA,
    },
    {
        "headline": "Niebla misteriosa cierra la autopista principal",
        "summary": "Una densa niebla de color rosa de origen desconocido se ha asentado sobre la Ruta 9, deteniendo el tráfico. Los conductores reportan oír música de arpa dentro de ella.",
        "full_script": "Atención conductores de la Autopista 9: se aconseja buscar rutas alternativas. Una extraña y brillante niebla rosa ha cubierto un tramo de diez millas de la autopista. La policía estatal informa que la visibilidad es cero y los camiones están estacionados en los arcenes. Curiosamente, varios camioneros, incluido Bob el Camionero, han llamado afirmando que la niebla huele a mermelada de fresa y reproduce música suave de arpa cuando bajas las ventanillas. El Departamento de Agricultura investiga si esto se debe a un derrame en la fábrica de mermelada cercana.",
        "category": NewsCategory.TRANSPORTE,
        "tone": NewsTone.MISTERIOSO,
    },
    {
        "headline": "La fiebre de TractorCoin invade los campos",
        "summary": "Los agricultores abandonan los cultivos tradicionales para minar TractorCoin, una criptomoneda generada al conducir cosechadoras en complejos patrones geométricos.",
        "full_script": "¿Es el trigo digital el futuro del campo? Los campos locales muestran extraños círculos de cultivo, pero los investigadores aclaran que no son extraterrestres, sino mineros de TractorCoin. Mediante cosechadoras con piloto automático guiadas por GPS, los agricultores ganan TractorCoin realizando maniobras geométricas en los campos de trigo. Los críticos advierten que esto destruye la producción real de alimentos, pero los defensores argumentan que un TractorCoin vale tres cabras y una carretilla usada. El mercado sigue siendo volátil.",
        "category": NewsCategory.ECONOMIA,
        "tone": NewsTone.ABSURDO,
    },
]


def seed_default_universe(owner_id: uuid.UUID) -> None:
    """Idempotent-friendly: copies templates so module-level data is never mutated."""
    for s in _STATIONS:
        db.session.add(Station(owner_id=owner_id, **s))

    for b in _BRANDS:
        fields = {k: v for k, v in b.items() if k != "commercial"}
        brand = CommercialBrand(owner_id=owner_id, **fields)
        db.session.add(brand)
        db.session.flush()  # need brand.id
        db.session.add(Commercial(owner_id=owner_id, brand_id=brand.id, **b["commercial"]))

    for c in _CHARACTERS:
        fields = {k: v for k, v in c.items() if k != "memory"}
        character = Character(owner_id=owner_id, **fields)
        db.session.add(character)
        db.session.flush()  # need character.id
        if c["memory"]:
            text, importance = c["memory"]
            db.session.add(
                CharacterMemory(
                    owner_id=owner_id,
                    character_id=character.id,
                    memory=text,
                    importance=importance,
                )
            )

    for n in _NEWS:
        db.session.add(NewsItem(owner_id=owner_id, **n))

    db.session.flush()
