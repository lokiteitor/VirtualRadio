"""Validate the real async path: enqueue via .delay() and let the worker process it."""
import sys
import time
import uuid

from app import create_app

app = create_app("development")
client = app.test_client()


def auth(t):
    return {"Authorization": f"Bearer {t}"}


email = f"async_{uuid.uuid4().hex[:8]}@test.com"
r = client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
tok = r.get_json()["data"]["access_token"]
station_id = client.get("/api/v1/stations", headers=auth(tok)).get_json()["data"][0]["id"]

r = client.post("/api/v1/episodes/generate", headers=auth(tok), json={"station_id": station_id})
assert r.status_code == 202, r.get_data(as_text=True)
job_id = r.get_json()["data"]["id"]
print(f"enqueued job {job_id}; polling (worker processes via Redis)...")

deadline = time.time() + 120
last = None
while time.time() < deadline:
    job = client.get(f"/api/v1/jobs/{job_id}", headers=auth(tok)).get_json()["data"]
    if job["status"] != last:
        print(f"  status={job['status']} progress={job['progress']}")
        last = job["status"]
    if job["status"] in ("completed", "failed"):
        break
    time.sleep(2)

if job["status"] == "completed":
    ep = client.get(f"/api/v1/episodes/{job['episode_id']}", headers=auth(tok)).get_json()["data"]
    audio = client.get(f"/api/v1/episodes/{job['episode_id']}/audio", headers=auth(tok))
    ok = bool(ep["audio_path"]) and audio.status_code == 200
    print(f"RESULT: async generation {'OK' if ok else 'FAILED'} (duration={ep['duration']}s, audio={audio.status_code})")
    sys.exit(0 if ok else 1)

print(f"RESULT: async generation did not complete (status={job['status']}, error={job.get('error')})")
sys.exit(1)
