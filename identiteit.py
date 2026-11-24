"""Wie is wie, zonder echte accounts.

* Elke browser krijgt één onraadbare cookie (`studiebuddy_id`). Daarmee hangen
  we het persoonlijke pakket en de vraaglimiet aan die browser.
* De moderator ontgrendelt `/moderatie` met MODERATIE_CODE of met
  ADMIN_USER + ADMIN_WACHTWOORD. De cookie bevat een HMAC-token, niet het
  wachtwoord. Zonder ingestelde waarden is moderatie enkel lokaal open, nooit op Vercel.
* `/admin` (verbruik) vraagt ADMIN_USER + ADMIN_WACHTWOORD via HTTP Basic Auth.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import time
from collections import defaultdict, deque

from flask import current_app, request

BROWSER_COOKIE = "studiebuddy_id"
MODERATIE_COOKIE = "sb_mod"
GELDIG_ID = re.compile(r"[A-Za-z0-9_-]{22}")
OP_VERCEL = bool(os.getenv("VERCEL"))

# shortcut: deze tellers staan in het geheugen, dus per Vercel-instantie en leeg na een koude start;
# het geld (totaal, daglimiet, vragen per browser) wordt wel in de database bewaakt
pogingen = defaultdict(deque)


def client_ip() -> str:
    # Op Vercel zet het platform zelf x-real-ip (niet te vervalsen); lokaal is remote_addr het echte adres.
    return request.headers.get("x-real-ip", request.remote_addr) if OP_VERCEL else request.remote_addr


def recent(soort: str, seconden: float, sleutel: str | None = None):
    """Tijdstippen van recente pogingen (ouder dan `seconden` vallen weg), standaard per IP-adres."""
    nu = time.monotonic()
    rij = pogingen[(soort, sleutel or client_ip())]
    while rij and nu - rij[0] > seconden:
        rij.popleft()
    return rij


def browser_id() -> str:
    """De id uit de cookie, of een nieuwe willekeurige id (niet te raden of over te nemen) als er geen geldige is."""
    bestaand = request.cookies.get(BROWSER_COOKIE, "")
    return bestaand if GELDIG_ID.fullmatch(bestaand) else secrets.token_urlsafe(16)


def met_cookie(antwoord, browser: str):
    reactie = current_app.make_response(antwoord)
    reactie.set_cookie(
        BROWSER_COOKIE, browser, max_age=365 * 24 * 3600,
        httponly=True, samesite="Strict",
        secure=request.is_secure or OP_VERCEL,  # Vercel is altijd https, Flask ziet dat niet achter de proxy
    )
    return reactie


def klopt(gegeven: str, juist: str) -> bool:
    """Vergelijk in constante tijd; lege verwachte waarde matcht nooit."""
    if not juist:
        return False
    return hmac.compare_digest((gegeven or "").encode(), juist.encode())


def login_vereist() -> bool:
    """De hele site achter HTTP Basic Auth zetten (optioneel)."""
    return bool(os.getenv("SITE_USER") and os.getenv("SITE_WACHTWOORD"))


def basislogin_ok() -> bool:
    auth = request.authorization
    return bool(auth and auth.type == "basic"
                and klopt(auth.username, os.getenv("SITE_USER", ""))
                and klopt(auth.password, os.getenv("SITE_WACHTWOORD", "")))


def admin_ingesteld() -> bool:
    return bool(os.getenv("ADMIN_USER") and os.getenv("ADMIN_WACHTWOORD"))


def admin_login_ok() -> bool:
    """HTTP Basic Auth met het beheerdersaccount (voor /admin)."""
    auth = request.authorization
    return bool(auth and auth.type == "basic"
                and klopt(auth.username, os.getenv("ADMIN_USER", ""))
                and klopt(auth.password, os.getenv("ADMIN_WACHTWOORD", "")))


def moderator_ingesteld() -> bool:
    return bool(os.getenv("MODERATIE_CODE") or admin_ingesteld())


def _moderator_token() -> str:
    # Afgeleid van geheime waarden: een vaste tekst zou iedereen met de broncode moderator laten worden.
    # Verander je het wachtwoord, dan zijn alle oude moderatorcookies meteen ongeldig.
    geheim = os.getenv("SECRET_KEY") or "\n".join(
        (os.getenv("MODERATIE_CODE", ""), os.getenv("ADMIN_USER", ""), os.getenv("ADMIN_WACHTWOORD", "")))
    return hmac.new(geheim.encode(), b"studiebuddy-moderator", hashlib.sha256).hexdigest()


def controleer_moderator(gebruiker: str, wachtwoord: str) -> bool:
    """Accepteer de moderatorcode (in één van beide velden) of admin/user + wachtwoord."""
    code = os.getenv("MODERATIE_CODE", "")
    if code and (klopt(gebruiker, code) or klopt(wachtwoord, code)):
        return True
    user = os.getenv("ADMIN_USER", "")
    pw = os.getenv("ADMIN_WACHTWOORD", "")
    return bool(user and pw) and klopt(gebruiker, user) and klopt(wachtwoord, pw)


def is_moderator() -> bool:
    if not moderator_ingesteld():
        return not OP_VERCEL  # lokaal handig open; online nooit zonder ingestelde login
    return klopt(request.cookies.get(MODERATIE_COOKIE, ""), _moderator_token())


def zet_moderator_cookie(antwoord):
    antwoord.set_cookie(
        MODERATIE_COOKIE, _moderator_token(), max_age=8 * 3600,
        httponly=True, samesite="Lax", secure=request.is_secure or OP_VERCEL,
    )
    return antwoord
