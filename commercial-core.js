// Gossmere commercial tooling v1 — validated by GitHub runner
(() => {
  'use strict';

  const CATALOG_KEY = 'gossmere-commercial-catalog-v1';
  const SETTINGS_KEY = 'gossmere-commercial-settings-v1';

  const DEFAULT_CATALOG = [
    { name: 'Automazione / workflow', price: null, recurring: false, taxable: true },
    { name: 'Biglietto da visita — design', price: null, recurring: false, taxable: true },
    { name: 'Biglietto digitale', price: null, recurring: false, taxable: true },
    { name: 'Biglietto digitale TAP / NFC', price: null, recurring: false, taxable: true },
    { name: 'Brand asset / materiale grafico', price: null, recurring: false, taxable: true },
    { name: 'Care — gestione e manutenzione', price: 39, recurring: true, taxable: true },
    { name: 'Data Intelligence — monitoraggio e analisi periodica (lancio)', price: 189, recurring: true, taxable: true },
    { name: 'Data Intelligence — monitoraggio e analisi periodica (standard)', price: 229, recurring: true, taxable: true },
    { name: 'Dominio — costo vivo registrar', price: null, recurring: true, taxable: true },
    { name: 'Gossmere Managed Domain', price: 99, recurring: true, taxable: true },
    { name: 'Growth / automazione continuativa', price: 89, recurring: true, taxable: true },
    { name: 'Hosting / infrastruttura', price: null, recurring: true, taxable: true },
    { name: 'Logo — design / restyling', price: null, recurring: false, taxable: true },
    { name: 'Personalizzazione dedicata', price: null, recurring: false, taxable: true },
    { name: 'Setup / configurazione', price: null, recurring: false, taxable: true },
    { name: 'Sito / Presence — Starter', price: 390, recurring: false, taxable: true },
    { name: 'Sito / Presence — Starter (fascia alta)', price: 590, recurring: false, taxable: true },
    { name: 'Sito / Business Flow — Conversion', price: 790, recurring: false, taxable: true },
    { name: 'Sito / Business Flow — Conversion (fascia alta)', price: 1190, recurring: false, taxable: true },
    { name: 'Studio Dati Professionale — una tantum (lancio)', price: 390, recurring: false, taxable: true },
    { name: 'Studio Dati Professionale — una tantum (standard)', price: 490, recurring: false, taxable: true },
    { name: 'Supporto tecnico dedicato', price: null, recurring: false, taxable: true },
    { name: 'Web App / System — Pro', price: 1490, recurring: false, taxable: true },
    { name: 'Web App / System — Pro (fascia alta)', price: 2900, recurring: false, taxable: true }
  ];

  const DEFAULT_SETTINGS = {
    vatEnabled: false,
    vatRate: 22,
    currency: 'EUR'
  };

  const normalize = value => String(value ?? '').trim().replace(/\s+/g, ' ');
  const byName = (a, b) => a.name.localeCompare(b.name, 'it', { sensitivity: 'base' });

  function loadCatalog() {
    try {
      const saved = JSON.parse(localStorage.getItem(CATALOG_KEY));
      if (Array.isArray(saved) && saved.length) return saved.sort(byName);
    } catch (_) {}
    saveCatalog(DEFAULT_CATALOG);
    return DEFAULT_CATALOG.map(x => ({ ...x })).sort(byName);
  }

  function saveCatalog(catalog) {
    const clean = catalog
      .filter(item => normalize(item.name))
      .map(item => ({
        name: normalize(item.name),
        price: item.price === '' || item.price == null ? null : Number(item.price),
        recurring: Boolean(item.recurring),
        taxable: item.taxable !== false
      }))
      .sort(byName);
    localStorage.setItem(CATALOG_KEY, JSON.stringify(clean));
    return clean;
  }

  function upsertCatalogItem(item) {
    const catalog = loadCatalog();
    const name = normalize(item.name);
    if (!name) return catalog;
    const idx = catalog.findIndex(x => x.name.localeCompare(name, 'it', { sensitivity: 'base' }) === 0);
    const clean = {
      name,
      price: item.price === '' || item.price == null ? null : Number(item.price),
      recurring: Boolean(item.recurring),
      taxable: item.taxable !== false
    };
    if (idx >= 0) catalog[idx] = clean; else catalog.push(clean);
    return saveCatalog(catalog);
  }

  function renameCatalogItem(oldName, nextItem) {
    let catalog = loadCatalog().filter(x => x.name !== oldName);
    catalog.push(nextItem);
    return saveCatalog(catalog);
  }

  function deleteCatalogItem(name) {
    return saveCatalog(loadCatalog().filter(x => x.name !== name));
  }

  function loadSettings() {
    try {
      return { ...DEFAULT_SETTINGS, ...(JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {}) };
    } catch (_) {
      return { ...DEFAULT_SETTINGS };
    }
  }

  function saveSettings(settings) {
    const clean = {
      ...DEFAULT_SETTINGS,
      ...settings,
      vatEnabled: Boolean(settings.vatEnabled),
      vatRate: Math.max(0, Number(settings.vatRate) || 0)
    };
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(clean));
    return clean;
  }

  function money(value) {
    return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(Number(value) || 0);
  }

  function totals(rows, settings = loadSettings()) {
    let subtotal = 0;
    let taxableBase = 0;
    for (const row of rows) {
      if (!row.selected) continue;
      const qty = Math.max(0, Number(row.qty) || 0);
      const unit = Math.max(0, Number(row.price) || 0);
      const line = qty * unit;
      subtotal += line;
      if (row.taxable !== false) taxableBase += line;
    }
    const vat = settings.vatEnabled ? taxableBase * (Number(settings.vatRate) || 0) / 100 : 0;
    return { subtotal, taxableBase, vat, total: subtotal + vat };
  }

  window.GossmereCommercial = {
    loadCatalog,
    saveCatalog,
    upsertCatalogItem,
    renameCatalogItem,
    deleteCatalogItem,
    loadSettings,
    saveSettings,
    money,
    totals
  };
})();