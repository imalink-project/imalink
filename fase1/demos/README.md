# 🖼️ ImaLink Demo og Testing# 🖼️ ImaLink Demo og Testing# 🖼️ ImaLink Demo og Testing



Testing og demo-ressurser for ImaLink Fase 1.



## 📁 StrukturTesting og demo-ressurser for ImaLink Fase 1.Testing og demo-ressurser for ImaLink Fase 1.



```

demos/

└── README.md                    # Denne filen - instruksjoner for testing## 📁 Struktur## 📁 Struktur

```



**Note:** Streamlit demo ble fjernet pga kompleksitet. Bruk i stedet direkte API-testing eller CLI-verktøy.

``````

## 🚀 Testing ImaLink API

demos/demos/

### 1. Start ImaLink API

Først må ImaLink API serveren kjøre:└── README.md                    # Denne filen - instruksjoner for testing└── README.md                    # Denne filen - instruksjoner for testing



```bash``````

cd /home/kjell/git_prosjekt/imalink/fase1/src

uv run python main.py

```

**Note:** Streamlit demo ble fjernet pga kompleksitet. Bruk i stedet direkte API-testing eller CLI-verktøy.**Note:** Streamlit demo ble fjernet pga kompleksitet. Bruk i stedet direkte API-testing eller CLI-verktøy.

### 2. Test API endpoints direkte med curl



**Test import:**

```bash## 🚀 Testing ImaLink API## 🚀 Testing ImaLink API

curl -X POST "http://localhost:8000/api/v1/import-sessions/" \

  -H "Content-Type: application/json" \

  -d '{"source_path": "/mnt/c/temp/PHOTOS_SRC_TEST_MICRO", "recursive": true, "author_id": 1}'

```### 1. Start ImaLink API### 1. Start ImaLink API



**Sjekk import status:**Først må ImaLink API serveren kjøre:Først må ImaLink API serveren kjøre:

```bash

curl -X GET "http://localhost:8000/api/v1/import_sessions/status/{import_id}"

```

```bash```bash

**List alle imports:**

```bashcd /home/kjell/git_prosjekt/imalink/fase1/srccd /home/kjell/git_prosjekt/imalink/fase1/src

curl -X GET "http://localhost:8000/api/v1/import_sessions/"

```uv run python main.pyuv run python main.py



### 3. Alternative testing verktøy``````

- **CLI tester**: `fase1/cli_tester.py`

- **API dokumentasjon**: `http://localhost:8000/docs` (Swagger UI)

- **Postman/Insomnia**: Importer OpenAPI spec fra `/docs`

### 2. Test API endpoints direkte med curl### 2. Test API endpoints direkte med curl

## 📋 Testing Oversikt



### 🔧 **CLI Tester** 

**Fil**: `../cli_tester.py`**Test import:****Test import:**



**Funksjoner**:```bash```bash

- ✅ Kommandolinje-basert testing av alle API endpoints  

- ✅ Import session testing med progress trackingcurl -X POST "http://localhost:8000/api/v1/import-sessions/" \curl -X POST "http://localhost:8000/api/v1/import-sessions/" \

- ✅ File discovery og processing verification

- ✅ Database tilstand inspeksjon  -H "Content-Type: application/json" \  -H "Content-Type: application/json" \

- ✅ Enkel og direkte - ingen kompleks UI

  -d '{"source_path": "/mnt/c/temp/PHOTOS_SRC_TEST_MICRO", "recursive": true, "author_id": 1}'  -d '{"source_path": "/mnt/c/temp/PHOTOS_SRC_TEST_MICRO", "recursive": true, "author_id": 1}'

**Bruk**:

```bash``````

cd /home/kjell/git_prosjekt/imalink/fase1

python cli_tester.py

```

**Sjekk import status:****Sjekk import status:**

### 🌐 **Swagger UI**

**URL**: `http://localhost:8000/docs````bash```bash



**Funksjoner**:curl -X GET "http://localhost:8000/api/v1/import_sessions/status/{import_id}"curl -X GET "http://localhost:8000/api/v1/import_sessions/status/{import_id}"

- ✅ Interaktiv API dokumentasjon

- ✅ Test alle endpoints direkte i browseren``````

- ✅ Se request/response schemas

- ✅ Autogenerert fra FastAPI koden



### 📡 **Direct API Testing****List alle imports:****List alle imports:**

**Bruk curl eller HTTP klient**

```bash```bash

**Viktige endpoints**:

- `POST /api/v1/import-sessions/` - Start importcurl -X GET "http://localhost:8000/api/v1/import_sessions/"curl -X GET "http://localhost:8000/api/v1/import_sessions/"

