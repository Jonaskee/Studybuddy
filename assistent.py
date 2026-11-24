"""
StudieBuddy - een simpele AI-assistent met eigen context (PoC).

Context die we zelf toevoegen:
  1. Rol                     -> hoe de assistent zich gedraagt
  2. Kennis                  -> ECTS-fiches: de standaardfiches uit Supabase (tabel vakken, zie supabase/schema.sql),
                                de PDF's die de student zelf uploadde, en context/<vak>/*.md als reserve
  3. Tijd / locatie          -> huidige dag, uur, semester en locatie
  4. Sessiegegevens          -> sessie-id, starttijd en aantal vragen van deze sessie

De system prompt zelf staat in systeem_prompt.md; bouw_context() vult de {velden} in.

Starten: python assistent.py
"""

import math
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from dotenv import load_dotenv

BASE_URL = "https://api.route33.ai/v1"
MODEL = "z-ai/glm-5.3-flash"  # goedkoopste model op route33
PRIJS_IN, PRIJS_UIT = 0.05, 0.20  # euro per 1M tokens (route33 pricing)
MAX_ANTWOORD_TOKENS = 600  # begrenst de kost per antwoord, ook als iemand om een "heel lang antwoord" vraagt
LOCATIE = "Campus, België"
TIJDZONE = ZoneInfo("Europe/Brussels")  # Vercel draait in UTC; zonder dit klopt het uur in de prompt niet

MAP = Path(__file__).parent
load_dotenv(MAP / ".env")


def _euro_uit_env(naam, standaard):
    """Bedrag in euro uit .env (punt, geen komma). 0 = geen enkele vraag meer; een tikfout laat de app niet starten."""
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


BUDGET = _euro_uit_env("TOTAAL_BUDGET", 1.00)   # euro in totaal; daarboven stuurt StudieBuddy geen oproepen meer
DAG_BUDGET = _euro_uit_env("DAG_BUDGET", 0.10)  # euro per dag, zodat één spammer niet in één dag alles opmaakt
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = (os.getenv("SUPABASE_KEY") or "").strip()  # publishable/anon key: RLS laat enkel de standaardfiches zien
# Geheim: enkel hiermee kan de server het verbruik lezen en boeken (supabase/verbruik.sql). Op Vercel is er geen vaste schijf.
SERVER_SLEUTEL = os.getenv("SUPABASE_SERVER_SLEUTEL")
PROMPT_BESTAND = MAP / "systeem_prompt.md"  # sjabloon van de system prompt
CONTEXT_MAP = MAP / "context"  # reserve: de fiches als .md, voor lokaal werken zonder Supabase

EXTRA_TEKENS = 4000  # ruimte voor secties naast "Algemene informatie" (alle fiches samen = ~15k tokens, te duur per vraag); gemeten met eval_bronnen.py
MAX_SECTIE_PDF = 2500  # tekens; een lange sectie uit een PDF wordt in delen geknipt, zodat enkel het nuttige deel meegaat
# Studententaal -> sectienummer van de ECTS-fiche (woordbegin), voor vragen die het vakjargon niet gebruiken.
HINTS = {
    2: ("volgtijd", "voorwaard", "opnemen", "beginnen", "starten", "simultaan"),
    3: ("leer", "omschrijv", "bouwt", "verder", "over"),
    4: ("leerdoel", "competent"),
    5: ("inhoud", "onderwerp", "thema", "werkdag", "fase", "activiteit", "buitenland"),
    6: ("materiaal", "boek", "cursus"),
    7: ("uren", "contactu", "werkvorm", "studietijd"),
    8: ("examen", "toets", "evalu", "geëvalu", "weegt", "weging", "portfolio", "permanent", "punten", "kans"),
    9: ("aanwezig", "afwezig", "ziek", "attest", "inhalen", "extra", "deadline", "buitenland", "reizen", "verplicht"),
}
# Koppen zoals ze in een ECTS-fiche als PDF staan (zonder "##"), met hun sectienummer.
PDF_KOPPEN = {
    1: ("algemene informatie", "algemene gegevens"),
    2: ("volgtijdelijkheid",),
    3: ("korte omschrijving", "omschrijving", "beschrijving"),
    4: ("olr-leerdoelen", "olr leerdoelen", "leerdoelen", "competenties", "doelstellingen"),
    5: ("leerinhoud", "inhoud"),
    6: ("studiematerialen", "studiemateriaal", "cursusmateriaal"),
    7: ("onderwijsorganisatie", "werkvormen", "onderwijsactiviteiten"),
    8: ("toetsing", "evaluatie", "beoordeling"),
    9: ("aanvullende bepalingen", "bijzondere bepalingen", "aanvullende toetsingsbepalingen"),
}
VOORKEUR = (3, 8, 2, 5, 9, 7, 6, 4)  # bij gelijke score: de secties waar studenten het vaakst naar vragen eerst
STOPWOORDEN = {"hoeveel", "welke", "wanneer", "waar", "voor", "zijn", "mijn", "moet", "hebben", "heeft", "krijg",
               "wordt", "worden", "deze", "die", "dat", "het", "een", "vak", "vakken", "alle", "samen", "geen", "niet"}

DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]

# Sessiegegevens: bestaan enkel zolang het programma draait
sessie = {
    "id": uuid.uuid4().hex[:8],
    "start": datetime.now(TIJDZONE),
    "vragen": [],
}


def sleutel(naam):
    """Vergelijkbare vaknaam: "Project Start-up" en "Project Start up" zijn hetzelfde vak."""
    return re.sub(r"[^a-z0-9]", "", (naam or "").lower())


def _pdf_kop(regel):
    """Het sectienummer als deze PDF-regel een kop is ("8. Toetsing & Evaluatie"), anders None."""
    schoon = re.sub(r"^\s*(\d+[.)]?\s*)", "", regel).strip().lower().rstrip(":")
    if not schoon or len(schoon) > 45:
        return None
    for nr, koppen in PDF_KOPPEN.items():
        if any(schoon == k or schoon.startswith(k + " ") for k in koppen):  # "evaluatievorm" is geen kop
            return nr
    return None


def _in_delen(sectie, maximum):
    """Een te lange sectie in stukken van hoogstens `maximum` tekens (op een witregel of regeleinde)."""
    tekst, delen = sectie["tekst"], []
    while len(tekst) > maximum:
        knip = max(tekst.rfind("\n\n", 0, maximum), tekst.rfind("\n", 0, maximum))
        knip = knip if knip > maximum // 3 else maximum
        delen.append(tekst[:knip].strip())
        tekst = tekst[knip:].strip()
    delen.append(tekst)
    return [{**sectie, "titel": sectie["titel"] + (f" (deel {i})" if len(delen) > 1 else ""), "tekst": d}
            for i, d in enumerate(delen, 1) if d]


def secties_uit(naam, tekst):
    """Knipt een ECTS-fiche op in secties: "## "-koppen (markdown), anders de koppen uit een PDF-fiche,
    anders stukken van ~1500 tekens. De eerste sectie is steeds de algemene informatie (gaat altijd mee)."""
    tekst = (tekst or "").strip()
    if not tekst:
        return []
    if re.search(r"(?m)^## ", tekst):
        kop, *delen = re.split(r"(?m)^## ", tekst)
        secties = []
        for deel in delen:
            titel, _, inhoud = deel.partition("\n")
            nr = re.match(r"\d+", titel)
            inhoud = re.sub(r"(?m)^-{3,}\s*$", "", inhoud).strip()  # scheidingslijnen kosten enkel tokens
            secties.append({"vak": naam, "nr": int(nr.group()) if nr else 0, "titel": titel.strip(), "tekst": inhoud})
        if secties:  # kop (academiejaar, opleidingscode) hoort bij de algemene informatie
            secties[0]["tekst"] = re.sub(r"(?m)^-{3,}\s*$", "", kop).strip() + "\n" + secties[0]["tekst"]
        return secties

    # PDF: zoek de gekende koppen; wat ervoor staat (vaknaam, opleiding, studiepunten) is algemene informatie
    secties, huidig = [], {"nr": 1, "titel": "1. Algemene informatie", "regels": []}
    for regel in tekst.splitlines():
        nr = _pdf_kop(regel)
        if nr and nr != huidig["nr"]:  # zelfde nummer (bv. de kop "Algemene informatie" na de inleiding): samenvoegen
            secties.append(huidig)
            huidig = {"nr": nr, "titel": f"{nr}. {regel.strip().rstrip(':')}", "regels": []}
        else:
            huidig["regels"].append(regel)
    secties.append(huidig)
    secties = [{"vak": naam, "nr": s["nr"], "titel": s["titel"], "tekst": "\n".join(s["regels"]).strip()}
               for s in secties if "\n".join(s["regels"]).strip()]
    if len({s["nr"] for s in secties}) < 3:  # geen herkenbare koppen: knip in stukken, het woordzoeken doet de rest
        stukken = _in_delen({"vak": naam, "nr": 1, "titel": "Fiche", "tekst": tekst}, 1500)
        return [{**s, "nr": 1 if i == 1 else 9 + i, "titel": "Begin van de fiche" if i == 1 else f"Deel {i}"}
                for i, s in enumerate(stukken, 1)]
    return [deel for s in secties for deel in _in_delen(s, MAX_SECTIE_PDF)]


