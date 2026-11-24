"""
StudieBuddy - webversie met een simpele chatinterface.

Hergebruikt alle logica uit assistent.py; enkel de in- en uitvoer verloopt
via de browser in plaats van de terminal.

Lokaal starten: python app.py  ->  http://127.0.0.1:5000
Vercel: herkent de Flask-app `app` in dit bestand automatisch (zet R33_API_KEY, SUPABASE_URL en SUPABASE_KEY bij Environment Variables).
"""

import hmac
import os
import re
import secrets
import threading
import time
from collections import defaultdict, deque

import httpx
from flask import Flask, Response, jsonify, request, send_from_directory

from assistent import api_fout, bouw_context, laad_verbruik, maak_client, verbruik_slot, vraag_ai

client = maak_client()
app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # weigert reuzegrote aanvragen meteen (413)

SITE_USER = os.getenv("SITE_USER")
SITE_WACHTWOORD = os.getenv("SITE_WACHTWOORD")
if not SITE_USER or not SITE_WACHTWOORD:
    raise SystemExit("Zet SITE_USER en SITE_WACHTWOORD in het .env bestand.")


MAX_VRAAG_TEKENS = 500        # lange vragen = veel input-tokens
MAX_VRAGEN_PER_BROWSER = 5    # PoC: elke browser mag in totaal 5 vragen stellen
MAX_VRAGEN_PER_MINUUT = 30    # voor de hele site samen: op de hackathon zit iedereen op hetzelfde IP
MAX_LOGIN_FOUTEN = 30         # per IP-adres per kwartier, tegen wachtwoord raden (ruim, want gedeeld wifi)

BROWSER_COOKIE = "studiebuddy_id"
GELDIG_ID = re.compile(r"[A-Za-z0-9_-]{22}")

# shortcut: deze tellers staan in het geheugen (leeg na herstart); de daglimiet en de vragen per browser staan op schijf
pogingen = defaultdict(deque)
vragen_per_browser = {}  # browser-id -> aantal gestelde vragen (startwaarde uit verbruik.json)
# shortcut: de geschiedenis staat enkel in het geheugen, na een herstart begint ze leeg (de limiet telt wel verder)
geschiedenis = defaultdict(list)  # browser-id -> eigen vragen, voor de zijbalk en de keuze van de ECTS-fiche


def recent(soort, seconden, sleutel=None):
    """Tijdstippen van recente pogingen (ouder dan `seconden` vallen weg), standaard per IP-adres."""
    # shortcut: achter een proxy (bv. Vercel) delen alle bezoekers misschien één remote_addr; X-Forwarded-For niet vertrouwen, dat kan iedereen vervalsen
    nu = time.monotonic()
    q = pogingen[(soort, sleutel or request.remote_addr)]
    while q and nu - q[0] > seconden:
        q.popleft()
    return q


def browser_id():
    """De id uit de cookie, of een nieuwe willekeurige id (niet te raden of over te nemen) als er geen geldige is."""
    b = request.cookies.get(BROWSER_COOKIE, "")
    return b if GELDIG_ID.fullmatch(b) else secrets.token_urlsafe(16)


def met_cookie(antwoord, browser):
    r = app.make_response(antwoord)
    r.set_cookie(BROWSER_COOKIE, browser, max_age=365 * 24 * 3600, httponly=True, samesite="Strict", secure=request.is_secure)
    return r


def aantal_gesteld(browser):
    """Aantal vragen van deze browser; de eerste keer geteld uit verbruik.json. Enkel oproepen met verbruik_slot vast."""
    if browser not in vragen_per_browser:
        vragen_per_browser[browser] = sum(1 for b in laad_verbruik().get("berichten", []) if b.get("browser") == browser)
    return vragen_per_browser[browser]


def reserveer_vraag(browser):
    """Telt een vraag voor deze browser vóór de AI-oproep, zodat gelijktijdige vragen de limiet niet omzeilen."""
    with verbruik_slot:
        if aantal_gesteld(browser) >= MAX_VRAGEN_PER_BROWSER:
            return False
        vragen_per_browser[browser] += 1
        return True


