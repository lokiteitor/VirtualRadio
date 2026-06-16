"""End-to-end smoke test against a live Postgres + Redis.

Run with the venv and DB/REDIS/MEDIA env vars set (see the README). Exercises the
full happy path plus ownership isolation, the audio Range request and a /suggest
fallback. Exits non-zero on the first failure.
"""
import sys
import uuid

from app import create_app
from app.extensions import db

app = create_app("development")
client = app.test_client()

PASS = 0
FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {extra}")


def auth(token):
    return {"Authorization": f"Bearer {token}"}


print("=== auth/register (seeds universe) ===")
email = f"user_{uuid.uuid4().hex[:8]}@test.com"
r = client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "display_name": "Tester"})
check("register 201", r.status_code == 201, r.get_data(as_text=True)[:300])
body = r.get_json()
tok = body["data"]["access_token"]
check("access_token present", bool(tok))
check("refresh_token present", bool(body["data"]["refresh_token"]))
check("user echoed", body["data"]["user"]["email"] == email)

print("=== health (public) ===")
r = client.get("/api/v1/health")
check("health 200", r.status_code == 200 and r.get_json()["data"]["status"] == "ok")

print("=== auth: 401 without token ===")
r = client.get("/api/v1/stations")
check("stations 401 no token", r.status_code == 401)
check("error envelope", r.get_json().get("error", {}).get("code") == "UNAUTHORIZED")

print("=== universe/summary (seeded) ===")
r = client.get("/api/v1/universe/summary", headers=auth(tok))
check("summary 200", r.status_code == 200)
summ = r.get_json()["data"]
check("4 stations seeded", summ["stations"] == 4, summ)
check("4 brands seeded", summ["brands"] == 4, summ)
check("4 commercials seeded", summ["commercials"] == 4, summ)
check("4 characters seeded", summ["characters"] == 4, summ)
check("3 news seeded", summ["news_items"] == 3, summ)
check("0 episodes", summ["episodes"] == 0, summ)

print("=== stations list + create + validation ===")
r = client.get("/api/v1/stations", headers=auth(tok))
stations = r.get_json()["data"]
check("list 4 stations", len(stations) == 4)
station_id = stations[0]["id"]
r = client.post("/api/v1/stations", headers=auth(tok), json={"name": "Test FM", "host_name": "Bot"})
check("create station 201", r.status_code == 201)
r = client.post("/api/v1/stations", headers=auth(tok), json={})
check("create station 422 (missing name)", r.status_code == 422, r.get_data(as_text=True)[:200])

print("=== news/suggest fallback (no LLM key) ===")
r = client.post("/api/v1/news/suggest", headers=auth(tok), json={"context": {"category": "Clima", "tone": "Absurdo"}})
check("news suggest 200", r.status_code == 200, r.get_data(as_text=True)[:200])
sug = r.get_json()["data"]
check("suggest has headline", bool(sug.get("headline")))
check("suggest category valid", sug.get("category") in ["Agricultura", "Transporte", "Economía", "Tecnología", "Clima", "Comunidad", "Política Local", "Sucesos Extraños"], sug.get("category"))

print("=== episode generate -> run pipeline inline -> poll job ===")
r = client.post("/api/v1/episodes/generate", headers=auth(tok), json={"station_id": station_id})
check("generate 202", r.status_code == 202, r.get_data(as_text=True)[:200])
job = r.get_json()["data"]
job_id = job["id"]
check("job queued", job["status"] == "queued", job)

# Run the Celery task body synchronously (no worker needed for the smoke test).
from app.tasks.generation import generate_episode_task

with app.app_context():
    generate_episode_task(job_id)

r = client.get(f"/api/v1/jobs/{job_id}", headers=auth(tok))
job = r.get_json()["data"]
check("job completed", job["status"] == "completed", job)
check("job progress 100", job["progress"] == 100, job)
check("job has episode_id", bool(job["episode_id"]), job)

print("=== episode detail + audio (Range) ===")
ep_id = job["episode_id"]
r = client.get(f"/api/v1/episodes/{ep_id}", headers=auth(tok))
ep = r.get_json()["data"]
check("episode 200", r.status_code == 200)
check("script_json non-empty", isinstance(ep["script_json"], list) and len(ep["script_json"]) > 0, len(ep["script_json"]))
check("audio_path set", bool(ep["audio_path"]), ep.get("audio_path"))
check("duration > 0", (ep["duration"] or 0) > 0, ep.get("duration"))
seg_types = {s.get("type") for s in ep["script_json"]}
check("has speech+music segments", "speech" in seg_types and "music" in seg_types, seg_types)

r = client.get(f"/api/v1/episodes/{ep_id}/audio", headers=auth(tok))
check("audio 200", r.status_code == 200 and r.mimetype == "audio/mpeg", f"{r.status_code} {r.mimetype}")
r = client.get(f"/api/v1/episodes/{ep_id}/audio", headers={**auth(tok), "Range": "bytes=0-1023"})
check("audio 206 Range", r.status_code == 206, r.status_code)

print("=== music: mock tracks were indexed by the pipeline ===")
r = client.get("/api/v1/music", headers=auth(tok))
music = r.get_json()
check("music indexed (>=3)", len(music["data"]) >= 3, len(music["data"]))
check("music meta total_duration", music["meta"].get("total_duration", 0) > 0, music["meta"])

print("=== character memory written by pipeline ===")
r = client.get("/api/v1/characters", headers=auth(tok))
chars = r.get_json()["data"]
mem_total = 0
for c in chars:
    rm = client.get(f"/api/v1/characters/{c['id']}/memories", headers=auth(tok))
    mem_total += len(rm.get_json()["data"])
check("character memories exist", mem_total >= 1, mem_total)

print("=== ownership isolation (second user) ===")
email2 = f"user_{uuid.uuid4().hex[:8]}@test.com"
r = client.post("/api/v1/auth/register", json={"email": email2, "password": "password123"})
tok2 = r.get_json()["data"]["access_token"]
r = client.get(f"/api/v1/stations/{station_id}", headers=auth(tok2))
check("other user's station -> 404", r.status_code == 404, r.status_code)
r = client.get(f"/api/v1/episodes/{ep_id}", headers=auth(tok2))
check("other user's episode -> 404", r.status_code == 404, r.status_code)
r = client.get(f"/api/v1/jobs/{job_id}", headers=auth(tok2))
check("other user's job -> 404", r.status_code == 404, r.status_code)

print("=== login + refresh ===")
r = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
check("login 200", r.status_code == 200)
refresh_tok = r.get_json()["data"]["refresh_token"]
r = client.post("/api/v1/auth/refresh", headers=auth(refresh_tok))
check("refresh 200 + access_token", r.status_code == 200 and bool(r.get_json()["data"]["access_token"]), r.status_code)
r = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
check("login wrong pw 401", r.status_code == 401)

print(f"\n==== RESULT: {PASS} passed, {FAIL} failed ====")
sys.exit(1 if FAIL else 0)
