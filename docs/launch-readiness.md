# Della Shopify launch readiness

Reviewed 4 November 2026. Destination: della-rice-1hj0pj1j.myshopify.com. Store remains password protected; no DNS cutover or paid order was made.

## Goal and acceptance criteria

A shopper can browse every rice variety, understand the brand and policies, contact Della, search, add products, edit their cart and complete a correctly configured checkout. Launch requires source-data reconciliation, working payments, verified email delivery, approved shipping/tax settings, redirect validation, consent/analytics validation and final public-launch approval.

## Completed and verified

- All 12 imported products are Active and included in Online Store. Existing USD prices, images and 794 g weights retained; no invented SKU, barcode or stock quantity.
- All 12 product URLs render their correct title, canonical URL and enabled Add to cart control. Catalogue groups four varieties in each of All Natural, Organic and Regenerative.
- Representative product gallery, add-to-cart and quantity editing tested: Basmati White at $7, quantity two totals $14 USD. Checkout handoff works. Test cart cleared without creating an order.
- Search for Jasmine returns all three product varieties after indexing.
- Migration notice and all 12 visible Catalogue preview labels removed (PR #6).
- Existing WordPress terms and returns policies copied after checking the public source; contact details and source shipping terms published through native Shopify policies. All five policy links appear in the footer, including existing privacy policy.
- Natural, Organic and Regenerative fact pages made visible. Static product fragments replaced with links to their corresponding live catalogue groups. Duplicate About and legacy sale-sheet pages remain hidden pending review.
- Catalogue, Organic Jasmine product, Regenerative Facts, Contact and empty cart checked at 390, 768 and 1440 px: no horizontal overflow or broken loaded main-content images. Earlier homepage/brand-page responsive checks are recorded in the historical checkpoint.
- Hero uses balanced columns and a naturally proportioned full image; numeric slide selectors removed. Earlier checks covered 390–2560 px.

## Blocked / awaiting owner setup

- Shopify checkout explicitly reports that the store cannot accept payments. Configure the appropriate provider and complete an authorised test order before public launch.
- Notifications sender info@dellarice.com is unverified. Mailbox owner must verify; contact/order delivery still needs end-to-end testing. Existing contact-delivery task remains open.
- WordPress admin session expired. Authenticated exports are needed to reconcile stock, SKUs/barcodes, historical orders/refunds, customers/consent and any private products or variations. Keep private exports outside this public repository.
- Source shipping policy restricts delivery to contiguous USA and describes a qualifying over-$25 promotional free-shipping offer. Reconcile actual zones, rates, discounts and taxes with the owner; default Standard/Express labels alone are insufficient evidence.

## In progress / not yet verified

- 181 imported recipes remain unpublished; review 14 duplicate groups (36 articles) and canonical choices before publication. Do not add a Recipes navigation link until useful articles are published.
- Redirect candidates are prepared, but have not been installed or validated. Activate only destinations that are live, and include policy and recipe mappings after canonical review.
- Consent, analytics/property ownership and conversion events are not verified. No Lighthouse or field performance score is claimed.
- Legal copy was migrated from the existing site; business approval and configuration consistency remain launch requirements.

## Next action and rollback

Complete owner-dependent setup and authenticated reconciliation, finish recipe/redirect checks, verify contact and transactional delivery and an approved checkout test, then obtain public-launch approval. Preserve password protection until then.

Theme changes are tracked in camster91/della-rice. Horizon theme 189341139245 and prior QA themes remain available. Revert the relevant theme commit or republish the retained theme for presentation rollback; product/publication and policy changes must be reconciled separately in admin. Do not delete source WordPress content.
