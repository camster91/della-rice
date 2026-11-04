# WooCommerce → Shopify migration staging

This folder contains public-source migration records and a reproducible, read-only extractor. No Shopify import has been performed by the extractor.

## Source data

`products.json` preserves source product IDs, handles, exact public names, descriptions, USD prices, categories, package weight, recorded dimensions, gallery order/alt text, availability and SEO metadata. Missing SKUs, barcodes or private stock counts stay unknown; filenames are not treated as SKUs.

`pages.json` and `recipes.json` preserve public page content, image/video references, original metadata and source URLs. WordPress forms, scripts, cart widgets and styling are stripped from the proposed rich text. Recipe video links are retained. This is source capture, not approval to publish duplicate recipes or placeholder review content.

`recipe-duplicate-groups.json` identifies identical text bodies for review. No source recipe is deleted. `redirect-candidates.csv` is a staging map: install a mapping only after its Shopify destination exists. Review duplicates before choosing canonical destinations.

## Import sequence

1. Confirm that the destination is `della-rice-1hj0pj1j.myshopify.com` and its selling currency is USD. Export/back up any existing Shopify products first.
2. Reconcile an authenticated WooCommerce export to include unpublished products, exact stock counts, SKU/barcode data, product tax status and any unexposed variants. The public API returned 401; this extractor only reads ordinary public pages and never bypasses that restriction.
3. Import `products-draft-USD.csv` without overwriting existing matching handles. Every first row sets `Status=draft` and `Published on online store=false`. Source gallery URLs are used so Shopify copies the images to its own CDN. Product types and one collection per product follow the public source categories. Source weight is preserved; no package dimensions are assumed to be shipping-box measurements.
4. Reconcile product count, USD prices, gallery images, SKUs, weights and inventory with the source. Inventory, tax, fulfilment and provider connections still require verified settings. Do not activate products until these checks pass.
5. Create a Recipes blog and migrate reviewed recipe records as draft articles, preserving handles and videos. Upload/copy page and recipe media to Shopify, then replace every source-domain image URL. Rewrite internal source links using the verified redirect map. Review duplicate recipe groups first.
6. Migrate useful standalone pages and approved legal copy. Do not import old cart/checkout/account forms, review duplicates or WordPress admin pages as static Shopify content.
7. Customers, orders, refunds, coupons, shipping/tax rules and payment credentials are not in public pages. Obtain authenticated exports and reconcile their supported Shopify equivalents. Never commit private exports to this public repository. Passwords and provider secrets must not be copied into theme files.
8. Review the migrated store and animations before merging the staging branch into the theme's connected branch. Publishing the existing theme was approved by the user, but was not completed while the browser connection was unavailable. Domain/DNS cutover remains a separate launch step.

Official CSV reference: https://help.shopify.com/en/manual/products/import-export/using-csv

The CSV uses current Shopify headings. SKU, barcode, inventory-quantity, tax and cost columns are omitted when the public source cannot verify them, rather than filling in guesses. A CSV does not carry a selling-currency field, so the USD destination check is mandatory before import.
