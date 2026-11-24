"""JSON-API waarop `static/js/data.js` draait.

De UI kent enkel deze endpoints; welke opslag erachter zit (Supabase of het
lokale JSON-bestand) maakt voor de frontend niets uit.
"""

from __future__ import annotations

import sys
import time

from flask import Blueprint, jsonify, request

import opslag
from identiteit import browser_id, is_moderator, met_cookie, recent

bp = Blueprint("data_api", __name__, url_prefix="/api/data")

MAX_SCHRIJVEN = 30           # uploads en wijzigingen per browser per kwartier: houdt spam en opslagkosten tegen
MAX_SCHRIJVEN_SITE = 300     # voor de hele site samen (wie telkens een nieuwe cookie maakt, botst hierop)


@bp.errorhandler(opslag.OpslagFout)
def opslagfout(fout):
    print(f"Opslagfout: {fout}", file=sys.stderr)  # details enkel in de serverlog, niet naar de gebruiker
    return jsonify(fout="De opslag is even niet bereikbaar. Probeer het zo opnieuw."), 503


@bp.errorhandler(opslag.ValidatieFout)
def validatiefout(fout):
    return jsonify(fout=str(fout)), 400


@bp.errorhandler(opslag.WeigeringFout)
def weigeringfout(fout):
    return jsonify(fout=str(fout)), 403


def _fout(melding, code=400):
    return jsonify(fout=melding), code


def _json():
    if (request.content_length or 0) > 256 * 1024:  # de 5 MB-grens is voor PDF's; een pakket in JSON is veel kleiner
        return None
    gegevens = request.get_json(silent=True)
    return gegevens if isinstance(gegevens, dict) else None


def _alleen_moderator():
    return None if is_moderator() else _fout("Alleen moderators mogen dit.", 403)


def _te_veel(browser):
    """429 als deze browser (of de hele site) te veel uploadt of wijzigt; telt deze poging anders mee."""
    eigen, site = recent("schrijven", 15 * 60, sleutel=browser), recent("schrijven", 15 * 60, sleutel="hele site")
    if len(eigen) >= MAX_SCHRIJVEN or len(site) >= MAX_SCHRIJVEN_SITE:
        return _fout("Te veel uploads of wijzigingen na elkaar. Probeer het over een kwartier opnieuw.", 429)
    eigen.append(time.monotonic())
    site.append(time.monotonic())
    return None


# ---------- zoeken ----------

@bp.get("/scholen")
def scholen():
    return met_cookie(jsonify(opslag.zoek_scholen(request.args.get("q", ""))), browser_id())


@bp.get("/richtingen")
def richtingen():
    return met_cookie(jsonify(opslag.zoek_richtingen(request.args.get("school", ""), request.args.get("q", ""))), browser_id())


@bp.get("/vind-richting")
def vind_richting():
    return met_cookie(jsonify(opslag.vind_richting(request.args.get("school", ""), request.args.get("richting", ""))), browser_id())


@bp.get("/pakketten")
def pakketten():
    return met_cookie(jsonify(opslag.haal_pakketten(request.args.get("richtingId", ""))), browser_id())


@bp.get("/pakket/<pakket_id>")
def pakket(pakket_id):
    resultaat = opslag.haal_pakket(pakket_id)
    if resultaat is None:
        return _fout("Pakket niet gevonden.", 404)
    return met_cookie(jsonify(resultaat), browser_id())


@bp.get("/afstudeerrichtingen")
def afstudeerrichtingen():
    return met_cookie(jsonify(opslag.haal_afstudeerrichtingen(request.args.get("richtingId", ""))), browser_id())


# ---------- ECTS-fiches ----------

@bp.post("/fiches")
def fiches():
    browser = browser_id()
    if weigering := _te_veel(browser):
        return weigering
    bestand = request.files.get("bestand")
    if not bestand or not bestand.filename:
        return _fout("Geen PDF ontvangen.")
    inhoud = bestand.read()
    if not inhoud:
        return _fout("Het bestand is leeg.")
    if len(inhoud) > opslag.MAX_FICHE_BYTES:
        return _fout("Het bestand is te groot (max. 4 MB).", 413)
    if not (bestand.mimetype == "application/pdf" or bestand.filename.lower().endswith(".pdf")):
        return _fout("Enkel PDF-bestanden zijn toegestaan.")
    return met_cookie(jsonify(opslag.bewaar_fiche(bestand.filename, inhoud)), browser)


