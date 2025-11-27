# Her er min oversikt over ImaLink

Denne oversikten skal bare endes av meg. AI-agenter skal bare kunne lese, ikke endre noe her.

## Kjerneideer

Tenke stort, implementere lite. Det som implementeres må kunne tilpasses nye områder.

Kjernen i Imalink er fotoet. Det er et motiv laget av en fortatter, kreator eller fotograf. Imalink skal lagre meta-informasjon om fotoet eller motivet. Begrepet "foto" har derfor en videre betydning enn bare bilder. Imalink kan etterhvert utvides til å gjelde andre typer kildemateriale. Databasemodellen Photo kan da tilpasses til disse typene materiale. Eksempler kan være artikler, videoer og annet.

Et Photo kan ha en eller flere kilder. For fotografier er dette typisk jpeg-filer og eventuelt raw-companions. Dette har blitt implementert fra starten av som en egen tabell ImageFile. Etterhvert kan dette ogeå brukes for andre ting, for eksempel photo-storages. Disse kan da bruke tagger og andre ting som Photo allerede har, mens ting som metadata ikke er relevante.

## Moduler i Imalink
Imalink består av 4 moduler. Hver modul har forskjellig rolle i det komplette systemet.
* **imalink** er selve databasen som holder metadataene. Den ligger på en ekstern server
* **imalink-core** inneholder kjernelogikken som definerer hvordan informasjon skal hentes fra bildefilene. Kjernelogikk og algoritmer er med denne modulen implementert på ett sted og definerer hvordan ImaLink fungerer. Den vil typisk ligge på lokal maskin for rask tilgang fra frontend. Den kan også ligge på samme server som backend for å muliggjøre opplasting av bilder over nettet. 
* **imalink-frontend** er et desktop-program med tilgang på lokalt filsystem. Det muliggjør rask opplasting av mange bilder scannet fra en katalog. imalink-frontend kommuniserer med imalink-core kjørende på en lokal server.
* **imalink-web** er en internettapplikasjon. Den fungerer som GUI for imalink backend og er tilgjengelig over internett. Skal kunne kjøres i browser eller kjøres som app på telefonen.

## Sentrale tabeller
Databasen har to sentrale tabeller som inneholder foto og tilhørende bildefiler. De andre tabellene i Imalink behandler metadata og koblinger mellom bilder.

### Tabellen Photo

Her er en manuell beskrivelse av databasetabellen med alle feltene som faktisk er lagret i databasen. Skjema for overføring av data, lagring på disk, eller annet må ha med de feltene som er relevante. Kommentarer må gis i kildefilen slik at dette dokumentet blir kompakt.

    __tablename__ = "photos"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'),nullable=False, index=True)

    hothash = Column(String(64), unique=True, nullable=False, index=True)
    hotpreview = Column(LargeBinary, nullable=False)

    exif_dict = Column(JSON, nullable=True)
    width = Column(Integer)
    height = Column(Integer)

    taken_at = Column(DateTime)
    gps_latitude = Column(Float)
    gps_longitude = Column(Float)
    
    rating = Column(Integer, default=0)
    category = Column(String(100), nullable=True, index=True)
    
    import_session_id = Column(Integer, ForeignKey('import_sessions.id'), nullable=True, index=True)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=True, index=True)
    stack_id = Column(Integer, ForeignKey('photo_stacks.id'), nullable=True, index=True)
    coldpreview_path = Column(String(255), nullable=True)
    
    timeloc_correction = Column(JSON, nullable=True)
    view_correction = Column(JSON, nullable=True)
    
    visibility = Column(String(20), nullable=False, default='private', index=True)
    
    # Relationships
    user = relationship("User", back_populates="photos")
    image_files = relationship("ImageFile", back_populates="photo", cascade="all, delete-orphan", 
                        foreign_keys="[ImageFile.photo_id]")
    author = relationship("Author", back_populates="photos")
    import_session = relationship("ImportSession", back_populates="photos")
    stack = relationship("PhotoStack", back_populates="photos", foreign_keys=[stack_id])
    tags = relationship("Tag", secondary="photo_tags", back_populates="photos")

#### Fremtidige nye felt i Photo
Per nå er alle objekter i Photo av typen "photo". Det bør utvides til flere typer. Typer kan implementeres som en enum, fordi det berører hardkodet behandling i programmet. Her er en liste over mulige typer:
* photo
* screenshot (kan muligens identifiseres ved import)
* video (identifiseres ved import)
* kollasj (et bilde generert fra andre bilder)
* story (Tekst, eventuelt med bilder i)

Alle disse typene vil benytte hotpreview og hothash.

### PhotoCreateSchema
Bilder overføres til Imalink via et json-skjema, definert i pydantic. Lages av imalink-core på grunnlag av en eller flere bildefiler som sendes fra FrontEnd.

* **fjernet, intern** id 
* user_id # Denne er kjent når bruker har logget inn
* hothash
* hotpreview
* exif_dict
* width
* height
* taken_at
* gps_latitude
* gps_longitude
* rating
* category # Typisk photo
* import_session_id # Denne er kjent når bilder overføres
* author_id # Typisk brukerens default author
* stack_id # Typisk null
* **fjernet, intern** coldpreview_path
* timeloc_correction # Typisk null
* view_correction # Typisk null
* visibility # Typisk privat

* image_file_list # One or more source image files

### Tabellen ImageFile
ImageFile er referanse til en fysisk kildefil. Typisk er dette bildefiler i jpeg eller raw. Det kan i fremtiden utvides til endre filtyper. Programstrukturen må ha fleksibilitet til å behandle alle typer dokumenter som en ImageFile.

    __tablename__ = "image_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    photo_id = Column(Integer, ForeignKey('photos.id'), nullable=True, index=True)
    imported_time = Column(DateTime, nullable=True)
    imported_info = Column(JSON, nullable=True)
    local_storage_info = Column(JSON, nullable=True)
    cloud_storage_info = Column(JSON, nullable=True)
    photo = relationship("Photo", back_populates="image_files", foreign_keys=[photo_id])

### ImageFileCreateSchema
Skjema for å sende inn ImageFile
* filename
* file_size
* **fjernet, intern** photo_id
* imported_time
* imported_info
* local_storage_info
* cloud_storage_info
