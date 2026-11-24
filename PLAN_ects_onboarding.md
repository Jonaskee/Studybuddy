# Plan: onboarding met pakketten, ECTS-beheer en de juiste context voor de AI

## 1. Waar we nu staan

| Onderdeel | Nu | Probleem voor wat we willen |
|---|---|---|
| ECTS-fiches | `.md` bestanden in `context/<vak>/`, ingelezen door `laad_vakken()` | Op Vercel is de map read-only: uploaden kan niet. Geen school/richting/jaar, geen eigenaar, geen status. |
| Gebruikers | Geen. `sessie` is globaal | Alle bezoekers delen één sessie. Privé pakketten en moderators hebben een identiteit nodig. |
| Relevantie | `relevante_vakken()`: zoekt woorden uit de vaknaam in de laatste 2 vragen, max 2 fiches | Werkt voor 8 vakken van één richting, niet voor veel scholen/richtingen. |
| Gesprek | Enkel de laatste vraag gaat naar het model | Geen echte vervolgvragen mogelijk. |

## 2. Het kernidee: pakketten

Een **pakket** = één school + één richting + één academiejaar (+ trajectschijf), met de vakken en hun ECTS-fiche erin. Bijvoorbeeld *"AP – Toegepaste Informatica – AI – 3de jaar – 2026-27"*, met 8 vakken.

- Studenten maken pakketten aan en delen ze. De volgende student van dezelfde richting hoeft alleen het pakket te kiezen.
- Een **publiek** pakket wordt pas zichtbaar voor iedereen na controle door een mens. Een **privé** pakket werkt meteen, maar enkel voor de maker.
- Wie een pakket kiest, krijgt een **persoonlijke versie**: vakken uitvinken, eigen vakken toevoegen. Die wijzigingen gelden enkel voor hem.
- Klopt het pakket niet meer (fiche verouderd, vak ontbreekt), dan dient de student een **wijzigingsvoorstel** in. Dat gaat ook langs een mens.

De persoonlijke versie is geen kopie maar het pakket **plus jouw aanpassingen erbovenop**. Wordt het publieke pakket verbeterd, dan krijgt iedereen die het gebruikt de verbetering automatisch.

## 3. Keuze: Supabase als enige nieuwe bouwsteen

Eén gratis Supabase-project geeft ons alles wat ontbreekt, zonder eigen server:

- **Postgres**: scholen, richtingen, pakketten, vakken
- **Auth**: inloggen met e-mail (magic link, geen wachtwoorden)
- **Row Level Security (RLS)**: de database zelf beslist wie wat ziet (privé vs publiek), ook als we een fout maken in Flask
- **Storage**: de originele PDF's bewaren, zodat de reviewer kan nakijken of een fiche echt is
- **`pg_trgm`** (ingebouwd): fuzzy zoeken, zodat "AP Hogeschool" en "Artesis Plantijn" hetzelfde vinden

Flask spreekt Supabase aan met `httpx` (hebben we al, via de REST-API). Enige nieuwe library: `pypdf` om tekst uit PDF's te halen.

## 4. Datamodel

```
scholen     (id, naam, aliassen[], email_domein, status)
richtingen  (id, school_id, naam, afstudeerrichting, status)
pakketten   (id, richting_id, academiejaar, trajectschijf,
             zichtbaarheid: 'prive' | 'publiek',
             status: 'in_review' | 'goedgekeurd' | 'afgekeurd',
             maker_id, gebaseerd_op_pakket_id, review_opmerking)
vakken      (id, pakket_id, naam, aliassen[], studiepunten, semester,
             fiche_md, fiche_pdf_pad,
             eigenaar_id,     -- NULL = hoort bij het pakket; ingevuld = eigen vak van één student
             status)
profielen   (user_id, pakket_id, rol: 'student' | 'moderator')
uitgevinkt  (user_id, vak_id)        -- vakken van het pakket die deze student niet volgt
voorstellen (id, pakket_id, type: 'vak_toevoegen' | 'vak_wijzigen' | 'vak_verwijderen',
             vak_id, nieuwe_data (json), indiener_id,
             status: 'in_review' | 'goedgekeurd' | 'afgekeurd', review_opmerking)
```

