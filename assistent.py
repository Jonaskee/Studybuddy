"""
StudieBuddy - een simpele AI-assistent met eigen context (PoC).

Context die we zelf toevoegen:
  1. Rol                     -> hoe de assistent zich gedraagt
  2. Kennis                  -> ECTS-fiches uit Supabase (tabel vakken, zie supabase/schema.sql),
                                met context/<vak>/*.md als reserve als Supabase niet bereikbaar is
  3. Tijd / locatie          -> huidige dag, uur, semester en locatie
  4. Sessiegegevens          -> sessie-id, starttijd en aantal vragen van deze sessie

De system prompt zelf staat in systeem_prompt.md; bouw_context() vult de {velden} in.

Starten: python assistent.py
"""

import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

BASE_URL = "https://api.route33.ai/v1"
MODEL = "z-ai/glm-5.3-flash"  # goedkoopste model op route33
PRIJS_IN, PRIJS_UIT = 0.05, 0.20  # euro per 1M tokens (route33 pricing)


MAX_ANTWOORD_TOKENS = 600  # begrenst de kost per antwoord, ook als iemand om een "heel lang antwoord" vraagt

MAP = Path(__file__).parent
load_dotenv(MAP / ".env")


def _euro_uit_env(naam, standaard):
    """Bedrag in euro uit .env; 0 betekent geen limiet."""
    ruw = (os.getenv(naam) or "").strip()
    if not ruw:
        return standaard
    try:
        waarde = float(ruw)
    except ValueError:
        raise SystemExit(f"{naam} in .env moet een getal zijn, bv. {naam}={standaard:.2f}")
    if not 0 <= waarde < float("inf"):  # vangt ook nan en inf, die de limiet anders stil uitschakelen
        raise SystemExit(f"{naam} in .env moet een getal van 0 of meer zijn, bv. {naam}={standaard:.2f}")
    return waarde


BUDGET = _euro_uit_env("TOTAAL_BUDGET", 1.00)    # euro in totaal; daarboven stuurt StudieBuddy geen oproepen meer (0 = geen limiet)
DAG_BUDGET = _euro_uit_env("DAG_BUDGET", 0.10)  # euro per dag, zodat één spammer niet in één dag alles opmaakt (0 = geen limiet)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = (os.getenv("SUPABASE_KEY") or "").strip()  # publishable/anon key: RLS laat enkel publieke, goedgekeurde vakken zien
LOCATIE = "Campus, België"

# Meerdere requests kunnen tegelijk verbruik.json lezen/schrijven.
verbruik_slot = threading.RLock()

CONTEXT_MAP = MAP / "context"
# Op Vercel is de projectmap read-only, enkel /tmp is schrijfbaar.
# shortcut: /tmp wordt gewist bij elke koude start, dus het budget telt op Vercel niet betrouwbaar; zet ook een limiet in het route33-dashboard
VERBRUIK_BESTAND = Path("/tmp/verbruik.json") if os.getenv("VERCEL") else MAP / "verbruik.json"
PROMPT_BESTAND = MAP / "systeem_prompt.md"  # sjabloon van de system prompt

INFO_VELDEN = ("Titularis", "Co-titularis(sen)", "Studieomvang", "Kalender", "Semester")
MAX_FICHES = 2  # alle fiches samen is veel tokens, dus veel kosten

DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]

# Sessiegegevens: bestaan enkel zolang het programma draait
sessie = {
    "id": uuid.uuid4().hex[:8],
    "start": datetime.now(),
    "vragen": [],
}


def laad_vakken():
    """Vaknaam -> ECTS-fiche. Uit Supabase; lukt dat niet, dan uit de map context/."""
    if SUPABASE_URL and SUPABASE_KEY:
        # shortcut: haalt alle publieke, goedgekeurde vakken op (RLS); later filteren op het pakket van de student
        try:
            r = httpx.get(f"{SUPABASE_URL}/rest/v1/vakken", headers={"apikey": SUPABASE_KEY},
                          params={"select": "naam,fiche_md", "order": "naam"}, timeout=10)
            r.raise_for_status()
            vakken = {v["naam"]: v["fiche_md"] or "" for v in r.json()}
            if vakken:
                return vakken
        except httpx.HTTPError:
            pass  # val terug op de lokale fiches
    return laad_vakken_lokaal()


def laad_vakken_lokaal():
    """Elke submap van context/ is een vak, met de ECTS-fiche(s) als .md erin."""
    vakken = {}
    for vak_map in sorted(CONTEXT_MAP.iterdir()):
        if vak_map.is_dir():
            fiches = [p.read_text(encoding="utf-8") for p in sorted(vak_map.glob("*.md"))]
            vakken[vak_map.name.replace("_", " ")] = "\n\n".join(fiches)
    return vakken


def overzicht(vakken):
    """Korte samenvatting per vak (titularis, studiepunten, semester) uit de fiches."""
    blokken = []
    for naam, fiche in vakken.items():
        info = [regel.replace("*", "").strip() for regel in fiche.splitlines()
                if any(regel.startswith(f"* **{veld}:**") for veld in INFO_VELDEN)]
        blokken.append(f"### {naam}\n" + "\n".join(f"- {i}" for i in info))
    return "\n\n".join(blokken)


def relevante_vakken(vakken, vragen):
    """Vakken die in de laatste 2 vragen genoemd worden (nieuwste vraag eerst)."""
    gevonden = []
    for vraag in reversed(list(vragen)[-2:]):
        for naam in vakken:
            woorden = [w for w in naam.lower().split() if len(w) > 3]
            if naam not in gevonden and any(w in vraag.lower() for w in woorden):
                gevonden.append(naam)
    return gevonden[:MAX_FICHES]


