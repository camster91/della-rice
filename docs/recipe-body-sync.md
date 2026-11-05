# Della Rice Shopify recipe body sync

This workflow builds on PR #8 at `2873de55836138d1b59766d6e2cdfc54d82b02a9`. It targets existing articles in the Recipes blog at `della-rice-1hj0pj1j.myshopify.com`. It submits the prepared HTML exactly, including CDN images, alt text and video links. The receipt provides the source URL, article ID and handle. The only mutation field is the body. Draft and published states, publication dates, handles, titles, featured images, blog assignments and tags are preserved. The preparation file's publication request is ignored.

## Prepare and reconcile

1. Apply the patch on the PR #8 branch or a branch containing it. Use Python 3.10 or later on Linux or macOS. Install Beautiful Soup in a virtual environment and generate the prepared payload.

   ```bash
   python -m venv /path/outside/repository/della-venv
   source /path/outside/repository/della-venv/bin/activate
   python -m pip install beautifulsoup4
   python migration/prepare-content-completion.py
   python -m unittest discover -s migration -p 'test_sync_recipe_bodies.py'
   ```

2. Use a Della Shopify Admin API token with `read_content` (or `read_online_store_pages`) for the live dry run. Inject it as `DELLA_SHOPIFY_ADMIN_TOKEN` using your private secret mechanism. Apply also needs `write_content` or `write_online_store_pages`. Run where the Shopify Admin API endpoint is reachable.
3. Recover trusted per-article Shopify readback evidence from the original import or a historical snapshot captured after any known, approved intervening changes. The checked-in receipt records identities and historical visibility but has no per-article body hash or revision timestamp. Its date and aggregate verification result cannot establish the baseline. A new Shopify read or the current WordPress capture cannot serve as historical evidence. If evidence is missing or a merchant edited an article, reconcile it individually with the merchant before considering a separate change.
4. Create a private baseline JSON file outside the checkout. Use a descriptive provenance and include only entries backed by historical evidence. For each entry, hash the exact historical Shopify Admin GraphQL `body` string encoded as UTF-8, without formatting or normalization. Copy `updatedAt` exactly as returned. The format below shows one illustrative entry.

   ```json
   {
     "store": "della-rice-1hj0pj1j.myshopify.com",
     "provenance": "Original import Admin API readback, retained in private storage",
     "articles": [
       {
         "id": "gid://shopify/Article/1",
         "source_url": "https://dellarice.com/recipe/example/",
         "body_sha256": "<64 lowercase hex characters>",
         "updatedAt": "2026-11-04T13:00:00Z"
       }
     ]
   }
   ```

## Generate and review the exact proposal

Create a fresh batch directory under an existing private parent outside the checkout. For initial triage, omit `--baseline` to inventory already-matching articles and identify rows needing evidence. With a baseline, begin with one eligible recipe.

```bash
python migration/sync-recipe-bodies.py dry-run \
  --out /private/della/batch-001 \
  --baseline /private/della/import-baseline.json \
  --limit 1
```

Review `plan.json` and `body.diff` privately. The plan lists every recipe and includes exact before/after HTML for the proposed batch. The diff quotes each HTML line to expose whitespace and line endings. A proposal needs a matching receipt ID, handle, blog, historical body hash and historical revision timestamp. Changed or missing destinations are excluded. Articles already matching the prepared HTML require no write. Eligible articles beyond the limit are deferred. Keep the reviewed files and obtain Cameron's explicit approval for the exact batch and plan SHA-256. Keep the historical baseline, plans, diffs, backups, logs and credentials out of GitHub.

## Apply only after approval

Arrange an exclusive recipe editing window. Pause staff edits and any other integrations that can update these articles, and run one apply at a time. Shopify's article update has no conditional revision argument. An immediate re-read reduces the risk of a concurrent edit, and the editing freeze covers the remaining interval between read and write.

```bash
python migration/sync-recipe-bodies.py apply \
  --out /private/della/batch-001 \
  --baseline /private/della/import-baseline.json \
  --approved-sha256 APPROVED_SHA256 \
  --confirm-edit-freeze
```

Apply first checks the whole batch against the reviewed snapshots, then processes articles sequentially. Each write is preceded by a durable private backup and an attempt record. Each success has an independent readback that must match the exact approved body and preserve the selected metadata. The batch stops at the first failure. Mutations are never automatically retried. Reads retry bounded transient failures.

If interrupted, inspect the per-article `.before.json`, `.attempt.json`, and `.verified.json` files. Confirm no process is active before clearing a stale `apply.lock`. A rerun of the same approved plan skips an exact desired body with unchanged metadata. A prior attempt marker blocks another mutation from that plan if the old body remains. Reconcile the live article against the backup and approved HTML before creating a fresh plan. If restoration is needed, review a body-only restoration separately using the backup and current revision. The tool performs no automatic rollback.

## Close out

After an approved pilot, preview the recipe in Shopify and verify images, video links, internal links and layout at representative phone, tablet and desktop widths. Repeat the dry run and approval for each batch. Review blocked recipes with the merchant and preserve all recipe identities while duplicate-media decisions remain open.

Separately reconcile the 28 captured pages against their Shopify destinations, verify product completeness and visibility, and reconcile any in-scope private commerce exports. Obtain separate approval for visibility or publication changes, redirects, and cutover. Before launch, verify redirect destinations, navigation, SEO, cart and checkout, forms, and analytics and consent.

Shopify references

- [Article fields](https://shopify.dev/docs/api/admin-graphql/2026-10/objects/Article)
- [Article update mutation](https://shopify.dev/docs/api/admin-graphql/2026-10/mutations/articleUpdate)
