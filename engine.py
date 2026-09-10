import json
import os
import time
from pathlib import Path
from types import SimpleNamespace
import libtorrent as lt

VIDEO = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.m4v', '.ts', '.webm', '.mpg', '.mpeg'}

def atomic(path, data):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_bytes(data)
    os.replace(tmp, path)

def validate_info(ti):
    fs = ti.files()
    for i in range(fs.num_files()):
        name = fs.file_path(i).replace('\\', '/')
        if name.startswith('/') or '..' in name.split('/') or ':' in name:
            raise ValueError('种子包含不安全的文件路径')
        if fs.file_flags(i) & lt.file_storage.flag_symlink:
            raise ValueError('暂不支持包含符号链接的种子')
    return ti

def inspect_torrent(path):
    return validate_info(lt.torrent_info(str(path)))

def default_priorities(ti):
    fs = ti.files()
    videos = [Path(fs.file_path(i)).suffix.lower() in VIDEO for i in range(fs.num_files())]
    return [4 if not (fs.file_flags(i) & fs.flag_pad_file) and (videos[i] or not any(videos)) else 0
            for i in range(fs.num_files())]

def task_status(item):
    h = item.get('handle')
    if h is not None and h.is_valid():
        return h.status()
    saved = item.get('summary', {})
    total, done = saved.get('total', 0), saved.get('done', 0)
    return SimpleNamespace(is_finished=bool(total and done >= total), has_metadata=item.get('_ti') is not None,
        paused=True, progress=done / total if total else 0., total_wanted=total, total_wanted_done=done,
        num_peers=0, num_seeds=0, download_payload_rate=0, upload_payload_rate=0,
        errc=SimpleNamespace(value=lambda:0), state=None)

