import asyncio
import re
import os
import html
import threading
import subprocess
import sys
from flask import Flask, render_template, request, jsonify, send_file
import edge_tts
import tempfile
from datetime import datetime

# Setup ffmpeg path for pydub
try:
    import imageio_ffmpeg
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    from pydub import AudioSegment
    from pydub.utils import which
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
    AudioSegment.ffprobe = ffmpeg_path  # ffprobe is included in same binary
    print(f"Using bundled ffmpeg: {ffmpeg_path}")
    
    # Also set environment variable for pydub
    os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ.get("PATH", "")
except Exception as e:
    print(f"Warning: ffmpeg setup failed: {e}")

app = Flask(__name__)
# Configuration for handling large texts
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
app.config['JSON_AS_ASCII'] = False  # Support non-ASCII characters

# Progress tracking for generation tasks
progress_tracker = {}

# Emotion to prosody mapping - Psycholinguistically calibrated values
# Pitch: +1% ≈ 1-2Hz change from baseline (male: 120Hz, female: 220Hz)
# Rate: +1% ≈ 1% change in syllables per second
# Volume: +1dB ≈ perceptible loudness change
EMOTION_PROSODY = {
    'happy': {'pitch': '+7%', 'rate': '+12%', 'volume': '+6dB'},        # Moderate pitch rise, 12% faster (natural joy)
    'excited': {'pitch': '+10%', 'rate': '+18%', 'volume': '+9dB'},     # High pitch, 18% faster speech (high arousal)
    'sad': {'pitch': '-6%', 'rate': '-12%', 'volume': '-7dB'},          # Lower pitch, 12% slower, quieter (low energy)
    'angry': {'pitch': '+4%', 'rate': '+15%', 'volume': '+12dB'},       # Slight pitch rise (tension), 15% faster, loud
    'calm': {'pitch': '-2%', 'rate': '-8%', 'volume': '-4dB'},          # Slight pitch drop, 8% slower, softer (relaxed)
    'whisper': {'pitch': '-4%', 'rate': '-10%', 'volume': '-15dB'},     # Lower pitch, 10% slower, very quiet
    'surprised': {'pitch': '+12%', 'rate': '+8%', 'volume': '+7dB'},    # Sharp pitch rise, moderate speed, louder
    'fearful': {'pitch': '+8%', 'rate': '+20%', 'volume': '+5dB'},      # Higher pitch, 20% faster (anxiety), moderate volume
    'disgusted': {'pitch': '-5%', 'rate': '-6%', 'volume': '+6dB'},     # Lower pitch (disapproval), slightly slower
    'neutral': {'pitch': '+0%', 'rate': '+0%', 'volume': '+0dB'},       # Baseline (no modulation)
    'serious': {'pitch': '-4%', 'rate': '+2%', 'volume': '+3dB'},       # Lower pitch (authority), steady pace
    'questioning': {'pitch': '+9%', 'rate': '+5%', 'volume': '+4dB'},   # Rising pitch (inquisitive), slightly faster
    'storytelling': {'pitch': '+3%', 'rate': '-5%', 'volume': '+5dB'}   # Slight pitch variation, 5% slower (clarity), louder
}

