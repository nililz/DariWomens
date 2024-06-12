import asyncio
import os
from flask import Flask, json, jsonify, render_template, request, send_file, send_from_directory
import edge_tts
from openai import OpenAI
from middleware import middleware

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
client = OpenAI()

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    
# Apply the middleware to the Flask app
middleware(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    recognized_text = "سلام، حال شما چطور است؟"
    
    # Send the recognized text to OpenAI API and get the response
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are helping women in Afghanistan who do not understand English, and output in JSON"},
            {"role": "user", "content": recognized_text}
        ]
    )

    # Extract the answer text from the response JSON
    answer = response.choices[0].message.content

    response_json = response.choices[0].message.content
    response_data = json.loads(response_json)
    answer = response_data.get('response', '')

    # Convert the answer text to speech
    TEXT = answer
    VOICE = "fa-IR-FaridNeural"
    OUTPUT_FILE = "test.mp3"

    async def generate_audio():
        communicate = edge_tts.Communicate(TEXT, VOICE)
        await communicate.save(OUTPUT_FILE)

    loop = request.event_loop
    loop.run_until_complete(generate_audio())

    return jsonify({'text': answer, 'audio': '/audio/test.mp3'})

@app.route('/audio/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)