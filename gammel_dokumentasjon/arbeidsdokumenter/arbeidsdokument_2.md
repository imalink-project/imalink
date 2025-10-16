# ImaLink - Forbedret Kravspesifikasjon (Utkast 2)

## 1. Bakgrunn og Motivasjon

### 1.1 Situasjonsanalyse
Jeg har gjennom årene akkumulert over hundre tusen bilder organisert i en filkatalog med underkataloger for år og anledninger. Mobiltelefonen har økt bildestrømmen dramatisk, og de gratis skytjenestene er fulle. Den manuelle organiseringsmetoden blir stadig mer tidkrevende og uhåndterlig.

**Nåværende arbeidsflyt:**
- Automatisk nedlasting fra kamera til OneDrive
- Manuell overføring til organisert filkatalog
- Manuell sikkerhetskopiering av filkatalogen

### 1.2 Identifiserte problemer
- **Skalerbarhet:** Manuell organisering blir uhåndterlig ved store mengder
- **Søkbarhet:** Vanskelig å finne spesifikke bilder
- **Backup:** Sikkerhetskopier foreldes teknologisk
- **Integrering:** Ingen smidig kobling mellom mobile enheter og organisert arkiv
- **Metadata:** Lite utnyttelse av tilgjengelig informasjon i bildene

### 1.3 Visjon
Imalink skal gi tilgang til alle mine bilder på PC og mobile enheter. Den skal fullt ut kunne erstatte Galleri-appen på telefonen og brukes til å vise ting til andre.

På kort sikt skal jeg kunne laste opp noen hundretalls bilder fra nyere tid og demonstrere mulighetene som ligger i visning basert på en tidslinje. 

På lang sikt skal jeg kunne laste opp alle bildene jeg finner på ulike medier. 

## 2. Overordnede Mål

### 2.1 Hovedmål
ImaLink skal være en intelligent database som bedrer tilgangen til mine bilder ved å:
- Hjelpe til med organisering og katalogisering
- Muliggjøre rask og fleksibel søking
- Bevare informasjonen som ligger i eksisterende filstruktur
- Sikre langsiktig tilgjengelighet av bildemateriell

### 2.2 Suksesskriterier
**🎯 SKAL UTDYPES:** Definer målbare kriterier som:
- Import av X bilder på Y minutter
- Søketid under Z sekunder
- Støtte for N forskjellige filformater
- Etc.

## 3. Funksjonelle Krav

### 3.1 MVP (Must-have) - Versjon 1.0
**Disse funksjonene må være på plass for at systemet skal være brukbart:**

#### 3.1.1 Bildeimport og -katalogisering
- [x] Import fra kildemapper med automatisk EXIF-uttrekk
- [x] Generering av unik identifikator (perceptuell hash) per bilde
- [x] Automatisk thumbnail-generering og lagring
- [x] Støtte for JPEG og vanlige RAW-formater (CR2, NEF, ARW)
- [x] Duplikatdeteksjon basert på perceptuell hash
- [x] **Image Pool Service** med tre størrelser (small: 400x400, medium: 800x800, large: 1200x1200)
- [x] EXIF-rotasjon baking inn i pool-bilder
- [x] Anti-upscaling beskyttelse for kvalitetsbevaring
- [x] Cascading optimization fra størst til minst

#### 3.1.2 Grunnleggende søk og visning
- [x] **IMPLEMENTERT:** Søk på dato/tidsperiode med datepicker
- [x] **IMPLEMENTERT:** Søk på filnavn med fritekst-felt
- [x] **IMPLEMENTERT:** Kronologisk visning av bilder i galleri-grid
- [x] **IMPLEMENTERT:** Detaljert metadata-visning i bildeviewer modal
- [x] **IMPLEMENTERT:** Avansert bildeviewer med pool-størrelser (small/medium/large)
- [x] **IMPLEMENTERT:** Full-size bildevisning med drag-scrolling funksjonalitet

#### 3.1.3 Avansert bildeviewer
- [x] **IMPLEMENTERT:** Modal-basert bildeviewer med tre pool-størrelser
- [x] **IMPLEMENTERT:** Detaljert filinformasjon i tre paneler
- [x] **IMPLEMENTERT:** Pool-størrelse dropdown (small/medium/large)
- [x] **IMPLEMENTERT:** Bilderotering med database-lagring
- [x] **IMPLEMENTERT:** Full-size visning med drag-scrolling
- [x] **IMPLEMENTERT:** Responsive design for mobil og desktop
- [x] **IMPLEMENTERT:** Tooltips og brukerguiding
- [x] **IMPLEMENTERT:** Nedlastingsfunksjonalitet

