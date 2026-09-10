"""Explicit diagnostic mode, using isolated data and optional caller-supplied test video."""
import json
import tempfile
from pathlib import Path
from PySide6 import QtCore,QtWidgets as W
from engine import Engine
from app import Window,theme
from player import Player
from windows_identity import configure
from version import VERSION

def run(report,video=None):
    result={'version':VERSION,'passed':False}
    window=None
    try:
        configure()
        app=W.QApplication([])
        theme(app)
        root=Path(tempfile.mkdtemp(prefix='lenny_exe_check_'))
        engine=Engine(root,dict(enable_dht=False,enable_lsd=False))
        window=Window(engine)
        window.show()
        assert not window.windowIcon().isNull()
        result.update(engine=True,logo=True,tray_available=W.QSystemTrayIcon.isSystemTrayAvailable())
        if result['tray_available']:
            window._tray_hint_shown=True
            window.minimize_to_tray()
            assert not window.isVisible() and window.timer.isActive()
            window.restore_window()
            assert window.isVisible()
        frames=[]
        if video:
            player=Player(QtCore.QUrl.fromLocalFile(str(Path(video).resolve())).toString(),'Generated build test',window)
            player.audio.setMuted(True)
            player.media.videoSink().videoFrameChanged.connect(lambda frame:frames.append(1) if frame.isValid() else None)
            player.show()
            timer=QtCore.QTimer()
            timer.timeout.connect(lambda:app.quit() if len(frames)>=10 else None)
            timer.start(100)
            QtCore.QTimer.singleShot(15000,app.quit)
            app.exec()
            timer.stop()
            from shiboken6 import isValid
            if isValid(player):
                player.close()
            assert len(frames)>=10,'No decoded frames'
        else:
            app.processEvents()
        window.shutdown()
        result.update(decoded_frames=len(frames),shutdown=True,passed=True)
    except Exception as error:
        result['error']=repr(error)
    finally:
        if window is not None:
            window.shutdown()
        Path(report).write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
    return 0 if result['passed'] else 1
