# Content completion preparation

Prepared from the existing public WordPress capture and Shopify import receipt. This is migration preparation, not evidence of a new Shopify publication.

Run `python migration/prepare-content-completion.py` (requires Beautiful Soup). The script performs no network writes and creates `migration/content-completion-articles.json` plus audit inventories and redirect candidates.

- 181 existing article IDs receive proposed lossless content updates and publication requests.
- 159 distinct recipe texts; 14 repeated-text groups. Every source article is retained because differing image URLs still need visual comparison. No article is deleted or silently consolidated.
- 402 image placements rewritten to the existing Shopify CDN mapping; missing image alt text gets the recipe title and a photo number. Recipe copy remains unchanged.
- Existing captured recipe-video links are appended where absent from the body.
- 28 source page records are classified, including legacy review/mockup and native commerce/account routes. Classification does not mean every unique paragraph has been merged into the new design.
- Source recipe/product/page links map to destination URLs. Redirect CSV remains prepared and uninstalled. Do not activate redirects before verifying their destinations are available.

## Validation performed

Builder executed successfully, all 181 receipt IDs matched uniquely, every prepared article has a title/body, no prepared recipe image retains a WordPress upload URL, and no unresolved source link was found in the prepared recipe bodies. Python compilation and diff whitespace checks passed.

## Execution still required

Authenticate Shopify specifically for Della. Read existing articles and compare to the original import before updating so later human edits are preserved. Apply, read back and publish the prepared content; verify videos, media, mobile/desktop recipe layouts, blog pagination and navigation. Review duplicate images before deciding whether to consolidate URLs. Verify the three remaining hidden legacy pages against the redesigned About/catalogue/wholesale equivalents. Install and test redirects only after destination validation. Authenticated WordPress content outside the public capture remains unknown until access is restored.

## Shopify progress and next import

All 181 imported recipe articles were verified visible in the password-protected store. The prepared article body edits are still pending. Four legacy paths were tested in Chrome: `/recipes`, `/about-us`, `/contact-us`, and `/find-us`. Shopify saved a fifth rule for `/shop`, but the storefront rendered the homepage there. Keep that path out of the bulk upload while it is investigated.

Import [shopify-redirects-pending.csv](../migration/shopify-redirects-pending.csv) in Shopify under **Content → Menus → URL redirects → Import**. It contains 204 unique source paths, excludes the five already saved rules, and contains no redirect chains within the batch. After import, check the processed count and sample a recipe, a product and a policy URL on the Shopify domain.

Keep `/regenfacts`, `/ricefacts` and `/sellsheets` out of this import. The first two reuse About content and the last contains static prices and merchandise headings. The WordPress About capture also lists Dalton Drye and gives Tammy Roberts a different role than the current Shopify About page. Confirm staff details before consolidating the legacy About copy.