def chunk_long_text(text, max_length=500):
    """Split very long text segments into smaller chunks to avoid timeouts"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    words = text.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1  # +1 for space
        if current_length + word_length > max_length and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def parse_text_with_emotions(text):
    """Parse text and extract emotion markers, return segments with emotions"""
    segments = []
    pattern = r'\[(\w+)\]'
    
    # Split by emotion markers while keeping the markers
    parts = re.split(pattern, text)
    
    # Handle text before first emotion marker
    if parts[0].strip() and not parts[0].startswith('['):
        segments.append({'emotion': 'neutral', 'text': parts[0].strip()})
    
    # Process emotion-text pairs
    i = 1
    while i < len(parts):
        if i + 1 < len(parts):
            emotion = parts[i].lower()
            content = parts[i + 1].strip()
            
            if content:
                # Split long content into chunks
                if len(content) > 500:
                    chunks = chunk_long_text(content, max_length=500)
                    for chunk in chunks:
                        if emotion in EMOTION_PROSODY:
                            segments.append({'emotion': emotion, 'text': chunk})
                        else:
                            # Unknown emotion, treat as neutral
                            segments.append({'emotion': 'neutral', 'text': chunk})
                else:
                    if emotion in EMOTION_PROSODY:
                        segments.append({'emotion': emotion, 'text': content})
                    else:
                        # Unknown emotion, treat as neutral
                        segments.append({'emotion': 'neutral', 'text': content})
        i += 2
    
    # If no segments found, return entire text as neutral
    if not segments:
        return [{'emotion': 'neutral', 'text': text.strip()}]
    
    return segments

def build_text_with_prosody_data(text):
    """Parse text and return segments with emotion data"""
    segments = parse_text_with_emotions(text)
    
    # Build plain text without emotion markers and collect prosody data
    text_parts = []
    prosody_segments = []
    
    for segment in segments:
        text_parts.append(segment['text'])
        prosody_segments.append({
            'text': segment['text'],
            'emotion': segment['emotion'],
            'prosody': EMOTION_PROSODY.get(segment['emotion'], EMOTION_PROSODY['neutral'])
        })
    
    plain_text = ' '.join(text_parts)
    return plain_text, prosody_segments

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/voices', methods=['GET'])
def get_voices():
    """Get list of available voices"""
    async def fetch_voices():
        voices = await edge_tts.list_voices()
        return voices
    
    voices = asyncio.run(fetch_voices())
    
    # Organize voices by language
    voice_data = {}
    for voice in voices:
        locale = voice['Locale']
        if locale not in voice_data:
            voice_data[locale] = []
        
        voice_data[locale].append({
            'name': voice['ShortName'],
            'display_name': voice['FriendlyName'],
            'gender': voice['Gender'],
            'locale': voice['Locale']
        })
    
    return jsonify(voice_data)

@app.route('/api/preview', methods=['POST'])
def preview_voice():
    """Generate a short preview for a voice"""
    try:
        data = request.json
        voice = data.get('voice', 'en-US-AriaNeural')
        
        # Short preview text
        preview_text = "Hello, this is a voice preview."
        
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_path = os.path.join(temp_dir, f'preview_{timestamp}.mp3')
        
        # Generate preview using subprocess
        script_path = os.path.join(os.path.dirname(__file__), 'generate_tts_simple.py')
        result = subprocess.run(
            [sys.executable, script_path, temp_path, voice, preview_text, "+0%", "+0Hz"],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode != 0 or not os.path.exists(temp_path):
            raise Exception("Preview generation failed")
        
        return send_file(
            temp_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f'preview_{voice}.mp3'
        )
        
    except Exception as e:
        print(f"ERROR in preview_voice: {type(e).__name__}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    """Get progress for a specific task"""
    progress = progress_tracker.get(task_id, {'completed': 0, 'total': 1})
    return jsonify(progress)

@app.route('/api/generate', methods=['POST'])
def generate_speech():
    """Generate speech from text with emotions"""
    task_id = None
    try:
        data = request.json
        text = data.get('text', '')
        voice = data.get('voice', 'en-US-AriaNeural')
        task_id = data.get('task_id', datetime.now().strftime("%Y%m%d%H%M%S%f"))
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Check text length (allow up to 100,000 characters for ~100 segments)
        if len(text) > 100000:
            return jsonify({'error': 'Text too long. Maximum 100,000 characters allowed.'}), 400
        
        print(f"\n{'='*60}")
        print(f"Starting TTS generation...")
        print(f"Voice: {voice}")
        print(f"Text length: {len(text)} characters")
        print(f"Task ID: {task_id}")
        
        # Parse text and get prosody data for each segment
        plain_text, prosody_segments = build_text_with_prosody_data(text)
        print(f"Plain text: {plain_text[:200]}")
        print(f"Total prosody segments to generate: {len(prosody_segments)}")
        
        # Initialize progress tracker
        progress_tracker[task_id] = {'completed': 0, 'total': len(prosody_segments)}
        
        # Show all segments for debugging
        for idx, seg in enumerate(prosody_segments):
            print(f"  Segment {idx}: [{seg['emotion']}] \"{seg['text'][:50]}...\"")
        
        # Create temporary directory for segments
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Generate audio for each emotion segment
        segment_files = []
        script_path = os.path.join(os.path.dirname(__file__), 'generate_tts_simple.py')
        
        for idx, segment in enumerate(prosody_segments):
            segment_text = segment['text']
            rate = segment['prosody']['rate']
            pitch = segment['prosody']['pitch']
            emotion = segment['emotion']
            
            segment_path = os.path.join(temp_dir, f'tts_{timestamp}_seg{idx}.mp3')
            print(f"Segment {idx} [{emotion}]: rate={rate}, pitch={pitch}")
            
            # Add delay to avoid rate limiting (except for first segment)
            if idx > 0:
                import time
                # Optimized delay: faster but still prevents rate limiting
                base_delay = 0.8  # Reduced from 2.0s
                increment = min(idx * 0.1, 1.2)  # Reduced increment
                delay = base_delay + increment
                delay = min(delay, 2.0)  # Maximum 2 second delay (reduced from 5s)
                print(f"Waiting {delay:.1f}s before segment {idx}...")
                time.sleep(delay)
            
            # Retry logic for rate limiting with exponential backoff
            max_retries = 10  # Increased retries for 100+ segments
            last_error = None
            
            for retry in range(max_retries):
                try:
                    result = subprocess.run(
                        [sys.executable, script_path, segment_path, voice, segment_text, rate, pitch],
                        capture_output=True,
                        text=True,
                        timeout=90  # Increased timeout for reliability
                    )
                    
                    if result.returncode == 0 and os.path.exists(segment_path):
                        print(f"✓ Segment {idx} generated successfully")
                        # Update progress
                        progress_tracker[task_id]['completed'] = idx + 1
                        break  # Success!
                    else:
                        last_error = result.stderr or result.stdout or "Unknown error"
                        if retry < max_retries - 1:
                            # Faster backoff: 2s, 4s, 8s, 16s... (capped at 20s)
                            wait_time = min(2 * (2 ** retry), 20)
                            print(f"Retry {retry + 1}/{max_retries} for segment {idx} (waiting {wait_time}s)")
                            import time
                            time.sleep(wait_time)
                except Exception as e:
                    last_error = str(e)
                    if retry < max_retries - 1:
                        # Faster backoff for exceptions too
                        wait_time = min(2 * (2 ** retry), 20)
                        print(f"Retry {retry + 1}/{max_retries} for segment {idx} (error: {str(e)[:100]}, waiting {wait_time}s)")
                        import time
                        time.sleep(wait_time)
                    else:
                        print(f"Exception on final retry for segment {idx}: {e}")
            else:
                # All retries failed
                error_msg = f"TTS generation failed for segment {idx} (emotion: {emotion}) after {max_retries} attempts: {last_error[:200]}"
                print(f"ERROR: {error_msg}")
                raise Exception(error_msg)
            
            if not os.path.exists(segment_path):
                raise Exception(f"Audio file was not created for segment {idx}")
            
            segment_files.append(segment_path)
        
        # If multiple segments, concatenate them; otherwise use the single file
        if len(segment_files) == 1:
            temp_path = segment_files[0]
        else:
            # Use ffmpeg directly for concatenation
            temp_path = os.path.join(temp_dir, f'tts_{timestamp}_final.mp3')
            print(f"Concatenating {len(segment_files)} segments using ffmpeg...")
            
            try:
                import imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                
                # Create concat demuxer file
                concat_file = os.path.join(temp_dir, f'concat_{timestamp}.txt')
                with open(concat_file, 'w', encoding='utf-8') as f:
                    for seg_file in segment_files:
                        # Use forward slashes and escape special chars
                        safe_path = seg_file.replace('\\', '/').replace("'", "'\\''")
                        f.write(f"file '{safe_path}'\n")
                
                # Run ffmpeg concat
                print(f"Running ffmpeg to merge {len(segment_files)} audio files...")
                result = subprocess.run(
                    [ffmpeg_exe, '-f', 'concat', '-safe', '0', '-i', concat_file,
                     '-c', 'copy', '-y', temp_path],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes for 100+ segments
                )
                
                # Debug: Print ffmpeg output
                if result.stdout:
                    print(f"ffmpeg stdout: {result.stdout}")
                if result.stderr:
                    print(f"ffmpeg stderr: {result.stderr}")
                
                # Clean up concat file
                try:
                    os.remove(concat_file)
                except Exception as clean_err:
                    print(f"Warning: Could not remove concat file: {clean_err}")
                
                if result.returncode == 0 and os.path.exists(temp_path):
                    print(f"Successfully concatenated {len(segment_files)} segments")
                    # Clean up segment files
                    for seg_file in segment_files:
                        try:
                            os.remove(seg_file)
                        except:
                            pass
                else:
                    raise Exception(f"ffmpeg failed: {result.stderr}")
                        
            except Exception as e:
                print(f"ffmpeg concatenation failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                
                # Fallback: use first segment only
                print("Warning: Using first segment only due to concatenation error.")
                temp_path = segment_files[0]
        
        print(f"Saving to: {temp_path}")
        
        if not os.path.exists(temp_path):
            raise Exception(f"Audio file was not created at {temp_path}")
        
        print(f"File size: {os.path.getsize(temp_path)} bytes")
        print(f"Audio generated successfully: {temp_path}")
        
        # Return the audio file
        return send_file(
            temp_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f'tts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp3'
        )
        
    except Exception as e:
        print(f"ERROR in generate_speech: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up progress tracker after some time
        if task_id and task_id in progress_tracker:
            import threading
            threading.Timer(60.0, lambda tid=task_id: progress_tracker.pop(tid, None)).start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
