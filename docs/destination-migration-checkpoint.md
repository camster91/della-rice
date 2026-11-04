# Destination migration checkpoint

Store verified: `della-rice-1hj0pj1j.myshopify.com`. Currency verified: USD.

- 12 source products imported as drafts. No SKUs, barcodes or inventory quantities invented. Original WooCommerce IDs are saved in tags and `della_migration.source` JSON metadata.
- 181 recipes imported as unpublished articles in the Recipes blog. All 181 texts, image URLs and links match staging after CDN rewriting and HTML normalisation. All 181 source URLs read back successfully. 36 recipes in 14 duplicate groups are tagged for review.
- Six new standalone pages imported hidden. Existing Contact, About, Where to Buy and Wholesale pages were preserved. Three policies remain for merchant review; old cart/checkout/account pages were excluded.
- All 441 distinct source media URLs have Shopify READY image records and CDN mappings. Product galleries preserve 34 source references, including source duplicates.
- Original SEO is retained in source metadata and native SEO fields where applicable. One whitespace-only recipe SEO description was omitted from the native field, preserving its original in source metadata.
- Target theme 189341761837 remains unpublished. Horizon 189341139245 remains live. QA copy 189343858989 isolates PR animation testing from the GitHub-connected theme.

## Remaining authenticated WordPress data

Export products/variations including unpublished records, real SKUs/barcodes, inventory, tax and shipping settings. Export customers with marketing consent, orders/refunds, reviews and coupons through authenticated admin tooling. Reconnect payment/fulfilment/tax providers independently; never commit credentials or private exports to this public repository. WordPress passwords are not transferable to Shopify customer authentication.

## Release gate

Merge and publication remain pending representative desktop, tablet and mobile QA, theme checks and PR review. Keep products and recipes in draft, storefront password protection enabled, source data intact and DNS unchanged. Draft products do not provide a complete live cart/checkout test.

## Recovery

The migration receipt identifies only records created in this run. Keep them hidden while reconciling exports. Horizon remains available as the prior theme for publication rollback. Do not delete source or destination data to roll back without explicit approval.
