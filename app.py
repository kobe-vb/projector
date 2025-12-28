#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify
from PIL import Image
import os
from pathlib import Path
import threading
import atexit

# Setup display
os.environ['DISPLAY'] = ':0'

from game.main import Game

app = Flask(__name__)

# Bepaal de werkdirectory
WORK_DIR = Path(__file__).parent.resolve()

# Uploadmap en huidige foto in de werkdirectory
UPLOAD_FOLDER = WORK_DIR / "uploads"
CURRENT_IMAGE = UPLOAD_FOLDER / "current_beamer_image.jpg"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Configuratie
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
BEAMER_RESOLUTION = (1920, 1080)

# Game instance (wordt in main thread geïnitialiseerd)
game = None

@app.route('/')
def index():
    """Toon de upload pagina"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """Handle foto upload en projectie"""
    global game
    
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
        rotation += 90
        if rotation != 0:
            img = img.rotate(-rotation, expand=True)
        
        # Behoud aspect ratio en fit binnen beamer resolutie
        img.thumbnail(BEAMER_RESOLUTION, Image.Resampling.LANCZOS)
        
        # Sla op
        img.save(CURRENT_IMAGE, 'JPEG', quality=95)
        
        # Update game (thread-safe via flag)
        if game:
            game.new_image_uploaded = True
        
        return jsonify({'success': True, 'message': 'Foto wordt geprojecteerd!'})
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop', methods=['POST'])
def stop_projection():
    """Stop de huidige projectie"""
    global game
    
    try:
        if game:
            game.edit_mode = False
            return jsonify({'success': True, 'message': 'Edit mode uitgeschakeld'})
        return jsonify({'success': True, 'message': 'Geen actieve game'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/status', methods=['GET'])
def status():
    """Get current status"""
    if game:
        return jsonify({
            'success': True,
            'edit_mode': game.edit_mode,
            'zoom': game.zoom,
            'current_corner': game.current_corner
        })
    return jsonify({'success': False, 'error': 'Game niet gestart'})

def run_flask():
    """Run Flask in een aparte thread"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)

def cleanup():
    """Cleanup bij afsluiten"""
    global game
    if game:
        print("🛑 Stopping game...")
        game.done = True

if __name__ == '__main__':
    atexit.register(cleanup)
    
    print("=" * 50)
    print("🚀 Beamer Photo Server gestart!")
    print("=" * 50)
    
    # Start Flask in aparte thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("✅ Flask server gestart in aparte thread")
    
    print(f"📱 Open op je telefoon: http://<pi-ip-adres>:5000")
    print(f"💻 Of lokaal: http://localhost:5000")
    print("=" * 50)
    print("🎮 Controller instructies:")
    print("  - A button: Selecteer volgende hoek")
    print("  - Joystick: Beweeg geselecteerde hoek")
    print("  - L1/R1: Zoom uit/in")
    print("  - D-pad: Pan (verschuif beeld)")
    print("  - B button: Opslaan en exit edit mode")
    print("=" * 50)
    
    # Start pygame in de MAIN thread (vereist voor display)
    game = Game()
    game.run()  # Blokkeert hier, maar Flask draait in thread