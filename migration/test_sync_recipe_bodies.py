import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('sync', Path(__file__).with_name('sync-recipe-bodies.py'))
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)

ID = 'gid://shopify/Article/1'
SOURCE = 'https://dellarice.com/recipe/example/'
BEFORE = {
    'id': ID, 'handle': 'example', 'blog': {'id': 'gid://shopify/Blog/1', 'handle': 'recipes'},
    'title': 'Original title', 'body': '<p>Original recipe.</p>',
    'createdAt': '2026-11-04T13:00:00Z', 'updatedAt': '2026-11-04T13:00:00Z',
    'isPublished': True, 'publishedAt': '2026-11-04T13:00:00Z',
    'summary': None, 'tags': ['rice'], 'templateSuffix': None, 'image': None,
}
BODY = '<p>Original recipe.</p><img src="https://cdn.shopify.com/example.jpg"><a href="https://youtu.be/test">Video</a>'
RECEIPT = {'id': ID, 'source_url': SOURCE, 'handle': 'example', 'isPublished': False}
PREPARED = {'id': ID, 'source_url': SOURCE, 'destination_path': '/blogs/recipes/example',
            'body_html': BODY, 'execution_status': 'prepared_not_applied', 'requested_is_published': True}
BASELINE = {'id': ID, 'source_url': SOURCE, 'body_sha256': sync.body_hash(BEFORE['body']),
            'updatedAt': BEFORE['updatedAt']}
INPUTS = ({ID: RECEIPT}, {ID: PREPARED}, {ID: BASELINE})


class FakeShopify:
    def __init__(self, before=BEFORE, outcome='ok'):
        self.current = copy.deepcopy(before)
        self.outcome = outcome
        self.writes = []

    def read(self, article_id):
        return copy.deepcopy(self.current)

    def update(self, article_id, body):
        self.writes.append((article_id, body))
        self.current['updatedAt'] = '2026-11-05T14:00:00Z'
        self.current['body'] = body if self.outcome != 'normalised' else body + '\n'
        if self.outcome == 'timeout':
            raise sync.SyncError('Transport failure')