def maak_vak(naam, tekst, aliassen=(), studiepunten=None, bron="standaard"):
    return {"naam": naam, "termen": {naam.lower(), *(a.lower() for a in aliassen)},
            "studiepunten": studiepunten, "secties": secties_uit(naam, tekst), "bron": bron}


def laad_vakken():
    """De standaardfiches: uit Supabase (tabel vakken), of uit context/ als Supabase niet bereikbaar is."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            r = httpx.get(f"{SUPABASE_URL}/rest/v1/vakken", headers={"apikey": SUPABASE_KEY},
                          params={"select": "naam,fiche_md,aliassen,studiepunten", "order": "naam"}, timeout=10)
            r.raise_for_status()
            if r.json():
                return [maak_vak(v["naam"], v["fiche_md"], v["aliassen"] or (), v["studiepunten"]) for v in r.json()]
        except httpx.HTTPError:
            pass  # val terug op de lokale fiches
    return laad_vakken_lokaal()


def laad_vakken_lokaal():
    """Elke submap van context/ is een vak, met de ECTS-fiche(s) als .md erin."""
    vakken = []
    for vak_map in sorted(CONTEXT_MAP.iterdir()) if CONTEXT_MAP.is_dir() else []:
        if vak_map.is_dir():
            tekst = "\n\n".join(p.read_text(encoding="utf-8") for p in sorted(vak_map.glob("*.md")))
            sp = re.search(r"\*\*Studieomvang:\*\*\s*(\d+)", tekst)
            vakken.append(maak_vak(vak_map.name.replace("_", " "), tekst, studiepunten=int(sp.group(1)) if sp else None))
    return vakken


def vakken_voor(gevolgd=None, eigen_fiches=None, standaard=None):
    """De vakken waarover de AI antwoordt. Zonder pakket: alle standaardfiches. Met een pakket uit de onboarding
    enkel de vakken van de student, zijn eigen geüploade PDF vóór de standaardfiche; een vak zonder fiche komt
    enkel in het overzicht, zodat de AI eerlijk kan zeggen dat er geen fiche is.
    gevolgd = [{"naam", "sp"}], eigen_fiches = {vaknaam: tekst uit de PDF}."""
    standaard = laad_vakken() if standaard is None else standaard
    if not gevolgd:
        return standaard
    per_sleutel = {sleutel(v["naam"]): v for v in standaard}
    eigen = {sleutel(naam): tekst for naam, tekst in (eigen_fiches or {}).items() if (tekst or "").strip()}
    vakken = []
    for g in gevolgd:
        naam, sp = str(g.get("naam") or "").strip(), g.get("sp")
        if not naam:
            continue
        basis = per_sleutel.get(sleutel(naam))
        if sleutel(naam) in eigen:
            vak = maak_vak(naam, eigen[sleutel(naam)], (basis or {}).get("termen", ()), bron="pdf")
        elif basis:
            vak = dict(basis)
        else:
            vak = maak_vak(naam, "", bron=None)
        vakken.append({**vak, "naam": naam, "termen": vak["termen"] | {naam.lower()},
                       "studiepunten": sp if sp is not None else vak["studiepunten"]})
    return vakken


def overzicht(vakken):
    """Door de server berekend overzicht: het model vergeet al eens een vak bij het optellen over alle fiches."""
    regels = []
    for v in vakken:
        sp = f"{v['studiepunten']:g} studiepunten" if v["studiepunten"] is not None else "studiepunten onbekend"
        regels.append(f"- {v['naam']}: {sp}" + ("" if v["secties"] else " (geen ECTS-fiche beschikbaar)"))
    totaal = sum(v["studiepunten"] or 0 for v in vakken)
    tekst = "\n".join(regels) + f"\nTotaal: {totaal:g} studiepunten over {len(vakken)} vakken."
    return {"vak": "Alle vakken", "nr": 0, "titel": "Overzicht studiepunten (berekend uit de fiches)", "tekst": tekst}


def genoemde_vakken(vakken, vragen):
    """De vakken die de nieuwste vraag noemt (naam of bijnaam), anders die van de vorige vraag (vervolgvraag)."""
    for vraag in reversed(list(vragen)[-2:]):
        q = vraag.lower()
        treffers = {v["naam"]: sum(bool(re.search(rf"(?<!\w){re.escape(t)}(?!\w)", q)) for t in v["termen"])
                    for v in vakken}
        beste = max(treffers.values(), default=0)
        if beste:
            return {naam for naam, n in treffers.items() if n == beste}
    return set()


def zoek_bronnen(vakken, vragen):
    """Kiest de stukken ECTS-fiche voor de nieuwste vraag: altijd "Algemene informatie" van elk vak
    (studiepunten, titularis, tweede examenkans, ...), plus de best passende andere secties."""
    gekozen = [s for v in vakken for s in v["secties"][:1]]
    rest = [s for v in vakken for s in v["secties"][1:]]
    genoemd = genoemde_vakken(vakken, vragen)
    woorden = {w for w in re.findall(r"\w+", vragen[-1].lower()) if len(w) >= 4 and w not in STOPWOORDEN}
    eigen_vak = {s["vak"]: v["naam"] for v in vakken for s in v["secties"]}  # sectie -> vaknaam in het pakket

    def score(s):
        tekst = s["tekst"].lower() + " " + s["titel"].lower()
        # zeldzame woorden tellen zwaarder (idf): "werkdagen" zegt meer dan "examen"
        punten = sum(math.log(len(rest) / df) for w in woorden
                     if w[:6] in tekst and (df := sum(w[:6] in (r["tekst"] + r["titel"]).lower() for r in rest)))
        punten += 2 * any(w.startswith(h) for w in woorden for h in HINTS.get(s["nr"], ()))
        if genoemd:
            punten = punten + 3 if eigen_vak.get(s["vak"], s["vak"]) in genoemd else punten * 0.2
        return punten

    ruimte = EXTRA_TEKENS
    for s in sorted(rest, key=lambda s: (-score(s), VOORKEUR.index(s["nr"]) if s["nr"] in VOORKEUR else 99)):
        if score(s) <= 0 or ruimte <= 0:
            break
        if len(s["tekst"]) <= ruimte or len(gekozen) == len(vakken):  # de beste sectie altijd, ook als ze groot is
            gekozen.append(s)
            ruimte -= len(s["tekst"])
    return gekozen


def bouw_context(context_aan, vragen=None, vakken=None, samenvattingen=()):
    """Stelt de system prompt samen. Geeft (prompt, labels) terug; labels = {"B1": bron, ...} voor de bronvermelding.
    `vragen` = eerdere vragen van deze gebruiker, de nieuwste laatst (standaard de terminalsessie).
    `vakken` = de vakken van deze student (vakken_voor); standaard alle standaardfiches.
    `samenvattingen` = secties met de eigen samenvattingen van de student; gaan altijd mee."""
    if not context_aan:
        return "Je bent een behulpzame assistent.", {}
    vragen = list(sessie["vragen"] if vragen is None else vragen)

    nu = datetime.now(TIJDZONE)
    semester = 1 if nu.month >= 9 or nu.month == 1 else 2
    vakken = laad_vakken() if vakken is None else vakken
    labels = {f"B{i}": s for i, s in enumerate([overzicht(vakken), *zoek_bronnen(vakken, vragen), *samenvattingen], 1)}
    bronnen = "\n\n".join(f"[{label}] {s['vak']} — {s['titel']}\n{s['tekst']}" for label, s in labels.items())

    # De tekst staat in systeem_prompt.md; hier vullen we enkel de {velden} in.
    prompt = PROMPT_BESTAND.read_text(encoding="utf-8").format(
        dag=DAGEN[nu.weekday()],
        datum=f"{nu:%d/%m/%Y}",
        uur=f"{nu:%H:%M}",
        semester=semester,
        locatie=LOCATIE,
        sessie_id=sessie["id"],
        sessie_start=f"{sessie['start']:%H:%M}",
        aantal_vragen=len(vragen),
        vorige_vragen=" | ".join(vragen[-4:-1]) or "(geen)",
        bronnen=bronnen,
    ).strip()
    return prompt, labels


def bronnen_uit_antwoord(antwoord, labels):
    """Houdt enkel bronlabels over die echt meegestuurd zijn (een verzonnen [B99] verdwijnt).
    Geeft (antwoord met [Bn]-labels, geciteerde bronnen in volgorde) terug."""
    # Het model plakt soms een kladversie voor het antwoord ("... [B2].AI for Business ..."): hou de laatste versie.
    plak = re.search(r"[.!?](?=[A-ZÀ-Ý])", antwoord)
    if plak and antwoord[plak.end():][:15].lower() == antwoord[:15].lower():
        antwoord = antwoord[plak.end():]
    geciteerd = []

    def vervang(m):
        echte = [l for l in re.findall(r"B\d+", m.group()) if l in labels]
        geciteerd.extend(l for l in echte if l not in geciteerd)
        return "".join(f"[{l}]" for l in echte)

    tekst = re.sub(r"\[\s*B\d+(?:\s*[-–,;]\s*B?\d+)*\s*\]", vervang, antwoord)
    return tekst, [{"label": l, **labels[l]} for l in geciteerd]


def maak_client():
    api_key = os.getenv("R33_API_KEY")
    if not api_key or not api_key.startswith("sk-r33-"):
        raise SystemExit("Zet eerst je route33 API key (R33_API_KEY) in het .env bestand.")
    # De limieten (budget, daglimiet, vragen per browser) staan in Supabase: zonder kan de chat niet veilig draaien.
    if not SUPABASE_URL or not SUPABASE_KEY or not SERVER_SLEUTEL:
        raise SystemExit("Zet SUPABASE_URL, SUPABASE_KEY en SUPABASE_SERVER_SLEUTEL in het .env bestand.")
    return httpx.Client(base_url=BASE_URL, headers={"Authorization": f"Bearer {api_key}"}, timeout=60)


def kost(usage):
    return (usage["prompt_tokens"] * PRIJS_IN + usage["completion_tokens"] * PRIJS_UIT) / 1_000_000


class Limiet(Exception):
    """Een limiet is bereikt; de tekst is de melding voor de gebruiker."""


def rpc(functie, **args):
    """Roept een databasefunctie uit supabase/verbruik.sql op, met de geheime serversleutel."""
    r = httpx.post(f"{SUPABASE_URL}/rest/v1/rpc/{functie}", headers={"apikey": SUPABASE_KEY},
                   json={"p_sleutel": SERVER_SLEUTEL, **args}, timeout=10)
    r.raise_for_status()
    return r.json() if r.content else None


def vraag_ai(client, vraag, context_aan, browser=None, max_per_browser=None, vakken=None, samenvattingen=()):
    """Controleert de limieten in de database, stelt de vraag en boekt de kost.
    Geeft (antwoord, resterende vragen, eigen vragen, bronnen) terug, of gooit Limiet."""
    # shortcut: telt enkel oproepen van StudieBuddy zelf, niet ander gebruik van dezelfde key; zet ook een limiet in het route33-dashboard
    res = rpc("vraag_reserveren", p_browser=browser, p_vraag=vraag, p_context=context_aan,
              p_max_per_browser=max_per_browser, p_budget=BUDGET, p_dag_budget=DAG_BUDGET)
    if not res["ok"]:
        raise Limiet({
            "budget": f"[Budget op] StudieBuddy heeft het budget van €{BUDGET:.2f} opgebruikt.",
            "dag": f"[Daglimiet] Het budget van €{DAG_BUDGET:.2f} voor vandaag is op. Morgen kan je weer vragen stellen.",
            "browser": f"Je hebt je {max_per_browser} vragen voor deze demo gebruikt. Bedankt om StudieBuddy te testen!",
        }[res["reden"]])

    vragen = res["vragen"] if browser else sessie["vragen"]
    try:
        systeem, labels = bouw_context(context_aan, vragen, vakken, samenvattingen)
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
    except Exception:
        rpc("vraag_annuleren", p_id=res["id"])  # mislukte oproep telt niet mee
        raise

    rpc("vraag_afronden", p_id=res["id"], p_euro=kost(usage),
        p_tokens_in=usage["prompt_tokens"], p_tokens_uit=usage["completion_tokens"])
    antwoord, bronnen = bronnen_uit_antwoord(antwoord, labels)
    return antwoord, res["resterend"], vragen, bronnen


def api_fout(fout):
    """Details enkel in de serverlog: de gebruiker krijgt geen interne info (bv. het antwoord van route33)."""
    detail = f" {fout.response.status_code} {fout.response.text[:200]}" if isinstance(fout, httpx.HTTPStatusError) else ""
    print(f"API-fout: {type(fout).__name__}{detail}", file=sys.stderr)
    return "[Fout] StudieBuddy kan nu even geen antwoord geven. Probeer het zo opnieuw; deze vraag telt niet mee."


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
                print(bouw_context(context_aan)[0] + "\n")
                continue

            sessie["vragen"].append(vraag)
            try:
                antwoord = vraag_ai(client, vraag, context_aan)[0]
            except Limiet as fout:
                antwoord = str(fout)
            except httpx.HTTPError as fout:
                antwoord = api_fout(fout)
            print(f"StudieBuddy: {antwoord}\n")
    except (KeyboardInterrupt, EOFError):
        print()

    print("Tot later!")


if __name__ == "__main__":
    main()
