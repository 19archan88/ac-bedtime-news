import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from profile_store import update_profile, read_profile, status, require_ready, SKILL_ROOT
from prepare_report import prepare


class ProfileStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_partial_then_later_update_and_new_read(self):
        self.assertFalse(status(read_profile(self.root))['ready'])
        update_profile(self.root, {'children': [{'id': 'child-a', 'alias': '示例甲'}]}, True)
        with self.assertRaises(ValueError):
            require_ready(self.root)
        update_profile(self.root, {'timezone': 'Asia/Shanghai',
            'onboarding': {'acknowledged': True, 'decisions': {'age': 'deferred', 'school': 'deferred', 'family_members': 'declined'}}}, True)
        saved, target = require_ready(self.root)
        self.assertEqual(target, 'child-a')
        update_profile(self.root, {'children': [{'id': 'child-a', 'birth_date': '2020-01-01'}], 'custom': {'retain': True}}, True)
        again = read_profile(self.root)
        self.assertEqual(again['children'][0]['alias'], '示例甲')
        self.assertNotIn('age', status(again)['missing'])
        self.assertEqual(again['family_id'], saved['family_id'])
        self.assertEqual(again['revision'], 3)

    def test_save_failure_preserves_previous(self):
        update_profile(self.root, {'children': [{'id': 'child-a'}]}, True)
        before = read_profile(self.root)
        with patch('pathlib.Path.replace', side_effect=PermissionError('read only')):
            with self.assertRaises(PermissionError):
                update_profile(self.root, {'timezone': 'UTC'}, True)
        self.assertEqual(read_profile(self.root), before)
        self.assertFalse(list(self.root.glob('.profile-*')))

    def test_private_boundary_and_confirmation(self):
        with self.assertRaises(ValueError):
            update_profile(SKILL_ROOT / 'private', {}, True)
        with self.assertRaises(ValueError):
            update_profile(self.root, {})
        self.assertFalse((self.root / 'FAMILY-profile.json').exists())

    def test_report_gate_and_explicit_temporary_choice(self):
        source = self.root / 'D-2030-01-01.md'
        source.write_text('# 虚构测试\n\n完整内容', encoding='utf-8')
        with self.assertRaises(ValueError):
            prepare(source, archive=self.root)
        self.assertFalse(source.with_suffix('.html').exists())
        with self.assertRaises(ValueError):
            prepare(source, temporary=True)
        result = prepare(source, temporary=True, acknowledged=True)
        self.assertTrue(result.exists())
        self.assertIsNone(read_profile(self.root))

    def test_multi_child_requires_selection_and_preserves_other(self):
        update_profile(self.root, {'children': [{'id': 'child-a'}, {'id': 'child-b'}]}, True)
        update_profile(self.root, {'children': [{'id': 'child-a', 'alias': '示例甲'}]}, True)
        value = read_profile(self.root)
        self.assertEqual(len(value['children']), 2)
        self.assertIn('target_child', status(value)['missing'])
        self.assertNotIn('target_child', status(value, 'child-a')['missing'])

    def test_sibling_decisions_do_not_leak(self):
        value = update_profile(self.root, {'children': [{'id': 'a'}, {'id': 'b'}],
            'timezone': 'UTC', 'onboarding': {'acknowledged': True,
            'decisions': {'age': 'deferred', 'alias': 'deferred', 'school': 'deferred', 'family_members': 'deferred'}}}, True)
        self.assertFalse(status(value, 'b')['ready'])
        value = update_profile(self.root, {'children': [{'id': 'b', 'onboarding': {'decisions': {
            'age': 'deferred', 'alias': 'deferred', 'school': 'deferred'}}}]}, True)
        self.assertTrue(status(value, 'b')['ready'])
        self.assertFalse(status(value, 'a')['ready'])

    def test_new_school_baseline_does_not_erase_history(self):
        from test_family_profile import baseline
        update_profile(self.root, {'children': [{'id': 'a', 'school_baselines': [baseline()]}]}, True)
        saved = update_profile(self.root, {'children': [{'id': 'a', 'school_baselines': [baseline('2031-08-20', 2)]}]}, True)
        self.assertEqual(len(saved['children'][0]['school_baselines']), 2)
        self.assertEqual(len(saved['change_history']), 2)

    def test_invalid_date_preserves_saved_profile(self):
        update_profile(self.root, {'children': [{'id': 'a'}]}, True)
        before = read_profile(self.root)
        with self.assertRaises(ValueError):
            update_profile(self.root, {'children': [{'id': 'a', 'birth_date': '2029-02-30'}]}, True)
        self.assertEqual(before, read_profile(self.root))


if __name__ == '__main__':
    unittest.main()
