"""Optional decoder integration: generates its own video, never plays personal content."""
import os
import sys
import tempfile
import subprocess
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_integration import make_torrent
import imageio_ffmpeg
from PySide6 import QtCore,QtWidgets as W
import libtorrent as lt
from engine import Engine
from app import Window,theme

root=Path(tempfile.mkdtemp(prefix='lenny_playback_'))
seed=root/'seed'
seed.mkdir()
video=seed/'sample.mp4'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-f','lavfi','-i',
    'testsrc2=size=640x360:rate=30','-t','24','-c:v','mpeg4','-b:v','4M','-movflags','+faststart',str(video)],check=True)
source=make_torrent(seed,video.read_bytes(),'sample.mp4')
print('Generated video bytes:',video.stat().st_size,flush=True)
opts=dict(enable_dht=False,enable_lsd=False,listen_interfaces='127.0.0.1:0')
a,b=Engine(root/'a',opts),Engine(root/'b',opts)
a.config.update(seed=True,upload=2048); a.apply_settings()
a.add(source,seed,[4])
b.config.update(download=512); b.apply_settings()
key=b.add(source,root/'download',[4])
app=W.QApplication([])
theme(app)
win=Window(b)
win.show()
state={'frames':0,'partial_frame':False,'closing':False,'deleted':False}
timer=QtCore.QTimer()
def step():
    a.tick()
    if state['closing']:
        if key not in b.items:
            state['deleted']=not (root/'download'/'sample.mp4').exists()
            app.quit()
        return
    item=b.items[key]
    h=item['handle']
    h.connect_peer(('127.0.0.1',a.session.listen_port()))
    if key not in win.players and win.stream.readiness(item)[1]>=1:
        win.preview(key)
        player=win.players[key]
        def frame(value):
            if value.isValid():
                state['frames']+=1
                state['partial_frame'] |= not h.status().is_finished
                if state['frames']==90:
                    win.grab().save(str(Path(__file__).resolve().parents[1]/'docs'/'interface.png'))
                    player.screen().grabWindow(player.winId()).save(str(Path(__file__).resolve().parents[1]/'docs'/'playback.png'))
                    value.toImage().save(str(Path(__file__).resolve().parents[1]/'docs'/'decoded-frame.png'))
                    def close_and_delete():
                        state['closing']=True
                        player.close()  # Exercise the user's window-X route, not only our helper.
                        QtCore.QTimer.singleShot(150,delete_after_close)
                    def delete_after_close():
                        try:
                            assert key not in win.players, 'closed player remains registered'
                            assert not win.stream.cache, 'playback cache was not released'
                            win.close_player(key)
                            b.remove(key,True)
                        except Exception as error:
                            state['error']=str(error)
                            app.quit()
                    QtCore.QTimer.singleShot(100,close_and_delete)
        player.media.videoSink().videoFrameChanged.connect(frame)
timer.timeout.connect(step)
timer.start(100)
QtCore.QTimer.singleShot(45000,app.quit)
try:
    app.exec()
    assert state['frames']>=90 and state['partial_frame'] and state['deleted'],state
    print('PASS: actual decoded video frames while torrent is still incomplete:',state,flush=True)
finally:
    timer.stop()
    win.close()
    a.close()
