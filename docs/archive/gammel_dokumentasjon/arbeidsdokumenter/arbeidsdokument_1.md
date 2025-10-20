# Imalink

## Bakgrunn

Jeg, som de fleste andre, har tatt mange bilder opp gjennom årene. Disse har jeg forsøkt å organisere i en stor katalog med filer, med underkataloger for år og anledninger. Etter som tiden går har denne katalogen eset ut til mer enn hundre tusen bilder. Dette er bilder jeg selv har tatt. I tillegg prøver jeg å ta vare på bilder som andre i familien har tatt. Dette er gjerne den eneste backupen de har.

Etter at mobiltelefonen kom har strømmen av nye bilder bare økt. I praksis blir bildene bare øyeblikksbilder for deling, og forsvinner i det store sluket. De gratis skytjenestene er fulle, og jeg har ikke tid til å organisere alt det nye som kommer inn. Ei heller har jeg noen klar kanal for overføring. Før i tiden brukte jeg å kopiere minnekort til maskinen og legge filene inn i den organiserte filkatalogen. Nå har jeg ingen entydig måte å hente bilder fra mobiltelefonen, som har blitt mitt hovedkamera.

Metoden jeg nå bruker er automatisk nedlasting fra kamera til en gratis katalog på OneDrive. Med jevne mellomrom overfører jeg bildene derfra til den organiserte filkatalogen og sletter bildene på OneDrive. OneDrive har med dette blitt det nye minnekortet.

Problemet med den organiserte filkatalogen er at det blir håpløst tidkrevende å lete etter bestemte bilder. Dette er enklere i f.eks Google Photo, men ikke ideellt. Dessuten er gratiskvoten for liten. Jeg ser behovet for et databasesystem som erstatter den manuelle organiseringen. Etter noen år har det utkrystallisert seg mange konkrete mekanismer som jeg tror kan revolusjonere måten jeg får tilgang til bildene mine. Det er viktig å gjøre overgangen fra manuell organisering til nytt system smidig og bakoverkompatibelt. Det manuelle systemet vil alltid ha sin styrke i å være enkelt å bla i for de som kommer etter meg. Ved eventuell databasekræsj vil også bildene være uberørt. Et problem som også berører alle er at sikkerhetskopier foreldes. Det som er tilgjengelig nå finnes kanskje ikke om noen år. Tape, for eksempel, er ikke allemannseie. Ikke Blue-ray heller. I dag bruker jeg eksterne harddisker. Det fine med dem er at kapasiteten øker etterhvert som bildemengden øker. Dog vet ingen hvor lenge de er i almenn bruk. Ei heller vet vi hvor lenge dataene kan ligge før de forsvinner. Aktiv overføring fra gamle til nye medier er derfor nødvendig.

## Imalink, krav og egenskaper

Imalink er en database over alle bildene. Du kan se på hvert bilde som negativer i gammeldags film. Her er all informasjonen tilgjengelig for fremkalling, bearbeiding og publisering. Ved hjelp av databasen kan mer eller nøyaktig tid og sted knyttes til bildene. Det samme er personer, bygninger og gjenstander. Digitalkameraet gjør mye av dette veldig enkelt å gjøre ved å hente ut metadata fra bildefilen. Med gamle scannede bilder må dette gjøres manuelt. Dette skal kunne gjøres i Imalink.

Flyten fra kilde til database må dokumenteres og lagres. Hver gang du overfører bilder fra f.eks en katalog med bilder må du beskrive denne kilden. Den kan være hva som helst fra vedlegg på mail til et sd-kort fra kameraet. Eller mobiltelefonens bildekatalog. Når man legger inn nytt kildemateriale bør alt lagres i en form som kan hentes frem igjen senere. Jeg ser for meg en slags backupstruktur, helst i form av kataloger med bilder og eventuelle filer med informasjon som er lagt til. En Id kan gjøre en slik kilde gjenfinnbar elektronisk eller via en label på et fysisk medium. Sist men ikke minst må kopi av en kilde kunne flyttes til nye medier.

Søkbarhet er kjernen i Imalink. Bildene må kunne karakteriseres på både de vanlige måtene og andre måter. Her er en liste over opplagte ting:

- Tag
- Stjerner
- Kontekst
- Kategori
- Fritekst
  
Søk må også kunne lagres. Disse vil brukes mye for å finne tilbake til ting en har holdt på med før. Historikk for hvert søk bør også lagres.

