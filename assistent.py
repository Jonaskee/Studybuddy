"""
StudieBuddy - een simpele AI-assistent met eigen context (PoC).

Context die we zelf toevoegen:
  1. Rol                     -> hoe de assistent zich gedraagt
  2. Kennis                  -> context/<vak>/*.md (ECTS-fiches)
  3. Tijd / locatie          -> huidige dag, uur, semester en locatie
  4. Sessiegegevens          -> sessie-id, starttijd en aantal vragen van deze sessie

Starten: python assistent.py
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

BASE_URL = "https://api.route33.ai/v1"
MODEL = "z-ai/glm-5.3-flash"  # goedkoopste model op route33
PRIJS_IN, PRIJS_UIT = 0.05, 0.20  # euro per 1M tokens (route33 pricing)
BUDGET = 1.00  # euro; daarboven stuurt StudieBuddy geen oproepen meer
LOCATIE = "Campus, België"

MAP = Path(__file__).parent
CONTEXT_MAP = MAP / "context"
VERBRUIK_BESTAND = MAP / "verbruik.json"

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


def relevante_vakken(vakken):
    """Vakken die in de laatste 2 vragen genoemd worden (nieuwste vraag eerst)."""
    gevonden = []
    for vraag in reversed(sessie["vragen"][-2:]):
        for naam in vakken:
            woorden = [w for w in naam.lower().split() if len(w) > 3]
            if naam not in gevonden and any(w in vraag.lower() for w in woorden):
                gevonden.append(naam)
    return gevonden[:MAX_FICHES]


def bouw_context(context_aan):
    """Stelt de system prompt samen. Zonder context krijgt het model niets extra."""
    if not context_aan:
        return "Je bent een behulpzame assistent."

    nu = datetime.now()
    semester = 1 if nu.month >= 9 or nu.month == 1 else 2
    vakken = laad_vakken()
    fiches = "\n\n".join(vakken[naam] for naam in relevante_vakken(vakken)) or "(geen specifiek vak gevraagd)"

    return f"""## Rol
Je bent StudieBuddy, een studieassistent voor een 3de-jaarsstudent.
Antwoord kort (1 à 2 zinnen) in het Nederlands en enkel op basis van de info hieronder.
Gebruik gewone tekst zonder opmaak (geen * of **), want het antwoord verschijnt in een terminal.

## Tijd en locatie
Vandaag is het {DAGEN[nu.weekday()]} {nu:%d/%m/%Y}, het is {nu:%H:%M}.
We zitten in semester {semester}.
Locatie: {LOCATIE}

## Sessie
Sessie-id: {sessie['id']}
Gestart om: {sessie['start']:%H:%M}
Aantal vragen deze sessie: {len(sessie['vragen'])}

## Vakken van de student (overzicht)
{overzicht(vakken)}

## Volledige ECTS-fiche van het gevraagde vak
{fiches}"""


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


def vraag_ai(client, vraag, systeem, context_aan):
    # shortcut: telt enkel oproepen van StudieBuddy zelf, niet ander gebruik van dezelfde key
    verbruik = laad_verbruik()
    if verbruik["euro"] >= BUDGET:
        return f"[Budget op] StudieBuddy heeft al €{verbruik['euro']:.4f} van de €{BUDGET:.2f} verbruikt."

    r = client.post("/chat/completions", json={
        "model": MODEL,
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
    verbruik["euro"] += euro
    verbruik.setdefault("berichten", []).append({
        "tijd": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "vraag": vraag[:80],
        "context": context_aan,
        "tokens_in": usage["prompt_tokens"],
        "tokens_uit": usage["completion_tokens"],
        "euro": euro,
    })
    VERBRUIK_BESTAND.parent.mkdir(exist_ok=True)
    VERBRUIK_BESTAND.write_text(json.dumps(verbruik, indent=2, ensure_ascii=False), encoding="utf-8")

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
