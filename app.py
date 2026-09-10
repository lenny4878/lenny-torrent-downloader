from i18n import tr, LANGUAGES, language, set_language, retranslate_widgets
import os
import sys
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets as W
from engine import Engine, inspect_torrent, status_text, task_status
from streaming import StreamService
from version import APP_NAME, VERSION

LOGO_PATH = Path(__file__).resolve().parent / 'assets' / 'logo.png'


def theme(app):
    app.setStyle('Fusion')
    app.setFont(QtGui.QFont('Microsoft YaHei UI', 10))
    app.setStyleSheet('''
        QWidget { color:#233249; font-family:"Microsoft YaHei UI"; }
        QMainWindow,QDialog { background:#f5f7fb; }
        QLabel { background:transparent; }
        QLabel#eyebrow { color:#61748e; font-size:11px; font-weight:600; }
        QLabel#heading { font-size:30px; font-weight:700; color:#152b48; }
        QLabel#muted { color:#728097; }
        QLabel#logo { background:#356cf6; color:white; border-radius:14px; font-size:28px; font-weight:700; }
        QFrame#card { background:white; border:1px solid #e5eaf2; border-radius:12px; }
        QLabel#metric { font-size:22px; font-weight:600; color:#233c64; }
        QPushButton { background:white; border:1px solid #dce3ee; border-radius:8px; padding:9px 16px; }
        QPushButton:hover { background:#edf3ff; border-color:#adc4fb; }
        QPushButton:pressed { background:#dfeaff; }
        QPushButton:disabled { color:#a3adbc; background:#f4f6f9; }
        QPushButton#primary { background:#356cf6; color:white; border:1px solid #356cf6; font-weight:600; }
        QPushButton#primary:hover { background:#285be0; }
        QTableWidget,QTreeWidget { background:white; alternate-background-color:#fafcff; border:1px solid #e5eaf2; border-radius:10px; selection-background-color:#eaf1ff; selection-color:#1d4cb0; outline:0; }
        QTableWidget::item { padding:8px; border-bottom:1px solid #f0f3f8; }
        QHeaderView::section { background:#f9fbfe; color:#7b879a; font-size:12px; padding:12px 8px; border:0; border-bottom:1px solid #e9eef5; }
        QPlainTextEdit { background:white; border:1px solid #e5eaf2; border-radius:10px; padding:12px; }
        QLineEdit,QSpinBox,QComboBox { background:white; border:1px solid #dce3ee; border-radius:7px; padding:8px; selection-background-color:#356cf6; }
        QLineEdit:focus,QSpinBox:focus { border-color:#356cf6; }
        QProgressBar { background:#e9effa; border:0; border-radius:5px; min-height:10px; max-height:10px; }
        QProgressBar::chunk { background:#5684f7; border-radius:5px; }
        QScrollBar:vertical { background:transparent; width:10px; margin:2px; }
        QScrollBar::handle:vertical { background:#cbd5e4; border-radius:4px; min-height:30px; }
        QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }
        QCheckBox { spacing:8px; }
        QToolTip { background:white; color:#233249; border:1px solid #dce3ee; padding:6px; }
    ''')


def completed_files(item):
    """Return only selected, complete, present files confined to the download root."""
    h = item.get('handle')
    if not task_status(item).is_finished:
        return []
    ti = item.get('_ti') or (h.torrent_file() if h is not None else None)
    if ti is None:
        return []
    fs = ti.files()
    progress = h.file_progress() if h is not None else [fs.file_size(i) for i in range(fs.num_files())]
    root = Path(item['folder']).resolve()
    files = []
    for i, priority in enumerate(item['priorities']):
        if not priority or progress[i] < fs.file_size(i):
            continue
        path = (root / fs.file_path(i)).resolve()
        if path.is_relative_to(root) and path.is_file():
            files.append((path, fs.file_size(i)))
    return sorted(files, key=lambda x: x[1], reverse=True)