Tidslinje er en åpenbar egenskap. Moderne bilder har tidspunkt for når de ble tatt. En intuitiv GUI for visualisering av bilder på tidslinjen vil være fantastisk. En mekanisme for å legge inn, eventuelt korrigere tidspunkt manuelt er også nødvendig. Ikke alle klokker er synkrone i digitalkameraene. Tidssone og sommertid kan spille oss et puss.

Søk på time, dag, uke, måned og år er en interessant mulighet. Det må integreres i tidslinjevisningen. Søk på tidsintervall i kalender likeså.

Geografisk sted er nyttig. Der de ikke finnes i metadata må de kunne spesifiseres på en enkel måte. En database over verdens stedsnavn sammen med klikk på kart kan brukes til det. Da må det spesifiseres at posisjon er unøyaktig, f.eks ved radius.

Søk på område kan være interessant.

Opphavsinformasjon må kunne lagres sammen med bildet. Kanskje en tabell med navn på fotograf.

Kanskje også en tabell med navn på folk som er med på bilder. I første omgang vil jeg bare ha manuell merking av folk på bildene.

Noen kameraer gir bilde både i råformat og jpeg. Et bilde må derfor kunne lagre flere kildefiler.

Imalink må kunne brukes i tandem med software for bilderedigering. For eksempel vil program som Photoshop ha sitt eget ekosystem. Det må tenkes gjennom hvordan de kan spille sammen.

Av og til blir det tatt mange bilder av samme motiv. De bør kunne grupperes i en stakk. Bare et av bildene i stakken vises i vanlig view, men stakken må kunne ekspanderes. En stakk kan ha spesielle formål, f.eks burst eller panorama. Jeg tar av og til panorama med mange enkeltbilder og setter dem sammen med PTGui til et gigapixel panorama. Det må legges inn nok informasjon til at en jobb lett kan sendes dit. På samme måte må det ferdige panoramaet kunne spores fra databasen.

Jeg tar av og til bilder for spesielle formål. Det vanlige er situasjonsbilder, landskapsbilder osv. En type bilder er kun for dokumentasjon, for eksempel av et eller annet som foregår langs veien. Jeg kan også ta temabilder, f.eks av stuffer i en mineralsamling. Jeg vil gjerne at Imalink kan håndtere disse i databasen på linje med andre bilder, men utelukke dem fra vanlig visning.

Bildeviseren kan ha mange forskjellige visningstyper. Standard er kronologisk visning med hensyn på da bildet ble tatt.

I stedet for albumfunksjon vil jeg ha mulighet til å operere med markdown-dokumenter. Da kan jeg velge bilder i den rekkefølgen jeg vil og blande dem med tekst. Lysbildevisning kan også genereres fra et slikt dokument.

## Noen viktige spesialegenskaper

Et bilde, eller mer presist, et motiv, representeres ved en hotpreview generert på en eksakt spesifisert måte fra en kildefil. Hotpreviewen blir lagret umiddelbart i databasen og skal aldri kunne endres. Fra hotpreviewen genereres en phash som både identifiserer bildet og muliggjør søk etter lignende bilder. Hashen blir da nøkkel til motivet i databasen. Dersom samme motiv finnes med f.eks både raw og jpeg markeres begge bildene med samme hash.

Siden hashen er unik kan den brukes som nøkkel i dokumenter for visning av et bilde. Selve hotpreviewen kan også brukes som søke-element.

Når bilder lastes opp skjer det ved hjelp et kildeobjekt. Kildeobjektet skal ha informasjon om hva slags medium filene blir hentet fra, f.eks et minnekort fra et bestemt kamera eller en manuelt redigert katalogstruktur. Så mye informasjon som mulig hentes fra tilgjengelig informasjon, både i metadata i bildefilene og eventuelt i katalogstrukturen. Denne informasjonen legges inn i databasen for hver bildefil. Kildeobjektet lagres også i databasen.

Bildefiler kan være veldig store. I noen tilfeller er det mest hensiktsmessig å lagre bildefilen på eksterne medier. Et slikt medium kan i skrivende stund være en ekstern harddisk. Bildene kan lagres i en hensiktsmessig struktur generert av kildeobjektet. Denne strukturen fungerer som en slags live backup. Dit kan all ekstra informasjon om bildet legges i et lesbart format som følger bildefilen. Dette gjør det enklere for neste generasjon å hente fram bildemateriale uten å ha Imalink.

En nedskalert versjon av bildefilen lagres for online aksess i Imalink. En filbasert struktur ved siden av databasen er en grei løsning. Den nedskalerte versjonen må være stor nok til å vises på websider.


