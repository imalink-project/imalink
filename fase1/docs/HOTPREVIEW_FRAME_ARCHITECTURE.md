# ImaLink Hotpreview Ramme-Arkitektur

## Problemstilling

**Utfordring**: Hvordan kan vi ha både stabil hashing og fleksibel visuell branding av hotpreview-bilder?

**Konflikt**: 
- Hash må være stabil (samme foto = samme hash)
- Visuell branding må kunne endres uten å påvirke eksisterende data

## Løsning: Ramme-basert Arkitektur

### Konsept

```
┌─────────────────────────────────────────┐
│ ImaLink Ramme (variabel branding)       │
│  ┌─────────────────────────────────┐    │
│  │                                 │    │  
│  │   Rent Hotpreview-bilde         │    │ ← Hash genereres herfra
│  │   (300x300, EXIF-rotert)       │    │
│  │   STABIL INNHOLD                │    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                  [IL]   │ ← Logo i rammeområdet
└─────────────────────────────────────────┘
```

### Arkitektoniske Lag

#### 1. **Kjernebildet** (Hashbart innhold)
- **Størrelse**: 300x300 piksler (eller mindre med aspect ratio)
- **Orientering**: EXIF-rotasjon anvendt
- **Format**: RGB JPEG, kvalitet 85
- **Innhold**: Rent thumbnail uten manipulering
- **Stabilitet**: Dette bildet endres aldri for samme kildefoto

#### 2. **Rammelaget** (Fleksibel branding)
- **Størrelse**: Større canvas (f.eks. 350x350)
- **Bakgrunn**: ImaLink merkevarefarger
- **Ramme**: Rød/gul border rundt kjernebildet
- **Logo**: ImaLink logo i rammeområdet (ikke på bildet)
- **Fleksibilitet**: Kan endres uten å påvirke hash

## Implementasjonsstrategi

### Dataflyt

```python
# 1. Generer rent kernebilde
clean_image = generate_clean_hotpreview(source_file)

# 2. Generer hash fra rent innhold  
hothash = generate_hash(clean_image)

# 3. Legg rent bilde inn i merkevareramme
branded_preview = add_imalink_frame(clean_image, brand_config)

# 4. Lagre både hash og branded preview
photo.hothash = hothash
photo.hotpreview = branded_preview
```

### Metoder

#### `_generate_clean_hotpreview(file_path)`
- Lager rent thumbnail fra originalfil
- Anvender EXIF-rotasjon
- Ingen visuell manipulering
- Returnerer bytes av rent JPEG

#### `_generate_content_hash(file_path)`
- Kaller `_generate_clean_hotpreview()`
- Genererer MD5/SHA fra rene bildedata
- Returnerer stabil hash-string

#### `_add_imalink_frame(clean_image_bytes, frame_config)`
- Tar rent bilde som input
- Lager større canvas med ramme
- Plasserer rent bilde i midten
- Legger til logo i rammeområdet
- Returnerer branded hotpreview

## Fordeler

### 🎯 **Hash-stabilitet**
- Hash genereres fra rent bildeinnhold
- Samme originalfoto gir alltid samme hash
- Duplikatdeteksjon fungerer pålitelig
- Database-integritet bevares

### 🎨 **Branding-fleksibilitet**  
- Ramme og logo kan endres fritt
- A/B-testing av forskjellige stiler mulig
- Seasonal/themed branding mulig
- Rollback uten dataverlust

### 🔄 **Bakoverkompatibilitet**
- Eksisterende hashes forblir gyldige
- Gradvis migrering mulig
- Ingen breaking changes

### ⚡ **Performance**
- Rent bilde kan caches separat
- Ramme kan genereres on-the-fly i UI
- Eller pre-generert med forskjellige stiler

## Alternative Implementeringsstrategier

### Strategi 1: Lagret ramme
```python
# Lagre komplett rammet bilde i database
photo.hotpreview = branded_preview  # Med ramme
photo.hothash = hash_from_clean_content  # Fra rent innhold
```

### Strategi 2: Runtime ramme  
```python  
# Lagre bare rent bilde, legg til ramme i UI
photo.hotpreview = clean_preview  # Uten ramme
# Frontend legger til ramme ved visning
```

### Strategi 3: Hybrid
```python
# Lagre begge varianter
photo.clean_preview = clean_image  # For hashing
photo.branded_preview = framed_image  # For visning
```

## Migrasjonsplan

### Fase 1: Implementer ramme-struktur
- Oppdater `_generate_hotpreview()` til ramme-basert
- Behold eksisterende hash-generering
- Test med nye uploads

### Fase 2: Gradvis migrering
- Regenerer hotpreview for eksisterende photos
- Behold eksisterende hashes (ikke regenerer)
- Valider at visuell konsistens opprettholdes

### Fase 3: Branding-eksperimentering
- Test forskjellige ramme-stiler
- A/B-test brukerpreferanser  
- Optimaliser ramme-design

## Konklusjon

Ramme-basert arkitektur løser det fundamentale spennet mellom **stabil identitet** og **fleksibel presentasjon**. 

Ved å skille **hashbart innhold** (rent bilde) fra **visuell branding** (ramme/logo) oppnår vi:

- ✅ Teknisk stabilitet (hash-konsistens)
- ✅ Merkevare-fleksibilitet (visuell variasjon)
- ✅ Fremtidssikkerhet (kan endre branding)
- ✅ Performance-optimalisering (caching-strategier)

Dette er en **arkitektonisk elegant** løsning som gir maksimal fleksibilitet uten å kompromittere data-integritet.