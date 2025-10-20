# Innledning
Kjernen i Imalink er måten vi forholder oss til bilder på. Når et bilde er tatt blir det lagret som en bildefil, som regel i jpeg. Av og til lagres det i raw-format. Ofte lagres begge deler. Filene som kommer ut fra kameraet kan sammenlignes med negativer fra film. Hvert bilde er en filmrute. Selve negativet lagres for alltid og er utgangspunktet for alle bilder som vises for publikum.

Når bilder hentes fra kamera til datamaskin kopieres originalfilene direkte og brukes uendret for visning og deling. Det gir problemer som at bildene forblir store når de deles på mail. Vi mister også sporingen tilbake til hvem som har tatt bildet, og eventuelle notater fotografen selv har tatt. 

# Importstrategi
Imalink tar grep og tvinger fotografen til å være konsekvent ved tømming av minnekort. Det som skjer går i flere trinn:

1. Imalink finner alle bildefiler på minnekortet, rekursivt hvis nødvendig.
2. For hver bildefil blir exif-data hentet ut. Store og unødvendige datafelt blir fjernet. Resten gjøres om til et json-format.
3. Det blir generert en hotpreview, 150x150 pixler. Den blir rotert riktig i henhold til exif_rotation. Fra hotpreview blir det generert en phash. Den regnes som unik og universell nok til å brukes i url-er. Paret hotpreview - hash fungeres som en synlig identifikasjon. Dersom du har hotpreviewen kan du genere hashen og finne igjen bilde. Hotpreview er derfor den mest sentrale delen av et bilde. Det er mulig at hotpreview bør få et mer spesifikt navn og ikke forveksles med en miniatyr generert på andre måter.
5. Det opprettes et Image-objekt i databasen. Her brukes noen regler som tar vare på muligheten for doble bildeformater. Dersom en finner ett bilde lages hotpreview fra det. Dersom det finnes flere bilder med samme navn og forskjellig type brukes samme hotpreview på begge bildene. På den måten kan du søke opp begge originalene ved hjelp av en hotpreview. Hotpreview og strippet exif-data lagres i databasen.
6. Nedskalerte versjoner av hvert bilde lagres på disk i en bilde-pool. Det gir raskest mulig tilgang på bildemateriale til forskjellig bruk.
7. Etter at et bilde har blitt importert blir originalene flyttet til et eget lagringsområde som senere kan være offline. Det brukes samme katalogstruktur som på mediet det importeres fra. Det gjøres en sjekk etterpå for å sikre at bildet virkelig er blitt kopiert. Da kan mediet slettes og brukes til andre ting. Det er vanlig å gjøre når en laster ned filer fra minnekort. Dersom man skulle miste databasen har en fortsatt tilgang på originalkopiene. De er lagret som vanlige filer og kan gjenfinnes uten bruk av Imalink.

# Database
Databasen inneholder egentlig bare strukturen, ikke selve bildene. Ideen er at du kan hente ut et bilde i ønsket størrelse ved hjelp av hotpreview eller hash. Selve originalen behøves ikke til vanlig bruk. Bare hvis du vil gjøre bildebehandling på det. Da ber Imalink deg om å sette inn mediet med originalene på, og vipps, har du det.

I tillegg til disse grunnfunksjonene kan databasen brukes til alle typer kategorisering for å lette tilgangen. Databasen kan skalere til millioner av bilder, så søkemuligheter er nødvendige. Slike funksjoner kan legges inn bit for bit. Søk på tid og sted er allerede mulig gjennom verdier som ligger i exif. Du kan også hente inn bilder fra en gitt import-session.

# Videre muligheter
Selve databasen skal være så enkel og entydig som mulig. Den er allerede brukbar til mye. Det som mangler er å arbeide med samlinger, f.eks album. Det bør bygges opp parallelt med bildedatabasen, gjerne i et separat databasesystem. Ting som kan lages er

* Gallerier
* Album
* Artikler
* Bildebøker
* Lysbildeserier

# Oppsummering
Vi har opprettet et universelt system for tilgang på bilder fra store bildearkiver. Bildearkivet bruker en visuell url i form av et miniatyrbilde. Det at url er universell kan lokale bildesamlinger gjøres universelle for tilgang for hvem som helst, eller for dem bildene er gjort tilgjengelige for.