- `GET /api/v1/import_sessions/status/{id}` - Sjekk progress  

- `GET /api/v1/image-files/` - List importerte bilder``````

- `GET /api/v1/authors/` - List authors



## ✅ System Status

### 3. Alternative testing verktøy### 3. Alternative testing verktøy

ImaLink Fase 1 er nå fullt operasjonell på WSL/Linux med:

- ✅ Python 3.13.7 + uv package management- **CLI tester**: `fase1/cli_tester.py`- **CLI tester**: `fase1/cli_tester.py`

- ✅ FastAPI server med alle endpoints

- ✅ RAW file format støtte (detection og kategorisering)  - **API dokumentasjon**: `http://localhost:8000/docs` (Swagger UI)- **API dokumentasjon**: `http://localhost:8000/docs` (Swagger UI)

- ✅ Cross-platform fil tilgang (`/mnt/c/temp/`)

- ✅ SQLite database med proper initialization- **Postman/Insomnia**: Importer OpenAPI spec fra `/docs`- **Postman/Insomnia**: Importer OpenAPI spec fra `/docs`

- ✅ Duplikat deteksjon og error handling



**Ready for continued development!** 🚀
## 📋 Testing Oversikt## 📋 Testing Oversikt



### 🔧 **CLI Tester** ### 🏠 **Main Hub** (`main.py`)

**Fil**: `../cli_tester.py`- **Formål**: Sentral navigasjonshub for alle demoer

- **Funksjoner**: 

**Funksjoner**:  - Oversikt over tilgjengelige demoer

- ✅ Kommandolinje-basert testing av alle API endpoints    - Direktelenker til spesifikke funksjoner

- ✅ Import session testing med progress tracking  - Instruksjoner og dokumentasjon

- ✅ File discovery og processing verification  - System status sjekk

- ✅ Database tilstand inspeksjon

- ✅ Enkel og direkte - ingen kompleks UI### 📥 **Import Sessions Demo** 

**Fil**: `pages/01_📥_Import_Sessions.py`

**Bruk**:

```bash**Funksjoner**:

cd /home/kjell/git_prosjekt/imalink/fase1- ✅ Start nye import-sesjoner med konfigurasjon

python cli_tester.py- ✅ Real-time progress tracking og status

```- ✅ Archive konfigurasjon med base path og naming

- ✅ File copying aktivering/deaktivering

### 🌐 **Swagger UI**- ✅ Error handling og debugging

**URL**: `http://localhost:8000/docs`- ✅ API endpoint explorer for import-relaterte calls



**Funksjoner**:**Bruk**:

- ✅ Interaktiv API dokumentasjon1. Sett source directory (f.eks. `C:/temp/PHOTOS_SRC_TEST_MICRO`)

- ✅ Test alle endpoints direkte i browseren2. Konfigurér arkiv settings (base path, subfolder)

- ✅ Se request/response schemas3. Start import og følg progress i real-time

- ✅ Autogenerert fra FastAPI koden4. Verifiser at filer kopieres til arkiv structure



### 📡 **Direct API Testing**### 🖼️ **Image Gallery Demo**

**Bruk curl eller HTTP klient****Fil**: `pages/02_🖼️_Image_Gallery.py`



**Viktige endpoints**:**Funksjoner**:

- `POST /api/v1/import-sessions/` - Start import- ✅ Bla gjennom importerte bilder i grid-layout

- `GET /api/v1/import_sessions/status/{id}` - Sjekk progress  - ✅ Vis metadata (dimensions, file size, GPS, EXIF)

- `GET /api/v1/image-files/` - List importerte bilder- ✅ Filter og søk funksjoner

- `GET /api/v1/authors/` - List authors- ✅ Author-basert filtrering  

- ✅ Detaljert image informasjon med JSON export

## ✅ System Status- ✅ System statistikk oversikt



ImaLink Fase 1 er nå fullt operasjonell på WSL/Linux med:**Bruk**:

- ✅ Python 3.13.7 + uv package management1. Juster visningsinnstillinger i sidebar

- ✅ FastAPI server med alle endpoints2. Utforsk bilder i grid-format

- ✅ RAW file format støtte (detection og kategorisering)  3. Ekspander metadata for detaljert informasjon

- ✅ Cross-platform fil tilgang (`/mnt/c/temp/`)4. Bruk statistikk tab for system oversikt

- ✅ SQLite database med proper initialization

- ✅ Duplikat deteksjon og error handling### 🔗 **API Testing Demo**

