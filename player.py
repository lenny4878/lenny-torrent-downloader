from PySide6 import QtCore, QtGui, QtWidgets as W
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink

class VideoCanvas(W.QWidget):
    """Paint decoded frames in the Qt backing store, avoiding blank native video surfaces."""
    def __init__(self,parent=None):
        super().__init__(parent)
        self.image=QtGui.QImage()
        self.setMinimumSize(480,270)

    def frame(self,value):
        if value.isValid():
            self.image=value.toImage()
            self.update()

    def paintEvent(self,event):
        painter=QtGui.QPainter(self)
        painter.fillRect(self.rect(),QtGui.QColor('#101722'))
        if not self.image.isNull():
            size=self.image.size().scaled(self.size(),QtCore.Qt.KeepAspectRatio)
            target=QtCore.QRect((self.width()-size.width())//2,(self.height()-size.height())//2,size.width(),size.height())
            painter.drawImage(target,self.image)

class Player(W.QDialog):
    closing = QtCore.Signal()

    def __init__(self, url, title, parent=None):
        super().__init__(parent)
        self._released = False
        self.setWindowTitle('边下边看 · ' + title)
        self.resize(960,620)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowFlag(QtCore.Qt.WindowMinMaxButtonsHint, True)
        layout = W.QVBoxLayout(self)
        video = VideoCanvas()
        self.video = video
        layout.addWidget(video,1)
        self.media = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.media.setAudioOutput(self.audio)
        self.sink=QVideoSink(self)
        self.sink.videoFrameChanged.connect(video.frame)
        self.media.setVideoSink(self.sink)
        self.audio.setVolume(.7)
        self.note = W.QLabel('正在读取视频；下载速度不足时会等待缓冲。')
        layout.addWidget(self.note)
        row = W.QHBoxLayout()
        toggle = W.QPushButton('播放 / 暂停')
        toggle.clicked.connect(lambda: self.media.pause() if self.media.playbackState() == QMediaPlayer.PlayingState else self.media.play())
        row.addWidget(toggle)
        self.seek = W.QSlider(QtCore.Qt.Horizontal)
        self.seek.setRange(0,0)
        self.seek.sliderReleased.connect(lambda: self.media.setPosition(self.seek.value()))
        self.media.durationChanged.connect(lambda n:self.seek.setRange(0,int(n)))
        self.media.positionChanged.connect(self.position)
        row.addWidget(self.seek,1)
        volume = W.QSlider(QtCore.Qt.Horizontal)
        volume.setRange(0,100)
        volume.setValue(70)
        volume.setMaximumWidth(100)
        volume.valueChanged.connect(lambda n:self.audio.setVolume(n/100))
        row.addWidget(W.QLabel('音量'))
        row.addWidget(volume)
        layout.addLayout(row)
        self.media.errorOccurred.connect(lambda *_:self.note.setText('暂时无法播放：'+self.media.errorString()+'。可继续下载后重新打开。'))
        self.media.setSource(QtCore.QUrl(url))
        self.media.play()

    def position(self, n):
        if not self.seek.isSliderDown():
            self.seek.setValue(int(n))
        self.note.setText(f'{n//60000:02d}:{n//1000%60:02d} / {self.media.duration()//60000:02d}:{self.media.duration()//1000%60:02d}   ·   跳转到未下载位置可能需要缓冲')

    def closeEvent(self,event):
        self.release_playback()
        super().closeEvent(event)

    def done(self,result):
        self.release_playback()
        super().done(result)

    def release_playback(self):
        if self._released:
            return
        self._released = True
        self.closing.emit()  # Revoke HTTP reads before stopping the decoder.
        self.media.stop()
        self.media.setSource(QtCore.QUrl())
        self.media.setVideoSink(None)
        self.media.setAudioOutput(None)
        self.sink.videoFrameChanged.disconnect(self.video.frame)
        self.video.image = QtGui.QImage()
        self.video.update()