**De vakken van een student** = vakken van zijn pakket, min `uitgevinkt`, plus vakken met `eigenaar_id = hij`. Dat is één query, en precies wat de AI nodig heeft.

Regels:

- **Zichtbaarheid (RLS)**: een pakket is zichtbaar als het `publiek` en `goedgekeurd` is, of als jij de maker bent, of als je moderator bent. Eigen vakken zijn enkel zichtbaar voor de eigenaar.
- **Wijzigingsvoorstellen** worden pas na goedkeuring in het pakket verwerkt. Tot dan ziet de indiener zijn voorstel al in zijn eigen versie, zodat hij niet hoeft te wachten.
- **Nooit echt verwijderen**: alles wat weg moet krijgt een status. Zo kan niemand per ongeluk of expres data vernietigen.
- **Nieuw academiejaar**: "Nieuw pakket op basis van 2026-27" kopieert de vakkenlijst (`gebaseerd_op_pakket_id`). De student hoeft dan enkel de nieuwe PDF's te uploaden.

## 5. Onboarding

1. **Inloggen** met e-mail (magic link). Het e-maildomein (`@student.ap.be`) stelt alvast een school voor.
2. **School en richting ingeven.** Het programma zoekt met fuzzy search of ze al bestaan en toont de beste treffers ("Bedoel je *Artesis Plantijn Hogeschool*?"). Een AI is hier niet nodig: `pg_trgm` is gratis en voorspelbaar.
3. **Pakket kiezen.** Lijst van bestaande pakketten voor die richting:

   | Pakket | Jaar | Vakken | Status | Gebruikers |
   |---|---|---|---|---|
   | AI – 3de jaar | 2026-27 | 8 | ✅ nagekeken | 23 |
   | AI – 3de jaar | 2025-26 | 7 | ✅ nagekeken | 41 |

   Plus de knop **"Geen van deze, ik maak een nieuw pakket"**.

4a. **Pakket gekozen** → pagina "Mijn vakken":
   - vakken uitvinken die hij niet volgt
   - **+ Vak toevoegen** (eigen vak, privé, met PDF), bv. een vak uit een ander jaar
   - per vak **"Klopt niet"** → wijzigingsvoorstel (nieuwe PDF, vak verwijderen) dat naar de review gaat

4b. **Nieuw pakket** → formulier:
   - academiejaar + trajectschijf
   - vakken toevoegen: per vak een **PDF-upload**. Uit de PDF halen we de tekst (`pypdf`), en één goedkope LLM-oproep vult naam, studiepunten, semester en titularis vooraf in. De student controleert.
   - **Privé of publiek**

5. **Klaar** → naar de chat. "Mijn vakken" blijft altijd bereikbaar in het menu.

## 6. Human in the loop en anti-spam

Pagina **/review**, enkel voor `rol = 'moderator'`. Daar staan nieuwe publieke pakketten, nieuwe scholen/richtingen en wijzigingsvoorstellen. Per item zie je de PDF naast de tekst, en bij een wijziging de verschillen met de huidige versie. Knoppen: **Goedkeuren** / **Afkeuren + opmerking** (de indiener ziet de opmerking).

Om spam en lege pakketten te voorkomen, controleren we al **vóór** de review automatisch:

- **Geen lege pakketten**: een publiek pakket moet minstens 1 vak hebben, en elk vak een fiche (PDF of tekst). Anders kan je niet indienen.
- **Geen dubbels**: bestaat er al een goedgekeurd pakket voor dezelfde richting + jaar + trajectschijf, dan wordt "nieuw publiek pakket" geweigerd en krijg je "stel een wijziging voor" aangeboden.
- **Limiet per student**: max. 3 openstaande voorstellen/pakketten in review tegelijk.
- **Optionele AI-hint voor de reviewer**: "lijkt een echte ECTS-fiche, studiepunten komen overeen". Dat is een hint, geen beslissing.

De moderators zijn in het begin wij (handmatig `rol` zetten in Supabase). Later eventueel een vertrouwde student per richting.

