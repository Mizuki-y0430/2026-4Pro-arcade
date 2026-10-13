"""Web化した進行管理とHTTP境界の回帰テスト。外部パッケージ不要。"""
import copy
import json
from pathlib import Path
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chess.web_game import WebGame
from web import make_server


class Clock:
    def __init__(self):
        self.now = 100

    def __call__(self):
        return self.now


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.web = WebGame(self.clock)

    def play(self):
        self.web.start()
        self.clock.now += 3
        self.web.tick()

    def test_countdown_blocks_moves_and_stop_cancels_start(self):
        self.web.start()
        with self.assertRaises(ValueError):
            self.web.move(dict(sr=6,sc=4,er=4,ec=4))
        self.assertEqual(self.web.snapshot()['countdown'], 3)
        self.web.stop()
        self.clock.now += 10
        self.web.tick()
        self.assertEqual(self.web.phase, 'paused')
        self.assertEqual(self.web.game.move_count, 0)

    def test_realtime_human_moves_cooldown_and_illegal_moves(self):
        self.play()
        self.web.move(dict(sr=6,sc=4,er=4,ec=4))
        with self.assertRaises(ValueError):
            self.web.move(dict(sr=6,sc=3,er=4,ec=3))
        self.clock.now += .5
        self.web.move(dict(sr=6,sc=3,er=4,ec=3))
        self.assertEqual(self.web.game.move_count, 2)  # 黒の手を待たずに再移動。
        self.clock.now += .5
        with self.assertRaises(ValueError):
            self.web.move(dict(sr=1,sc=4,er=3,ec=4))
        with self.assertRaises(ValueError):
            self.web.move(dict(sr=6,sc=0,er=2,ec=0))
        self.assertEqual(self.web.game.move_count, 2)

    def test_bad_coordinates_and_promotion_cannot_mutate_board(self):
        self.play()
        before = copy.deepcopy(self.web.game.board)
        for invalid in [dict(sr=True,sc=4,er=4,ec=4),dict(sr=6,sc=4,er=9,ec=4),dict(sr=6,sc=4,er=4,ec=4,promotion='K')]:
            with self.assertRaises(ValueError):
                self.web.move(invalid)
        self.assertEqual(self.web.game.board, before)

    def test_ai_uses_original_engine_and_stop_freezes_board(self):
        self.play()
        self.clock.now += 1
        self.web.tick()
        self.assertEqual(self.web.game.history[-1][2][0], 'b')
        self.web.stop()
        before = copy.deepcopy(self.web.game.board)
        self.clock.now += 10
        self.web.tick()
        self.assertEqual(self.web.game.board, before)

    def test_settings_validate_all_fields_before_mutation(self):
        with self.assertRaises(ValueError):
            self.web.configure(dict(mode='aivsai',cooldown_ms=True))
        self.assertEqual(self.web.mode, 'ai')
        self.web.configure(dict(level='strong',cooldown_ms=0,animation=False))
        self.assertEqual((self.web.level,self.web.cooldown_ms,self.web.animation),('strong',0,False))

    def test_auto_mode_and_piece_cooldown(self):
        self.web.configure(dict(mode='aivsai'))
        self.play()
        self.web.piece_cd.clear()
        self.clock.now += 1
        self.web.tick()
        first = self.web.game.history[-1]
        self.assertEqual(first[2][0], 'w')
        self.assertGreater(self.web.piece_cd[first[1]],self.clock.now)
        self.clock.now += 1
        self.web.tick()
        self.assertEqual(self.web.game.history[-1][2][0], 'b')
        with self.assertRaises(ValueError):
            self.web.move(dict(sr=6,sc=4,er=4,ec=4))

    def test_checkmate_score_and_auto_rematch(self):
        self.web.configure(dict(mode='aivsai'))
        self.play()
        for move in [(6,5,5,5),(1,4,3,4),(6,6,4,6)]:
            self.assertTrue(self.web.game.move(*move))
        self.assertTrue(self.web._apply(0,3,4,7))
        self.assertEqual(self.web.phase,'finished')
        self.assertEqual(self.web.match_score['b'],1)
        self.assertEqual(self.web.snapshot()['rematch_in'],3)
        self.clock.now += 3
        self.web.tick()
        self.assertEqual(self.web.phase,'playing')
        self.assertEqual(self.web.game.move_count,0)
        self.assertEqual(self.web.match_no,2)
        self.assertEqual(self.web.match_score['b'],1)

    def test_stop_after_finish_prevents_auto_rematch(self):
        self.web.configure(dict(mode='aivsai'));self.play()
        for move in [(6,5,5,5),(1,4,3,4),(6,6,4,6)]:
            self.web.game.move(*move)
        self.web._apply(0,3,4,7);self.web.stop()
        self.clock.now += 30;self.web.tick()
        self.assertTrue(self.web.game.game_over)
        self.assertEqual(self.web.match_no,1)

    def test_promotion_and_snapshot_is_detached(self):
        self.play()
        self.web.game.board=[[None]*8 for _ in range(8)]
        self.web.game.board[7][7]='wK';self.web.game.board[0][7]='bK';self.web.game.board[1][0]='wP'
        self.web.move(dict(sr=1,sc=0,er=0,ec=0,promotion='R'))
        self.assertEqual(self.web.game.board[0][0],'wR')
        snap=self.web.snapshot();snap['board'][0][0]=None
        self.assertEqual(self.web.game.board[0][0],'wR')


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=make_server()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
        cls.thread=threading.Thread(target=cls.server.serve_forever,kwargs={'poll_interval':.05},daemon=True)
        cls.thread.start()
        cls.opener=build_opener(ProxyHandler({}))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2)

    def call(self,path,data=None,headers=None):
        hdr={'Origin':self.base};hdr.update(headers or {})
        request=Request(self.base+path,data=None if data is None else json.dumps(data).encode(),headers=hdr)
        try:
            response=self.opener.open(request,timeout=3)
        except HTTPError as error:
            response=error
        with response:
            raw=response.read()
            return response.code,json.loads(raw) if 'application/json' in response.headers.get('Content-Type','') else raw

    def test_independent_sessions_and_tk_free_import(self):
        _,first=self.call('/api/session');_,second=self.call('/api/session')
        self.call('/api/start',{}, {'X-Chess-Token':first['token']})
        _,one=self.call('/api/state',headers={'X-Chess-Token':first['token']})
        _,two=self.call('/api/state',headers={'X-Chess-Token':second['token']})
        self.assertEqual((one['phase'],two['phase']),('countdown','ready'))
        self.assertNotIn('tkinter',sys.modules)

    def test_missing_token_and_wrong_origin_rejected(self):
        self.assertEqual(self.call('/api/state')[0],403)
        self.assertEqual(self.call('/api/reset',{})[0],403)
        _,session=self.call('/api/session')
        code,_=self.call('/api/start',{}, {'X-Chess-Token':session['token'],'Origin':'https://example.invalid'})
        self.assertEqual(code,403)

    def test_bad_data_and_unknown_paths(self):
        _,session=self.call('/api/session');headers={'X-Chess-Token':session['token']}
        self.assertEqual(self.call('/api/settings',[],headers)[0],400)
        self.assertEqual(self.call('/api/settings',{'cooldown_ms':-1},headers)[0],400)
        self.assertEqual(self.call('/api/unknown',{},headers)[0],404)
        self.assertEqual(self.call('/../chess.py')[0],404)

    def test_assets_and_host_check(self):
        for path in ('/','/game.js','/style.css'):
            self.assertEqual(self.call(path)[0],200)
        self.assertEqual(self.call('/api/session',headers={'Host':'example.invalid'})[0],403)


if __name__=='__main__':
    unittest.main()
