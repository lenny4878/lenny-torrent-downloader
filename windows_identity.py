"""Give the Python-hosted desktop app its own stable Windows taskbar identity."""
import ctypes
import sys

APP_ID = 'Lenny.TorrentDownloader.Desktop'

def configure():
    if sys.platform != 'win32':
        return
    shell = ctypes.WinDLL('shell32',use_last_error=True)
    function = shell.SetCurrentProcessExplicitAppUserModelID
    function.argtypes = [ctypes.c_wchar_p]
    function.restype = ctypes.c_long
    result = function(APP_ID)
    if result < 0:
        raise OSError(f'Cannot set taskbar identity (HRESULT {result:#x})')
