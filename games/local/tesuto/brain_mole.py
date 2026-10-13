import pygame
import random
import sys
import json
import os
from quiz_database import LEVEL_INFOS, generate_question, reload_database

reload_database()

# Pygameの初期化
pygame.init()

# 仮想画面サイズ (Full HD: 1920x1080)
VIRTUAL_WIDTH, VIRTUAL_HEIGHT = 1920, 1080
FPS = 30

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
virtual_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

pygame.display.set_caption("デス・モグラたたき (完全版)")
clock = pygame.time.Clock()

# 基本カラー定義
WHITE = (255, 255, 255)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
BLACK = (20, 20, 20)
HOLE_COLOR = (30, 20, 15)
MOLE_COLOR = (140, 95, 70)
MOLE_HIT_COLOR = (220, 60, 60)
NOSE_COLOR = (230, 140, 160)
CYAN = (52, 152, 219)
YELLOW = (241, 196, 15)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)

# デフォルト設定値
DEFAULT_BG_RGB = [20, 15, 25]
DEFAULT_ACCENT_RGB = [235, 130, 20]
DEFAULT_TIME = 45
DEFAULT_LIVES = 3
DEFAULT_FONT_IDX = 0

# ランキング保存・読込
RANKING_FILE = "mole_rankings.json"

