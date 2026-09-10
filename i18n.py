"""Application translations. Chinese source keys remain stable across releases."""
import re
from string import Formatter
LANGUAGES = {'zh':'简体中文', 'en':'English', 'de':'Deutsch', 'fr':'Français', 'ja':'日本語'}
_language = 'zh'
# Chinese | English | German | French | Japanese
_ROWS = '''设置|Settings|Einstellungen|Paramètres|設定
语言 / Language|语言 / Language|Sprache / Language|Langue / Language|言語 / Language
下载偏好|Download preferences|Download-Einstellungen|Préférences de téléchargement|ダウンロード設定
下载上限（KB/s，0 为不限）|Download limit (KB/s, 0 = unlimited)|Download-Limit (KB/s, 0 = unbegrenzt)|Limite de réception (Ko/s, 0 = illimitée)|受信上限（KB/s、0 は無制限）
上传上限（KB/s，0 为不限）|Upload limit (KB/s, 0 = unlimited)|Upload-Limit (KB/s, 0 = unbegrenzt)|Limite d’envoi (Ko/s, 0 = illimitée)|送信上限（KB/s、0 は無制限）
同时运行任务数|Active task limit|Max. aktive Aufgaben|Nombre maximal de tâches actives|同時実行タスク数
选择文件夹…|Choose folder…|Ordner wählen…|Choisir un dossier…|フォルダーを選択…
默认保存目录|Default download folder|Standard-Downloadordner|Dossier de téléchargement par défaut|既定の保存先
用于新添加的任务；已有下载仍保存在原位置。|Applies to new tasks; existing downloads keep their location.|Gilt für neue Aufgaben; vorhandene Downloads bleiben am bisherigen Ort.|S’applique aux nouvelles tâches ; les téléchargements existants restent au même endroit.|新しいタスクに適用されます。既存の保存先は変わりません。
下载完成后继续上传做种|Continue seeding after download|Nach dem Download weiter verteilen|Continuer le partage après le téléchargement|完了後もシードを続ける
保存设置|Save settings|Speichern|Enregistrer|設定を保存
取消|Cancel|Abbrechen|Annuler|キャンセル
选择默认保存文件夹|Choose default download folder|Standardordner wählen|Choisir le dossier par défaut|既定の保存先を選択
请选择目录|Choose a folder|Ordner wählen|Choisir un dossier|保存先を選択
请选择或填写默认保存目录。|Choose or enter a default download folder.|Bitte einen Standardordner wählen oder eingeben.|Choisissez ou saisissez un dossier par défaut.|既定の保存先を選択または入力してください。
添加种子 · 选择下载内容|Add torrent · Select files|Torrent hinzufügen · Dateien wählen|Ajouter un torrent · Choisir les fichiers|Torrent を追加 · ファイルを選択
文件|File|Datei|Fichier|ファイル
大小|Size|Größe|Taille|サイズ
已默认勾选视频文件；其他文件可按需手动勾选。|Videos are selected by default. Select other files as needed.|Videos sind vorausgewählt. Weitere Dateien bei Bedarf auswählen.|Les vidéos sont présélectionnées. Sélectionnez les autres fichiers si nécessaire.|動画は既定で選択されています。必要に応じて他のファイルも選択できます。
全选|Select all|Alle wählen|Tout sélectionner|すべて選択
全不选|Deselect all|Keine wählen|Tout désélectionner|すべて解除
保存位置|Save location|Speicherort|Emplacement|保存先
浏览…|Browse…|Durchsuchen…|Parcourir…|参照…
添加后开始下载|Start downloading after adding|Nach dem Hinzufügen starten|Démarrer après l’ajout|追加後にダウンロードを開始
添加任务|Add task|Aufgabe hinzufügen|Ajouter la tâche|タスクを追加
选择保存目录|Choose download folder|Downloadordner wählen|Choisir le dossier de téléchargement|保存先を選択
请检查|Check input|Eingabe prüfen|Vérifier la saisie|入力内容を確認
请至少勾选一个文件并填写保存目录。|Select at least one file and enter a download folder.|Mindestens eine Datei und einen Downloadordner wählen.|Sélectionnez au moins un fichier et indiquez un dossier.|ファイルを1つ以上選び、保存先を入力してください。
本地下载 · 边下边看  /  {v0}|Local downloads · Watch while downloading  /  {v0}|Lokal herunterladen · Währenddessen ansehen  /  {v0}|Télécharger en local · Regarder pendant le téléchargement  /  {v0}|ローカル保存 · ダウンロードしながら再生  /  {v0}
收起到托盘|Hide to tray|In den Infobereich|Réduire dans la zone de notification|トレイに格納
全部任务|All tasks|Alle Aufgaben|Toutes les tâches|すべてのタスク
正在运行|Running|Aktiv|En cours|実行中
下载速度|Download|Download|Réception|受信速度
上传速度|Upload|Upload|Envoi|送信速度
＋ 添加种子|＋ Add torrent|＋ Torrent hinzufügen|＋ Ajouter un torrent|＋ Torrent を追加
添加磁力链接|Add magnet link|Magnet-Link hinzufügen|Ajouter un lien magnet|Magnet リンクを追加
开始|Start|Starten|Démarrer|開始
暂停|Pause|Pausieren|Suspendre|一時停止
停止|Stop|Stoppen|Arrêter|停止
打开文件|Open file|Datei öffnen|Ouvrir le fichier|ファイルを開く
打开目录|Open folder|Ordner öffnen|Ouvrir le dossier|フォルダーを開く
移除任务|Remove task|Aufgabe entfernen|Retirer la tâche|タスクを削除
名称|Name|Name|Nom|名前
进度|Progress|Fortschritt|Progression|進捗
连接|Peers|Peers|Pairs|接続数
状态|Status|Status|État|状態
播放|Play|Wiedergabe|Lecture|再生
双击已完成任务打开文件；包含多个文件时可选择要打开的文件。|Double-click a completed task to open a file; choose a file for multi-file tasks.|Abgeschlossene Aufgabe doppelt anklicken; bei mehreren Dateien eine auswählen.|Double-cliquez sur une tâche terminée pour ouvrir un fichier ; choisissez-en un si nécessaire.|完了したタスクをダブルクリックして開きます。複数ある場合はファイルを選択できます。
任务详情     ·     双击已完成任务即可打开文件|Task details     ·     Double-click a completed task to open|Aufgabendetails     ·     Abgeschlossene Aufgabe zum Öffnen doppelt anklicken|Détails     ·     Double-cliquez sur une tâche terminée pour l’ouvrir|タスクの詳細     ·     完了したタスクをダブルクリックして開く
就绪|Ready|Bereit|Prêt|準備完了
显示主窗口|Show window|Fenster anzeigen|Afficher la fenêtre|ウィンドウを表示
退出并停止下载|Exit and stop downloads|Beenden und Downloads stoppen|Quitter et arrêter les téléchargements|ダウンロードを停止して終了
当前桌面环境没有可用的系统托盘|System tray is unavailable on this desktop.|Kein Infobereich auf diesem Desktop verfügbar.|La zone de notification est indisponible.|この環境ではシステムトレイを使用できません。
部分任务未能恢复|Some tasks could not be restored|Einige Aufgaben konnten nicht wiederhergestellt werden|Certaines tâches n’ont pas pu être restaurées|一部のタスクを復元できませんでした
已收起到系统托盘，下载继续。双击图标恢复，右键可退出。|Downloads continue in the tray. Double-click to restore; right-click to exit.|Downloads laufen im Infobereich weiter. Doppelklick zum Öffnen, Rechtsklick zum Beenden.|Les téléchargements continuent. Double-cliquez pour ouvrir ; clic droit pour quitter.|トレイでダウンロードを続行します。ダブルクリックで表示、右クリックで終了できます。
选择种子文件|Choose torrent file|Torrent-Datei wählen|Choisir un fichier torrent|Torrent ファイルを選択
种子文件 (*.torrent)|Torrent files (*.torrent)|Torrent-Dateien (*.torrent)|Fichiers torrent (*.torrent)|Torrent ファイル (*.torrent)
磁力链接|Magnet link|Magnet-Link|Lien magnet|Magnet リンク
保存目录|Download folder|Downloadordner|Dossier de téléchargement|保存先
先获取文件信息，再自动下载视频；没有视频时下载全部普通文件。|Fetch metadata, then download videos automatically; if none, download all regular files.|Zuerst Metadaten abrufen, dann Videos laden; ohne Videos werden alle normalen Dateien geladen.|Récupère les métadonnées puis les vidéos ; sinon, télécharge tous les fichiers ordinaires.|情報を取得してから動画を自動でダウンロードします。動画がなければ通常ファイルをすべて取得します。
添加并开始|Add and start|Hinzufügen und starten|Ajouter et démarrer|追加して開始
请填写有效的磁力链接和保存目录|Enter a valid magnet link and download folder.|Gültigen Magnet-Link und Downloadordner eingeben.|Saisissez un lien magnet valide et un dossier.|有効な Magnet リンクと保存先を入力してください。
无法添加|Could not add task|Hinzufügen fehlgeschlagen|Ajout impossible|追加できません
无法添加种子|Could not add torrent|Torrent konnte nicht hinzugefügt werden|Impossible d’ajouter le torrent|Torrent を追加できません
视频正在准备|Preparing video|Video wird vorbereitet|Préparation de la vidéo|動画を準備中
请等待起播分片下载完成。|Wait for the initial playback pieces to download.|Bitte warten, bis die Startstücke geladen sind.|Attendez le téléchargement des premiers blocs de lecture.|再生開始に必要なピースのダウンロードをお待ちください。
尚未完成|Not finished|Noch nicht abgeschlossen|Non terminé|未完了
文件下载完成后即可直接打开。|The file can be opened once downloading finishes.|Die Datei kann nach Abschluss geöffnet werden.|Le fichier pourra être ouvert une fois téléchargé.|ダウンロード完了後にファイルを開けます。
找不到文件|File not found|Datei nicht gefunden|Fichier introuvable|ファイルが見つかりません
下载文件可能已被移动或删除，请检查保存目录。|The file may have been moved or deleted. Check the download folder.|Die Datei wurde möglicherweise verschoben oder gelöscht. Downloadordner prüfen.|Le fichier a peut-être été déplacé ou supprimé. Vérifiez le dossier.|ファイルが移動または削除された可能性があります。保存先を確認してください。
选择要打开的文件|Choose file to open|Datei zum Öffnen wählen|Choisir le fichier à ouvrir|開くファイルを選択
选择文件后打开，也可以双击；文件按大小排列。|Select a file to open, or double-click. Files are sorted by size.|Datei wählen oder doppelt anklicken. Dateien sind nach Größe sortiert.|Sélectionnez un fichier ou double-cliquez. Les fichiers sont triés par taille.|ファイルを選択するかダブルクリックして開きます。サイズ順で表示しています。
请从目录打开|Open from folder|Aus dem Ordner öffnen|Ouvrir depuis le dossier|フォルダーから開いてください
此文件是程序、脚本或快捷方式，请在保存目录中自行检查后打开。|This is a program, script or shortcut. Inspect it in the download folder before opening.|Dies ist ein Programm, Skript oder eine Verknüpfung. Vor dem Öffnen im Ordner prüfen.|Ce fichier est un programme, script ou raccourci. Vérifiez-le dans le dossier avant de l’ouvrir.|プログラム、スクリプト、またはショートカットです。保存先で内容を確認してから開いてください。
无法打开文件|Could not open file|Datei konnte nicht geöffnet werden|Impossible d’ouvrir le fichier|ファイルを開けません
系统未能打开此文件，请检查默认播放器或文件关联。|Check the default player or file associations.|Standardplayer oder Dateizuordnungen prüfen.|Vérifiez le lecteur par défaut ou les associations de fichiers.|既定のプレーヤーやファイルの関連付けを確認してください。
删除任务|Delete task|Aufgabe löschen|Supprimer la tâche|タスクを削除
同时永久删除此任务已下载的文件（不进入回收站）|Also permanently delete downloaded files (bypass Recycle Bin)|Heruntergeladene Dateien endgültig löschen (ohne Papierkorb)|Supprimer aussi définitivement les fichiers (sans corbeille)|ダウンロード済みファイルも完全に削除（ごみ箱に入れない）
未勾选时，仅删除任务记录，保留下载内容。|Leave unchecked to remove only the task and keep downloaded files.|Ohne Häkchen wird nur die Aufgabe entfernt; Dateien bleiben erhalten.|Sans cette option, seule la tâche est supprimée ; les fichiers sont conservés.|未選択の場合はタスクのみ削除し、ファイルは残します。
无法删除|Could not delete|Löschen fehlgeschlagen|Suppression impossible|削除できません
▶ 播放|▶ Play|▶ Abspielen|▶ Lire|▶ 再生
缓冲 {v0}|Buffering {v0}|Puffern {v0}|Tampon {v0}|バッファー {v0}
优先预览选中文件中最大的一个视频。下载不足时播放会等待缓冲。|Previews the largest selected video. Playback waits if more data is needed.|Vorschau des größten gewählten Videos. Bei fehlenden Daten wird gepuffert.|Prévisualise la plus grande vidéo sélectionnée. La lecture attend si nécessaire.|選択した最大の動画を再生します。データが不足するとバッファリングします。
最小化到托盘后继续下载                                      关闭窗口或从托盘退出会停止下载|Downloads continue in the tray. Closing the window or exiting stops downloads.|Downloads laufen im Infobereich weiter. Fenster schließen oder Beenden stoppt Downloads.|Les téléchargements continuent en arrière-plan. Fermer la fenêtre ou quitter les arrête.|トレイではダウンロードを続行します。ウィンドウを閉じるか終了すると停止します。
等待有效速度|Waiting for data|Warten auf Daten|En attente de données|データを待機中
已完成|Completed|Abgeschlossen|Terminé|完了
{v0} 分钟（估算）|{v0} min (estimated)|{v0} Min. (geschätzt)|{v0} min (estimation)|約 {v0} 分
暂无错误记录|No errors recorded|Keine Fehler protokolliert|Aucune erreur enregistrée|エラー記録なし
程序已经运行。若窗口已收起，请双击系统托盘中的 Logo 恢复；升级时先退出旧版本。|The app is already running. Double-click its tray icon to restore it. Exit the old version before upgrading.|Die App läuft bereits. Zum Öffnen das Symbol im Infobereich doppelt anklicken. Vor dem Update die alte Version beenden.|L’application est déjà ouverte. Double-cliquez sur son icône de notification. Quittez l’ancienne version avant la mise à jour.|すでに起動しています。トレイのアイコンをダブルクリックしてください。更新前に旧版を終了してください。
边下边看 · |Watch while downloading · |Während des Downloads ansehen · |Regarder pendant le téléchargement · |ダウンロードしながら再生 · 
正在读取视频；下载速度不足时会等待缓冲。|Loading video; buffering may occur if downloading is too slow.|Video wird geladen; bei langsamen Downloads wird gepuffert.|Chargement de la vidéo ; une connexion lente peut nécessiter une mise en tampon.|動画を読み込み中です。受信速度が不足するとバッファリングします。
播放 / 暂停|Play / Pause|Wiedergabe / Pause|Lecture / Pause|再生 / 一時停止
音量|Volume|Lautstärke|Volume|音量
暂时无法播放：|Playback unavailable: |Wiedergabe nicht möglich: |Lecture indisponible : |再生できません：
。可继续下载后重新打开。|. Download more data, then reopen.|. Weitere Daten laden und erneut öffnen.|. Téléchargez davantage puis réessayez.|。ダウンロードが進んでから再度開いてください。
种子包含不安全的文件路径|Torrent contains an unsafe file path|Torrent enthält einen unsicheren Dateipfad|Le torrent contient un chemin non sûr|Torrent に安全でないパスが含まれています
暂不支持包含符号链接的种子|Torrents containing symbolic links are not supported|Torrents mit symbolischen Links werden nicht unterstützt|Les torrents contenant des liens symboliques ne sont pas pris en charge|シンボリックリンクを含む Torrent は未対応です
上次删除未完成，请检查文件后重试：|Previous deletion incomplete; check files and retry: |Vorheriges Löschen unvollständig; Dateien prüfen und erneut versuchen: |Suppression précédente incomplète ; vérifiez les fichiers et réessayez : |前回の削除が未完了です。ファイルを確認して再試行してください：
恢复任务失败：|Could not restore task: |Aufgabe konnte nicht wiederhergestellt werden: |Restauration impossible : |タスクを復元できません：
这个任务已经存在|This task already exists|Diese Aufgabe existiert bereits|Cette tâche existe déjà|このタスクはすでに存在します
请至少选择一个文件|Select at least one file|Mindestens eine Datei wählen|Sélectionnez au moins un fichier|ファイルを1つ以上選択してください
磁力链接 · 获取文件信息|Magnet · Fetching metadata|Magnet · Metadaten abrufen|Magnet · Récupération des métadonnées|Magnet · 情報を取得中
缺少下载文件信息，无法安全删除文件。请先开始任务获取信息，或取消勾选删除文件，仅移除任务。|File metadata is missing. Start the task to fetch it, or remove the task without deleting files.|Dateiinformationen fehlen. Aufgabe zum Abrufen starten oder nur die Aufgabe ohne Dateien löschen.|Métadonnées manquantes. Démarrez la tâche pour les récupérer ou retirez-la sans supprimer les fichiers.|ファイル情報がありません。タスクを開始して情報を取得するか、ファイルを残してタスクのみ削除してください。
文件路径超出保存目录，已取消删除|File is outside the download folder; deletion cancelled|Datei außerhalb des Downloadordners; Löschen abgebrochen|Fichier hors du dossier de téléchargement ; suppression annulée|保存先の外にあるため削除を中止しました
文件与另一个任务共用，请先移除任务并保留文件|File is shared with another task; remove the task while keeping files|Datei wird von einer anderen Aufgabe verwendet; Aufgabe ohne Dateien entfernen|Fichier partagé avec une autre tâche ; retirez la tâche en conservant les fichiers|別のタスクと共有しているため、ファイルを残してタスクを削除してください
续传状态保存失败；再次开始时会校验已有文件。|Could not save resume data; existing files will be checked on restart.|Fortsetzungsdaten nicht gespeichert; Dateien werden beim nächsten Start geprüft.|Données de reprise non enregistrées ; les fichiers seront vérifiés au redémarrage.|再開データを保存できませんでした。次回開始時に既存ファイルを検証します。
下载文件信息或存储尚未就绪，请重新开始任务后重试|Metadata or storage not ready; restart the task and retry|Metadaten oder Speicher nicht bereit; Aufgabe neu starten und erneut versuchen|Métadonnées ou stockage indisponibles ; redémarrez la tâche puis réessayez|情報またはストレージの準備ができていません。タスクを再開して再試行してください
文件删除失败：|File deletion failed: |Dateien konnten nicht gelöscht werden: |Échec de suppression des fichiers : |ファイルの削除に失敗しました：
正在删除文件|Deleting files|Dateien werden gelöscht|Suppression des fichiers|ファイルを削除中
已停止|Stopped|Gestoppt|Arrêté|停止済み
错误：|Error: |Fehler: |Erreur : |エラー：
已完成 · 做种中|Completed · Seeding|Fertig · Verteilen|Terminé · Partage|完了 · シード中
已暂停|Paused|Pausiert|Suspendu|一時停止中
排队中|Queued|In Warteschlange|En attente|待機列
正在获取磁力链接信息|Fetching magnet metadata|Magnet-Metadaten abrufen|Récupération des métadonnées magnet|Magnet 情報を取得中
校验已有文件|Checking existing files|Vorhandene Dateien prüfen|Vérification des fichiers|既存ファイルを検証中
下载中|Downloading|Wird heruntergeladen|Téléchargement|ダウンロード中
已连接，等待数据|Connected, waiting for data|Verbunden, warte auf Daten|Connecté, en attente de données|接続済み、データ待機中
正在寻找下载来源|Searching for peers|Peers werden gesucht|Recherche de pairs|接続先を検索中'''
CATALOG = {}
for row in _ROWS.splitlines():
    cells = row.split('|')
    assert len(cells) == 5, row
    CATALOG[cells[0]] = dict(zip(LANGUAGES, cells))

