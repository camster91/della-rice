#!/usr/bin/env python3
"""Plan and apply explicitly approved Della Rice recipe body updates."""
import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parent
STORE = 'della-rice-1hj0pj1j.myshopify.com'
API_VERSION = '2026-10'
MAX_BATCH = 20
GID = re.compile(r'gid://shopify/Article/[0-9]+')
SHA = re.compile(r'[0-9a-f]{64}')
FIELDS = '''
  id handle title body createdAt updatedAt isPublished publishedAt
  blog { id handle }
  summary tags templateSuffix image { url altText }
'''
READ = '''
query ReadRecipe($id: ID!) {
  node(id: $id) { __typename ... on Article { ''' + FIELDS + ''' } }
}
'''
UPDATE = '''
mutation UpdateRecipeBody($id: ID!, $body: HTML!) {
  articleUpdate(id: $id, article: {body: $body}) {
    article { id }
    userErrors { field message }
  }
}
'''
SHOP = 'query VerifyStore { shop { myshopifyDomain } }'


class SyncError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Shopify:
    def __init__(self, token):
        self.token = token
        self.opener = build_opener(NoRedirect())

    def graphql(self, query, variables, *, write=False):
        request = Request(
            f'https://{STORE}/admin/api/{API_VERSION}/graphql.json',
            json.dumps({'query': query, 'variables': variables}).encode(),
            {'Content-Type': 'application/json', 'X-Shopify-Access-Token': self.token},
        )
        attempts = 1 if write else 4
        for attempt in range(attempts):
            try:
                with self.opener.open(request, timeout=25) as response:
                    if response.headers.get('X-Shopify-API-Version') != API_VERSION:
                        raise SyncError('Unexpected Shopify API version.')
                    result = json.load(response)
                errors = result.get('errors', [])
                if not errors and isinstance(result.get('data'), dict):
                    return result['data']
                retry = bool(errors) and all(
                    error.get('extensions', {}).get('code') == 'THROTTLED' for error in errors
                )
                message = 'Shopify throttled the request.' if retry else 'Shopify GraphQL request failed.'
            except HTTPError as error:
                retry = error.code in (429, 500, 502, 503, 504)
                message = f'Shopify HTTP {error.code}.'
            except (URLError, TimeoutError, OSError, ValueError):
                retry = True
                message = 'Shopify transport or response failure.'
            if not retry or attempt + 1 == attempts:
                raise SyncError(message)
            time.sleep(2 ** attempt)

    def verify_store(self):
        if self.graphql(SHOP, {})['shop']['myshopifyDomain'] != STORE:
            raise SyncError('Shopify store identity mismatch.')

    def read(self, article_id):
        node = self.graphql(READ, {'id': article_id})['node']
        if node is not None and node.pop('__typename') != 'Article':
            raise SyncError('Destination node is not an article.')
        return node

    def update(self, article_id, body):
        result = self.graphql(UPDATE, {'id': article_id, 'body': body}, write=True)['articleUpdate']
        if result['userErrors'] or (result['article'] or {}).get('id') != article_id:
            raise SyncError('Shopify rejected the update or returned an unexpected article.')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def body_hash(body):
    return digest(body.encode('utf-8'))


def read_json(path):
    return json.loads(path.read_bytes())


