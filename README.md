# Della Rice — Shopify redesign

Shopify Online Store 2.0 theme implementing the Della Redesign Figma file, reconciled with the newer WordPress review pages. Built on Shopify Dawn 16.1.1 (`3e9ee22`), with reusable Della sections and locally bundled design assets.

## Development

Use Shopify CLI and `shopify theme check`. Connect this repository's `main` branch to an **unpublished** Shopify theme. Keep production publishing and domain changes separate from draft development.

Pages: Home, the rice catalogue, About, Where to Buy, Wholesale and Contact. Product, variant, media, search, cart and checkout handoff retain Dawn's native implementation.

## Migration status

The target Shopify store began with no products. The theme therefore shows an explicitly labelled catalogue preview using the 12 verified WordPress product names, images, weights and source prices. It switches to Shopify product objects when products are imported. No inventory, SKUs, tax rules or shipping rates have been invented. Preview prices are source USD values, not configured Shopify selling prices.

The contact form uses Shopify's native contact form. A live retailer database has not been supplied; the Where to Buy page provides a real contact path instead of simulated search results. Verified Faire and Airgoods ordering links are preserved. The proposed merchandise module is omitted until there is an approved catalogue.

See [migration checklist](docs/migration.md) and [source catalogue](docs/catalogue-source.json). This repository contains no WordPress credentials, customer records, orders or temporary Figma download links.

The migration staging branch also contains [captured public source data and import payloads](migration/README.md), [capture results and blockers](migration/capture-report.md), and [GSAP motion implementation notes](docs/gsap-motion.md). Capture is complete for the public sitemap inventory; destination imports and animation browser verification are still pending. Private WooCommerce exports must never be committed to this repository.

## Design notes

Colours, spacing, layouts, images and typography roles follow the Figma baseline. Lilita One and Spline Sans Mono are bundled. Recoleta is referenced for the serif homepage headings with Georgia as the fallback; a licensed webfont file is still required for an exact Recoleta match. The green footer logo is rendered cream for legibility.

## Licence

Dawn code retains its original MIT licence in LICENSE.md. Della brand assets and content remain the property of their respective owners.