# ---------- pakketten maken ----------

@bp.post("/pakketten")
def maak_pakket():
    gegevens = _json()
    if gegevens is None:
        return _fout("Ongeldige aanvraag.")
    browser = browser_id()
    if weigering := _te_veel(browser):
        return weigering
    return met_cookie(jsonify(opslag.maak_pakket(browser, gegevens)), browser)


@bp.post("/voorstellen")
def voorstel():
    gegevens = _json()
    if gegevens is None:
        return _fout("Ongeldige aanvraag.")
    browser = browser_id()
    if weigering := _te_veel(browser):
        return weigering
    return met_cookie(jsonify(opslag.stel_wijziging_voor(
        browser, str(gegevens.get("pakketId") or ""), gegevens.get("tekst"))), browser)


# ---------- mijn pakket ----------

@bp.get("/mijn-pakket")
def mijn_pakket():
    browser = browser_id()
    return met_cookie(jsonify(opslag.haal_mijn_pakket(browser)), browser)


@bp.get("/mijn-pakket/volledig")
def mijn_pakket_volledig():
    browser = browser_id()
    return met_cookie(jsonify(opslag.haal_mijn_pakket_volledig(browser)), browser)


@bp.post("/mijn-pakket")
def bewaar_mijn_pakket():
    gegevens = _json()
    if gegevens is None:
        return _fout("Ongeldige aanvraag.")
    browser = browser_id()
    if weigering := _te_veel(browser):
        return weigering
    return met_cookie(jsonify(opslag.sla_mijn_pakket_op(browser, gegevens)), browser)


# ---------- moderatie ----------

@bp.get("/wachtrij")
def wachtrij():
    weigering = _alleen_moderator()
    if weigering:
        return weigering
    return met_cookie(jsonify(opslag.haal_wachtrij()), browser_id())


@bp.post("/pakketten/<pakket_id>/goedkeuren")
def keur_pakket_goed(pakket_id):
    weigering = _alleen_moderator()
    if weigering:
        return weigering
    opslag.keur_pakket_goed(pakket_id)
    return jsonify(ok=True)


@bp.post("/pakketten/<pakket_id>/afwijzen")
def wijs_pakket_af(pakket_id):
    weigering = _alleen_moderator()
    if weigering:
        return weigering
    gegevens = _json() or {}
    opslag.wijs_pakket_af(pakket_id, gegevens.get("reden"))
    return jsonify(ok=True)


@bp.post("/pakketten/<pakket_id>/samenvoegen")
def voeg_pakket_samen(pakket_id):
    weigering = _alleen_moderator()
    if weigering:
        return weigering
    doel = opslag.voeg_pakket_samen(pakket_id)
    if doel is None:
        return _fout("Geen passend pakket gevonden om mee samen te voegen.", 409)
    return jsonify(pakket=doel)


@bp.post("/voorstellen/<voorstel_id>/goedkeuren")
def keur_voorstel_goed(voorstel_id):
    weigering = _alleen_moderator()
    if weigering:
        return weigering
    opslag.keur_voorstel_goed(voorstel_id)
    return jsonify(ok=True)


@bp.post("/voorstellen/<voorstel_id>/afwijzen")
def wijs_voorstel_af(voorstel_id):
    weigering = _alleen_moderator()
    if weigering:
        return weigering
    gegevens = _json() or {}
    opslag.wijs_voorstel_af(voorstel_id, gegevens.get("reden"))
    return jsonify(ok=True)


# ---------- demo ----------

@bp.post("/reset-demo")
def reset_demo():
    weigering = _alleen_moderator()
    if weigering:
        return weigering
    opslag.reset_demo()
    browser = browser_id()
    return met_cookie(jsonify(ok=True), browser)
