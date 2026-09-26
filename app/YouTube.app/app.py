import sys
import subprocess
import json
import re
from flask import Flask, render_template, request, Response, jsonify, stream_with_context

app = Flask(__name__)

def extract_video_id(url_or_id):
    if not url_or_id:
        return None
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    match = re.search(r'(?:v=|\/([0-9A-Za-z_-]{11})|youtu\.be\/)([0-9A-Za-z_-]{11})', url_or_id)
    if match:
        return match.group(1) or match.group(2)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/watch')
def watch_page():
    return render_template('index.html')

@app.route('/api/search')
def search_videos():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    # Execute search query using yt-dlp simulation without flat-playlist constraint
    cmd = [
        sys.executable, '-m', 'yt_dlp',
        '--js-runtimes', 'node',
        '--dump-json',
        '--no-download',
        f'ytsearch12:{query}'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if result.returncode != 0:
            return jsonify({"error": "Failed to perform search"}), 500

        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                # Handle both single video objects and playlist container entries if returned
                entries = data.get('entries', [data]) if data.get('_type') == 'playlist' else [data]
                
                for entry in entries:
                    vid_id = entry.get('id')
                    if not vid_id:
                        continue
                    
                    # Fallback thumbnail construction if missing
                    thumb = entry.get('thumbnail')
                    if not thumb and vid_id:
                        thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

                    videos.append({
                        'id': vid_id,
                        'title': entry.get('title') or 'Untitled',
                        'duration': entry.get('duration_string') or 'N/A',
                        'uploader': entry.get('uploader') or entry.get('channel') or 'Unknown',
                        'thumbnail': thumb
                    })
            except json.JSONDecodeError:
                continue

        return jsonify(videos[:12])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/formats')
def get_formats():
    raw_input = request.args.get('v')
    video_id = extract_video_id(raw_input)
    if not video_id:
        return jsonify({"error": "Invalid ID"}), 400

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    cmd = [
        sys.executable, '-m', 'yt_dlp',
        '--js-runtimes', 'node',
        '--dump-json',
        video_url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            return jsonify({"error": "Failed to fetch video info"}), 500

        data = json.loads(result.stdout)
        
        formats = []
        for f in data.get('formats', []):
            if f.get('vcodec') != 'none' and f.get('height'):
                formats.append({
                    'format_id': f.get('format_id'),
                    'resolution': f'{f.get("height")}p',
                    'ext': f.get('ext')
                })

        seen = set()
        unique_formats = []
        for fmt in sorted(formats, key=lambda x: int(x['resolution'][:-1]), reverse=True):
            if fmt['resolution'] not in seen:
                seen.add(fmt['resolution'])
                unique_formats.append(fmt)

        subtitles = []
        subs_data = data.get('subtitles', {}) or data.get('automatic_captions', {})
        for lang, subs in subs_data.items():
            for sub in subs:
                if sub.get('ext') in ['vtt', 'srt']:
                    subtitles.append({'lang': lang, 'url': sub.get('url')})
                    break

        return jsonify({
            'title': data.get('title'),
            'formats': unique_formats,
            'subtitles': subtitles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stream')
def stream_video():
    raw_input = request.args.get('v')
    format_id = request.args.get('format_id', 'best[ext=mp4]/best')
    video_id = extract_video_id(raw_input)
    
    if not video_id:
        return "Invalid YouTube URL or ID", 400

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    format_arg = format_id if format_id else 'best[ext=mp4]/best'

    cmd = [
        sys.executable,
        '-m',
        'yt_dlp',
        '--js-runtimes', 'node',
        '-f', f'{format_arg}+bestaudio/best',
        '-o', '-',
        video_url
    ]

    def generate():
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1024 * 64
        )
        try:
            for chunk in iter(lambda: process.stdout.read(64 * 1024), b''):
                yield chunk
        except Exception as e:
            print(f"Streaming exception: {e}")
        finally:
            process.kill()
            process.wait()

    return Response(
        stream_with_context(generate()),
        mimetype='video/mp4',
        headers={
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'no-cache'
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)