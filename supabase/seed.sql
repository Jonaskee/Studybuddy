-- De 8 standaard ECTS-fiches (AP, Toegepaste Informatica, Artificiële Intelligentie, 3e bachelor, 2026-27).
-- Ze stonden eerst in context/; de chat haalt er zijn bronnen uit. Pakketten en scholen: zie ../supabase.sql.
insert into public.vakken (naam, studiepunten, semester, fiche_md)
select v.naam, v.studiepunten, v.semester, v.fiche_md from (values
  ('AI and Society', 3, 'Semester 1', $fiche$# ECTS-fiche: AI and Society

**Artesis Plantijn Hogeschool Antwerpen**  
*Departement:* Media, design en IT  
*Academiejaar:* 2026-2027  
*Opleidingscode:* 39702/3670/2627/1/15  

---

## 1. Algemene informatie

* **Opleiding:** Bachelor in de toegepaste informatica, trajectschijf 3
* **Afstudeerrichting:** Artificiële Intelligentie
* **Type opleidingsonderdeel:** Enkelvoudig opleidingsonderdeel
* **Studieomvang:** 3 studiepunten (ECTS)
* **Totale studietijd:** 78,00 uren
* **Titularis:** Haddouchi Hassan
* **Onderwijstaal:** Nederlands
* **Kalender:** Semester 1
* **Beoordeling:** Wordt gequoteerd op 20 (tot op een geheel getal)
* **Grensdatum leerkrediet:** 01.12.2026 (1ste semester)
* **Tweede examenkans:** Wel mogelijk
* **Delibereerbaarheid / tolereerbaarheid:** Dit opleidingsonderdeel komt in aanmerking voor deliberatie/tolerantie onder de voorwaarden van de opleiding waarvoor je bent ingeschreven.
* **Examencontract:** Men kan dit opleidingsonderdeel **niet** volgen binnen een:
  * Examencontract met het oog op het behalen van een creditbewijs
  * Examencontract met het oog op het behalen van een diploma

---

## 2. Volgtijdelijkheid

Op dit opleidingsonderdeel is **geen volgtijdelijkheid** van toepassing.

---

## 3. Korte omschrijving

Dit vak biedt studenten een grondig inzicht in de impact van kunstmatige intelligentie (AI) op de samenleving.  
De studenten zullen:
* Kennis opdoen over de fundamenten en de geschiedenis van AI.
* De ethische, sociale, en juridische vraagstukken verkennen die voortkomen uit AI-toepassingen.
* Leren hoe AI-technologieën verantwoord kunnen worden ontwikkeld en ingezet.

---

## 4. OLR-Leerdoelen

| Competentie | Doelomschrijving |
| :--- | :--- |
| **Analyseren** | Analyseert de impact van AI-technologieën op sociale, economische, en culturele aspecten van de samenleving. |
| **Communiceren** | Neemt actief deel aan discussies en debatten over complexe AI-gerelateerde kwesties, en ontwikkelen hun vaardigheden in het beargumenteren van verschillende standpunten. |
| **Professioneel handelen** | Evalueert kritisch de toepassingen van AI in verschillende sectoren en wegen de potentiële voordelen af tegen de risico's. |
| **Professioneel handelen** | Identificeert en beoordeelt ethische dilemma's en uitdagingen die samenhangen met de implementatie van AI, inclusief vraagstukken rondom privacy, autonomie, en bias. Studenten interpreteren wet- en regelgeving die relevant is voor AI, zoals data privacy wetten en aansprakelijkheid. |
| **Realiseren** | Past kennis toe door het analyseren van case studies en het ontwerpen van oplossingen voor hypothetische problemen rond AI-implementaties. |

---

## 5. Leerinhoud

* **Introductie:** Overzicht van AI-concepten, geschiedenis, en sleuteltechnologieën.
* **Ethiek in AI:** Bespreking van morele en ethische kwesties zoals privacy, bias en verantwoordelijkheid.
* **Harmonisatie tussen mens en AI-synergie:** Begrip van menselijke cognitie en gedrag, het belang van mensgerichte AI-ontwerpen, en inzichten uit de gedragswetenschappen over effectieve samenwerking tussen mens en AI.
* **AI en Werk:** Impact van automatisering en AI op arbeid en werkgelegenheid.
* **Juridische Aspecten:** Wetgeving en regulering rond AI, inclusief databescherming.
* **Case Studies:** Analyse van specifieke AI-implementaties in verschillende sectoren zoals o.a. gezondheidszorg, financiën en industrie.

---

## 6. Studiematerialen

* **Studiewijzer:** Verplicht
* **Online leermateriaal op Digitap:** Verplicht

---

## 7. Onderwijsorganisatie & Werkvormen

| Werkvorm | Uren |
| :--- | :--- |
| Hoor- en/of werkcolleges | 12,00 uren |
| Practicum en/of oefeningen | 24,00 uren |
| Werktijd buiten de contacturen | 42,00 uren |
| **Totale studietijd** | **78,00 uren** |

---

## 8. Toetsing & Evaluatie

### Eerste examenkans

| Moment | Evaluatievorm | Weging | Opmerkingen |
| :--- | :--- | :--- | :--- |
| Eerste examenperiode | Kennis- en inzichtstoets in de examenreeks | 40,00% | Digitaal |
| Eerste examenperiode | Vaardigheidstoets in de examenreeks | 30,00% | Digitaal |
| Eerste examenperiode | Portfolio *(niet herhaalbaar in 2e kans)* | 15,00% | Permanente evaluatie |
| Eerste examenperiode | Vaardigheidstoets permanent tijdens de lesweken *(niet herhaalbaar in 2e kans)* | 15,00% | Permanente evaluatie |

### Tweede examenkans

| Moment | Evaluatievorm | Weging | Opmerkingen |
| :--- | :--- | :--- | :--- |
| Tweede examenperiode | Kennis- en inzichtstoets in de examenreeks | 40,00% | Digitaal |
| Tweede examenperiode | Vaardigheidstoets in de examenreeks | 30,00% | Digitaal |
| Overdracht uit 1e kans | Portfolio | 15,00% | Niet herhaalbaar in 2e kans |
| Overdracht uit 1e kans | Permanente vaardigheidstoets | 15,00% | Niet herhaalbaar in 2e kans |

---

## 9. Aanvullende bepalingen

* **Inclusieve maatregel extra examentijd:**  
  De totale examentijd voor de digitale en/of schriftelijke kennis- en inzichtstoets(en) bestaat uit de voorziene tijd voor deze toets plus $1/3$ extra examentijd met een maximum van 30 minuten voor alle studenten. De extra examentijd als individuele aanpassing is hierbij dus inbegrepen.

* **Afwezigheid (deel)examen:**  
  Voor de voorwaarden voor het inhalen van een afwezigheid op een (deel)examen binnen en buiten de examenreeksen: zie het onderwijs- en examenreglement.  
  *Buiten de examenreeks geldt aanvullend nog:* Niet elke evaluatieactiviteit kan ingehaald worden wegens organisatorische of didactische redenen.$fiche$),
  ('AI for Business', 6, 'Semester 1', $fiche$# ECTS-fiche: AI for Business

**Artesis Plantijn Hogeschool Antwerpen**  
*Departement:* Media, design en IT  
*Academiejaar:* 2026-2027  
*Opleidingscode:* 39703/3670/2627/1/49  

---

## 1. Algemene informatie

* **Opleiding:** Bachelor in de toegepaste informatica, trajectschijf 3
* **Afstudeerrichting:** Artificiële Intelligentie
* **Type opleidingsonderdeel:** Enkelvoudig opleidingsonderdeel
* **Studieomvang:** 6 ECTS (studiepunten)
* **Totale studietijd:** 156,00 uren
* **Titularis:** Cop Christophe
* **Onderwijstaal:** Nederlands
* **Semester:** Semester 1
* **Beoordeling:** Geaanrekend op 20 (tot op een geheel getal)
* **Grensdatum leerkrediet:** 01.12.2026 (1ste semester)
* **Tweede examenkans:** Wel mogelijk
* **Delibereerbaarheid / tolereerbaarheid:** Dit opleidingsonderdeel komt in aanmerking voor deliberatie/tolerantie onder de voorwaarden van de opleiding waarvoor je bent ingeschreven.
* **Examencontract:** Men kan dit opleidingsonderdeel **niet** volgen binnen een:
  * Examencontract met het oog op het behalen van een creditbewijs
  * Examencontract met het oog op het behalen van een diploma

---

## 2. Volgtijdelijkheid

Op dit opleidingsonderdeel is **geen volgtijdelijkheid** van toepassing.

---

## 3. Korte omschrijving

Dit opleidingsonderdeel (olod) is gericht op het toepassen van AI-technologieën binnen verschillende toepassingsdomeinen. De studenten:

* Verkennen verschillende toepassingsgebieden van AI binnen het bedrijfsleven.
* Ontwerpen en implementeren AI-gebaseerde oplossingen voor specifieke business problemen.
* Analyseren de impact van AI-oplossingen op bedrijfsprocessen en besluitvorming.
* Beoordelen de economische en ethische implicaties van het gebruik van AI in het bedrijfsleven.

*Dit olod bouwt verder op de kennis en vaardigheden uit **ML Algorithms** en **Data Engineering**.*

---

## 4. OLR-Leerdoelen

| Competentie | Doelomschrijving |
| :--- | :--- |
| **Analyseren** | Analyseert de effectiviteit en impact van AI-technologieën op bedrijfsprocessen en operationele efficiëntie. |
| **Communiceren** | Presenteert projectresultaten en strategieën effectief aan een publiek van zowel technische als niet-technische stakeholders. |
| **Onderzoeken** | Onderzoekt AI-toepassingen in diverse zakelijke domeinen zoals marketing, financiën, en supply chain management. |
| **Ontwerpen** | - Evalueert de economische voordelen en kosten van AI-implementaties in bedrijfscontexten.<br>- Ontwerpt AI-modellen om specifieke zakelijke problemen op te lossen. |
| **Professioneel handelen** | Beoordeelt ethische overwegingen en naleven van privacywetgeving bij het gebruik van AI in zakelijke toepassingen. |
| **Realiseren** | Implementeert AI-oplossingen in projecten die real-world bedrijfsuitdagingen adresseren. |

---

## 5. Leerinhoud

De toepassingsdomeinen worden jaarlijks bekeken op basis van hun relevantie en aansluiting bij het overige AI-curriculum. Mogelijke cases zijn:

* **AI in Marketing:** Gebruik van AI voor klantensegmentatie, voorspellende analyse, en gepersonaliseerde marketing.
* **AI in Financiën:** Toepassingen zoals fraudedetectie en risicobeheer.
* **AI in Supply Chain Management:** Optimalisatie van logistiek, vraagvoorspelling, en automatisering van de supply chain.

---

## 6. Studiematerialen

* **Online leermateriaal op Digitap** *(Verplicht)*
* **Studiewijzer** *(Verplicht)*

---

## 7. Onderwijsorganisatie & Werkvormen

| Werkvorm | Uren |
| :--- | :--- |
| Hoor- en/of werkcolleges | 12,00 uren |
| Practicum en/of oefeningen | 36,00 uren |
| Werktijd buiten de contacturen | 108,00 uren |
| **Totale studietijd** | **156,00 uren** |

---

## 8. Toetsing & Evaluatie

### Overzicht evaluatieonderdelen

#### Eerste examenkans
* **Kennis- en inzichtstoets in de examenreeks** (20,00%)
  * *Moment:* Eerste examenperiode
  * *Opmerking:* Digitaal.
* **Vaardigheidstoets in de examenreeks** (40,00%)
  * *Moment:* Eerste examenperiode
  * *Opmerking:* Digitaal.
* **Vaardigheidstoets permanent tijdens de lesweken (Permanente evaluatie)** (40,00%)
  * *Moment:* Eerste examenperiode
  * *Opmerking:* **Niet herhaalbaar in de tweede examenkans** (geldt voor beide examenkansen).

#### Tweede examenkans
* **Kennis- en inzichtstoets in de examenreeks** (20,00%)
  * *Moment:* Tweede examenperiode
  * *Opmerking:* Digitaal.
* **Vaardigheidstoets in de examenreeks** (40,00%)
  * *Moment:* Tweede examenperiode
  * *Opmerking:* Digitaal.
* **Permanente evaluatie overdracht** (40,00%)
  * *Het behaalde cijfer voor de permanente evaluatie uit de eerste periode blijft behouden.*

---

### Aanvullende toetsingsbepalingen

* **Inclusieve maatregel extra examentijd:**  
  De totale examentijd voor de digitale en/of schriftelijke kennis- en inzichtstoets(en) bestaat uit de voorziene tijd voor deze toets plus 1/4 extra examentijd met een maximum van 30 minuten voor alle studenten. De extra examentijd als individuele aanpassing is hierbij dus inbegrepen.
* **Afwezigheid (deel)examen:**  
  * Zie het onderwijs- en examenreglement voor de voorwaarden m.b.t. het inhalen van een afwezigheid op een (deel)examen binnen en buiten de examenreeksen.
  * Buiten de examenreeks geldt aanvullend: *Niet elke evaluatieactiviteit kan ingehaald worden wegens organisatorische of didactische redenen.*$fiche$),
  ('Applied AI project', 9, 'Semester 1', $fiche$# ECTS-fiche: Applied AI Project

**Artesis Plantijn Hogeschool Antwerpen**  
*Departement:* Media, design en IT  
*Academiejaar:* 2026-2027  
*Opleidingscode:* 39705/3670/2627/1/20  

---

## 1. Algemene informatie

* **Opleiding:** Bachelor in de toegepaste informatica, trajectschijf 3
* **Afstudeerrichting:** Artificiële Intelligentie
* **Type opleidingsonderdeel:** Enkelvoudig opleidingsonderdeel
* **Studieomvang:** 9 studiepunten (ECTS)
* **Totale studietijd:** 234,00 uren
* **Titularis:** Casteels Wim
* **Co-titularis(sen):** Cop Christophe
* **Onderwijstaal:** Nederlands
* **Kalender:** Semester 1
* **Beoordeling:** Wordt gequoteerd op 20 (tot op een geheel getal)
* **Grensdatum leerkrediet:** 01.12.2026 (1ste semester)
* **Tweede examenkans:** **Niet mogelijk**
* **Delibereerbaarheid / tolereerbaarheid:** Voor dit opleidingsonderdeel moet je slagen (**wordt nooit gedelibereerd/getolereerd**).
* **Examencontract:** Men kan dit opleidingsonderdeel **niet** volgen binnen een:
  * Examencontract met het oog op het behalen van een creditbewijs
  * Examencontract met het oog op het behalen van een diploma

---

## 2. Volgtijdelijkheid

Om dit opleidingsonderdeel te mogen opnemen, moet voldaan zijn aan de volgende voorwaarde:

* Binnen **trajectschijf 1** al minstens **60 studiepunten** afgewerkt hebben **EN**
* Binnen **trajectschijf 2** al minstens **50 studiepunten** afgewerkt hebben **EN**
* (Geslaagd voor *Artificial intelligence project* **OF** geslaagd voor *International IT project*) **OF** geslaagd voor *International IT project_A*.

---

## 3. Korte omschrijving

In kleine teams wordt een AI-project uitgewerkt voor een eindklant volgens de projectmethodologie.

---

## 4. OLR-Leerdoelen

| Competentie | Doelomschrijving |
| :--- | :--- |
| **Analyseren** | • Analyseert een probleem vanuit het perspectief van belanghebbenden en relevante contexten.<br>• Interpreteert en verwerkt feedback van stakeholders in de oplossing. |
| **Communiceren** | • Communiceert efficiënt en effectief binnen de beroepscontext.<br>• Stelt documentatie op met correct taalgebruik, aangepast aan het doelpubliek. |
| **Optimaliseren** | • Ontwikkelt een AI-oplossing met aandacht voor herbruikbaarheid en efficiëntie.<br>• Stelt een releaseplan op.<br>• Stelt een testplan op en test de toepassing op structurele wijze. |
| **Professioneel handelen** | • Hanteert de principes van projectopvolging en gebruikt methodes, hulpmiddelen en processen om projecten te beheren.<br>• Neemt een proactieve houding aan doorheen het volledige project.<br>• Reflecteert over het geleverde werk en maakt aanbevelingen naar de toekomst.<br>• Werkt klantgericht en omgevingsbewust. |
| **Projectmatig samenwerken** | • Werkt constructief samen om collectieve resultaten te verwezenlijken. |

---

## 5. Leerinhoud

* Samenwerken in team, opdelen in taken
* Praktisch gebruik van de gekozen projectmethodologie voor de opvolging van dit alles
* Uitwerken van de verschillende deelaspecten
* Professioneel communiceren (schriftelijk en mondeling)
* Doortesten van het hele project
* Debuggen van het traject
* Opstellen van een Roadmap en gestructureerde verdere ontwikkeling
* Voorbereiding voor uitrol van het project
* Presentatie en eindverdediging naar o.a. de opdrachtgever toe
* Diepgaand documenteren van het project (o.a. ook de code)

---

## 6. Studiematerialen

* **Online leermateriaal op Digitap:** Verplicht
* **Studiewijzer:** Verplicht

---

## 7. Onderwijsorganisatie & Werkvormen

| Werkvorm | Uren |
| :--- | :--- |
| Vormen van groepsleren | 96,00 uren |
| Werktijd buiten de contacturen | 138,00 uren |
| **Totale studietijd** | **234,00 uren** |

---

## 8. Toetsing & Evaluatie

### Evaluatieoverzicht

> **Opgelet:** Er is **geen tweede examenkans** mogelijk. Evaluatie is **niet herhaalbaar**.

| Evaluatiemoment | Vorm | Weging |
| :--- | :--- | :--- |
| **Eerste examenperiode** | Projectopdracht | **100,00%** |

---

## 9. Bijzondere bepalingen & Aanwezigheid

### Verplichte aanwezigheid bij de onderwijsactiviteiten
* Voor dit opleidingsonderdeel geldt dat je **verplicht aanwezig** moet zijn bij alle onderwijsactiviteiten. De leerdoelen kunnen immers enkel tijdens de contactmomenten verworven worden door interactie met de groep en/of de lector.
* **Afwezigheidsprocedure bij overmacht/ziekte:**
  1. Melden **vóór aanvang** van de activiteit via de webmodule *'Mijn afwezigheden'* in iBaMaFlex.
  2. Wettigen door middel van een geldig attest binnen de **2 kalenderdagen** na de activiteit via iBaMaFlex (termijn verlengd tot eerstvolgende werkdag bij weekend/feestdag).
  3. Religieuze feestdagen moeten vóór 15 oktober (of binnen 14 dagen na inschrijving) gemeld zijn.
* **Sanctie bij afwezigheid:**  
  * Er wordt een **0 gegeven op de deelexamens "projectopdracht"** zodra de student een **tweede keer ongewettigd afwezig** is op semesterbasis.

### Eindverdediging & Jury
* Het eindcijfer voor de *Projectopdracht* wordt tijdens de **eindverdediging** vastgelegd door een jury van vakexperten.
* **Zonder deelname aan de eindverdediging krijgt de student een 0** voor dit examenonderdeel.

### Afwezigheid (deel)examen
* Voor voorwaarden rond het inhalen van een afwezigheid: zie het onderwijs- en examenreglement.
* *Buiten de examenreeks geldt:* Niet elke evaluatieactiviteit kan ingehaald worden wegens organisatorische of didactische redenen.$fiche$),
  ('Bachelorproef en stage', 27, 'Semester 1 of Semester 2', $fiche$# ECTS-fiche: Bachelorproef en stage

**Artesis Plantijn Hogeschool Antwerpen**  
*Departement:* Media, design en IT  
*Academiejaar:* 2026-27  
*Opleidingscode:* 37004/3658/2627/1/32  

---

## 1. Algemene informatie

* **Komt voor in:**
  * $\rightarrow$ Bachelor in de elektronica-ICT, trajectschijf 3
  * $\rightarrow$ Bachelor in de toegepaste informatica
* **In andere opleidingen:**
  * $\rightarrow$ Bachelor in de toegepaste informatica als *International bachelor thesis & internship_A*
* **Type:** Enkelvoudig opleidingsonderdeel
* **Studieomvang:** 27 studiepunten (ECTS)
* **Totale studietijd:** 702.00 uren
* **Titularis:** De Vos Jeroen
* **Onderwijstaal:** Nederlands
* **Kalender:** Semester 1 of Semester 2
* **Beoordeling:** Gequoteerd op 20 (tot op een geheel getal)
* **Grensdata leerkrediet:** 
  * 01.12.2026 (1ste semester)
  * 15.03.2027 (2de semester)
* **Tweede examenkans:** Wel mogelijk
* **Delibereerbaarheid / tolereerbaarheid:** Voor dit opleidingsonderdeel moet je slagen (**wordt nooit gedelibereerd/getolereerd**).
* **Contracten:** Men kan dit opleidingsonderdeel **niet** volgen binnen een:
  * Creditcontract
  * Examencontract (met het oog op het behalen van een creditbewijs)
  * Examencontract (met het oog op het behalen van een diploma)

---

## 2. Volgtijdelijkheid

Om dit opleidingsonderdeel te kunnen opnemen, moet voldaan zijn aan de volgende gecombineerde voorwaarden:

1. Binnen **trajectschijf 1** al minstens **60 studiepunten** afgewerkt hebben **EN**
2. Binnen **trajectschijf 2** al minstens **54 studiepunten** afgewerkt hebben **EN**
3. **Geslaagd voor minstens één van de volgende projectvakken:**
   * *Software Project_A* **OF** *Software project*
   * *Cyber security and cloud project_A* **OF** *Security project*
   * *IoT project_A* **OF** *IoT project*
   * *Business Project_A* **OF** *Business project*
   * *International IT project* **OF** *International IT project_A*
   * *Artificial intelligence project*
4. **Projectopvolging (simultaan of vooraf behaald):**
   * (Simultaan te volgen met *Applied business project* **OF** *Applied software project* **OF** *Applied cyber security and cloud project* **OF** *Applied IoT project* **OF** *Applied AI project*)  
   **OF**  
   * (Geslaagd voor *Applied business project* **OF** *Applied software project* **OF** *Applied cyber security and cloud project* **OF** *Applied IoT project* **OF** *Applied AI project*)
5. **Geslaagd voor projectanalyse:**
   * *Security project analysis* **OF** *IoT project analysis* **OF** *Business project analysis* **OF** *Software project analysis* **OF** *AI project analysis* **OF** *Project analysis_U* **OF** *Project analysis*

---

## 3. Korte omschrijving

De bachelorproef en stage is het sluitstuk van je studie. Je loopt bij een extern partnerbedrijf je stage waarbij je individueel een project uitvoert. Tijdens je stage schrijf je je bachelorproef over je stageproject. Na afloop van je stage kom je deze verdedigen voor een jury.

---

## 4. OLR-Leerdoelen

| Competentiedomein | Leerdoelen |
| :--- | :--- |
| **Adviseren** | • Adviseert over de ingebruikname en de toepassingsmogelijkheden van de IT-oplossing.<br>• Geeft op een onderbouwde manier advies over de eigen keuzes bij het ontwerp van de oplossing. |
| **Analyseren** | • Beschrijft de betrokken bedrijfsprocessen (AS-IS en TO-BE) o.a. gebruik makende van diagrammen.<br>• Beschrijft de context waarin de oplossing zal functioneren.<br>• Identificeert stakeholders en omgevingsfactoren die een invloed kunnen hebben op de uitvoering van het project.<br>• Stelt een analyse op op basis van een case uit het werkveld.<br>• Verzamelt relevante gegevens om functionele en niet-functionele vereisten op te stellen. |
| **Beheren** | • Stelt een functionele (user manual) of technische documentatie op. |
| **Communiceren** | • Communiceert professioneel met teamleden, leidinggevenden en andere belanghebbenden doorheen het project.<br>• Geeft presentaties waarbij de communicatie wordt afgestemd op de professionele context, het publiek en het doel van de communicatie.<br>• Stelt heldere, gestructureerde en volledige verslagen op over de vooruitgang van het project en de ontwikkelde systemen. |
| **Ondernemen** | • Integreert nieuwe ontwikkelingen binnen het gekozen toepassingsdomein in de oplossing.<br>• Neemt verantwoordelijkheid en initiatief binnen het project en/of team. |
| **Onderzoeken** | • Evalueert en onderzoekt mogelijke oplossingen voor een concreet probleem en maakt innovatieve, technologisch onderbouwde keuzes. |
| **Ontwerpen** | • Beschrijft de datastromen.<br>• Beschrijft de voor- en nadelen van de beschikbare technologieën en identificeert op welke manier deze technologieën voldoen aan de behoeften van de eindgebruikers.<br>• Ontwerpt een oplossing volgens de eigen gemaakte analyse en de geldende kwaliteitscriteria. |
| **Optimaliseren** | • Beschrijft testscenario's, maakt een testplan op en documenteert de testresultaten.<br>• Evalueert de goede werking van een complex systeem door geschikte testen en/of metingen uit te voeren.<br>• Interpreteert test- en meetresultaten en stelt hieruit de nodige acties en aanbevelingen voor om fouten op te lossen of de werking van systemen te optimaliseren. |
| **Professioneel handelen** | • Houdt rekening met de maatschappelijke en/of professionele context waarin hij werkt en de implicaties die zijn handelen kunnen teweegbrengen.<br>• Reflecteert over tekorten in de eigen kennis en competenties en neemt initiatieven om deze te remediëren.<br>• Stelt een correcte tijdsplanning op om de eigen taken uit te voeren binnen het kader van de globale planning van het team.<br>• Werkt efficiënt, proactief, met doorzettingsvermogen en neemt verantwoordelijkheid voor de resultaten. |
| **Projectmatig samenwerken** | • Werkt zowel zelfstandig als in een multidisciplinair team opdrachten en projecten uit op een constructieve en professionele manier. |
| **Realiseren** | • Bouwt hardware- en/of softwaresystemen met bestaande bouwstenen die voldoen aan de opgestelde vereisten.<br>• Ontwikkelt veilige oplossingen met aandacht voor gemaakte afspraken, deadlines en vereisten binnen een professionele context. |

---

## 5. Leerinhoud

* De student volgt een stage van **60 werkdagen** (4 dagen per week gedurende minstens 15 weken) bij een binnenlands of buitenlands bedrijf.
* De stage omvat een volledig project waarbij planning, analyse, (technische) implementatie, testen en documenteren aan bod komen. 
* Opvolging gebeurt op basis van een timesheet en twee stagebezoeken.
* Op basis van het type stage stelt de student de volgende documenten op:
  * Blueprint of onderzoeksvraag
  * Testplan en testdocumentatie
  * User manual of technische documentatie
  * Eindconclusie (in het geval van onderzoek)
* Halverwege de stage presenteert de student de gemaakte analyse; op het einde volgt de presentatie van het volledige traject inclusief demo voor een jury van lectoren en de stagementor.

---

## 6. Studiematerialen

* **Online leermateriaal op Digitap:** Verplicht
* **Studiewijzer:** Verplicht

---

## 7. Onderwijsorganisatie & Werkvormen

| Werkvorm | Studieomvang |
| :--- | :--- |
| Werkplekleren en/of stage | 442.00 uren |
| Werktijd buiten de contacturen | 260.00 uren |
| **Totale studietijd** | **702.00 uren** |

---

## 8. Toetsing & Beoordeling

### Eerste examenkans
* **Portfolio (Bachelorproef):** 40.00%  
  * *Moment:* Eerste examenperiode  
  * *Opmerking:* Bachelorproef.
* **Praktijkbeoordeling in een professionele context (Stage):** 60.00%  
  * *Moment:* Eerste examenperiode (permanent)  
  * *Opmerking:* Stage. Deze evaluatie komt mede tot stand door inbreng van een externe beoordelaar (de stagementor). **Niet herhaalbaar in tweede examenkans.**

### Tweede examenkans
* **Portfolio (Bachelorproef):** 40.00%  
  * *Moment:* Tweede examenperiode  
  * *Opmerking:* Bachelorproef herkanst.
* **Praktijkbeoordeling in een professionele context (Stage):** 60.00%  
  * *Overdracht:* Cijfer uit eerste examenkans wordt overgedragen (niet herneembaar).

---

## 9. Aanvullende bepalingen en reglementering

### Aanvang van de stage
* De student mag **maximaal 6 studiepunten** opnemen aan andere opleidingsonderdelen die gelijktijdig ingericht worden met Bachelorproef en stage in hetzelfde semester.
* Stage in semester 1 is enkel uitzonderlijk mogelijk mits tijdige melding (uiterlijk 31 mei van het voorafgaande academiejaar aan de stagecoördinator) en goedkeuring voor vervroegd afstuderen.
* Strikte deadlines en aanvraagprocedures via Digitap. Zonder goedgekeurde en ondertekende overeenkomst, risicoanalyse én werkpostfiche kan de stage niet starten.
* Het bijwonen van stage-infosessies is verplicht.

### Slaagvoorwaarden en de "Fail (F)" regel
* Zowel voor **Praktijkbeoordeling in een professionele context** als voor **Portfolio** moet minstens de helft worden behaald.
* **Slaag-eis per deelcomponent:**
  * Indien een student een deelcijfer $< 10/20$ behaalt op één of meerdere onderdelen van het portfolio (Presentaties, Analyse, Testen, Documentatie), leidt dit tot een **Fail ('F')** voor het deelexamen Portfolio.
  * Indien een student $< 10/20$ behaalt op soft skills of technische skills, leidt dit tot een **Fail ('F')** voor het deelexamen Praktijkbeoordeling.
  * Een 'F' op een deelexamen resulteert onherroepelijk in een **'F' (Fail) voor het volledige opleidingsonderdeel**.
* Deelname aan de eindverdediging voor een jury van vakexperten is verplicht; ontbreken leidt tot een 0 voor het examenonderdeel.
* Ethisch handelen en respect voor vertrouwelijke bedrijfsdata zijn vereist; inbreuken leiden direct tot een 'F' voor het opleidingsonderdeel.

### Opbouw deelexamens
* **Portfolio:**
  * *User driven & technology driven stages:* Blueprint, Testen, Documentatie, Presentatie.
  * *Onderzoeksstages:* Onderzoeksvraag, Testen, Documentatie, Conclusie, Presentatie.
* **Praktijkbeoordeling in professionele context:**
  * Soft skills
  * Technische skills

### Aanwezigheden, deadlines en overmacht
* **Aanwezigheid verplicht:** Permanente evaluatie gedurende de stage en bij de intervisiemomenten.
* **Afwezigheid melden en wettigen:** Uiterlijk de dag zelf melden aan mentor en AP-begeleider, én binnen 2 kalenderdagen een geldig attest/bewijs indienen via iBaMaFlex.
* Ongewettigde afwezigheid op de stage resulteert in een **0-score** voor de praktijkbeoordeling.
* Ongewettigde afwezigheid op een intervisiemoment kan niet worden ingehaald.
* **Deadlines portfolio:** Laattijdig indienen geeft een 0-score voor de betreffende opdracht (tenzij gewettigde overmacht binnen 2 kalenderdagen via iBaMaFlex).$fiche$),
  ('IT professional', 3, 'Semester 1 of Academiejaar', $fiche$# ECTS-fiche: IT Professional

**Artesis Plantijn Hogeschool Antwerpen**  
*Departement:* Media, design en IT  
*Academiejaar:* 2026-27  
*Opleidingscode:* 36999/3658/2627/1/56  

---

## 1. Algemene informatie

* **Komt voor in:**
  * $\rightarrow$ Bachelor in de elektronica-ICT, trajectschijf 3
  * $\rightarrow$ Bachelor in de toegepaste informatica
* **Type opleidingsonderdeel:** Enkelvoudig opleidingsonderdeel
* **Studieomvang:** 3 studiepunten (ECTS)
* **Totale studietijd:** 78,00 uren
* **Titularis:** Herman Bruno
* **Onderwijstaal:** Nederlands
* **Kalender:** Semester 1 of Academiejaar
* **Beoordeling:** Gequoteerd op 20 (tot op een geheel getal)
* **Mogelijke grensdata voor leerkrediet:**
  * 01.12.2026 (Academiejaar)
  * 01.12.2026 (1ste semester)
* **Tweede examenkans:** **Niet mogelijk**
* **Delibereerbaarheid / tolereerbaarheid:** Voor dit opleidingsonderdeel moet je slagen (**wordt nooit gedelibereerd/getolereerd**).
* **Examencontract:** Men kan dit opleidingsonderdeel **niet** volgen binnen een:
  * Examencontract (met het oog op het behalen van een creditbewijs)
  * Examencontract (met het oog op het behalen van een diploma)

---

## 2. Volgtijdelijkheid

* **Simultaan te volgen met:** *Bachelorproef en stage*

---

## 3. Korte omschrijving

Binnenkort kom je als startende professional op de arbeidsmarkt. Hoe zorg je ervoor dat jij eruit springt? In dit vak ontdek je je sterke eigenschappen en leer je die vertalen naar een professionele CV, motivatiebrief en sollicitatiegesprek. Je krijgt inzicht in diverse carrièremogelijkheden binnen ICT aan de hand van gastsprekers en praktijkgerichte activiteiten.

> **Let op:** Dit opleidingsonderdeel bevat een leeractiviteit in België of in het buitenland en wordt geregistreerd als **internationale mobiliteit**.

---

## 4. OLR-Leerdoelen

| Competentiedomein | Leerdoelomschrijving |
| :--- | :--- |
| **Communiceren** | • Communiceert mondeling efficiënt en effectief naar de stakeholders in een internationale omgeving en heeft aandacht voor cultuur.<br>• Gebruikt Engels als voertaal tijdens projectwerk.<br>• Rapporteert en documenteert schriftelijk efficiënt en effectief met een correct Engels taalgebruik en aangepast aan de verschillende stakeholders.<br>• Schrijft zakelijk, correct en helder, conform taalregels en wetenschappelijke conventies inzake bronvermelding.<br>• Vat informatie uit gastlessen en praktijkactiviteiten nauwkeurig en gestructureerd samen. |
| **Internationaliseren** | • Werkt constructief samen in een internationaal team om collectieve resultaten te verwezenlijken. |
| **Ondernemen** | • Brengt persoonlijke ambities, sterktes en drijfveren overtuigend over in CV, motivatiebrief en sollicitatiegesprek.<br>• Gaat ondernemend en proactief om met nieuwe kansen en technologische evoluties.<br>• Volgt vacatures binnen het werkveld op en vertaalt deze naar een gerichte en professionele sollicitatie. |
| **Onderzoeken** | • Brengt actuele technologische kennis en inzichten duidelijk over aan collega's, leidinggevenden en klanten.<br>• Reflecteert kritisch over de eigen rol binnen het ICT-domein en over maatschappelijke uitdagingen zoals digitalisering en inclusie.<br>• Verwerkt inzichten uit gastlezingen, workshops en werkveldactiviteiten tot een onderbouwde eigen visie op het ICT-beroepenveld. |
| **Professioneel handelen** | • Analyseert visies en perspectieven van verschillende betrokkenen rond duurzaamheidsuitdagingen, en plaatst de eigen rol hierin kritisch.<br>• Functioneert adequaat in een digitale werkomgeving en toont inzicht in de werking van het technische ecosysteem.<br>• Toont bewustzijn van de maatschappelijke, ethische en duurzame impact van digitale technologie. |

---

## 5. Leerinhoud

### Thema's
* Sociaal, ethische en juridische aspecten van digitale evoluties
* Gastlezing samenvatten
* Zelfreflectie
* Curriculum Vitae (CV)
* Motivatiebrief
* Sollicitatietraining
* Technische kennis op begrijpelijke wijze overdragen aan derden
* Overzicht van carrièremogelijkheden aan de hand van gastsprekers

### Verplichte activiteiten buiten contacturen
* Gastlessen (*on campus*)
* Hackathon (*off campus*)
* Hackathon sustainability (*AP*)
* AUHA-jobbeurs (*off campus*)
* Een technische beurs, conferentie of workshop (*off campus, zelf te kiezen*) – 2x
* Sollicitatietraining (*on campus*)
* Bedrijfsbezoek (*off campus*)
* Actieve deelname in een maatschappelijk project (min. 8u) rond digitalisering en inclusie (*off campus*)
* Deelname aan de Internationale week / Internationaal project  
  *(De deelnamekosten kunnen variëren; studenten dienen rekening te houden met een financiële bijdrage afhankelijk van de bestemming).*

---

## 6. Studiematerialen

* **Studiewijzer:** Verplicht
* **Online leermateriaal op Digitap:** Verplicht

---

## 7. Onderwijsorganisatie & Werkvormen

| Werkvorm | Aantal uren |
| :--- | :--- |
| Hoor- en/of werkcolleges | 24,00 uren |
| Werktijd buiten de contacturen | 54,00 uren |
| **Totale studietijd** | **78,00 uren** |

---

## 8. Toetsing & Evaluatie

### Evaluatie(s) voor beide examenkansen (niet herhaalbaar in tweede examenkans)

> **Belangrijk:** Er is **geen tweede examenkans** voor dit opleidingsonderdeel. Beide onderdelen vinden plaats in de eerste examenperiode.

| Evaluatievorm | Weging | Moment | Opmerkingen |
| :--- | :--- | :--- | :--- |
| **Portfolio** | 50,00% | Eerste examenperiode | Digitaal |
| **Reflectieopdracht eenmalig tijdens de lesweken** | 50,00% | Eerste examenperiode | Digitaal in te dienen |

---

## 9. Bijzondere bepalingen & Reglementering

### Verplichte aanwezigheid bij de onderwijsactiviteiten
* Voor dit opleidingsonderdeel geldt dat je **verplicht aanwezig moet zijn bij alle onderwijsactiviteiten**. De leerdoelen kunnen namelijk enkel tijdens de activiteiten aangeleerd en verworven worden wegens de betrokkenheid van externen.
* **Procedure bij gewettigde afwezigheid (ziekte/overmacht):**
  1. Meld je afwezigheid **vóór aanvang** via de webmodule *'Mijn afwezigheden'* in iBaMaFlex.
  2. Bezorg een geldig medisch attest of bewijsmateriaal **binnen 2 kalenderdagen** na de activiteit via *'Mijn afwezigheden'* in iBaMaFlex (termijn schuift op naar de eerstvolgende werkdag indien de 2de dag in een weekend/feestdag valt).
  3. Een religieuze feestdag geldt enkel mits tijdige melding (uiterlijk 15 oktober of binnen 14 dagen na inschrijving).
* **Sanctie:** Er wordt een **0** gegeven op het deelexamen *"Reflectieopdracht eenmalig tijdens de lesweken"* zodra de student een **tweede keer ongewettigd afwezig** is op semesterbasis.

### Afwezigheid (deel)examen & Inhaalmogelijkheden
* Zie het algemene onderwijs- en examenreglement voor de voorwaarden rond inhalen.
* Buiten de examenreeks geldt aanvullend:
  * Je kan **slechts één (deel)examen** per opleidingsonderdeel inhalen en daarvoor **éénmaal een inhaalmoment** afspreken.
  * Niet elke evaluatieactiviteit kan ingehaald worden vanwege organisatorische of didactische redenen.

### Verplichte deelname internationale week
* Wie dit opleidingsonderdeel volgt, is **verplicht om te reizen** naar een hogeschool of universiteit die een internationale week organiseert om te kunnen slagen.
* De actieve deelname is verplicht. Indien hier niet aan voldaan wordt, krijgt de student een **0 voor het gehele opleidingsonderdeel**.$fiche$),
  ('Project Start up', 6, 'Semester 1', $fiche$# ECTS-fiche: Project Start up

**Artesis Plantijn Hogeschool Antwerpen**

*Departement:* Media, design en IT

*Academiejaar:* 2026-27

*Opleidingscode:* 35774/3658/2627/1/19

## 1. Algemene informatie

* **Komt voor in:**
  * $\rightarrow$ Bachelor in de elektronica-ICT, trajectschijf 3 (Keuzeoptie: Startup)
  * $\rightarrow$ Bachelor in de toegepaste informatica (Keuzeoptie: Startup)
* **Type opleidingsonderdeel:** Enkelvoudig opleidingsonderdeel
* **Studieomvang:** 6 studiepunten (ECTS)
* **Totale studietijd:** 156,00 uren
* **Titularis:** Serneels Alexander
* **Co-titularis(sen):** Van Eyken Koen
* **Onderwijstaal:** Nederlands
* **Kalender:** Semester 1
* **Beoordeling:** Gequoteerd op 20 (tot op een geheel getal)
* **Mogelijke grensdata voor leerkrediet:** 01.12.2026 (1ste semester)
* **Tweede examenkans:** **Niet mogelijk**
* **Delibereerbaarheid / tolereerbaarheid:** Voor dit opleidingsonderdeel moet je slagen (**wordt nooit gedelibereerd/getolereerd**).
* **Examencontract:** Men kan dit opleidingsonderdeel **niet** volgen binnen een:
  * Creditcontract
  * Examencontract (met het oog op het behalen van een creditbewijs)
  * Examencontract (met het oog op het behalen van een diploma)

## 2. Volgtijdelijkheid

Om dit opleidingsonderdeel te kunnen opnemen, moet voldaan zijn aan de volgende voorwaarden:

* Binnen **trajectschijf 1** al minstens **60 studiepunten** afgewerkt hebben **EN**
* Binnen **trajectschijf 2** al minstens **50 studiepunten** afgewerkt hebben **EN**
* Geslaagd of gedelibereerd/getolereerd voor ***Ideation*** **EN**
* Geslaagd of gedelibereerd/getolereerd voor ***Business development***

## 3. Korte omschrijving

De essentie van dit opleidingsonderdeel is om met een zelf samengesteld team aan de slag te gaan met een concreet startupidee. Elk van deze startupideeën doorloopt de verschillende fases om van idee tot concreet product te gaan. In dit proces zijn een aantal 'gates' of beslissingsmomenten ingebouwd, waar telkens beslist wordt of het idee wel of niet verder mag gaan: enkel de beste ideeën gaan telkens door naar de volgende fase.

De studenten die niet verder mogen gaan met hun startupidee krijgen een opdracht aangereikt die samenhangt met een reëel probleem. Finaal implementeren de studenten een Minimum Viable Product (MVP) dat hun toelaat om feedback van eindgebruikers te krijgen op het concept. Onderweg moeten de teams ook opdrachten uitvoeren zoals het implementeren van een content marketing plan en het opstellen van een verdienmodel.

## 4. OLR-Leerdoelen

| Competentiedomein | Doelomschrijving |
| :--- | :--- |
| **Communiceren** | Communiceert en werkt op een efficiënte en effectieve manier in een multidisciplinair team waarbij de rollen helder worden verdeeld. |
| **Communiceren** | Presenteert een product dat klaar is om naar de markt te brengen. |
| **Ondernemen** | Analyseert de theorie van ondernemen met betrekking tot het starten van een onderneming of eenmanszaak waarbij technologie als hefboom wordt gebruikt om oplossingen te bieden voor bepaalde probleemstellingen. |
| **Ondernemen** | Implementeert een minimum viable product (prototype) en toetst dit aan de markt. |
| **Ondernemen** | Pitcht innovatieve ideeën/concepten aan de hand van onder andere een Business Model Canvas en Value Proposition Canvas op een bondige en overtuigende manier. |
| **Ondernemen** | Werkt innovatieve ideeën en concepten uit tot een business concept in team in de vorm van een Business Model Canvas. |
| **Ontwerpen** | Ontwerpt aan de hand van ideation, BMC, VPC, designs en prototyping, een innovatieve product of dienst met een adequate product-market fit waarbij technologie als hefboom wordt gebruikt om oplossingen te bieden voor bepaalde probleemstellingen. |
| **Ontwerpen** | Ontwikkelt op een iteratieve manier een product of dienst. |
| **Professioneel handelen** | Beheert gebruikersdata op een verantwoordelijke manier conform de geldende Europese wetgeving. |
| **Projectmatig samenwerken** | Past de principes van design thinking toe om te behoeften en problemen van de eindgebruiker in kaart te brengen. |
| **Projectmatig samenwerken** | Stelt een projectplan op. |
| **Projectmatig samenwerken** | Werkt constructief en doelgericht mee aan teamvergaderingen. |
| **Projectmatig samenwerken** | Werkt via een projectmatige methodologie (scrum of design thinking) manier. |
| **Projectmatig samenwerken** | Zorgt voor kwaliteitsborging door gestructureerd te testen. |
| **Realiseren** | Ontwikkelt minimaal een proof of concept voor een innovatief product of dienst vanuit hypotheses die werden afgetoetst met de markt. |

## 5. Leerinhoud

### Projectwerk
In dit opleidingsonderdeel ligt de focus op het realiseren van een concreet project. Elke student draagt bij aan het bedenken van een innovatief startup-concept, maar via een selectieproces met 'gateways' worden enkel de beste projecten meegenomen naar elke volgende fase. Studenten wiens idee niet worden weerhouden, krijgen een opdracht opgelegd.

De fasering van het projectwerk is als volgt:
* **Fase 1 – Idea stage:** Studenten selecteren een innovatief idee dat ze in team moeten 'pitchen' voor een jury. Hiervoor kunnen ze zich baseren op een idee dat ze voorafgaand individueel uitwerkten in het kader van het vak *Business Development*.
* **Fase 2 – Design van een Prototype:** Het idee wordt uitgewerkt in een prototype dat de essentie in zich heeft van het initiële idee.
* **Fase 3 – Development van een 'Minimum Viable Product' (MVP):** Ontwikkeling volgens de Agile Sprintmethodiek van een eerste werkende versie van het product, die getest moet worden door echte gebruikers.

### Theoretische fundering
* Introductie tot Entrepreneurship
* Duurzaam en circulair ondernemen
* Idee & innovatie – Trendspotting
* The Lean Startup & Minimum Viable Product
* Technieken & modellen voor het uitwerken & toetsen van een start-up concept: van idee tot product/market fit
* Business model, Business model patronen & Business model canvas
* Verdienmodellen & Break-even analyse
* Marktonderzoek & Content-marketing
* Stappenplan voor het opstarten van een onderneming

## 6. Studiematerialen

* **Studiewijzer:** Verplicht
* **Online leermateriaal op Digitap:** Verplicht

## 7. Onderwijsorganisatie & Werkvormen

| Werkvorm | Uren |
| :--- | :--- |
| Practicum en/of oefeningen | 36,00 uren |
| Vormen van groepsleren | 36,00 uren |
| Werktijd buiten de contacturen | 84,00 uren |
| **Totale studietijd** | **156,00 uren** |

## 8. Toetsing & Evaluatie

### Evaluaties (Eerste examenkans)

| Evaluatiemoment | Evaluatievorm | Weging | Opmerkingen |
| :--- | :--- | :--- | :--- |
| Eerste examenperiode | Projectopdracht | 100,00% | Niet herhaalbaar in de tweede examenkans |

> **Tweede examenkans:** Niet mogelijk.

## 9. Aanvullende bepalingen & Reglementering

### Verplichte aanwezigheid bij de onderwijsactiviteiten
Voor dit opleidingsonderdeel geldt dat je **verplicht aanwezig moet zijn bij alle onderwijsactiviteiten**. De leerdoelen kunnen immers enkel tijdens de contactmomenten verworven worden door de vereiste interactie met de groep en/of lector.

**Procedure bij overmacht of ziekte:**
* Meld je afwezigheid **vóór de aanvang** van de onderwijsactiviteit via de webmodule *'Mijn afwezigheden'* in iBaMaFlex.
* Wettig je afwezigheid met een geldig medisch attest of bewijsmateriaal binnen de **2 kalenderdagen** na de gemiste activiteit via iBaMaFlex (verlengd tot eerstvolgende werkdag indien de 2e dag in een weekend/feestdag valt).
* Religieuze feestdagen moeten uiterlijk op 15 oktober (of binnen 14 dagen na inschrijving) gemeld zijn via de officiële procedure.

> **Let op:** Er wordt een **0 gegeven op het deelexamen "Projectopdracht" zodra de student een tweede keer ongewettigd afwezig is** op semesterbasis.

### Eindverdediging & Deelexamens
* Het cijfer van de 'Projectopdracht' wordt tijdens de **eindverdediging** vastgelegd met een jury van vakexperten.
* Zonder deelname aan de eindverdediging krijgt de student een **0** voor dit examenonderdeel.

### Afwezigheid (deel)examen
* Voor de voorwaarden voor het inhalen van een afwezigheid op een (deel)examen binnen en buiten de examenreeksen: zie het onderwijs- en examenreglement.
* *Buiten de examenreeks geldt:* Niet elke evaluatieactiviteit kan ingehaald worden wegens organisatorische of didactische redenen.$fiche$),
  ('Sustainable IT', 3, 'Semester 1', $fiche$# ECTS-fiche: Sustainable IT

**Artesis Plantijn Hogeschool Antwerpen**  
*Departement:* Media, design en IT  
*Academiejaar:* 2026-27  
*Opleidingscode:* 40051/3658/2627/1/34  

---

## 1. Algemene informatie

* **Komt voor in:**
  * $\rightarrow$ Bachelor in de elektronica-ICT, trajectschijf 3
  * $\rightarrow$ Bachelor in de toegepaste informatica
* **Type opleidingsonderdeel:** Enkelvoudig opleidingsonderdeel
* **Studieomvang:** 3 studiepunten (ECTS)
* **Totale studietijd:** 78,00 uren
* **Titularis:** Cop Christophe *(Co-titularis(sen) zijn nog niet (allemaal) gekend)*
* **Onderwijstaal:** Nederlands
* **Kalender:** Semester 1
* **Beoordeling:** Gequoteerd op 20 (tot op een geheel getal)
* **Grensdatum leerkrediet:** 01.12.2026 (1ste semester)
* **Tweede examenkans:** Wel mogelijk
* **Delibereerbaarheid / tolereerbaarheid:** Dit opleidingsonderdeel komt in aanmerking voor deliberatie/tolerantie onder de voorwaarden van de opleiding waarvoor je bent ingeschreven.
* **Examencontracten:** Men kan dit opleidingsonderdeel **niet** volgen binnen een:
  * Creditcontract
  * Examencontract (met het oog op het behalen van een creditbewijs)
  * Examencontract (met het oog op het behalen van een diploma)

---

## 2. Volgtijdelijkheid

Op dit opleidingsonderdeel is **geen volgtijdelijkheid** van toepassing.

---

## 3. Korte omschrijving

In dit OLOD richten we ons op het bevorderen van duurzaamheid en milieubewustzijn in IT. Het vak behandelt ook de bredere milieu-impact van IT en biedt inzichten in duurzame IT-strategieën voor bedrijven. Door ethische en duurzame technologiepraktijken te integreren, ontwikkel je de vaardigheden om een positieve impact te maken in hun toekomstige carrière als IT-ontwikkelaars.

---

## 4. OLR-Leerdoelen

### Professioneel handelen
* Analyseert de impact van IT op e-waste of milieu.
* Beoordeelt de levenscyclus van IT-producten en -resultaten.
* Evalueert duurzame IT-strategieën.
* Identificeert acties om de impact van IT op e-waste of milieu te verminderen.
* Integreert duurzame overwegingen in technische beslissingen.
* Reflecteert over de inzet van IT tegenover duurzaamheid en milieu.

---

## 5. Leerinhoud

1. **Duurzaamheid:**
   * Energie
   * Grondstoffen en materialen
   * Water
2. **Hoe kunnen we IT duurzamer maken?**
3. **Hoe kan IT helpen bij duurzaamheid?**
4. **Menselijk gedrag & Change management**
5. **Sustainable AI**
6. **Wetgeving en regels**

---

## 6. Studiematerialen

* **Online leermateriaal op Digitap:** Verplicht
* **Studiewijzer:** Verplicht

---

## 7. Onderwijsorganisatie & Werkvormen

| Werkvorm | Uren |
| :--- | :--- |
| Hoor- en/of werkcolleges | 24,00 uren |
| Werktijd buiten de contacturen | 54,00 uren |
| **Totale studietijd** | **78,00 uren** |

---

## 8. Toetsing & Evaluatie

### Eerste examenkans

| Moment | Evaluatievorm | Weging |
| :--- | :--- | :--- |
| Eerste examenperiode | Kennis- en inzichtstoets in de examenreeks | 85,00% |
| Eerste examenperiode | Projectopdracht | 15,00% |

### Tweede examenkans

| Moment | Evaluatievorm | Weging |
| :--- | :--- | :--- |
| Tweede examenperiode | Kennis- en inzichtstoets in de examenreeks | 85,00% |
| Tweede examenperiode | Projectopdracht | 15,00% |

---

## 9. Aanvullende bepalingen

* **Inclusieve maatregel extra examentijd:**  
  De totale examentijd voor de digitale en/of schriftelijke kennis- en inzichtstoets(en) bestaat uit de voorziene tijd voor deze toets plus $1/3$ extra examentijd met een maximum van 30 minuten voor alle studenten. De extra examentijd als individuele aanpassing is hierbij dus inbegrepen.

* **Afwezigheid (deel)examen:**  
  Voor de voorwaarden voor het inhalen van een afwezigheid op een (deel)examen binnen en buiten de examenreeksen: zie het onderwijs- en examenreglement.  
  *Buiten de examenreeks geldt aanvullend nog het volgende:* Niet elke evaluatieactiviteit kan ingehaald worden wegens organisatorische of didactische redenen.$fiche$),
  ('Trends in AI', 3, 'Semester 1', $fiche$# ECTS-fiche: Trends in AI

**Artesis Plantijn Hogeschool Antwerpen**  
*Departement:* Media, design en IT  
*Academiejaar:* 2026-27  
*Opleidingscode:* 39704/3670/2627/1/83  

---

## 1. Algemene informatie

* **Komt voor in:** $\rightarrow$ Bachelor in de toegepaste informatica, trajectschijf 3
* **Afstudeerrichting:** Artificiële Intelligentie
* **Type opleidingsonderdeel:** Enkelvoudig opleidingsonderdeel
* **Studieomvang:** 3 studiepunten (ECTS)
* **Totale studietijd:** 78,00 uren
* **Titularis:** Haddouchi Hassan
* **Onderwijstaal:** Nederlands
* **Kalender:** Semester 1
* **Beoordeling:** Gequoteerd op 20 (tot op een geheel getal)
* **Mogelijke grensdata voor leerkrediet:** 01.12.2026 (1ste semester)
* **Tweede examenkans:** Wel mogelijk
* **Delibereerbaarheid / tolereerbaarheid:** Dit opleidingsonderdeel komt in aanmerking voor deliberatie/tolerantie onder de voorwaarden van de opleiding waarvoor je bent ingeschreven.
* **Examencontracten:** Men kan dit opleidingsonderdeel **niet** volgen binnen een:
  * Examencontract (met het oog op het behalen van een creditbewijs)
  * Examencontract (met het oog op het behalen van een diploma)

---

## 2. Volgtijdelijkheid

Op dit opleidingsonderdeel is **geen volgtijdelijkheid** van toepassing.

---

## 3. Korte omschrijving

Dit vak is ontworpen om studenten te informeren over de nieuwste ontwikkelingen en trends in artificiële intelligentie. Studenten leren o.a. de volgende vaardigheden:

* Identificeren van opkomende technologieën en methodieken binnen het veld van AI.
* Analyseren van de technologische vooruitgang en hun potentiële impact op de industrie.
* Toepassen van recente AI-inzichten op praktische en theoretische problemen.

*Dit olod bouwt verder op de kennis en vaardigheden uit **Deep Learning**.*

---

## 4. OLR-Leerdoelen

| Competentiedomein | Leerdoelomschrijving |
| :--- | :--- |
| **Analyseren** | Analyseert de impact van nieuwe technologieën op zowel de technologische sector als de maatschappij in het algemeen. |
| **Communiceren** | Presenteert AI-onderzoeksresultaten op een duidelijke en overtuigende manier, zowel schriftelijk als mondeling. |
| **Onderzoeken** | Ontwikkelt een onderzoeksproject dat een innovatieve AI-trend verkent, met aandacht voor zowel de technische details als de bredere implicaties. |
| **Ontwerpen** | Identificeert recente ontwikkelingen en innovaties binnen het domein van kunstmatige intelligentie. |
| **Ontwerpen** | Verklaart hoe nieuwe technologieën en methodieken binnen AI functioneren en potentieel de huidige praktijken kunnen transformeren. |
| **Professioneel handelen** | Beoordeelt de ethische en maatschappelijke gevolgen van de nieuwste trends in AI. |
| **Realiseren** | Past recente AI-inzichten en -technieken toe op zowel theoretische als praktische problemen binnen verschillende industrieën. |

---

## 5. Leerinhoud

De leerinhouden worden jaarlijks herbekeken op basis van:
* Populariteit en innovativiteit binnen het vakgebied.
* De mate waarin de onderwerpen nog niet in het overige IT-curriculum behandeld zijn.

---

## 6. Studiematerialen

* **Studiewijzer:** Verplicht
* **Online leermateriaal op Digitap:** Verplicht

---

## 7. Onderwijsorganisatie & Werkvormen

| Werkvorm | Uren |
| :--- | :--- |
| Hoor- en/of werkcolleges | 12,00 uren |
| Practicum en/of oefeningen | 24,00 uren |
| Werktijd buiten de contacturen | 42,00 uren |
| **Totale studietijd** | **78,00 uren** |

---

## 8. Toetsing & Evaluatie

### Eerste examenkans

| Evaluatiemoment | Evaluatievorm | Weging | Opmerkingen |
| :--- | :--- | :--- | :--- |
| Eerste examenperiode | Kennis- en inzichtstoets in de examenreeks | 45,00% | Digitaal |
| Eerste examenperiode | Vaardigheidstoets in de examenreeks | 45,00% | Digitaal |
| Eerste examenperiode | Vaardigheidstoets permanent tijdens de lesweken | 10,00% | Permanente evaluatie *(niet herhaalbaar)* |

### Tweede examenkans

| Evaluatiemoment | Evaluatievorm | Weging | Opmerkingen |
| :--- | :--- | :--- | :--- |
| Tweede examenperiode | Kennis- en inzichtstoets in de examenreeks | 45,00% | Digitaal |
| Tweede examenperiode | Vaardigheidstoets in de examenreeks | 45,00% | Digitaal |
| Overdracht uit 1e kans | Permanente vaardigheidstoets | 10,00% | Niet herhaalbaar in 2e examenkans |

---

## 9. Aanvullende bepalingen

* **Inclusieve maatregel extra examentijd:**  
  De totale examentijd voor de digitale en/of schriftelijke kennis- en inzichtstoets(en) bestaat uit de voorziene tijd voor deze toets plus $1/3$ extra examentijd met een maximum van 30 minuten voor alle studenten. De extra examentijd als individuele aanpassing is hierbij dus inbegrepen.

* **Afwezigheid (deel)examen:**  
  Voor de voorwaarden voor het inhalen van een afwezigheid op een (deel)examen binnen en buiten de examenreeksen: zie het onderwijs- en examenreglement.  
  *Buiten de examenreeks geldt aanvullend nog het volgende:* Niet elke evaluatieactiviteit kan ingehaald worden wegens organisatorische of didactische redenen.$fiche$)
) as v (naam, studiepunten, semester, fiche_md);

-- Bijnamen waarmee studenten naar een vak vragen (gebruikt door genoemde_vakken() in assistent.py).
update public.vakken v set aliassen = a.aliassen
from (values
  ('Bachelorproef en stage', '{bap,bachelorproef,stage,thesis}'::text[]),
  ('Project Start up', '{startup,start-up,"start up","project start"}'),
  ('Applied AI project', '{"applied ai","ai project","ai-project"}'),
  ('Sustainable IT', '{sustainable,duurzame it}'),
  ('IT professional', '{"it professional","it-professional"}'),
  ('AI and Society', '{"ai and society","ai & society",society}'),
  ('AI for Business', '{"ai for business","ai voor business"}'),
  ('Trends in AI', '{trends,"trends in ai"}')
) as a(naam, aliassen)
where v.naam = a.naam;