def private_write(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as file:
        file.write(data)
        file.flush()
        os.fsync(file.fileno())
    # Persist the directory entry before any remote write.
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def index_rows(rows):
    by_id = {}
    sources = set()
    for row in rows:
        article_id = row['id']
        source = row['source_url']
        if not GID.fullmatch(article_id) or not source or source in sources or article_id in by_id:
            raise SyncError('Invalid or duplicate article identity in migration input.')
        by_id[article_id] = row
        sources.add(source)
    return by_id


def load_inputs(baseline_path):
    receipt = read_json(ROOT / 'destination-import-receipt.json')
    if receipt['store'] != STORE:
        raise SyncError('Receipt store mismatch.')
    recorded = index_rows(receipt['recipes'])
    prepared = index_rows(read_json(ROOT / 'content-completion-articles.json'))
    if not recorded or recorded.keys() != prepared.keys():
        raise SyncError('Prepared articles and receipts have different ID sets.')
    for article_id, row in prepared.items():
        original = recorded[article_id]
        if (row['source_url'] != original['source_url']
                or row['destination_path'] != f"/blogs/recipes/{original['handle']}"
                or row['execution_status'] != 'prepared_not_applied'
                or not row['body_html'].strip()):
            raise SyncError('Prepared article does not match its receipt.')
    baseline = {}
    if baseline_path:
        evidence = read_json(baseline_path)
        if evidence['store'] != STORE or not evidence['provenance'].strip():
            raise SyncError('Baseline requires the Della store and historical provenance.')
        baseline = index_rows(evidence['articles'])
        for article_id, row in baseline.items():
            if (article_id not in recorded or row['source_url'] != recorded[article_id]['source_url']
                    or not SHA.fullmatch(row['body_sha256'])
                    or not isinstance(row['updatedAt'], str) or not row['updatedAt']):
                raise SyncError('Invalid historical baseline entry.')
    return recorded, prepared, baseline


def classify(current, original, proposed, evidence):
    if current is None:
        return 'missing'
    if (current['id'] != original['id'] or current['handle'] != original['handle']
            or current['blog']['handle'] != 'recipes'):
        return 'identity_conflict'
    if current['body'] == proposed['body_html']:
        return 'already_matches'
    if evidence is None:
        return 'baseline_missing'
    if (body_hash(current['body']) != evidence['body_sha256']
            or current['updatedAt'] != evidence['updatedAt']):
        return 'destination_changed'
    return 'eligible'


def make_plan(api, inputs, limit):
    receipts, prepared, baseline = inputs
    rows = []
    changes = []
    for article_id, original in receipts.items():
        current = api.read(article_id)
        proposed = prepared[article_id]
        status = classify(current, original, proposed, baseline.get(article_id))
        if status == 'eligible':
            if len(changes) < limit:
                status = 'proposed'
                changes.append({'id': article_id, 'before': current, 'body': proposed['body_html']})
            else:
                status = 'deferred'
        rows.append({'id': article_id, 'source_url': original['source_url'],
                     'destination_path': proposed['destination_path'], 'status': status})
    return {'version': 1, 'store': STORE, 'api_version': API_VERSION,
            'articles': rows, 'changes': changes}


def diff_bytes(plan):
    diff = []
    for change in plan['changes']:
        article_id = change['id']
        # JSON quoting keeps every line ending and invisible character reviewable.
        before = [json.dumps(line, ensure_ascii=False) + '\n'
                  for line in change['before']['body'].splitlines(keepends=True)]
        after = [json.dumps(line, ensure_ascii=False) + '\n'
                 for line in change['body'].splitlines(keepends=True)]
        diff.extend(difflib.unified_diff(before, after, f'{article_id} before', f'{article_id} after'))
    return ''.join(diff).encode('utf-8')


def unchanged_metadata(before, after):
    return after is not None and all(
        after.get(field) == value for field, value in before.items()
        if field not in ('body', 'updatedAt')
    )


def apply_plan(api, inputs, plan, out):
    receipts, prepared, baseline = inputs
    changes = plan['changes']
    ids = [change['id'] for change in changes]
    if (plan['version'] != 1 or plan['store'] != STORE or plan['api_version'] != API_VERSION
            or not 1 <= len(ids) <= MAX_BATCH or len(set(ids)) != len(ids)):
        raise SyncError('Invalid approval plan or batch size.')

    for change in changes:
        article_id = change['id']
        original = receipts[article_id]
        proposed = prepared[article_id]
        if (classify(change['before'], original, proposed, baseline.get(article_id)) != 'eligible'
                or change['body'] != proposed['body_html']):
            raise SyncError('Plan no longer matches the migration inputs and baseline.')

    lock = out / 'apply.lock'
    private_write(lock, b'Apply in progress. Inspect the journal before removing a stale lock.\n')
    try:
        # Refuse stale batches before touching any article. Recheck each item at write time.
        for change in changes:
            assert_current(api, change)
        for change in changes:
            article_id = change['id']
            stem = article_id.rsplit('/', 1)[1]
            current = assert_current(api, change)
            if current['body'] == change['body']:
                print(f'{article_id}: desired body already verified')
                continue
            backup = out / f'{stem}.before.json'
            if backup.exists():
                if read_json(backup) != current:
                    raise SyncError(f'{article_id}: existing backup does not match the current article.')
            else:
                private_write(backup, json_bytes(current))
            # A previous ambiguous write requires operator reconciliation, even if the old body remains.
            private_write(out / f'{stem}.attempt.json', json_bytes(
                {'id': article_id, 'desired_body_sha256': body_hash(change['body'])}
            ))
            # Read again after durable backup/journalling so the revision check is adjacent to the write.
            if assert_current(api, change) != current:
                raise SyncError(f'{article_id}: destination changed while backing up.')
            try:
                api.update(article_id, change['body'])
                after = api.read(article_id)
                if not unchanged_metadata(current, after) or after['body'] != change['body']:
                    raise SyncError('Destination readback differs from the approved result.')
                private_write(out / f'{stem}.verified.json', json_bytes(after))
            except (SyncError, OSError, KeyError, TypeError, ValueError) as error:
                raise SyncError(f'{article_id}: update outcome requires reconciliation; see private backup.') from error
            print(f'{article_id}: body and unchanged metadata verified')
    finally:
        lock.unlink()


def assert_current(api, change):
    current = api.read(change['id'])
    before = change['before']
    if current == before:
        return current
    if unchanged_metadata(before, current) and current['body'] == change['body']:
        return current
    raise SyncError(f"{change['id']}: destination changed since review; regenerate the plan.")


def output_directory(value, mode):
    out = Path(value).expanduser().resolve()
    if out.is_relative_to(ROOT.parent):
        raise SyncError('Use a private output directory outside the repository.')
    if mode == 'dry-run':
        out.mkdir(mode=0o700)
    if not out.is_dir() or out.stat().st_mode & 0o077:
        raise SyncError('Output must be a private directory with mode 0700.')
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('dry-run', 'apply'))
    parser.add_argument('--out', required=True, help='Private directory outside the repository')
    parser.add_argument('--baseline', type=Path, help='Trusted historical per-article evidence')
    parser.add_argument('--limit', type=int, default=5, help=f'Dry-run batch size (1–{MAX_BATCH})')
    parser.add_argument('--approved-sha256', help='Exact SHA-256 approved after reviewing plan.json')
    parser.add_argument('--confirm-edit-freeze', action='store_true',
                        help='Confirm exclusive recipe editing for the duration of apply')
    args = parser.parse_args()
    if not 1 <= args.limit <= MAX_BATCH:
        parser.error(f'--limit must be 1–{MAX_BATCH}')
    if args.mode == 'apply' and not (args.approved_sha256 and args.baseline and args.confirm_edit_freeze):
        parser.error('apply requires --approved-sha256, --baseline and --confirm-edit-freeze')
    try:
        if args.baseline and args.baseline.resolve().is_relative_to(ROOT.parent):
            raise SyncError('Keep the historical baseline outside the repository.')
        inputs = load_inputs(args.baseline)
        token = os.environ.get('DELLA_SHOPIFY_ADMIN_TOKEN')
        if not token:
            raise SyncError('Set DELLA_SHOPIFY_ADMIN_TOKEN using a private environment binding.')
        out = output_directory(args.out, args.mode)
        api = Shopify(token)
        if args.mode == 'dry-run':
            api.verify_store()
            plan = make_plan(api, inputs, args.limit)
            data = json_bytes(plan)
            private_write(out / 'plan.json', data)
            private_write(out / 'body.diff', diff_bytes(plan))
            for status in sorted({row['status'] for row in plan['articles']}):
                count = sum(row['status'] == status for row in plan['articles'])
                print(f'{status}: {count}')
            print(f'Plan SHA-256: {digest(data)}')
        else:
            data = (out / 'plan.json').read_bytes()
            if digest(data) != args.approved_sha256:
                raise SyncError('Plan SHA-256 does not match the approved digest.')
            api.verify_store()
            apply_plan(api, inputs, json.loads(data), out)
    except (SyncError, OSError, ValueError, KeyError, TypeError) as error:
        print(str(error) if isinstance(error, SyncError) else f'Local or response failure ({type(error).__name__}).',
              file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