def load_rankings():
    if os.path.exists(RANKING_FILE):
        try:
            with open(RANKING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {str(i): [] for i in range(1, 11)}

def save_rankings(rankings):
    try:
        with open(RANKING_FILE, "w", encoding="utf-8") as f:
            json.dump(rankings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("ランキング保存エラー:", e)

# 詳細設定保存・読込
SETTINGS_FILE = "mole_settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "bg_rgb": list(DEFAULT_BG_RGB),
        "accent_rgb": list(DEFAULT_ACCENT_RGB),
        "custom_time": DEFAULT_TIME,
        "custom_lives": DEFAULT_LIVES,
        "font_idx": DEFAULT_FONT_IDX
    }

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("設定保存エラー:", e)

# モグラ・穴パーツ作成
def create_mole_surfaces():
    hole_surf = pygame.Surface((200, 55), pygame.SRCALPHA)
    pygame.draw.rect(hole_surf, HOLE_COLOR, (0, 0, 200, 55), border_radius=20)

    mole_normal = pygame.Surface((150, 130), pygame.SRCALPHA)
    pygame.draw.rect(mole_normal, MOLE_COLOR, (6, 0, 26, 26), border_radius=6)
    pygame.draw.rect(mole_normal, MOLE_COLOR, (118, 0, 26, 26), border_radius=6)
    pygame.draw.rect(mole_normal, MOLE_COLOR, (0, 20, 150, 110), border_top_left_radius=50, border_top_right_radius=50)
    pygame.draw.rect(mole_normal, BLACK, (36, 60, 12, 12))
    pygame.draw.rect(mole_normal, BLACK, (102, 60, 12, 12))
    pygame.draw.rect(mole_normal, NOSE_COLOR, (65, 75, 20, 12), border_radius=4)

    mole_hit = pygame.Surface((150, 130), pygame.SRCALPHA)
    pygame.draw.rect(mole_hit, MOLE_HIT_COLOR, (6, 0, 26, 26), border_radius=6)
    pygame.draw.rect(mole_hit, MOLE_HIT_COLOR, (118, 0, 26, 26), border_radius=6)
    pygame.draw.rect(mole_hit, MOLE_HIT_COLOR, (0, 20, 150, 110), border_top_left_radius=50, border_top_right_radius=50)
    pygame.draw.line(mole_hit, BLACK, (30, 58), (46, 74), 4)
    pygame.draw.line(mole_hit, BLACK, (46, 58), (30, 74), 4)
    pygame.draw.line(mole_hit, BLACK, (96, 58), (112, 74), 4)
    pygame.draw.line(mole_hit, BLACK, (112, 58), (96, 74), 4)
    pygame.draw.rect(mole_hit, NOSE_COLOR, (65, 75, 20, 12), border_radius=4)

    return hole_surf, mole_normal, mole_hit

SURF_HOLE, SURF_MOLE_NORMAL, SURF_MOLE_HIT = create_mole_surfaces()

HOLE_POSITIONS = []
margin_x, margin_y = 250, 520
spacing_x, spacing_y = 350, 260
for row in range(2):
    for col in range(5):
        HOLE_POSITIONS.append((margin_x + col * spacing_x, margin_y + row * spacing_y))

# 問題と分野は data/questions.xlsx から共通読込します。

class Mole:
    def __init__(self, hole_idx, position):
        self.hole_idx = hole_idx
        self.x, self.y = position
        self.rect = pygame.Rect(self.x - 75, self.y - 110, 150, 110)
        self.value = ""
        self.is_correct = False
        self.is_active = False
        self.timer = 0
        self.hit_timer = 0
        self.text_surf = None
        self.text_rect = None

    def spawn(self, value, is_correct, duration, font):
        self.value = str(value)
        self.is_correct = is_correct
        self.is_active = True
        self.timer = duration
        self.hit_timer = 0
        self.text_surf = font.render(self.value, True, WHITE)
        self.text_rect = self.text_surf.get_rect(center=(self.x, self.y - 75))

    def update_text_font(self, font):
        if self.value and self.is_active:
            self.text_surf = font.render(self.value, True, WHITE)
            self.text_rect = self.text_surf.get_rect(center=(self.x, self.y - 75))

    def update(self):
        if self.hit_timer > 0:
            self.hit_timer -= 1
            if self.hit_timer <= 0:
                self.is_active = False
        elif self.is_active:
            self.timer -= 1
            if self.timer <= 0:
                self.is_active = False

    def draw(self, surface):
        surface.blit(SURF_HOLE, (self.x - 100, self.y - 25))
        if self.is_active:
            mole_surf = SURF_MOLE_HIT if self.hit_timer > 0 else SURF_MOLE_NORMAL
            surface.blit(mole_surf, (self.x - 75, self.y - 110))
            if self.text_surf:
                surface.blit(self.text_surf, self.text_rect)

class MoleGame:
    def __init__(self):
        self.state = "MENU"
        self.database_error = ""
        self.level = 1
        self.score = 0

        self.font_presets = [
            {"name": "ゴシック体", "font": "meiryo,msgothic,hiraginosans,yugothic,arial"},
            {"name": "明朝体 (Serif)", "font": "msmincho,yumincho,hiraginominchopro,georgia,serif"},
            {"name": "丸ゴシック体", "font": "hg丸ｺﾞｼｯｸm-pro,hiragino maru gothic pro,kosugi maru,arial"}
        ]

        loaded_settings = load_settings()
        self.bg_rgb = loaded_settings.get("bg_rgb", list(DEFAULT_BG_RGB))
        self.accent_rgb = loaded_settings.get("accent_rgb", list(DEFAULT_ACCENT_RGB))
        self.custom_time = loaded_settings.get("custom_time", DEFAULT_TIME)
        self.custom_lives = loaded_settings.get("custom_lives", DEFAULT_LIVES)
        self.font_idx = loaded_settings.get("font_idx", DEFAULT_FONT_IDX)

        if not (0 <= self.font_idx < len(self.font_presets)):
            self.font_idx = 0

        self.update_fonts()

        self.lives = self.custom_lives
        self.time_left = float(self.custom_time)
        self.moles = [Mole(i, pos) for i, pos in enumerate(HOLE_POSITIONS)]
        self.q_text = ""
        self.correct_val = ""
        self.dummy_vals = []
        self.q_surf = None
        self.q_rect = None

        self.last_time_int = -1
        self.time_surf = None
        self.score_surf = None
        self.lives_surf = None

        self.user_name = ""
        self.rankings = load_rankings()
        self.view_level = 1
        self.rank_category = "score"
        self.last_registered_entry = None

        # メニュー UIボタン
        self.btn_start_rect = pygame.Rect(250, 130, 420, 75)
        self.btn_ranking_rect = pygame.Rect(750, 130, 420, 75)
        self.btn_settings_rect = pygame.Rect(1250, 130, 420, 75)

        # Lv.1 〜 Lv.10 カード
        self.level_rects = []
        for i in range(5):
            self.level_rects.append(pygame.Rect(120, 270 + i * 145, 800, 130))
        for i in range(5):
            self.level_rects.append(pygame.Rect(1000, 270 + i * 145, 800, 130))

        # 設定画面 UI
        self.btn_settings_back_rect = pygame.Rect(380, 855, 400, 55)
        self.dragging_slider = None

        self.TRACK_X = 480
        self.TRACK_W = 255

        self.slider_keys = [
            ("bg_r", "背景色 R (赤)", 188),
            ("bg_g", "背景色 G (緑)", 233),
            ("bg_b", "背景色 B (青)", 278),
            ("accent_r", "UI色 R (赤)", 373),
            ("accent_g", "UI色 G (緑)", 418),
            ("accent_b", "UI色 B (青)", 463)
        ]

        self.btn_color_reset_rect = pygame.Rect(280, 490, 220, 42)
        self.btn_all_reset_rect   = pygame.Rect(520, 490, 220, 42)

        self.time_display_box = pygame.Rect(260, 590, 180, 45)
        self.btn_time_dec10_rect = pygame.Rect(460, 590, 60, 45)
        self.btn_time_dec5_rect  = pygame.Rect(530, 590, 60, 45)
        self.btn_time_inc5_rect  = pygame.Rect(600, 590, 60, 45)
        self.btn_time_inc10_rect = pygame.Rect(670, 590, 60, 45)

        self.lives_display_box = pygame.Rect(260, 685, 180, 45)
        self.btn_lives_dec1_rect = pygame.Rect(460, 685, 60, 45)
        self.btn_lives_inc1_rect = pygame.Rect(530, 685, 60, 45)

        self.font_btn_rects = [
            pygame.Rect(260, 780, 230, 48),
            pygame.Rect(510, 780, 230, 48),
            pygame.Rect(760, 780, 230, 48)
        ]

        # ランキング UI
        self.btn_rank_back_rect = pygame.Rect(800, 960, 320, 65)
        self.rank_tab_rects = [pygame.Rect(265 + i * 140, 165, 130, 45) for i in range(10)]

        self.btn_rank_cat_score = pygame.Rect(280, 230, 190, 45)
        self.btn_rank_cat_time  = pygame.Rect(490, 230, 190, 45)
        self.btn_rank_cat_life  = pygame.Rect(700, 230, 190, 45)
        self.btn_rank_clear_data= pygame.Rect(1400, 230, 200, 45)

        # 名前入力 Rect
        self.btn_submit_rect = pygame.Rect(710, 740, 500, 75)

        self.update_dashboard_cache()

    def update_fonts(self):
        font_name = self.font_presets[self.font_idx]["font"]
        self.font_small = pygame.font.SysFont(font_name, 22)
        self.font_medium = pygame.font.SysFont(font_name, 30)
        self.font_large = pygame.font.SysFont(font_name, 42)
        self.font_title = pygame.font.SysFont(font_name, 58)

        if hasattr(self, 'moles'):
            for m in self.moles:
                m.update_text_font(self.font_medium)
            if self.q_text:
                self.q_surf = self.font_large.render(self.q_text, True, WHITE)
                self.q_rect = self.q_surf.get_rect(center=(960, 195))

    def save_current_settings(self):
        save_settings({
            "bg_rgb": self.bg_rgb,
            "accent_rgb": self.accent_rgb,
            "custom_time": self.custom_time,
            "custom_lives": self.custom_lives,
            "font_idx": self.font_idx
        })

    def get_current_bg(self):
        return tuple(self.bg_rgb)

    def get_current_theme(self):
        acc = self.accent_rgb
        bg_normal = (max(15, acc[0] // 5), max(15, acc[1] // 5), max(15, acc[2] // 5))
        bg_active = (max(35, acc[0] // 3), max(35, acc[1] // 3), max(35, acc[2] // 3))
        return {
            "bg_normal": bg_normal,
            "bg_active": bg_active,
            "accent": tuple(acc)
        }

    def update_dashboard_cache(self):
        self.score_surf = self.font_medium.render(f"スコア: {self.score}", True, WHITE)
        self.lives_surf = self.font_medium.render(f"ライフ: {'♥ ' * self.lives}", True, RED)

    def start_game(self):
        try:
            reload_database()
            self.database_error = ""
        except ValueError as exc:
            self.database_error = str(exc)
            return
        self.state = "PLAYING"
        self.score = 0
        self.lives = self.custom_lives
        self.time_left = float(self.custom_time)
        self.last_time_int = -1
        self.user_name = ""
        self.last_registered_entry = None
        self.update_dashboard_cache()
        for m in self.moles:
            m.is_active = False
        self.next_question()

    def next_question(self):
        self.q_text, self.correct_val, self.dummy_vals = generate_question(self.level)
        self.q_surf = self.font_large.render(self.q_text, True, WHITE)
        self.q_rect = self.q_surf.get_rect(center=(960, 195))
        self.spawn_moles()

    def spawn_moles(self):
        for m in self.moles:
            m.is_active = False

        count = random.randint(2, 10)
        selected_holes = random.sample(range(10), count)
        duration = random.randint(60, 120)

        self.moles[selected_holes[0]].spawn(self.correct_val, True, duration, self.font_medium)

        random.shuffle(self.dummy_vals)
        for i, hole_idx in enumerate(selected_holes[1:]):
            dummy_val = self.dummy_vals[i % len(self.dummy_vals)]
            self.moles[hole_idx].spawn(dummy_val, False, duration, self.font_medium)

    def update_slider_value(self, key, mouse_x):
        val = max(0, min(255, int(mouse_x - self.TRACK_X)))
        if key == "bg_r": self.bg_rgb[0] = val
        elif key == "bg_g": self.bg_rgb[1] = val
        elif key == "bg_b": self.bg_rgb[2] = val
        elif key == "accent_r": self.accent_rgb[0] = val
        elif key == "accent_g": self.accent_rgb[1] = val
        elif key == "accent_b": self.accent_rgb[2] = val
        self.save_current_settings()

    def handle_click(self, pos):
        if self.state == "PLAYING":
            for mole in self.moles:
                if mole.is_active and mole.hit_timer == 0:
                    if mole.rect.collidepoint(pos):
                        mole.hit_timer = 8
                        if mole.is_correct:
                            self.score += 100
                            self.update_dashboard_cache()
                            self.next_question()
                        else:
                            self.score = max(0, self.score - 50)
                            self.lives -= 1
                            self.update_dashboard_cache()
                            if self.lives <= 0:
                                self.state = "INPUT_NAME"
                        break

        elif self.state == "MENU":
            if self.btn_start_rect.collidepoint(pos):
                self.start_game()
                return

            if self.btn_ranking_rect.collidepoint(pos):
                self.view_level = self.level
                self.last_registered_entry = None
                self.state = "RANKING"
                return

            if self.btn_settings_rect.collidepoint(pos):
                self.state = "SETTINGS"
                return

            for idx, r in enumerate(self.level_rects):
                if r.collidepoint(pos):
                    self.level = idx + 1
                    return

        elif self.state == "SETTINGS":
            if self.btn_settings_back_rect.collidepoint(pos):
                self.save_current_settings()
                self.state = "MENU"
                return

            for key, _, y_pos in self.slider_keys:
                if (self.TRACK_X - 15 <= pos[0] <= self.TRACK_X + self.TRACK_W + 15) and (y_pos - 15 <= pos[1] <= y_pos + 15):
                    self.dragging_slider = key
                    self.update_slider_value(key, pos[0])
                    return

            if self.btn_color_reset_rect.collidepoint(pos):
                self.bg_rgb = list(DEFAULT_BG_RGB)
                self.accent_rgb = list(DEFAULT_ACCENT_RGB)
                self.save_current_settings()
                return

            if self.btn_all_reset_rect.collidepoint(pos):
                self.bg_rgb = list(DEFAULT_BG_RGB)
                self.accent_rgb = list(DEFAULT_ACCENT_RGB)
                self.custom_time = DEFAULT_TIME
                self.custom_lives = DEFAULT_LIVES
                self.font_idx = DEFAULT_FONT_IDX
                self.update_fonts()
                self.update_dashboard_cache()
                self.save_current_settings()
                return

            if self.btn_time_dec10_rect.collidepoint(pos): self.custom_time = max(10, self.custom_time - 10); self.save_current_settings()
            if self.btn_time_dec5_rect.collidepoint(pos):  self.custom_time = max(10, self.custom_time - 5); self.save_current_settings()
            if self.btn_time_inc5_rect.collidepoint(pos):  self.custom_time = min(180, self.custom_time + 5); self.save_current_settings()
            if self.btn_time_inc10_rect.collidepoint(pos): self.custom_time = min(180, self.custom_time + 10); self.save_current_settings()

            if self.btn_lives_dec1_rect.collidepoint(pos): self.custom_lives = max(1, self.custom_lives - 1); self.save_current_settings()
            if self.btn_lives_inc1_rect.collidepoint(pos): self.custom_lives = min(10, self.custom_lives + 1); self.save_current_settings()

            for idx, r in enumerate(self.font_btn_rects):
                if r.collidepoint(pos):
                    self.font_idx = idx
                    self.update_fonts()
                    self.update_dashboard_cache()
                    self.save_current_settings()
                    return

        elif self.state == "RANKING":
            if self.btn_rank_back_rect.collidepoint(pos):
                self.state = "MENU"
                return

            for idx, r in enumerate(self.rank_tab_rects):
                if r.collidepoint(pos):
                    self.view_level = idx + 1
                    return

            if self.btn_rank_cat_score.collidepoint(pos): self.rank_category = "score"
            elif self.btn_rank_cat_time.collidepoint(pos):  self.rank_category = "time"
            elif self.btn_rank_cat_life.collidepoint(pos):  self.rank_category = "life"

            elif self.btn_rank_clear_data.collidepoint(pos):
                self.rankings = {str(i): [] for i in range(1, 11)}
                save_rankings(self.rankings)

        elif self.state == "INPUT_NAME":
            if self.btn_submit_rect.collidepoint(pos):
                self.submit_score()

    def handle_mouse_up(self):
        self.dragging_slider = None

    def handle_mouse_motion(self, pos):
        if self.state == "SETTINGS" and self.dragging_slider:
            self.update_slider_value(self.dragging_slider, pos[0])

    def submit_score(self):
        name = self.user_name.strip() if self.user_name.strip() else "NO_NAME"
        lvl_str = str(self.level)
        if lvl_str not in self.rankings: self.rankings[lvl_str] = []

        entry = {
            "name": name,
            "score": self.score,
            "time_left": round(max(0, self.time_left), 1),
            "lives": self.lives
        }
        self.rankings[lvl_str].append(entry)
        self.last_registered_entry = entry

        save_rankings(self.rankings)
        self.view_level = self.level
        self.state = "RANKING"

    def get_sorted_rankings(self, level_str):
        data = self.rankings.get(level_str, [])
        if self.rank_category == "score":
            return sorted(data, key=lambda x: (x.get("score", 0), x.get("time_left", 0), x.get("lives", 0)), reverse=True)
        elif self.rank_category == "time":
            return sorted(data, key=lambda x: (x.get("time_left", 0), x.get("score", 0), x.get("lives", 0)), reverse=True)
        elif self.rank_category == "life":
            return sorted(data, key=lambda x: (x.get("lives", 0), x.get("score", 0), x.get("time_left", 0)), reverse=True)
        return data

    def update(self):
        if self.state == "PLAYING":
            self.time_left -= 1 / FPS
            if self.time_left <= 0:
                self.time_left = 0
                self.state = "INPUT_NAME"

            current_time_int = int(self.time_left)
            if current_time_int != self.last_time_int:
                self.last_time_int = current_time_int
                self.time_surf = self.font_medium.render(f"残り時間: {current_time_int}秒", True, WHITE)

            active_count = sum(1 for mole in self.moles if mole.is_active)
            for mole in self.moles:
                mole.update()

            if active_count == 0:
                self.spawn_moles()

    def draw(self, surface):
        bg_col = self.get_current_bg()
        theme = self.get_current_theme()

        surface.fill(bg_col)

        if self.state == "MENU":
            title = self.font_title.render("デス・モグラたたき (完全版)", True, RED)
            surface.blit(title, title.get_rect(center=(VIRTUAL_WIDTH//2, 60)))

            pygame.draw.rect(surface, GREEN, self.btn_start_rect, border_radius=15)
            pygame.draw.rect(surface, WHITE, self.btn_start_rect, width=3, border_radius=15)
            t_start = self.font_large.render("ゲームスタート", True, BLACK)
            surface.blit(t_start, t_start.get_rect(center=self.btn_start_rect.center))

            pygame.draw.rect(surface, CYAN, self.btn_ranking_rect, border_radius=15)
            pygame.draw.rect(surface, WHITE, self.btn_ranking_rect, width=3, border_radius=15)
            t_rank = self.font_large.render("ランキング", True, BLACK)
            surface.blit(t_rank, t_rank.get_rect(center=self.btn_ranking_rect.center))

            pygame.draw.rect(surface, DARK_GRAY, self.btn_settings_rect, border_radius=15)
            pygame.draw.rect(surface, theme["accent"], self.btn_settings_rect, width=3, border_radius=15)
            t_sett = self.font_large.render("⚙ 詳細設定", True, WHITE)
            surface.blit(t_sett, t_sett.get_rect(center=self.btn_settings_rect.center))

            info_txt = self.font_small.render(f"※ レベルを選択してスタート（時間: {self.custom_time}秒 / ライフ: {self.custom_lives}機）", True, GRAY)
            surface.blit(info_txt, info_txt.get_rect(center=(VIRTUAL_WIDTH//2, 230)))

            for i in range(10):
                r = self.level_rects[i]
                is_selected = (self.level == i + 1)

                card_bg = theme["bg_active"] if is_selected else theme["bg_normal"]
                border_col = theme["accent"] if is_selected else DARK_GRAY
                border_w = 4 if is_selected else 2

                pygame.draw.rect(surface, card_bg, r, border_radius=14)
                pygame.draw.rect(surface, border_col, r, width=border_w, border_radius=14)

                title_str, sub_str = LEVEL_INFOS[i]
                t_col = YELLOW if is_selected else WHITE

                t_title = self.font_medium.render(title_str, True, t_col)
                t_sub = self.font_small.render(sub_str, True, WHITE if is_selected else GRAY)

                surface.blit(t_title, (r.x + 25, r.y + 20))
                surface.blit(t_sub, (r.x + 25, r.y + 70))

                if is_selected:
                    tag = self.font_medium.render("[ 選択中 ]", True, theme["accent"])
                    surface.blit(tag, (r.right - 150, r.y + 45))

            if self.database_error:
                error_surf = self.font_small.render(self.database_error, True, RED)
                surface.blit(error_surf, (120, 1020))

        elif self.state == "SETTINGS":
            pygame.draw.rect(surface, theme["bg_normal"], (200, 40, 1520, 990), border_radius=20)
            pygame.draw.rect(surface, theme["accent"], (200, 40, 1520, 990), width=4, border_radius=20)

            title_sett = self.font_title.render("⚙ 詳細設定 (SETTINGS)", True, YELLOW)
            surface.blit(title_sett, title_sett.get_rect(center=(VIRTUAL_WIDTH//2, 80)))

            t_sec1 = self.font_medium.render("1. 背景カラー (カーソルドラッグで作成)", True, CYAN)
            surface.blit(t_sec1, (260, 140))

            t_sec2 = self.font_medium.render("2. UIテーマカラー (カーソルドラッグで作成)", True, CYAN)
            surface.blit(t_sec2, (260, 325))

            values_map = {
                "bg_r": self.bg_rgb[0], "bg_g": self.bg_rgb[1], "bg_b": self.bg_rgb[2],
                "accent_r": self.accent_rgb[0], "accent_g": self.accent_rgb[1], "accent_b": self.accent_rgb[2]
            }
            colors_map = {
                "bg_r": RED, "bg_g": GREEN, "bg_b": CYAN,
                "accent_r": RED, "accent_g": GREEN, "accent_b": CYAN
            }

            for key, label, y_pos in self.slider_keys:
                val = values_map[key]
                col = colors_map[key]

                t_lbl = self.font_small.render(f"{label}:", True, col)
                surface.blit(t_lbl, (280, y_pos - 10))

                pygame.draw.rect(surface, DARK_GRAY, (self.TRACK_X, y_pos - 4, self.TRACK_W, 8), border_radius=4)
                pygame.draw.rect(surface, col, (self.TRACK_X, y_pos - 4, val, 8), border_radius=4)

                knob_x = self.TRACK_X + val
                pygame.draw.circle(surface, WHITE, (knob_x, y_pos), 12)
                pygame.draw.circle(surface, col, (knob_x, y_pos), 8)

                t_val = self.font_small.render(f"{val:3d}", True, WHITE)
                surface.blit(t_val, (755, y_pos - 10))

            pygame.draw.rect(surface, YELLOW, self.btn_color_reset_rect, border_radius=8)
            t_c_res = self.font_small.render("🎨 カラーリセット", True, BLACK)
            surface.blit(t_c_res, t_c_res.get_rect(center=self.btn_color_reset_rect.center))

            pygame.draw.rect(surface, RED, self.btn_all_reset_rect, border_radius=8)
            t_a_res = self.font_small.render("🔄 全設定初期化", True, WHITE)
            surface.blit(t_a_res, t_a_res.get_rect(center=self.btn_all_reset_rect.center))

            t_sec3 = self.font_medium.render("3. 制限時間設定 (Time Limit)", True, CYAN)
            surface.blit(t_sec3, (260, 555))

            pygame.draw.rect(surface, BLACK, self.time_display_box, border_radius=10)
            pygame.draw.rect(surface, theme["accent"], self.time_display_box, width=2, border_radius=10)
            t_time_label = self.font_medium.render(f"{self.custom_time} 秒", True, YELLOW)
            surface.blit(t_time_label, t_time_label.get_rect(center=self.time_display_box.center))

            for label, rect, col in [("-10", self.btn_time_dec10_rect, RED), ("-5", self.btn_time_dec5_rect, RED),
                                    ("+5", self.btn_time_inc5_rect, GREEN), ("+10", self.btn_time_inc10_rect, GREEN)]:
                pygame.draw.rect(surface, col, rect, border_radius=8)
                pygame.draw.rect(surface, WHITE, rect, width=1, border_radius=8)
                t_btn = self.font_small.render(label, True, WHITE)
                surface.blit(t_btn, t_btn.get_rect(center=rect.center))

            t_sec4 = self.font_medium.render("4. 初期ライフ設定 (Initial Lives)", True, CYAN)
            surface.blit(t_sec4, (260, 650))

            pygame.draw.rect(surface, BLACK, self.lives_display_box, border_radius=10)
            pygame.draw.rect(surface, theme["accent"], self.lives_display_box, width=2, border_radius=10)
            t_lives_label = self.font_medium.render(f"{self.custom_lives} 機", True, YELLOW)
            surface.blit(t_lives_label, t_lives_label.get_rect(center=self.lives_display_box.center))

            for label, rect, col in [("-1", self.btn_lives_dec1_rect, RED), ("+1", self.btn_lives_inc1_rect, GREEN)]:
                pygame.draw.rect(surface, col, rect, border_radius=8)
                pygame.draw.rect(surface, WHITE, rect, width=1, border_radius=8)
                t_btn = self.font_small.render(label, True, WHITE)
                surface.blit(t_btn, t_btn.get_rect(center=rect.center))

            t_sec5 = self.font_medium.render("5. フォント設定 (Font Style)", True, CYAN)
            surface.blit(t_sec5, (260, 745))

            for i, p in enumerate(self.font_presets):
                r = self.font_btn_rects[i]
                is_sel = (self.font_idx == i)
                btn_bg = theme["accent"] if is_sel else DARK_GRAY
                border_c = GREEN if is_sel else GRAY

                pygame.draw.rect(surface, btn_bg, r, border_radius=10)
                pygame.draw.rect(surface, border_c, r, width=3 if is_sel else 1, border_radius=10)
                t_label = self.font_small.render(p["name"], True, BLACK if is_sel else WHITE)
                surface.blit(t_label, t_label.get_rect(center=r.center))

            pygame.draw.rect(surface, GREEN, self.btn_settings_back_rect, border_radius=12)
            t_back = self.font_medium.render("決定してメニューに戻る", True, BLACK)
            surface.blit(t_back, t_back.get_rect(center=self.btn_settings_back_rect.center))

            t_sec_prev = self.font_large.render("ライブプレビュー", True, CYAN)
            surface.blit(t_sec_prev, (1360, 140))

            prev_box = pygame.Rect(1200, 190, 480, 720)
            pygame.draw.rect(surface, bg_col, prev_box, border_radius=16)
            pygame.draw.rect(surface, WHITE, prev_box, width=2, border_radius=16)

            p_card1 = pygame.Rect(1230, 220, 420, 85)
            pygame.draw.rect(surface, theme["bg_normal"], p_card1, border_radius=10)
            pygame.draw.rect(surface, DARK_GRAY, p_card1, width=2, border_radius=10)
            surface.blit(self.font_small.render("通常カード背景", True, WHITE), (1250, 245))

            p_card2 = pygame.Rect(1230, 320, 420, 95)
            pygame.draw.rect(surface, theme["bg_active"], p_card2, border_radius=10)
            pygame.draw.rect(surface, theme["accent"], p_card2, width=4, border_radius=10)
            surface.blit(self.font_small.render("選択中カード", True, YELLOW), (1250, 335))
            surface.blit(self.font_small.render("[ アクセント枠線 ]", True, theme["accent"]), (1250, 370))

            pygame.draw.rect(surface, HOLE_COLOR, (1340, 540, 200, 40), border_radius=15)
            surface.blit(SURF_MOLE_NORMAL, (1365, 450))
            p_mole_text = self.font_medium.render("クイズ文字", True, WHITE)
            surface.blit(p_mole_text, p_mole_text.get_rect(center=(1440, 485)))

            bg_txt = f"背景 RGB: ({self.bg_rgb[0]}, {self.bg_rgb[1]}, {self.bg_rgb[2]})"
            acc_txt = f"UI RGB: ({self.accent_rgb[0]}, {self.accent_rgb[1]}, {self.accent_rgb[2]})"
            surface.blit(self.font_small.render(bg_txt, True, WHITE), (1240, 610))
            surface.blit(self.font_small.render(acc_txt, True, YELLOW), (1240, 645))

        elif self.state == "PLAYING":
            pygame.draw.rect(surface, theme["bg_normal"], (100, 30, 1720, 90), border_radius=12)

            if self.time_surf: surface.blit(self.time_surf, (150, 55))
            if self.score_surf: surface.blit(self.score_surf, (800, 55))
            if self.lives_surf: surface.blit(self.lives_surf, (1350, 55))

            pygame.draw.rect(surface, theme["accent"], (100, 140, 1720, 110), border_radius=12)
            if self.q_surf: surface.blit(self.q_surf, self.q_rect)

            for mole in self.moles: mole.draw(surface)

        elif self.state == "INPUT_NAME":
            pygame.draw.rect(surface, theme["bg_normal"], (360, 150, 1200, 780), border_radius=20)
            pygame.draw.rect(surface, RED, (360, 150, 1200, 780), width=4, border_radius=20)

            go_title = self.font_title.render("GAME OVER", True, RED)
            res_score = self.font_large.render(f"Lv.{self.level} 結果 - スコア: {self.score}点 | 残り時間: {int(self.time_left)}秒 | 残ライフ: {self.lives}", True, WHITE)
            prompt_txt = self.font_medium.render("ユーザー名を入力してください (英数字10文字以内)", True, CYAN)

            surface.blit(go_title, go_title.get_rect(center=(VIRTUAL_WIDTH//2, 240)))
            surface.blit(res_score, res_score.get_rect(center=(VIRTUAL_WIDTH//2, 340)))
            surface.blit(prompt_txt, prompt_txt.get_rect(center=(VIRTUAL_WIDTH//2, 440)))

            pygame.draw.rect(surface, BLACK, (560, 520, 800, 90), border_radius=12)
            pygame.draw.rect(surface, theme["accent"], (560, 520, 800, 90), width=3, border_radius=12)

            cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
            input_surf = self.font_large.render(self.user_name + cursor, True, YELLOW)
            surface.blit(input_surf, input_surf.get_rect(center=(VIRTUAL_WIDTH//2, 565)))

            pygame.draw.rect(surface, GREEN, self.btn_submit_rect, border_radius=15)
            t_sub = self.font_large.render("送信してランキング登録", True, BLACK)
            surface.blit(t_sub, t_sub.get_rect(center=self.btn_submit_rect.center))

        elif self.state == "RANKING":
            pygame.draw.rect(surface, theme["bg_normal"], (200, 50, 1520, 980), border_radius=20)
            pygame.draw.rect(surface, theme["accent"], (200, 50, 1520, 980), width=4, border_radius=20)

            rank_title = self.font_title.render("🏆 ハイスコアランキング", True, YELLOW)
            surface.blit(rank_title, rank_title.get_rect(center=(VIRTUAL_WIDTH//2, 100)))

            for i in range(10):
                r = self.rank_tab_rects[i]
                is_active = (self.view_level == i + 1)
                tab_bg = theme["accent"] if is_active else DARK_GRAY
                text_col = BLACK if is_active else WHITE

                pygame.draw.rect(surface, tab_bg, r, border_radius=8)
                t_tab = self.font_small.render(f"Lv.{i+1}", True, text_col)
                surface.blit(t_tab, t_tab.get_rect(center=r.center))

            for cat_key, rect, label in [
                ("score", self.btn_rank_cat_score, "★ スコア順"),
                ("time",  self.btn_rank_cat_time,  "⏱ 残り時間順"),
                ("life",  self.btn_rank_cat_life,  "❤️ 残りライフ順")
            ]:
                is_cat_sel = (self.rank_category == cat_key)
                c_bg = theme["accent"] if is_cat_sel else DARK_GRAY
                c_txt = BLACK if is_cat_sel else WHITE

                pygame.draw.rect(surface, c_bg, rect, border_radius=8)
                t_c = self.font_small.render(label, True, c_txt)
                surface.blit(t_c, t_c.get_rect(center=rect.center))

            pygame.draw.rect(surface, RED, self.btn_rank_clear_data, border_radius=8)
            t_clr = self.font_small.render("🗑 データ消去", True, WHITE)
            surface.blit(t_clr, t_clr.get_rect(center=self.btn_rank_clear_data.center))

            surface.blit(self.font_medium.render("順位", True, CYAN), (340, 300))
            surface.blit(self.font_medium.render("ユーザー名", True, CYAN), (580, 300))
            surface.blit(self.font_medium.render("スコア", True, CYAN), (920, 300))
            surface.blit(self.font_medium.render("残り時間", True, CYAN), (1180, 300))
            surface.blit(self.font_medium.render("残ライフ", True, CYAN), (1420, 300))

            pygame.draw.line(surface, GRAY, (280, 340), (1640, 340), 3)

            sorted_list = self.get_sorted_rankings(str(self.view_level))

            for i in range(10):
                y_pos = 355 + i * 52
                rank_str = f"{i + 1}位"

                if i < len(sorted_list):
                    item = sorted_list[i]
                    name_str = str(item.get("name", "---"))
                    score_str = f"{item.get('score', 0)} 点"
                    time_str = f"{item.get('time_left', 0.0)} 秒"
                    life_str = f"{item.get('lives', 0)} 機"
                    is_new = (item is self.last_registered_entry)
                else:
                    name_str = "---"
                    score_str = "---"
                    time_str = "---"
                    life_str = "---"
                    is_new = False

                text_color = GREEN if is_new else WHITE

                t_r = self.font_small.render(rank_str, True, text_color)
                t_n = self.font_small.render(name_str, True, text_color)
                t_s = self.font_small.render(score_str, True, text_color)
                t_t = self.font_small.render(time_str, True, text_color)
                t_l = self.font_small.render(life_str, True, text_color)

                surface.blit(t_r, (350, y_pos))
                surface.blit(t_n, (580, y_pos))
                surface.blit(t_s, (920, y_pos))
                surface.blit(t_t, (1180, y_pos))
                surface.blit(t_l, (1420, y_pos))

            pygame.draw.rect(surface, CYAN, self.btn_rank_back_rect, border_radius=12)
            t_back = self.font_medium.render("メニューに戻る", True, BLACK)
            surface.blit(t_back, t_back.get_rect(center=self.btn_rank_back_rect.center))

def main():
    game = MoleGame()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                vx = event.pos[0] * VIRTUAL_WIDTH / SCREEN_WIDTH
                vy = event.pos[1] * VIRTUAL_HEIGHT / SCREEN_HEIGHT
                game.handle_click((vx, vy))

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                game.handle_mouse_up()

            elif event.type == pygame.MOUSEMOTION:
                vx = event.pos[0] * VIRTUAL_WIDTH / SCREEN_WIDTH
                vy = event.pos[1] * VIRTUAL_HEIGHT / SCREEN_HEIGHT
                game.handle_mouse_motion((vx, vy))

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.state == "SETTINGS":
                        game.save_current_settings()
                        game.state = "MENU"
                    else:
                        pygame.quit()
                        sys.exit()

                if game.state == "MENU":
                    if pygame.K_1 <= event.key <= pygame.K_9: game.level = event.key - pygame.K_1 + 1
                    elif event.key == pygame.K_0: game.level = 10
                    elif event.key == pygame.K_s: game.state = "SETTINGS"
                    elif event.key == pygame.K_r: game.view_level = game.level; game.last_registered_entry = None; game.state = "RANKING"
                    elif event.key == pygame.K_SPACE: game.start_game()

                elif game.state == "SETTINGS":
                    if event.key in (pygame.K_SPACE, pygame.K_s):
                        game.save_current_settings()
                        game.state = "MENU"

                elif game.state == "INPUT_NAME":
                    if event.key == pygame.K_RETURN: game.submit_score()
                    elif event.key == pygame.K_BACKSPACE: game.user_name = game.user_name[:-1]
                    else:
                        if len(game.user_name) < 10 and event.unicode.isprintable() and event.unicode not in ['\r', '\n', '\t']:
                            game.user_name += event.unicode

                elif game.state == "RANKING":
                    if pygame.K_1 <= event.key <= pygame.K_9: game.view_level = event.key - pygame.K_1 + 1
                    elif event.key == pygame.K_0: game.view_level = 10
                    elif event.key == pygame.K_SPACE: game.state = "MENU"

        game.update()

        game.draw(virtual_surface)
        scaled_surf = pygame.transform.smoothscale(virtual_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled_surf, (0, 0))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()