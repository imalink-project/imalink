# 🖼️ ImaLink Demo Hub

Profesjonell demo-suite for ImaLink Fase 1 med multi-demo Streamlit interface.

## 📁 Struktur

```
demos/
├── streamlit/                    # Streamlit demo system
│   ├── main.py                  # 🏠 Hovedside med demo-oversikt
│   └── pages/                   # 📄 Individual demo pages
│       ├── 01_📥_Import_Sessions.py    # Import og arkivering demo
│       ├── 02_🖼️_Image_Gallery.py      # Bildegalleri og søk
│       ├── 03_🔗_API_Testing.py        # API endpoint testing  
│       └── 04_📊_System_Statistics.py  # System overvåking
└── README.md                    # Denne filen
```

## 🚀 Kom i gang

### 1. Start ImaLink API
Først må ImaLink API serveren kjøre:

```bash
cd /path/to/imalink/fase1
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 2. Start Demo Hub
Start demo-systemet fra prosjektroot:

```bash
cd demos/streamlit
streamlit run main.py
```

### 3. Navigér til demoer
- **Hovedside**: Oversikt over alle tilgjengelige demoer
- **Sidebar**: Navigasjon mellom individuelle demoer
- **Auto-routing**: Direktelenker mellom relaterte demoer

## 📋 Demo Oversikt

### 🏠 **Main Hub** (`main.py`)
- **Formål**: Sentral navigasjonshub for alle demoer
- **Funksjoner**: 
  - Oversikt over tilgjengelige demoer
  - Direktelenker til spesifikke funksjoner
  - Instruksjoner og dokumentasjon
  - System status sjekk

### 📥 **Import Sessions Demo** 
**Fil**: `pages/01_📥_Import_Sessions.py`

**Funksjoner**:
- ✅ Start nye import-sesjoner med konfigurasjon
- ✅ Real-time progress tracking og status
- ✅ Archive konfigurasjon med base path og naming
- ✅ File copying aktivering/deaktivering
- ✅ Error handling og debugging
- ✅ API endpoint explorer for import-relaterte calls

**Bruk**:
1. Sett source directory (f.eks. `C:/temp/PHOTOS_SRC_TEST_MICRO`)
2. Konfigurér arkiv settings (base path, subfolder)
3. Start import og følg progress i real-time
4. Verifiser at filer kopieres til arkiv structure

### 🖼️ **Image Gallery Demo**
**Fil**: `pages/02_🖼️_Image_Gallery.py`

**Funksjoner**:
- ✅ Bla gjennom importerte bilder i grid-layout
- ✅ Vis metadata (dimensions, file size, GPS, EXIF)
- ✅ Filter og søk funksjoner
- ✅ Author-basert filtrering  
- ✅ Detaljert image informasjon med JSON export
- ✅ System statistikk oversikt

**Bruk**:
1. Juster visningsinnstillinger i sidebar
2. Utforsk bilder i grid-format
3. Ekspander metadata for detaljert informasjon
4. Bruk statistikk tab for system oversikt

### 🔗 **API Testing Demo**
**Fil**: `pages/03_🔗_API_Testing.py`

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
- `/api/v1/images/*` - Image operations  
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