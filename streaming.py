"""Local, token-protected HTTP ranges backed exclusively by verified torrent pieces."""
import mimetypes
import secrets
import threading
import time
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import libtorrent as lt
from engine import VIDEO

class StreamService:
    def __init__(self, engine):
        self.engine = engine
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.inflight = set()
        self.prepared = {}
        self.routes = {}
        self.closed = False
        engine.listeners.append(self.on_alert)
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_HEAD(self):
                self.serve(head=True)

            def do_GET(self):
                self.serve()

            def serve(self, head=False):
                route = owner.routes.get(self.path)
                if route is None:
                    self.send_error(404)
                    return
                key, index = route
                item = owner.engine.items.get(key)
                if not item or item.get('handle') is None or not item.get('_ti'):
                    self.send_error(410)
                    return
                fs = item['_ti'].files()
                length = fs.file_size(index)
                start, end, partial = 0, length - 1, False
                try:
                    value = self.headers.get('Range')
                    if value:
                        if not value.startswith('bytes=') or ',' in value:
                            raise ValueError()
                        a, b = value[6:].split('-', 1)
                        if a:
                            start, end = int(a), min(int(b), length-1) if b else length-1
                        else:
                            count = int(b)
                            if count <= 0:
                                raise ValueError()
                            start = max(0, length-count)
                        partial = True
                    if start < 0 or start >= length or end < start:
                        raise ValueError()
                except ValueError:
                    self.send_response(416)
                    self.send_header('Content-Range', f'bytes */{length}')
                    self.end_headers()
                    return
                sent = False
                try:
                    offset = fs.file_offset(index)
                    piece_len = item['_ti'].piece_length()
                    first = (offset+start)//piece_len
                    # Wait before headers, so a missing first piece gets a proper retryable response.
                    data = owner.read(key, first, self.path) if not head else b''
                    self.send_response(206 if partial else 200)
                    self.send_header('Accept-Ranges', 'bytes')
                    self.send_header('Content-Length', str(end-start+1))
                    self.send_header('Content-Type', mimetypes.guess_type(fs.file_path(index))[0] or 'application/octet-stream')
                    self.send_header('Cache-Control','no-store')
                    if partial:
                        self.send_header('Content-Range', f'bytes {start}-{end}/{length}')
                    self.end_headers()
                    sent = True
                    if head:
                        return
                    cursor = start
                    while cursor <= end and self.path in owner.routes:
                        piece, within = divmod(offset+cursor, piece_len)
                        if piece != first:
                            data = owner.read(key, piece, self.path)
                        count = min(len(data)-within, end-cursor+1)
                        if count <= 0:
                            raise OSError('Invalid verified piece size')
                        self.wfile.write(data[within:within+count])
                        cursor += count
                    self.wfile.flush()
                except (TimeoutError, OSError, RuntimeError, KeyError):
                    # Never substitute sparse-file zeroes or pretend that missing bytes are EOF.
                    if not sent:
                        try:
                            self.send_error(503,'Video data is not ready; retry after buffering')
                        except OSError:
                            pass
                    self.close_connection = True

        self.server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def candidate(self, item):
        ti = item.get('_ti')
        if ti is None or item.get('handle') is None or item.get('mode') in ('stopped','deleting'):
            return None
        fs = ti.files()
        files = [i for i,p in enumerate(item['priorities']) if p and Path(fs.file_path(i)).suffix.lower() in VIDEO
                 and fs.file_size(i) > 0]
        return max(files, key=fs.file_size) if files else None

    def initial_pieces(self, ti, index):
        fs = ti.files()
        offset, length, pl = fs.file_offset(index), fs.file_size(index), ti.piece_length()
        first, last = offset//pl, (offset+length-1)//pl
        head_end = min(last, (offset+min(length,2*1024*1024)-1)//pl)
        tail_start = max(first, (offset+max(0,length-1024*1024))//pl)
        return sorted(set(range(first,head_end+1)) | set(range(tail_start,last+1)))

    def readiness(self, item):
        index = self.candidate(item)
        if index is None:
            return None, 0.
        h = item['handle']
        pieces = self.initial_pieces(item['_ti'],index)
        ready = sum(h.have_piece(p) for p in pieces)
        return index, ready / len(pieces)

    def tick(self):
        for key,item in list(self.engine.items.items()):
            index = self.candidate(item)
            if index is None or not item['wanted']:
                continue
            h = item['handle']
            if self.prepared.get(key) == h:
                continue
            self.prepared[key] = h
            for order, p in enumerate(self.initial_pieces(item['_ti'],index)):
                if not h.have_piece(p):
                    h.set_piece_deadline(p, 500 + order*50)

    def url(self, key, index):
        self.cancel(key)
        path = '/' + secrets.token_urlsafe(24)
        self.routes[path] = (key,index)
        return f'http://127.0.0.1:{self.server.server_port}{path}'

    def cancel(self, key):
        with self.lock:
            for path,route in list(self.routes.items()):
                if route[0] == key:
                    self.routes.pop(path,None)
            item = self.engine.items.get(key,{})
            handles = {item.get('handle'), self.prepared.get(key)} - {None}
            for cached in list(self.cache):
                if cached[0] in handles:
                    self.cache.pop(cached,None)
            self.inflight.difference_update({entry for entry in self.inflight if entry[0] in handles})
            for handle in handles:
                if handle.is_valid():
                    handle.clear_piece_deadlines()

    def read(self, key, piece, token=None):
        deadline = time.monotonic()+45
        requested = False
        while not self.closed and time.monotonic() < deadline:
            if not any(route[0] == key for route in list(self.routes.values())):
                raise OSError('Playback closed')
            item = self.engine.items.get(key)
            h = item.get('handle') if item else None
            if h is None or item.get('mode') in ('stopped','deleting'):
                raise OSError('Task stopped')
            cache_key = (h,piece)
            with self.lock:
                if token is not None and self.routes.get(token,(None,None))[0] != key:
                    raise OSError('Playback session closed')
                if not any(route[0] == key for route in self.routes.values()):
                    raise OSError('Playback closed')
                data = self.cache.get(cache_key)
                if data is not None:
                    self.cache.move_to_end(cache_key)
                    return data
                if h.have_piece(piece) and cache_key not in self.inflight:
                    self.inflight.add(cache_key)
                    h.read_piece(piece)
            if not requested:
                ti = item['_ti']
                for p in range(piece, min(piece+16, ti.num_pieces())):
                    if not h.have_piece(p):
                        h.set_piece_deadline(p, 100+(p-piece)*150)
                requested = True
            time.sleep(.025)
        raise TimeoutError('等待视频分片超时')

    def on_alert(self, alert):
        if isinstance(alert, lt.read_piece_alert):
            key = (alert.handle, alert.piece)
            with self.lock:
                if key not in self.inflight:
                    return  # Ignore late disk reads after the player has closed.
                self.inflight.discard(key)
                if not alert.error.value():
                    self.cache[key] = bytes(alert.buffer)
                    while sum(map(len,self.cache.values())) > 32*1024*1024:
                        self.cache.popitem(last=False)

    def close(self):
        self.closed = True
        for key in list(self.engine.items):
            self.cancel(key)
        with self.lock:
            self.routes.clear()
            self.cache.clear()
            self.inflight.clear()
            self.prepared.clear()
        self.server.shutdown()
        self.server.server_close()
        self.engine.listeners.remove(self.on_alert)
