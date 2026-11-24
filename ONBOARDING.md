# Onboarding en moderatie

## Pagina's

| URL | Bestand | Wat |
|---|---|---|
| `/onboarding` | `static/onboarding.html` + `static/js/onboarding.js` | School en richting → pakket kiezen → nieuw pakket of aanpassen → status |
| `/moderatie` | `static/moderatie.html` + `static/js/moderatie.js` | Human in the loop: publieke pakketten en wijzigingsvoorstellen nakijken |
| `/` | `static/index.html` | De chat. Stuurt naar `/onboarding` zolang de onboarding niet afgerond is. |

Gedeelde stijl: `static/css/studybuddy.css` (licht en donker). De licht/donker-knop staat in `static/js/theme.js`: elke knop met `data-theme-toggle` wisselt het thema, de keuze wordt bewaard in `localStorage` (`sb-theme`).

Werkt op gsm en pc: onder 960 px breed één kolom zoals op een telefoon, daarboven een zijpaneel met de stappen links en de inhoud rechts.

## Data: frontend → backend → Supabase

De schermen praten enkel met `static/js/data.js` (object `SB`). Dat bestand doet
`fetch("/api/data/...")`; dezelfde functienamen en teruggegeven vormen als vroeger,
dus de UI is niet veranderd. Achter de API staat `opslag.py`:

```
browser (data.js)
   → /api/data/...            (data_api.py, Flask)
       → opslag.py
            → Supabase (REST + Storage)   als SUPABASE_URL + server-sleutel gezet zijn
            → data_store.json             anders (lokaal ontwikkelen)
```

De API heeft ook `/api/chat` (AI) en `/api/status` (vraaglimiet en eigen vorige
vragen) in `app.py`.

### Supabase klaarzetten

1. Maak een project op supabase.com.
2. SQL Editor → plak `supabase.sql` → Run. Dat maakt de tabellen, indexen en
   zet RLS dicht voor de publieke sleutel.
3. Storage → New bucket → naam `ects-fiches`, Private (of laat de SQL het doen).
4. Project Settings → API: kopieer de **Project URL** en de **service_role**-sleutel.
5. Zet ze in `.env`:

```
SUPABASE_URL=https://jouwproject.supabase.co
SUPABASE_SERVER_SLEUTEL=eyJ...service_role...
```

Gebruik bewust **niet** de anon-key: die staat nergens in de frontend, maar RLS
zet alles dicht. De server-sleutel blijft server-side.

De voorbeelddata (scholen, richtingen, pakketten, één voorstel) wordt bij de
eerste data-aanvraag automatisch geplaatst als de databank leeg is. Uitzetten
met `SEED_DEMO=0`.

### Tabellen

`pakketten` bewaart `vakken` en `groepen` als JSONB (één rij per pakket, dus
opslaan is atomair). Dat is een bewuste vereenvoudiging van de vroegere
genormaliseerde tabellen; de veldnamen binnen de JSON zijn dezelfde als in de UI.

```
scholen                (id, naam)
richtingen             (id, school_id → scholen, naam)
pakketten              (id, richting_id → richtingen, academiejaar, fase,
                        afstudeerrichting, status, gebruikers, mogelijk_verouderd,
                        ingediend_door, ingediend_op, afwijs_reden,
                        groepen jsonb, vakken jsonb, created_at)
persoonlijke_pakketten (student_id, basis_pakket_id → pakketten, uitgezet jsonb,
                        overgeslagen jsonb, keuzes jsonb, eigen_vakken jsonb, updated_at)
wijzigingsvoorstellen  (id, pakket_id → pakketten, tekst, door, op, status, afwijs_reden)
```

Hoe keuzes werken:
- **Keuzevak:** vakken met dezelfde `groep` (soort `keuze`); de student kiest er `kies` uit.
- **Keuzeoptie:** een groep met soort `optie`; elk vak in die groep hoort via `optie` bij een bundel (bv. "Startup"). De student kiest `kies` opties en krijgt alle vakken van die optie.
- **Semester:** `1`, `2`, `1of2` (student kiest zelf, bv. stage) of `jaar` (jaarvak). Zo komen de studiepunten per semester uit.

In de voorbeelddata is het pakket "3e bachelor · Artificiële Intelligentie"
overgenomen uit de ECTS-fiches in `context/` (samen 60 sp). De andere pakketten
en de optie "Research" zijn verzonnen voorbeelden.

### Lokaal zonder Supabase