class SyncTests(unittest.TestCase):
    def test_receipt_alone_cannot_authorise_body_change(self):
        api = FakeShopify()
        plan = sync.make_plan(api, (*INPUTS[:2], {}), 5)
        self.assertEqual(plan['articles'][0]['status'], 'baseline_missing')
        self.assertEqual(plan['changes'], [])
        self.assertEqual(api.writes, [])

    def test_detects_body_revision_and_identity_conflicts(self):
        variants = [
            (None, 'missing'),
            (dict(BEFORE, body='Merchant copy'), 'destination_changed'),
            (dict(BEFORE, updatedAt='2026-11-05T13:00:00Z'), 'destination_changed'),
            (dict(BEFORE, handle='moved'), 'identity_conflict'),
            (dict(BEFORE, body=BODY), 'already_matches'),
        ]
        for current, expected in variants:
            with self.subTest(expected=expected):
                self.assertEqual(sync.classify(current, RECEIPT, PREPARED, BASELINE), expected)

    def test_plan_carries_exact_diff_and_defers_excess_updates(self):
        second = ID[:-1] + '2'
        other_source = SOURCE + 'other'
        other = dict(BEFORE, id=second, handle='other')
        inputs = (
            {ID: RECEIPT, second: dict(RECEIPT, id=second, source_url=other_source, handle='other')},
            {ID: PREPARED, second: dict(PREPARED, id=second, source_url=other_source,
                                       destination_path='/blogs/recipes/other')},
            {ID: BASELINE, second: dict(BASELINE, id=second, source_url=other_source)},
        )
        api = FakeShopify()
        api.read = lambda article_id: BEFORE if article_id == ID else other
        plan = sync.make_plan(api, inputs, 1)
        self.assertEqual([row['status'] for row in plan['articles']], ['proposed', 'deferred'])
        self.assertEqual(plan['changes'][0]['body'], BODY)
        self.assertIn(b'youtu.be/test', sync.diff_bytes(plan))
        self.assertIn(b'cdn.shopify.com/example.jpg', sync.diff_bytes(plan))
        self.assertEqual(api.writes, [])

    def test_durable_backup_body_only_apply_and_resume(self):
        for published in (True, False):
            with self.subTest(published=published), tempfile.TemporaryDirectory() as directory:
                api = FakeShopify(dict(BEFORE, isPublished=published))
                plan = sync.make_plan(api, INPUTS, 5)
                out = Path(directory)
                update = api.update

                def require_backup(article_id, body):
                    self.assertEqual(sync.read_json(out / '1.before.json'), api.current)
                    self.assertTrue((out / '1.attempt.json').is_file())
                    update(article_id, body)

                api.update = require_backup
                sync.apply_plan(api, INPUTS, plan, out)
                self.assertEqual(sync.read_json(out / '1.verified.json')['body'], BODY)
                self.assertEqual(api.current['isPublished'], published)
                sync.apply_plan(api, INPUTS, plan, out)
                self.assertEqual(api.writes, [(ID, BODY)])

    def test_stale_plan_aborts_before_write(self):
        api = FakeShopify()
        plan = sync.make_plan(api, INPUTS, 5)
        api.current['title'] = 'New merchant title'
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(sync.SyncError, 'changed since review'):
                sync.apply_plan(api, INPUTS, plan, Path(directory))
        self.assertEqual(api.writes, [])

    def test_edit_between_preflight_and_write_aborts(self):
        api = FakeShopify()
        plan = sync.make_plan(api, INPUTS, 5)
        with patch.object(api, 'read', side_effect=[BEFORE, BEFORE, dict(BEFORE, body='New edit')]):
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(sync.SyncError, 'changed since review'):
                    sync.apply_plan(api, INPUTS, plan, Path(directory))
        self.assertEqual(api.writes, [])

    def test_verification_mismatch_and_ambiguous_write_halt(self):
        for outcome in ('timeout', 'normalised'):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as directory:
                api = FakeShopify(outcome=outcome)
                plan = sync.make_plan(api, INPUTS, 5)
                out = Path(directory)
                with self.assertRaisesRegex(sync.SyncError, 'requires reconciliation'):
                    sync.apply_plan(api, INPUTS, plan, out)
                self.assertTrue((out / '1.before.json').exists())
                self.assertFalse((out / '1.verified.json').exists())
                api.current = copy.deepcopy(BEFORE)
                with self.assertRaises(FileExistsError):
                    sync.apply_plan(api, INPUTS, plan, out)
                self.assertEqual(len(api.writes), 1)

    def test_mutation_serialises_only_id_and_body(self):
        api = sync.Shopify('fake')
        with patch.object(api, 'graphql', return_value={
            'articleUpdate': {'article': {'id': ID}, 'userErrors': []},
        }) as graphql:
            api.update(ID, BODY)
        graphql.assert_called_once_with(sync.UPDATE, {'id': ID, 'body': BODY}, write=True)
        self.assertIn('article: {body: $body}', sync.UPDATE)
        self.assertNotIn('isPublished', sync.UPDATE)

    def test_changed_plan_body_is_rejected(self):
        api = FakeShopify()
        plan = sync.make_plan(api, INPUTS, 5)
        plan['changes'][0]['body'] = '<p>Unapproved content</p>'
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(sync.SyncError, 'no longer matches'):
                sync.apply_plan(api, INPUTS, plan, Path(directory))
        self.assertEqual(api.writes, [])

    def test_duplicate_receipt_identity_is_rejected(self):
        with self.assertRaisesRegex(sync.SyncError, 'duplicate'):
            sync.index_rows([RECEIPT, RECEIPT])

    def test_hash_is_checked_before_api_access(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / 'plan.json').write_text(json.dumps({'changed': True}))
            argv = ['sync-recipe-bodies.py', 'apply', '--out', directory, '--baseline', '/tmp/baseline.json',
                    '--approved-sha256', '0' * 64, '--confirm-edit-freeze']
            with (patch.object(sync, 'load_inputs', return_value=INPUTS),
                  patch.object(sync.Shopify, 'verify_store') as verify,
                  patch.dict(sync.os.environ, {'DELLA_SHOPIFY_ADMIN_TOKEN': 'fake'}),
                  patch.object(sync.sys, 'argv', argv)):
                self.assertEqual(sync.main(), 1)
            verify.assert_not_called()


if __name__ == '__main__':
    unittest.main()
