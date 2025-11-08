# Photo Search Criteria - Regler og Eksempler

## 📋 Oversikt over søkekriterier

### Tilgjengelige filtre

| Felt | Type | Beskrivelse | Logikk |
|------|------|-------------|--------|
| `author_id` | int \| null | Filtrer på fotograf | Exact match |
| `import_session_id` | int \| null | Filtrer på import-sesjon | Exact match |
| `tag_ids` | int[] \| null | Filtrer på tags | OR (minst én tag) |
| `rating_min` | 0-5 \| null | Minimum rating | Inclusive (>=) |
| `rating_max` | 0-5 \| null | Maximum rating | Inclusive (<=) |
| `taken_after` | datetime \| null | Tatt etter dato | Inclusive (>=) |
| `taken_before` | datetime \| null | Tatt før dato | Inclusive (<=) |
| `has_gps` | bool \| null | GPS-data tilgjengelig | true/false/null |
| `has_raw` | bool \| null | RAW-fil tilgjengelig | true/false/null |
| `offset` | int | Pagination offset | Default: 0 |
| `limit` | int | Pagination limit | Default: 100, max: 1000 |
| `sort_by` | string | Sorteringsfelt | taken_at/created_at/rating |
| `sort_order` | string | Sorteringsrekkefølge | asc/desc |

---

## 🔍 Søkeregler

### 1. **Tomme søk returnerer alt**
```json
{
  "offset": 0,
  "limit": 100
}
```
→ Returnerer alle brukerens bilder (med pagination)

### 2. **Alle filtre er optional**
- Hvis et felt er `null` eller utelatt, ignoreres det
- Bare felter med verdier påvirker søket

### 3. **Flere filtre = AND-logikk**
```json
{
  "author_id": 1,
  "rating_min": 4,
  "has_raw": true
}
```
→ Bilder som oppfyller **ALLE** kriteriene (author=1 **OG** rating>=4 **OG** har RAW)

### 4. **tag_ids bruker OR-logikk**
```json
{
  "tag_ids": [5, 12, 23]
}
```
→ Bilder med **MINST ÉN** av taggene (id 5 **ELLER** 12 **ELLER** 23)

### 5. **Boolean-filtre (has_gps, has_raw)**
- `true`: Bare bilder **med** feature
- `false`: Bare bilder **uten** feature
- `null` (utelatt): **Alle** bilder

---

## 💡 Eksempler

### Eksempel 1: Alle 5-stjerners bilder
```json
{
  "rating_min": 5,
  "rating_max": 5,
  "sort_by": "taken_at",
  "sort_order": "desc"
}
```

### Eksempel 2: Sommerbilder fra en bestemt fotograf
```json
{
  "author_id": 1,
  "taken_after": "2024-06-01T00:00:00",
  "taken_before": "2024-08-31T23:59:59"
}
```

### Eksempel 3: RAW-filer med GPS fra en import-sesjon
```json
{
  "import_session_id": 3,
  "has_raw": true,
  "has_gps": true
}
```

### Eksempel 4: Bilder med "landscape" eller "sunset" tags
```json
{
  "tag_ids": [5, 12],
  "rating_min": 3
}
```

### Eksempel 5: Høykvalitets-bilder UTEN RAW
```json
{
  "rating_min": 4,
  "has_raw": false
}
```

### Eksempel 6: Alle bilder fra siste måned
```json
{
  "taken_after": "2024-10-01T00:00:00",
  "sort_by": "taken_at",
  "sort_order": "desc"
}
```

---

## ✅ Validering

### Automatiske valideringer:
1. **rating_max >= rating_min**
   ```json
   {"rating_min": 4, "rating_max": 2}  ❌ Error
   {"rating_min": 4, "rating_max": 5}  ✅ OK
   ```

2. **taken_before >= taken_after**
   ```json
   {"taken_after": "2024-08-01", "taken_before": "2024-07-01"}  ❌ Error
   {"taken_after": "2024-07-01", "taken_before": "2024-08-01"}  ✅ OK
   ```

3. **tag_ids ikke tom array**
   ```json
   {"tag_ids": []}      ❌ Error
   {"tag_ids": [5]}     ✅ OK
   {"tag_ids": null}    ✅ OK (ignoreres)
   ```

---

## 🎯 Avanserte kombinasjoner

### Kombiner flere filtre for presise søk:

**"Mine beste RAW-bilder fra Italia-turen":**
```json
{
  "import_session_id": 42,
  "tag_ids": [8, 15],  // "Italy", "Travel"
  "rating_min": 4,
  "has_raw": true,
  "has_gps": true,
  "sort_by": "rating",
  "sort_order": "desc"
}
```

**"Ubearbeidede bilder fra siste uke":**
```json
{
  "rating_min": 0,
  "rating_max": 0,
  "taken_after": "2024-10-25T00:00:00",
  "sort_by": "taken_at",
  "sort_order": "desc"
}
```

**"Alle portrettbilder med GPS, sortert etter dato":**
```json
{
  "tag_ids": [3],  // "Portrait"
  "has_gps": true,
  "sort_by": "taken_at",
  "sort_order": "asc"
}
```

---

## 🔄 Pagination

**Standard pagination:**
```json
{
  "offset": 0,    // Start fra første bilde
  "limit": 100    // Hent 100 bilder (default)
}
```

**Neste side:**
```json
{
  "offset": 100,  // Hopp over første 100
  "limit": 100    // Hent neste 100
}
```

**Custom page size:**
```json
{
  "offset": 0,
  "limit": 50     // Bare 50 bilder per side
}
```

---

## 📊 Response-format

Alle søk returnerer:
```json
{
  "data": [...],     // Array av PhotoResponse
  "total": 234,      // Totalt antall treff
  "offset": 0,       // Current offset
  "limit": 100       // Current limit
}
```

Dette gjør det enkelt å implementere pagination i frontend!