Zonder geldige `SUPABASE_URL` + sleutel gebruikt de backend `data_store.json`
(staat in `.gitignore`). Alles werkt dan lokaal, maar op Vercel is dat bestand
vluchtig: elke cold start begint opnieuw. Gebruik daar Supabase.

## Omgevingsvariabelen

| Variabele | Wat |
|---|---|
| `R33_API_KEY` | verplicht voor de chat (route33) |
| `SUPABASE_URL` | bv. `https://xxxx.supabase.co` |
| `SUPABASE_SERVER_SLEUTEL` (of `SUPABASE_KEY`) | service_role-sleutel |
| `SITE_USER` + `SITE_WACHTWOORD` | optioneel: hele site achter HTTP Basic Auth |
| `ADMIN_USER` + `ADMIN_WACHTWOORD` | moderator-login (of `MODERATIE_CODE`) |
| `SECRET_KEY` | optioneel: stabiele HMAC voor de moderatorcookie (anders afgeleid van de inloggegevens) |
| `DAG_BUDGET` | euro's aan AI per dag; leeg = 1,00, `0` = geen limiet |
| `MAX_VRAGEN_PER_BROWSER` | vragen per browser; standaard 5, `0` = onbeperkt |
| `MAX_VRAAG_TEKENS` | standaard 500 |
| `MAX_VRAGEN_PER_MINUUT` | voor de hele site samen; standaard 30 |
| `SEED_DEMO` | `0` = geen voorbeelddata plaatsen |
| `ALLOW_RESET` | `1` = "Voorbeelddata terugzetten" ook op Supabase toelaten |
| `DATA_BESTAND` / `UPLOAD_MAP` | optioneel: ander pad voor de lokale fallback |

Op Vercel zet je dezelfde variabelen bij **Environment Variables**. Verplicht
daar: `R33_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVER_SLEUTEL` (anders ben je
data kwijt bij elke herstart). De AI-limieten staan in het geheugen en in
`verbruik.json` in `/tmp`; na een cold start tellen de per-browser-tellers
opnieuw (de daglimiet in `verbruik.json` geldt op Vercel dus niet betrouwbaar).

Vercel laat per serverless request max. ~4,5 MB door. Daarom is de PDF-limiet
in de UI 4 MB en uploadt de frontend één PDF per request.

## Mijn pakket

Na de onboarding wordt het persoonlijke pakket bewaard (`slaMijnPakketOp`). De chat toont het in de zijbalk (`haalMijnPakketVolledig`), en `/onboarding` toont bovenaan "Jouw pakket" met een knop om het verder aan te passen. De status (privé, in controle, afgewezen + reden) is daar ook te zien.

## Moderatie afschermen

Zet `ADMIN_USER` + `ADMIN_WACHTWOORD` (of `MODERATIE_CODE`) in `.env` of bij de
Environment Variables op Vercel. Dan vraagt `/moderatie` eerst om in te loggen;
de cookie is 8 uur geldig en bevat een HMAC-token, niet het wachtwoord. De
moderatie-API (`/api/data/wachtrij`, goedkeuren, afwijzen, samenvoegen) weigert
zonder die cookie. Zonder ingestelde gegevens is moderatie open, handig lokaal.

De hele site achter HTTP Basic Auth zetten kan met `SITE_USER` + `SITE_WACHTWOORD`.

## Mijn pakket

Na de onboarding wordt het persoonlijke pakket op de server bewaard
(`slaMijnPakketOp` → `persoonlijke_pakketten`). De chat toont het in de zijbalk
(`haalMijnPakketVolledig`), en `/onboarding` toont bovenaan "Jouw pakket" met
een knop om het verder aan te passen. De status (privé, in controle, afgewezen
+ reden) is daar ook te zien.

## Bekende shortcuts

- Eén gedeelde moderatorlogin in plaats van echte accounts. Vervangen door de rol `moderator` zodra Supabase Auth er is.
- Het persoonlijke pakket hangt aan een browsercookie (`studiebuddy_id`), niet aan een account. Een andere browser of toestel ziet het niet.
- De vraaggeschiedenis voor de AI-context staat in het geheugen van de server; na een herstart begint ze leeg (de teller per browser staat in `verbruik.json`, op Vercel in `/tmp`).
- De koppeling tussen een PDF en een vak gebeurt op bestandsnaam (bv. `databanken.pdf` → "Databanken").
- `voegPakketSamen` doet twee updates (doelpakket + status van de bron); er is geen transactie. Bij een netwerkfout halverwege kan de bron op `in_controle` blijven staan.
