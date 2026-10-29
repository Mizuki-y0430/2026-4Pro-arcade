"""原作との問題一致、時間・回答・保存・HTTP境界を確認します。"""
import copy
import json
from pathlib import Path
import random
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from web_game import DEFAULTS, Store, WebGame
from web_quiz import generate_question
from web import make_server
from test_quiz_database import edit_copy


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.store = Store(self.folder/'data', self.folder/'original')
        self.now = 100.0
        self.game = WebGame(self.store, lambda: self.now, random.Random(8))

    def start(self, level=1):
        self.game.start({'level': level})

    def hit(self, correct):
        mole = next(m for m in self.game.moles if m['correct'] == correct and not m['hit_until'])
        self.game.hit(dict(hole=mole['hole'], wave=self.game.wave))

    def test_excel_provides_all_levels_without_loading_pygame(self):
        for level in range(1, 11):
            for _ in range(50):
                q, answer, wrong = generate_question(level)
                self.assertTrue(q and str(answer) and wrong)
            self.start(level)
            self.assertEqual(sum(m['correct'] for m in self.game.moles), 1)
            self.game.stop()
        self.assertEqual(len(self.game.database.level_infos), 10)
        self.assertNotIn('pygame', sys.modules)

    def test_correct_replaces_question_and_wrong_deducts_life(self):
        self.start()
        wave = self.game.wave
        self.hit(True)
        self.assertEqual(self.game.score, 100)
        self.assertGreater(self.game.wave, wave)
        self.hit(False)
        self.assertEqual((self.game.score, self.game.lives), (50, 2))
        self.now += .3
        self.game.tick()
        self.hit(False)
        self.assertEqual((self.game.score, self.game.lives), (0, 1))
        self.game.spawn()
        self.hit(False)
        self.assertEqual(self.game.phase, 'result')

    def test_four_targets_keep_one_correct_answer_at_random_positions(self):
        positions = set()
        for level in range(1, 11):
            self.game.stop()
            self.start(level)
            for _ in range(20):
                snapshot = self.game.snapshot()
                self.assertEqual(snapshot['hole_count'], 4)
                self.assertEqual({m['hole'] for m in snapshot['moles']}, set(range(4)))
                correct = [m for m in self.game.moles if m['correct']]
                self.assertEqual(len(correct), 1)
                self.assertEqual(correct[0]['value'], str(self.game.answer))
                self.assertTrue(all(m['value'] != str(self.game.answer) for m in self.game.moles if not m['correct']))
                positions.add(correct[0]['hole'])
                self.game.next_question()
        self.assertEqual(positions, set(range(4)))

    def test_old_default_palette_migrates_without_losing_other_settings(self):
        legacy = self.folder/'legacy'
        legacy.mkdir()
        old = {**DEFAULTS, 'bg_rgb': [20, 15, 25], 'accent_rgb': [235, 130, 20], 'custom_time': 90, 'custom_lives': 5}
        (legacy/'mole_settings.json').write_text(json.dumps(old), encoding='utf-8')
        migrated = Store(self.folder/'migrated', legacy)
        self.assertEqual(migrated.settings, {**DEFAULTS, 'custom_time': 90, 'custom_lives': 5})
        custom = {**old, 'accent_rgb': [100, 20, 30]}
        migrated.configure(custom)
        self.assertEqual(Store(self.folder/'migrated', legacy).settings, custom)

    def test_hit_repeat_and_old_wave_cannot_change_score(self):
        self.start()
        bad = next(m for m in self.game.moles if not m['correct'])
        data = dict(hole=bad['hole'], wave=self.game.wave)
        self.game.hit(data)
        with self.assertRaises(ValueError):
            self.game.hit(data)
        self.game.spawn()
        with self.assertRaises(ValueError):
            self.game.hit(data)
        self.assertEqual(self.game.lives, 2)

    def test_deadline_and_hidden_moles_use_elapsed_time(self):
        self.start()
        wave, question = self.game.wave, self.game.question
        self.now += 5
        self.game.tick()
        self.assertGreater(self.game.wave, wave)
        self.assertEqual(self.game.question, question)
        self.now += 40
        self.game.tick()
        self.assertEqual((self.game.phase, self.game.time_left), ('result', 0))
        with self.assertRaises(ValueError):
            self.hit(True)

    def test_settings_validate_atomically_and_persist(self):
        for patch in [dict(custom_time=True),dict(custom_time=9),dict(custom_lives=11),dict(bg_rgb=[1,2,999]),dict(font_idx=4)]:
            with self.assertRaises(ValueError):
                self.game.configure({**DEFAULTS, **patch})
            self.assertEqual(self.store.settings, DEFAULTS)
        changed = {**DEFAULTS, 'custom_time': 10, 'custom_lives': 1, 'bg_rgb': [80,120,200]}
        self.game.configure(changed)
        self.assertEqual(Store(self.folder/'data', self.folder/'original').settings, changed)
        self.start()
        self.assertEqual((self.game.time_left, self.game.lives), (10, 1))
        with self.assertRaises(ValueError):
            self.game.configure(DEFAULTS)

    def test_submit_once_server_score_and_original_files_preserved(self):
        original = self.folder/'original'
        original.mkdir()
        original_file = original/'mole_rankings.json'
        original_file.write_text('{"1":[{"name":"original","score":1000}]}',encoding='utf-8')
        store = Store(self.folder/'copied', original)
        game = WebGame(store, lambda: self.now)
        game.start({'level':1})
        with self.assertRaises(ValueError):
            game.submit({'name':'early'})
        self.now += 45
        game.tick()
        with self.assertRaises(ValueError):
            game.submit({'name':'long_name_123'})
        game.submit({'name':'', 'score':99999})
        self.assertEqual(store.rankings['1'][-1]['score'], 0)
        self.assertEqual(store.rankings['1'][-1]['name'], 'NO_NAME')
        with self.assertRaises(ValueError):
            game.submit({'name':'again'})
        store.clear()
        self.assertEqual(json.loads(original_file.read_text(encoding='utf-8'))['1'][0]['score'], 1000)
        self.assertEqual(Store(self.folder/'copied', original).ranking(1,'score'), [])

    def test_rank_order_legacy_missing_fields_and_snapshot_copy(self):
        for entry in [dict(name='a',score=100),dict(name='b',score=50,time_left=8,lives=3)]:
            self.store.add(1,entry)
        self.assertEqual(self.store.ranking(1,'score')[0]['name'],'a')
        self.assertEqual(self.store.ranking(1,'time')[0]['name'],'b')
        self.assertEqual(self.store.ranking(1,'life')[0]['name'],'b')
        self.start()
        snapshot=self.game.snapshot()
        self.assertNotIn('correct',snapshot['moles'][0])
        snapshot['settings']['custom_time']=180
        self.assertEqual(self.game.settings['custom_time'],45)

    def test_invalid_inputs_stop_and_restart(self):
        for level in (True,0,11,'1'):
            with self.assertRaises(ValueError):
                self.game.start({'level':level})
        self.start()
        with self.assertRaises(ValueError):
            self.start()
        for hole in (True,-1,4,9,10,'1'):
            with self.assertRaises(ValueError):
                self.game.hit({'hole':hole,'wave':self.game.wave})
        self.game.stop()
        with self.assertRaises(ValueError):
            self.game.hit({'hole':0,'wave':self.game.wave})
        self.start(10)
        self.assertEqual((self.game.score,self.game.lives,self.game.level),(0,3,10))


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.server=make_server(data_dir=Path(self.temp.name))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.close)
        self.base=f'http://127.0.0.1:{self.server.server_port}'
        self.opener=build_opener(ProxyHandler({}))
        self.token=self.call('/api/session')['token']

    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def call(self,path,data=None,headers=None):
        h={'X-Mole-Token':self.token} if hasattr(self,'token') else {}
        if data is not None:h.update(Origin=self.base,**{'Content-Type':'application/json'})
        h.update(headers or {})
        request=Request(self.base+path,headers=h,data=json.dumps(data).encode() if data is not None else None)
        with self.opener.open(request,timeout=5) as response:
            raw=response.read()
            return json.loads(raw) if response.headers.get_content_type()=='application/json' else raw

    def test_session_isolation_and_assets_no_pygame(self):
        second=self.call('/api/session')['token']
        self.call('/api/start',{'level':7})
        self.assertEqual(self.call('/api/state')['phase'],'playing')
        self.assertEqual(self.call('/api/state',headers={'X-Mole-Token':second})['phase'],'menu')
        for path in ('/','/game.js','/style.css'):
            self.assertTrue(self.call(path))
        self.assertNotIn('pygame',sys.modules)

    def test_origin_host_token_and_source_routes(self):
        for path,data,headers,code in [('/api/start',{'level':1},{'Origin':'https://example.invalid'},403),('/api/start',{'level':1},{'X-Mole-Token':'bad'},403),('/api/state',None,{'Host':'evil.invalid'},403),('/brain_mole.py',None,{},404),('/.web-data/rankings.json',None,{},404)]:
            with self.assertRaises(HTTPError) as error:
                self.call(path,data,headers)
            self.assertEqual(error.exception.code,code)

    def test_malformed_data_and_ranking_parameters(self):
        for path,data in [('/api/start',[]),('/api/start',{'level':False}),('/api/hit',{'hole':0,'wave':1}),('/api/settings',{})]:
            with self.assertRaises(HTTPError) as error:
                self.call(path,data)
            self.assertEqual(error.exception.code,400)
        for path in ('/api/rankings?level=11','/api/rankings?level=abc','/api/rankings?sort=bad'):
            with self.assertRaises(HTTPError) as error:
                self.call(path)
            self.assertEqual(error.exception.code,400)
        self.assertIn('entries',self.call('/api/rankings?level=1&sort=score'))

    def test_excel_error_is_reported_and_fixed_file_can_start(self):
        path = Path(self.temp.name)/'questions.xlsx'
        edit_copy(path, {'E2': None})
        game = self.server.sessions[self.token]['game']
        game.quiz_path = path
        with self.assertRaises(HTTPError) as error:
            self.call('/api/start', {'level': 2})
        self.assertEqual(error.exception.code, 400)
        detail = json.loads(error.exception.read())['error']
        self.assertIn('問題一覧', detail)
        self.assertIn('2行目', detail)
        self.assertEqual(game.phase, 'menu')
        edit_copy(path, {'E2': 'H'})
        self.assertEqual(self.call('/api/start', {'level': 2})['phase'], 'playing')


if __name__=='__main__':
    unittest.main()