class SettingsDialog(W.QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('设置'))
        self.setMinimumWidth(650)
        layout = W.QFormLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)
        title = W.QLabel(tr('下载偏好'))
        title.setObjectName('heading')
        layout.addRow(title)
        self.fields = {}
        self.language = W.QComboBox()
        for code, name in LANGUAGES.items():
            self.language.addItem(name, code)
        self.language.setCurrentIndex(self.language.findData(config.get('language', 'zh')))
        layout.addRow('语言 / Language', self.language)
        for key, label, low, high in [('download',tr('下载上限（KB/s，0 为不限）'),0,1000000),
                                      ('upload',tr('上传上限（KB/s，0 为不限）'),0,1000000),
                                      ('active',tr('同时运行任务数'),1,20)]:
            spin = W.QSpinBox()
            spin.setRange(low, high)
            spin.setValue(config[key])
            self.fields[key] = spin
            layout.addRow(label, spin)
        self.folder = W.QLineEdit(config['folder'])
        self.folder.setMinimumWidth(280)
        row = W.QHBoxLayout()
        row.addWidget(self.folder, 1)
        browse = W.QPushButton(tr('选择文件夹…'))
        browse.clicked.connect(self.browse)
        row.addWidget(browse)
        layout.addRow(tr('默认保存目录'), row)
        hint = W.QLabel(tr('用于新添加的任务；已有下载仍保存在原位置。'))
        hint.setObjectName('muted')
        layout.addRow(hint)
        self.seed = W.QCheckBox(tr('下载完成后继续上传做种'))
        self.seed.setChecked(config['seed'])
        layout.addRow(self.seed)
        buttons = W.QDialogButtonBox(W.QDialogButtonBox.Save | W.QDialogButtonBox.Cancel)
        buttons.button(W.QDialogButtonBox.Save).setText(tr('保存设置'))
        buttons.button(W.QDialogButtonBox.Save).setObjectName('primary')
        buttons.button(W.QDialogButtonBox.Cancel).setText(tr('取消'))
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def browse(self):
        folder = W.QFileDialog.getExistingDirectory(self, tr('选择默认保存文件夹'), self.folder.text())
        if folder:
            self.folder.setText(folder)

    def validate(self):
        if not self.folder.text().strip():
            W.QMessageBox.warning(self, tr('请选择目录'), tr('请选择或填写默认保存目录。'))
            return
        self.accept()

    def values(self):
        return dict(**{k:v.value() for k,v in self.fields.items()},
                    folder=self.folder.text().strip(), seed=self.seed.isChecked(), language=self.language.currentData())


def size(n):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024 or unit == 'TB':
            return f'{n:.1f} {unit}'
        n /= 1024


