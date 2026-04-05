import os
import sys
import numpy as np
import pretty_midi
from scipy.io import wavfile
from flask import Flask, render_template, request, send_file, jsonify
import tempfile
import webbrowser
from threading import Timer

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
SHARED_DIR = os.path.join(PROJECT_ROOT, 'shared')

if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

import midi_to_wave

# PyInstaller compatibility for template and static files
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__, template_folder=os.path.join(CURRENT_DIR, 'templates'), static_folder=os.path.join(CURRENT_DIR, 'static'))

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5002")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/synthesise', methods=['POST'])
def synthesise():
    if 'midi_file' not in request.files:
        return jsonify({"error": "No MIDI file uploaded"}), 400
    
    file = request.files['midi_file']
    sample_rate = int(request.form.get('rate', 48000))

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Extract up to 3 waveform layers
    wave_layers = []
    for i in range(1, 4):
        w_type = request.form.get(f'wave_type{i}')
        if w_type:
            vol = float(request.form.get(f'vol{i}', 0.0))
            if vol > 0:
                duty = float(request.form.get(f'duty{i}', 0.5))
                wave_layers.append({
                    'type': w_type,
                    'duty': duty,
                    'volume': vol
                })

    if not wave_layers:
        # Default to a single square wave if no layers provided with volume > 0
        wave_layers = [{'type': 'pulse', 'duty': 0.5, 'volume': 1.0}]

    try:
        # Save MIDI to temporary file
        temp_midi = tempfile.NamedTemporaryFile(delete=False, suffix='.mid')
        file.save(temp_midi.name)
        
        # Save WAV to temporary file
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        # Run synthesis from our module
        midi_to_wave.midi_to_audio(temp_midi.name, temp_wav.name, sample_rate, wave_layers)
        
        # Cleanup MIDI
        os.unlink(temp_midi.name)
        
        # Construct original filename without extension
        original_filename = "output"
        if file.filename:
            original_filename = os.path.splitext(file.filename)[0]
        
        # Indicate mixing in the filename if multiple layers
        suffix = "mix" if len(wave_layers) > 1 else wave_layers[0]['type']
        download_name = f"{original_filename}_{suffix}.wav"
        
        return send_file(temp_wav.name, as_attachment=True, download_name=download_name)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Open browser automatically after 1 second
    Timer(1, open_browser).start()
    print("DEBUG: SERVER RUNNING ON PORT 5002")
    app.run(host='127.0.0.1', port=5002, debug=False)