def set_language(code):
    global _language
    _language = code if code in LANGUAGES else 'en'

def language():
    return _language

def tr(source, **values):
    text = CATALOG.get(source, {}).get(_language, source)
    return text.format_map(values) if values else text


def translated_text(text, old_language):
    """Retranslate only registered UI messages, preserving formatted values."""
    for source, translations in CATALOG.items():
        old = translations[old_language]
        if '{' not in old:
            if text == old:
                return tr(source)
            continue
        pattern = ''; names = []
        for literal, field, spec, conversion in Formatter().parse(old):
            pattern += re.escape(literal)
            if field is not None:
                pattern += '(.*?)'; names.append(field)
        match = re.fullmatch(pattern, text, re.DOTALL)
        if match:
            return tr(source, **dict(zip(names, match.groups())))
    return text


def retranslate_widgets(root, old_language):
    from PySide6 import QtCore, QtGui, QtWidgets as W
    for obj in [root, *root.findChildren(QtCore.QObject)]:
        properties = []
        if isinstance(obj, (W.QLabel, W.QAbstractButton, QtGui.QAction)) and not obj.property('user_content'):
            properties.append(('text', 'setText'))
        if isinstance(obj, W.QWidget):
            properties += [('windowTitle','setWindowTitle'), ('toolTip','setToolTip')]
        for getter, setter in properties:
            value = getattr(obj, getter)()
            translated = translated_text(value, old_language)
            if translated != value:
                getattr(obj, setter)(translated)
        if isinstance(obj, W.QTableWidget):
            for col in range(obj.columnCount()):
                item = obj.horizontalHeaderItem(col)
                if item: item.setText(translated_text(item.text(), old_language))