class AddDialog(W.QDialog):
    def __init__(self, source, folder, parent):
        super().__init__(parent)
        self.setWindowTitle(tr('添加种子 · 选择下载内容'))
        self.resize(740, 460)
        ti = inspect_torrent(source)
        layout = W.QVBoxLayout(self)
        title = W.QLabel(ti.name())
        title.setProperty('user_content', True)
        title.setTextFormat(QtCore.Qt.PlainText)
        layout.addWidget(title)
        self.files = W.QTreeWidget()
        self.files.setHeaderLabels([tr('文件'), tr('大小')])
        fs = ti.files()
        video_ext = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.m4v', '.ts', '.webm', '.mpg', '.mpeg'}
        has_video = any(Path(fs.file_path(i)).suffix.lower() in video_ext for i in range(fs.num_files()))
        for i in range(fs.num_files()):
            row = W.QTreeWidgetItem([Path(fs.file_path(i)).name, size(fs.file_size(i))])
            row.setToolTip(0, fs.file_path(i))
            pad = bool(fs.file_flags(i) & fs.flag_pad_file)
            chosen = not pad and (not has_video or Path(fs.file_path(i)).suffix.lower() in video_ext)
            row.setCheckState(0, QtCore.Qt.Checked if chosen else QtCore.Qt.Unchecked)
            if pad:
                row.setDisabled(True)
            self.files.addTopLevelItem(row)
        self.files.header().setSectionResizeMode(0, W.QHeaderView.Stretch)
        self.files.header().setSectionResizeMode(1, W.QHeaderView.ResizeToContents)
        layout.addWidget(self.files)
        if has_video:
            layout.addWidget(W.QLabel(tr('已默认勾选视频文件；其他文件可按需手动勾选。')))
        select = W.QHBoxLayout()
        for label, state in [(tr('全选'), QtCore.Qt.Checked), (tr('全不选'), QtCore.Qt.Unchecked)]:
            b = W.QPushButton(label)
            b.clicked.connect(lambda checked=False, state=state: self.select(state))
            select.addWidget(b)
        select.addStretch()
        layout.addLayout(select)
        row = W.QHBoxLayout()
        self.folder = W.QLineEdit(folder)
        row.addWidget(W.QLabel(tr('保存位置')))
        row.addWidget(self.folder)
        browse = W.QPushButton(tr('浏览…'))
        browse.clicked.connect(self.browse)
        row.addWidget(browse)
        layout.addLayout(row)
        self.start = W.QCheckBox(tr('添加后开始下载'))
        self.start.setChecked(True)
        layout.addWidget(self.start)
        buttons = W.QDialogButtonBox(W.QDialogButtonBox.Ok | W.QDialogButtonBox.Cancel)
        buttons.button(W.QDialogButtonBox.Ok).setText(tr('添加任务'))
        buttons.button(W.QDialogButtonBox.Cancel).setText(tr('取消'))
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def select(self, state):
        for i in range(self.files.topLevelItemCount()):
            item = self.files.topLevelItem(i)
            if not item.isDisabled():
                item.setCheckState(0, state)

    def browse(self):
        folder = W.QFileDialog.getExistingDirectory(self, tr('选择保存目录'), self.folder.text())
        if folder:
            self.folder.setText(folder)

    def priorities(self):
        return [4 if self.files.topLevelItem(i).checkState(0) == QtCore.Qt.Checked else 0
                for i in range(self.files.topLevelItemCount())]

    def validate(self):
        if not any(self.priorities()) or not self.folder.text().strip():
            W.QMessageBox.warning(self, tr('请检查'), tr('请至少勾选一个文件并填写保存目录。'))
        else:
            self.accept()


