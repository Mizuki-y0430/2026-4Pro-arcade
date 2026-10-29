"""Web版の進行と保存。画面を開かず、Python標準ライブラリだけで動きます。"""
import copy
import json
import os
from pathlib import Path
import random
import time

from quiz_database import DEFAULT_PATH, QuestionDatabase

DEFAULTS = dict(bg_rgb=[240, 239, 237], accent_rgb=[183, 25, 41], custom_time=45, custom_lives=3, font_idx=0)
HOLE_COUNT = 4


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{low}〜{high}の整数を指定してください。")
    return value


def validated_settings(data):
    if not isinstance(data, dict) or set(data) != set(DEFAULTS):
        raise ValueError("設定項目が不正です。")
    result = copy.deepcopy(data)
    for key in ('bg_rgb', 'accent_rgb'):
        if not isinstance(data[key], list) or len(data[key]) != 3:
            raise ValueError("色はRGBの3要素で指定してください。")
        for value in data[key]:
            integer(value, 0, 255)
    integer(data['custom_time'], 10, 180)
    integer(data['custom_lives'], 1, 10)
    integer(data['font_idx'], 0, 2)
    return result


class Store:
    def __init__(self, folder, original):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.settings = validated_settings(self.load('settings.json', Path(original)/'mole_settings.json', DEFAULTS))
        # 旧標準配色だけを更新し、時間・ライフや独自の配色は保持する。
        if self.settings['bg_rgb'] == [20, 15, 25] and self.settings['accent_rgb'] == [235, 130, 20]:
            self.settings.update(bg_rgb=DEFAULTS['bg_rgb'][:], accent_rgb=DEFAULTS['accent_rgb'][:])
        self.rankings = self.load('rankings.json', Path(original)/'mole_rankings.json', {str(i): [] for i in range(1, 11)})
        if not isinstance(self.rankings, dict):
            raise ValueError("ランキングの形式が不正です。")
        for level in range(1, 11):
            rows = self.rankings.setdefault(str(level), [])
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError("ランキングの形式が不正です。")
        # 元のファイルを読むのは初回のみ。以後はWeb専用のコピーを使います。
        self.save('settings.json', self.settings)
        self.save('rankings.json', self.rankings)

    def load(self, name, legacy, default):
        path = self.folder/name
        source = path if path.exists() else legacy
        return json.loads(source.read_text(encoding='utf-8')) if source.exists() else copy.deepcopy(default)

    def save(self, name, data):
        target = self.folder/name
        temp = target.with_suffix('.tmp')
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temp, target)

    def configure(self, data):
        settings = validated_settings(data)
        self.save('settings.json', settings)
        self.settings = settings

    def add(self, level, entry):
        rankings = copy.deepcopy(self.rankings)
        rankings[str(level)].append(entry)
        self.save('rankings.json', rankings)
        self.rankings = rankings

    def clear(self):
        rankings = {str(i): [] for i in range(1, 11)}
        self.save('rankings.json', rankings)
        self.rankings = rankings

    def ranking(self, level, category):
        integer(level, 1, 10)
        keys = {'score': ('score', 'time_left', 'lives'), 'time': ('time_left', 'score', 'lives'), 'life': ('lives', 'score', 'time_left')}
        if category not in keys:
            raise ValueError("並び順が不正です。")
        return copy.deepcopy(sorted(self.rankings[str(level)], key=lambda row: tuple(row.get(key, 0) for key in keys[category]), reverse=True)[:10])