# Multi-line and formatted messages are kept as complete translation units.
_EXTRA = [
 ('{v0}\n保存位置：{v1}\n已完成：{v2} / {v3}   剩余时间：{v4}\n状态：{v5}   已连接来源：{v6}   已连接完整来源：{v7}\n最近连接/存储提示：{v8}\n提示：暂时找不到来源不代表种子永久失效；本工具无法补出无人提供的分片。',
 '{v0}\nLocation: {v1}\nCompleted: {v2} / {v3}   Remaining: {v4}\nStatus: {v5}   Peers: {v6}   Seeds: {v7}\nLatest connection/storage message: {v8}\nTip: no peers now does not mean a torrent is permanently unavailable. Missing pieces require someone sharing them.',
 '{v0}\nSpeicherort: {v1}\nFertig: {v2} / {v3}   Restzeit: {v4}\nStatus: {v5}   Peers: {v6}   Seeds: {v7}\nLetzte Verbindungs-/Speichermeldung: {v8}\nHinweis: Fehlende Peers bedeuten nicht, dass ein Torrent dauerhaft unbrauchbar ist. Fehlende Teile müssen von jemandem angeboten werden.',
 '{v0}\nEmplacement : {v1}\nTerminé : {v2} / {v3}   Temps restant : {v4}\nÉtat : {v5}   Pairs : {v6}   Sources complètes : {v7}\nDernier message réseau/stockage : {v8}\nRemarque : l’absence de pairs peut être temporaire. Les blocs manquants doivent être partagés par une source.',
 '{v0}\n保存先：{v1}\n完了：{v2} / {v3}   残り時間：{v4}\n状態：{v5}   接続数：{v6}   完全なソース数：{v7}\n最新の接続・保存メッセージ：{v8}\nヒント：接続先がなくても永久に無効とは限りません。誰も共有していないピースは取得できません。'),
 ('{v0} {v1}\n{v2} 个运行任务 · ↓ {v3}/s · ↑ {v4}/s',
 '{v0} {v1}\n{v2} active tasks · ↓ {v3}/s · ↑ {v4}/s',
 '{v0} {v1}\n{v2} aktive Aufgaben · ↓ {v3}/s · ↑ {v4}/s',
 '{v0} {v1}\n{v2} tâches actives · ↓ {v3}/s · ↑ {v4}/s',
 '{v0} {v1}\n{v2} 件実行中 · ↓ {v3}/s · ↑ {v4}/s'),
 ('添加一个 .torrent 文件开始。\n\n没有速度时，请查看连接数和此处的状态信息。',
 'Add a .torrent file or magnet link to begin.\n\nIf downloads stall, check the peer count and status here.',
 'Zum Start eine .torrent-Datei oder einen Magnet-Link hinzufügen.\n\nBei Stillstand die Peer-Anzahl und den Status hier prüfen.',
 'Ajoutez un fichier .torrent ou un lien magnet pour commencer.\n\nSi le téléchargement stagne, vérifiez les pairs et l’état ici.',
 '.torrent ファイルまたは Magnet リンクを追加して開始します。\n\n速度が出ない場合は接続数と状態を確認してください。'),
 ('{v0}:{v1} / {v2}:{v3}   ·   跳转到未下载位置可能需要缓冲',
 '{v0}:{v1} / {v2}:{v3}   ·   Seeking to missing data may require buffering',
 '{v0}:{v1} / {v2}:{v3}   ·   Sprünge zu fehlenden Daten erfordern eventuell Puffern',
 '{v0}:{v1} / {v2}:{v3}   ·   Un saut vers des données manquantes peut nécessiter un tampon',
 '{v0}:{v1} / {v2}:{v3}   ·   未取得の位置へ移動するとバッファリングする場合があります'),
 ('边下边看 · {v0}', 'Watch while downloading · {v0}', 'Während des Downloads ansehen · {v0}', 'Regarder pendant le téléchargement · {v0}', 'ダウンロードしながら再生 · {v0}')
]
for row in _EXTRA:
    CATALOG[row[0]] = dict(zip(LANGUAGES, row))