#### 3.1.4 Kildehåndtering
- [x] **IMPLEMENTERT:** Import API med batch-prosessering
- [ ] **🎯 UTDYP:** Registrering av kildemedier med beskrivelse
- [ ] **🎯 UTDYP:** Sporing av hvilket medium originalfiler ligger på
- [ ] **🎯 UTDYP:** Backup-struktur for kildemateriale

### 3.2 Ønskede funksjoner (Should-have) - Versjon 2.0

#### 3.2.1 Avansert søk og metadata
- [ ] **🎯 UTDYP:** Tag-system for manuell kategorisering
- [ ] **🎯 UTDYP:** Stjerne-rating (1-5)
- [ ] **🎯 UTDYP:** Fritekst-beskrivelser
- [ ] **🎯 UTDYP:** Geografisk søk og kartvisning
- [ ] **🎯 UTDYP:** Kontekst/kategori-klassifisering

#### 3.2.2 Tidslinje og kalender
- [ ] **🎯 UTDYP:** Interaktiv tidslinjevisning
- [ ] **🎯 UTDYP:** Kalenderintegrasjon
- [ ] **🎯 UTDYP:** Manuell korrigering av tidsstempel

#### 3.2.3 Organisering og gruppering
- [ ] **🎯 UTDYP:** Bildestakker (burst, panorama, serie)
- [ ] **🎯 UTDYP:** Håndtering av RAW+JPEG par
- [ ] **🎯 UTDYP:** Spesielle kategorier (dokumentasjon, etc.)

### 3.3 Fremtidige muligheter (Could-have) - Versjon 3.0+

#### 3.3.1 Avanserte funksjoner
- [ ] **🎯 UTDYP:** Persongjenkjenning og tagging
- [ ] **🎯 UTDYP:** AI-basert automatisk tagging
- [ ] **🎯 UTDYP:** Objektgjenkjenning
- [ ] **🎯 UTDYP:** Lignende bilder basert på innhold

#### 3.3.2 Integrasjoner
- [ ] **🎯 UTDYP:** Photoshop/Lightroom workflow
- [ ] **🎯 UTDYP:** PTGui panorama-integrasjon
- [ ] **🎯 UTDYP:** Export til sosiale medier
- [ ] **🎯 UTDYP:** Markdown-baserte album/presentasjoner

## 4. Tekniske Krav og Arkitektur

### 4.1 Ytelseskrav
**🎯 SKAL UTDYPES:** Spesifiser konkrete krav:
- Støtte for X antall bilder (100k? 1M?)
- Import-hastighet: Y bilder per minutt
- Søkeresponstid: under Z sekunder
- Minnebruk og diskplass-krav

### 4.2 Teknologi-stack
**IMPLEMENTERT:** Valgte konkrete teknologier:

#### Backend
- **Database:** SQLite med SQLAlchemy ORM
- **Programmeringsspråk:** Python 3.13
- **Web Framework:** FastAPI med Uvicorn
- **Bildeprosessering:** Pillow (PIL)
- **EXIF-håndtering:** PIL EXIF-moduler

#### Frontend  
- **Web:** Vanilla HTML, CSS, JavaScript
- **Styling:** Tailwind-inspirert utility CSS
- **API:** REST med FastAPI
- **Mobil:** Responsiv web-design

### 4.3 Arkitekturprinsipper
**IMPLEMENTERT:** Overordnet arkitektur:
- ✅ **Modulær oppbygning** med tydelig separasjon av concerns
- ✅ **API-basert kommunikasjon** via FastAPI REST endpoints
- ✅ **Separasjon av data og presentasjon** (backend/frontend)
- ✅ **Service-lag** for bildebehandling (Image Pool Service)
- ✅ **Database abstraksjon** med SQLAlchemy ORM
- 🔄 **Plugin-arkitektur** for utvidelser (fremtidig)

### 4.4 Nåværende Implementering (Oktober 2025)