class WebGame:
    def __init__(self, store, clock=time.monotonic, rng=None, quiz_path=DEFAULT_PATH):
        self.store, self.clock = store, clock
        self.quiz_path = quiz_path
        self.database = QuestionDatabase(quiz_path)
        self.rng = rng or random.Random()
        self.settings = copy.deepcopy(store.settings)
        self.phase, self.level = 'menu', 1
        self.score, self.lives, self.time_left = 0, self.settings['custom_lives'], self.settings['custom_time']
        self.wave, self.revision = 0, 0
        self.moles, self.question, self.feedback = [], '', ''
        self.submitted = False

    def start(self, data):
        if self.phase == 'playing':
            raise ValueError("ゲームはすでに進行中です。")
        level = integer(data.get('level'), 1, 10)
        database = QuestionDatabase(self.quiz_path)
        self.database = database
        self.settings = copy.deepcopy(self.store.settings)
        self.level, self.phase = level, 'playing'
        self.score, self.lives = 0, self.settings['custom_lives']
        self.time_left = self.settings['custom_time']
        self.deadline = self.clock() + self.time_left
        self.submitted = False
        self.feedback = '正解を持ったモグラをたたこう！'
        self.next_question()

    def next_question(self):
        self.question, self.answer, self.dummies = self.database.generate(self.level, self.rng)
        self.spawn()

    def spawn(self):
        self.wave += 1
        self.revision += 1
        holes = self.rng.sample(range(HOLE_COUNT), HOLE_COUNT)
        self.expires = self.clock() + self.rng.randint(60, 120) / 30
        dummies = self.dummies[:]
        self.rng.shuffle(dummies)
        self.moles = [dict(hole=hole, value=str(self.answer if i == 0 else dummies[(i-1) % len(dummies)]), correct=i == 0, hit_until=0) for i, hole in enumerate(holes)]

    def tick(self):
        if self.phase != 'playing':
            return
        now = self.clock()
        self.time_left = max(0, self.deadline-now)
        if self.time_left == 0:
            self.phase = 'result'
            self.revision += 1
            return
        self.moles = [m for m in self.moles if not m['hit_until'] or now < m['hit_until']]
        if now >= self.expires or not self.moles:
            self.spawn()

    def hit(self, data):
        self.tick()
        if self.phase != 'playing':
            raise ValueError("プレイ中だけ回答できます。")
        hole = integer(data.get('hole'), 0, HOLE_COUNT-1)
        if type(data.get('wave')) is not int or data['wave'] != self.wave:
            raise ValueError("モグラが入れ替わりました。もう一度選んでください。")
        mole = next((m for m in self.moles if m['hole'] == hole and not m['hit_until']), None)
        if mole is None:
            raise ValueError("そのモグラはもう隠れています。")
        if mole['correct']:
            self.score += 100
            self.feedback = '正解！ ＋100点'
            self.next_question()
        else:
            self.score = max(0, self.score-50)
            self.lives -= 1
            mole['hit_until'] = self.clock() + 8/30
            self.feedback = 'おしい！ −50点・ライフ−1'
            if self.lives == 0:
                self.phase = 'result'
        self.revision += 1

    def stop(self):
        self.phase = 'menu'
        self.revision += 1

    def configure(self, data):
        if self.phase == 'playing':
            raise ValueError("設定はプレイを終了してから変更してください。")
        self.store.configure(data)
        self.settings = copy.deepcopy(self.store.settings)
        self.revision += 1

    def submit(self, data):
        self.tick()
        if self.phase != 'result' or self.submitted:
            raise ValueError("この結果は登録できません。")
        name = data.get('name', '')
        if not isinstance(name, str) or len(name) > 10 or any(not c.isprintable() for c in name):
            raise ValueError("名前は10文字以内で入力してください。")
        entry = dict(name=name.strip() or 'NO_NAME', score=self.score, time_left=round(self.time_left, 1), lives=self.lives)
        self.store.add(self.level, entry)
        self.submitted = True
        self.revision += 1

    def snapshot(self):
        self.tick()
        return dict(phase=self.phase, level=self.level, score=self.score, lives=self.lives, time_left=round(self.time_left, 2),
                    wave=self.wave, revision=self.revision, stamp=self.clock(), question=self.question, feedback=self.feedback,
                    submitted=self.submitted, settings=copy.deepcopy(self.settings), levels=self.database.level_infos, hole_count=HOLE_COUNT,
                    moles=[dict(hole=m['hole'], value=m['value'], hit=bool(m['hit_until'])) for m in self.moles] if self.phase == 'playing' else [])
