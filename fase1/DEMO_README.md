# 🖼️ ImaLink Demo Frontend

En ren HTML-frontend som demonstrerer ImaLink API-funksjonalitet.

## 🚀 Kom i gang

1. **Start serveren:**
   ```bash
   cd c:\Users\kjell\GIT\imalink\fase1\src
   python main.py
   ```

2. **Åpne demo-frontenden:**
   - Gå til: http://localhost:8000/demo
   - Eller direkte: http://localhost:8000/static/demo.html

## 🎯 Funksjonalitet

### Import-funksjoner:
- ✅ **Start Import**: Importer bilder fra en katalog
- ✅ **Import Oversikt**: Se status på alle imports
- ✅ **Real-time oppdateringer**: Auto-refresh av import-fremgang
- ✅ **Detaljert statistikk**: Filer funnet, importert, duplikater, feil

### Bilde-visning:
- ✅ **Bildegalleri**: Vis alle importerte bilder
- ✅ **Metadata**: Filnavn, hash, størrelse, dato
- ✅ **Import-sporing**: Se hvilken import bildet kom fra

## 🔧 Tekniske detaljer

### API-endepunkter som brukes:
- `POST /api/v1/imports/` - Start ny import
- `GET /api/v1/imports/` - List alle imports
- `GET /api/v1/imports/status/{import_id}` - Import-status
- `GET /api/v1/images/` - List alle bilder

### Frontend-teknologi:
- **Ren HTML/CSS/JavaScript** - Ingen frameworks
- **Responsive design** - Fungerer på desktop og mobil
- **Real-time oppdateringer** - WebAPI fetch med intervals
- **Modern UI** - Gradient colors og smooth animations

## 📂 Test-data

Standard test-katalog: `C:/temp/PHOTOS_SRC_TEST_MICRO`

For å teste:
1. Sett inn test-katalog path
2. Klikk "Start Import"
3. Se real-time fremgang i import-oversikten
4. Bilder vises automatisk etter import

## 🎨 UI-funksjoner

- **Auto-refresh**: Oppdaterer automatisk i 30 sekunder
- **Status-indikatorer**: Fargekodet status (grønn=fullført, gul=pågår, rød=feil)
- **Progress bars**: Visuell fremgang for pågående imports
- **Responsive statistikk**: Adaptiv layout for alle skjermstørrelser
- **Error handling**: Tydelige feilmeldinger ved API-problemer

## 🔍 Debugging

Åpne Developer Tools (F12) for å se:
- API-kall og responses
- Console logging av import-statistikk
- Network-feil hvis API er nede

## 📋 Eksempel API-respons

```json
{
  "imports": [
    {
      "id": 1,
      "status": "completed", 
      "source_path": "C:/temp/PHOTOS_SRC_TEST_MICRO",
      "total_files_found": 12,
      "images_imported": 6,
      "duplicates_skipped": 6,
      "errors_count": 0
    }
  ],
  "total": 1
}
```

Dette demonstrerer perfekt hvordan ImaLink API-et fungerer! 🚀