window.SOS_ORDER_CONFIG = Object.freeze({
  apiBase: "",
  turnstileSiteKey: "",
  serverCheckoutEnabled: false
});
// Production activation must set the public Turnstile site key and enable
// serverCheckoutEnabled only after D1, Access, notification delivery and
// preview E2E tests pass. No secrets belong in this file.
