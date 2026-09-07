# CHECKPOINT — Gossmere digital business cards — 2026-09-07

## Repository
`GossmereHQ/gossmere-site`

## Files in active workstream
- `biglietto.html` — Erika Iengo
- `biglietto-federica.html` — Federica Iengo

## Current live intent
Two mobile-first digital business cards on `gossmere.com`, dark Gossmere styling, with contact actions, vCard save and QR code.

### Erika
- Name: Erika Iengo
- Role EN: `Founder & Digital Solutions Architect`
- Role IT: `Fondatrice, sviluppatrice e progettista di soluzioni digitali`
- WhatsApp/phone: `+39 338 756 1749`
- Email: `gossmere@gmail.com`
- URL: `https://gossmere.com/biglietto.html`

### Federica
- Name: Federica Iengo
- Role EN: `Data Engineer & BI / Analytics Specialist`
- Role IT: `Data Engineer e specialista in Business Intelligence e analisi dati`
- Contact routes through Gossmere / Erika phone and `gossmere@gmail.com`
- URL: `https://gossmere.com/biglietto-federica.html`
- Positioning note currently visible: specialist Gossmere service with separate scope/cost.

## Last correction completed
The Gossmere mark previously rendered badly because both cards referenced `/assets/gossmere-logo.webp`, which visually appeared as a smaller rectangular image inside the badge.

Both cards have now been corrected to use the intended Gossmere symbol directly as an embedded WebP data URI, with the mark enlarged from 118px to 124px inside the 132px badge. This avoids dependence on the wrong padded asset.

Commits:
- Erika logo fix: `f69003aec5f16a55bc9a957135547efc3c266cba`
- Federica logo fix: `b9387ddb3f3d08d2278d012f6c04d722f063e200`

## Important operating rule for the next chat
Do not restart the design from scratch and do not send Erika back to an old chat message. Read this checkpoint and inspect the current versions of `biglietto.html` and `biglietto-federica.html` in GitHub before editing.

Continue making requested corrections directly in GitHub as in this work session, rather than only giving snippets for Erika to paste manually.

## Next step
Open/test both live pages after GitHub Pages propagation and continue visual refinements from the current versions if Erika reports anything still off. Preserve working contact links, QR targets and current card structure unless explicitly asked to change them.