class Window(W.QMainWindow):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        set_language(engine.config.get('language', 'zh'))
        self._shut_down = False
        self._restore_maximized = False
        self._tray_hint_shown = False
        self.stream = StreamService(engine)
        self.players = {}
        self.setWindowIcon(QtGui.QIcon(str(LOGO_PATH)))
        self.setWindowTitle(f'{APP_NAME} {VERSION}')
        self.resize(1280, 820)
        self.setMinimumSize(1100, 700)
        self.setAcceptDrops(True)
        body = W.QWidget()
        self.setCentralWidget(body)
        layout = W.QVBoxLayout(body)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(18)
        header = W.QHBoxLayout()
        logo = W.QLabel()
        logo.setFixedSize(56, 56)
        logo.setPixmap(QtGui.QPixmap(str(LOGO_PATH)).scaled(112,112,QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))
        logo.setScaledContents(True)
        logo.setAlignment(QtCore.Qt.AlignCenter)
        header.addWidget(logo)
        titles = W.QVBoxLayout()
        titles.setSpacing(2)
        heading = W.QLabel(APP_NAME)
        heading.setWordWrap(True)
        heading.setObjectName('heading')
        titles.addWidget(heading)
        caption = W.QLabel(tr('本地下载 · 边下边看  /  {v0}', v0=f'{VERSION}'))
        caption.setObjectName('muted')
        caption.setWordWrap(True)
        titles.addWidget(caption)
        header.addLayout(titles, 1)
        header.addStretch()
        self.language_combo = W.QComboBox()
        self.language_combo.setAccessibleName('Language')
        for code, name in LANGUAGES.items():
            self.language_combo.addItem(name, code)
        self.language_combo.setCurrentIndex(self.language_combo.findData(language()))
        self.language_combo.currentIndexChanged.connect(self.change_language)
        header.addWidget(self.language_combo)
        self.tray_button = W.QPushButton(tr('收起到托盘'))
        self.tray_button.clicked.connect(self.minimize_to_tray)
        header.addWidget(self.tray_button)
        setting = W.QPushButton(tr('设置'))
        setting.clicked.connect(self.settings)
        header.addWidget(setting)
        layout.addLayout(header)
        metrics = W.QHBoxLayout()
        metrics.setSpacing(14)
        self.metrics = []
        for label in (tr('全部任务'), tr('正在运行'), tr('下载速度'), tr('上传速度')):
            card = W.QFrame()
            card.setObjectName('card')
            box = W.QVBoxLayout(card)
            box.setContentsMargins(18, 13, 18, 13)
            tag = W.QLabel(label)
            tag.setObjectName('eyebrow')
            value = W.QLabel('0')
            value.setObjectName('metric')
            box.addWidget(tag)
            box.addWidget(value)
            self.metrics.append(value)
            metrics.addWidget(card)
        layout.addLayout(metrics)
        bar = W.QGridLayout()
        for label, callback in [(tr('＋ 添加种子'), self.pick), (tr('添加磁力链接'), self.add_magnet), (tr('开始'), lambda: self.toggle(True)),
                                (tr('暂停'), lambda: self.toggle(False)), (tr('停止'),self.stop), (tr('打开文件'), self.open_file),
                                (tr('打开目录'), self.open_folder), (tr('移除任务'), self.remove)]:
            button = W.QPushButton(label)
            button.clicked.connect(callback)
            if label == tr('＋ 添加种子'):
                button.setObjectName('primary')
            index = bar.count()
            bar.addWidget(button, index // 4, index % 4)
        layout.addLayout(bar)
        self.table = W.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([tr('名称'), tr('进度'), tr('下载速度'), tr('上传速度'), tr('连接'), tr('状态'), tr('播放')])
        for col in range(self.table.columnCount()):
            self.table.horizontalHeaderItem(col).setTextAlignment(
                (QtCore.Qt.AlignLeft if col == 0 else QtCore.Qt.AlignHCenter) | QtCore.Qt.AlignVCenter)
        self.table.setSelectionBehavior(W.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(W.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, W.QHeaderView.Stretch)
        self.table.setColumnWidth(5, 185)
        self.table.setColumnWidth(6, 130)
        self.table.itemSelectionChanged.connect(self.details)
        self.table.cellDoubleClicked.connect(lambda row, col: self.open_file() if col != 6 else None)
        self.table.setToolTip(tr('双击已完成任务打开文件；包含多个文件时可选择要打开的文件。'))
        layout.addWidget(self.table, 3)
        info = W.QLabel(tr('任务详情     ·     双击已完成任务即可打开文件'))
        info.setObjectName('eyebrow')
        layout.addWidget(info)
        self.detail = W.QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setMaximumHeight(170)
        layout.addWidget(self.detail, 1)
        self.footer = W.QLabel(tr('就绪'))
        self.footer.setObjectName('muted')
        layout.addWidget(self.footer)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.save_timer = QtCore.QTimer(self)
        self.save_timer.timeout.connect(self.engine.checkpoint)
        self.save_timer.start(30000)
        self.alert_timer = QtCore.QTimer(self)
        self.alert_timer.timeout.connect(self.engine.drain)
        self.alert_timer.start(50)
        self.tray = W.QSystemTrayIcon(self.windowIcon(),self)
        self.tray.setToolTip(f'{APP_NAME} {VERSION}')
        menu = W.QMenu(self)
        menu.addAction(tr('显示主窗口'),self.restore_window)
        menu.addSeparator()
        menu.addAction(tr('退出并停止下载'),self.exit_app)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_activated)
        self.tray.messageClicked.connect(self.restore_window)
        if W.QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        else:
            self.tray_button.setEnabled(False)
            self.tray_button.setToolTip(tr('当前桌面环境没有可用的系统托盘'))
        self.refresh()
        if engine.errors:
            W.QMessageBox.warning(self, tr('部分任务未能恢复'), '\n'.join(engine.errors))

    def minimize_to_tray(self):
        if self._shut_down or not W.QSystemTrayIcon.isSystemTrayAvailable() or not self.tray.isVisible():
            return
        if not self.isMinimized():
            self._restore_maximized = self.isMaximized()
        self.hide()
        if not self._tray_hint_shown:
            self._tray_hint_shown = True
            self.tray.showMessage(APP_NAME,tr('已收起到系统托盘，下载继续。双击图标恢复，右键可退出。'),W.QSystemTrayIcon.Information,3000)

    def restore_window(self):
        if self._shut_down:
            return
        if self._restore_maximized:
            self.showMaximized()
        else:
            self.showNormal()
        self.raise_()
        self.activateWindow()

    def tray_activated(self,reason):
        if reason in (W.QSystemTrayIcon.Trigger,W.QSystemTrayIcon.DoubleClick):
            self.restore_window()

    def changeEvent(self,event):
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.WindowStateChange and self.isMinimized() and hasattr(self,'tray'):
            self._restore_maximized = bool(event.oldState() & QtCore.Qt.WindowMaximized)
            QtCore.QTimer.singleShot(0,self.minimize_to_tray)

    def exit_app(self):
        self.close()
        W.QApplication.instance().quit()

    def key(self):
        row = self.table.currentRow()
        cell = self.table.item(row, 0) if row >= 0 else None
        return cell.data(QtCore.Qt.UserRole) if cell else None

    def pick(self):
        source, _ = W.QFileDialog.getOpenFileName(self, tr('选择种子文件'), str(Path.home() / 'Downloads'), tr('种子文件 (*.torrent)'))
        if source:
            self.add(source)

    def add_magnet(self, uri=''):
        dialog = W.QDialog(self)
        dialog.setWindowTitle(tr('添加磁力链接'))
        dialog.resize(680, 240)
        layout = W.QFormLayout(dialog)
        uri_input = W.QLineEdit(uri if isinstance(uri,str) else '')
        uri_input.setPlaceholderText('magnet:?xt=urn:btih:…')
        layout.addRow(tr('磁力链接'),uri_input)
        folder = W.QLineEdit(self.engine.config['folder'])
        row = W.QHBoxLayout()
        row.addWidget(folder,1)
        browse = W.QPushButton(tr('选择文件夹…'))
        def choose():
            path = W.QFileDialog.getExistingDirectory(dialog,tr('选择保存目录'),folder.text())
            if path:
                folder.setText(path)
        browse.clicked.connect(choose)
        row.addWidget(browse)
        layout.addRow(tr('保存目录'),row)
        hint = W.QLabel(tr('先获取文件信息，再自动下载视频；没有视频时下载全部普通文件。'))
        hint.setWordWrap(True)
        layout.addRow(hint)
        buttons = W.QDialogButtonBox(W.QDialogButtonBox.Ok | W.QDialogButtonBox.Cancel)
        buttons.button(W.QDialogButtonBox.Ok).setText(tr('添加并开始'))
        buttons.button(W.QDialogButtonBox.Cancel).setText(tr('取消'))
        def accept():
            try:
                value = uri_input.text().strip()
                if not value.startswith('magnet:?') or not folder.text().strip():
                    raise ValueError(tr('请填写有效的磁力链接和保存目录'))
                self.engine.add(value,folder.text().strip())
                dialog.accept()
            except Exception as e:
                W.QMessageBox.warning(dialog,tr('无法添加'),str(e))
        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        dialog.exec()
        self.refresh()

    def add(self, source):
        try:
            dialog = AddDialog(source, self.engine.config['folder'], self)
            if dialog.exec() == W.QDialog.Accepted:
                self.engine.add(source, dialog.folder.text().strip(), dialog.priorities(), dialog.start.isChecked())
                self.refresh()
        except Exception as e:
            W.QMessageBox.warning(self, tr('无法添加种子'), str(e))

    def dragEnterEvent(self, event):
        if event.mimeData().text().strip().startswith('magnet:?') or any(u.isLocalFile() and u.toLocalFile().lower().endswith('.torrent') for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().text().strip().startswith('magnet:?'):
            self.add_magnet(event.mimeData().text().strip())
            event.acceptProposedAction()
            return
        for url in event.mimeData().urls():
            if url.isLocalFile() and url.toLocalFile().lower().endswith('.torrent'):
                self.add(url.toLocalFile())
        event.acceptProposedAction()

    def toggle(self, wanted):
        if self.key():
            if not wanted:
                self.close_player(self.key())
            self.engine.toggle(self.key(), wanted)
            self.refresh()

    def stop(self):
        if self.key():
            self.close_player(self.key())
            self.engine.stop(self.key())
            self.refresh()

    def close_player(self,key):
        player = self.players.pop(key,None)
        self.stream.cancel(key)
        if player is not None:
            from shiboken6 import isValid
            if isValid(player):
                player.close()

    def player_closed(self,key,player):
        # A delayed signal from an older player must not cancel its replacement.
        if self.players.get(key) is player:
            self.players.pop(key,None)
            self.stream.cancel(key)

    def preview(self,key):
        item = self.engine.items.get(key)
        if item is None:
            return
        index,ready = self.stream.readiness(item)
        if index is None or ready < 1:
            W.QMessageBox.information(self,tr('视频正在准备'),tr('请等待起播分片下载完成。'))
            return
        self.close_player(key)
        from player import Player
        player = Player(self.stream.url(key,index), item['name'],self)
        self.players[key] = player
        player.closing.connect(lambda:self.player_closed(key,player))
        player.finished.connect(lambda _:self.player_closed(key,player))
        player.destroyed.connect(lambda:self.player_closed(key,player))
        player.show()

    def open_folder(self):
        if self.key():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self.engine.items[self.key()]['folder']))

    def open_file(self):
        key = self.key()
        if not key:
            return
        item = self.engine.items[key]
        if not task_status(item).is_finished:
            W.QMessageBox.information(self, tr('尚未完成'), tr('文件下载完成后即可直接打开。'))
            return
        files = completed_files(item)
        if not files:
            W.QMessageBox.warning(self, tr('找不到文件'), tr('下载文件可能已被移动或删除，请检查保存目录。'))
            return
        path = files[0][0]
        if len(files) > 1:
            dialog = W.QDialog(self)
            dialog.setWindowTitle(tr('选择要打开的文件'))
            dialog.resize(700, 360)
            box = W.QVBoxLayout(dialog)
            box.addWidget(W.QLabel(tr('选择文件后打开，也可以双击；文件按大小排列。')))
            listing = W.QListWidget()
            for file, length in files:
                row = W.QListWidgetItem(f'{file.relative_to(Path(item["folder"]).resolve())}   ·   {size(length)}')
                row.setToolTip(str(file))
                listing.addItem(row)
            listing.setCurrentRow(0)
            box.addWidget(listing)
            buttons = W.QDialogButtonBox(W.QDialogButtonBox.Open | W.QDialogButtonBox.Cancel)
            buttons.button(W.QDialogButtonBox.Open).setText(tr('打开文件'))
            buttons.button(W.QDialogButtonBox.Cancel).setText(tr('取消'))
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            listing.itemDoubleClicked.connect(lambda _: dialog.accept())
            box.addWidget(buttons)
            if dialog.exec() != W.QDialog.Accepted:
                return
            path = files[listing.currentRow()][0]
        if path.suffix.lower() in {'.exe','.com','.bat','.cmd','.ps1','.vbs','.js','.msi','.scr','.lnk','.url','.hta','.reg'}:
            W.QMessageBox.information(self, tr('请从目录打开'), tr('此文件是程序、脚本或快捷方式，请在保存目录中自行检查后打开。'))
            return
        if not QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path))):
            W.QMessageBox.warning(self, tr('无法打开文件'), tr('系统未能打开此文件，请检查默认播放器或文件关联。'))

    def remove(self):
        key = self.key()
        if not key:
            return
        dialog = W.QDialog(self)
        dialog.setWindowTitle(tr('删除任务'))
        layout = W.QVBoxLayout(dialog)
        name = W.QLabel(self.engine.items[key]['name'])
        name.setProperty('user_content', True)
        name.setTextFormat(QtCore.Qt.PlainText)
        layout.addWidget(name)
        delete = W.QCheckBox(tr('同时永久删除此任务已下载的文件（不进入回收站）'))
        layout.addWidget(delete)
        layout.addWidget(W.QLabel(tr('未勾选时，仅删除任务记录，保留下载内容。')))
        buttons = W.QDialogButtonBox(W.QDialogButtonBox.Ok | W.QDialogButtonBox.Cancel)
        buttons.button(W.QDialogButtonBox.Ok).setText(tr('删除任务'))
        buttons.button(W.QDialogButtonBox.Cancel).setText(tr('取消'))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == W.QDialog.Accepted:
            try:
                self.close_player(key)
                self.engine.remove(key,delete.isChecked())
                self.refresh()
            except Exception as e:
                W.QMessageBox.warning(self,tr('无法删除'),str(e))

    def settings(self):
        dialog = SettingsDialog(self.engine.config, self)
        if dialog.exec() == W.QDialog.Accepted:
            self.engine.config.update(dialog.values())
            self.engine.apply_settings()
            self.change_language(code=self.engine.config['language'])

    def change_language(self, index=None, code=None):
        code = code or self.language_combo.currentData()
        old = language()
        set_language(code)
        self.engine.config['language'] = language()
        self.engine.apply_settings()
        self.language_combo.blockSignals(True)
        self.language_combo.setCurrentIndex(self.language_combo.findData(language()))
        self.language_combo.blockSignals(False)
        retranslate_widgets(self, old)
        self.refresh()

    def refresh(self):
        self.engine.tick()
        self.stream.tick()
        selected = self.key()
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.engine.items))
        down = up = running = 0
        for row, (key, item) in enumerate(self.engine.items.items()):
            s = task_status(item)
            down += s.download_payload_rate
            up += s.upload_payload_rate
            running += int(not s.paused)
            values = [item['name'], f'{s.progress * 100:.1f}%', size(s.download_payload_rate)+'/s',
                      size(s.upload_payload_rate)+'/s', str(s.num_peers), status_text(item, s)]
            for col, value in enumerate(values):
                cell = W.QTableWidgetItem('' if col == 1 else value)
                cell.setTextAlignment((QtCore.Qt.AlignLeft if col == 0 else QtCore.Qt.AlignHCenter) | QtCore.Qt.AlignVCenter)
                cell.setToolTip(value)
                if col == 0:
                    cell.setData(QtCore.Qt.UserRole, key)
                self.table.setItem(row, col, cell)
                if col == 5:
                    cell.setForeground(QtGui.QColor('#238464' if s.is_finished else '#4266a3'))
            progress = self.table.cellWidget(row, 1)
            if progress is None:
                progress = W.QWidget()
                box = W.QVBoxLayout(progress)
                box.setContentsMargins(8, 8, 8, 8)
                box.setSpacing(4)
                progress.label = W.QLabel()
                progress.label.setAlignment(QtCore.Qt.AlignCenter)
                progress.bar = W.QProgressBar()
                progress.bar.setRange(0, 1000)
                progress.bar.setTextVisible(False)
                box.addWidget(progress.label)
                box.addWidget(progress.bar)
                self.table.setCellWidget(row, 1, progress)
            progress.label.setText(f'{s.progress * 100:.1f}%')
            progress.bar.setValue(int(s.progress * 1000))
            progress.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            play = self.table.cellWidget(row,6)
            if play is None:
                play = W.QPushButton()
                play.clicked.connect(lambda checked=False,button=play:self.preview(button.property('key')))
                self.table.setCellWidget(row,6,play)
            play.setProperty('key',key)
            video,ready = self.stream.readiness(item)
            play.setEnabled(video is not None and ready >= 1)
            play.setText(tr('▶ 播放') if ready >= 1 else tr('缓冲 {v0}', v0=f'{ready:.0%}') if video is not None else '—')
            play.setToolTip(tr('优先预览选中文件中最大的一个视频。下载不足时播放会等待缓冲。'))
            if key == selected:
                self.table.selectRow(row)
        self.table.blockSignals(False)
        if not selected and self.table.rowCount():
            self.table.selectRow(0)
        for label, value in zip(self.metrics, (str(len(self.engine.items)), str(running), size(down)+'/s', size(up)+'/s')):
            label.setText(value)
        self.footer.setText(tr('最小化到托盘后继续下载                                      关闭窗口或从托盘退出会停止下载'))
        if hasattr(self,'tray'):
            self.tray.setToolTip(tr('{v0} {v1}\n{v2} 个运行任务 · ↓ {v3}/s · ↑ {v4}/s', v0=f'{APP_NAME}', v1=f'{VERSION}', v2=f'{running}', v3=f'{size(down)}', v4=f'{size(up)}'))
        self.details()

    def details(self):
        key = self.key()
        if key not in self.engine.items:
            self.detail.setPlainText(tr('添加一个 .torrent 文件开始。\n\n没有速度时，请查看连接数和此处的状态信息。'))
            return
        item = self.engine.items[key]
        s = task_status(item)
        remaining = max(0, s.total_wanted - s.total_wanted_done)
        eta = tr('{v0} 分钟（估算）', v0=f'{remaining / s.download_payload_rate / 60:.0f}') if s.download_payload_rate else tr('等待有效速度')
        if s.is_finished:
            eta = tr('已完成')
        self.detail.setPlainText(tr('{v0}\n保存位置：{v1}\n已完成：{v2} / {v3}   剩余时间：{v4}\n状态：{v5}   已连接来源：{v6}   已连接完整来源：{v7}\n最近连接/存储提示：{v8}\n提示：暂时找不到来源不代表种子永久失效；本工具无法补出无人提供的分片。', v0=f"{item['name']}", v1=f"{item['folder']}", v2=f'{size(s.total_wanted_done)}', v3=f'{size(s.total_wanted)}', v4=f'{eta}', v5=f'{status_text(item, s)}', v6=f'{s.num_peers}', v7=f'{s.num_seeds}', v8=f"{item['message'] or tr('暂无错误记录')}"))

    def closeEvent(self, event):
        self.shutdown()
        event.accept()

    def shutdown(self):
        if self._shut_down:
            return
        self._shut_down = True
        self.tray.hide()
        self.timer.stop()
        self.save_timer.stop()
        self.alert_timer.stop()
        for key in list(self.players):
            self.close_player(key)
        self.stream.close()
        self.engine.close()


def main():
    from windows_identity import configure
    configure()  # Must precede QApplication and every native window.
    app = W.QApplication(sys.argv)
    theme(app)
    app.setWindowIcon(QtGui.QIcon(str(LOGO_PATH)))
    root = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Torrent_V1' / 'data'
    root.mkdir(parents=True, exist_ok=True)
    lock = QtCore.QLockFile(str(root / 'app.lock'))
    if not lock.tryLock(100):
        W.QMessageBox.information(None, APP_NAME, tr('程序已经运行。若窗口已收起，请双击系统托盘中的 Logo 恢复；升级时先退出旧版本。'))
        return
    engine = Engine(root)
    window = Window(engine)
    app.aboutToQuit.connect(window.shutdown)
    window.show()
    if len(sys.argv) > 1:
        if sys.argv[1].lower().endswith('.torrent'):
            QtCore.QTimer.singleShot(200, lambda: window.add(sys.argv[1]))
        elif sys.argv[1].startswith('magnet:?'):
            QtCore.QTimer.singleShot(200, lambda: window.add_magnet(sys.argv[1]))
    sys.exit(app.exec())


if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--self-test':
        from runtime_smoke import run
        sys.exit(run(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else None))
    else:
        main()
