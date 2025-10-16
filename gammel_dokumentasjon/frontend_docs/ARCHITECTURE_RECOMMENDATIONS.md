# ImaLink Frontend Arkitektur - Anbefalinger

## 🎯 Modularitetsanalyse

### Nåværende Styrker:
- ✅ Godt design system med tokens
- ✅ Konsistent routing struktur  
- ✅ API-lag organisering
- ✅ TypeScript typing

### Kritiske Forbedringspunkter:

## 1. 📦 Gjenbrukbare Komponenter (Høy Prioritet)

### Opprett disse i `/src/lib/components/`:

```
/lib/components/
├── ui/                   # Basis UI komponenter
│   ├── Button.svelte
│   ├── Card.svelte  
│   ├── Modal.svelte
│   ├── Spinner.svelte
│   └── ErrorMessage.svelte
├── layout/               # Layout komponenter
│   ├── PageHeader.svelte
│   ├── DataTable.svelte
│   └── EmptyState.svelte
└── domain/               # Domene-spesifikke
    ├── PhotoCard.svelte
    ├── ImportProgress.svelte
    └── AuthorCard.svelte
```

### Eksempel: PageHeader.svelte
```svelte
<script lang="ts">
  interface Props {
    title: string;
    description?: string;
    actions?: Snippet;
  }
  
  let { title, description, actions }: Props = $props();
</script>

<div class="page-header">
  <div class="page-header-content">
    <h1>{title}</h1>
    {#if description}
      <p>{description}</p>
    {/if}
  </div>
  {#if actions}
    <div class="page-header-actions">
      {@render actions()}
    </div>
  {/if}
</div>
```

## 2. 🔄 Standardisert Data Loading Pattern

### Opprett `/lib/composables/` eller `/lib/hooks/`:

```typescript
// useDataFetching.ts
export function useDataFetching<T>(
  fetchFn: () => Promise<T>, 
  dependencies: any[] = []
) {
  let data = $state<T | null>(null);
  let loading = $state(true);
  let error = $state('');

  async function load() {
    loading = true;
    error = '';
    try {
      data = await fetchFn();
    } catch (err: any) {
      error = err.message || 'Failed to load data';
    } finally {
      loading = false;
    }
  }

  return { data, loading, error, load };
}
```

### Bruk i sider:
```svelte
<script lang="ts">
  import { useDataFetching } from '$lib/hooks/useDataFetching';
  import { PhotosApi } from '$lib/api/photos';
  
  const { data: photos, loading, error, load } = useDataFetching(
    () => PhotosApi.getPhotos()
  );
</script>
```

## 3. 🎨 Utility-First CSS Konsistens

### Flytt ALL styling til utility classes:

```css
/* I +layout.svelte - utvid utility classes */
:global(.page-container) {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-xl);
}

:global(.card) {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-light);
}

:global(.data-table) {
  width: 100%;
  border-collapse: collapse;
  /* osv */
}
```

## 4. 📁 Forbedret Filstruktur

### Anbefalt struktur for `/lib/`:

```
/lib/
├── api/                  # API klienter
│   ├── photos.ts
│   ├── authors.ts  
│   └── imports.ts
├── components/           # Gjenbrukbare komponenter
│   ├── ui/              # Generelle UI
│   ├── layout/          # Layout komponenter  
│   └── domain/          # Domene-spesifikke
├── stores/              # Svelte stores
│   ├── app.ts           # Global state
│   ├── photos.ts        # Photo state
│   └── auth.ts          # Auth state (fremtidig)
├── types/               # TypeScript typer
├── utils/               # Utility funksjoner
├── hooks/               # Gjenbrukbare composables
└── constants/           # App konstanter
```

## 5. 🚀 Implementeringsplan

### Fase 1: Basis Komponenter (1-2 dager)
1. PageHeader.svelte
2. DataTable.svelte  
3. Spinner.svelte
4. ErrorMessage.svelte
5. Button.svelte (erstatt inline buttons)

### Fase 2: Data Loading (1 dag)
1. useDataFetching hook
2. Oppdater eksisterende sider til å bruke den

### Fase 3: Domain Komponenter (2-3 dager)  
1. PhotoCard.svelte
2. AuthorCard.svelte
3. ImportProgress.svelte

### Fase 4: Refaktorer Eksisterende (2-3 dager)
1. /routes/+page.svelte (photos)
2. /routes/import/+page.svelte  
3. /routes/authors/+page.svelte
4. /routes/database-status/+page.svelte

## 6. 📋 Template for Nye Sider

### Standardisert page template:
```svelte
<script lang="ts">
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import DataTable from '$lib/components/layout/DataTable.svelte';
  import { useDataFetching } from '$lib/hooks/useDataFetching';
  import { currentView } from '$lib/stores/app';
  
  currentView.set('page-name');
  
  const { data, loading, error, load } = useDataFetching(/* ... */);
</script>

<div class="page-container">
  <PageHeader 
    title="Page Title" 
    description="Page description"
  >
    {#snippet actions()}
      <button class="btn btn-primary" on:click={load}>
        🔄 Refresh
      </button>
    {/snippet}
  </PageHeader>
  
  <!-- Resten av siden bruker standardiserte komponenter -->
</div>
```

## 7. 🔧 Type Safety Forbedring

### Sentraliser API typer:
```typescript
// /lib/types/api.ts
export interface Photo {
  id: number;
  title: string;
  // ... alle felter
}

export interface ApiResponse<T> {
  data: T[];
  total: number;
}

// /lib/types/ui.ts  
export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
}
```

## Konklusjon

Med disse endringene blir arkitekturen:
- ✅ Mer modulær og gjenbrukbar
- ✅ Lettere å vedlikeholde
- ✅ Konsistent på tvers av sider
- ✅ Raskere å utvikle nye features

**Anbefaling**: Implementer Fase 1-2 før du lager nye sider.