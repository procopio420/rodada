# Issue #106 — E2E-05 current gap

The shared Android/Web runner has no browser scenario that turns a product unavailable after a Guest or Staff draft and before the POST reaches Django. Do not label E2E-05 PASS based solely on unit tests. Required proof: real UI submit, server-side 409 PRODUCTS_NOT_CONFIRMABLE, unchanged existing orders and 0 new Charges/Payments, with an independent PostgreSQL receipt on the same SHA.
