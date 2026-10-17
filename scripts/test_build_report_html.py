"""Fast per-report checks; full browser export QA is required when affected or requested."""
import base64
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

from build_report_html import build


def settings(path):
    text = path.read_text(encoding="utf-8")
    return json.loads(re.search(r'<script id="report-settings" type="application/json">(.*?)</script>', text, re.S).group(1))


class ReportBuilderTests(unittest.TestCase):
    def test_portable_output_preserves_source_and_sibling_state(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'D-2026-09-17.md'
            raw='# 测试报告\n\nprompt_version: v2.0\n\n## 一、金句\n\n**“你想到了另一种办法。”**\n'.encode('utf-8')
            source.write_bytes(raw)
            state=root/'STATE-latest.json';state.write_text('{"unchanged":true}',encoding='utf-8')
            result=build(source,headline='好奇与成长')
            self.assertEqual(result,source.with_suffix('.html'))
            self.assertEqual(source.read_bytes(),raw)
            self.assertEqual(state.read_text(encoding='utf-8'),'{"unchanged":true}')
            data=settings(result)
            self.assertEqual(base64.b64decode(data['markdownBase64']),raw)
            self.assertEqual(data['sourceSha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(data['dateLabel'],'2026 . 09 . 17')
            self.assertFalse(re.search(r'<(?:script|link|img)\b[^>]*(?:src|href)=["\']https?://',result.read_text(encoding='utf-8')))

    def test_source_cannot_break_out_of_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'D-2026-09-17.md'
            raw='# 测试\n\n</script><script>window.pwned=1</script>\n'
            source.write_bytes(raw.encode('utf-8'))
            result=build(source,headline='</script><img src=x onerror=alert(1)>')
            data=settings(result)
            self.assertEqual(base64.b64decode(data['markdownBase64']).decode(),raw)
            rendered = result.read_text(encoding='utf-8')
            self.assertNotIn('<script>window.pwned=1</script>', rendered)
            self.assertIn('&lt;script&gt;window.pwned=1&lt;/script&gt;', rendered)

    def test_annual_period_not_first_quoted_date(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'Y-2026-B-孩子的一年.md'
            source.write_text('# 孩子的一年\n\n2026-01-03 是一个记忆片段。',encoding='utf-8')
            data=settings(build(source,audience='child'))
            self.assertEqual(data['dateLabel'],'2026')
            self.assertEqual(data['audience'],'child')

    def test_invalid_and_empty_inputs_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'report.md';source.write_text('# 原本',encoding='utf-8')
            with self.assertRaises(ValueError):build(source,output=source)
            self.assertEqual(source.read_text(encoding='utf-8'),'# 原本')
            source.write_text('',encoding='utf-8')
            with self.assertRaises(ValueError):build(source)


if __name__=='__main__':unittest.main()
