# ImaLink Logo Assets

Dette er logo- og ikonfilene for ImaLink-applikasjonen.

## Filer

### Kilde
- `imalink_logo.svg` - Hovedlogo i SVG-format (skalebar vektor)

### Web og App Ikoner
- `imalink_icon_16.png` - 16x16px (Windows Small Icon, Taskbar)
- `imalink_icon_24.png` - 24x24px (Windows Medium Icon)
- `imalink_icon_32.png` - 32x32px (Windows Large Icon, Desktop)
- `imalink_icon_48.png` - 48x48px (Windows XL Icon)
- `imalink_icon_64.png` - 64x64px (Standard App Icon)
- `imalink_icon_128.png` - 128x128px (macOS App Icon)
- `imalink_icon_256.png` - 256x256px (High-DPI Displays)
- `imalink_icon_512.png` - 512x512px (Retina Displays, App Stores)

### Spesialformater
- `imalink_icon.ico` - Windows ICO-fil (multi-size)
- `favicon.ico` - Web favicon (16, 32, 48px)
- `apple-touch-icon.png` - 180x180px (iOS Safari, PWA)

## Design

Logoen viser et fjelllandskap med solnedgang:
- **Gul bakgrunn** (#f1c40f) - Representerer lys og kreativitet
- **Rød ramme** (#e74c3c) - Gir kontrast og merkevaregjenkjennelse
- **Fjellsilhuett** - Symboliserer stabilitet og kvalitet
- **Sol** - Representerer klarhet og visjon
- **"IL"** - ImaLink forkortelse

## Bruk

### Web
```html
<!-- Favicon -->
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/imalink_icon_32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/imalink_icon_16.png">

<!-- Apple Touch Icon -->
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
```

### App Manifest
```json
{
  "icons": [
    {
      "src": "/imalink_icon_192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/imalink_icon_512.png", 
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### Desktop App
- Bruk `imalink_icon.ico` for Windows-applikasjoner
- Bruk `imalink_icon_128.png` eller høyere for macOS
- Bruk `imalink_icon_64.png` for Linux desktop

## Farger
- Primær gul: `#f1c40f`
- Accent rød: `#e74c3c`
- Fjell mørk: `#2c3e50`, `#34495e`
- Sol orange: `#e67e22`, `#f39c12`, `#f1c40f`