# Della migration verification

Destination: `della-rice-1hj0pj1j.myshopify.com`, USD. No other store was modified.

## Completed and verified

- 12 draft products: descriptions, source prices, 794 g weights, 34 READY gallery references, no fabricated SKUs or inventory quantities. All 12 source metadata records read back.
- 181 unpublished recipe articles: text, image URLs and links compared to staging after CDN rewriting and HTML normalisation; all source URLs read back. 36 articles in 14 duplicate groups tagged for review.
- Six hidden standalone pages with source and SEO metadata; existing pages retained. About, Where to Buy and Wholesale assigned to their dedicated templates after finding the generic `page` suffix.
- 441 unique source media URLs mapped to Shopify READY CDN files. No source-host image dependencies in imported recipe bodies.
- Homepage title and description migrated from source to Shopify preferences and verified in rendered HTML. Password protection remains enabled.
- Shopify CLI 5.0.1 Theme Check: 0 errors, 9 inherited Dawn warnings. JavaScript syntax passes. Source staging checks pass for 221 URLs.
- Reduced-motion initialization constructs no animations; section unload/reload and pagehide revert contexts in the local lifecycle check. Browser loaded all four Della scripts deferred, with no recorded JavaScript errors.
- Isolated unpublished QA theme 189343858989: homepage, About, Where to Buy, Wholesale, Contact, catalogue and empty cart reviewed. About/Where to Buy/Wholesale/Contact/catalogue/cart measured at 390, 768 and 1440 px without horizontal overflow or broken visible images. Form controls have labels. Mobile menu opens, Escape closes it, and slideshow controls select exactly one panel.

## Limits and next actions

- All products and recipes remain drafts; six imported pages remain hidden. Source duplicates and policies require review before content publication. Five captured product titles contain the source site-title suffix and should be checked against authenticated product names.
- WordPress `/wp-admin/` redirects to the storefront login; no authenticated admin session is available. Customers/consent, historical orders/refunds, reviews, discounts, hidden variations, SKUs/barcodes, stock, tax, shipping and provider configuration still require authenticated exports. Keep those exports out of this public repository.
- Live product variant selection, add-to-cart, populated cart and checkout cannot be fully verified while the catalogue remains draft. No paid order or contact message was submitted. Contact markup/native required-field validation was inspected; email delivery and hCaptcha completion remain untested.
- Performance review covers deferred motion scripts, eager first/lazy hidden bundled hero images, image loading and responsive geometry. No Lighthouse score, field CWV result or real-user analytics event is claimed. Analytics and consent-provider configuration remain to be reconciled.
- Figma hero visual reference was inspected. Final client copy, team assets and prior design-review decisions are not invented.
- Redirect candidates are prepared but not installed for hidden draft destinations. Review canonical choices in duplicate groups before activation.
- GitHub hosted validation was queued during this review; the same pinned theme checker passed locally. Do not bypass required repository protections.

## Rollback

Horizon 189341139245 remains available as the prior published theme. The import receipt identifies created draft resources for reconciliation. Publication affects Shopify only; DNS/domain cutover, password removal, source deletion and paid orders remain outside this release.
