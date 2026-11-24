"""Wie is wie, zonder echte accounts.

* Elke browser krijgt één onraadbare cookie (`studiebuddy_id`). Daarmee hangen
  we het persoonlijke pakket en de vraaglimiet aan die browser.
* De moderator ontgrendelt `/moderatie` met MODERATIE_CODE of met
  ADMIN_USER + ADMIN_WACHTWOORD. De cookie bevat een HMAC-token, niet het
  wachtwoord. Zonder ingestelde waarden is moderatie open (handig lokaal).
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets

from flask import current_app, request

BROWSER_COOKIE = "studiebuddy_id"
MODERATIE_COOKIE = "sb_mod"
GELDIG_ID = re.compile(r"[A-Za-z0-9_-]{22}")


def browser_id() -> str:
    bestaand = request.cookies.get(BROWSER_COOKIE, "")
    return bestaand if GELDIG_ID.fullmatch(bestaand) else secrets.token_urlsafe(16)


def met_cookie(antwoord, browser: str):
    reactie = current_app.make_response(antwoord)
    reactie.set_cookie(
        BROWSER_COOKIE, browser, max_age=365 * 24 * 3600,
        httponly=True, samesite="Strict", secure=request.is_secure,
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


def moderator_ingesteld() -> bool:
    return bool(os.getenv("MODERATIE_CODE") or (os.getenv("ADMIN_USER") and os.getenv("ADMIN_WACHTWOORD")))


def _moderator_token() -> str:
    geheim = (os.getenv("SECRET_KEY") or os.getenv("MODERATIE_CODE") or "studiebuddy-demo").encode()
    return hmac.new(geheim, b"studiebuddy-moderator", hashlib.sha256).hexdigest()


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
        return True
    return klopt(request.cookies.get(MODERATIE_COOKIE, ""), _moderator_token())


def zet_moderator_cookie(antwoord):
    antwoord.set_cookie(
        MODERATIE_COOKIE, _moderator_token(), max_age=8 * 3600,
        httponly=True, samesite="Lax", secure=request.is_secure,
    )
    return antwoord
