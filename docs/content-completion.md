# Content completion preparation

Prepared from the existing public WordPress capture and Shopify import receipt. This is migration preparation, not evidence of a new Shopify publication.

Run `python migration/prepare-content-completion.py` (requires Beautiful Soup). The script performs no network writes and creates `migration/content-completion-articles.json` plus audit inventories and redirect candidates.

- 181 existing article IDs receive proposed lossless content updates and publication requests.
- 159 distinct recipe texts; 14 repeated-text groups. Every source article is retained because differing image URLs still need visual comparison. No article is deleted or silently consolidated.
- 402 image placements rewritten to the existing Shopify CDN mapping; missing image alt text gets the recipe title and a photo number. Recipe copy remains unchanged.
- Existing captured recipe-video links are appended where absent from the body.
- 28 source page records are classified, including legacy review/mockup and native commerce/account routes. Classification does not mean every unique paragraph has been merged into the new design.
- Source recipe/product/page links map to destination URLs. The 204-row redirect batch was imported and spot checked in Shopify.

## Validation performed

Builder executed successfully, all 181 receipt IDs matched uniquely, every prepared article has a title/body, no prepared recipe image retains a WordPress upload URL, and no unresolved source link was found in the prepared recipe bodies. Python compilation and diff whitespace checks passed.

## Verified Shopify changes

- All 181 imported recipes are visible on the password-protected storefront. Four recipes have verified manual image alt text updates: Cajun Lemon Butter Tilapia with Jasmine Rice, 3 Beans and Brown Basmati Rice Salad (the -2 URL), Cajun Jambalaya, and Wintry Citrus Rice and Quinoa Salad.
- Shopify confirmed 204 redirects added. Legacy Basmati White Rice, Wintry Citrus Rice and Quinoa Salad, and the refund policy URLs landed on their correct targets. Separate checks confirmed /recipes, /about-us, /contact-us, /find-us, /ricefacts, and /sellsheets. PR #10 supplies a verified browser redirect for /shop to the catalogue. It does not return an HTTP 301.
- New Spirit Medium is active on Shopify headings. Bianca was asked to review weight and spacing. Micah received the password-protected Shopify preview URL.
- The current About page shows Tammy Roberts as Quality Assurance Manager, as Stephen requested. Dalton is absent from the page, consistent with Tiffany's removal request.

## Commerce data reconciliation

All 12 WooCommerce product names and prices match the Shopify catalogue. Each WooCommerce product is in stock with blank SKU and barcode fields and no quantity tracking. All 12 Shopify products are active with inventory tracking off.

WooCommerce shows 50 customers and 57 orders: 40 Processing, 16 Completed, and one Refunded. Shopify's order list is empty. Processing is the source status and does not establish fulfilment state. Reconcile these records against fulfilment before cutover. Obtain the client's decision on whether historical records should stay accessible in WooCommerce or move to Shopify. Keep customer and order exports out of this public repository.

## Execution still required

- Resume authenticated Shopify access. Compare the current article HTML to the original import before applying prepared changes. Preserve newer edits and the verified manual changes. Verify recipe alt text, source video links, and internal links after writes. Preserve all 14 repeated-text groups until the differences in media are reviewed.
- Confirm the store owner can move the development store to a live plan and activate payments. Run a test order, check shipping and tax totals, and verify contact and order notifications after sender verification.
- Della needs to confirm the old over-$25 shipping offer. Shopify currently shows USD 8 Standard, free from USD 70, and USD 15 Express. Verify shipping coverage and tax settings with the approved policy.
- Shopify Customer Events showed no connected pixels. The old WordPress Rank Math analytics page showed a connection prompt. Identify the intended analytics property, verify consent, and confirm purchase tracking with a test order.
- Get final launch approval after the above checks. Keep the legacy store available as a source and rollback reference through cutover.

## Plan from Shopify readback

Use `python migration/plan-recipe-patches.py /private/article-snapshot.json /private/recipe-patch-plan.json` once a fresh authenticated readback is available. The snapshot is an object with `store` and `articles`. Each article needs `id` (matching the receipt), `handle`, `blog_handle`, `title`, `updated_at` and `body_html`.

The planner edits current article HTML in place. It fills missing Shopify CDN image alt text, rewrites links covered by the imported redirect batch, and adds missing captured short YouTube links. It leaves existing descriptions, editor copy, and visibility intact. It holds missing or mismatched records. Before applying a job, re-read the current article and compare both its update time and body hash with the expected values. Regenerate the plan if either changed. The planner does not call Shopify or publish anything.
