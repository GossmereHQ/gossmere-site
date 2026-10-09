# Gossmere parent brand — visual baseline

Approved direction: 2026-10-09. Scope: Gossmere **parent brand** (not a replacement for each sister product's own accent).

## Canonical tokens
- Absolute background: `#000000`.
- Primary cyan: `#63DFFF`. Focus and modest highlights: `#A3EFFF`.
- Silver secondary typography/detail: `#C9D1D8`.
- Neutral primary typography: `#E9EDF0`.
- Muted tertiary text: `#8B979F`.
- Reserved deep surface: `#05090B`.
- Minimal low-opacity cyan accent; no violet gradients or large saturated aqua panels.
- Font: Manrope, with sensible system fallbacks.
- Hierarchy: ample black negative space, restrained accents, tested mobile contrast and button focus states.

## Logo asset constraints
- Current upstream source in site: `assets/gossmere-logo.webp`, a **lossy VP8 WebP without alpha channel**; original symbol shape must be preserved.
- Source WebP is deliberately **not overwritten** by a hand-drawn approximation.
- Site uses `mix-blend-mode: screen` on the black canvas to visually suppress dark raster pixels. This is an **interim rendering technique**; it is **not a transparent source asset** and can produce artifacts where backgrounds are not absolute black.
- Final approved deliverable: genuine transparency (lossless PNG/WebP-alpha or SVG from original vector), visually inspect edges/glow at normal size; preserve exact symbol silhouette, spacing and colors; no black embedded square/tile; no forced rounding or shadow. Require original source or an independently reviewed faithful extraction before replacing the asset.
- Favicon must be inspected separately for size, padding, transparency support and contrast.

## Release ownership / checklist
Owner: `GossmereHQ/gossmere-site`. Do not modify unrelated apps or products as part of this site brand pass.
- Changes on `design/gossmere-silver-cyan-2026-10-09` for review; merge only after explicit owner approval.
- Before merge verify desktop + mobile screenshots IT and EN, sections, wordmark/logo perception, contrast, reduced-motion/keyboard focus, favicon and hero sizing.
- Next: produce genuine alpha logo faithfully, replace 3 website instances & favicon, compare before/after and seek user approval.
