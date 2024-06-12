import asyncio
import os
from flask import Flask, json, jsonify, render_template, request, send_from_directory
import edge_tts
from werkzeug.utils import secure_filename
from openai import OpenAI
from middleware import middleware

client = OpenAI()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'audio' 
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

ALLOWED_EXTENSIONS = {'wav'} 
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop

def close_event_loop(loop):
    if loop.is_running():
        loop.stop()
    loop.close()

def middleware(flask_app):
    @flask_app.before_request
    def before_request():
        request.event_loop = create_event_loop()

    @flask_app.after_request
    def after_request(response):
        loop = request.event_loop
        close_event_loop(loop)
        return response

middleware(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file part'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected audio file'}), 400

    if audio_file and allowed_file(audio_file.filename):
        filename = secure_filename(audio_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(filepath)

        try:
            with open(filepath, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    response_format="text",
                    language="fa"
                )
        except Exception as e:
            return jsonify({'error': f'Transcription error: {str(e)}'}), 500

        recognized_text = transcription

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[
                    {"role": "system", "content": "You are helping users who may speak Farsi, output in JSON with a 'response' key containing your reply, and a 'language' key indicating the detected language of the input (which should be in Farsi)."},
                    {"role": "user", "content": recognized_text}
                ]
            )
        except Exception as e:
            return jsonify({'error': f'OpenAI API error: {str(e)}'}), 500
        
        try:
            response_json = response.choices[0].message.content
            response_data = json.loads(response_json)
            answer = response_data.get('response', '')
            detected_language = response_data.get('language', 'Unknown') 

            async def generate_audio():
                voice = "fa-IR-FaridNeural" if detected_language == 'Farsi' else "en-US-ChristopherNeural" 
                communicate = edge_tts.Communicate(answer, voice)
                await communicate.save(filepath)  

            loop = request.event_loop
            loop.run_until_complete(generate_audio())

            return jsonify({'text': answer, 'audio': f'/audio/{filename}'})

        except Exception as e:
            return jsonify({'error': f'Error during TTS or response processing: {str(e)}'}), 500

    else:
        return jsonify({'error': 'Audio file type not allowed'}), 400

@app.route('/audio/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)