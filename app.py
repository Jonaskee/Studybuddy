"""
StudieBuddy - webversie met een simpele chatinterface.

Hergebruikt alle logica uit assistent.py; enkel de in- en uitvoer verloopt
via de browser in plaats van de terminal.

Lokaal starten: python app.py  ->  http://127.0.0.1:5000
Vercel: herkent de Flask-app `app` in dit bestand automatisch (zet R33_API_KEY bij Environment Variables).
"""

import httpx
from flask import Flask, jsonify, request, send_from_directory

from assistent import api_fout, bouw_context, maak_client, sessie, vraag_ai

client = maak_client()
app = Flask(__name__, static_folder="static")


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.post("/api/chat")
def chat():
    data = request.get_json(force=True)
    vraag = (data.get("vraag") or "").strip()
    if not vraag:
        return jsonify(fout="Lege vraag"), 400
    context_aan = bool(data.get("context", True))

    # shortcut: sessie is globaal, op Vercel dus gedeeld door alle bezoekers en leeg na een koude start; per gebruiker bijhouden zodra meerdere studenten het gebruiken
    sessie["vragen"].append(vraag)
    try:
        antwoord = vraag_ai(client, vraag, bouw_context(context_aan), context_aan)
    except httpx.HTTPStatusError as fout:
        antwoord = api_fout(fout)
    return jsonify(antwoord=antwoord, vorige_vragen=sessie["vragen"][-5:])


if __name__ == "__main__":
    app.run(debug=False)
