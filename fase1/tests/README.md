# ImaLink Testing

## 🧪 Minimal Unit Tests

Dette er minimalsettet av tester for ImaLink som fokuserer på det som **oftest går galt**:

### 📁 Test Files

- **`test_routes.py`** - Hovedtester som sjekker at alle ruter eksisterer
- **`run_tests.py`** - Enkel test-runner script

### 🎯 Hva testene dekker

#### API Route Tests
- ✅ `/health` - Health check endpoint
- ✅ `/api/images/` - Images API eksisterer og returnerer riktig format
- ✅ `/api/authors/` - Authors API eksisterer og returnerer riktig format  
- ✅ `/api/imports/imports` - Import API eksisterer og returnerer riktig format

#### Route Cleanup Tests  
- ✅ `/demo` routes returnerer 404 (gamle HTML demoer fjernet)
- ✅ `/demo/import` routes returnerer 404 (gamle HTML demoer fjernet)

#### Error Handling Tests
- ✅ `404` for ikke-eksisterende ruter
- ✅ `404` for ikke-eksisterende API ruter

## 🚀 Hvordan kjøre testene

### Fra tests/ katalog:
```bash
cd tests/
python run_tests.py
```

### Fra rot-nivå med pytest:
```bash
# Alle tester
python -m pytest tests/ -v

# Kun route-tester  
python -m pytest tests/test_routes.py -v

# Kort sammendrag
python -m pytest tests/ --tb=short
```

### Fra src/ katalog (utviklingsmode):
```bash
cd src/
python -m pytest ../tests/test_routes.py -v
```

## 📊 Forventet resultat

```
✅ 11/11 tests passed (100%)
⚡ Runtime: ~1 second
🎯 Focus: Route existence & status codes
```

## 🔍 Hva testene IKKE dekker

Disse testene er **minimale** og fokuserer kun på at ruter fungerer. De tester IKKE:

- ❌ Business logic 
- ❌ Database operasjoner
- ❌ File upload/processing
- ❌ Authentication/Authorization
- ❌ Performance

## 📝 Testfilosofi

> **"Test det som oftest går galt, ikke alt som kan gå galt"**

Disse testene fanger de vanligste problemene:
- **404 errors** (manglende ruter)
- **500 errors** (server crashes)  
- **Import errors** (missing dependencies)
- **Response format errors** (API contract changes)

For mer omfattende testing, utvid gradvis etter behov.
