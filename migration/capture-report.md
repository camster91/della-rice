# Migration capture — 4 November 2026

Completed and verified:

- Captured every URL in the three public WordPress sitemaps: 221 successful reads, zero capture errors.
- 12 products: four All Natural, four Organic and four Regenerative.
- 34 product gallery images with source order and alternative text.
- Exact public descriptions, USD prices, category, source product IDs and 794 g recorded weight for all 12 products; original dimensions retained separately.
- 28 public pages and 181 recipe records, including original metadata, content, images and video links.
- 441 unique same-site media references inventoried for copying to Shopify.
- 14 groups containing 36 recipe URLs have identical text bodies. All records are retained; no deduplication or source deletion was performed.
- Prepared a Shopify product CSV with 12 draft/unpublished product rows and 34 total image rows. Source media URLs still require successful Shopify import/copy.
- Prepared article/page payloads and destination/redirect candidates. Six additional standalone pages and three policies are flagged for review.
- Validated record counts, product IDs/handles, currency, prices, weights, categories, CSV publication state, SEO length limits and stripped executable/form markup.

In progress:

- GSAP/ScrollTrigger visual polish is implemented on the staging branch, with reduced-motion support and a merchant enable/disable setting. JavaScript syntax and Shopify Theme Check pass. Browser visual verification remains pending.

Blocked:

- The connected browser timed out during publication/import work and recovery attempts. The theme has **not** been confirmed published, and none of this capture has been imported into Shopify.
- The connected Shopify API accounts do not identify the Della destination; they must not be used for this migration.
- The public WooCommerce API returned 401. Only ordinary public pages were read. Exact stock counts, missing SKUs/barcodes, unpublished products, customers, orders and coupons require the authenticated WordPress/WooCommerce export.

Next action:

Restore the Browser connection to the Della WordPress and Shopify tabs. Export the authenticated source records, confirm Shopify currency, reconcile/import products and content, then review and deploy the animation changes. The user's theme-publication approval remains valid. Domain/DNS changes have not been performed.
