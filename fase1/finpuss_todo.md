# Finpuss videre på Fase 1

Noe bør fortsatt gjøres før jeg avslutter fase 1:

1. Legge til en tabell jeg vil kalle "Selection". En selection er et lagret søk som genererer et sett bilder. Selections kan fungere som "album" i andre systemer bortsett fra at bildenes rekkefølge er automatisk. De må være søkbare.
2. Lage en strategi for "SourceBackup". En sourcebackup lagrer fysisk originalbildene til en vanlig katalog på en disk. Den har en unik id. Mange SourceBackup-filer kan lagres på samme disk og kunne finnes ved søk etter id'en. En sourcebackup er nært knyttet til en import og bør kanskje knyttes sammen. En import kan når som helst oppdatere sin SourceBackup ved å knytte den til et lagringsmedium koblet til maskinen. Sourcebackup skal i utgangspunktet inneholde all brukerstyrt informasjon om bildene som finnes i databasen, men i lesbare tekstfiler som f.eks json.
3. Legge til nedskalerte filer i en eller flere størrelser. Disse skal alltid være online og tilgjengelige ved databasesøk. Størrelser kan være f.eks small, medium, large med large som f.eks 1200 pixler. Ikke alle størrelser behøver å lages med en gang for alle bilder. I starten kan alle bilder få small og medium automatisk. Type filstruktur og strategi for oppdatering må tenkes gjennom.
4. Rammeverk for å sette et bilde inn en markdown-fil. Det bør være nok å spesifisere bildets id og noen hint for å vise bildet i passe størrelse. Bildebrowser bør kunne operere med ulike modi for ulike størrelser.
5. Selection i den thumbnail-baserte bildebrowseren. Kan brukes for å gjøre operasjoner på mange bilder i slengen, f.eks sette stjerner. Undo-funksjon?
6. Gruppering av bilder i stacks. Egen tabell "Stack" med felter som kan behandle burst, panorama eller motivserie. Bilder som har stack-referanse vises som bunke i bildebrowseren. Stack må kunne ekspanderes og kollapses manuelt. Kun ett utvalgt bilde vises i bildebrowseren når stack er kollapset.
7. En tabell for markdown-dokumenter. Disse har litt til felles med Selection og vises på egen side. Forskjellen er at bilder er lenket til tekst og kan vises i rekkefølge bestemt av brukeren. Et fotoalbum vil typisk være et slikt dokument. I senere versjoner bør det lages en GUI-komponent for Wysiwyg-aktig editering.
8. Strategi for brukeraksess til programmet. Det må kreves innlogging. Aksess til bilder må kunne styres. Det må velges noe som er enkelt å implementere. 

Når disse oppgavene er på plass begynner programmet å bli brukbart og kan gjøres alment tilgjengelig.

# Tanker om fase 2
Fase 2 starter der fase 1 fryses. Mye kan gjøres på GUI-siden. Programmet kan gjøres mer modulært med mulighet for individuelle utvidelser. 
- Samspill med ekstern bildebehandling.
- Mekanisme for dynamisk bildevisning
- Avansert visningsmodus, f.eks langsom innzooming mot et punkt i bildet.
- Hjelp fra AI for å kategorisere hva, evt hvem som er på bildene. Viktig å markere at AI aldri skal brukes automatisk under visning eller søk. Kun av brukere med skriverettigheter.

