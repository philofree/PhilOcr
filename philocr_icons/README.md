# PhiloFree Icon Set

This directory contains a comprehensive icon set based on the Greek letter φ (phi), which is the primary logo element for PhiloFree.

## Icon Files

### Favicons (Small Icons)
- **favicon-16.svg** - 16×16 favicon for browser tabs
- **favicon-32.svg** - 32×32 favicon for high-DPI displays

### Standard Icons (100×100 viewBox)

#### Circle Icons
- **icon-circle.svg** - Light background (#f4f1ec) with dark phi (#1b1b1b) - matches current favicon
- **icon-circle-dark.svg** - Dark navy background (#1e3a6e) with light phi (#f4f1ec)
- **icon-circle-navy.svg** - Deeper navy background (#152d52) with light gray phi (#c0c0c0)

#### Square Icons
- **icon-square.svg** - Light background with rounded corners (4px radius)
- **icon-square-dark.svg** - Dark navy background with light phi

#### Rounded Square Icons
- **icon-rounded.svg** - Light background with larger rounded corners (12px radius)
- **icon-rounded-dark.svg** - Dark navy background with larger rounded corners

#### Outline Icons
- **icon-outline.svg** - Outlined circle with dark phi, no fill
- **icon-outline-white.svg** - Outlined circle with white phi, for dark backgrounds

#### Monochrome Icons
- **icon-monochrome.svg** - Black background with white phi
- **icon-white.svg** - White background with black phi

### App Icons (PWA/Mobile)
- **app-icon-192.svg** - 192×192 icon for Progressive Web App (light mode)
- **app-icon-512.svg** - 512×512 icon for Progressive Web App (light mode)

## Design Specifications

- **Font**: Gentium Plus (matching the site's Greek text font)
- **Letter**: φ (lowercase phi)
- **Color Palette**:
  - Background light: `#f4f1ec`
  - Background dark: `#1e3a6e` (main brand color)
  - Background navy: `#152d52` (darker brand variant)
  - Text dark: `#1b1b1b`
  - Text light: `#f4f1ec` or `#c0c0c0`

## Usage

### In HTML

```html
<!-- Favicon -->
<link rel="icon" type="image/svg+xml" href="/icons/favicon-16.svg">

<!-- App icons for PWA -->
<link rel="apple-touch-icon" href="/icons/app-icon-192.svg">
<link rel="manifest" href="/manifest.json">
```

### In CSS

SVG icons can be embedded directly in CSS using data URIs, or referenced as background images:

```css
.logo {
  background-image: url('/icons/icon-circle.svg');
  background-size: contain;
  background-repeat: no-repeat;
  width: 100px;
  height: 100px;
}
```

### For Different Contexts

- **Browser tabs**: Use `favicon-16.svg` or `favicon-32.svg`
- **Dark backgrounds**: Use `*-dark.svg` variants or `icon-outline-white.svg`
- **Light backgrounds**: Use `icon-circle.svg` or other light variants
- **PWA/Mobile apps**: Use `app-icon-192.svg` and `app-icon-512.svg`
- **Print materials**: Use `icon-monochrome.svg` for grayscale printing

## Generating PNG Versions (Optional)

If you need PNG versions of these icons for systems that don't support SVG, you can use tools like:

- **ImageMagick**: `convert icon-circle.svg -resize 512x512 icon-circle-512.png`
- **Inkscape**: `inkscape --export-png=icon-circle-512.png --export-width=512 icon-circle.svg`
- **Online converters**: Various SVG to PNG converters available online

## Web Manifest

The `manifest.json` file in the parent directory includes references to the appropriate icons for Progressive Web App support. This allows PhiloFree to be installed as a web app on mobile devices and desktop systems.
