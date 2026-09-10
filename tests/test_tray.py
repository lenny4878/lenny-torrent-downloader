import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6 import QtWidgets as W, QtCore
from PySide6.QtTest import QTest
from app import Window,theme,LOGO_PATH
from engine import Engine

class TrayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=W.QApplication.instance() or W.QApplication([])
        theme(cls.app)

    def setUp(self):
        self.root=tempfile.TemporaryDirectory(prefix='lenny_tray_')
        self.engine=Engine(self.root.name,dict(enable_dht=False,enable_lsd=False))
        self.window=Window(self.engine)
        self.window.show()
        QTest.qWait(100)

    def tearDown(self):
        self.window.shutdown()
        self.window.close()
        self.root.cleanup()

    def test_hide_restore_timers_and_exit(self):
        window=self.window
        self.assertTrue(LOGO_PATH.is_file())
        self.assertFalse(window.windowIcon().isNull())
        with patch.object(W.QSystemTrayIcon,'isSystemTrayAvailable',return_value=True):
            window.tray.show()
            with patch.object(window.tray,'showMessage'):
                window.showMinimized()
                QTest.qWait(100)
            self.assertFalse(window.isVisible())
            self.assertTrue(window.timer.isActive())
            self.assertTrue(window.save_timer.isActive())
            self.assertTrue(window.alert_timer.isActive())
            with patch.object(self.engine,'tick',wraps=self.engine.tick) as tick:
                QTest.qWait(1100)
                self.assertGreaterEqual(tick.call_count,1)
            window.tray_activated(W.QSystemTrayIcon.DoubleClick)
            QTest.qWait(100)
            self.assertTrue(window.isVisible())
            self.assertFalse(window.isMinimized())
            window.showMaximized()
            QTest.qWait(100)
            window.minimize_to_tray()
            window.restore_window()
            self.assertTrue(window.isMaximized())
            window.showNormal()
            QTest.qWait(100)
            window.grab().save(str(Path(__file__).resolve().parents[1]/'docs'/'interface.png'))
            with patch.object(self.engine,'close',wraps=self.engine.close) as close:
                window.exit_app()
                window.shutdown()
                self.assertEqual(close.call_count,1)
            self.assertFalse(window.tray.isVisible())
            self.assertFalse(window.timer.isActive())

    def test_no_tray_keeps_minimized_window(self):
        with patch.object(W.QSystemTrayIcon,'isSystemTrayAvailable',return_value=False):
            self.window.showMinimized()
            QTest.qWait(100)
            self.assertTrue(self.window.isVisible())
            self.assertTrue(self.window.isMinimized())

if __name__=='__main__':
    unittest.main()
