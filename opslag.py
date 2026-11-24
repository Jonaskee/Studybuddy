"""Opslaglaag voor StudieBuddy.

De frontend praat nooit rechtstreeks met de databank. Alle pakketten, scholen,
voorstellen en persoonlijke pakketten lopen via deze module, die twee
implementaties heeft:

* SupabaseOpslag  – zodra SUPABASE_URL + een server-sleutel in de omgeving staan.
                    Dit is de bedoelde productieopslag (werkt ook op Vercel).
* LokaleOpslag    – een JSON-bestand naast dit bestand. Handig om lokaal te
                    ontwikkelen zonder Supabase. Op Vercel is het bestand
                    vluchtig (serverless); gebruik daar Supabase.

De interne vorm van een pakket is de rij zoals ze in de databank staat
(snake_case). `pakket_voor_ui()` zet die om naar de vorm die `static/js/data.js`
en de schermen verwachten (camelCase + richtingNaam/schoolNaam).
"""

from __future__ import annotations

import json
import os
import re
import secrets
import threading
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv

MAP = Path(__file__).parent
load_dotenv(MAP / ".env")

SEMESTERS = {"1": "Semester 1", "2": "Semester 2", "1of2": "Semester 1 of 2", "jaar": "Hele academiejaar"}
FASES = ["1e bachelor", "2e bachelor", "3e bachelor", "Schakeljaar", "Master"]
ACADEMIEJAREN = ["2026-2027", "2025-2026"]

MAX_NAAM = 120
MAX_TEKST = 1000
MAX_FICHE_BYTES = 10 * 1024 * 1024
FICHE_BUCKET = "ects-fiches"


class OpslagFout(Exception):
    """De opslag zelf is onbereikbaar (bv. Supabase); de API antwoordt met 503."""


class ValidatieFout(Exception):
    """De aanvraag van de gebruiker klopt niet; de API antwoordt met 400."""


class WeigeringFout(Exception):
    """Deze actie mag niet; de API antwoordt met 403."""


# ---------------------------------------------------------------------------
# hulpmiddelen
# ---------------------------------------------------------------------------

def norm(s) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def nieuw_id() -> str:
    return secrets.token_hex(5)  # 10 tekens, enkel a-z0-9


def vandaag() -> str:
    return date.today().isoformat()


def vak(naam, semester, sp, fiche=None, groep=None, optie=None):
    return {
        "naam": naam,
        "semester": semester,
        "sp": sp,
        "fiche": {"naam": fiche} if fiche else None,
        "groep": groep,
        "optie": optie,
    }


def pakket_rij(pakket_id, richting_id, academiejaar, fase, afstudeerrichting, status,
               vakken, groepen=None, gebruikers=1, mogelijk_verouderd=False,
               ingediend_door=None, ingediend_op=None, afwijs_reden=None):
    return {
        "id": pakket_id,
        "richting_id": richting_id,
        "academiejaar": academiejaar,
        "fase": fase,
        "afstudeerrichting": afstudeerrichting or None,
        "status": status,
        "gebruikers": gebruikers,
        "mogelijk_verouderd": mogelijk_verouderd,
        "ingediend_door": ingediend_door,
        "ingediend_op": ingediend_op,
        "afwijs_reden": afwijs_reden,
        "groepen": groepen or [],
        "vakken": vakken,
    }


