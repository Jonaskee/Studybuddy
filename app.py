"""
StudieBuddy - webversie met chat, onboarding, moderatie en verbruiksoverzicht.

Lokaal starten: python app.py  ->  http://127.0.0.1:5000
Vercel: herkent de Flask-app `app` in dit bestand. Alle omgevingsvariabelen staan in ONBOARDING.md.

Pagina's: /  (chat)  ·  /onboarding  ·  /moderatie (pakketten nakijken)  ·  /admin (verbruik en kosten)
"""

from __future__ import annotations

import os
import time
from datetime import datetime

import httpx
from flask import Flask, Response, jsonify, make_response, redirect, render_template, request, send_from_directory

import assistent
import opslag
from assistent import Limiet, api_fout, maak_client, rpc, vakken_voor, vraag_ai
from data_api import bp as data_bp
from identiteit import (
    BROWSER_COOKIE, admin_ingesteld, admin_login_ok, basislogin_ok, browser_id, controleer_moderator,
    is_moderator, login_vereist, met_cookie, recent, zet_moderator_cookie,
)

client = maak_client()
app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # voor de PDF-upload; Vercel laat zelf max. ~4,5 MB per request door
app.register_blueprint(data_bp)

MAX_VRAAG_TEKENS = int(os.getenv("MAX_VRAAG_TEKENS", "500"))              # lange vragen = veel input-tokens
MAX_VRAGEN_PER_BROWSER = int(os.getenv("MAX_VRAGEN_PER_BROWSER", "5"))    # 0 = onbeperkt (geteld in de database)
MAX_VRAGEN_PER_MINUUT = int(os.getenv("MAX_VRAGEN_PER_MINUUT", "30"))     # hele site samen: op de hackathon één IP
MAX_LOGIN_FOUTEN = 30  # per IP-adres per kwartier, tegen wachtwoord raden (ruim, want gedeeld wifi)
ONBEPERKT = 1_000_000  # wat "0 = onbeperkt" voor de databank betekent


def max_per_browser():
    return MAX_VRAGEN_PER_BROWSER if MAX_VRAGEN_PER_BROWSER > 0 else ONBEPERKT


@app.before_request
def site_login():
    """Login: /admin vraagt het beheerdersaccount (HTTP Basic Auth), de rest de sitelogin (als die ingesteld is)."""
    beheer = request.path == "/admin" or request.path.startswith("/admin/")
    if beheer and not admin_ingesteld():
        return Response("Niet gevonden.", 404)
    if not beheer and not login_vereist():
        return None
    fouten = recent("login", 15 * 60)
    if len(fouten) >= MAX_LOGIN_FOUTEN:
        return Response("Te veel foute pogingen. Probeer het over 15 minuten opnieuw.", 429)
    if admin_login_ok() if beheer else basislogin_ok():
        return None
    if request.authorization:
        fouten.append(time.monotonic())
    # Een andere realm, zodat de browser voor /admin apart om het beheerderswachtwoord vraagt.
    realm = "StudieBuddy beheer" if beheer else "StudieBuddy"
    return Response("Inloggen vereist.", 401, {"WWW-Authenticate": f'Basic realm="{realm}"'})


@app.after_request
def beveiligingsheaders(r):
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["X-Frame-Options"] = "DENY"  # niet in een iframe van een andere site (clickjacking)
    r.headers["Referrer-Policy"] = "no-referrer"
    # Achter een login: pagina's en API niet cachen; afbeeldingen, css en js mag de browser even bijhouden.
    r.headers["Cache-Control"] = "private, max-age=3600" if request.path.startswith("/static/") else "no-store"
    # Enkel eigen scripts en stijl (inline, want de pagina's hebben inline code) plus de lettertypes van Google Fonts.
    r.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
    return r


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


def studiecontext(browser):
    """De vakken waarover de AI antwoordt: met een pakket uit de onboarding enkel die van de student, met zijn
    eigen geüploade PDF's; zonder pakket (of als de opslag even weg is) alle standaardfiches."""
    try:
        volledig = opslag.haal_mijn_pakket_volledig(browser)
    except (opslag.OpslagFout, httpx.HTTPError):
        return vakken_voor()
    if not volledig:
        return vakken_voor()
    gevolgd = [{"naam": v.get("naam"), "sp": v.get("sp")} for v in volledig["vakken"]]
    return vakken_voor(gevolgd, opslag.fiche_teksten(browser, volledig))