**Fil**: `pages/03_🔗_API_Testing.py`

**Ready for continued development!** 🚀
**Funksjoner**:
- ✅ Test alle API endepunkter direkte
- ✅ Redigerbare request bodies for POST/PUT
- ✅ Query parameter support  
- ✅ Complete request/response visning
- ✅ JSON formatering og syntax highlighting
- ✅ Error handling og debugging tools
- ✅ Quick action buttons for vanlige operasjoner

**Kategorier**:
- **Import Sessions**: Full import session API
- **Images**: Image management og queries
- **Authors**: Author CRUD og søk
- **Debug**: System debug endpoints

### 📊 **System Statistics Demo**
**Fil**: `pages/04_📊_System_Statistics.py`

**Funksjoner**:
- ✅ Real-time system dashboard med key metrics
- ✅ Auto-refresh funksjonalitet (30s intervals)
- ✅ API endpoint helse monitoring med response times
- ✅ Detaljert statistikk for images, authors og imports
- ✅ Recent activity tracking
- ✅ Import success rates og system performance
- ✅ Route discovery og API mapping

**Dashboards**:
- **Overview**: Key metrics og recent activity
- **Detailed Stats**: Comprehensive system statistics  
- **System Health**: API connectivity og performance monitoring

## 🔧 Konfigurasjon

### Environment Variables
Alle demoer bruker samme konfigurasjon:

```python
API_BASE = "http://localhost:8000/api/v1"
```

### Streamlit Settings
Standard Streamlit konfigurasjon med:
- **Wide layout**: Maksimal skjermbredde
- **Expanded sidebar**: Navigasjon alltid synlig
- **Custom icons**: Emoji-baserte page icons
- **Auto-refresh**: Valgfri real-time updates

### API Dependencies
Demoene forutsetter at følgende API endepunkter er tilgjengelig:
- `/api/v1/import_sessions/*` - Import management
- `/api/v1/image-files/*` - Image operations  
- `/api/v1/authors/*` - Author management
- `/debug/routes` - System introspection
- `/health` - Health check

## 🎯 Bruksmønstre

### 1. **Development Testing**
- Start med Import Demo for å teste ny import funksjonalitet
- Bruk API Testing for å verifisere endpoint behavior
- Overvåk System Statistics under utvikling

### 2. **User Acceptance Testing**  
- Image Gallery for end-user experience testing
- Import Sessions for workflow validation
- System Statistics for performance verification

### 3. **System Monitoring**
- System Statistics med auto-refresh for live monitoring
- API Testing for endpoint health checks
- Import Sessions for operation tracking

### 4. **Demo og Presentasjon**
- Main Hub som startpunkt for demoer
- Image Gallery for visual demonstration
- System Statistics for impressive metrics display

## 🔄 Utvidelse og Tilpasning

### Legge til nye demoer:
1. **Opprett ny fil** i `pages/` directory
2. **Navngivning**: `05_🎯_New_Demo.py` (sequential numbering)
3. **Følg template** fra eksisterende demoer
4. **Legg til i main.py** for hovedside-navigasjon

### Demo Template:
```python
"""
New Demo - ImaLink Streamlit Demo
================================

Beskrivelse av demo-funksjonalitet.
"""

import streamlit as st
import requests
import sys
from pathlib import Path

# Project imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

API_BASE = "http://localhost:8000/api/v1"

def main():
    st.header("🎯 New Demo")
    st.markdown("Demo description and functionality")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Settings")
    api_base = st.sidebar.text_input("API Base URL", value=API_BASE)
    
    # Main content
    # Implement demo functionality here
    
if __name__ == "__main__":
    main()
```

### Styleguide:
- **Icons**: Bruk emoji for visual identification
- **Layout**: Consistent column og tab struktur
- **Error handling**: Graceful degradation ved API issues
- **Help text**: Informative placeholders og tooltips
- **Navigation**: Cross-demo linking hvor relevant

## 📈 Performance Considerations

### Caching Strategy
- API responses caches for bedre performance
- Session state brukes for å bevare data mellom interactions
- Auto-refresh implementert effektivt med minimal overhead

### Resource Management
- Timeout på alle API requests (5-30s depending on operation)
- Error boundaries for robust user experience  
- Graceful degradation når API er utilgjengelig

### User Experience
- Loading spinners for lang-kjørende operasjoner
- Progress bars for import tracking
- Real-time updates uten full page refresh
- Responsive layout for forskjellige skjermstørrelser

---

**ImaLink Demo Hub gir en komplett testing og demonstrasjon suite for alle aspekter av ImaLink systemet!** 🎉