def seed_data():
    """Dezelfde voorbeelddata als vroeger in data.js (3e bachelor AI uit de ECTS-fiches)."""
    return {
        "scholen": [
            {"id": "ap", "naam": "AP Hogeschool Antwerpen"},
            {"id": "tm", "naam": "Thomas More"},
        ],
        "richtingen": [
            {"id": "ti", "school_id": "ap", "naam": "Toegepaste Informatica"},
            {"id": "eict", "school_id": "ap", "naam": "Elektronica-ICT"},
            {"id": "tm-ti", "school_id": "tm", "naam": "Toegepaste Informatica"},
        ],
        "pakketten": [
            pakket_rij("p3-ai", "ti", "2026-2027", "3e bachelor", "Artificiële Intelligentie", "publiek", [
                vak("AI and Society", "1", 3, "ects_fiche_ai_and_society.pdf"),
                vak("AI for Business", "1", 6, "ects_fiche_ai_for_business.pdf"),
                vak("Applied AI project", "1", 9, "ects_fiche_applied_ai_project.pdf"),
                vak("Trends in AI", "1", 3, "ects_fiche_trends_in_ai.pdf"),
                vak("Sustainable IT", "1", 3, "ects_fiche_sustainable_it.pdf"),
                vak("IT professional", "jaar", 3, "ects_fiche_it_professional.pdf"),
                vak("Bachelorproef en stage", "1of2", 27, "ects_fiche_bachelorproef_en_stage.pdf"),
                vak("Project Start-up", "1", 6, "ects_fiche_project_start_up.pdf", "opt", "Startup"),
                vak("Research project", "1", 6, None, "opt", "Research"),
            ], [{"id": "opt", "soort": "optie", "naam": "Keuzeoptie", "kies": 1}], gebruikers=23),
            pakket_rij("p3-oit", "ti", "2026-2027", "3e bachelor", "OIT", "publiek", [
                vak("IT Service Management", "1", 6),
                vak("Enterprise Architecture", "1", 6),
                vak("Security Operations", "1", 6),
                vak("Sustainable IT", "1", 3, "ects_fiche_sustainable_it.pdf"),
                vak("IT professional", "jaar", 3, "ects_fiche_it_professional.pdf"),
                vak("Bachelorproef en stage", "1of2", 27, "ects_fiche_bachelorproef_en_stage.pdf"),
                vak("Project Start-up", "1", 6, "ects_fiche_project_start_up.pdf", "opt", "Startup"),
                vak("Research project", "1", 6, None, "opt", "Research"),
            ], [{"id": "opt", "soort": "optie", "naam": "Keuzeoptie", "kies": 1}], gebruikers=11),
            pakket_rij("p2-ai", "ti", "2026-2027", "2e bachelor", "Artificiële Intelligentie", "publiek", [
                vak("Machine Learning", "1", 6, "machine-learning.pdf"),
                vak("Data Engineering", "1", 6),
                vak("Programmeren 3", "1", 6, "programmeren-3.pdf"),
                vak("Wiskunde voor AI", "1", 6),
                vak("Deep Learning", "2", 6),
                vak("Cloud Computing", "2", 6),
                vak("Project AI", "2", 9),
                vak("Computer Vision", "2", 3, None, "k2"),
                vak("Robotics", "2", 3, None, "k2"),
                vak("Game AI", "2", 3, None, "k2"),
            ], [{"id": "k2", "soort": "keuze", "naam": "Keuzevak semester 2", "kies": 1}], gebruikers=17),
            pakket_rij("p2-oit", "ti", "2026-2027", "2e bachelor", "OIT", "publiek", [
                vak("Netwerken 2", "1", 6),
                vak("Systeembeheer", "1", 6, "systeembeheer.pdf"),
                vak("Databanken 2", "1", 6),
                vak("Cloud Infrastructure", "2", 6),
                vak("IT Security", "2", 6),
                vak("Linux Advanced", "2", 3, None, "k2"),
                vak("Scripting", "2", 3, None, "k2"),
                vak("Virtualisatie", "2", 3, None, "k2"),
            ], [{"id": "k2", "soort": "keuze", "naam": "Keuzevakken semester 2", "kies": 2}], gebruikers=9),
            pakket_rij("p1", "ti", "2026-2027", "1e bachelor", None, "publiek", [
                vak("Programmeren 1", "1", 6, "programmeren-1.pdf"),
                vak("Databanken", "1", 6, "databanken.pdf"),
                vak("Webdesign", "1", 6),
                vak("Computersystemen", "1", 6),
                vak("Programmeren 2", "2", 6),
                vak("Netwerken", "2", 6, "netwerken.pdf"),
                vak("Wiskunde", "2", 6),
                vak("Communicatie", "jaar", 3),
            ], [], gebruikers=31, mogelijk_verouderd=True),
            pakket_rij("p1-oud", "ti", "2025-2026", "1e bachelor", None, "publiek", [
                vak("Programmeren 1", "1", 6),
                vak("Databanken", "1", 6),
                vak("Webdesign", "1", 6),
                vak("Programmeren 2", "2", 6),
                vak("Netwerken", "2", 6),
                vak("Wiskunde", "2", 6),
            ], [], gebruikers=40),
            pakket_rij("q1", "ti", "2026-2027", "3e bachelor", "Artificiële Intelligentie", "in_controle", [
                vak("Applied AI project", "1", 9, "applied-ai.pdf"),
                vak("Trends in AI", "1", 3, "trends-ai.pdf"),
                vak("AI for Business", "1", 6),
                vak("Data Engineering", "2", 6),
            ], [], gebruikers=0, ingediend_door="student #4821", ingediend_op="2026-11-24"),
            pakket_rij("q2", "tm-ti", "2026-2027", "2e bachelor", None, "in_controle", [],
                      [], gebruikers=0, ingediend_door="student #5102", ingediend_op="2026-11-24"),
        ],
        "voorstellen": [
            {
                "id": "v1", "pakket_id": "p1", "door": "student #3310", "op": "2026-11-23",
                "status": "in_controle",
                "tekst": "Wiskunde heet dit jaar 'Wiskunde voor informatici' en Communicatie is een keuzevak geworden.",
                "afwijs_reden": None,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Lokale opslag (JSON-bestand)
# ---------------------------------------------------------------------------

class LokaleOpslag:
    is_lokaal = True

    def __init__(self, pad: Path):
        self.pad = Path(pad)
        self.lock = threading.RLock()

    def _leeg(self):
        return {"scholen": [], "richtingen": [], "pakketten": [], "voorstellen": [], "persoonlijke": {}}

    def _lees(self):
        try:
            db = json.loads(self.pad.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return self._leeg()
        for sleutel, standaard in self._leeg().items():
            db.setdefault(sleutel, standaard)
        return db

    def _schrijf(self, db):
        self.pad.parent.mkdir(parents=True, exist_ok=True)
        tijdelijk = self.pad.with_suffix(".tmp")
        tijdelijk.write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")
        tijdelijk.replace(self.pad)

    def _wijzig(self, functie):
        with self.lock:
            db = self._lees()
            resultaat = functie(db)
            self._schrijf(db)
            return resultaat

    # primitieven
    def scholen(self):
        with self.lock:
            return list(self._lees()["scholen"])

    def richtingen(self):
        with self.lock:
            return list(self._lees()["richtingen"])

    def pakketten(self, richting_id=None):
        with self.lock:
            rijen = list(self._lees()["pakketten"])
        return [r for r in rijen if richting_id is None or r["richting_id"] == richting_id]

    def pakket(self, pakket_id):
        with self.lock:
            return next((r for r in self._lees()["pakketten"] if r["id"] == pakket_id), None)

    def bewaar_pakket(self, rij):
        def doe(db):
            db["pakketten"] = [r for r in db["pakketten"] if r["id"] != rij["id"]] + [rij]
            return rij
        return self._wijzig(doe)

    def wijzig_pakket(self, pakket_id, velden):
        def doe(db):
            for rij in db["pakketten"]:
                if rij["id"] == pakket_id:
                    rij.update(velden)
                    return rij
            return None
        return self._wijzig(doe)

    def bewaar_school(self, rij):
        def doe(db):
            if not any(s["id"] == rij["id"] for s in db["scholen"]):
                db["scholen"].append(rij)
            return rij
        return self._wijzig(doe)

    def bewaar_richting(self, rij):
        def doe(db):
            if not any(r["id"] == rij["id"] for r in db["richtingen"]):
                db["richtingen"].append(rij)
            return rij
        return self._wijzig(doe)

    def voorstellen(self, status=None):
        with self.lock:
            rijen = list(self._lees()["voorstellen"])
        return [r for r in rijen if status is None or r.get("status") == status]

    def bewaar_voorstel(self, rij):
        def doe(db):
            db["voorstellen"] = [r for r in db["voorstellen"] if r["id"] != rij["id"]] + [rij]
            return rij
        return self._wijzig(doe)

    def wijzig_voorstel(self, voorstel_id, velden):
        def doe(db):
            for rij in db["voorstellen"]:
                if rij["id"] == voorstel_id:
                    rij.update(velden)
                    return rij
            return None
        return self._wijzig(doe)

    def persoonlijk(self, student_id):
        with self.lock:
            rij = self._lees()["persoonlijke"].get(student_id)
        return dict(rij) if rij else None

    def bewaar_persoonlijk(self, rij):
        def doe(db):
            db["persoonlijke"][rij["student_id"]] = rij
            return rij
        return self._wijzig(doe)

    def seed_nodig(self):
        with self.lock:
            return not self._lees()["scholen"]

    def seed_plaatsen(self, seed):
        def doe(db):
            db["scholen"] = seed["scholen"]
            db["richtingen"] = seed["richtingen"]
            db["pakketten"] = seed["pakketten"]
            db["voorstellen"] = seed["voorstellen"]
            db["persoonlijke"] = {}
        self._wijzig(doe)

    def wis_alles(self):
        self._wijzig(lambda db: (db.clear(), db.update(self._leeg())))

    def bewaar_fiche(self, naam, inhoud):
        map_ = Path(os.getenv("UPLOAD_MAP") or ("/tmp/studiebuddy-uploads" if os.getenv("VERCEL") else MAP / "uploads"))
        map_.mkdir(parents=True, exist_ok=True)
        veilig = veilige_bestandsnaam(naam)
        pad = map_ / f"{nieuw_id()}-{veilig}"
        pad.write_bytes(inhoud)
        return {"naam": Path(naam).name, "pad": str(pad.name)}


# ---------------------------------------------------------------------------
# Supabase-opslag (REST + Storage)
# ---------------------------------------------------------------------------

class SupabaseOpslag:
    is_lokaal = False

    def __init__(self, url: str, sleutel: str):
        basis = url.rstrip("/")
        self.client = httpx.Client(
            base_url=basis + "/rest/v1",
            headers={
                "apikey": sleutel,
                "Authorization": f"Bearer {sleutel}",
                "Content-Type": "application/json",
            },
            timeout=20,
        )
        self.storage = httpx.Client(
            base_url=basis + "/storage/v1",
            headers={"apikey": sleutel, "Authorization": f"Bearer {sleutel}"},
            timeout=60,
        )

    def _controleer(self, antwoord):
        if antwoord.status_code >= 400:
            detail = antwoord.text[:300]
            raise OpslagFout(f"Supabase-fout {antwoord.status_code}: {detail}")
        return antwoord

    def _get(self, tabel, params=None):
        antwoord = self.client.get(f"/{tabel}", params={"select": "*", **(params or {})})
        return self._controleer(antwoord).json()

    def _post(self, tabel, rijen, on_conflict=None):
        if not rijen:
            return []
        params = {"select": "*"}
        if on_conflict:
            params["on_conflict"] = on_conflict
        antwoord = self.client.post(
            f"/{tabel}", params=params, json=rijen,
            headers={"Prefer": "resolution=merge-duplicates,return=representation"},
        )
        return self._controleer(antwoord).json()

    def _patch(self, tabel, filters, velden):
        antwoord = self.client.patch(
            f"/{tabel}", params={**filters, "select": "*"}, json=velden,
            headers={"Prefer": "return=representation"},
        )
        rijen = self._controleer(antwoord).json()
        return rijen[0] if rijen else None

    def _delete(self, tabel, filters):
        self._controleer(self.client.delete(f"/{tabel}", params=filters))

    # primitieven
    def scholen(self):
        return self._get("scholen")

    def richtingen(self):
        return self._get("richtingen")

    def pakketten(self, richting_id=None):
        return self._get("pakketten", {"richting_id": f"eq.{richting_id}"} if richting_id else None)

    def pakket(self, pakket_id):
        rijen = self._get("pakketten", {"id": f"eq.{pakket_id}", "limit": 1})
        return rijen[0] if rijen else None

    def bewaar_pakket(self, rij):
        rijen = self._post("pakketten", [rij], on_conflict="id")
        return rijen[0] if rijen else rij

    def wijzig_pakket(self, pakket_id, velden):
        return self._patch("pakketten", {"id": f"eq.{pakket_id}"}, velden)

    def bewaar_school(self, rij):
        self._post("scholen", [rij], on_conflict="id")
        return rij

    def bewaar_richting(self, rij):
        self._post("richtingen", [rij], on_conflict="id")
        return rij

    def voorstellen(self, status=None):
        return self._get("wijzigingsvoorstellen", {"status": f"eq.{status}"} if status else None)

    def bewaar_voorstel(self, rij):
        rijen = self._post("wijzigingsvoorstellen", [rij], on_conflict="id")
        return rijen[0] if rijen else rij

    def wijzig_voorstel(self, voorstel_id, velden):
        return self._patch("wijzigingsvoorstellen", {"id": f"eq.{voorstel_id}"}, velden)

    def persoonlijk(self, student_id):
        rijen = self._get("persoonlijke_pakketten", {"student_id": f"eq.{student_id}", "limit": 1})
        return rijen[0] if rijen else None

    def bewaar_persoonlijk(self, rij):
        rijen = self._post("persoonlijke_pakketten", [rij], on_conflict="student_id")
        return rijen[0] if rijen else rij

    def seed_nodig(self):
        return not self._get("scholen", {"limit": 1})

    def seed_plaatsen(self, seed):
        self._post("scholen", seed["scholen"], on_conflict="id")
        self._post("richtingen", seed["richtingen"], on_conflict="id")
        self._post("pakketten", seed["pakketten"], on_conflict="id")
        self._post("wijzigingsvoorstellen", seed["voorstellen"], on_conflict="id")

    def wis_alles(self):
        self._delete("wijzigingsvoorstellen", {"id": "neq.0"})
        self._delete("persoonlijke_pakketten", {"student_id": "neq.0"})
        for tabel in ("pakketten", "richtingen", "scholen"):
            self._delete(tabel, {"id": "neq.0"})

    def bewaar_fiche(self, naam, inhoud):
        veilig = veilige_bestandsnaam(naam)
        pad = f"{nieuw_id()}-{veilig}"
        antwoord = self.storage.post(
            f"/object/{FICHE_BUCKET}/{pad}",
            content=inhoud,
            headers={"Content-Type": "application/pdf", "x-upsert": "true"},
        )
        if antwoord.status_code >= 400:
            # Bucket ontbreekt of is niet schrijfbaar: pakket opslaan lukt nog, enkel de PDF niet.
            return {"naam": Path(naam).name, "pad": None,
                    "waarschuwing": f"PDF niet geüpload ({antwoord.status_code}); maak de bucket '{FICHE_BUCKET}' aan."}
        return {"naam": Path(naam).name, "pad": pad}


def veilige_bestandsnaam(naam: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", Path(naam or "fiche.pdf").name)[-120:] or "fiche.pdf"


# ---------------------------------------------------------------------------
# opslag kiezen
# ---------------------------------------------------------------------------

_opslag = None
_seed_gecontroleerd = False
_opslag_slot = threading.Lock()


def maak_opslag():
    url = (os.getenv("SUPABASE_URL") or "").strip()
    sleutel = (os.getenv("SUPABASE_SERVER_SLEUTEL") or os.getenv("SUPABASE_KEY") or "").strip()
    if url.startswith("http") and sleutel:
        return SupabaseOpslag(url, sleutel)
    pad = os.getenv("DATA_BESTAND") or ("/tmp/studiebuddy-data.json" if os.getenv("VERCEL") else str(MAP / "data_store.json"))
    return LokaleOpslag(Path(pad))


def huidige_opslag():
    global _opslag, _seed_gecontroleerd
    with _opslag_slot:
        if _opslag is None:
            _opslag = maak_opslag()
        if not _seed_gecontroleerd:
            if os.getenv("SEED_DEMO", "1") != "0" and _opslag.seed_nodig():
                _opslag.seed_plaatsen(seed_data())
            _seed_gecontroleerd = True
        return _opslag


# ---------------------------------------------------------------------------
# namen en checks
# ---------------------------------------------------------------------------

MAX_FICHE_TEKST = 40_000  # tekens; genoeg voor een ECTS-fiche, houdt pakketten klein


def pdf_naar_tekst(inhoud: bytes) -> str:
    """Tekst uit een PDF halen (pypdf). Lege string als het niet lukt (bv. een scan)."""
    try:
        from io import BytesIO
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        lezer = PdfReader(BytesIO(inhoud))
        if lezer.is_encrypted:
            lezer.decrypt("")
        stukken = []
        for pagina in lezer.pages[:30]:
            stukken.append(pagina.extract_text() or "")
            if sum(map(len, stukken)) > MAX_FICHE_TEKST:
                break
    except Exception:
        return ""
    tekst = "\n".join(stukken)
    tekst = re.sub(r"[ \t]+", " ", tekst)
    tekst = re.sub(r"\n\s*\n+", "\n\n", tekst).strip()
    return tekst[:MAX_FICHE_TEKST]


def bewaar_fiche(naam, inhoud):
    """PDF in Supabase Storage (of lokaal) bewaren + de tekst eruit halen voor de chat."""
    if len(inhoud) > MAX_FICHE_BYTES:
        raise ValidatieFout("Het bestand is te groot (max. 10 MB).")
    if not inhoud.lstrip()[:5].startswith(b"%PDF"):
        raise ValidatieFout(f"'{Path(naam).name}' is geen geldige PDF.")
    resultaat = huidige_opslag().bewaar_fiche(naam, inhoud)
    tekst = pdf_naar_tekst(inhoud)
    resultaat["tekst"] = tekst
    if not tekst:
        extra = "Uit deze PDF kon geen tekst gehaald worden (scan?); de chat kan hem niet lezen."
        resultaat["waarschuwing"] = (resultaat.get("waarschuwing", "") + " " + extra).strip()
    return resultaat


def fiche_teksten(student_id):
    """Vaknaam -> fichetekst voor de vakken die deze student volgt (uit geüploade PDF's).
    Faalt nooit: zonder pakket of bij een opslagfout gewoon een lege dict."""
    try:
        volledig = haal_mijn_pakket_volledig(student_id)
        if not volledig:
            return {}
        basis = huidige_opslag().pakket(volledig["mijn"]["basisPakketId"]) or {}
        ruw = {v.get("naam"): v for v in basis.get("vakken") or []}
        uit = {}
        for v in volledig["vakken"]:
            fiche = (ruw.get(v.get("naam")) or v).get("fiche") or {}
            if fiche.get("tekst"):
                uit[v["naam"]] = fiche["tekst"]
        return uit
    except Exception:
        return {}


def _naam_lookup():
    winkel = huidige_opslag()
    scholen = {s["id"]: s["naam"] for s in winkel.scholen()}
    richtingen = {r["id"]: r for r in winkel.richtingen()}
    return scholen, richtingen


def _vak_voor_ui(v):
    fiche = v.get("fiche")
    if not fiche or "tekst" not in fiche:
        return v
    fiche = {k: w for k, w in fiche.items() if k != "tekst"}
    fiche["leesbaar"] = True
    return {**v, "fiche": fiche}


def pakket_voor_ui(rij, scholen, richtingen):
    richting = richtingen.get(rij["richting_id"]) or {}
    return {
        "id": rij["id"],
        "richtingId": rij["richting_id"],
        "academiejaar": rij["academiejaar"],
        "fase": rij["fase"],
        "afstudeerrichting": rij.get("afstudeerrichting"),
        "status": rij["status"],
        "gebruikers": rij.get("gebruikers") or 0,
        "mogelijkVerouderd": bool(rij.get("mogelijk_verouderd")),
        "ingediendDoor": rij.get("ingediend_door"),
        "ingediendOp": rij.get("ingediend_op"),
        "afwijsReden": rij.get("afwijs_reden"),
        "groepen": rij.get("groepen") or [],
        "vakken": [_vak_voor_ui(v) for v in rij.get("vakken") or []],
        "richtingNaam": richting.get("naam") or "?",
        "schoolNaam": scholen.get(richting.get("school_id")) or "?",
    }


def _zelfde_scope(a, b):
    return (a["richting_id"] == b["richting_id"]
            and a["academiejaar"] == b["academiejaar"]
            and a["fase"] == b["fase"]
            and norm(a.get("afstudeerrichting")) == norm(b.get("afstudeerrichting")))


def _overlap(rij, anderen):
    """Beste publieke pakket met dezelfde scope + het aantal overlappende vaknamen."""
    namen = {norm(v.get("naam")) for v in rij.get("vakken") or []}
    beste = None
    for ander in anderen:
        if ander["id"] == rij["id"] or ander["status"] != "publiek":
            continue
        if not _zelfde_scope(rij, ander):
            continue
        overlap = len(namen & {norm(v.get("naam")) for v in ander.get("vakken") or []})
        if beste is None or overlap > beste[1]:
            beste = (ander, overlap)
    return beste


def checks_voor(rij):
    winkel = huidige_opslag()
    scholen, richtingen = _naam_lookup()
    anderen = winkel.pakketten(rij["richting_id"])
    beste = _overlap(rij, anderen)
    vakken = rij.get("vakken") or []
    return {
        "leeg": len(vakken) == 0,
        "fiches": {"met": sum(1 for v in vakken if v.get("fiche")), "totaal": len(vakken)},
        "zonderSemester": sum(1 for v in vakken if v.get("semester") not in SEMESTERS),
        "overlap": None if not beste or beste[1] == 0 else {
            "aantal": beste[1],
            "totaal": len(vakken),
            "met": pakket_voor_ui(beste[0], scholen, richtingen),
        },
    }


# ---------------------------------------------------------------------------
# zoeken
# ---------------------------------------------------------------------------

def zoek_scholen(q):
    q = norm(q)
    winkel = huidige_opslag()
    return [{"id": s["id"], "naam": s["naam"]}
            for s in winkel.scholen() if q in norm(s["naam"])][:6]


def _vind_school(naam):
    return next((s for s in huidige_opslag().scholen() if norm(s["naam"]) == norm(naam)), None)


def _vind_richting(school_id, naam):
    return next((r for r in huidige_opslag().richtingen()
                 if r["school_id"] == school_id and norm(r["naam"]) == norm(naam)), None)


def _aantal_publiek_per_richting():
    winkel = huidige_opslag()
    telling = {}
    for rij in winkel.pakketten():
        if rij["status"] == "publiek":
            telling[rij["richting_id"]] = telling.get(rij["richting_id"], 0) + 1
    return telling


def zoek_richtingen(school_naam, q):
    school = _vind_school(school_naam)
    if not school:
        return []
    telling = _aantal_publiek_per_richting()
    q = norm(q)
    return [{"id": r["id"], "naam": r["naam"], "aantalPakketten": telling.get(r["id"], 0)}
            for r in huidige_opslag().richtingen()
            if r["school_id"] == school["id"] and q in norm(r["naam"])][:6]


def vind_richting(school_naam, richting_naam):
    school = _vind_school(school_naam)
    richting = school and _vind_richting(school["id"], richting_naam)
    if not richting:
        return None
    telling = _aantal_publiek_per_richting()
    return {"schoolId": school["id"], "richtingId": richting["id"],
            "aantalPakketten": telling.get(richting["id"], 0)}


def haal_afstudeerrichtingen(richting_id):
    return sorted({r["afstudeerrichting"] for r in huidige_opslag().pakketten(richting_id)
                   if r.get("afstudeerrichting")})


def haal_pakketten(richting_id):
    winkel = huidige_opslag()
    scholen, richtingen = _naam_lookup()
    rijen = [r for r in winkel.pakketten(richting_id) if r["status"] == "publiek"]
    rijen.sort(key=lambda r: (r.get("afstudeerrichting") or ""))
    rijen.sort(key=lambda r: r["fase"])
    rijen.sort(key=lambda r: r["academiejaar"], reverse=True)
    return [pakket_voor_ui(r, scholen, richtingen) for r in rijen]


def haal_pakket(pakket_id):
    rij = huidige_opslag().pakket(pakket_id)
    if not rij:
        return None
    scholen, richtingen = _naam_lookup()
    return pakket_voor_ui(rij, scholen, richtingen)


# ---------------------------------------------------------------------------
# pakketten maken en persoonlijke pakketten
# ---------------------------------------------------------------------------

def _valideer_vakken(vakken, groepen):
    if not isinstance(vakken, list):
        raise ValidatieFout("Ongeldige vakkenlijst.")
    groep_ids = {g.get("id") for g in groepen}
    schoon = []
    for v in vakken:
        if not isinstance(v, dict):
            raise ValidatieFout("Ongeldig vak.")
        naam = str(v.get("naam") or "").strip()
        if not naam:
            raise ValidatieFout("Elk vak moet een naam hebben.")
        if len(naam) > MAX_NAAM:
            raise ValidatieFout(f"Vaknaam te lang (max. {MAX_NAAM} tekens).")
        semester = str(v.get("semester") or "")
        if semester not in SEMESTERS:
            raise ValidatieFout(f"Ongeldig semester voor '{naam}'.")
        try:
            sp = int(v.get("sp"))
        except (TypeError, ValueError):
            raise ValidatieFout(f"Ongeldig aantal studiepunten voor '{naam}'.")
        if not 1 <= sp <= 60:
            raise ValidatieFout(f"Studiepunten voor '{naam}' moeten tussen 1 en 60 liggen.")
        groep = v.get("groep") or None
        if groep and groep not in groep_ids:
            raise ValidatieFout(f"Onbekende keuzegroep voor '{naam}'.")
        optie = (str(v.get("optie")).strip() if v.get("optie") else None) or None
        fiche = v.get("fiche")
        if fiche is not None:
            if not isinstance(fiche, dict) or not str(fiche.get("naam") or "").strip():
                raise ValidatieFout(f"Ongeldige ECTS-fiche voor '{naam}'.")
            tekst = fiche.get("tekst")
            fiche = {"naam": str(fiche["naam"])[:MAX_NAAM], "pad": fiche.get("pad") or None}
            if isinstance(tekst, str) and tekst.strip():
                fiche["tekst"] = tekst.strip()[:MAX_FICHE_TEKST]
        schoon.append({"naam": naam, "semester": semester, "sp": sp, "fiche": fiche,
                       "groep": groep, "optie": optie})
    return schoon


def _valideer_groepen(groepen):
    if groepen is None:
        return []
    if not isinstance(groepen, list):
        raise ValidatieFout("Ongeldige keuzegroepen.")
    schoon = []
    for g in groepen:
        if not isinstance(g, dict):
            raise ValidatieFout("Ongeldige keuzegroep.")
        gid = str(g.get("id") or "").strip()
        soort = g.get("soort")
        if not gid or soort not in ("keuze", "optie"):
            raise ValidatieFout("Ongeldige keuzegroep.")
        naam = str(g.get("naam") or "").strip()[:MAX_NAAM] or ("Keuzeoptie" if soort == "optie" else "Keuzevak")
        try:
            kies = int(g.get("kies"))
        except (TypeError, ValueError):
            raise ValidatieFout("Ongeldig aantal te kiezen vakken in een keuzegroep.")
        if not 1 <= kies <= 20:
            raise ValidatieFout("Ongeldig aantal te kiezen vakken in een keuzegroep.")
        schoon.append({"id": gid, "soort": soort, "naam": naam, "kies": kies})
    return schoon


def maak_pakket(student_id, gegevens):
    winkel = huidige_opslag()
    school_naam = str(gegevens.get("schoolNaam") or "").strip()
    richting_naam = str(gegevens.get("richtingNaam") or "").strip()
    if not school_naam or not richting_naam:
        raise ValidatieFout("School en richting zijn verplicht.")
    academiejaar = str(gegevens.get("academiejaar") or "").strip()
    fase = str(gegevens.get("fase") or "").strip()
    if not academiejaar or not fase:
        raise ValidatieFout("Academiejaar en jaar zijn verplicht.")
    groepen = _valideer_groepen(gegevens.get("groepen"))
    vakken = _valideer_vakken(gegevens.get("vakken"), groepen)
    zichtbaarheid = gegevens.get("zichtbaarheid")
    if zichtbaarheid not in ("prive", "publiek"):
        raise ValidatieFout("Kies of het pakket privé of publiek is.")

    school = _vind_school(school_naam)
    if not school:
        school = {"id": nieuw_id(), "naam": school_naam[:MAX_NAAM]}
        winkel.bewaar_school(school)
    richting = _vind_richting(school["id"], richting_naam)
    if not richting:
        richting = {"id": nieuw_id(), "school_id": school["id"], "naam": richting_naam[:MAX_NAAM]}
        winkel.bewaar_richting(richting)

    rij = pakket_rij(
        nieuw_id(), richting["id"], academiejaar[:40], fase[:40],
        str(gegevens.get("afstudeerrichting") or "").strip()[:MAX_NAAM] or None,
        "in_controle" if zichtbaarheid == "publiek" else "prive",
        vakken, groepen, gebruikers=1,
        ingediend_door="student #" + student_id[-4:], ingediend_op=vandaag(),
    )
    winkel.bewaar_pakket(rij)
    winkel.bewaar_persoonlijk({
        "student_id": student_id, "basis_pakket_id": rij["id"],
        "uitgezet": [], "overgeslagen": [], "keuzes": {}, "eigen_vakken": [],
    })

    scholen, richtingen = _naam_lookup()
    return pakket_voor_ui(rij, scholen, richtingen)


def sla_mijn_pakket_op(student_id, gegevens):
    winkel = huidige_opslag()
    basis = str(gegevens.get("basisPakketId") or "")
    if not winkel.pakket(basis):
        raise ValidatieFout("Dat pakket bestaat niet (meer).")
    keuzes = gegevens.get("keuzes") or {}
    if not isinstance(keuzes, dict):
        raise ValidatieFout("Ongeldige keuzes.")
    eigen = gegevens.get("eigenVakken") or []
    if not isinstance(eigen, list):
        raise ValidatieFout("Ongeldige eigen vakken.")
    schoon_eigen = []
    for v in eigen:
        if not isinstance(v, dict) or not str(v.get("naam") or "").strip():
            raise ValidatieFout("Ongeldig eigen vak.")
        schoon_eigen.append({
            "naam": str(v["naam"]).strip()[:MAX_NAAM],
            "semester": str(v.get("semester") or "1"),
            "sp": int(v.get("sp") or 0),
        })
    rij = {
        "student_id": student_id,
        "basis_pakket_id": basis,
        "uitgezet": [str(x) for x in (gegevens.get("uitgezet") or []) if x],
        "overgeslagen": [str(x) for x in (gegevens.get("overgeslagen") or []) if x],
        "keuzes": keuzes,
        "eigen_vakken": schoon_eigen,
    }
    winkel.bewaar_persoonlijk(rij)
    return _persoonlijk_voor_ui(rij)


def _persoonlijk_voor_ui(rij):
    return {
        "basisPakketId": rij["basis_pakket_id"],
        "uitgezet": rij.get("uitgezet") or [],
        "keuzes": rij.get("keuzes") or {},
        "overgeslagen": rij.get("overgeslagen") or [],
        "eigenVakken": rij.get("eigen_vakken") or [],
    }


def haal_mijn_pakket(student_id):
    rij = huidige_opslag().persoonlijk(student_id)
    return _persoonlijk_voor_ui(rij) if rij else None


def gevolgde_vakken(pakket, mijn):
    uitgezet = set(mijn.get("uitgezet") or [])
    overgeslagen = set(mijn.get("overgeslagen") or [])
    keuzes = mijn.get("keuzes") or {}
    groepen = {g["id"]: g for g in pakket.get("groepen") or []}
    lijst = []
    for v in pakket.get("vakken") or []:
        groep_id = v.get("groep")
        if not groep_id:
            if v.get("naam") not in uitgezet:
                lijst.append(v)
            continue
        if groep_id in overgeslagen:
            continue
        groep = groepen.get(groep_id)
        gekozen = keuzes.get(groep_id) or []
        if groep and groep.get("soort") == "optie":
            if v.get("optie") in gekozen:
                lijst.append(v)
        elif v.get("naam") in gekozen:
            lijst.append(v)
    return lijst + [{**v, "eigen": True} for v in mijn.get("eigenVakken") or []]


def haal_mijn_pakket_volledig(student_id):
    winkel = huidige_opslag()
    rij = winkel.persoonlijk(student_id)
    if not rij:
        return None
    basis = winkel.pakket(rij["basis_pakket_id"])
    if not basis:
        return None
    scholen, richtingen = _naam_lookup()
    pakket = pakket_voor_ui(basis, scholen, richtingen)
    mijn = _persoonlijk_voor_ui(rij)
    return {"mijn": mijn, "pakket": pakket, "vakken": gevolgde_vakken(pakket, mijn)}


# ---------------------------------------------------------------------------
# voorstellen en moderatie
# ---------------------------------------------------------------------------

def stel_wijziging_voor(student_id, pakket_id, tekst):
    tekst = str(tekst or "").strip()
    if len(tekst) < 5:
        raise ValidatieFout("Beschrijf kort wat er moet veranderen.")
    if len(tekst) > MAX_TEKST:
        raise ValidatieFout(f"Voorstel te lang (max. {MAX_TEKST} tekens).")
    winkel = huidige_opslag()
    if not winkel.pakket(pakket_id):
        raise ValidatieFout("Dat pakket bestaat niet (meer).")
    rij = {
        "id": nieuw_id(), "pakket_id": pakket_id, "tekst": tekst,
        "door": "student #" + student_id[-4:], "op": vandaag(),
        "status": "in_controle", "afwijs_reden": None,
    }
    winkel.bewaar_voorstel(rij)
    return {"id": rij["id"], "pakketId": pakket_id, "tekst": tekst,
            "door": rij["door"], "op": rij["op"], "status": rij["status"]}


def haal_wachtrij():
    winkel = huidige_opslag()
    scholen, richtingen = _naam_lookup()
    pakketten = []
    for rij in winkel.pakketten():
        if rij["status"] == "in_controle":
            pakketten.append({**pakket_voor_ui(rij, scholen, richtingen), "checks": checks_voor(rij)})
    voorstellen = []
    for rij in winkel.voorstellen("in_controle"):
        basis = winkel.pakket(rij["pakket_id"])
        voorstellen.append({
            "id": rij["id"], "pakketId": rij["pakket_id"], "tekst": rij["tekst"],
            "door": rij["door"], "op": rij["op"], "status": rij["status"],
            "pakket": pakket_voor_ui(basis, scholen, richtingen) if basis else None,
        })
    return {"pakketten": pakketten, "voorstellen": voorstellen}


def keur_pakket_goed(pakket_id):
    huidige_opslag().wijzig_pakket(pakket_id, {"status": "publiek", "afwijs_reden": None})


def wijs_pakket_af(pakket_id, reden):
    huidige_opslag().wijzig_pakket(pakket_id, {"status": "afgewezen", "afwijs_reden": reden or None})


def voeg_pakket_samen(pakket_id):
    """Voeg de nieuwe vakken toe aan het publieke pakket waarop dit het meest lijkt.

    Keuzegroepen worden overgezet (of aangemaakt) zodat een keuzevak geen
    verplicht vak wordt. De bron krijgt status 'samengevoegd'.
    """
    winkel = huidige_opslag()
    bron = winkel.pakket(pakket_id)
    if not bron:
        return None
    anderen = winkel.pakketten(bron["richting_id"])
    beste = _overlap(bron, anderen)
    if not beste:
        return None
    doel, _ = beste

    bestaand = {norm(v.get("naam")) for v in doel.get("vakken") or []}
    doel_groepen = list(doel.get("groepen") or [])
    groep_map = {}

    def semesters(rij, groep_id):
        return ",".join(sorted({v.get("semester", "") for v in rij.get("vakken") or [] if v.get("groep") == groep_id}))

    for groep in bron.get("groepen") or []:
        gevonden = None
        for kandidaat in doel_groepen:
            if kandidaat.get("soort") != groep.get("soort"):
                continue
            if groep.get("soort") == "optie":
                gevonden = kandidaat
                break
            if norm(kandidaat.get("naam")) == norm(groep.get("naam")) \
                    or semesters(doel, kandidaat.get("id")) == semesters(bron, groep.get("id")):
                gevonden = kandidaat
                break
        if not gevonden:
            nieuwe_id = groep["id"]
            while any(g.get("id") == nieuwe_id for g in doel_groepen):
                nieuwe_id = groep["id"] + "-" + nieuw_id()[:4]
            gevonden = {**groep, "id": nieuwe_id}
            doel_groepen.append(gevonden)
        groep_map[groep["id"]] = gevonden["id"]

    nieuwe_vakken = list(doel.get("vakken") or [])
    for v in bron.get("vakken") or []:
        if norm(v.get("naam")) in bestaand:
            continue
        if v.get("groep") and v.get("groep") not in groep_map:
            continue  # onbekende groep: niet als verplicht vak toevoegen
        nieuwe_vakken.append({**v, "groep": groep_map.get(v.get("groep")) if v.get("groep") else None})

    winkel.wijzig_pakket(doel["id"], {"vakken": nieuwe_vakken, "groepen": doel_groepen})
    winkel.wijzig_pakket(bron["id"], {"status": "samengevoegd"})

    scholen, richtingen = _naam_lookup()
    bijgewerkt = winkel.pakket(doel["id"])
    return pakket_voor_ui(bijgewerkt, scholen, richtingen)


def keur_voorstel_goed(voorstel_id):
    huidige_opslag().wijzig_voorstel(voorstel_id, {"status": "goedgekeurd"})


def wijs_voorstel_af(voorstel_id, reden):
    huidige_opslag().wijzig_voorstel(voorstel_id, {"status": "afgewezen", "afwijs_reden": reden or None})


def reset_demo():
    winkel = huidige_opslag()
    if not winkel.is_lokaal and os.getenv("ALLOW_RESET") != "1":
        raise WeigeringFout("Reset staat uit voor de gedeelde databank (zet ALLOW_RESET=1 om dit toe te laten).")
    winkel.wis_alles()
    winkel.seed_plaatsen(seed_data())
