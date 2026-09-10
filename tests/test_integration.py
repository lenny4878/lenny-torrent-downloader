import concurrent.futures
import os
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import libtorrent as lt
from engine import Engine
from streaming import StreamService

def make_torrent(folder, data, name='sample.bin'):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/name).write_bytes(data)
    fs = lt.file_storage()
    fs.add_file(name,len(data))
    torrent = lt.create_torrent(fs, 16384)
    lt.set_piece_hashes(torrent,str(folder))
    source = folder.parent/(name+'.torrent')
    source.write_bytes(lt.bencode(torrent.generate()))
    return source

class Integration(unittest.TestCase):
    def test_torrent_full_transfer_and_queue(self):
        root=Path(tempfile.mkdtemp(prefix='lenny_full_transfer_'))
        data=os.urandom(256*1024)
        source=make_torrent(root/'seed',data)
        second=make_torrent(root/'other',b'q'*16384,'other.bin')
        opts=dict(enable_dht=False,enable_lsd=False,listen_interfaces='127.0.0.1:0')
        a,b=Engine(root/'a',opts),Engine(root/'b',opts)
        try:
            a.config['seed']=True
            a.add(source,root/'seed',[4])
            b.config['active']=1
            key=b.add(source,root/'download',[4])
            queued=b.add(second,root/'queue',[4])
            b.tick()
            self.assertTrue(b.items[queued]['handle'].status().paused)
            until=time.monotonic()+15
            while time.monotonic()<until:
                a.tick(); b.tick()
                h=b.items[key]['handle']
                h.connect_peer(('127.0.0.1',a.session.listen_port()))
                if h.status().is_finished:
                    break
                time.sleep(.025)
            self.assertTrue(h.status().is_finished)
            b.tick()
            self.assertFalse(b.items[key]['wanted'])
            self.assertFalse(b.items[queued]['handle'].status().paused)
            h.flush_cache()
            time.sleep(.2)
            self.assertEqual((root/'download'/'sample.bin').read_bytes(),data)
        finally:
            a.close(); b.close()

    def test_magnet_stop_ranges_delete(self):
        root = Path(tempfile.mkdtemp(prefix='lenny_integration_'))
        payload = os.urandom(8*1024*1024)
        source = make_torrent(root/'seed',payload)
        opts = dict(enable_dht=False,enable_lsd=False,listen_interfaces='127.0.0.1:0')
        a,b = Engine(root/'a',opts),Engine(root/'b',opts)
        stream = None
        def pump(condition,seconds=20):
            until = time.monotonic()+seconds
            while time.monotonic()<until:
                a.tick(); b.tick()
                if condition():
                    return
                time.sleep(.025)
            self.fail('condition timed out')
        try:
            a.config.update(seed=True,upload=2048)
            a.apply_settings()
            a.add(source,root/'seed',[4])
            b.config.update(download=128)
            b.apply_settings()
            local=b.session.get_peer_class(lt.session.local_peer_class_id)
            local['download_limit']=128*1024
            b.session.set_peer_class(lt.session.local_peer_class_id,local)
            uri = lt.make_magnet_uri(lt.torrent_info(str(source)))
            key = b.add(uri,root/'download')
            def connect():
                b.items[key]['handle'].connect_peer(('127.0.0.1',a.session.listen_port()))
                return b.items[key].get('_ti') is not None
            pump(connect)
            self.assertEqual(b.items[key]['name'],'sample.bin')
            with self.assertRaises(ValueError):
                b.add(source,root/'download',[4])
            pump(lambda:b.items[key]['handle'].status().total_wanted_done>32768)
            b.toggle(key,False)
            self.assertEqual(b.items[key]['mode'],'paused')
            self.assertIsNotNone(b.items[key]['handle'])
            b.stop(key)
            pump(lambda:b.items[key]['handle'] is None)
            b.close()
            b = Engine(root/'b',opts)
            local=b.session.get_peer_class(lt.session.local_peer_class_id)
            local['download_limit']=128*1024
            b.session.set_peer_class(lt.session.local_peer_class_id,local)
            self.assertEqual(b.items[key]['mode'],'stopped')
            self.assertIsNone(b.items[key]['handle'])
            b.toggle(key,True)
            pump(connect)
            stream = StreamService(b)
            url = stream.url(key,0)
            with concurrent.futures.ThreadPoolExecutor() as pool:
                def request(value):
                    req=urllib.request.Request(url,headers={'Range':value})
                    with urllib.request.urlopen(req,timeout=15) as response:
                        return response.status,response.headers.get('Content-Range'),response.read()
                future=pool.submit(request,'bytes=0-127')
                pump(future.done)
                code,header,body=future.result()
                self.assertEqual((code,header,body),(206,f'bytes 0-127/{len(payload)}',payload[:128]))
                future=pool.submit(request,'bytes=-128')
                pump(future.done)
                self.assertEqual(future.result()[2],payload[-128:])
                future=pool.submit(request,f'bytes={len(payload)+1}-')
                pump(future.done)
                with self.assertRaises(urllib.error.HTTPError) as failure:
                    future.result()
                self.assertEqual(failure.exception.code,416)
            self.assertFalse(b.items[key]['handle'].status().is_finished, 'range read must work before completion')
            stream.close(); stream=None
            b.remove(key)
            self.assertTrue((root/'download'/'sample.bin').exists())
            key=b.add(uri,root/'download')
            pump(connect)
            (root/'download'/'unrelated.txt').write_text('keep me')
            b.stop(key)
            pump(lambda:b.items[key]['handle'] is None)
            b.close()
            b=Engine(root/'b',opts)
            self.assertIsNotNone(b.params(b.items[key]).ti)
            b.remove(key,True)
            pump(lambda:key not in b.items)
            self.assertFalse((root/'download'/'sample.bin').exists())
            self.assertTrue((root/'download'/'unrelated.txt').exists())
            print('PASS: magnet metadata, duplicate detection, pause vs unload, restart, verified partial HTTP ranges, keep/delete and unrelated-file preservation',flush=True)
        finally:
            if stream:
                stream.close()
            a.close(); b.close()

    def test_magnet_without_metadata_can_be_removed(self):
        root=Path(tempfile.mkdtemp(prefix='lenny_empty_magnet_'))
        e=Engine(root/'state',dict(enable_dht=False,enable_lsd=False))
        try:
            uri='magnet:?xt=urn:btih:'+'1'*40
            for stopped in (False,True):
                key=e.add(uri,root/'downloads',wanted=False)
                if stopped:
                    e.stop(key)
                    until=time.monotonic()+3
                    while e.items[key]['handle'] is not None and time.monotonic()<until:
                        e.tick(); time.sleep(.02)
                (root/'downloads'/'unrelated.txt').write_text('keep')
                e.remove(key,True)
                self.assertNotIn(key,e.items)
                self.assertTrue((root/'downloads'/'unrelated.txt').exists())
        finally:
            e.close()

if __name__ == '__main__':
    unittest.main()
