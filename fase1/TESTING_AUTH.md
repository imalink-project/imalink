# Deaktivering av Autentisering under Testing

## Oversikt

Backend-en har implementert JWT-basert autentisering som krever at alle API-kall inkluderer et gyldig access token. For å gjøre testing enklere, kan autentiseringen deaktiveres midlertidig.

## Hvordan aktivere test-modus (uten autentisering)

### Metode 1: Miljøvariabel

Legg til følgende i `.env`-filen din:

```bash
DISABLE_AUTH=True
```

### Metode 2: Sett miljøvariabel i terminalen (midlertidig)

```bash
# Linux/Mac/WSL
export DISABLE_AUTH=True
uv run src/main.py

# Windows CMD
set DISABLE_AUTH=True
uv run src/main.py

# Windows PowerShell
$env:DISABLE_AUTH="True"
uv run src/main.py
```

## Hva skjer når autentisering er deaktivert?

Når `DISABLE_AUTH=True`:

1. **Ingen token kreves**: API-endepunkter som normalt krever autentisering kan nå kalles uten `Authorization`-header
2. **Automatisk test-bruker**: Systemet oppretter og bruker automatisk en test-bruker:
   - Username: `test_user`
   - Email: `test@example.com`
   - Full Name: `Test User`
3. **Alle endepunkter tilgjengelig**: Du får full tilgang til alle API-endepunkter uten å måtte logge inn først

## Eksempel på bruk

### Med autentisering aktivert (normalt)

```bash
# Først: Logg inn for å få token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword"}'

# Deretter: Bruk token i alle requests
curl http://localhost:8000/api/v1/photos \
  -H "Authorization: Bearer <your_token_here>"
```

### Med autentisering deaktivert (test-modus)

```bash
# Direkte tilgang uten token
curl http://localhost:8000/api/v1/photos
```

## Testing i kode

Når du kjører tester, kan du sette miljøvariabelen i test-oppsettet:

```python
import os
os.environ["DISABLE_AUTH"] = "True"

# Dine tester her - ingen autentisering kreves
```

## Sikkerhet og advarsler

⚠️ **VIKTIG SIKKERHETSVARSEL**:

- **ALDRI** aktiver `DISABLE_AUTH` i produksjon
- **ALDRI** commit en `.env`-fil med `DISABLE_AUTH=True` til git
- Denne funksjonen er **KUN** for lokal utvikling og testing
- Husk å slå av `DISABLE_AUTH` når du er ferdig med testing

## Vanlige problemer

### "Not authenticated" selv med DISABLE_AUTH=True

1. Sjekk at miljøvariabelen er satt:
   ```bash
   echo $DISABLE_AUTH  # Linux/Mac/WSL
   echo %DISABLE_AUTH%  # Windows CMD
   ```

2. Restart serveren etter å ha satt miljøvariabelen

3. Sjekk at `.env`-filen blir lastet (må være i root-mappen)

### Test-bruker opprettes ikke

Test-brukeren opprettes automatisk første gang et autentisert endepunkt kalles med `DISABLE_AUTH=True`. Hvis det er problemer, sjekk databasen eller loggene.

## Tilbake til normal modus

For å aktivere autentisering igjen:

1. Fjern eller sett `DISABLE_AUTH=False` i `.env`
2. Restart serveren
3. Bruk normale login/token-prosedyrer

## Implementasjonsdetaljer

Funksjonen er implementert i:
- `src/core/config.py` - Konfigurasjonsflagg
- `src/api/dependencies.py` - Modifisert `get_current_active_user` dependency

Når `DISABLE_AUTH=True`, returnerer `get_current_active_user()` alltid test-brukeren uten å sjekke for authentication token.