#### Backend Struktur
```
src/
├── api/                    # FastAPI REST endpoints
│   ├── image_files.py          # Bilde-API (henting, pool, metadata)
│   ├── import_api.py      # Import-funksjonalitet
│   └── authors.py         # Forfatter/fotograf-håndtering
├── database/
│   ├── models.py          # SQLAlchemy database modeller
│   └── connection.py      # Database-tilkobling
├── services/
│   └── image_pool.py      # Image Pool Service (cascading optimization)
├── static/               # Frontend filer
│   ├── gallery.html      # Hovedgalleri
│   ├── gallery.js        # JavaScript-logikk
│   ├── styles.css        # CSS-styling
│   └── test_gallery.html # Test-side
├── config.py             # Konfigurasjon og miljøvariabler
└── main.py              # FastAPI app og server
```

#### Nøkkelkomponenter
- **Image Pool Service**: Algoritmisk filstruktur med hash-basert organisering
- **EXIF Baking**: Permanent innbaking av rotasjon i pool-bilder
- **Anti-upscaling**: Kvalitetsbeskyttelse ved reskalering
- **Responsive UI**: Fungerer på desktop og mobil
- **Drag Scrolling**: Profesjonell bildenavigering

### 4.4 Lagring og backup
**🎯 SKAL UTDYPES:** Detaljert strategi for:
- Database-backup og recovery
- Filbasert lagring av store bilder
- Migrering mellom lagringsmedia
- Versjonshåndtering av kildemateriale

## 5. Brukergrensesnitt og UX

### 5.1 Målgruppe
**🎯 SKAL UTDYPES:** 
- Primær: Meg selv (semi-profesjonell fotograf)
- Sekundær: Familiemedlemmer
- Fremtidig: Andre fotografer med lignende behov

### 5.2 Plattformstrategi
**🎯 SKAL UTDYPES:** Prioriter plattformer:
1. Desktop (Windows/Mac/Linux)
2. Web-interface
3. Mobil-app (fremtidig)

### 5.3 Brukergrensesnitt-konsepter
**IMPLEMENTERT:** Hovedvisninger:
- [x] **Hovedgalleri** med responsivt thumbnail-grid og hover-effekter
- [x] **Avansert bildeviewer** med modal-visning og pool-størrelse dropdown
- [x] **Detaljvisning** med tre informasjonspaneler (fil, teknisk, metadata)
- [x] **Søkegrensesnitt** med datepicker og fritekst-søk
- [x] **Import/kilde-administrasjon** via API-endepunkter
- [x] **Full-size bildevisning** med drag-scrolling og tooltips
- [ ] **Tidslinjevisning** (planlagt for fase 2)

## 6. Bruksscenarier (User Stories)

### 6.1 Import-scenario
**🎯 SKAL UTDYPES:** Detaljert beskrivelse av:
```
Som fotograf vil jeg kunne importere 500 bilder fra et 
bryllup på under 15 minutter, med automatisk duplikat-
deteksjon og metadata-uttrekk.
```

### 6.2 Søke-scenario  
**🎯 SKAL UTDYPES:**
```
Som bruker vil jeg kunne finne alle bilder fra "ferie i 
Italia sommer 2019" på under 30 sekunder, selv om jeg 
har 50.000 bilder i databasen.
```

### 6.3 Organisering-scenario
**🎯 SKAL UTDYPES:**
```
Som fotograf vil jeg kunne gruppere en serie på 20 
panorama-bilder til én stakk og sende dem direkte til 
PTGui for sammensetning.
```

## 7. Integrasjoner og Workflow

### 7.1 Eksisterende verktøy
**🎯 SKAL UTDYPES:** Hvordan integrere med:
- Adobe Photoshop/Lightroom
- PTGui (panorama)
- Eksisterende filkatalog
- OneDrive/Google Photos

### 7.2 Import/Export
**🎯 SKAL UTDYPES:** Støtte for:
- Import fra forskjellige kilder
- Export til forskjellige formater
- Metadata-preservering
- Batch-operasjoner

## 8. Implementeringsplan

### 8.1 Fase 1: Grunnleggende infrastruktur (MVP) ✅ FERDIG
**IMPLEMENTERT OKTOBER 2025:**
- [x] Database-design med SQLAlchemy modeller
- [x] FastAPI backend med REST API
- [x] Grunnleggende import-funksjonalitet med EXIF-uttrekk
- [x] Bildegalleri med thumbnail-grid
- [x] Image Pool Service med cascading optimization
- [x] Avansert bildeviewer modal med pool-størrelser
- [x] Full-size bildevisning med drag-scrolling
- [x] Responsive web-design

