"""
Meet of StudieBuddy de juiste ECTS-info vindt en juist antwoordt.

  python eval_bronnen.py        -> enkel het zoeken (gratis): zit de juiste sectie in wat naar de AI gaat?
  python eval_bronnen.py --ai   -> ook echte AI-antwoorden (kost ~1 cent): klopt het antwoord en de bron?

Voeg een vraag toe zodra iemand een fout antwoord meldt, zo komt die fout nooit terug.
"""

import re
import sys

import assistent

# (vraag, eerdere vraag of None, verwachte tekst in het antwoord (één van), verwachte bronnen {(vak, sectienummer)})
VRAGEN = [
    ("Hoeveel studiepunten is Trends in AI?", None, ["3"], {("Trends in AI", 1)}),
    ("Wie geeft AI for Business?", None, ["Cop"], {("AI for Business", 1)}),
    ("Is er een tweede examenkans voor Applied AI project?", None, ["niet", "geen"],
     {("Applied AI project", 1), ("Applied AI project", 8)}),
    ("Hoe wordt Sustainable IT geëvalueerd?", None, ["85"], {("Sustainable IT", 8)}),
    ("Hoeveel weegt het portfolio bij AI and Society?", None, ["15"], {("AI and Society", 8)}),
    ("Wat zijn de voorwaarden om aan de bachelorproef te beginnen?", None, ["60", "54"], {("Bachelorproef en stage", 2)}),
    ("Hoeveel werkdagen duurt de stage?", None, ["60"], {("Bachelorproef en stage", 5)}),
    ("Wat gebeurt er als ik twee keer ongewettigd afwezig ben bij Project Start up?", None, ["0"],
     {("Project Start up", 9)}),
    ("Moet ik naar het buitenland voor IT professional?", None, ["internationale week", "reizen"],
     {("IT professional", 9), ("IT professional", 5)}),
    ("Welke vakken hebben geen tweede examenkans?", None, ["Applied AI project"],
     {("Applied AI project", 1), ("IT professional", 1), ("Project Start up", 1)}),
    ("Hoeveel studiepunten zijn al mijn vakken samen?", None, ["60"], {("Alle vakken", 0), ("Trends in AI", 1)}),
    ("Wat leer je in Trends in AI?", None, ["ontwikkeling", "trend", "technolog"], {("Trends in AI", 3), ("Trends in AI", 5)}),
    ("En hoe wordt dat vak geëvalueerd?", "Wie is titularis van Sustainable IT?", ["85"], {("Sustainable IT", 8)}),
    ("Hoeveel extra examentijd krijg ik bij AI and Society?", None, ["1/3", "30 minuten"], {("AI and Society", 9)}),
    ("Wat is de BAP?", None, ["stage"], {("Bachelorproef en stage", 3)}),
    ("Wanneer is de grensdatum voor leerkrediet van Sustainable IT?", None, ["01.12.2026", "1 december", "01/12/2026"],
     {("Sustainable IT", 1)}),
    ("Welke vakken bouwen verder op Deep Learning?", None, ["Trends in AI"], {("Trends in AI", 3)}),
    ("In welk lokaal heb ik les voor Trends in AI?", None, ["niet", "geen"], set()),  # staat niet in de fiche
]


def test_opschonen():
    """Verzonnen of rare bronlabels en een geplakte kladversie van het model worden correct opgeruimd."""
    labels = {"B2": {"vak": "AI for Business", "nr": 1}, "B8": {"vak": "Trends in AI", "nr": 1}}
    tekst, b = assistent.bronnen_uit_antwoord(
        "AI for Business wordt gegeven door Cop [B2].AI for Business wordt gegeven door titularis Cop [B2].", labels)
    assert tekst == "AI for Business wordt gegeven door titularis Cop [B2]." and [x["label"] for x in b] == ["B2"], tekst
    tekst, b = assistent.bronnen_uit_antwoord("Niet in de fiche [B8-B16]; zie [B99] en [B2, B8].", labels)
    assert tekst == "Niet in de fiche [B8]; zie  en [B2][B8]." and [x["label"] for x in b] == ["B8", "B2"], tekst
    tekst, _ = assistent.bronnen_uit_antwoord("Het telt 3 studiepunten [B8]. Het is in semester 1.", labels)
    assert tekst == "Het telt 3 studiepunten [B8]. Het is in semester 1."


def main(met_ai):
    test_opschonen()
    vakken = assistent.laad_vakken()
    client = assistent.maak_client() if met_ai else None
    gevonden = juist = bron_ok = 0
    for vraag, vorige, verwacht, bronnen in VRAGEN:
        vragen = ([vorige] if vorige else []) + [vraag]
        gekozen = {(b["vak"], b["nr"]) for b in [assistent.overzicht(vakken), *assistent.zoek_bronnen(vakken, vragen)]}
        zoek_ok = not bronnen or bool(bronnen & gekozen)
        gevonden += zoek_ok
        regel = f"{'ok ' if zoek_ok else 'MIS'} zoeken"
        if met_ai:
            systeem, labels = assistent.bouw_context(True, vragen, vakken)
            r = client.post("/chat/completions", json={
                "model": assistent.MODEL, "max_tokens": assistent.MAX_ANTWOORD_TOKENS,
                "messages": [{"role": "system", "content": systeem}, {"role": "user", "content": vraag}]})
            r.raise_for_status()
            antwoord = r.json()["choices"][0]["message"]["content"]
            tekst, geciteerd = assistent.bronnen_uit_antwoord(antwoord, labels)
            a_ok = any(v.lower() in tekst.lower() for v in verwacht)
            b_ok = not bronnen or bool(bronnen & {(b["vak"], b["nr"]) for b in geciteerd})
            juist += a_ok
            bron_ok += b_ok
            regel += f" | {'ok ' if a_ok else 'FOUT'} antwoord | {'ok ' if b_ok else 'FOUT'} bron"
            regel += f"\n      -> {re.sub(r'\s+', ' ', tekst)[:160]}"
            regel += f"\n      bronnen: {', '.join(f'{b['vak']} §{b['nr']}' for b in geciteerd) or '-'}"
        print(f"{regel} | {vraag}")
    n = len(VRAGEN)
    print(f"\nZoeken: {gevonden}/{n} juiste sectie meegestuurd")
    if met_ai:
        print(f"Antwoord: {juist}/{n} juist  |  Bron: {bron_ok}/{n} juiste bron vermeld")
    assert gevonden == n, "het zoeken mist een sectie: zie MIS hierboven"


if __name__ == "__main__":
    main("--ai" in sys.argv)
