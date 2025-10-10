# 🎨 ImaLink UI Component Library

En moderne, type-safe komponentbibliotek bygget for Svelte 5 med fullstendig TypeScript-støtte og konsistent design system.

## 📋 Innholdsfortegnelse

- [Oversikt](#oversikt)
- [Base UI Komponenter](#base-ui-komponenter)
  - [Button](#button)
  - [Card](#card)
  - [Input](#input)
  - [InputWithSuggestions](#inputwithsuggestions)
  - [SelectWithHistory](#selectwithhistory)
  - [PageHeader](#pageheader)
- [Services](#services)
  - [InputHistoryService](#inputhistoryservice)
- [Domain Komponenter](#domain-komponenter)
  - [PhotoCard](#photocard)
  - [PhotoGrid](#photogrid)
- [Installasjon og Bruk](#installasjon-og-bruk)
- [Design System](#design-system)
- [Bidrag](#bidrag)

---

## 🚀 Oversikt

Dette komponentbiblioteket er bygget med følgende prinsipper:

- **Svelte 5 Native**: Bruker nye features som `$state`, `$derived`, og `$props`
- **TypeScript First**: Alle komponenter har fullstendige type-definisjoner
- **Design System Integration**: Basert på CSS custom properties for konsistens
- **Modularitet**: Hver komponent kan brukes individuelt eller sammen
- **Accessibility**: ARIA-attributter og semantisk HTML
- **Responsive**: Mobile-first design som fungerer på alle skjermstørrelser

---

## 🧱 Base UI Komponenter

### Button

En fleksibel knapp-komponent med forskjellige varianter og tilstander.

#### Props

```typescript
interface ButtonProps {
  variant?: 'primary' | 'success' | 'error' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  loading?: boolean;
  onclick?: (event: MouseEvent) => void;
}
```

#### Eksempler

```svelte
<script>
  import { Button } from '$lib/components/ui';
</script>

<!-- Basis bruk -->
<Button>Click me</Button>

<!-- Forskjellige varianter -->
<Button variant="primary">Primary</Button>
<Button variant="success">Success</Button>
<Button variant="error">Error</Button>
<Button variant="outline">Outline</Button>

<!-- Forskjellige størrelser -->
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>

<!-- Med loading state -->
<Button loading={true}>Saving...</Button>

<!-- Med event handler -->
<Button onclick={() => console.log('Clicked!')}>
  Click me
</Button>
```

#### CSS Classes

- `.btn` - Base button styling
- `.btn-primary` - Primary variant
- `.btn-success` - Success variant  
- `.btn-error` - Error variant
- `.btn-outline` - Outline variant
- `.btn-sm` - Small size
- `.btn-lg` - Large size
- `.btn-loading` - Loading state

---

### Card

En container-komponent for å gruppere relatert innhold.

#### Props

```typescript
interface CardProps {
  variant?: 'default' | 'compact' | 'elevated';
  padding?: 'sm' | 'md' | 'lg';
  shadow?: boolean;
}
```

#### Eksempler

```svelte
<script>
  import { Card } from '$lib/components/ui';
</script>

<!-- Basis bruk -->
<Card>
  <h3>Card Title</h3>
  <p>Card content goes here</p>
</Card>

<!-- Forskjellige varianter -->
<Card variant="compact" padding="sm">
  Compact card with small padding
</Card>

<Card variant="elevated" shadow={true}>
  Elevated card with enhanced shadow
</Card>

<!-- Uten shadow -->
<Card shadow={false}>
  Card without shadow
</Card>
```

#### CSS Classes

- `.card` - Base card styling
- `.card-compact` - Compact variant
- `.card-elevated` - Elevated variant
- `.card-no-shadow` - No shadow modifier
- `.card-padding-sm` - Small padding
- `.card-padding-md` - Medium padding

---

### Input

En form input-komponent med label, validering og hjelpetekst.

#### Props

```typescript
interface InputProps {
  label?: string;
  placeholder?: string;
  value?: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'url';
  required?: boolean;
  disabled?: boolean;
  error?: string;
  help?: string;
  oninput?: (event: Event) => void;
  onchange?: (event: Event) => void;
}
```

#### Eksempler

```svelte
<script>
  import { Input } from '$lib/components/ui';
  
  let name = $state('');
  let email = $state('');
  let password = $state('');
</script>

<!-- Basis bruk -->
<Input label="Name" bind:value={name} />

<!-- Med placeholder og help tekst -->
<Input 
  label="Email" 
  type="email"
  placeholder="your@email.com"
  bind:value={email}
  help="Vi sender aldri spam"
/>

<!-- Med validering -->
<Input 
  label="Password" 
  type="password"
  bind:value={password}
  required
  error={password.length < 8 ? 'Minimum 8 karakterer' : undefined}
/>

<!-- Disabled state -->
<Input label="Read only" value="Cannot edit" disabled />
```

#### Features

- Automatisk ID generering for accessibility
- ARIA attributes for screen readers
- Error state styling
- Help text support
- Required field indication

---

### InputWithSuggestions

En avansert input-komponent med autocomplete/suggestions funksjonalitet. Perfekt for felt hvor brukeren ofte gjenbruker verdier.

#### Props

```typescript
interface InputWithSuggestionsProps {
  label?: string;
  placeholder?: string;
  value?: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'url';
  required?: boolean;
  disabled?: boolean;
  error?: string;
  help?: string;
  suggestions?: string[];
  maxSuggestions?: number;
  oninput?: (event: Event) => void;
  onchange?: (event: Event) => void;
  onselect?: (value: string) => void;
}
```

#### Eksempler

```svelte
<script>
  import { InputWithSuggestions } from '$lib/components/ui';
  
  let searchQuery = $state('');
  
  const recentSearches = [
    'Oslo',
    'Bergen',
    'Trondheim',
    'Stavanger'
  ];
</script>

<!-- Med suggestions liste -->
<InputWithSuggestions 
  label="Søk etter by"
  bind:value={searchQuery}
  suggestions={recentSearches}
  placeholder="Start å skrive..."
  onselect={(value) => console.log('Selected:', value)}
/>

<!-- Med begrenset antall suggestions -->
<InputWithSuggestions 
  label="Filtrer"
  bind:value={searchQuery}
  suggestions={manyOptions}
  maxSuggestions={5}
/>
```

#### Features

- **Autocomplete**: Viser filtrerte forslag basert på input
- **Keyboard navigation**: Bruk pil-taster for å navigere i forslagslisten
- **Accessibility**: Full ARIA support med `role="listbox"` og `aria-activedescendant`
- **Click outside**: Lukker forslagslisten automatisk
- **Escape key**: Lukk med Escape-tasten
- **Case-insensitive filtering**: Matcher uavhengig av store/små bokstaver

---

### SelectWithHistory

En select-komponent som automatisk husker tidligere valg og viser dem øverst i listen. Bruker localStorage for å bevare historikk mellom sessions.

#### Props

```typescript
interface SelectWithHistoryProps {
  label?: string;
  value?: string | number;
  options?: SelectOption[];
  required?: boolean;
  disabled?: boolean;
  error?: string;
  help?: string;
  placeholder?: string;
  multiple?: boolean;
  historyConfig?: HistoryConfig;
  onchange?: (event: Event) => void;
  onselect?: (value: string | number) => void;
}

interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

interface HistoryConfig {
  key: string;        // localStorage key
  maxItems?: number;  // Max antall historikk-elementer (default: 20)
  unique?: boolean;   // Fjern duplikater (default: true)
}
```

#### Eksempler

```svelte
<script>
  import { SelectWithHistory } from '$lib/components/ui';
  
  let selectedAuthorId = $state('');
  
  const authors = [
    { id: 1, name: 'John Doe' },
    { id: 2, name: 'Jane Smith' },
    { id: 3, name: 'Bob Johnson' }
  ];
</script>

<!-- Med history tracking -->
<SelectWithHistory
  label="👤 Velg forfatter"
  bind:value={selectedAuthorId}
  options={authors.map(a => ({ value: a.id, label: a.name }))}
  placeholder="Velg..."
  historyConfig={{ 
    key: 'author-selection-history',
    maxItems: 10 
  }}
  help="Tidligere valg vises øverst"
/>

<!-- Single select (standard) -->
<SelectWithHistory
  label="Land"
  bind:value={country}
  options={countryOptions}
  historyConfig={{ key: 'country-history' }}
/>

<!-- Multiple select med history -->
<SelectWithHistory
  label="Tags"
  bind:value={selectedTags}
  options={tagOptions}
  multiple={true}
  historyConfig={{ key: 'tags-history' }}
/>
```

#### Features

- **Automatisk historikk**: Lagrer valg i localStorage automatisk
- **Gruppert visning**: Viser "Tidligere brukte verdier" og "Alle alternativer" separat
- **Multiple select støtte**: Fungerer både for single og multiple select
- **Persistent**: Historikk bevares mellom sessions
- **Konfigurerbar**: Sett max antall historikk-elementer
- **Type-safe**: Full TypeScript støtte

#### Integrerer med InputHistoryService

Komponenten bruker `InputHistoryService` internt for å håndtere localStorage. Du kan også bruke denne servicen direkte:

```typescript
import { InputHistoryService } from '$lib/services/input-history.service';

// Legg til i historikk
InputHistoryService.addToHistory(
  { key: 'my-key', maxItems: 15 },
  'Min verdi'
);

// Hent historikk
const history = InputHistoryService.getHistory('my-key');

// Fjern fra historikk
InputHistoryService.removeFromHistory('my-key', 'Min verdi');

// Tøm all historikk
InputHistoryService.clearHistory('my-key');

// Søk i historikk
const results = InputHistoryService.searchHistory('my-key', 'søkeord');
```

---

### PageHeader

En gjenbrukbar header-komponent for konsistente side-headers.

#### Props

```typescript
interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: string;
  actions?: any; // Snippet for action buttons
}
```

#### Eksempler

```svelte
<script>
  import { PageHeader, Button } from '$lib/components/ui';
</script>

<!-- Basis bruk -->
<PageHeader title="Page Title" />

<!-- Med beskrivelse og ikon -->
<PageHeader 
  title="Photos" 
  icon="📸"
  description="Browse your photo collection"
/>

<!-- Med action buttons -->
<PageHeader 
  title="Settings" 
  icon="⚙️"
  description="Manage your preferences"
>
  <Button variant="primary">Save Changes</Button>
  <Button variant="outline">Reset</Button>
</PageHeader>
```

#### Features

- Responsive design (stacks vertically on mobile)
- Flexible action slot for buttons
- Consistent spacing og typography
- Icon support med emoji eller SVG

---

```

---

## � Services

### InputHistoryService

En TypeScript service for å håndtere input-historikk i localStorage. Brukes internt av `SelectWithHistory`, men kan også brukes standalone i egne komponenter.

#### API

```typescript
class InputHistoryService {
  // Legg til verdi i historikk
  static addToHistory(config: HistoryConfig, value: string): void;
  
  // Hent historikk for en key
  static getHistory(key: string): string[];
  
  // Fjern en spesifikk verdi fra historikk
  static removeFromHistory(key: string, value: string): void;
  
  // Tøm all historikk for en key
  static clearHistory(key: string): void;
  
  // Søk i historikk
  static searchHistory(key: string, query: string): string[];
  
  // Sjekk om en verdi finnes i historikk
  static hasInHistory(key: string, value: string): boolean;
}

interface HistoryConfig {
  key: string;        // Unik nøkkel for localStorage
  maxItems?: number;  // Max antall elementer (default: 20)
  unique?: boolean;   // Fjern duplikater (default: true)
}
```

#### Eksempler

```typescript
import { InputHistoryService } from '$lib/services/input-history.service';

// Legg til i historikk
InputHistoryService.addToHistory(
  { key: 'search-history', maxItems: 50, unique: true },
  'Oslo'
);

// Hent historikk
const searches = InputHistoryService.getHistory('search-history');
console.log(searches); // ['Oslo', 'Bergen', ...]

// Søk i historikk
const filtered = InputHistoryService.searchHistory('search-history', 'os');
console.log(filtered); // ['Oslo']

// Fjern en verdi
InputHistoryService.removeFromHistory('search-history', 'Oslo');

// Tøm all historikk
InputHistoryService.clearHistory('search-history');

// Sjekk om verdi finnes
const hasValue = InputHistoryService.hasInHistory('search-history', 'Oslo');
```

#### Features

- **localStorage basert**: Persistent mellom sessions
- **Type-safe**: Full TypeScript support
- **Error handling**: Graceful fallback ved localStorage feil
- **Unique values**: Automatisk fjern duplikater (konfigurerbar)
- **Size limit**: Konfigurerbar max størrelse
- **Search support**: Innebygd søkefunksjonalitet

#### Bruk i egne komponenter

```svelte
<script lang="ts">
  import { InputHistoryService } from '$lib/services/input-history.service';
  
  let searchValue = $state('');
  let suggestions = $state<string[]>([]);
  
  const HISTORY_KEY = 'my-search-history';
  
  // Last inn historikk
  $effect(() => {
    suggestions = InputHistoryService.getHistory(HISTORY_KEY);
  });
  
  function handleSearch() {
    // Lagre søket
    InputHistoryService.addToHistory(
      { key: HISTORY_KEY, maxItems: 20 },
      searchValue
    );
    
    // Utfør søk...
  }
</script>

<input 
  bind:value={searchValue} 
  list="suggestions"
  on:change={handleSearch}
/>

<datalist id="suggestions">
  {#each suggestions as suggestion}
    <option value={suggestion} />
  {/each}
</datalist>
```

---

## 🎨 Domain Komponenter

### PhotoCard

En spesialisert komponent for å vise foto-informasjon i forskjellige formater.

#### Props

```typescript
interface PhotoCardProps {
  photo: any;
  variant?: 'compact' | 'detailed' | 'grid' | 'list';
  showActions?: boolean;
  clickable?: boolean;
  onclick?: () => void;
}
```

#### Photo Object Structure

```typescript
interface Photo {
  primary_filename: string;
  hothash: string;
  hotpreview?: string; // Base64 encoded image
  taken_at?: string;
  title?: string;
  description?: string;
  author?: { name: string };
  width?: number;
  height?: number;
  rating?: number;
  has_gps?: boolean;
  gps_latitude?: number;
  gps_longitude?: number;
  has_raw_companion?: boolean;
  files?: string[];
  tags?: string[];
  created_at: string;
}
```

#### Eksempler

```svelte
<script>
  import { PhotoCard } from '$lib/components/domain';
  
  const photo = {
    primary_filename: "sunset.jpg",
    hothash: "abc123",
    taken_at: "2024-08-15T18:30:00Z",
    width: 1920,
    height: 1080,
    rating: 4,
    created_at: "2024-08-16T10:15:00Z"
  };
</script>

<!-- Forskjellige varianter -->
<PhotoCard {photo} variant="compact" />
<PhotoCard {photo} variant="grid" />
<PhotoCard {photo} variant="detailed" />
<PhotoCard {photo} variant="list" />

<!-- Med actions og click handler -->
<PhotoCard 
  {photo} 
  variant="grid"
  showActions={true}
  clickable={true}
  onclick={() => openPhotoModal(photo)}
/>
```

#### Varianter

- **`compact`**: Minimal informasjon, små thumbnails
- **`grid`**: Standard grid-visning med medium informasjon  
- **`detailed`**: Full informasjon inkludert metadata
- **`list`**: Horisontal layout for listevisning

---

### PhotoGrid

En container-komponent for å vise flere PhotoCard komponenter i forskjellige layouts.

#### Props

```typescript
interface PhotoGridProps {
  photos: any[];
  layout?: 'grid' | 'list' | 'masonry';
  cardVariant?: 'compact' | 'detailed' | 'grid' | 'list';
  showActions?: boolean;
  onPhotoClick?: (photo: any) => void;
}
```

#### Eksempler

```svelte
<script>
  import { PhotoGrid } from '$lib/components/domain';
  
  let photos = [...]; // Array of photo objects
  
  function handlePhotoClick(photo) {
    console.log('Clicked photo:', photo.primary_filename);
  }
</script>

<!-- Grid layout -->
<PhotoGrid 
  {photos}
  layout="grid"
  cardVariant="compact"
/>

<!-- List layout -->
<PhotoGrid 
  {photos}
  layout="list"
  onPhotoClick={handlePhotoClick}
/>

<!-- Masonry layout med actions -->
<PhotoGrid 
  {photos}
  layout="masonry"
  cardVariant="detailed"
  showActions={true}
  onPhotoClick={handlePhotoClick}
/>
```

#### Layouts

- **`grid`**: Responsive grid med auto-fill columns
- **`list`**: Single column liste-visning
- **`masonry`**: Pinterest-style masonry layout

---

## 📦 Installasjon og Bruk

### Import Statements

```typescript
// Base UI komponenter
import { Button, Card, Input, PageHeader } from '$lib/components/ui';

// Domain komponenter  
import { PhotoCard, PhotoGrid } from '$lib/components/domain';

// Individuell import
import Button from '$lib/components/ui/Button.svelte';
import PhotoCard from '$lib/components/domain/PhotoCard.svelte';
```

### Type Definitions

Alle TypeScript interfaces er tilgjengelige via:

```typescript
import type { 
  ButtonProps, 
  CardProps, 
  InputProps, 
  PageHeaderProps 
} from '$lib/components/ui';

import type { 
  PhotoCardProps, 
  PhotoGridProps 
} from '$lib/components/domain';
```

---

## 🎨 Design System

### CSS Custom Properties

Komponentene bruker følgende design tokens:

```css
:root {
  /* Colors */
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  --color-success: #10b981;
  --color-error: #dc2626;
  --color-warning: #f59e0b;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* Typography */
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  
  /* Border radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 10px 15px rgba(0, 0, 0, 0.1);
}
```

### Utility Classes

Globale utility classes tilgjengelig i hele applikasjonen:

```css
/* Text utilities */
.text-xs, .text-sm, .text-lg, .text-xl
.text-success, .text-error, .text-warning, .text-muted
.font-medium, .font-semibold, .font-bold

/* Layout utilities */
.flex, .flex-col, .grid
.items-center, .justify-center, .justify-between
.gap-sm, .gap-md, .gap-lg
.space-y-sm, .space-y-md, .space-y-lg

/* Component utilities */
.btn, .card, .form-input, .alert
.loading-spinner
```

---

## 🔧 Utvidelse og Tilpasning

### Legge til Nye Varianter

```svelte
<!-- Button.svelte -->
<script lang="ts">
  interface Props {
    variant?: 'primary' | 'success' | 'error' | 'outline' | 'ghost'; // Ny variant
    // ... andre props
  }
</script>

<style>
  :global(.btn-ghost) {
    background: transparent;
    color: var(--color-gray-600);
    border: none;
  }
  
  :global(.btn-ghost:hover) {
    background: var(--color-gray-50);
  }
</style>
```

### Lage Nye Komponenter

```svelte
<!-- Badge.svelte -->
<script lang="ts">
  interface Props {
    variant?: 'default' | 'success' | 'error' | 'warning';
    size?: 'sm' | 'md';
  }
  
  let { variant = 'default', size = 'md', children }: Props & { children: any } = $props();
  
  const classes = $derived([
    'badge',
    `badge-${variant}`,
    size !== 'md' ? `badge-${size}` : null
  ].filter(Boolean).join(' '));
</script>

<span class={classes}>
  {@render children()}
</span>

<style>
  .badge {
    display: inline-flex;
    align-items: center;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-full);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
  }
  
  .badge-default {
    background: var(--color-gray-100);
    color: var(--color-gray-800);
  }
  
  .badge-success {
    background: var(--bg-success);
    color: var(--color-success-hover);
  }
  
  /* ... andre varianter */
</style>
```

---

## ✅ Implementeringsstatus

### Implementerte Komponenter

| Komponent | Status | Features | Bruk i prod |
|-----------|--------|----------|-------------|
| Button | ✅ Komplett | Varianter, størrelser, loading state | ✅ Brukes |
| Card | ✅ Komplett | Varianter, padding, shadow | ✅ Brukes |
| Input | ✅ Komplett | Validering, error handling, help text | ✅ Brukes |
| InputWithSuggestions | ✅ Komplett | Autocomplete, keyboard nav, ARIA | ⏳ Klar til bruk |
| SelectWithHistory | ✅ Komplett | History tracking, localStorage, multiple | ✅ Brukes i import |
| PageHeader | ✅ Komplett | Title, description, actions | ✅ Brukes |
| PhotoCard | ✅ Komplett | Lazy loading, thumbnails | ✅ Brukes |
| PhotoGrid | ✅ Komplett | Responsive grid, masonry | ✅ Brukes |

### Implementerte Services

| Service | Status | Features | Testing |
|---------|--------|----------|---------|
| InputHistoryService | ✅ Komplett | localStorage, search, CRUD | ✅ I bruk |

### Brukseksempler i Produksjon

#### SelectWithHistory i Import Flow

```svelte
<!-- Fra /frontend/src/routes/import/new/+page.svelte -->
<SelectWithHistory
  label="👤 Author (Optional)"
  bind:value={selectedAuthorId}
  options={authors.map(author => ({ value: author.id, label: author.name }))}
  placeholder="Velg forfatter..."
  disabled={importing}
  historyConfig={{ key: HISTORY_KEYS.AUTHOR_NAMES, maxItems: 10 }}
  help="Velg en forfatter for alle importerte bilder"
/>
```

**Verifisert funksjonalitet:**
- ✅ Viser tidligere brukte forfattere øverst
- ✅ Lagrer valg i localStorage under key `HISTORY_KEYS.AUTHOR_NAMES`
- ✅ Begrenser til max 10 historikk-elementer
- ✅ Fungerer med disabled state under import
- ✅ Integrert med existing author management

---

## 🧪 Testing og Utvikling

### Demo Sider

- `/ui-demo` - Viser alle base UI komponenter
- `/photo-demo` - Demonstrerer PhotoCard og PhotoGrid varianter

### Live Reloading

Alle komponenter støtter Svelte's hot module replacement for rask utvikling.

### Type Checking

```bash
npm run check        # Type checking
npm run check:watch  # Kontinuerlig type checking
```

---

## 🎯 Best Practices

### Komponent Komposisjon

```svelte
<!-- God praksis: Komponenter sammen -->
<PageHeader title="My Photos" icon="📸">
  <Button variant="primary">Upload</Button>
</PageHeader>

<PhotoGrid 
  {photos}
  layout="grid"
  cardVariant="compact"
  onPhotoClick={openLightbox}
/>
```

### Konsistent Styling

```svelte
<!-- Bruk design tokens -->
<div style="padding: var(--spacing-lg); gap: var(--spacing-md);">
  <!-- Innhold -->
</div>

<!-- Bruk utility classes -->
<div class="flex items-center gap-md">
  <Button variant="primary">Save</Button>
  <Button variant="outline">Cancel</Button>
</div>
```

### TypeScript Integration

```typescript
// Type din data korrekt
interface Photo {
  id: string;
  filename: string;
  // ... andre fields
}

let photos: Photo[] = $state([]);

// Bruk typed event handlers
function handlePhotoClick(photo: Photo) {
  console.log('Clicked:', photo.filename);
}
```

---

## 📈 Performance

### Lazy Loading

Komponenter lastes kun når de importeres:

```typescript
// Treg import
import { Button } from '$lib/components/ui';

// Rask - kun det du trenger
import Button from '$lib/components/ui/Button.svelte';
```

### Bundle Size

Hver komponent er separat og bidrar kun til bundle size når brukt.

### CSS Optimization

- Scoped CSS forhindrer konflikter
- Utility classes gjenbrukes på tvers av komponenter
- Design tokens reduserer CSS duplikasjon

---

## 🚀 Fremtidige Forbedringer

### Planlagte Komponenter

- `Modal` - Dialog og overlay komponenter
- `Alert` - Notification komponenter  
- `Badge` - Status og kategorisering
- `Tooltip` - Kontekstuell hjelp
- `DataTable` - Tabeller med sortering og filtrering
- `Dropdown` - Avanserte select/meny komponenter
- `Tabs` - Tab navigation
- `Accordion` - Collapsible content sections

### Implementerte men kan forbedres

#### InputWithSuggestions
- ⏳ Ikke brukt i produksjon ennå
- 💡 Kunne vært brukt for søkefelt
- 💡 Kunne integreres med InputHistoryService for persistent suggestions

#### SelectWithHistory
- ✅ Fungerer bra i import flow
- 💡 Kunne brukes flere steder (storage location, tags, etc.)
- 💡 Kunne ha visuell indikator for "fra historikk"

### Tekniske Forbedringer

- Dark mode støtte
- Animasjoner og overganger (Svelte transitions)
- Full accessibility audit med axe-core
- Storybook dokumentasjon
- Unit tests for alle komponenter
- Visual regression testing
- Performance profiling

---

## 🚀 Fremtidige Forbedringer

### Planlagte Komponenter

- `Modal` - Dialog og overlay komponenter
- `Alert` - Notification komponenter
- `Badge` - Status og kategorisering
- `Tooltip` - Kontekstuell hjelp
- `DataTable` - Tabeller med sortering og filtrering
- `Dropdown` - Select og meny komponenter

### Forbedringer

- Dark mode støtte
- Animasjoner og overganger
- Accessibility audit og forbedringer
- Storybook dokumentasjon
- Unit tests for alle komponenter

---

## 📞 Support og Bidrag

### Rapportere Issues

Hvis du finner bugs eller har forslag til forbedringer, vennligst opprett en issue.

### Bidra med Kode

1. Fork repositoryet
2. Opprett en feature branch
3. Følg eksisterende kode-stil og conventions
4. Test endringene dine
5. Opprett en pull request

### Kode-stil

- Bruk TypeScript for alle komponenter
- Følg Svelte 5 conventions med `$state`, `$derived`, etc.
- Bruk semantic HTML og ARIA attributes
- Inkluder CSS custom properties for theming
- Skriv tydelige props interfaces

---

*Denne dokumentasjonen oppdateres kontinuerlig med nye komponenter og features.*

---

## 📝 Changelog

### 2025-10-10: Input History Components

**Nye komponenter:**
- ✅ `InputWithSuggestions` - Input med autocomplete/suggestions
- ✅ `SelectWithHistory` - Select med localStorage-basert historikk
- ✅ `InputHistoryService` - Service for å håndtere input-historikk

**Implementert i produksjon:**
- SelectWithHistory brukes i `/import/new` for author-valg
- Historikk lagres i localStorage under HISTORY_KEYS.AUTHOR_NAMES
- Max 10 historikk-elementer per key

**Tekniske forbedringer:**
- Fikset `$derived` til `$derived.by` for arrays i Svelte 5
- Oppdatert SelectOption interface med `isHistory` og `isGroup` properties
- Full TypeScript type-safety
- Ingen kompileringsfeil i noen komponenter

**Testing:**
- ✅ Alle UI-komponenter kompilerer uten feil
- ✅ SelectWithHistory verifisert i import flow
- ✅ InputHistoryService fungerer med localStorage
- ⏳ InputWithSuggestions klar til bruk (ikke i prod ennå)

---