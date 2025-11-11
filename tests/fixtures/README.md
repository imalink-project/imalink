# Test Photo Fixtures

Self-contained test photo "eggs" for ImaLink testing.

## Konsept

**PhotoEgg** er et "egg" (self-contained fixture) som inneholder all data som trengs for å lage en Photo-instans + primary ImageFile, uten å kreve faktiske bildefiler på disk.

### Hvorfor "Egg"?

- 🥚 **Self-contained**: Alt du trenger er i én pakke
- 🥚 **Portable**: Kan serialiseres til JSON/YAML
- 🥚 **Versionable**: Kan sjekkes inn i Git
- 🥚 **Reusable**: Samme fixtures brukes på tvers av tester

## Struktur

### PhotoEgg

Inneholder:
- `hothash` - Content-based hash identifier
- `hotpreview_base64` - Base64-encoded 150x150px JPEG thumbnail
- `primary_file` - ImageFileEgg med filnavn
- Metadata: `width`, `height`, `taken_at`, `gps_*`, `rating`, `visibility`
- `exif_dict` - Optional EXIF data
- `description` - Human-readable beskrivelse (kun for dokumentasjon)
- `tags` - Foreslåtte tags (kun for dokumentasjon)

**Ikke inkludert:**
- ❌ Coldpreview (ikke nødvendig for de fleste tester)
- ❌ Faktiske bildefiler på disk
- ❌ ImageFile storage paths

### ImageFileEgg

Minimal ImageFile-data:
- `filename` - Primary image filename (required)
- `file_format` - Optional (auto-detected fra filename)
- `file_size` - Optional (default 1MB)

### PhotoEggCollection

Organisert samling av PhotoEggs:
- `name` - Collection navn
- `description` - Hva samlingen inneholder
- `version` - For compatibility tracking
- `photos` - Dict[str, PhotoEgg] - Named fixtures

## Bruk

### 1. Enkel bruk med create_test_photo_egg()

```python
from src.schemas.test_fixtures import create_test_photo_egg

# Lag minimal test photo
photo_egg = create_test_photo_egg(
    hothash="abc123...",
    filename="test.jpg",
    taken_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    rating=4,
    visibility="public"
)

# Create Photo instance
photo = Photo(**photo_egg.to_photo_kwargs(test_user.id))
```

### 2. Bruk forhåndsdefinerte collections

```python
from tests.fixtures.photo_eggs import timeline_photos

# Create alle photos i collection
created = timeline_photos.create_all(db_session, test_user.id)

# Eller hent enkeltfoto
beach_egg = timeline_photos.get("summer_2024_beach")
photo = Photo(**beach_egg.to_photo_kwargs(test_user.id))
```

### 3. Last fra JSON-fil

```python
from src.schemas.test_fixtures import PhotoEggCollection

# Load collection from JSON
with open('tests/fixtures/timeline_photos.json') as f:
    collection = PhotoEggCollection.model_validate_json(f.read())

# Create all photos
created = collection.create_all(db_session, test_user.id)
```

### 4. Lag egne collections

```python
from src.schemas.test_fixtures import PhotoEggCollection, create_test_photo_egg

my_photos = PhotoEggCollection(
    name="my_test_photos",
    description="My custom test photos",
    version="1.0",
    photos={
        "photo1": create_test_photo_egg(
            hothash="hash1...",
            filename="photo1.jpg",
            rating=5
        ),
        "photo2": create_test_photo_egg(
            hothash="hash2...",
            filename="photo2.jpg",
            rating=3
        )
    }
)

# Serialize to JSON for version control
with open('my_photos.json', 'w') as f:
    f.write(my_photos.model_dump_json(indent=2))
```

## Tilgjengelige Collections

### timeline_photos
Photos spanning different years/months for timeline API testing:
- `summer_2024_beach` - Summer 2024, rating 5, public
- `winter_2024_mountains` - Winter 2024, rating 4, authenticated
- `autumn_2023_forest` - Autumn 2023, rating 3, private
- `spring_2023_flowers` - Spring 2023, rating 4, public

### visibility_photos
Photos with different visibility levels:
- `private_family` - Private visibility
- `authenticated_event` - Authenticated visibility
- `public_landscape` - Public visibility

### rating_photos
Photos with different ratings for preview selection:
- `five_star` - Rating 5
- `four_star` - Rating 4
- `three_star` - Rating 3
- `no_rating` - Rating 0

### gps_photos
Photos with/without GPS coordinates:
- `oslo_location` - Oslo coordinates
- `bergen_location` - Bergen coordinates
- `no_gps` - No GPS data

## Eksempel Test

```python
def test_timeline_year_aggregation(test_db_session, test_user):
    """Test year aggregation with timeline photos."""
    from tests.fixtures.photo_eggs import timeline_photos
    
    # Create all timeline photos
    created = timeline_photos.create_all(test_db_session, test_user.id)
    
    # Test timeline API
    response = client.get("/api/v1/timeline?granularity=year")
    data = response.json()
    
    # Should have 2 years (2024 and 2023)
    assert len(data["data"]) == 2
    assert {b["year"] for b in data["data"]} == {2024, 2023}
    
    # 2024 should have 2 photos
    year_2024 = next(b for b in data["data"] if b["year"] == 2024)
    assert year_2024["count"] == 2
```

## Fordeler

✅ **Ingen eksterne filer**: Alt i Python-kode eller JSON  
✅ **Versjonskontroll**: Fixtures sjekkes inn i Git  
✅ **Konsistent**: Samme testdata på alle maskiner  
✅ **Dokumentert**: description og tags forklarer hva fixtures er  
✅ **Fleksibel**: Lett å lage nye combinations  
✅ **Type-safe**: Pydantic validering  

## Struktur på disk

```
tests/
  fixtures/
    __init__.py
    photo_eggs.py           # Predefined Python collections
    timeline_photos.json    # Timeline test photos
    visibility_photos.json  # Visibility test photos
    README.md              # This file
```

## Fremtidig utvidelse

Kan enkelt utvides med:
- 📸 PhotoStack fixtures (JPEG+RAW pairs)
- 📝 PhotoText document fixtures  
- 👤 Author fixtures
- 🏷️ Tag fixtures
- 📦 Complete "scenario" fixtures (user + photos + documents)