def bouw_context(context_aan, vragen=None, eigen_fiches=None):
    """Stelt de system prompt samen. Zonder context krijgt het model niets extra.

    `vragen` is de vraaggeschiedenis van deze bezoeker (web) of None (terminal,
    dan gebruiken we de globale sessie). `eigen_fiches` (vaknaam -> tekst) komt
    uit de PDF's die de student zelf uploadde en wint van de standaardfiches.
    """
    if not context_aan:
        return "Je bent een behulpzame assistent."

    vragen = list(sessie["vragen"] if vragen is None else vragen)
    nu = datetime.now()
    semester = 1 if nu.month >= 9 or nu.month == 1 else 2
    vakken = laad_vakken()
    if eigen_fiches:
        vakken = {**vakken, **{naam: f"## ECTS-fiche {naam} (geüploade PDF)\n\n{tekst}"
                               for naam, tekst in eigen_fiches.items()}}
    fiches = "\n\n".join(vakken[naam] for naam in relevante_vakken(vakken, vragen)) or "(geen specifiek vak gevraagd)"

    # De tekst staat in systeem_prompt.md; hier vullen we enkel de {velden} in.
    return PROMPT_BESTAND.read_text(encoding="utf-8").format(
        dag=DAGEN[nu.weekday()],
        datum=f"{nu:%d/%m/%Y}",
        uur=f"{nu:%H:%M}",
        semester=semester,
        locatie=LOCATIE,
        sessie_id=sessie["id"],
        sessie_start=f"{sessie['start']:%H:%M}",
        aantal_vragen=len(vragen),
        overzicht=overzicht(vakken),
        fiches=fiches,
    ).strip()


def maak_client():
    load_dotenv(MAP / ".env")
    api_key = os.getenv("R33_API_KEY")
    if not api_key or not api_key.startswith("sk-r33-"):
        raise SystemExit("Zet eerst je route33 API key (R33_API_KEY) in het .env bestand.")
    return httpx.Client(base_url=BASE_URL, headers={"Authorization": f"Bearer {api_key}"}, timeout=60)


def laad_verbruik():
    """Totaal uitgegeven euro's plus een log per bericht, bewaard tussen sessies."""
    if VERBRUIK_BESTAND.exists():
        return json.loads(VERBRUIK_BESTAND.read_text(encoding="utf-8"))
    return {"euro": 0.0}


def kost(usage):
    return (usage["prompt_tokens"] * PRIJS_IN + usage["completion_tokens"] * PRIJS_UIT) / 1_000_000


def vandaag_verbruikt(verbruik):
    vandaag = datetime.now().strftime("%d/%m/%Y")
    return sum(b["euro"] for b in verbruik.get("berichten", []) if b.get("tijd", "").startswith(vandaag))


def vraag_ai(client, vraag, systeem, context_aan, browser=None):
    # shortcut: telt enkel oproepen van StudieBuddy zelf, niet ander gebruik van dezelfde key; zet ook een limiet in het route33-dashboard
    with verbruik_slot:
        verbruik = laad_verbruik()
    if BUDGET and verbruik["euro"] >= BUDGET:
        return f"[Budget op] StudieBuddy heeft al €{verbruik['euro']:.4f} van de €{BUDGET:.2f} verbruikt."
    if DAG_BUDGET and vandaag_verbruikt(verbruik) >= DAG_BUDGET:
        return f"[Daglimiet] Het budget van €{DAG_BUDGET:.2f} voor vandaag is op. Morgen kan je weer vragen stellen."

    r = client.post("/chat/completions", json={
        "model": MODEL,
        "max_tokens": MAX_ANTWOORD_TOKENS,
        "messages": [
            {"role": "system", "content": systeem},
            {"role": "user", "content": vraag},
        ],
    })
    r.raise_for_status()
    data = r.json()
    antwoord = data["choices"][0]["message"]["content"]

    usage = data["usage"]
    euro = kost(usage)
    with verbruik_slot:
        verbruik = laad_verbruik()  # opnieuw lezen: een andere request kan intussen geschreven hebben
        verbruik["euro"] += euro
        verbruik.setdefault("berichten", []).append({
            "tijd": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "vraag": vraag[:80],
            "context": context_aan,
            "browser": browser,
            "tokens_in": usage["prompt_tokens"],
            "tokens_uit": usage["completion_tokens"],
            "euro": euro,
        })
        try:
            VERBRUIK_BESTAND.parent.mkdir(parents=True, exist_ok=True)
            VERBRUIK_BESTAND.write_text(json.dumps(verbruik, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass  # chat blijft werken ook als het logbestand niet schrijfbaar is

    return antwoord


def api_fout(fout):
    return f"[API-fout {fout.response.status_code}] {fout.response.text[:200]}"


def main():
    client = maak_client()

    context_aan = True

    print("StudieBuddy: Hallo! Ik ben je StudieBuddy. Wat wil je weten?\n")

    try:
        while True:
            vraag = input("Jij: ").strip()
            if not vraag:
                continue
            if vraag == "/stop":
                break
            if vraag.startswith("/context"):
                keuze = vraag.removeprefix("/context").strip()
                context_aan = {"aan": True, "uit": False}.get(keuze, not context_aan)
                print(f"[Context staat nu {'AAN' if context_aan else 'UIT'}]\n")
                continue
            if vraag == "/toon":
                print(bouw_context(context_aan) + "\n")
                continue

            sessie["vragen"].append(vraag)
            try:
                antwoord = vraag_ai(client, vraag, bouw_context(context_aan), context_aan)
            except httpx.HTTPStatusError as fout:
                antwoord = api_fout(fout)
            print(f"StudieBuddy: {antwoord}\n")
    except (KeyboardInterrupt, EOFError):
        print()

    print("Tot later!")


if __name__ == "__main__":
    main()
