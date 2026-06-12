import os
import json
import hashlib
import sqlite3
import random
from pydub import AudioSegment
from pydub.generators import Sine, Sawtooth, Triangle, WhiteNoise
from gtts import gTTS
from database import get_db_connection

# Define static folders relative to backend root
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BACKEND_DIR, "static")
MUSIC_DIR = os.path.join(STATIC_DIR, "music")
VOX_DIR = os.path.join(STATIC_DIR, "vox")
FX_DIR = os.path.join(STATIC_DIR, "fx")
EPISODES_DIR = os.path.join(STATIC_DIR, "episodes")

# Map of voices to gTTS top-level domains (TLDs) for accents
VOICE_TLDS = {
    "host": "com.mx",      # Mexican accent
    "caller": "com.mx",    # Mexican accent
    "reporter": "com.mx",  # Mexican accent
    "commercial": "com.mx" # Mexican accent
}

class AudioProductionEngine:
    def __init__(self, db_conn):
        self.conn = db_conn
        self.ensure_dirs()
        self.generate_fx_assets()
        self.generate_mock_music_if_empty()

    def ensure_dirs(self):
        """Creates the required folders for the static asset pipeline."""
        for path in [STATIC_DIR, MUSIC_DIR, VOX_DIR, FX_DIR, EPISODES_DIR]:
            os.makedirs(path, exist_ok=True)

    def generate_fx_assets(self):
        """Generates radio FX like beeps, sweeps, and static noise if they don't exist."""
        static_file = os.path.join(FX_DIR, "static_hum.mp3")
        sweeper_file = os.path.join(FX_DIR, "sweeper.mp3")
        
        # 1. Radio Static Hum (5 seconds of quiet white noise)
        if not os.path.exists(static_file):
            print("Generating radio static hum FX...")
            noise = WhiteNoise().to_audio_segment(duration=5000, volume=-28)
            noise.export(static_file, format="mp3")
            
        # 2. Sweeper Sound (A futuristic synthesizer sweep + white noise blast)
        if not os.path.exists(sweeper_file):
            print("Generating sweeper transition FX...")
            sweep = AudioSegment.silent(duration=1500)
            
            # Layer a fast pitch-shifting sine wave
            for ms in range(0, 1000, 10):
                freq = 100 + (ms * 1.5) # Slanted pitch upward
                note = Sine(freq).to_audio_segment(duration=15, volume=-15)
                sweep = sweep.overlay(note, position=ms)
                
            # Add a white noise burst in the middle
            noise_burst = WhiteNoise().to_audio_segment(duration=500, volume=-18).fade_out(400)
            sweep = sweep.overlay(noise_burst, position=400)
            sweep.export(sweeper_file, format="mp3")

    def generate_mock_music_if_empty(self):
        """Generates mock chiptune music tracks if the music directory has no MP3 files."""
        existing_mp3s = [f for f in os.listdir(MUSIC_DIR) if f.endswith(".mp3")]
        if len(existing_mp3s) > 0:
            return
            
        print("Music library is empty! Generating chiptune mock music tracks for testing...")
        
        # Track 1: Country Farm Synth (slow chord progression)
        self.generate_synth_track(
            filename="synth_pastoral.mp3",
            tempo=110,
            chords=[[261.63, 329.63, 392.00], [349.23, 440.00, 523.25], [392.00, 493.88, 587.33], [261.63, 329.63, 392.00]], # C, F, G, C
            melody=[392.00, 329.63, 349.23, 261.63, 293.66, 329.63, 392.00, 392.00],
            duration_sec=30
        )
        
        # Track 2: Highway Overdrive (faster driving bassline)
        self.generate_synth_track(
            filename="synth_highway.mp3",
            tempo=140,
            chords=[[220.00, 261.63, 329.63], [196.00, 246.94, 293.66], [174.61, 220.00, 261.63], [196.00, 246.94, 293.66]], # Am, G, F, G
            melody=[220.00, 329.63, 220.00, 329.63, 293.66, 261.63, 246.94, 196.00],
            duration_sec=30
        )
        
        # Track 3: Conspiracy X-Files Ambient (slow mystery triangle waves)
        self.generate_synth_track(
            filename="synth_ambient.mp3",
            tempo=80,
            chords=[[293.66, 349.23, 440.00], [220.00, 261.63, 329.63], [293.66, 349.23, 440.00], [329.63, 392.00, 493.88]], # Dm, Am, Dm, Em
            melody=[440.00, 523.25, 493.88, 392.00, 440.00, 349.23, 329.63, 293.66],
            duration_sec=35
        )
        
        # Register mock tracks in SQLite database
        self.sync_music_library()

    def generate_synth_track(self, filename, tempo, chords, melody, duration_sec):
        """Generates a chiptune-like song segment and exports it as MP3."""
        file_path = os.path.join(MUSIC_DIR, filename)
        
        beat_ms = int(60000 / tempo)
        num_beats = int((duration_sec * 1000) / beat_ms)
        
        track = AudioSegment.silent(duration=duration_sec * 1000)
        
        # Generate background chord pads (using Triangle waves for a softer tone)
        chord_track = AudioSegment.silent(duration=duration_sec * 1000)
        for beat in range(0, num_beats, 4):
            chord_notes = chords[(beat // 4) % len(chords)]
            pad = AudioSegment.silent(duration=beat_ms * 4)
            for freq in chord_notes:
                wave = Triangle(freq).to_audio_segment(duration=beat_ms * 4, volume=-22)
                pad = pad.overlay(wave)
            chord_track = chord_track.overlay(pad, position=beat * beat_ms)
            
        # Generate simple melody (using Sine waves)
        melody_track = AudioSegment.silent(duration=duration_sec * 1000)
        for beat in range(num_beats):
            note_freq = melody[beat % len(melody)]
            if beat % 2 == 0:  # play note every 2 beats
                # half notes
                wave = Sine(note_freq).to_audio_segment(duration=beat_ms * 2 - 20, volume=-16).fade_out(50)
                melody_track = melody_track.overlay(wave, position=beat * beat_ms)
                
        # Mix them
        mix = chord_track.overlay(melody_track)
        
        # Add simple chiptune drum click (using WhiteNoise)
        drums = AudioSegment.silent(duration=duration_sec * 1000)
        for beat in range(num_beats):
            if beat % 4 == 0: # kick
                click = Sine(60).to_audio_segment(duration=100, volume=-10).fade_out(80)
                drums = drums.overlay(click, position=beat * beat_ms)
            if beat % 4 == 2: # snare click
                snare = WhiteNoise().to_audio_segment(duration=60, volume=-24).fade_out(40)
                drums = drums.overlay(snare, position=beat * beat_ms)
                
        final_mix = mix.overlay(drums).fade_out(1000)
        final_mix.export(file_path, format="mp3")

    def sync_music_library(self):
        """Scans the music folder, computes file hashes and saves tracks to SQLite."""
        cursor = self.conn.cursor()
        
        # Get list of MP3 files
        mp3_files = [f for f in os.listdir(MUSIC_DIR) if f.endswith(".mp3")]
        
        # Remove tracks from DB that no longer exist on disk
        cursor.execute("SELECT file_path FROM music_tracks")
        db_paths = [row["file_path"] for row in cursor.fetchall()]
        for dp in db_paths:
            relative_dp = os.path.basename(dp)
            if relative_dp not in mp3_files:
                cursor.execute("DELETE FROM music_tracks WHERE file_path = ?", (dp,))
                
        # Index new files
        for filename in mp3_files:
            file_path = os.path.join(MUSIC_DIR, filename)
            
            # Compute MD5 hash to prevent duplicates
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            file_hash = hasher.hexdigest()
            
            # Read metadata (use filename fallback if metadata is empty)
            title = filename.replace(".mp3", "").replace("_", " ").title()
            artist = "VirtualRadio Station"
            duration = 30.0 # Default fallback
            
            try:
                # Get duration using pydub
                audio = AudioSegment.from_file(file_path)
                duration = len(audio) / 1000.0
            except Exception as e:
                print(f"Error reading file duration for {filename}: {e}")
                
            # Insert or ignore duplicate hashes
            cursor.execute("""
                INSERT INTO music_tracks (file_path, title, artist, duration, file_hash)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(file_hash) DO UPDATE SET
                    file_path=excluded.file_path,
                    title=excluded.title,
                    artist=excluded.artist,
                    duration=excluded.duration
            """, (file_path, title, artist, duration, file_hash))
            
        self.conn.commit()

    def get_tts_audio(self, text, voice_role):
        """Synthesizes text using gTTS and applies character specific TLD filters. Caches files."""
        # Clean text
        text_clean = text.strip()
        if not text_clean:
            return AudioSegment.silent(duration=500)
            
        # Create a unique filename for the spoken text to reuse synthesis
        hash_input = f"{text_clean}_{voice_role}".encode('utf-8')
        file_hash = hashlib.md5(hash_input).hexdigest()
        cached_file = os.path.join(VOX_DIR, f"vox_{file_hash}.mp3")
        
        if os.path.exists(cached_file):
            return AudioSegment.from_file(cached_file)
            
        print(f"Synthesizing voice [{voice_role}]: '{text_clean[:40]}...'")
        
        # Match TLD
        tld = VOICE_TLDS.get(voice_role, "es")
        
        try:
            # Generate speech using gTTS
            tts = gTTS(text=text_clean, lang="es", tld=tld, slow=False)
            tts.save(cached_file)
            return AudioSegment.from_file(cached_file)
        except Exception as e:
            print(f"TTS synthesis failed for voice role '{voice_role}': {e}. Generating silent clip.")
            # Fallback: return silence based on average reading speed (approx 3 words per second)
            word_count = len(text_clean.split())
            estimated_duration_ms = max(500, int((word_count / 3.0) * 1000))
            # Just create a very soft synthetic hum or click so the user knows there is a fallback happening
            beep = Sine(440).to_audio_segment(duration=100, volume=-30)
            silence = AudioSegment.silent(duration=estimated_duration_ms - 100)
            return beep + silence

    def apply_telephony_filter(self, audio_segment):
        """Applies a Bandpass Filter (300Hz to 3kHz) to make audio sound like a phone call."""
        # Bandpass is achieved by applying high-pass and low-pass in series
        return audio_segment.high_pass_filter(300).low_pass_filter(3000)

    def compile_episode(self, episode_id):
        """
        Processes an episode's script JSON, renders speech, overlays static, ducks music,
        adds sweepers, and exports the final MP3.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,))
        episode = cursor.fetchone()
        if not episode:
            raise ValueError(f"Episode with ID {episode_id} not found.")
            
        script = json.loads(episode["script_json"])
        
        # Load helper FX
        static_hum = AudioSegment.from_file(os.path.join(FX_DIR, "static_hum.mp3"))
        sweeper = AudioSegment.from_file(os.path.join(FX_DIR, "sweeper.mp3"))
        
        final_mix = AudioSegment.empty()
        
        # Fetch tracks map to map track index -> file_path
        cursor.execute("SELECT id, file_path FROM music_tracks")
        tracks_db = {row["id"]: row["file_path"] for row in cursor.fetchall()}
        
        # Procedural tracks mapping
        cursor.execute("SELECT * FROM music_tracks ORDER BY id ASC")
        all_tracks = [dict(t) for t in cursor.fetchall()]
        
        print(f"Compiling episode audio for: {episode['title']}")
        
        for idx, segment in enumerate(script):
            seg_type = segment["type"]
            
            if seg_type == "speech":
                speaker_type = segment.get("voice_id", "host")
                text = segment.get("text", "")
                
                # 1. Synthesize Speech
                vox_audio = self.get_tts_audio(text, speaker_type)
                
                # 2. Apply Telephony filter if it's a phone call
                if segment.get("effect") == "telephony":
                    vox_audio = self.apply_telephony_filter(vox_audio)
                    # Mix in a tiny bit of telephone crackle / white noise
                    static_crackle = WhiteNoise().to_audio_segment(duration=len(vox_audio), volume=-28)
                    vox_audio = vox_audio.overlay(static_crackle)
                else:
                    # Normal speech: overlay subtle radio broadcast hum (-26dB) in background
                    hum_segment = static_hum
                    while len(hum_segment) < len(vox_audio):
                        hum_segment += static_hum
                    hum_segment = hum_segment[:len(vox_audio)].fade_out(100)
                    vox_audio = vox_audio.overlay(hum_segment)
                    
                # Add a brief padding (300ms) at the end of speech
                vox_audio += AudioSegment.silent(duration=300)
                
                final_mix += vox_audio
                
            elif seg_type == "music":
                # Find track path
                track_idx = segment.get("track_id", 0)
                file_path = None
                
                # Map from planner index to DB ID if possible
                if all_tracks and track_idx is not None and track_idx < len(all_tracks):
                    file_path = all_tracks[track_idx]["file_path"]
                else:
                    # Fallback to random song
                    cursor.execute("SELECT file_path FROM music_tracks ORDER BY RANDOM() LIMIT 1")
                    res = cursor.fetchone()
                    if res:
                        file_path = res["file_path"]
                        
                if file_path and os.path.exists(file_path):
                    song = AudioSegment.from_file(file_path)
                    
                    # Prototype slice: only play 40 seconds of song to render episodes fast!
                    # Make it fade in and fade out
                    slice_dur_ms = 40000
                    if len(song) > slice_dur_ms:
                        song = song[:slice_dur_ms]
                    song = song.fade_in(1500).fade_out(2000)
                    
                    # Overlay sweeper effect at the very beginning of the song (Radio style transition!)
                    song = song.overlay(sweeper.fade_out(500), position=0)
                    
                    final_mix += song + AudioSegment.silent(duration=500)
                else:
                    # Silent fallback
                    final_mix += AudioSegment.silent(duration=5000)
                    
            elif seg_type == "fx":
                fx_name = segment.get("fx_type")
                if fx_name == "sweeper":
                    final_mix += sweeper
                elif fx_name == "static":
                    final_mix += static_hum
                else:
                    final_mix += AudioSegment.silent(duration=1000)
                    
        # Apply global volume normalization (LUFS alternative for chiptunes / simple mixes)
        final_mix = final_mix.normalize()
        
        # Export Episode MP3
        filename = f"episode_{episode_id}.mp3"
        output_path = os.path.join(EPISODES_DIR, filename)
        
        print(f"Exporting final mix to {output_path}...")
        final_mix.export(output_path, format="mp3")
        
        # Calculate duration of the episode in seconds
        duration_sec = len(final_mix) / 1000.0
        
        # Update episode table with final path and duration
        cursor.execute(
            "UPDATE episodes SET duration = ?, audio_path = ? WHERE id = ?",
            (duration_sec, f"static/episodes/{filename}", episode_id)
        )
        self.conn.commit()
        
        print(f"Episode {episode_id} compiled successfully! Duration: {duration_sec}s")
        return f"static/episodes/{filename}", duration_sec

if __name__ == "__main__":
    # Test compilation
    conn = get_db_connection()
    # Initialize engine (this will generate mock files if needed)
    engine = AudioProductionEngine(conn)
    # Import script generator and run
    from generator import ScriptGenerationEngine
    script_engine = ScriptGenerationEngine(conn)
    
    ep_id, title, _ = script_engine.generate_episode("AgroTalk FM")
    path, duration = engine.compile_episode(ep_id)
    print(f"Test compilation done. Path: {path}, Duration: {duration}s")
    conn.close()
