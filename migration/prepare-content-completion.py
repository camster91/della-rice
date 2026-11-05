#!/usr/bin/env python3
"""Prepare lossless content updates from the captured source; performs no network writes."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent

def read(name):
    return json.loads((ROOT / name).read_text())

def save(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

recipes = read('recipe-import-staging.json')
pages = read('page-import-staging.json')
receipt = read('destination-import-receipt.json')
media = read('media-cdn-map.json')
ids = {x['source_url']: x['id'] for x in receipt['recipes']}
paths = {urlsplit(x['source_url']).path.rstrip('/') or '/': x['destination_path']
         for x in recipes + pages if x['destination_path']}
for x in read('products.json'):
    paths[urlsplit(x['source_url']).path.rstrip('/')] = '/products/' + x['handle']
paths.update({'/shop': '/collections/all', '/cart': '/cart', '/checkout': '/checkout'})
unresolved = []

def rewrite(value, owner):
    absolute = urljoin(owner, value)
    parts = urlsplit(absolute)
    if parts.hostname not in ('dellarice.com', 'www.dellarice.com'):
        return value
    key = absolute.split('#')[0].split('?')[0]
    if key in media:
        return media[key]['url'] + ('#' + parts.fragment if parts.fragment else '')
    target = paths.get(parts.path.rstrip('/') or '/')
    if target:
        return target + ('?' + parts.query if parts.query else '') + ('#' + parts.fragment if parts.fragment else '')
    unresolved.append({'owner': owner, 'url': absolute})
    return value

updates = []
text_groups = {}
for item in recipes:
    source = item['source_url']
    soup = BeautifulSoup(item['body_html'], 'html.parser')
    fingerprint = hashlib.sha256(' '.join(soup.stripped_strings).encode()).hexdigest()
    text_groups.setdefault(fingerprint, []).append(source)
    for node in soup.find_all(True):
        for attr in ('src', 'href', 'poster'):
            if node.get(attr):
                node[attr] = rewrite(node[attr], source)
    for index, image in enumerate(soup.find_all('img'), 1):
        if not image.get('alt', '').strip():
            image['alt'] = item['title'] + (' — photo ' + str(index) if index > 1 else '')
    for video in item.get('video_urls', []):
        if not any(link.get('href') == video for link in soup.find_all('a')):
            p = soup.new_tag('p')
            a = soup.new_tag('a', href=video)
            a.string = 'Watch the recipe video'
            p.append(a)
            soup.append(p)
    updates.append({'id': ids[source], 'source_url': source, 'destination_path': item['destination_path'],
                    'title': item['title'], 'body_html': str(soup), 'requested_is_published': True,
                    'duplicate_media_review': item['duplicate_review_required'],
                    'execution_status': 'prepared_not_applied'})

save('content-completion-articles.json', updates)
duplicates = [{'text_sha256': key, 'source_urls': urls,
               'decision': 'Preserve all imported articles; repeated text does not prove images are interchangeable.'}
              for key, urls in text_groups.items() if len(urls) > 1]
save('content-completion-duplicates.json', duplicates)
page_inventory = [{'source_url': p['source_url'], 'destination_path': p['destination_path'],
                   'action': p['migration_action'], 'captured_html_bytes': len(p['body_html'].encode()),
                   'note': 'Native commerce/account functionality replaces source dynamic page.'
                   if p['source_handle'] in ('cart', 'checkout', 'my-account') else
                   'Preserve source capture; verify unique copy against the destination before closing.'}
                  for p in pages]
save('content-completion-pages.json', page_inventory)
with (ROOT / 'content-completion-redirects.csv').open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Redirect from', 'Redirect to'])
    for source, target in sorted(paths.items()):
        if source != '/' and source != target:
            writer.writerow([source + '/', target])
summary = {'execution_status': 'prepared_not_applied', 'store': receipt['store'],
           'article_updates': len(updates), 'distinct_recipe_texts': len(text_groups),
           'duplicate_text_groups': len(duplicates), 'source_page_records': len(page_inventory),
           'rewritten_image_count': sum(len(BeautifulSoup(x['body_html'], 'html.parser').find_all('img')) for x in updates),
           'unresolved_source_links': sorted({x['url'] for x in unresolved}),
           'unresolved_link_occurrences': unresolved,
           'next_action': 'Authenticate Della Shopify, read existing article bodies to detect later edits, apply updates, read back, publish and validate redirects. Do not overwrite newer edits.'}
save('content-completion-summary.json', summary)
assert len(updates) == len(receipt['recipes']) == len({x['id'] for x in updates})
assert all(x['body_html'] and x['title'] for x in updates)
assert not any('dellarice.com/wp-content/' in img.get('src', '')
               for x in updates for img in BeautifulSoup(x['body_html'], 'html.parser').find_all('img'))
print(json.dumps({k: v for k, v in summary.items() if k not in ('unresolved_link_occurrences',)}, indent=2))
