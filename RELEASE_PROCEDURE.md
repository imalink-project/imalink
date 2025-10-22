# ImaLink Standard Release Procedure

Dette dokumentet definerer standard prosedyre for alle ImaLink releases.

## 📦 Semantic Versioning

ImaLink følger [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH (e.g., 1.2.3)
```

- **MAJOR** (1.x.x): Breaking changes - inkompatible API-endringer
- **MINOR** (x.1.x): Ny funksjonalitet - backward compatible
- **PATCH** (x.x.1): Bug fixes - backward compatible

### Eksempler
- `1.0.0` → `1.0.1`: Bug fix i photo tagging
- `1.0.0` → `1.1.0`: Ny feature (e.g., collections)
- `1.0.0` → `2.0.0`: Breaking change (e.g., ny auth system)

---

## 🔄 Release Workflow

### Steg 1: Forberedelse

```bash
# 1. Sjekk ut main branch
git checkout main
git pull origin main

# 2. Opprett release branch
git checkout -b release/v1.2.0

# 3. Oppdater versjonsnummer
# Rediger: pyproject.toml
[project]
version = "1.2.0"

# 4. Oppdater CHANGELOG.md
## [1.2.0] - 2025-11-15

### Added
- Feature X
- Feature Y

### Changed
- Updated behavior Z

### Fixed
- Bug #123
```

### Steg 2: Testing & Validation

```bash
# 1. Kjør alle tester
pytest tests/ -v

# 2. Kjør sikkerhetsskanning
pip-audit

# 3. Test med fresh database
cd fase1
rm /mnt/c/temp/00imalink_data/imalink.db  # eller ditt path
python -c "from src.database.connection import init_database; init_database()"

# 4. Start server og test manuelt
cd src
python main.py
# Test alle nye features i browser/Postman

# 5. Verifiser dokumentasjon
# Sjekk at README.md, API_REFERENCE.md er oppdatert
```

### Steg 3: Finalize Release

```bash
# 1. Commit alle endringer
git add -A
git commit -m "Release v1.2.0

- Feature X implemented
- Bug #123 fixed
- Updated documentation
"

# 2. Merge til main
git checkout main
git merge release/v1.2.0

# 3. Tag release
git tag -a v1.2.0 -m "Version 1.2.0

New features:
- Feature X: Description
- Feature Y: Description

Bug fixes:
- #123: Description

Breaking changes:
- None
"

# 4. Push til GitHub
git push origin main
git push origin v1.2.0

# 5. Slett release branch
git branch -d release/v1.2.0
```

### Steg 4: GitHub Release

1. Gå til GitHub repository
2. Klikk "Releases" → "Create a new release"
3. Velg tag: `v1.2.0`
4. Release title: `ImaLink v1.2.0`
5. Beskrivelse (kopier fra CHANGELOG.md):

```markdown
## 🎉 What's New

### Added
- Feature X: Description with details
- Feature Y: Description with details

### Changed
- Updated behavior Z to improve performance

### Fixed
- Bug #123: Description of the fix

## 📦 Installation

```bash
git clone https://github.com/kjelkols/imalink.git
cd imalink
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 🔗 Full Changelog
See [CHANGELOG.md](CHANGELOG.md) for complete history.
```

6. Attach assets (hvis nødvendig): Docker images, binaries, etc.
7. Publish release

### Steg 5: Post-Release

```bash
# 1. Opprett development branch for neste versjon
git checkout -b develop

# 2. Oppdater versjonsnummer til dev
# Rediger: pyproject.toml
[project]
version = "1.3.0-dev"

# 3. Oppdater CHANGELOG.md
## [Unreleased] - Development

### Added
- WIP: Feature Z

# 4. Commit og push
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 1.3.0-dev"
git push origin develop
```

---

## 🐛 Hotfix Procedure

For kritiske bugs i produksjon:

```bash
# 1. Branch fra tagged release
git checkout v1.2.0
git checkout -b hotfix/v1.2.1

# 2. Fix bug
# ... kode-endringer ...

# 3. Oppdater version til 1.2.1
# pyproject.toml, CHANGELOG.md

# 4. Test grundig
pytest tests/

# 5. Merge til main
git checkout main
git merge hotfix/v1.2.1

# 6. Tag hotfix
git tag -a v1.2.1 -m "Hotfix v1.2.1: Critical bug fix"

# 7. Push
git push origin main
git push origin v1.2.1

# 8. Merge til develop også
git checkout develop
git merge hotfix/v1.2.1
git push origin develop

# 9. Slett hotfix branch
git branch -d hotfix/v1.2.1
```

---

## 📝 CHANGELOG Template

Hver release skal dokumenteres i `CHANGELOG.md`:

```markdown
## [1.2.0] - 2025-11-15

### Added
- New photo collections feature
- Bulk photo operations API
- Export to ZIP functionality

### Changed
- Improved tag autocomplete performance (3x faster)
- Updated dependencies (FastAPI 0.115.0)

### Deprecated
- Old `/image-files/` endpoint (use `/photos/new-photo` instead)

### Removed
- Legacy import session format (pre-1.0)

### Fixed
- #123: Tag deletion cascade error
- #124: GPS coordinate parsing for negative values
- #125: Memory leak in preview generation

### Security
- Updated Pillow to 11.3.1 (CVE-2024-XXXX)
```

---

## 🔒 Security Releases

For sikkerhetsfiks:

1. **IKKE** kommit detaljer om vulnerability før patching
2. Lag hotfix som beskrevet over
3. Publiser security advisory på GitHub
4. Notify brukere via preferred channels
5. Update CHANGELOG med `### Security` section

---

## ✅ Pre-Release Checklist

Før hver release, verifiser:

- [ ] Alle tester kjører (`pytest tests/`)
- [ ] Ingen sikkerhetssårbarheter (`pip-audit`)
- [ ] Dokumentasjon oppdatert
- [ ] CHANGELOG.md oppdatert
- [ ] Version bumped i `pyproject.toml`
- [ ] Breaking changes dokumentert
- [ ] Migration scripts (hvis nødvendig)
- [ ] Fresh database test
- [ ] Manual API testing

---

## 🎯 Release Schedule

Anbefalt:

- **Major releases**: 1-2 ganger per år
- **Minor releases**: Månedlig eller ved behov
- **Patch releases**: Ved behov (bugs, security)

---

## 📞 Rollback Procedure

Hvis en release feiler i produksjon:

```bash
# 1. Identifiser siste fungerende versjon
git tag  # List all tags

# 2. Checkout siste fungerende tag
git checkout v1.1.0

# 3. Redeploy
# ... deployment steps ...

# 4. Kommuniser til brukere
# GitHub issue, email, etc.

# 5. Fix bug og release ny patch
git checkout main
git checkout -b hotfix/v1.2.1
# ... fix ...
```

---

*Følg denne prosedyren for konsistente og pålitelige releases!*
