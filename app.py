#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageOps
import subprocess
import os
from pathlib import Path

app = Flask(__name__)

# Bepaal de werkdirectory
WORK_DIR = Path(__file__).parent.resolve()

# Uploadmap en huidige foto in de werkdirectory
UPLOAD_FOLDER = WORK_DIR / "uploads"
CURRENT_IMAGE = UPLOAD_FOLDER / "current_beamer_image.jpg"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Maak de map aan als die niet bestaat
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
BEAMER_RESOLUTION = (1920, 1080)  # Pas aan naar jouw beamer

feh_process = None

@app.route('/')
def index():
    """Toon de upload pagina"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """Handle foto upload en projectie"""
    global feh_process
    
    try:
        # Check of er een foto is
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': 'Geen foto gevonden'})
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Geen bestand geselecteerd'})
        
        # Rotation parameter
        rotation = int(request.form.get('rotation', 0))
        
        # Open en bewerk de foto
        img = Image.open(file.stream)
        
        # Converteer naar RGB (voor het geval het een PNG met alpha is)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # Roteer indien nodig
        if rotation != 0:
            img = img.rotate(-rotation, expand=True)
        
        # Behoud aspect ratio en fit binnen beamer resolutie
        img.thumbnail(BEAMER_RESOLUTION, Image.Resampling.LANCZOS)
        
        # Sla op
        img.save(CURRENT_IMAGE, 'JPEG', quality=95)
        
        # Stop huidige feh process als die er is
        if feh_process and feh_process.poll() is None:
            feh_process.terminate()
            feh_process.wait(timeout=2)
        
        # Start feh om de foto te tonen
        feh_process = subprocess.Popen([
            'feh',
            '--fullscreen',
            '--hide-pointer',
            '--auto-zoom',
            '--borderless',
            CURRENT_IMAGE
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return jsonify({'success': True, 'message': 'Foto wordt geprojecteerd!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop', methods=['POST'])
def stop_projection():
    """Stop de huidige projectie"""
    global feh_process
    
    try:
        if feh_process and feh_process.poll() is None:
            feh_process.terminate()
            feh_process.wait(timeout=2)
            return jsonify({'success': True})
        return jsonify({'success': True, 'message': 'Geen actieve projectie'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def cleanup():
    """Cleanup bij afsluiten"""
    global feh_process
    if feh_process and feh_process.poll() is None:
        feh_process.terminate()
        feh_process.wait(timeout=2)

if __name__ == '__main__':
    import atexit
    atexit.register(cleanup)
    
    import os
    os.environ['DISPLAY'] = ':0'
        
    feh_process = subprocess.Popen([
        'feh',
        '--fullscreen',
        '--hide-pointer',
        '--auto-zoom',
        '--borderless',
        CURRENT_IMAGE
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    
    print("=" * 50)
    print("🚀 Beamer Photo Server gestart!")
    print("=" * 50)
    print(f"📱 Open op je telefoon: http://<pi-ip-adres>:5000")
    print(f"💻 Of lokaal: http://localhost:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)