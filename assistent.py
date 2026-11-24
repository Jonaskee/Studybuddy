"""
StudieBuddy - een simpele AI-assistent met eigen context (PoC).

Context die we zelf toevoegen:
  1. Rol                     -> hoe de assistent zich gedraagt
  2. Kennis                  -> ECTS-fiches uit Supabase (tabel vakken, zie supabase/schema.sql)
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
BUDGET = 1.00  # euro; daarboven stuurt StudieBuddy geen oproepen meer
MAX_ANTWOORD_TOKENS = 600  # begrenst de kost per antwoord, ook als iemand om een "heel lang antwoord" vraagt
LOCATIE = "Campus, België"

MAP = Path(__file__).parent
load_dotenv(MAP / ".env")
try:
    DAG_BUDGET = float(os.getenv("DAG_BUDGET", "0.10"))  # euro per dag, zodat één spammer niet in één dag alles opmaakt
except ValueError:
    raise SystemExit("DAG_BUDGET in .env moet een getal zijn, bv. DAG_BUDGET=0.10")
if not 0 <= DAG_BUDGET < float("inf"):  # vangt ook nan en inf, die de limiet anders stil uitschakelen
    raise SystemExit("DAG_BUDGET in .env moet een getal van 0 of meer zijn, bv. DAG_BUDGET=0.10")
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # publishable/anon key: RLS laat enkel publieke, goedgekeurde data zien
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
    """Vaknaam -> ECTS-fiche, uit Supabase."""
    # shortcut: haalt alle publieke vakken op (er is nu één pakket); vanaf de onboarding (fase 1) filteren op het pakket van de student
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/vakken", headers={"apikey": SUPABASE_KEY},
                  params={"select": "naam,fiche_md", "order": "naam"}, timeout=10)
    r.raise_for_status()
    return {v["naam"]: v["fiche_md"] or "" for v in r.json()}


def overzicht(vakken):
    """Korte samenvatting per vak (titularis, studiepunten, semester) uit de fiches."""
    blokken = []
    for naam, fiche in vakken.items():
        info = [regel.replace("*", "").strip() for regel in fiche.splitlines()
                if any(regel.startswith(f"* **{veld}:**") for veld in INFO_VELDEN)]
        blokken.append(f"### {naam}\n" + "\n".join(f"- {i}" for i in info))
    return "\n\n".join(blokken)


def relevante_vakken(vakken, vragen):
    """Vakken die in de laatste 2 vragen van deze gebruiker genoemd worden (nieuwste vraag eerst)."""
    gevonden = []
    for vraag in reversed(vragen[-2:]):
        for naam in vakken:
            woorden = [w for w in naam.lower().split() if len(w) > 3]
            if naam not in gevonden and any(w in vraag.lower() for w in woorden):
                gevonden.append(naam)
    return gevonden[:MAX_FICHES]


def bouw_context(context_aan, vragen=None):
    """Stelt de system prompt samen. `vragen` = eerdere vragen van deze gebruiker (standaard de terminalsessie)."""
    if not context_aan:
        return "Je bent een behulpzame assistent."
    if vragen is None:
        vragen = sessie["vragen"]

    nu = datetime.now()
    semester = 1 if nu.month >= 9 or nu.month == 1 else 2
    vakken = laad_vakken()
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
    api_key = os.getenv("R33_API_KEY")
    if not api_key or not api_key.startswith("sk-r33-"):
        raise SystemExit("Zet eerst je route33 API key (R33_API_KEY) in het .env bestand.")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise SystemExit("Zet SUPABASE_URL en SUPABASE_KEY in het .env bestand.")
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
    return sum(b["euro"] for b in verbruik.get("berichten", []) if b["tijd"].startswith(vandaag))


verbruik_slot = threading.Lock()  # gelijktijdige vragen mogen elkaars kost niet overschrijven


def vraag_ai(client, vraag, systeem, context_aan, browser=None):
    # shortcut: telt enkel oproepen van StudieBuddy zelf, niet ander gebruik van dezelfde key; zet ook een limiet in het route33-dashboard
    with verbruik_slot:
        verbruik = laad_verbruik()
    if verbruik["euro"] >= BUDGET:
        return f"[Budget op] StudieBuddy heeft al €{verbruik['euro']:.4f} van de €{BUDGET:.2f} verbruikt."
    if vandaag_verbruikt(verbruik) >= DAG_BUDGET:
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
        verbruik = laad_verbruik()  # opnieuw lezen: een andere vraag kan intussen kost bijgeschreven hebben
        verbruik["euro"] += euro
        verbruik.setdefault("berichten", []).append({
            "tijd": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "vraag": vraag[:80],
            "context": context_aan,
            "tokens_in": usage["prompt_tokens"],
            "tokens_uit": usage["completion_tokens"],
            "euro": euro,
            "browser": browser,  # zodat de limiet per browser een herstart overleeft
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
