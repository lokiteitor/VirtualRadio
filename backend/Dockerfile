FROM python:3.12-slim

# System deps: FFmpeg for the audio engine (pydub) + build essentials for psycopg
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Media volume mount point (music / vox / fx / episodes)
RUN mkdir -p /data/media

EXPOSE 5000

# Default command runs the API with Gunicorn; the worker service overrides it.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "wsgi:app"]
