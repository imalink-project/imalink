# Slik deaktiverer du autentisering under testing

## Rask guide

### Steg 1: Opprett .env fil

Kopier `.env.example` til `.env`:

```bash
cp .env.example .env
```

### Steg 2: Aktiver test-modus

Åpne `.env` og endre:

```bash
DISABLE_AUTH=True
```

### Steg 3: Start serveren

```bash
# Fra fase1/ mappen
export DISABLE_AUTH=True
uv run src/main.py
```

### Steg 4: Test at det virker

```bash
# Test med curl (ingen token nødvendig)
curl http://localhost:8000/api/v1/photos

# Eller kjør test-skriptet
uv run python python_demos/test_disable_auth.py
```

## Viktig!

- ✅ Bruk kun i utvikling/testing
- ❌ ALDRI i produksjon
- 🔒 Sett tilbake til `DISABLE_AUTH=False` når du er ferdig

Se `TESTING_AUTH.md` for fullstendig dokumentasjon.
