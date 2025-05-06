from flask import Flask, request, send_file, Response
import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()
app = Flask(__name__)

# Configurar APIs
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Voz pública Rachel


@app.route('/')
def index():
    return '🤖 Julie está en línea.'


@app.route('/start', methods=['GET', 'POST'])
def start():
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech" action="/call" method="POST" timeout="10">
    <Say>Hola, soy Julie. </Say>
  </Gather>
  <Say>No recibí tu respuesta. Intenta más tarde.</Say>
  <Hangup/>
</Response>"""
    return Response(twiml, mimetype='text/xml')


@app.route('/call', methods=['POST'])
def call():
    try:
        user_input = request.form.get('SpeechResult')
        print("📩 Usuario dijo:", user_input)

        # RESPUESTA FIJA para esta prueba
        reply = "Hola, soy Julie. Estoy lista para ayudarte con lo que necesites."
        print("🧪 Texto para ElevenLabs:", reply)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"respuesta_{timestamp}.mp3"

        # Solicitud sin streaming
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "text": reply,
                "voice_settings": {
                    "stability": 0.6,
                    "similarity_boost": 0.8
                }
            })

        with open(filename, "wb") as f:
            f.write(response.content)

        time.sleep(1.5)

        if os.path.getsize(filename) < 1000:
            print("⚠️ El archivo de audio está vacío o corrupto.")
            return Response("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>No pude generar el audio correctamente. Lo siento.</Say>
  <Hangup/>
</Response>""",
                            mimetype="text/xml")

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>https://{request.host}/{filename}</Play>
  <Pause length="1"/>
  <Gather input="speech" action="/call" method="POST" timeout="10">
    <Say>¿Quieres seguir hablando conmigo?</Say>
  </Gather>
  <Say>No recibí tu respuesta. Hasta luego.</Say>
  <Hangup/>
</Response>"""
        return Response(twiml, mimetype="text/xml")

    except Exception as e:
        print("❌ Error general:", e)
        return Response("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Ocurrió un error en la conversación. Hasta luego.</Say>
  <Hangup/>
</Response>""",
                        mimetype="text/xml")


@app.route('/<filename>')
def serve_audio(filename):
    return send_file(filename, mimetype="audio/mpeg")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
