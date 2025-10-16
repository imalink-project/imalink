# ImaLink Desktop Demo

En enkel Flet desktop app for å demonstrere CRUD-operasjoner på Author-tabellen.

## Setup

1. Installer avhengigheter:
```bash
cd /home/kjell/git_prosjekt/imalink/fase1/desktop_demo
pip install -r requirements.txt
```

2. Kjør appen:
```bash
python author_crud_demo.py
```

## Features

- ✅ **Create**: Legg til nye forfattere
- ✅ **Read**: Vis liste over alle forfattere
- ✅ **Update**: Rediger eksisterende forfattere
- ✅ **Delete**: Slett forfattere (med bekreftelse)

## UI Komponenter

- Form for input (navn, email, bio)
- Liste over forfattere med edit/delete knapper
- Status meldinger for operasjoner
- Bekreftelsesdialog for sletting

## Teknologi

- **Flet**: Cross-platform desktop UI framework
- **SQLAlchemy**: Database ORM
- **Backend Integration**: Bruker eksisterende models og database connection

## Arkitektur

Dette er en prototype for å teste desktop client-konseptet hvor:
- Python håndterer tung prosessering (file scanning, EXIF, etc.)
- Native UI med file pickers
- Direkte database tilgang
- Kan kjøre offline

## Neste Steg

Når denne fungerer bra, kan vi utvide til:
- File picker for import
- Progress bars for lange operasjoner
- Hotpreview visning
- EXIF data extraction
- Preview generation
