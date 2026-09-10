import ctypes
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from windows_identity import configure, APP_ID

@unittest.skipUnless(sys.platform=='win32','Windows only')
class Identity(unittest.TestCase):
    def test_native_taskbar_identity_and_icons(self):
        configure()
        shell=ctypes.WinDLL('shell32')
        get=shell.GetCurrentProcessExplicitAppUserModelID
        get.argtypes=[ctypes.POINTER(ctypes.c_wchar_p)]
        get.restype=ctypes.c_long
        value=ctypes.c_wchar_p()
        self.assertEqual(get(ctypes.byref(value)),0)
        try:
            self.assertEqual(value.value,APP_ID)
        finally:
            free=ctypes.WinDLL('ole32').CoTaskMemFree
            free.argtypes=[ctypes.c_void_p]
            free(ctypes.cast(value,ctypes.c_void_p))
        from PySide6 import QtGui,QtWidgets as W
        app=W.QApplication.instance() or W.QApplication([])
        icon=QtGui.QIcon(str(Path(__file__).resolve().parents[1]/'assets'/'logo.png'))
        app.setWindowIcon(icon)
        window=W.QWidget()
        window.setWindowIcon(icon)
        window.show()
        app.processEvents()
        send=ctypes.WinDLL('user32').SendMessageW
        send.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_size_t,ctypes.c_ssize_t]
        send.restype=ctypes.c_ssize_t
        self.assertNotEqual(send(int(window.winId()),0x7f,0,0),0)
        self.assertNotEqual(send(int(window.winId()),0x7f,1,0),0)
        window.close()

if __name__=='__main__':
    unittest.main()