## 7. Hoe weet de AI welke fiche relevant is?

In stappen, goedkoopste eerst:

1. **Enkel de vakken van de student** (zijn pakket, min uitgevinkt, plus eigen vakken). Dat is de grootste winst: ±8–12 vakken in plaats van de hele database. Het korte overzicht (naam, ECTS, semester, titularis) gaat altijd mee, zoals nu, maar uit kolommen in plaats van de fiche te parsen.
2. **Woorden + aliassen**: de huidige `relevante_vakken()` blijft, maar matcht ook op `aliassen` ("BAP", "stage" → Bachelorproef en stage).
3. **Router-oproep als er niets matcht**: een mini-oproep aan hetzelfde goedkope model: "Dit zijn de vakken (id + naam) en dit is de vraag. Welke vakken (max 2) zijn relevant? Antwoord als JSON." Een paar honderd tokens, een fractie van een cent.
4. **Welke fiche**: eigen vak of eigen voorstel > fiche uit het pakket. Is iets nog niet nagekeken, dan staat dat in de prompt, zodat de AI het erbij zegt.
5. **Pas later, als fiches groot worden**: fiches per sectie opknippen en met embeddings (pgvector, zit in Supabase) enkel de relevante stukken meesturen. Nu niet nodig: één fiche is ±120 regels.

Daarnaast nodig om "vragen stellen" goed te laten werken:

- **Sessie per gebruiker** in plaats van de globale `sessie`.
- **Laatste paar berichten meesturen** naar het model, zodat vervolgvragen werken.

## 8. Fases

| Fase | Wat | Resultaat |
|---|---|---|
| 0 | Supabase-project, tabellen, RLS. Seed-script dat de 8 bestaande fiches importeert als één goedgekeurd pakket *AP – TI – AI – 3de jaar – 2026-27*. `laad_vakken()` leest uit de DB. | App werkt zoals nu, data zit in de DB. |
| 1 | Inloggen + onboarding (school/richting zoeken → pakket kiezen) + "Mijn vakken" (uitvinken). Sessie en context per gebruiker. | Elke student krijgt antwoorden over zijn eigen vakken. |
| 2 | Nieuw pakket maken + eigen vak toevoegen: PDF-upload, tekst eruit halen, velden vooraf invullen, privé/publiek. | Studenten vullen ontbrekende richtingen zelf aan. |
| 3 | Reviewpagina, wijzigingsvoorstellen, anti-spamregels. | Publieke pakketten zijn nagekeken door een mens. |
| 4 | Aliassen, router-oproep, gespreksgeschiedenis. | De AI vindt het juiste vak ook bij vage vragen. |
| 5 (optioneel) | "Nieuw jaar op basis van vorig jaar", embeddings, vertrouwde studenten als moderator. | Schaal. |

De frontend blijft gewone HTML + JS (zoals `static/index.html`), met extra pagina's `onboarding.html`, `vakken.html` en `review.html`, en de Supabase JS-library via CDN voor het inloggen.

## 9. Risico's

- **RLS fout = privé data zichtbaar voor iedereen.** Test expliciet met twee accounts voor we live gaan.
- **Prompt injection via een fiche**: een PDF kan tekst bevatten als "negeer je instructies". Publieke pakketten gaan langs een mens, en privé vakken treffen enkel de uploader zelf. Zet in de system prompt dat de fiche data is, geen instructies.
- **Review-achterstand**: als niemand nakijkt, blijft alles hangen. Daarom werkt een pakket of voorstel al meteen voor de indiener zelf.
- **Budget**: router- en PDF-oproepen zijn extra API-calls. Verwaarloosbaar met het huidige model, maar het budget in `verbruik.json` telt op Vercel niet betrouwbaar. Zet het verbruik ook in de DB.

## 10. Open vragen voor het team

1. Supabase oké, of moet het iets anders zijn?
2. Enkel inloggen met een school-e-mailadres (minder spam), of elk e-mailadres?
3. Wie zijn de eerste moderators?
4. Mag een student meerdere pakketten combineren (bv. GIT-student met vakken uit 2de en 3de jaar), of volstaat "eigen vak toevoegen"?
