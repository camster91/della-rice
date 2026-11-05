#!/usr/bin/env python3
"""Plan body-only Shopify recipe patches from a fresh, read-only article snapshot."""
import argparse
import csv
import hashlib
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent
ATTR = re.compile(r"""(?P<prefix>\s)(?P<name>[\w:-]+)\s*=\s*(?P<quote>["'])(?P<value>.*?)(?P=quote)""", re.S)
LEGACY_HOSTS = {"dellarice.com", "www.dellarice.com"}

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

class RecipeBody(HTMLParser):
    def __init__(self, body, title, redirects):
        super().__init__(convert_charrefs=False)
        self.body, self.title, self.redirects = body, title, redirects
        self.offsets = [0, *(m.end() for m in re.finditer("\n", body))]
        self.patches = []
        self.photo = 0

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        line, column = self.getpos()
        start = self.offsets[line - 1] + column
        attributes = dict(attrs)
        if tag == "img":
            self.photo += 1
        image_alt = self.title + (f" — photo {self.photo}" if self.photo > 1 else "")
        shopify_image = tag == "img" and urlsplit(attributes.get("src") or "").hostname == "cdn.shopify.com"

        def replace(match):
            key = match["name"].lower()
            old = html.unescape(match["value"])
            new = old
            if key == "alt" and shopify_image and not old.strip():
                new = image_alt
            if tag == "a" and key == "href":
                parts = urlsplit(old)
                target = self.redirects.get(parts.path.rstrip("/"))
                if target and parts.scheme in ("http", "https") and parts.hostname in LEGACY_HOSTS:
                    new = urlunsplit(("", "", target, parts.query, parts.fragment))
            if new == old:
                return match[0]
            return f'{match["prefix"]}{match["name"]}="{html.escape(new, quote=True)}"'

        updated = ATTR.sub(replace, raw)
        if shopify_image and "alt" not in attributes:
            tail = "/>" if raw.endswith("/>") else ">"
            updated = updated[:-len(tail)] + f' alt="{html.escape(image_alt, quote=True)}"' + tail
        if updated != raw:
            self.patches.append((start, start + len(raw), updated))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def updated(self):
        result = self.body
        for start, end, text in reversed(self.patches):
            result = result[:start] + text + result[end:]
        return result

def make_plan(snapshot, receipt, source, redirects):
    if snapshot.get("store") != receipt["store"]:
        raise ValueError("Snapshot store must match the Della Shopify import receipt.")
    records = snapshot["articles"]
    current = {x["id"]: x for x in records}
    if len(current) != len(records):
        raise ValueError("Snapshot contains duplicate article IDs.")
    jobs, holds, unchanged = [], [], []
    for item in receipt["recipes"]:
        record = current.get(item["id"])
        origin = source[item["source_url"]]
        if (not record or record.get("handle") != item["handle"]
                or record.get("blog_handle") != "recipes"
                or not isinstance(record.get("body_html"), str)
                or not record["body_html"].strip()
                or not isinstance(record.get("title"), str) or not record["title"].strip()
                or not record.get("updated_at")):
            holds.append({"id": item["id"], "reason": "Missing or mismatched recipe snapshot"})
            continue
        old = record["body_html"]
        parser = RecipeBody(old, record["title"], redirects)
        parser.feed(old)
        parser.close()
        new = parser.updated()
        for url in origin.get("video_urls", []):
            parts = urlsplit(url)
            if parts.scheme == "https" and parts.hostname == "youtu.be" and re.fullmatch(r"/[A-Za-z0-9_-]{11}", parts.path):
                video_id = parts.path[1:]
                if video_id not in new:
                    new += f'<p><a href="{html.escape(url, quote=True)}">Watch the recipe video</a></p>'
        if new == old:
            unchanged.append(item["id"])
            continue
        jobs.append({"id": item["id"], "handle": record["handle"],
                     "expected_updated_at": record["updated_at"],
                     "expected_body_sha256": hashlib.sha256(old.encode()).hexdigest(),
                     "body_html": new})
    return {"store": receipt["store"], "status": "planned_not_applied",
            "updates": jobs, "held": holds, "unchanged": unchanged}

def main():
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("snapshot", type=Path, help="JSON with store and articles; see migration README")
    arg.add_argument("output", type=Path, help="New private JSON plan path")
    args = arg.parse_args()
    receipt = read(ROOT / "destination-import-receipt.json")
    source = {r["source_url"]: r for r in read(ROOT / "recipe-import-staging.json")}
    with (ROOT / "shopify-redirects-pending.csv").open(encoding="utf-8", newline="") as csv_file:
        redirects = {r["Redirect from"]: r["Redirect to"] for r in csv.DictReader(csv_file)}
    plan = make_plan(read(args.snapshot), receipt, source, redirects)
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(plan, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(f"{len(plan['updates'])} updates, {len(plan['unchanged'])} unchanged, {len(plan['held'])} held.")

if __name__ == "__main__":
    main()