@app.post("/api/chat")
def chat():
    # Enkel JSON: een formulier van een andere site kan dit niet versturen (CSRF), en fetch van een andere site wordt door CORS geblokkeerd.
    gegevens = request.get_json(silent=True)
    if not isinstance(gegevens, dict) or not isinstance(gegevens.get("vraag"), str):
        return jsonify(fout="Ongeldige aanvraag"), 400
    vraag = gegevens["vraag"].strip()
    if not vraag:
        return jsonify(fout="Lege vraag"), 400
    if len(vraag) > MAX_VRAAG_TEKENS:
        return jsonify(fout=f"Je vraag is te lang (max. {MAX_VRAAG_TEKENS} tekens)."), 400
    context_aan = bool(gegevens.get("context", True))

    # shortcut: wie cookies wist of een incognitovenster opent, krijgt opnieuw 5 vragen; de daglimiet blijft wel gelden
    browser = browser_id()

    vragen = recent("chat", 60, sleutel="hele site")
    if len(vragen) >= MAX_VRAGEN_PER_MINUUT:
        return met_cookie((jsonify(fout="Het is even druk. Wacht een minuutje en probeer opnieuw."), 429), browser)
    vragen.append(time.monotonic())

    try:
        vakken = studiecontext(browser) if context_aan else None
        tekst, resterend, eigen_vragen, bronnen = vraag_ai(client, vraag, context_aan, browser, max_per_browser(), vakken)
    except Limiet as fout:
        return met_cookie((jsonify(fout=str(fout)), 429), browser)
    except httpx.HTTPError as fout:  # route33 of Supabase onbereikbaar of fout; de vraag is dan al teruggegeven
        return met_cookie(jsonify(antwoord=api_fout(fout)), browser)
    # bronnen = de ECTS-secties die het antwoord citeert, met hun tekst, zodat de student het zelf kan nalezen
    return met_cookie(jsonify(antwoord=tekst, vorige_vragen=eigen_vragen[-5:],
                              resterend=resterend if MAX_VRAGEN_PER_BROWSER > 0 else None,
                              bronnen=bronnen if context_aan else None), browser)


@app.get("/api/status")
def status():
    """Bij het laden van de pagina: hoeveel vragen nog over en de eigen vorige vragen, zodat een refresh niets reset."""
    browser = browser_id()
    if browser != request.cookies.get(BROWSER_COOKIE):
        s = {"resterend": max_per_browser(), "vragen": []}  # nieuwe browser: niets op te zoeken
    else:
        try:
            s = rpc("browser_status", p_browser=browser, p_max_per_browser=max_per_browser())
        except httpx.HTTPError as fout:
            api_fout(fout)
            return jsonify(fout="Status even niet beschikbaar."), 503
    return met_cookie(jsonify(resterend=s["resterend"] if MAX_VRAGEN_PER_BROWSER > 0 else None,
                              max_vragen=MAX_VRAGEN_PER_BROWSER, vorige_vragen=s["vragen"]), browser)


@app.template_filter("euro")
def euro(bedrag, decimalen=4):
    return f"€{float(bedrag):.{decimalen}f}".replace(".", ",")


@app.template_filter("getal")
def getal(n):
    """Belgische notatie: 1.284 · 12,9K · 1,2M."""
    n = int(n)
    if n < 10_000:
        return f"{n:,}".replace(",", ".")
    grens, letter = (1_000_000, "M") if n >= 1_000_000 else (1_000, "K")
    return f"{n / grens:.1f}".replace(".", ",") + letter


def mooi_maximum(n):
    """Afgeronde top voor de y-as: 1, 2, 5, 10, 20, 50, ..."""
    stap = 1
    while True:
        for f in (1, 2, 5):
            if f * stap >= n:
                return f * stap
        stap *= 10


@app.get("/admin")
def admin():
    """Beheerpagina: kosten, tokens, berichten en sessies, rechtstreeks uit de database."""
    try:
        s = rpc("admin_statistieken")
    except httpx.HTTPError as fout:
        api_fout(fout)
        return Response("Statistieken even niet beschikbaar.", 503)
    piek = max(u["berichten"] for u in s["per_uur"])
    return render_template("admin.html", s=s, budget=assistent.BUDGET, dag_budget=assistent.DAG_BUDGET,
                           max_per_browser=MAX_VRAGEN_PER_BROWSER, piek=piek, y_max=mooi_maximum(piek),
                           nu=datetime.now(assistent.TIJDZONE))


@app.errorhandler(413)
def te_groot(_):
    return jsonify(fout="Het bestand is te groot. Een PDF mag max. 4 MB zijn."), 413


if __name__ == "__main__":
    app.run(debug=False)