def klopt(gegeven, juist):
    return hmac.compare_digest((gegeven or "").encode(), juist.encode())  # constante tijd: geen info via timing


@app.before_request
def login_vereist():
    """De browser vraagt eerst gebruikersnaam en wachtwoord (HTTP Basic Auth), voor elke pagina en API-oproep."""
    # shortcut: één gedeeld account voor de hele site, geen login per student; dat komt met Supabase Auth in fase 1
    fouten = recent("login", 15 * 60)
    if len(fouten) >= MAX_LOGIN_FOUTEN:
        return Response("Te veel foute pogingen. Probeer het over 15 minuten opnieuw.", 429)
    a = request.authorization
    if not (a and a.type == "basic" and klopt(a.username, SITE_USER) and klopt(a.password, SITE_WACHTWOORD)):
        if a:
            fouten.append(time.monotonic())
        return Response("Inloggen vereist.", 401, {"WWW-Authenticate": 'Basic realm="StudieBuddy"'})


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("vraag"), str):
        return jsonify(fout="Ongeldige aanvraag"), 400
    vraag = data["vraag"].strip()
    if not vraag:
        return jsonify(fout="Lege vraag"), 400
    if len(vraag) > MAX_VRAAG_TEKENS:
        return jsonify(fout=f"Je vraag is te lang (max. {MAX_VRAAG_TEKENS} tekens)."), 400
    context_aan = bool(data.get("context", True))

    # shortcut: wie cookies wist of een incognitovenster opent, krijgt opnieuw 5 vragen; de daglimiet blijft wel gelden
    browser = browser_id()

    vragen = recent("chat", 60, sleutel="hele site")
    if len(vragen) >= MAX_VRAGEN_PER_MINUUT:
        antwoord = jsonify(fout="Het is even druk. Wacht een minuutje en probeer opnieuw."), 429
    elif not reserveer_vraag(browser):
        antwoord = jsonify(fout=f"Je hebt je {MAX_VRAGEN_PER_BROWSER} vragen voor deze demo gebruikt. Bedankt om StudieBuddy te testen!"), 429
    else:
        vragen.append(time.monotonic())
        eigen_vragen = geschiedenis[browser]
        eigen_vragen.append(vraag)
        try:
            tekst = vraag_ai(client, vraag, bouw_context(context_aan, eigen_vragen), context_aan, browser)
        except httpx.HTTPError as fout:  # ook verbindingsfouten en timeouts, niet enkel foute statuscodes
            with verbruik_slot:
                vragen_per_browser[browser] -= 1  # mislukte oproep telt niet mee
            tekst = api_fout(fout) if isinstance(fout, httpx.HTTPStatusError) else \
                "[Verbindingsfout] StudieBuddy kan de server even niet bereiken. Probeer het zo opnieuw; deze vraag telt niet mee."
        antwoord = jsonify(antwoord=tekst, vorige_vragen=eigen_vragen[-5:],
                           resterend=MAX_VRAGEN_PER_BROWSER - vragen_per_browser[browser])

    return met_cookie(antwoord, browser)


@app.get("/api/status")
def status():
    """Bij het laden van de pagina: hoeveel vragen nog over en de eigen vorige vragen, zodat een refresh niets reset."""
    browser = browser_id()
    if browser != request.cookies.get(BROWSER_COOKIE):
        resterend = MAX_VRAGEN_PER_BROWSER  # nieuwe browser: niets opzoeken, en geen lege tellers aanmaken
    else:
        with verbruik_slot:
            resterend = max(0, MAX_VRAGEN_PER_BROWSER - aantal_gesteld(browser))
    return met_cookie(jsonify(resterend=resterend, max_vragen=MAX_VRAGEN_PER_BROWSER,
                              vorige_vragen=geschiedenis.get(browser, [])[-5:]), browser)


if __name__ == "__main__":
    app.run(debug=False)
