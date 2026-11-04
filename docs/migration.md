# Migration checklist

Sources inspected 4 November 2026:

- Figma: https://www.figma.com/design/JwrtPMZPn1jchJpwYu4viQ/Della-Redesign
- WordPress: New Home revision 13134, Contact revision 13161, Wholesale revision 13117, About revision 13344 and Where to Buy revision 13343.
- Shopify: della-rice-1hj0pj1j; initial theme Horizon 189341139245. Initial product catalogue empty.

## Theme configuration

Connect `camster91/della-rice`, branch `main`, as an unpublished theme. Create pages with handles and templates:

| Handle | Template |
| --- | --- |
| about | page.about |
| where-to-buy | page.where-to-buy |
| wholesale | page.wholesale |
| contact | page.contact |

The standard page handles render editable Della section groups directly, so draft pages do not depend on publishing a theme just to select its templates. The named templates are retained for use on additional page handles.

Each Della section supports editing, removal and reordering in the theme editor. Image slots accept merchant image uploads and otherwise use bundled source assets. Configure a real menu in the header section when required; default navigation covers the four pages and rice catalogue.

## Required before launch

- Import the 12 WooCommerce products, preserving verified descriptions, images, SKUs, variant IDs/attributes and weight. Set product type or tags to `All Natural`, `Organic`, or `Regenerative`. Catalogue preview is a design aid and cannot be purchased.
- Verify selling currency (source prices are USD), pricing, inventory, availability, tax, shipping, payment providers and fulfilment. Customer and order migration are separate, unperformed work.
- Supply approved package nutrition/cooking content. Product pages render actual Shopify product content and do not invent package claims.
- Verify store notification sender/recipient and submit one explicitly authorised contact-form test. No test message has been sent.
- Supply a licensed Recoleta webfont for the serif homepage headings; Georgia is currently the fallback. Confirm the final typography choice from the older review board.
- Supply verified retailer data or a locator URL. Default contact route is functional; no fake store results are shown.
- Review final copy, staff names/photos, business address/phone/email and legal policies. Unapproved merchandise is omitted.
- Check mobile (390), tablet (768), desktop (1440), keyboard navigation, image proportions, forms, unavailable variants, add to cart, quantity changes, discounts and checkout handoff with real products.
- Confirm canonical metadata, products' structured data, indexability, analytics consent and no duplicate analytics installation. No custom analytics was added.

## Redirect map to prepare

WordPress `/product/{handle}/` → Shopify `/products/{handle}` once handles are confirmed. `/store/` and `/shop/` → `/collections/all`; `/about/` and `/about-us/` → `/pages/about`; `/contact-us/` → `/pages/contact`; `/where-to-buy/` → `/pages/where-to-buy`; `/wholesale/` → `/pages/wholesale`. Inventory all public URLs and recipes first; no redirects have been installed.

## Launch and rollback

Keep WordPress and its DNS unchanged until merchant approval, redirect coverage and commerce testing are complete. Back up WordPress and confirm Shopify domain/SSL readiness. Publish the approved Shopify theme and change the domain only with explicit approval. Record the prior DNS values and previous live theme; restore them if launch smoke tests fail. Avoid introducing new orders during an unresolved dual-store cutover.