### 8.2 Fase 2: Søk og organisering ⏳ PÅGÅENDE
**DELVIS IMPLEMENTERT:**
- [x] Grunnleggende søkefunksjoner (dato, filnavn)
- [x] Metadata-visning i tre paneler (fil, teknisk, metadata)
- [ ] Tag-system for manuell kategorisering
- [ ] Tidslinjevisning
- [ ] Avanserte søkefiltre

### 8.3 Fase 3: Avanserte funksjoner 📋 PLANLAGT
**FREMTIDIGE UTVIDELSER:**
- [ ] Integrasjoner med eksterne verktøy
- [ ] AI-baserte funksjoner (persongjenkjenning, etc.)
- [ ] Mobilapp
- [ ] Cloud-synkronisering

## 9. Risiko og Begrensninger

### 9.1 Tekniske risikoer
**🎯 SKAL UTDYPES:**
- Ytelse ved store datamengder
- Kompatibilitet med RAW-formater
- Backup og recovery-strategi

### 9.2 Brukeraksept
**🎯 SKAL UTDYPES:**
- Læringskurve for nytt system
- Migrering fra eksisterende workflow
- Vedlikehold og oppdateringer

## 10. Suksessmålinger og Oppnådde Resultater

### 10.1 Tekniske Prestasjoner (Oktober 2025)
**MÅLOPPNÅELSE MVP:**
- ✅ **Import-hastighet**: Rask EXIF-uttrekk og thumbnail-generering
- ✅ **Søkerespons**: Umiddelbar søking i galleri ved bruk av database-indekser
- ✅ **Bildevisning**: Tre optimaliserte pool-størrelser for rask lasting
- ✅ **Brukeropplevelse**: Profesjonell drag-scrolling og responsiv design
- ✅ **Metadata-tilgang**: Komplett EXIF-informasjon i strukturerte paneler

### 10.2 Funksjonelle Milepæler
**FERDIGSTILT:**
- 🎯 **Grunnleggende bildeviewer** - Overgår forventningene med avansert pool-system
- 🎯 **Søkefunksjonalitet** - Dato og filnavn-søk implementert
- 🎯 **Responsive design** - Fungerer på desktop og mobil
- 🎯 **Image Pool Service** - Avansert optimalisering med anti-upscaling

### 10.3 Fremtidige KPI-er
**TIL MÅLING I FASE 2:**
- Tid spart på bildeorganisering sammenlignet med manuell metode
- Antall bilder systemet kan håndtere effektivt (målsetning: 100k+)
- Brukertilfredshet med søk og navigering
- Import-volum og batch-prosessering ytelse

---

## 📝 Status og Neste Steg (Oktober 2025)

### ✅ Ferdigstilt i MVP:
1. **Teknologi-stack** - FastAPI + SQLite + Vanilla JS ✅
2. **Grunnleggende MVP** - Fungerer som planlagt ✅  
3. **Brukergrensesnitt** - Profesjonelt responsive design ✅
4. **Image Pool Service** - Avansert optimalisering implementert ✅
5. **Bildeviewer** - Overgår opprinnelige krav ✅

### 🎯 Høyeste prioritet for Fase 2:
1. **Tag-system** - Manuell kategorisering og merking
2. **Tidslinjevisning** - Kronologisk navigering
3. **Avanserte søkefiltre** - Kamera, GPS, fotograf
4. **Batch-operasjoner** - Massebehandling av bilder
5. **Performance-testing** - Skalering til 10k+ bilder

### 🤔 Åpne arkitektur-spørsmål:
- **Skalering**: Når/hvordan migrere fra SQLite til PostgreSQL?
- **Mobil-app**: Native app vs. PWA (Progressive Web App)?
- **Cloud-integrasjon**: Lokal-først vs. hybrid cloud-løsning?
- **AI-funksjoner**: Når introdusere maskinlæring for tagging?

### 💡 Lessons Learned:
- **Image Pool Service** var en suksess - gir betydelig bedre ytelse enn on-the-fly resizing
- **Drag-scrolling** gjør stor forskjell for brukeropplevelse med store bilder
- **Responsive design** viktigere enn forventet - fungerer overraskende godt på mobil
- **API-first approach** gir god fleksibilitet for fremtidige utvidelser