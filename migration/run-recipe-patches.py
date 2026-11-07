#!/usr/bin/env python3
"""Read Della recipe bodies or verify and apply a prepared body-only patch plan."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parent
STORE = "della-rice-1hj0pj1j.myshopify.com"
ENDPOINT = f"https://{STORE}/admin/api/2026-10/graphql.json"
READ_ARTICLE = """
query ReadRecipe($id: ID!) {
  article(id: $id) { id handle title updatedAt body blog { handle } }
}
"""
WRITE_BODY = """
mutation UpdateRecipeBody($id: ID!, $article: ArticleUpdateInput!) {
  articleUpdate(id: $id, article: $article) {
    article { id }
    userErrors { field }
  }
}
"""

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def request_graphql(token, query, variables=None):
    request = Request(
        ENDPOINT, method="POST",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token},
    )
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Shopify returned HTTP {exc.code}.") from None
    except (URLError, TimeoutError, ValueError):
        raise RuntimeError("Shopify response could not be read. Check the article before retrying.") from None
    if payload.get("errors") or not isinstance(payload.get("data"), dict):
        raise RuntimeError("Shopify returned a GraphQL error. Check authentication and article scopes.")
    return payload["data"]

def read_article(api, expected):
    article = api(READ_ARTICLE, {"id": expected["id"]}).get("article")
    if (not article or article.get("id") != expected["id"]
            or article.get("handle") != expected["handle"]
            or (article.get("blog") or {}).get("handle") != "recipes"
            or not isinstance(article.get("body"), str) or not article.get("updatedAt")):
        raise RuntimeError(f"Recipe identity or body did not match for {expected['id']}.")
    return article

def snapshot(api, recipes):
    return {"store": STORE, "articles": [
        {"id": a["id"], "handle": a["handle"], "blog_handle": a["blog"]["handle"],
         "title": a["title"], "updated_at": a["updatedAt"], "body_html": a["body"]}
        for a in (read_article(api, r) for r in recipes.values())
    ]}

def apply(api, plan, recipes, limit, write):
    updates = plan["updates"]
    ids = [r["id"] for r in updates]
    if plan["store"] != STORE or plan["status"] != "planned_not_applied" or len(set(ids)) != len(ids):
        raise RuntimeError("Unexpected store, plan status, or duplicate article IDs.")
    for job in updates:
        known = recipes.get(job["id"])
        if not known or job["handle"] != known["handle"] or not job["body_html"].strip():
            raise RuntimeError("Plan contains an unknown recipe or empty body.")
    counts = {"ready": 0, "applied": 0, "already_current": 0, "held": 0}
    for job in updates:
        if counts["applied"] >= limit:
            break
        current = read_article(api, job)
        if current["body"] == job["body_html"]:
            counts["already_current"] += 1
            continue
        digest = hashlib.sha256(current["body"].encode()).hexdigest()
        if (digest != job["expected_body_sha256"]
                or current["updatedAt"] != job["expected_updated_at"]):
            counts["held"] += 1
            print(f"Held {job['id']}: changed since snapshot.", flush=True)
            continue
        if not write:
            counts["ready"] += 1
            continue
        print(f"Applying {job['id']}.", flush=True)
        result = api(WRITE_BODY, {"id": job["id"], "article": {"body": job["body_html"]}})["articleUpdate"]
        if result["userErrors"] or (result.get("article") or {}).get("id") != job["id"]:
            raise RuntimeError(f"Shopify did not confirm update for {job['id']}.")
        if read_article(api, job)["body"] != job["body_html"]:
            raise RuntimeError(f"Readback differed for {job['id']}. Review this record before resuming.")
        counts["applied"] += 1
        print(f"Verified {job['id']}.", flush=True)
    return counts

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_subparsers(dest="mode", required=True)
    read = mode.add_parser("snapshot")
    read.add_argument("output", type=Path)
    sync = mode.add_parser("apply")
    sync.add_argument("plan", type=Path)
    sync.add_argument("--write", action="store_true", help="Apply and read back each verified change")
    sync.add_argument("--limit", type=int, default=20, help="Maximum writes in this run")
    args = parser.parse_args()
    token = os.environ.get("DELLA_SHOPIFY_ADMIN_TOKEN")
    if not token:
        parser.error("DELLA_SHOPIFY_ADMIN_TOKEN is required in the local environment.")
    if args.mode == "apply" and args.limit < 1:
        parser.error("--limit must be positive.")
    receipt = json.loads((ROOT / "destination-import-receipt.json").read_text())
    if receipt["store"] != STORE:
        raise RuntimeError("Unexpected store in the import receipt.")
    recipes = {x["id"]: x for x in receipt["recipes"]}
    def api(query, variables=None):
        return request_graphql(token, query, variables)
    shop = api("query DellaShop { shop { myshopifyDomain } }")["shop"]
    if shop["myshopifyDomain"] != STORE:
        raise RuntimeError("Token did not identify the Della Shopify store.")
    if args.mode == "snapshot":
        data = snapshot(api, recipes)
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
            out.write("\n")
        print(f"Read {len(data['articles'])} recipes.")
    else:
        plan = json.loads(args.plan.read_text())
        print(json.dumps(apply(api, plan, recipes, args.limit, args.write)))

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        sys.exit(str(error))
