import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6 import QtWidgets as W,QtCore
from PySide6.QtTest import QTest
from app import Window,SettingsDialog,AddDialog,theme
from engine import Engine,inspect_torrent
from test_integration import make_torrent

class BasicUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=W.QApplication.instance() or W.QApplication([])
        theme(cls.app)

    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='lenny_basic_ui_'))
        self.engine=Engine(self.root/'state',dict(enable_dht=False,enable_lsd=False))
        self.window=Window(self.engine)
        self.window.show()

    def tearDown(self):
        self.window.close()

    def test_settings_folder_selection_cancel_and_save(self):
        folder=str(self.root/'new folder')
        dialog=SettingsDialog(self.engine.config,self.window)
        with patch('app.W.QFileDialog.getExistingDirectory',return_value=folder):
            dialog.browse()
        self.assertEqual(dialog.folder.text(),folder)
        with patch('app.W.QFileDialog.getExistingDirectory',return_value=''):
            dialog.browse()
        self.assertEqual(dialog.folder.text(),folder)
        dialog.close()
        def accept(d):
            d.folder.setText(folder)
            d.fields['download'].setValue(1024)
            d.fields['upload'].setValue(256)
            d.fields['active'].setValue(2)
            return W.QDialog.Accepted
        with patch.object(SettingsDialog,'exec',accept):
            self.window.settings()
        restored=Engine(self.root/'state',dict(enable_dht=False,enable_lsd=False))
        try:
            self.assertEqual(restored.config['folder'],folder)
            self.assertEqual(restored.config['active'],2)
            self.assertEqual(restored.session.get_settings()['download_rate_limit'],1024*1024)
            self.assertEqual(restored.session.get_settings()['upload_rate_limit'],256*1024)
        finally:
            restored.close()

    def test_file_selection_and_invalid_torrent(self):
        source=make_torrent(self.root/'seed',b'x'*32768,'sample.mp4')
        dialog=AddDialog(source,str(self.root/'download'),self.window)
        self.assertEqual(dialog.priorities(),[4])
        dialog.select(QtCore.Qt.Unchecked)
        self.assertEqual(dialog.priorities(),[0])
        with patch('app.W.QMessageBox.warning') as warning:
            dialog.validate()
            self.assertTrue(warning.called)
        dialog.select(QtCore.Qt.Checked)
        dialog.validate()
        self.assertEqual(dialog.result(),W.QDialog.Accepted)
        broken=self.root/'bad.torrent'
        broken.write_bytes(b'not a torrent')
        with self.assertRaises(Exception):
            inspect_torrent(broken)

    def test_alignment_open_and_delete_dialog(self):
        source=make_torrent(self.root/'seed',b'x'*32768,'sample.mp4')
        key=self.engine.add(source,self.root/'seed',[4])
        for _ in range(100):
            self.window.refresh()
            if self.engine.items[key]['handle'].status().is_finished:
                break
            QTest.qWait(25)
        self.assertTrue(self.engine.items[key]['handle'].status().is_finished)
        table=self.window.table
        self.assertTrue(table.item(0,0).textAlignment() & QtCore.Qt.AlignLeft)
        for col in range(1,6):
            self.assertTrue(table.item(0,col).textAlignment() & QtCore.Qt.AlignHCenter)
            self.assertTrue(table.horizontalHeaderItem(col).textAlignment() & QtCore.Qt.AlignHCenter)
        self.assertEqual(table.cellWidget(0,1).label.alignment(),QtCore.Qt.AlignCenter)
        with patch('app.QtGui.QDesktopServices.openUrl',return_value=True) as opened:
            table.cellDoubleClicked.emit(0,0)
            self.assertEqual(Path(opened.call_args[0][0].toLocalFile()),self.root/'seed'/'sample.mp4')
        second=make_torrent(self.root/'other',b'z'*131072,'另一个测试视频.mp4')
        self.engine.add(second,self.root/'pending',[4],False)
        self.window.refresh()
        QTest.qWait(100)
        self.window.grab().save(str(Path(__file__).resolve().parents[1]/'docs'/'interface.png'))
        table.selectRow(0)
        defaults=[]
        def cancel(d):
            defaults.append(d.findChild(W.QCheckBox).isChecked())
            return W.QDialog.Rejected
        with patch.object(W.QDialog,'exec',cancel):
            self.window.remove()
        self.assertEqual(defaults,[False])
        self.assertIn(key,self.engine.items)
        with patch.object(W.QDialog,'exec',return_value=W.QDialog.Accepted):
            self.window.remove()
        self.assertNotIn(key,self.engine.items)
        self.assertTrue((self.root/'seed'/'sample.mp4').exists())

if __name__=='__main__':
    unittest.main()
