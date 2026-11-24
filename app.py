"""
StudieBuddy - webversie met chat, onboarding en moderatie.

Lokaal starten: python app.py  ->  http://127.0.0.1:5000
Vercel: herkent de Flask-app `app` in dit bestand.

Omgevingsvariabelen (in .env of bij Vercel):
  R33_API_KEY             verplicht, voor de AI-chat
  SUPABASE_URL            bv. https://xxxx.supabase.co
  SUPABASE_SERVER_SLEUTEL de service_role-sleutel (of SUPABASE_KEY)
  SITE_USER/SITE_WACHTWOORD  optioneel: hele site achter Basic Auth
  ADMIN_USER/ADMIN_WACHTWOORD of MODERATIE_CODE  moderator-login
  DAG_BUDGET              optioneel: euro per dag (0 = geen limiet)
  MAX_VRAGEN_PER_BROWSER  optioneel: vragen per browser (0 = onbeperkt)
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque

import httpx
from flask import Flask, Response, jsonify, make_response, redirect, request, send_from_directory

import opslag
from assistent import api_fout, bouw_context, laad_verbruik, maak_client, verbruik_slot, vraag_ai
from data_api import bp as data_bp
from identiteit import (
    basislogin_ok, browser_id, controleer_moderator, is_moderator,
    login_vereist, met_cookie, zet_moderator_cookie,
)

client = maak_client()
app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # per upload; Vercel zelf beperkt tot ~4,5 MB
app.register_blueprint(data_bp)

MAX_VRAAG_TEKENS = int(os.getenv("MAX_VRAAG_TEKENS", "500"))
MAX_VRAGEN_PER_BROWSER = int(os.getenv("MAX_VRAGEN_PER_BROWSER", "5"))  # 0 = onbeperkt
MAX_VRAGEN_PER_MINUUT = int(os.getenv("MAX_VRAGEN_PER_MINUUT", "30"))
MAX_LOGIN_FOUTEN = 30  # per IP per kwartier

pogingen = defaultdict(deque)
vragen_per_browser = {}
# shortcut: de geschiedenis staat in het geheugen; na een herstart begint ze leeg.
geschiedenis = defaultdict(list)


def recent(soort, seconden, sleutel=None):
    """Tijdstippen van recente pogingen (per IP, of per eigen sleutel); oudere vallen weg."""
    nu = time.monotonic()
    rij = pogingen[(soort, sleutel or request.remote_addr)]
    while rij and nu - rij[0] > seconden:
        rij.popleft()
    return rij


def aantal_gesteld(browser):
    """Aantal vragen van deze browser; de eerste keer geteld uit verbruik.json."""
    if browser not in vragen_per_browser:
        vragen_per_browser[browser] = sum(
            1 for bericht in laad_verbruik().get("berichten", [])
            if bericht.get("browser") == browser
        )
    return vragen_per_browser[browser]


def reserveer_vraag(browser):
    if MAX_VRAGEN_PER_BROWSER <= 0:
        return True
    with verbruik_slot:
        if aantal_gesteld(browser) >= MAX_VRAGEN_PER_BROWSER:
            return False
        vragen_per_browser[browser] += 1
        return True


def resterend(browser):
    if MAX_VRAGEN_PER_BROWSER <= 0:
        return None
    with verbruik_slot:
        return max(0, MAX_VRAGEN_PER_BROWSER - aantal_gesteld(browser))


@app.before_request
def site_login():
    """Optioneel: de hele site achter Basic Auth (zet SITE_USER en SITE_WACHTWOORD)."""
    if not login_vereist():
        return None
    fouten = recent("login", 15 * 60)
    if len(fouten) >= MAX_LOGIN_FOUTEN:
        return Response("Te veel foute pogingen. Probeer het over 15 minuten opnieuw.", 429)
    if basislogin_ok():
        return None
    if request.authorization:
        fouten.append(time.monotonic())
    return Response("Inloggen vereist.", 401, {"WWW-Authenticate": 'Basic realm="StudieBuddy"'})


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/favicon.ico")
def favicon():
    return send_from_directory(app.static_folder + "/img", "favicon.ico")


@app.get("/onboarding")
def onboarding():
    return send_from_directory(app.static_folder, "onboarding.html")


@app.get("/moderatie")
def moderatie():
    if not is_moderator():
        return send_from_directory(app.static_folder, "moderatie-login.html")
    return send_from_directory(app.static_folder, "moderatie.html")


@app.post("/moderatie")
def moderatie_login():
    fouten = recent("moderatie", 15 * 60)
    if len(fouten) >= MAX_LOGIN_FOUTEN:
        return Response("Te veel foute pogingen. Probeer het over 15 minuten opnieuw.", 429)
    gebruiker = request.form.get("gebruiker") or request.form.get("code") or ""
    wachtwoord = request.form.get("wachtwoord") or ""
    if controleer_moderator(gebruiker, wachtwoord):
        return zet_moderator_cookie(make_response(redirect("/moderatie", code=303)))
    fouten.append(time.monotonic())
    return redirect("/moderatie?fout=1", code=303)


@app.post("/api/chat")
def chat():
    gegevens = request.get_json(silent=True)
    if not isinstance(gegevens, dict) or not isinstance(gegevens.get("vraag"), str):
        return jsonify(fout="Ongeldige aanvraag"), 400
    vraag = gegevens["vraag"].strip()
    if not vraag:
        return jsonify(fout="Lege vraag"), 400
    if len(vraag) > MAX_VRAAG_TEKENS:
        return jsonify(fout=f"Je vraag is te lang (max. {MAX_VRAAG_TEKENS} tekens)."), 400
    context_aan = bool(gegevens.get("context", True))
    browser = browser_id()

    vragen = recent("chat", 60, sleutel="hele site")
    if len(vragen) >= MAX_VRAGEN_PER_MINUUT:
        antwoord = jsonify(fout="Het is even druk. Wacht een minuutje en probeer opnieuw."), 429
    elif not reserveer_vraag(browser):
        antwoord = (jsonify(fout=f"Je hebt je {MAX_VRAGEN_PER_BROWSER} vragen voor deze demo gebruikt. "
                                 "Bedankt om StudieBuddy te testen!"), 429)
    else:
        vragen.append(time.monotonic())
        eigen_vragen = geschiedenis[browser]
        eigen_vragen.append(vraag)
        try:
            eigen_fiches = opslag.fiche_teksten(browser) if context_aan else {}
            tekst = vraag_ai(client, vraag, bouw_context(context_aan, eigen_vragen, eigen_fiches), context_aan, browser)
        except httpx.HTTPError as fout:
            # Mislukte oproep telt niet mee (ook verbindingsfouten en timeouts).
            with verbruik_slot:
                if MAX_VRAGEN_PER_BROWSER > 0:
                    vragen_per_browser[browser] = max(0, vragen_per_browser.get(browser, 1) - 1)
            tekst = api_fout(fout) if isinstance(fout, httpx.HTTPStatusError) else \
                "[Verbindingsfout] StudieBuddy kan de server even niet bereiken. Probeer het zo opnieuw; deze vraag telt niet mee."
        antwoord = jsonify(antwoord=tekst, vorige_vragen=eigen_vragen[-5:], resterend=resterend(browser))

    return met_cookie(antwoord, browser)


@app.get("/api/status")
def status():
    """Bij het laden: hoeveel vragen nog over en de eigen vorige vragen (per browsercookie)."""
    browser = browser_id()
    if browser != request.cookies.get("studiebuddy_id"):
        over = MAX_VRAGEN_PER_BROWSER if MAX_VRAGEN_PER_BROWSER > 0 else None
        vorige = []
    else:
        over = resterend(browser)
        vorige = geschiedenis.get(browser, [])[-5:]
    return met_cookie(jsonify(resterend=over, max_vragen=MAX_VRAGEN_PER_BROWSER, vorige_vragen=vorige), browser)


@app.errorhandler(413)
def te_groot(_):
    return jsonify(fout="Het bestand is te groot. Op Vercel mag een upload max. 4,5 MB zijn."), 413


if __name__ == "__main__":
    app.run(debug=False)