class Engine:
    def __init__(self, root, extra=None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.items, self.pending, self.errors = {}, set(), []
        self.listeners = []
        self.config = dict(download=0, upload=512, active=3, seed=False,
                           folder=str(Path.home() / 'Downloads' / 'Torrent'))
        if (self.root / 'settings.json').exists():
            self.config.update(json.loads((self.root / 'settings.json').read_text('utf-8')))
        settings = dict(listen_interfaces='0.0.0.0:0', enable_dht=True, enable_lsd=True,
                        enable_upnp=False, enable_natpmp=False, ignore_limits_on_local_network=False,
                        alert_mask=int(lt.alert.category_t.error_notification |
                                       lt.alert.category_t.storage_notification |
                                       lt.alert.category_t.status_notification |
                                       lt.alert.category_t.tracker_notification))
        settings.update(extra or {})
        self.session = lt.session(settings)
        self.apply_settings()
        index = self.root / 'tasks.json'
        if index.exists():
            for item in json.loads(index.read_text('utf-8')):
                try:
                    item.setdefault('mode', 'running' if item.get('wanted') else 'paused')
                    if item['mode'] == 'deleting':
                        item['mode'] = 'stopped'
                        self.errors.append('上次删除未完成，请检查文件后重试：' + item['name'])
                    item.update(handle=None, message='')
                    p = self.params(item)
                    item['_ti'] = validate_info(p.ti) if p.ti else None
                    self.items[item['key']] = item
                    if item['mode'] != 'stopped':
                        item['handle'] = self.session.add_torrent(p)
                except Exception as e:
                    self.errors.append('恢复任务失败：' + str(e))

    def params(self, item):
        key = item['key']
        resume = self.root / (key + '.resume')
        source = self.root / (key + '.torrent')
        if resume.exists():
            p = lt.read_resume_data(resume.read_bytes())
        elif item.get('magnet'):
            p = lt.parse_magnet_uri(item['magnet'])
        else:
            p = lt.add_torrent_params()
        if source.exists():
            p.ti = inspect_torrent(source)
        elif p.ti is None and item.get('_ti') is not None:
            p.ti = validate_info(item['_ti'])
        if item.get('priorities'):
            p.file_priorities = item['priorities']
        p.save_path = item['folder']
        p.flags &= ~lt.torrent_flags.auto_managed
        p.flags |= lt.torrent_flags.paused | lt.torrent_flags.duplicate_is_error
        return p

    def apply_settings(self):
        self.session.apply_settings(dict(download_rate_limit=int(self.config['download'])*1024,
                                         upload_rate_limit=int(self.config['upload'])*1024))
        atomic(self.root / 'settings.json', json.dumps(self.config, ensure_ascii=False).encode('utf-8'))

    def persist(self):
        records = [{k:v for k,v in x.items() if k not in ('handle','message') and not k.startswith('_')}
                   for x in self.items.values()]
        atomic(self.root / 'tasks.json', json.dumps(records, ensure_ascii=False).encode('utf-8'))

    def add(self, source, folder, priorities=None, wanted=True):
        magnet = str(source).strip().startswith('magnet:?')
        p = lt.parse_magnet_uri(str(source).strip()) if magnet else lt.add_torrent_params()
        ti = None if magnet else inspect_torrent(source)
        hashes = p.info_hashes if magnet else ti.info_hashes()
        key = str(hashes.v2 if hashes.has_v2() else hashes.v1)
        if key in self.items:
            raise ValueError('这个任务已经存在')
        # Compare both hashes, so hybrid torrent/magnet aliases cannot create duplicate tasks.
        for x in self.items.values():
            other = self.params(x).info_hashes if not x.get('_ti') else x['_ti'].info_hashes()
            if ((hashes.has_v1() and other.has_v1() and hashes.v1 == other.v1) or
                (hashes.has_v2() and other.has_v2() and hashes.v2 == other.v2)):
                raise ValueError('这个任务已经存在')
        if ti:
            priorities = priorities if priorities is not None else default_priorities(ti)
            if len(priorities) != ti.num_files() or not any(priorities):
                raise ValueError('请至少选择一个文件')
            p.ti, p.file_priorities = ti, priorities
        Path(folder).mkdir(parents=True, exist_ok=True)
        p.save_path = str(Path(folder).resolve())
        p.flags &= ~lt.torrent_flags.auto_managed
        p.flags |= lt.torrent_flags.paused | lt.torrent_flags.duplicate_is_error
        h = self.session.add_torrent(p)
        if ti:
            atomic(self.root / (key + '.torrent'), Path(source).read_bytes())
        self.items[key] = dict(key=key, name=ti.name() if ti else p.name or '磁力链接 · 获取文件信息',
            folder=p.save_path, priorities=priorities or [], wanted=wanted,
            mode='running' if wanted else 'paused', handle=h, message='', _ti=ti,
            magnet=str(source).strip() if magnet else '')
        self.persist()
        return key

    def toggle(self, key, wanted):
        item = self.items[key]
        if item['mode'] == 'deleting':
            return
        if wanted and item.get('handle') is None:
            item['handle'] = self.session.add_torrent(self.params(item))
        item['wanted'] = wanted
        item['mode'] = 'running' if wanted else 'paused'
        if not wanted and item.get('handle') is not None:
            item['handle'].pause()
            self.save_resume(key)
        self.persist()

    def stop(self, key):
        item = self.items[key]
        if item['mode'] == 'deleting':
            return
        s = task_status(item)
        item['summary'] = dict(total=s.total_wanted, done=s.total_wanted_done)
        item.update(wanted=False, mode='stopped')
        h = item.get('handle')
        if h is not None:
            h.pause()
            self.save_resume(key)
            # Detach only after saving resume data. UI stays responsive while the alert arrives.
            item['_detach'] = True
        self.persist()

    def remove(self, key, delete_files=False):
        item = self.items[key]
        if delete_files:
            ti = item.get('_ti')
            h = item.get('handle')
            if ti is None and h is not None and h.is_valid() and h.status().has_metadata:
                ti = validate_info(h.torrent_file())
                item['_ti'] = ti
            if ti is None:
                ti = self.params(item).ti
            if ti is None:
                if item.get('summary',{}).get('done',0) or item.get('priorities'):
                    raise ValueError('缺少下载文件信息，无法安全删除文件。请先开始任务获取信息，或取消勾选删除文件，仅移除任务。')
                # A metadata-less magnet has no payload files or disk storage to delete.
                self.remove(key,False)
                return
            if ti:
                fs = validate_info(ti).files()
                root = Path(item['folder']).resolve()
                targets = {(root / fs.file_path(i)).resolve() for i in range(fs.num_files())}
                if any(not p.is_relative_to(root) for p in targets):
                    raise ValueError('文件路径超出保存目录，已取消删除')
                for other in self.items.values():
                    if other is item or not other.get('_ti'):
                        continue
                    ofs = other['_ti'].files()
                    paths = {(Path(other['folder']) / ofs.file_path(i)).resolve() for i in range(ofs.num_files())}
                    if targets & paths:
                        raise ValueError('文件与另一个任务共用，请先移除任务并保留文件')
            if item.get('handle') is None:
                item['handle'] = self.session.add_torrent(self.params(item))
            item.update(mode='deleting', wanted=False)
            item.pop('_detach', None)
            self.session.remove_torrent(item['handle'], lt.options_t.delete_files)
            self.persist()
        else:
            if item.get('handle') is not None:
                self.session.remove_torrent(item['handle'])
            self.forget(key)

    def forget(self, key):
        self.items.pop(key, None)
        self.pending.discard(key)
        for suffix in ('.torrent','.resume'):
            (self.root / (key + suffix)).unlink(missing_ok=True)
        self.persist()

    def save_resume(self, key):
        h = self.items[key].get('handle')
        if h is not None and h.is_valid() and key not in self.pending:
            self.pending.add(key)
            h.save_resume_data(lt.save_resume_flags_t.save_info_dict)

    def drain(self):
        for a in self.session.pop_alerts():
            for listener in self.listeners:
                listener(a)
            key = next((k for k,x in self.items.items() if getattr(a,'handle',None) == x.get('handle')),None)
            if not key:
                continue
            item = self.items[key]
            if isinstance(a, lt.save_resume_data_alert):
                atomic(self.root / (key + '.resume'), bytes(lt.write_resume_data_buf(a.params)))
                self.pending.discard(key)
                if item.pop('_detach', False) and item['mode'] == 'stopped':
                    self.session.remove_torrent(item['handle'])
                    item['handle'] = None
            elif isinstance(a, lt.save_resume_data_failed_alert):
                self.pending.discard(key)
                if item.pop('_detach', False):
                    self.session.remove_torrent(item['handle'])
                    item['handle'] = None
                    item['message'] = '续传状态保存失败；再次开始时会校验已有文件。'
            elif isinstance(a, lt.torrent_deleted_alert):
                self.forget(key)
            elif isinstance(a, lt.torrent_delete_failed_alert):
                error = a.error.message() if a.error.value() else '下载文件信息或存储尚未就绪，请重新开始任务后重试'
                item.update(handle=None, mode='stopped', message='文件删除失败：' + error)
                self.errors.append(item['message'])
                self.persist()
            elif isinstance(a, (lt.tracker_error_alert, lt.file_error_alert, lt.torrent_error_alert)):
                item['message'] = a.message()

    def tick(self):
        self.drain()
        active = 0
        changed = False
        for key,x in list(self.items.items()):
            h = x.get('handle')
            if h is None or not h.is_valid() or x['mode'] in ('stopped','deleting'):
                continue
            s = h.status()
            if s.has_metadata and x.get('_ti') is None:
                try:
                    x['_ti'] = validate_info(h.torrent_file())
                    x['name'] = x['_ti'].name()
                    if not x['priorities']:
                        x['priorities'] = default_priorities(x['_ti'])
                        h.prioritize_files(x['priorities'])
                    self.save_resume(key)
                    changed = True
                except Exception as e:
                    x['message'] = str(e)
                    self.stop(key)
                    continue
            if s.is_finished and not self.config['seed'] and x['wanted']:
                x.update(wanted=False,mode='paused')
                changed = True
                self.save_resume(key)
            run = x['wanted'] and active < self.config['active'] and not s.errc.value()
            if run:
                active += 1
                if s.paused:
                    h.resume()
            elif not s.paused:
                h.pause()
        if changed:
            self.persist()

    def checkpoint(self):
        self.persist()
        for key in self.items:
            self.save_resume(key)

    def close(self):
        self.session.pause()
        self.checkpoint()
        deadline = time.monotonic() + 6
        while self.pending and time.monotonic() < deadline:
            self.drain()
            time.sleep(.05)

def status_text(item, s):
    if item.get('mode') == 'deleting':
        return '正在删除文件'
    if item.get('mode') == 'stopped':
        return '已停止'
    if s.errc.value():
        return '错误：' + s.errc.message()
    if s.is_finished:
        return '已完成 · 做种中' if not s.paused else '已完成'
    if not item['wanted']:
        return '已暂停'
    if s.paused:
        return '排队中'
    if not s.has_metadata:
        return '正在获取磁力链接信息'
    if s.state in (lt.torrent_status.checking_files, lt.torrent_status.checking_resume_data):
        return '校验已有文件'
    if s.download_payload_rate:
        return '下载中'
    return '已连接，等待数据' if s.num_peers else '正在寻找下载来源'
