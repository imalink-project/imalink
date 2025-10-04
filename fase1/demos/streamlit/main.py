"""
ImaLink Demo Hub - Streamlit Homepage
===================================

Hovedside for alle ImaLink Streamlit-demoer med navigasjon til forskjellige funksjoner.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    # Page configuration
    st.set_page_config(
        page_title="ImaLink Demo Hub",
        page_icon="🖼️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("🖼️ ImaLink Demo Hub")
    st.markdown("---")
    
    # Introduction
    st.markdown("""
    Velkommen til ImaLink demo-senteret! Her kan du utforske alle funksjonene i ImaLink systemet 
    gjennom interaktive demoer.
    """)
    
    # Demo categories
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Import & Archive")
        st.markdown("""
        **Import Sessions Demo**
        - Test bildeimport fra lokale mapper
        - Arkivering med intelligent mappestruktur  
        - Real-time progress tracking
        - Metadata ekstraksjjon og lagring
        """)
        
        if st.button("🚀 Åpne Import Demo", key="import_demo", use_container_width=True):
            st.info("ℹ️ Åpne 'Import Sessions' fra sidebar eller kjør: `streamlit run demos/streamlit/pages/01_Import_Sessions.py`")
    
    with col2:
        st.subheader("🔍 Browse & Search") 
        st.markdown("""
        **Image Gallery Demo**
        - Bla gjennom importerte bilder
        - Søk og filtrer etter metadata
        - Vis EXIF-informasjon
        - Author management
        """)
        
        if st.button("🖼️ Åpne Gallery Demo", key="gallery_demo", use_container_width=True):
            st.info("ℹ️ Åpne 'Image Gallery' fra sidebar eller kjør: `streamlit run demos/streamlit/pages/02_Image_Gallery.py`")
    
    # Additional demos row
    st.markdown("### 🔧 Tekniske Demoer")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("""
        **API Testing**
        - Test alle API-endepunkter
        - Se request/response data  
        - Valider system funksjonalitet
        """)
        
        if st.button("🔗 API Tester", key="api_demo", use_container_width=True):
            st.info("ℹ️ Åpne 'API Testing' fra sidebar")
    
    with col4:
        st.markdown("""
        **System Statistics**  
        - Database statistikker
        - Import historikk
        - System helse og performance
        """)
        
        if st.button("📊 System Stats", key="stats_demo", use_container_width=True):
            st.info("ℹ️ Åpne 'System Statistics' fra sidebar")
    
    # Quick start guide
    st.markdown("---")
    st.subheader("🚀 Kom i gang")
    
    with st.expander("📋 Instruksjoner"):
        st.markdown("""
        ### Starte demo-systemet:
        
        1. **Fra prosjektroot:**
           ```bash
           cd demos/streamlit
           streamlit run main.py
           ```
        
        2. **Navigasjon:**
           - Bruk sidebar til venstre for å bytte mellom demoer
           - Hver demo har sin egen side og funksjonalitet
           - Alle demoer kjører mot samme API (localhost:8000)
        
        3. **Forutsetninger:**
           - ImaLink API server må kjøre på localhost:8000
           - Start med: `uvicorn src.main:app --host 0.0.0.0 --port 8000`
        
        ### Demo-funksjoner:
        - **Import Sessions**: Test bildeimport og arkivering
        - **Image Gallery**: Bla og søk i importerte bilder  
        - **API Testing**: Test alle endepunkter direkte
        - **System Statistics**: Overvåk system ytelse
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
        ImaLink Fase 1 - Demo Hub | Built with Streamlit ❤️
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()