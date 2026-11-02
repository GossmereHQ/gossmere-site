/* Gossmere Services: no remote requests, storage, analytics or user-supplied HTML. */
(() => {
  "use strict";
  const form = document.getElementById("sv-form");
  const locale = document.documentElement.lang;
  const status = document.getElementById("sv-status");
  const titles = {
    it: "Richiesta servizi Gossmere",
    en: "Gossmere service enquiry",
    fr: "Demande de services Gossmere",
    de: "Anfrage zu Gossmere Dienstleistungen",
    es: "Consulta sobre servicios Gossmere",
    pt: "Pedido de serviços Gossmere"
  };
  const messages = {
    it: "Si apre una bozza email. Controlla il contenuto e inviala dalla tua applicazione di posta: il sito non invia messaggi automaticamente.",
    en: "An email draft will open. Review and send it using your email app; this website does not submit it automatically.",
    fr: "Un brouillon d’e-mail va s’ouvrir. Vérifiez-le et envoyez-le depuis votre application de messagerie.",
    de: "Ein E-Mail-Entwurf wird geöffnet. Bitte prüfen und über Ihre E-Mail-App selbst absenden.",
    es: "Se abrirá un borrador de correo. Revísalo y envíalo desde tu aplicación de correo.",
    pt: "Será aberto um rascunho de e-mail. Reveja-o e envie-o através da sua aplicação de correio."
  };
  const clean = (value, max, multiline = false) => {
    let s = String(value || "").normalize("NFC").slice(0, max);
    s = s.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "");
    if (!multiline) s = s.replace(/[\r\n\t]+/g, " ");
    return s.trim();
  };
  const safe = (key, max, multiline = false) => clean(form.elements.namedItem(key)?.value, max, multiline);
  const service = form?.elements.namedItem("service");
  const langSelect = document.getElementById("sv-language");
  if (langSelect) {
    langSelect.addEventListener("change", () => {
      const valid = ["/services/", "/servizi/", "/services/fr/", "/services/de/", "/services/es/", "/services/pt/"];
      if (valid.includes(langSelect.value)) window.location.assign(langSelect.value);
    });
  }
  if (!form || !status || !service) return;
  form.addEventListener("submit", event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const chosen = service.options[service.selectedIndex]?.textContent || "";
    const subject = (titles[locale] || titles.en) + ": " + clean(chosen, 90);
    const details = [
      "Name / Nome: " + safe("name", 120),
      "Company / Azienda: " + safe("company", 130),
      "Reply email / Email: " + safe("email", 254),
      "Phone / Telefono: " + safe("phone", 32),
      "Service / Servizio: " + clean(chosen, 90),
      "", "Message / Messaggio:", safe("message", 1200, true)
    ].join("\n");
    if (!safe("name", 120) || !safe("email", 254) || safe("message", 1200, true).length < 10) return;
    const uri = "mailto:gossmere@gmail.com?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(details);
    status.textContent = messages[locale] || messages.en;
    window.location.href = uri;
  });
})();
