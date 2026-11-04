# Draft theme verification — 4 November 2026

Repository: camster91/della-rice, branch main. Shopify draft theme: 189341761837 (`della-rice/main`). The current Horizon theme and public WordPress domain have not been replaced.

## Completed and verified

- Connected the GitHub branch to the unpublished Shopify theme through the authenticated browser.
- Fixed the two server-side import validation errors: unsupported Lilita font-picker handle and page-width step. Native settings use supported Dawn fonts; Della typography is loaded from bundled fonts. The theme editor's colour warning cleared and storefront colour variables render correctly.
- Created About, Where to Buy and Wholesale page records in the password-protected staging store. Existing Contact page is reused. Standard page handles render editable Della section groups without requiring a live theme change.
- Opened and verified Home, About, Where to Buy, Wholesale, Contact, catalogue and empty-cart routes in the actual Shopify preview.
- Desktop homepage: 1440 px viewport; no horizontal overflow. Tablet: 768 px; no horizontal overflow. Mobile: 390 px; no horizontal overflow. Shopify's native mobile preview was also visually checked.
- Mobile menu opens and its links render; Escape closes it. Hero controls change the visible image and selected state.
- All 12 catalogue-preview product images loaded after scrolling. No visible Liquid errors were found in the tested routes.
- Contact form renders labelled name, email, optional phone, enquiry topic and message inputs with Shopify native submission handling. No message was submitted.
- Wholesale buttons retain the verified Faire and Airgoods links.
- Shopify Theme Check 5.0.1: zero errors, nine warnings inherited from Dawn. No Della-section warnings.

## Completed but awaiting verification

- Native product, variant, product-media and cart templates are present, but real product behaviour, checkout, selling plans and sold-out scenarios cannot be verified until products are migrated.
- Full-page mobile/tablet QA of every route and final performance measurement remain release checks; the measured responsive pass above covers the homepage.

## Blocked / awaiting merchant information

- The Shopify catalogue was empty. The 12-card catalogue is clearly marked as a design preview and cannot be purchased. Verify product migration, inventory, SKUs, pricing/currency, tax, shipping, payments and fulfilment before launch.
- Exact Recoleta webfont matching awaits a licensed webfont file; the current serif fallback is Georgia.
- Approved retailer data/locator, final package claims, staff content and legal details remain merchant review items.
- Form delivery, analytics consent, redirect installation and domain cutover remain unperformed.

## Next action

Import and reconcile the WooCommerce product catalogue, then test purchase and contact flows. Review the staged design before publishing any theme or changing DNS.

Screenshots in this directory show the actual Shopify staging preview, not a generated mockup.
