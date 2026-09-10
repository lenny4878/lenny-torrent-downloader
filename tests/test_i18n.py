import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path
from string import Formatter
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6 import QtWidgets as W
from app import Window, SettingsDialog, theme
from engine import Engine, status_text, task_status
from i18n import CATALOG, LANGUAGES, tr, set_language, translated_text

class Languages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = W.QApplication.instance() or W.QApplication([])
        theme(cls.app)

    def test_catalog_coverage_and_placeholders(self):
        def fields(text):
            return {f for _, f, _, _ in Formatter().parse(text) if f is not None}
        for source, translations in CATALOG.items():
            self.assertEqual(set(translations), set(LANGUAGES))
            for code, text in translations.items():
                self.assertTrue(text)
                self.assertEqual(fields(source), fields(text), (source, code))
        for filename in ('app.py', 'engine.py', 'player.py'):
            tree = ast.parse((Path(__file__).resolve().parents[1]/filename).read_text('utf-8-sig'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'tr':
                    self.assertIn(node.args[0].value, CATALOG, filename)

    def test_live_switch_save_restart_and_settings(self):
        with tempfile.TemporaryDirectory(prefix='lenny_languages_') as folder:
            engine = Engine(folder, dict(enable_dht=False, enable_lsd=False))
            window = Window(engine)
            window.show()
            session = engine.session
            try:
                for code in ['en', 'de', 'fr', 'ja', 'zh']:
                    window.language_combo.setCurrentIndex(window.language_combo.findData(code))
                    self.app.processEvents()
                    self.assertEqual(window.table.horizontalHeaderItem(0).text(), tr('名称'))
                    self.assertIn(tr('设置'), [b.text() for b in window.findChildren(W.QPushButton)])
                    self.assertEqual(window.tray.contextMenu().actions()[0].text(), tr('显示主窗口'))
                    self.assertIs(engine.session, session)
                    self.assertTrue(window.timer.isActive())
                    self.assertEqual(json.loads((Path(folder)/'settings.json').read_text('utf-8'))['language'], code)
                    dialog = SettingsDialog(engine.config, window)
                    self.assertEqual(dialog.windowTitle(), tr('设置'))
                    self.assertEqual(dialog.language.currentData(), code)
                    dialog.close()
                    path = Path(__file__).resolve().parents[1]/'docs'
                    path.mkdir(exist_ok=True)
                    window.grab().save(str(path/f'language-{code}.png'))
                def accept(dialog):
                    dialog.language.setCurrentIndex(dialog.language.findData('ja'))
                    return W.QDialog.Accepted
                with patch.object(SettingsDialog, 'exec', accept):
                    window.settings()
                self.assertEqual(window.table.horizontalHeaderItem(0).text(), '名前')
            finally:
                window.close()
            restored = Engine(folder, dict(enable_dht=False, enable_lsd=False))
            try:
                self.assertEqual(restored.config['language'], 'ja')
                self.assertEqual(tr('删除任务'), 'タスクを削除')
            finally:
                restored.close()
                set_language('zh')

    def test_formatted_text_round_trip(self):
        source = '缓冲 {v0}'
        set_language('en')
        value = tr(source, v0='37%')
        for code in ('de', 'fr', 'ja', 'zh'):
            old = 'en' if code == 'de' else previous
            set_language(code)
            value = translated_text(value, old)
            self.assertEqual(value, tr(source, v0='37%'))
            previous = code
        set_language('invalid')
        self.assertEqual(tr('设置'), 'Settings')
        set_language('zh')

if __name__ == '__main__':
    unittest.main()
