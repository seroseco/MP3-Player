import json, time, subprocess, math, os, sys, random, io, unicodedata, threading, tempfile, importlib, shutil, calendar
import pygame
try:
    from mutagen import File as MutagenFile
except Exception:
    MutagenFile = None
PILImage = None
PILImageOps = None
try:
    PILImage = importlib.import_module("PIL.Image")
    PILImageOps = importlib.import_module("PIL.ImageOps")
except Exception:
    pass

# ---------------------------
# 마치 PMP같은 런처 (HVGA)
# ---------------------------


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "system", "config.json")
LEGACY_CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
ICON_DIR = os.path.join(BASE_DIR, "system", "UI", "icons")
UI_DIR = os.path.join(BASE_DIR, "system", "UI")
FONT_DIR = os.path.join(BASE_DIR, "system", "font")
LEGACY_FONT_DIR = os.path.join(BASE_DIR, "system", "fonts")
LANG_DIR = os.path.join(BASE_DIR, "system", "lang")
DEFAULT_WALLPAPER = "./system/UI/default1.png"
DEFAULT_ALBUM_ART = os.path.join(UI_DIR, "albumart.png")
DEFAULT_VIDEO_THUMB = os.path.join(UI_DIR, "videoimg.png")
DEFAULT_TEXT_THUMB = os.path.join(UI_DIR, "txtimg.png")
DEFAULT_PHOTO_THUMB = os.path.join(UI_DIR, "photoimg.png")
SOFTWARE_INFO_VERSION = "Roy's PMP 1.0.1"
LEGACY_VIDEO_THUMB = os.path.join(BASE_DIR, "system", "ui", "videoimg.png")
MUSIC_DIR = os.path.join(BASE_DIR, "files", "music")
VIDEO_DIR = os.path.join(BASE_DIR, "files", "video")
IMAGE_DIR = os.path.join(BASE_DIR, "files", "image")
DOCUMENT_DIR = os.path.join(BASE_DIR, "files", "document")
TRASH_IMAGE_DIR = os.path.join(BASE_DIR, "files", ".trash", "files", "image")
TRASH_META_PATH = os.path.join(BASE_DIR, "files", ".trash", "meta", "data.json")

STATUS_H = 36
MARGIN = 10
GRID_COLS = 3
GRID_ROWS = 4
ICON_W = 92
ICON_H = 92
GAP_X = 10
GAP_Y = 14

LONG_PRESS_MS = 650
SWIPE_THRESHOLD = 55  # resistive: bigger threshold
PHOTO_COLS = 4
PHOTO_ROTATION_FIXES = {
    # EXIF 방향 정보가 없거나 잘못된 특정 파일을 수동 보정한다.
    "img_6963.jpeg": -90,
    "img_2868.jpeg": -90,
    "img_3297.jpeg": -90,
}


def load_config():
    data = {}
    # 기본 설정 파일 우선, 없으면 레거시 설정을 읽어 마이그레이션한다.
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = loaded
        except Exception:
            data = {}
    elif os.path.isfile(LEGACY_CONFIG_PATH):
        try:
            with open(LEGACY_CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = loaded
                    save_config(data)
        except Exception:
            data = {}
    return data if isinstance(data, dict) else {}


def save_config(cfg):
    # 설정은 항상 UTF-8 JSON으로 저장한다.
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def clamp(x, a, b):
    return max(a, min(b, x))


def norm_text(s):
    try:
        return unicodedata.normalize("NFC", str(s))
    except Exception:
        return str(s)


def normalize_language(code):
    # 입력 언어 코드를 내부 표준 코드(ko/en/ja/custom)로 정규화한다.
    c = str(code).strip().lower()
    if c.startswith("custom") or c == "user":
        return "custom"
    if c.startswith("en"):
        return "en"
    if c.startswith("ja") or c.startswith("jp"):
        return "ja"
    return "ko"


def load_language_pack(lang):
    # 언어 코드에 맞는 언어팩 JSON을 로드한다.
    lang_code = normalize_language(lang)
    if lang_code == "custom":
        filename = "custom.json"
    elif lang_code == "en":
        filename = "en-us.json"
    elif lang_code == "ja":
        filename = "ja-jp.json"
    else:
        filename = "ko-kr.json"
    path = os.path.join(LANG_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


THEMES = {
    "light": {
        "home_bg": (255, 255, 255),
        "panel_bg": (255, 255, 255),
        "panel_border": (220, 224, 232),
        "button_bg": (246, 248, 252),
        "button_border": (210, 215, 225),
        "icon_bg": (240, 244, 250),
        "icon_border": (208, 214, 224),
        "text": (14, 18, 24),
        "status_bg": (255, 255, 255),
        "status_line": (225, 230, 238),
        "status_text": (12, 16, 22),
        "toast_bg": (255, 255, 255),
        "toast_border": (210, 216, 228),
        "toast_text": (18, 24, 34),
        "pager_active": (16, 20, 28),
        "pager_inactive": (170, 176, 188),
        "settings_bg": (255, 255, 255),
        "power_bg": (255, 255, 255),
        "power_text": (12, 16, 22),
    },
    "dark": {
        "home_bg": (0, 0, 0),
        "panel_bg": (0, 0, 0),
        "panel_border": (48, 52, 60),
        "button_bg": (20, 22, 28),
        "button_border": (62, 68, 80),
        "icon_bg": (18, 20, 26),
        "icon_border": (72, 78, 92),
        "text": (246, 248, 255),
        "status_bg": (0, 0, 0),
        "status_line": (52, 58, 70),
        "status_text": (246, 248, 255),
        "toast_bg": (12, 14, 20),
        "toast_border": (92, 104, 130),
        "toast_text": (246, 248, 255),
        "pager_active": (246, 248, 255),
        "pager_inactive": (92, 100, 118),
        "settings_bg": (0, 0, 0),
        "power_bg": (0, 0, 0),
        "power_text": (246, 248, 255),
    },
    "transparent": {
        "home_bg": (0, 0, 0),
        "panel_bg": (16, 18, 24),
        "panel_border": (84, 94, 116),
        "button_bg": (24, 26, 34),
        "button_border": (96, 108, 132),
        "icon_bg": (22, 24, 32),
        "icon_border": (110, 124, 152),
        "text": (246, 248, 255),
        "status_bg": (0, 0, 0),
        "status_line": (60, 68, 84),
        "status_text": (246, 248, 255),
        "toast_bg": (16, 18, 24),
        "toast_border": (120, 132, 160),
        "toast_text": (246, 248, 255),
        "pager_active": (246, 248, 255),
        "pager_inactive": (100, 112, 136),
        "settings_bg": (0, 0, 0),
        "power_bg": (0, 0, 0),
        "power_text": (246, 248, 255),
    },
}

ACCENT_PRESETS = {
    "blue": (84, 136, 210),
    "green": (44, 198, 88),
    "pinkred": (228, 86, 118),
    "warmyellow": (232, 198, 54),
    "orange": (242, 142, 42),
    "gray": (128, 128, 128),
}

HANGUL_CHOSEONG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
HANGUL_JUNGSEONG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
HANGUL_JONGSEONG = ["", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
HANGUL_JONG_COMBINE = {
    ("ㄱ", "ㅅ"): "ㄳ",
    ("ㄴ", "ㅈ"): "ㄵ",
    ("ㄴ", "ㅎ"): "ㄶ",
    ("ㄹ", "ㄱ"): "ㄺ",
    ("ㄹ", "ㅁ"): "ㄻ",
    ("ㄹ", "ㅂ"): "ㄼ",
    ("ㄹ", "ㅅ"): "ㄽ",
    ("ㄹ", "ㅌ"): "ㄾ",
    ("ㄹ", "ㅍ"): "ㄿ",
    ("ㄹ", "ㅎ"): "ㅀ",
    ("ㅂ", "ㅅ"): "ㅄ",
}
HANGUL_JONG_SPLIT = {v: k for k, v in HANGUL_JONG_COMBINE.items()}
HANGUL_JUNG_BACKSTEP = {
    "ㅐ": "ㅏ",
    "ㅒ": "ㅑ",
    "ㅔ": "ㅓ",
    "ㅖ": "ㅕ",
    "ㅘ": "ㅗ",
    "ㅙ": "ㅘ",
    "ㅚ": "ㅗ",
    "ㅛ": "ㅗ",
    "ㅝ": "ㅜ",
    "ㅞ": "ㅝ",
    "ㅟ": "ㅜ",
    "ㅠ": "ㅜ",
    "ㅢ": "ㅡ",
    "ㅑ": "ㅏ",
    "ㅕ": "ㅓ",
    "ㅏ": "ㆍ",
    "ㅓ": "ㅣ",
    "ㅗ": "ㆍ",
    "ㅜ": "ㅡ",
}


class Button:
    def __init__(self, rect, label, app, icon=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.app = app
        self.icon = icon
        self.pressed = False

    def draw(self, surf, small_font, pal):
        r = self.rect.copy()
        if self.pressed:
            r.y += 2

        if self.icon:
            ix = r.centerx - self.icon.get_width() // 2
            iy = r.y + 6
            shadow = self.icon.copy()
            shadow.fill((0, 0, 0, 120), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(shadow, (ix + 2, iy + 3))
            surf.blit(self.icon, (ix, iy))

        text_shadow = small_font.render(self.label, True, (0, 0, 0))
        text = small_font.render(self.label, True, (255, 255, 255))
        tx = r.centerx - text.get_width() // 2
        ty = r.bottom - 10
        surf.blit(text_shadow, (tx + 1, ty + 1))
        surf.blit(text, (tx, ty))


class Shell:
    def __init__(self, cfg):
        self.cfg = cfg
        self.w, self.h = cfg.get("resolution", [320, 480])

        self.lang = normalize_language(cfg.get("language", "ko"))
        self.i18n = load_language_pack(self.lang)

        self.theme = cfg.get("theme", "light")
        if self.theme == "classic":
            self.theme = "light"
        if self.theme not in THEMES:
            self.theme = "light"

        self.brightness = int(clamp(cfg.get("brightness", 100), 40, 100))
        self.time_24h = bool(cfg.get("time_24h", False))
        self.device_name = norm_text(cfg.get("device_name", self.tr("title")))
        self.editing_name = False
        self.wallpaper = str(cfg.get("wallpaper", DEFAULT_WALLPAPER))
        self.accent_key = str(cfg.get("accent_color", "blue"))
        if self.accent_key not in ACCENT_PRESETS:
            self.accent_key = "blue"
        self.home_show_power = bool(cfg.get("home_show_power", True))
        self.general_reset_confirm = ""
        self.general_reset_confirm_start = 0
        self.general_reset_confirm_ms = 180
        self.device_model = norm_text(str(cfg.get("device_model", "PMP")))
        self.device_model_name = norm_text(str(cfg.get("device_model_name", "PMP Shell")))
        self.serial_number = norm_text(str(cfg.get("serial_number", "0000000000")))
        self.bt_address = norm_text(str(cfg.get("bt_address", "00:00:00:00:00:00")))
        self.settings_info_tab = "basic"
        self.settings_info_name_popup_active = False
        self.settings_info_name_popup_start = 0
        self.settings_info_name_popup_ms = 180

        pygame.init()
        pygame.display.set_caption(cfg.get("title", "PMP Shell"))
        self.screen = pygame.display.set_mode((self.w, self.h))
        pygame.mouse.set_visible(True)

        self.font_path = self.pick_font_path()
        if self.font_path:
            self.font = pygame.font.Font(self.font_path, 16)
            self.small_font = pygame.font.Font(self.font_path, 13)
            self.title_font = pygame.font.Font(self.font_path, 24)
            self.settings_footer_font = pygame.font.Font(self.font_path, 27)
            self.calc_expr_font = pygame.font.Font(self.font_path, 18)
            self.calc_value_font = pygame.font.Font(self.font_path, 40)
            self.lock_time_font = pygame.font.Font(self.font_path, 68)
            self.lock_date_font = pygame.font.Font(self.font_path, 18)
        else:
            self.font = pygame.font.SysFont(None, 16)
            self.small_font = pygame.font.SysFont(None, 13)
            self.title_font = pygame.font.SysFont(None, 24)
            self.settings_footer_font = pygame.font.SysFont(None, 27)
            self.calc_expr_font = pygame.font.SysFont(None, 18)
            self.calc_value_font = pygame.font.SysFont(None, 40)
            self.lock_time_font = pygame.font.SysFont(None, 68)
            self.lock_date_font = pygame.font.SysFont(None, 18)

        self.clock = pygame.time.Clock()

        self.state = "HOME"
        self.page = 0
        self.apps = cfg.get("apps", [])
        self.per_page = GRID_COLS * GRID_ROWS
        self.total_pages = max(1, math.ceil(len(self.apps) / self.per_page))

        self.touch_down = False
        self.down_pos = (0, 0)
        self.down_time = 0
        self.active_button = None
        self.did_swipe = False
        self.list_touch_drag = False
        self.list_touch_moved = False
        self.list_touch_start_y = 0
        self.list_touch_start_scroll = 0

        self.message = ""
        self.message_start = 0
        self.message_duration = 0
        self.message_until = 0
        self.icon_map = self.load_icons()
        self.now_icons = self.load_now_icons()
        self.video_ui_icons = self.load_video_ui_icons()
        self.photo_ui_icons = self.load_photo_ui_icons()
        self.files_ui_icons = self.load_files_ui_icons()
        self.lock_home_icon = self.load_lock_home_icon()
        self.settings_footer_icon = self.load_settings_footer_icon()
        self.settings_full_icons = self.load_settings_full_icons()
        self.settings_full_icons_24 = self.prepare_settings_full_icons(24)
        self.wallpaper_img = self.load_wallpaper(self.wallpaper)
        self.ensure_wallpaper_valid()
        self.music_files = self.load_music_files()
        self.video_files = self.load_video_files()
        self.photo_files = self.load_photo_files()
        self.text_files = self.load_text_files()
        self.photo_thumb_cache = {}
        self.photo_view_cache = {}
        self.photo_meta_time_cache = {}
        self.photo_info_cache = {}
        self.wallpaper_thumb_cache = {}
        self.photo_view = "GRID"  # GRID, VIEWER
        self.photo_index = 0
        self.photo_pick_wallpaper = False
        self.video_view = "LIST"  # LIST, PLAYER
        self.video_index = -1
        self.video_rotation = 0
        self.ffmpeg_bin = self.find_ffmpeg_bin()
        self.ffplay_bin = self.find_ffplay_bin()
        self.video_proc = None
        self.video_audio_proc = None
        self.video_decode_thread = None
        self.video_decode_running = False
        self.video_frame_lock = threading.Lock()
        self.video_latest_frame = None
        self.video_latest_frame_id = 0
        self.video_rendered_frame_id = -1
        self.video_frame_surface = None
        self.video_frame_w = 0
        self.video_frame_h = 0
        self.video_frame_bytes = 0
        self.video_fps = 30.0
        self.video_playing = False
        self.video_play_base_pos = 0.0
        self.video_play_started_ms = 0
        self.video_pause_pos = 0.0
        self.video_path = ""
        self.video_prev_button_last_tap = 0
        self.video_prev_chain_active = False
        self.video_paused_music = False
        self.video_audio_started = False
        self.video_audio_start_path = ""
        self.video_audio_start_seek = 0.0
        self.video_ui_visible = True
        self.video_ui_anim_from = 1.0
        self.video_ui_anim_to = 1.0
        self.video_ui_anim_start = 0
        self.video_ui_anim_ms = 220
        self.video_ui_progress = 1.0
        self.video_ui_last_interaction = pygame.time.get_ticks()
        self.video_ui_auto_hide_ms = 2200
        self.video_ui_touch_consumed = False
        self.video_progress_drag = False
        self.video_progress_drag_pos = 0.0
        self.photo_ui_visible = True
        self.photo_ui_anim_from = 1.0
        self.photo_ui_anim_to = 1.0
        self.photo_ui_anim_start = 0
        self.photo_ui_anim_ms = 220
        self.photo_ui_progress = 1.0
        self.photo_ui_touch_consumed = False
        self.photo_slide_active = False
        self.photo_slide_from_path = ""
        self.photo_slide_to_path = ""
        self.photo_slide_dir = 0  # +1 next, -1 prev
        self.photo_slide_start = 0
        self.photo_slide_ms = 220
        self.photo_zoom = 1.0
        self.photo_zoom_min = 1.0
        self.photo_zoom_max = 4.0
        self.photo_zoom_anim_active = False
        self.photo_zoom_anim_from = 1.0
        self.photo_zoom_anim_to = 1.0
        self.photo_zoom_anim_start = 0
        self.photo_zoom_anim_ms = 180
        self.photo_last_tap_ms = 0
        self.photo_last_tap_pos = (0, 0)
        self.photo_pinch_ids = []
        self.photo_pinch_start_dist = 0.0
        self.photo_pinch_start_zoom = 1.0
        self.photo_fingers = {}
        self.photo_wheel_nav_last_ms = 0
        self.photo_wheel_nav_gap_ms = 170
        self.photo_wheel_nav_accum = 0.0
        self.photo_wheel_nav_step = 1.8
        self.video_volume_sync_ms = 0
        self.seek_hold_kind = None  # "music" / "video"
        self.seek_hold_dir = 0      # -1 prev, +1 next
        self.seek_hold_triggered = False
        self.seek_hold_last_ms = 0
        self.seek_hold_consumed = False
        last_path = cfg.get("music_last_path")
        last_idx = int(cfg.get("music_last_index", 0))
        if last_path and last_path in self.music_files:
            self.music_index = self.music_files.index(last_path)
        else:
            self.music_index = int(clamp(last_idx, 0, max(0, len(self.music_files) - 1)))
        self.music_paused = False
        self.music_event = pygame.USEREVENT + 1
        self.mixer_ready = False
        self.list_scroll = 0.0
        self.list_scroll_target = 0.0
        self.list_scroll_velocity = 0.0
        self.list_scroll_inertia_active = False
        self.list_scroll_anim_last_ms = pygame.time.get_ticks()
        self.list_touch_last_y = 0.0
        self.list_touch_last_ms = 0
        self.list_touch_smooth_y = 0.0
        self.music_view = "MENU"  # MENU, NOW, LIST, QUEUE, ALBUMS, ARTISTS, ARTIST_ALBUMS
        self.shuffle_enabled = bool(cfg.get("music_shuffle", False))
        self.repeat_mode = str(cfg.get("music_repeat", "all"))  # off, all, one
        if self.repeat_mode not in ("off", "all", "one"):
            self.repeat_mode = "all"
        self.music_volume = float(clamp(cfg.get("music_volume", 0.8), 0.0, 1.0))
        # Video player volume is linked to music volume.
        self.video_volume = self.music_volume
        self.music_started_at = 0
        self.music_pause_started = 0
        self.music_paused_total = 0
        self.music_progress_drag = False
        self.music_progress_drag_pos = 0.0
        self.music_history = []
        self.music_backend = "mixer"
        self.music_proc = None
        self.track_meta_cache = {}
        self.music_search = ""
        self.music_sort = str(cfg.get("music_sort", "name"))  # name, album, artist
        if self.music_sort not in ("name", "album", "artist"):
            self.music_sort = "name"
        self.queue_source = str(cfg.get("music_queue_source", "songs"))  # songs, album, genre, liked
        if self.queue_source not in ("songs", "album", "genre", "liked"):
            self.queue_source = "songs"
        self.queue_album = cfg.get("music_queue_album")
        self.queue_genre = cfg.get("music_queue_genre")
        self.queue_artist = cfg.get("music_queue_artist")
        self.queue_sort = str(cfg.get("music_queue_sort", self.music_sort))
        if self.queue_sort not in ("name", "album", "artist"):
            self.queue_sort = self.music_sort
        if self.queue_source == "album" and not self.queue_album:
            self.queue_source = "songs"
            self.queue_sort = self.music_sort
        if self.queue_source == "genre" and not self.queue_genre:
            self.queue_source = "songs"
            self.queue_sort = self.music_sort
        self.music_likes = set(cfg.get("music_likes", []))
        self.prev_button_last_tap = 0
        self.prev_chain_active = False
        self.editing_music_search = False
        self.sort_picker_open = False
        self.music_ctx_artist = None
        self.music_ctx_album = None
        self.music_ctx_genre = None
        self.album_art_cache = {}
        self.video_meta_cache = {}
        self.video_thumb_cache = {}
        self.text_meta_cache = {}
        self.text_content_cache = {}
        self.text_thumb_cache = {}
        self.text_lines_cache = {}
        self.video_search = ""
        self.video_sort = str(cfg.get("video_sort", "name"))  # name, date
        if self.video_sort not in ("name", "date"):
            self.video_sort = "name"
        self.editing_video_search = False
        self.video_sort_picker_open = False
        self.text_search = ""
        self.text_sort = "name"  # name, date
        self.editing_text_search = False
        self.text_sort_picker_open = False
        self.text_view = "LIST"  # LIST, READER
        self.text_index = 0
        self.files_view = "ROOT"  # ROOT, LIST, INFO
        self.files_path = ""
        self.files_source = "internal"  # internal, trash
        self.files_search = ""
        self.files_sort = "name"  # name, date, size
        self.files_sort_desc = False
        self.files_sort_picker_open = False
        self.editing_files_search = False
        self.files_info_entry = None
        self.files_icon_cache = {}
        self.files_selected = set()
        self.files_delete_confirm_active = False
        self.files_delete_confirm_start = 0
        self.files_delete_confirm_ms = 180
        self.files_delete_confirm_paths = []
        self.files_delete_confirm_action = ""
        self.files_info_rename_active = False
        self.files_info_rename_text = ""
        self.files_info_rename_start = 0
        self.files_info_rename_ms = 180
        self.vk_visible = False
        self.vk_lang_pref = str(cfg.get("vk_lang_pref", "en")).lower()
        if self.vk_lang_pref not in ("ko", "en"):
            self.vk_lang_pref = "en"
        self.vk_mode = self.vk_lang_pref  # ko, en, num
        self.vk_shift = False
        self.vk_caps = False
        self.vk_shift_last_tap = 0
        self.vk_shift_double_ms = 340
        self.vk_target_id = ""
        self.vk_target_max = 64
        self.vk_committed = ""
        self.vk_h_l = ""
        self.vk_h_v = ""
        self.vk_h_t = ""
        self.vk_last_ko_key = ""
        self.vk_last_ko_time = 0
        self.vk_last_ko_cycle = 0
        self.vk_key_rects = []
        self.vk_lift = 0.0
        self.vk_lift_target = 0.0
        self.files_trash_meta_cache = {}
        self.screen_off = False
        self.screen_off_progress = 0.0
        self.screen_off_anim_from = 0.0
        self.screen_off_anim_to = 0.0
        self.screen_off_anim_start = 0
        self.screen_off_anim_ms = 140
        self.esc_hold_started = 0
        self.esc_hold_handled = False
        self.lock_unlock_hold_ms = 500
        self.power_hold_ms = 1500
        self.boot_hold_ms = 10000
        self.boot_active = False
        self.boot_start = 0
        self.boot_black_ms = 260
        self.boot_load_ms = 6000
        self.lock_resume_route = ("HOME",)
        self.lock_unlock_fade_active = False
        self.lock_unlock_fade_start = 0
        self.lock_unlock_fade_ms = 180
        self.lock_unlock_fade_alpha = 0.0
        self.text_font_percent = 100
        self.text_font_min = 60
        self.text_font_max = 220
        self.text_font_step = 10
        self.text_font_cache = {}
        self.calc_expr = ""
        self.calc_display = "0"
        self.calc_error = False
        self.calc_just_evaluated = False
        self.calc_prev_expr = ""
        now_tt = time.localtime()
        self.calendar_year = int(now_tt.tm_year)
        self.calendar_month = int(now_tt.tm_mon)
        self.calendar_min = (2000, 1)
        self.calendar_max = (2038, 1)
        if (self.calendar_year, self.calendar_month) < self.calendar_min:
            self.calendar_year, self.calendar_month = self.calendar_min
        if (self.calendar_year, self.calendar_month) > self.calendar_max:
            self.calendar_year, self.calendar_month = self.calendar_max
        self.now_backdrop_cache = {}
        self.transition_active = False
        self.transition_from = None
        self.transition_start = 0
        self.transition_ms = 220
        self.transition_dir = 1  # 1: right->left, -1: left->right
        self.pending_back_transition = False
        self.last_route = (self.state, self.music_view)
        self.last_frame_surface = None
        self.power_confirm_active = False
        self.power_confirm_start = 0
        self.power_confirm_ms = 180
        self.settings_picker_active = False
        self.settings_picker_start = 0
        self.settings_picker_ms = 180
        self.settings_picker_kind = ""
        self.settings_picker_options = []
        self.bt_enabled = bool(cfg.get("bt_enabled", False))
        self.bt_scanning = False
        self.bt_scan_started = 0
        self.bt_scan_ms = 1800
        self.bt_connect_ms = 900
        bt_airpods_name = norm_text(str(cfg.get("bt_airpods_name", "AirPods Pro - Find My")))
        bt_audi_name = norm_text(str(cfg.get("bt_audi_name", "Audi A6")))
        self.bt_devices = [
            {"name": bt_airpods_name, "paired": False, "connected": False, "state": "idle", "started": 0},
            {"name": bt_audi_name, "paired": False, "connected": False, "state": "idle", "started": 0},
        ]
        self.eq_presets = [
            (self.tr("eq.preset.default", default="기본"), [0, 0, 0, 0, 0]),
            (self.tr("eq.preset.bass", default="저음 강화"), [4, 2, 0, -1, -2]),
            (self.tr("eq.preset.vocal", default="보컬"), [-1, 1, 3, 2, 0]),
            (self.tr("eq.preset.classic", default="클래식"), [2, 1, 0, 1, 2]),
            (self.tr("eq.preset.powerful", default="파워풀"), [5, 3, 1, 0, -1]),
        ]
        self.eq_selected = 0
        self.fake_battery_level = int(clamp(cfg.get("fake_battery_level", 73), 1, 100))
        self.fake_battery_health = int(clamp(cfg.get("fake_battery_health", 100), 1, 100))
        self.fake_battery_saver = bool(cfg.get("fake_battery_saver", False))
        self.fake_battery_charging = bool(cfg.get("fake_battery_charging", False))
        self.photo_delete_confirm_active = False
        self.photo_delete_confirm_start = 0
        self.photo_delete_confirm_ms = 180
        self.photo_delete_target_path = ""
        self.photo_share_sheet_active = False
        self.photo_share_sheet_start = 0
        self.photo_share_sheet_ms = 180
        self.exit_requested = False
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_endevent(self.music_event)
            pygame.mixer.music.set_volume(self.music_volume)
            self.mixer_ready = True
        except Exception:
            self.mixer_ready = False

    def tone(self, color, delta):
        return tuple(int(clamp(c + delta, 0, 255)) for c in color)

    def pick_font_path(self):
        file_candidates = [
            os.path.join(FONT_DIR, "NotoSansKR-Regular.ttf"),
            os.path.join(FONT_DIR, "NanumGothic.ttf"),
            os.path.join(FONT_DIR, "MalgunGothic.ttf"),
            os.path.join(LEGACY_FONT_DIR, "NotoSansKR-Regular.ttf"),
            os.path.join(LEGACY_FONT_DIR, "NanumGothic.ttf"),
            os.path.join(LEGACY_FONT_DIR, "MalgunGothic.ttf"),
        ]
        for path in file_candidates:
            if os.path.isfile(path):
                return path

        name_candidates = [
            "Apple SD Gothic Neo",
            "NanumGothic",
            "Malgun Gothic",
            "Noto Sans CJK KR",
            "Noto Sans KR",
            "UnDotum",
            "Arial Unicode MS",
        ]
        for name in name_candidates:
            matched = pygame.font.match_font(name)
            if matched:
                return matched
        return None

    # 언어팩 문자열 조회 + format 치환용 공통 헬퍼
    def tr(self, key, **kwargs):
        fallback = kwargs.pop("default", key)
        text = self.i18n.get(key, fallback)
        try:
            return text.format(**kwargs)
        except Exception:
            return text

    # 언어 변경 시 i18n 캐시와 트랙 메타 캐시를 함께 초기화한다.
    def set_language(self, code):
        self.lang = normalize_language(code)
        self.i18n = load_language_pack(self.lang)
        self.track_meta_cache.clear()

    def pal(self):
        return THEMES.get(self.theme, THEMES["light"])

    def home_apps(self):
        if self.home_show_power:
            return list(self.apps)
        return [a for a in self.apps if self.app_key(a) != "power"]

    def refresh_home_pages(self):
        total = max(1, math.ceil(len(self.home_apps()) / max(1, self.per_page)))
        self.total_pages = total
        self.page = int(clamp(self.page, 0, total - 1))

    # 설정값만 초기화(콘텐츠 파일은 유지)하는 공장 초기화
    def apply_factory_settings(self):
        self.lang = "ko"
        self.i18n = load_language_pack(self.lang)
        self.theme = "light"
        self.brightness = 100
        self.time_24h = False
        self.device_name = self.tr("title", default="나의 PMP")
        self.wallpaper = DEFAULT_WALLPAPER
        self.accent_key = "blue"
        self.vk_lang_pref = "en"
        self.vk_mode = self.vk_lang_pref
        self.home_show_power = True
        self.bt_enabled = False
        self.serial_number = "0000000000"
        self.bt_address = "00:00:00:00:00:00"
        self.fake_battery_level = 73
        self.fake_battery_health = 100
        self.fake_battery_saver = False
        self.fake_battery_charging = False
        self.music_sort = "name"
        self.video_sort = "name"
        self.wallpaper_img = self.load_wallpaper(self.wallpaper)
        if self.wallpaper_img is None:
            self.wallpaper = DEFAULT_WALLPAPER
            self.wallpaper_img = self.load_wallpaper(self.wallpaper)
        self.settings_picker_active = False
        self.editing_name = False
        self.refresh_home_pages()
        self.save_pref()

    # 콘텐츠 + 설정 전체 초기화(파일/휴지통 포함)
    def wipe_all_content_and_settings(self):
        self.stop_video_process()
        self.stop_mpv()
        if self.mixer_ready:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

        targets = (
            MUSIC_DIR,
            VIDEO_DIR,
            IMAGE_DIR,
            DOCUMENT_DIR,
            os.path.join(BASE_DIR, "files", ".trash", "files"),
        )
        for root in targets:
            try:
                os.makedirs(root, exist_ok=True)
                for name in os.listdir(root):
                    p = os.path.join(root, name)
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        try:
                            os.remove(p)
                        except Exception:
                            pass
            except Exception:
                pass

        try:
            os.makedirs(os.path.dirname(TRASH_META_PATH), exist_ok=True)
            with open(TRASH_META_PATH, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        self.music_files = self.load_music_files()
        self.video_files = self.load_video_files()
        self.photo_files = self.load_photo_files()
        self.text_files = self.load_text_files()
        self.photo_thumb_cache.clear()
        self.photo_view_cache.clear()
        self.photo_meta_time_cache.clear()
        self.photo_info_cache.clear()
        self.track_meta_cache.clear()
        self.text_meta_cache.clear()
        self.text_content_cache.clear()
        self.text_thumb_cache.clear()
        self.text_lines_cache.clear()
        self.video_thumb_cache.clear()
        self.files_icon_cache.clear()
        self.files_selected = set()
        self.files_path = ""
        self.files_view = "ROOT"
        self.files_source = "internal"
        self.apply_factory_settings()
        self.start_boot_sequence()

    def save_pref(self):
        self.cfg["language"] = self.lang
        self.cfg["theme"] = self.theme
        self.cfg["brightness"] = self.brightness
        self.cfg["accent_color"] = self.accent_key
        self.cfg["bt_enabled"] = self.bt_enabled
        self.cfg["fake_battery_level"] = int(self.fake_battery_level)
        self.cfg["fake_battery_health"] = int(self.fake_battery_health)
        self.cfg["fake_battery_saver"] = bool(self.fake_battery_saver)
        self.cfg["fake_battery_charging"] = bool(self.fake_battery_charging)
        self.cfg["time_24h"] = self.time_24h
        self.cfg["device_name"] = self.device_name
        self.cfg["wallpaper"] = self.wallpaper
        self.cfg["device_model"] = self.device_model
        self.cfg["device_model_name"] = self.device_model_name
        self.cfg["serial_number"] = self.serial_number
        self.cfg["bt_address"] = self.bt_address
        self.cfg["home_show_power"] = bool(self.home_show_power)
        self.cfg["vk_lang_pref"] = self.vk_lang_pref
        self.cfg["music_shuffle"] = self.shuffle_enabled
        self.cfg["music_repeat"] = self.repeat_mode
        self.cfg["music_volume"] = round(self.music_volume, 2)
        self.cfg["music_likes"] = sorted(list(self.music_likes))
        self.cfg["music_last_index"] = int(self.music_index)
        self.cfg["music_last_path"] = self.music_files[self.music_index] if (0 <= self.music_index < len(self.music_files)) else ""
        self.cfg["music_queue_source"] = self.queue_source
        self.cfg["music_queue_album"] = self.queue_album
        self.cfg["music_queue_genre"] = self.queue_genre
        self.cfg["music_queue_artist"] = self.queue_artist
        self.cfg["music_queue_sort"] = self.queue_sort
        self.cfg["music_sort"] = self.music_sort
        self.cfg["video_sort"] = self.video_sort
        self.cfg["video_volume"] = round(self.music_volume, 2)
        save_config(self.cfg)

    def ui_accent(self):
        return ACCENT_PRESETS.get(self.accent_key, ACCENT_PRESETS["blue"])

    # 현재 재생 컨텍스트를 즉시 config.json에 저장한다.
    def remember_play_state(self):
        self.cfg["music_last_index"] = int(self.music_index)
        self.cfg["music_last_path"] = self.music_files[self.music_index] if (0 <= self.music_index < len(self.music_files)) else ""
        self.cfg["music_queue_source"] = self.queue_source
        self.cfg["music_queue_album"] = self.queue_album
        self.cfg["music_queue_genre"] = self.queue_genre
        self.cfg["music_queue_artist"] = self.queue_artist
        self.cfg["music_queue_sort"] = self.queue_sort
        self.cfg["music_sort"] = self.music_sort
        self.cfg["video_sort"] = self.video_sort
        self.cfg["video_volume"] = round(self.music_volume, 2)
        save_config(self.cfg)

    def load_wallpaper(self, rel_or_abs_path):
        if os.path.isabs(rel_or_abs_path):
            path = rel_or_abs_path
        else:
            path = os.path.join(BASE_DIR, rel_or_abs_path)
        try:
            img = pygame.image.load(path).convert()
            iw, ih = img.get_size()
            if iw <= 0 or ih <= 0:
                return None
            scale = max(self.w / iw, self.h / ih)
            nw = max(1, int(iw * scale))
            nh = max(1, int(ih * scale))
            scaled = pygame.transform.smoothscale(img, (nw, nh))
            x = max(0, (nw - self.w) // 2)
            y = max(0, (nh - self.h) // 2)
            return scaled.subsurface((x, y, self.w, self.h)).copy()
        except Exception:
            return None

    def resolve_wallpaper_path(self):
        if os.path.isabs(self.wallpaper):
            return self.wallpaper
        return os.path.join(BASE_DIR, self.wallpaper)

    def ensure_wallpaper_valid(self):
        wp = self.resolve_wallpaper_path()
        if not os.path.isfile(wp):
            self.wallpaper = DEFAULT_WALLPAPER
            self.wallpaper_img = self.load_wallpaper(self.wallpaper)
            self.save_pref()

    def app_key(self, app):
        key = app.get("key")
        if key:
            return str(key).lower()
        builtin = app.get("builtin")
        if builtin:
            return str(builtin).lower()
        return str(app.get("name", "")).lower()

    def app_label(self, app):
        key = self.app_key(app)
        return self.tr(f"app.{key}", default=app.get("name", "앱"))

    def load_icons(self):
        icon_map = {}
        def load_icon_file(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                size = 70
                resized = pygame.transform.smoothscale(img, (size, size))
                rounded = pygame.Surface((size, size), pygame.SRCALPHA)
                rounded.blit(resized, (0, 0))
                mask = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, size, size), border_radius=18)
                rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                return rounded
            except Exception:
                return None
        if os.path.isdir(ICON_DIR):
            for fname in os.listdir(ICON_DIR):
                root, ext = os.path.splitext(fname)
                if ext.lower() != ".png":
                    continue
                fpath = os.path.join(ICON_DIR, fname)
                loaded = load_icon_file(fpath)
                if loaded is not None:
                    icon_map[root.lower()] = loaded
        if "app" not in icon_map:
            for cand in (
                os.path.join(ICON_DIR, "App.png"),
                os.path.join(ICON_DIR, "app.png"),
                os.path.join(UI_DIR, "App.png"),
                os.path.join(UI_DIR, "app.png"),
            ):
                if os.path.isfile(cand):
                    loaded = load_icon_file(cand)
                    if loaded is not None:
                        icon_map["app"] = loaded
                        break
        return icon_map

    def load_now_icons(self):
        # SVG files are pre-made in system/UI.
        defs = {
            "prev": "prev.svg",
            "play": "play.svg",
            "pause": "pause.svg",
            "bluetooth": "bluetooth.svg",
            "next": "next.svg",
            "shuffle": "shuffle.svg",
            "repeat": "repeat.svg",
            "queue": "playlist.svg",
            "volume0": "volume0.svg",
            "volume1": "volume1.svg",
            "volume2": "volume2.svg",
            "volume3": "volume3.svg",
        }
        out = {}
        for key, fname in defs.items():
            path = os.path.join(UI_DIR, fname)
            try:
                img = pygame.image.load(path).convert_alpha()
                # Some SVG exports include large transparent margins.
                # Trim them so icons fill button areas predictably.
                bounds = img.get_bounding_rect(min_alpha=1)
                if bounds.w > 0 and bounds.h > 0:
                    img = img.subsurface(bounds).copy()
                out[key] = img
            except Exception:
                out[key] = None
        return out

    def load_video_ui_icons(self):
        defs = {
            "portrait": "rotation.png",
            "rot_left": "rotation_left.png",
            "rot_right": "rotation_right.png",
        }
        out = {}
        for key, fname in defs.items():
            path = os.path.join(UI_DIR, fname)
            try:
                out[key] = pygame.image.load(path).convert_alpha()
            except Exception:
                out[key] = None
        return out

    def load_photo_ui_icons(self):
        defs = {
            "share": ("shere.svg", "share.svg"),
            "trash": ("trash.svg",),
        }
        out = {}
        for key, names in defs.items():
            loaded = None
            for fname in names:
                path = os.path.join(UI_DIR, fname)
                try:
                    loaded = pygame.image.load(path).convert_alpha()
                    break
                except Exception:
                    continue
            out[key] = loaded
        return out

    def load_files_ui_icons(self):
        defs = {
            "internal": ("device.svg",),
            "external": ("sd.svg", "SD.svg"),
            "trash": ("trash.svg",),
            "folder": ("folder.svg",),
            "folder_document": ("folder_document.png",),
            "folder_image": ("folder_image.png",),
            "folder_music": ("folder_muisc.png", "folder_music.png"),
            "folder_video": ("folder_video.png",),
            "file": ("files.png",),
        }
        out = {}
        for key, names in defs.items():
            loaded = None
            for fname in names:
                path = os.path.join(UI_DIR, fname)
                try:
                    loaded = pygame.image.load(path).convert_alpha()
                    break
                except Exception:
                    continue
            out[key] = loaded
        return out

    def load_lock_home_icon(self):
        def make_rounded_70(img):
            size = 70
            resized = pygame.transform.smoothscale(img, (size, size))
            rounded = pygame.Surface((size, size), pygame.SRCALPHA)
            rounded.blit(resized, (0, 0))
            mask = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, size, size), border_radius=18)
            rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            return rounded
        for cand in (
            os.path.join(UI_DIR, "home.png"),
            os.path.join(ICON_DIR, "home.png"),
            os.path.join(ICON_DIR, "Home.png"),
        ):
            try:
                if os.path.isfile(cand):
                    raw = pygame.image.load(cand).convert_alpha()
                    return make_rounded_70(raw)
            except Exception:
                continue
        return None

    def load_settings_footer_icon(self):
        def make_rounded_62(img):
            size = 62
            resized = pygame.transform.smoothscale(img, (size, size))
            rounded = pygame.Surface((size, size), pygame.SRCALPHA)
            rounded.blit(resized, (0, 0))
            mask = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, size, size), border_radius=16)
            rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            return rounded
        for cand in (
            os.path.join(UI_DIR, "setting.png"),
            os.path.join(UI_DIR, "Setting.png"),
            os.path.join(ICON_DIR, "setting.png"),
            os.path.join(ICON_DIR, "Setting.png"),
        ):
            try:
                if os.path.isfile(cand):
                    raw = pygame.image.load(cand).convert_alpha()
                    return make_rounded_62(raw)
            except Exception:
                continue
        return None

    def load_settings_full_icons(self):
        defs = {
            "bluetooth": os.path.join(ICON_DIR, "BT.png"),
            "sound": os.path.join(ICON_DIR, "Sound.png"),
            "display": os.path.join(ICON_DIR, "Display.png"),
            "battery": os.path.join(ICON_DIR, "Battery.png"),
            "wallpaper": os.path.join(ICON_DIR, "Photo.png"),
            "home_lock": os.path.join(ICON_DIR, "home.png"),
            "general": os.path.join(ICON_DIR, "Setting.png"),
            "info": os.path.join(ICON_DIR, "info.png"),
        }
        out = {}
        for key, path in defs.items():
            try:
                out[key] = pygame.image.load(path).convert_alpha() if os.path.isfile(path) else None
            except Exception:
                out[key] = None
        return out

    def prepare_settings_full_icons(self, target=24):
        out = {}
        for key, icon in self.settings_full_icons.items():
            if icon is None:
                out[key] = None
                continue
            iw, ih = icon.get_size()
            scale = min(target / max(1, iw), target / max(1, ih))
            nw = max(1, int(iw * scale))
            nh = max(1, int(ih * scale))
            draw = pygame.transform.smoothscale(icon, (nw, nh))
            rounded = pygame.Surface((nw, nh), pygame.SRCALPHA)
            rounded.blit(draw, (0, 0))
            mask = pygame.Surface((nw, nh), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, nw, nh), border_radius=max(4, min(nw, nh) // 4))
            rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            out[key] = rounded
        return out

    def draw_png_icon_only(self, rect, icon, force_color=(246, 248, 255)):
        if icon is None:
            return
        target = max(8, min(rect.w, rect.h) - 8)
        iw, ih = icon.get_size()
        scale = min(target / max(1, iw), target / max(1, ih))
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        icon_draw = pygame.transform.smoothscale(icon, (nw, nh))
        tint = icon_draw.copy()
        tint.fill(force_color + (0,), special_flags=pygame.BLEND_RGB_ADD)
        x = rect.centerx - nw // 2
        y = rect.centery - nh // 2
        self.screen.blit(tint, (x, y))

    def draw_icon_only_rotated(self, rect, icon_key, force_color=(246, 248, 255), angle=0):
        icon = self.now_icons.get(icon_key)
        if icon is None:
            return
        target = max(8, min(rect.w, rect.h) - 4)
        iw, ih = icon.get_size()
        scale = min(target / max(1, iw), target / max(1, ih))
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        icon_draw = pygame.transform.smoothscale(icon, (nw, nh))
        icon_draw = self.tint_icon(icon_draw, force_color)
        if angle:
            icon_draw = pygame.transform.rotate(icon_draw, angle)
        rr = icon_draw.get_rect(center=rect.center)
        self.screen.blit(icon_draw, rr.topleft)

    def draw_png_icon_only_rotated(self, rect, icon, force_color=(246, 248, 255), angle=0):
        if icon is None:
            return
        target = max(8, min(rect.w, rect.h) - 8)
        iw, ih = icon.get_size()
        scale = min(target / max(1, iw), target / max(1, ih))
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        icon_draw = pygame.transform.smoothscale(icon, (nw, nh))
        tint = icon_draw.copy()
        tint.fill(force_color + (0,), special_flags=pygame.BLEND_RGB_ADD)
        if angle:
            tint = pygame.transform.rotate(tint, angle)
        rr = tint.get_rect(center=rect.center)
        self.screen.blit(tint, rr.topleft)

    def draw_text_rotated_center(self, font, text, color, center, angle):
        surf = font.render(text, True, color)
        if angle:
            surf = pygame.transform.rotate(surf, angle)
        rr = surf.get_rect(center=center)
        self.screen.blit(surf, rr.topleft)

    def theme_icon_color(self):
        if self.theme in ("dark", "transparent"):
            return (245, 248, 255)
        return (40, 44, 52)

    def tint_icon(self, icon, rgb):
        tinted = icon.copy()
        tinted.fill(rgb + (0,), special_flags=pygame.BLEND_RGB_ADD)
        return tinted

    def draw_icon_only(self, rect, icon_key, fallback_text="", active=False, force_color=None):
        icon = self.now_icons.get(icon_key)
        if icon:
            target = max(8, min(rect.w, rect.h) - 4)
            iw, ih = icon.get_size()
            scale = min(target / max(1, iw), target / max(1, ih))
            nw = max(1, int(iw * scale))
            nh = max(1, int(ih * scale))
            icon_draw = pygame.transform.smoothscale(icon, (nw, nh))
            tint = force_color if force_color else self.theme_icon_color()
            icon_draw = self.tint_icon(icon_draw, tint)
            x = rect.centerx - nw // 2
            y = rect.centery - nh // 2
            if active:
                gl = pygame.Surface((nw + 10, nh + 10), pygame.SRCALPHA)
                pygame.draw.ellipse(gl, (255, 255, 255, 28), gl.get_rect())
                self.screen.blit(gl, (x - 5, y - 5))
            self.screen.blit(icon_draw, (x, y))
            return
        if fallback_text:
            col = (220, 230, 245) if active else self.pal()["text"]
            t = self.title_font.render(fallback_text, True, col)
            self.screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

    def load_music_files(self):
        exts = (".mp3", ".wav", ".ogg", ".flac", ".m4a")
        files = []
        if os.path.isdir(MUSIC_DIR):
            for name in sorted(os.listdir(MUSIC_DIR)):
                if name.lower().endswith(exts):
                    files.append(os.path.join(MUSIC_DIR, name))
        return files

    def load_video_files(self):
        exts = (".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v")
        files = []
        if os.path.isdir(VIDEO_DIR):
            for name in sorted(os.listdir(VIDEO_DIR)):
                if name.lower().endswith(exts):
                    files.append(os.path.join(VIDEO_DIR, name))
        return files

    def load_photo_files(self):
        exts = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")
        files = []
        if os.path.isdir(IMAGE_DIR):
            for name in sorted(os.listdir(IMAGE_DIR)):
                if name.lower().endswith(exts):
                    files.append(os.path.join(IMAGE_DIR, name))
        return files

    def load_text_files(self):
        exts = (".txt",)
        files = []
        if os.path.isdir(DOCUMENT_DIR):
            for name in sorted(os.listdir(DOCUMENT_DIR)):
                if name.lower().endswith(exts):
                    files.append(os.path.join(DOCUMENT_DIR, name))
        return files

    def find_ffmpeg_bin(self):
        for cand in ("ffmpeg", "/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
            try:
                if os.path.sep in cand:
                    if os.path.isfile(cand):
                        return cand
                else:
                    proc = subprocess.run(["which", cand], capture_output=True, text=True, timeout=0.5)
                    if proc.returncode == 0 and proc.stdout.strip():
                        return proc.stdout.strip().splitlines()[0]
            except Exception:
                continue
        return None

    def find_ffplay_bin(self):
        for cand in ("ffplay", "/opt/homebrew/bin/ffplay", "/usr/local/bin/ffplay"):
            try:
                if os.path.sep in cand:
                    if os.path.isfile(cand):
                        return cand
                else:
                    proc = subprocess.run(["which", cand], capture_output=True, text=True, timeout=0.5)
                    if proc.returncode == 0 and proc.stdout.strip():
                        return proc.stdout.strip().splitlines()[0]
            except Exception:
                continue
        return None

    def probe_video_length_ffprobe(self, path):
        try:
            proc = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    path,
                ],
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            if proc.returncode == 0:
                out = (proc.stdout or "").strip()
                if out:
                    val = float(out)
                    if val > 0:
                        return val
        except Exception:
            pass
        return 0.0

    def probe_mp4_length_atom(self, path):
        # Minimal MP4 parser for moov/mvhd duration.
        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception:
            return 0.0

        def walk_boxes(start, end):
            i = start
            while i + 8 <= end:
                size = int.from_bytes(data[i:i + 4], "big", signed=False)
                typ = data[i + 4:i + 8]
                hdr = 8
                if size == 1:
                    if i + 16 > end:
                        return
                    size = int.from_bytes(data[i + 8:i + 16], "big", signed=False)
                    hdr = 16
                elif size == 0:
                    size = end - i
                if size < hdr:
                    return
                box_end = i + size
                if box_end > end:
                    return
                yield (typ, i + hdr, box_end)
                i = box_end

        try:
            for typ, payload_start, payload_end in walk_boxes(0, len(data)):
                if typ != b"moov":
                    continue
                for ctyp, cstart, cend in walk_boxes(payload_start, payload_end):
                    if ctyp != b"mvhd" or cstart + 20 > cend:
                        continue
                    version = data[cstart]
                    if version == 1:
                        if cstart + 32 > cend:
                            continue
                        timescale = int.from_bytes(data[cstart + 20:cstart + 24], "big", signed=False)
                        duration = int.from_bytes(data[cstart + 24:cstart + 32], "big", signed=False)
                    else:
                        timescale = int.from_bytes(data[cstart + 12:cstart + 16], "big", signed=False)
                        duration = int.from_bytes(data[cstart + 16:cstart + 20], "big", signed=False)
                    if timescale > 0 and duration > 0:
                        return float(duration) / float(timescale)
        except Exception:
            return 0.0
        return 0.0

    def probe_mp4_length_mfra(self, path):
        # Fragmented MP4 fallback: use mfra/tfra last decode time.
        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception:
            return 0.0

        def walk_boxes(start, end):
            i = start
            while i + 8 <= end:
                size = int.from_bytes(data[i:i + 4], "big", signed=False)
                typ = data[i + 4:i + 8]
                hdr = 8
                if size == 1:
                    if i + 16 > end:
                        return
                    size = int.from_bytes(data[i + 8:i + 16], "big", signed=False)
                    hdr = 16
                elif size == 0:
                    size = end - i
                if size < hdr:
                    return
                box_end = i + size
                if box_end > end:
                    return
                yield (typ, i + hdr, box_end)
                i = box_end

        # track_id -> (timescale, kind)
        track_info = {}
        try:
            for typ, ps, pe in walk_boxes(0, len(data)):
                if typ != b"moov":
                    continue
                for ctyp, cps, cpe in walk_boxes(ps, pe):
                    if ctyp != b"trak":
                        continue
                    tid = None
                    ts = None
                    kind = None
                    for ttyp, tps, tpe in walk_boxes(cps, cpe):
                        if ttyp == b"tkhd":
                            ver = data[tps]
                            if ver == 1 and tps + 24 <= tpe:
                                tid = int.from_bytes(data[tps + 20:tps + 24], "big", signed=False)
                            elif tps + 16 <= tpe:
                                tid = int.from_bytes(data[tps + 12:tps + 16], "big", signed=False)
                        elif ttyp == b"mdia":
                            for mtyp, mps, mpe in walk_boxes(tps, tpe):
                                if mtyp == b"mdhd":
                                    ver = data[mps]
                                    if ver == 1 and mps + 24 <= mpe:
                                        ts = int.from_bytes(data[mps + 20:mps + 24], "big", signed=False)
                                    elif mps + 16 <= mpe:
                                        ts = int.from_bytes(data[mps + 12:mps + 16], "big", signed=False)
                                elif mtyp == b"hdlr" and mps + 12 <= mpe:
                                    kind = data[mps + 8:mps + 12]
                    if tid and ts:
                        track_info[tid] = (ts, kind)
        except Exception:
            track_info = {}

        best_sec = 0.0
        try:
            for typ, ps, pe in walk_boxes(0, len(data)):
                if typ != b"mfra":
                    continue
                for ctyp, cps, cpe in walk_boxes(ps, pe):
                    if ctyp != b"tfra" or cps + 16 > cpe:
                        continue
                    ver = data[cps]
                    tid = int.from_bytes(data[cps + 4:cps + 8], "big", signed=False)
                    lengths = int.from_bytes(data[cps + 8:cps + 12], "big", signed=False)
                    l_traf = ((lengths >> 4) & 0x3) + 1
                    l_trun = ((lengths >> 2) & 0x3) + 1
                    l_sam = (lengths & 0x3) + 1
                    n = int.from_bytes(data[cps + 12:cps + 16], "big", signed=False)
                    off = cps + 16
                    last_time = 0
                    for _ in range(n):
                        if ver == 1:
                            if off + 16 > cpe:
                                break
                            t = int.from_bytes(data[off:off + 8], "big", signed=False)
                            off += 16  # time + moof_offset
                        else:
                            if off + 8 > cpe:
                                break
                            t = int.from_bytes(data[off:off + 4], "big", signed=False)
                            off += 8  # time + moof_offset
                        off += l_traf + l_trun + l_sam
                        if off > cpe:
                            break
                        last_time = t
                    ts, kind = track_info.get(tid, (0, None))
                    if ts > 0 and last_time > 0:
                        sec = float(last_time) / float(ts)
                        # Prefer video track duration when available.
                        if kind == b"vide":
                            return sec
                        best_sec = max(best_sec, sec)
        except Exception:
            return best_sec
        return best_sec

    def video_meta_for(self, path):
        path = os.fspath(path)
        if path in self.video_meta_cache:
            return self.video_meta_cache[path]
        name = norm_text(os.path.basename(path))  # keep extension
        length = 0.0
        try:
            if MutagenFile:
                media = MutagenFile(path)
                if media and getattr(media, "info", None) and getattr(media.info, "length", None):
                    length = float(media.info.length)
        except Exception:
            length = 0.0
        if length <= 0.0:
            length = self.probe_video_length_ffprobe(path)
        if length <= 0.0 and path.lower().endswith((".mp4", ".m4v", ".mov")):
            length = self.probe_mp4_length_mfra(path)
        if length <= 0.0 and path.lower().endswith((".mp4", ".m4v", ".mov")):
            length = self.probe_mp4_length_atom(path)
        meta = {"name": name, "length": max(0.0, length)}
        self.video_meta_cache[path] = meta
        return meta

    def text_file_created_at(self, path):
        try:
            st = os.stat(path)
            return float(getattr(st, "st_birthtime", st.st_ctime))
        except Exception:
            return 0.0

    def _read_text_file(self, path):
        for enc in ("utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"):
            try:
                with open(path, "r", encoding=enc, errors="strict") as f:
                    return f.read()
            except Exception:
                continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    def text_meta_for(self, path):
        path = os.fspath(path)
        if path in self.text_meta_cache:
            return self.text_meta_cache[path]
        raw = self._read_text_file(path)
        self.text_content_cache[path] = raw
        name = norm_text(os.path.basename(path))
        compact = " ".join(raw.replace("\r", "\n").split())
        preview = compact[:68]
        if len(compact) > 68:
            preview = preview.rstrip() + "…"
        if not preview:
            preview = self.tr("text.preview.empty", default="(빈 텍스트)")
        meta = {"name": name, "preview": preview}
        self.text_meta_cache[path] = meta
        return meta

    def text_content_for(self, path):
        path = os.fspath(path)
        cached = self.text_content_cache.get(path)
        if cached is not None:
            return cached
        raw = self._read_text_file(path)
        self.text_content_cache[path] = raw
        return raw

    def default_text_thumb(self, size):
        size = int(clamp(size, 16, 256))
        key = ("__text_default__", size)
        if key in self.text_thumb_cache:
            return self.text_thumb_cache[key]
        surf = None
        try:
            if os.path.isfile(DEFAULT_TEXT_THUMB):
                base = pygame.image.load(DEFAULT_TEXT_THUMB).convert_alpha()
                surf = self._rounded_image_surface(base, size, radius=6)
        except Exception:
            surf = None
        if surf is None:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(surf, (74, 78, 88), (0, 0, size, size), border_radius=6)
            line = (205, 210, 220)
            for i in range(4):
                y = 6 + i * max(4, size // 6)
                pygame.draw.line(surf, line, (6, y), (size - 6, y), 2)
        self.text_thumb_cache[key] = surf
        return surf

    def text_thumb_for(self, path, size):
        path = os.fspath(path)
        key = (path, int(size))
        cached = self.text_thumb_cache.get(key)
        if cached:
            return cached
        surf = self.default_text_thumb(size)
        self.text_thumb_cache[key] = surf
        return surf

    def _rounded_image_surface(self, base, size, radius=6):
        try:
            bw, bh = base.get_size()
            if bw <= 0 or bh <= 0:
                return None
            scale = max(size / float(bw), size / float(bh))
            nw = max(1, int(bw * scale))
            nh = max(1, int(bh * scale))
            scaled = pygame.transform.smoothscale(base, (nw, nh))
            cx = max(0, (nw - size) // 2)
            cy = max(0, (nh - size) // 2)
            cropped = scaled.subsurface((cx, cy, size, size)).copy()
            rounded = pygame.Surface((size, size), pygame.SRCALPHA)
            rounded.blit(cropped, (0, 0))
            mask = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, size, size), border_radius=radius)
            rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            return rounded
        except Exception:
            return None

    def default_video_thumb(self, size):
        size = int(clamp(size, 16, 256))
        if not hasattr(self, "video_thumb_cache"):
            self.video_thumb_cache = {}
        cache_key = ("__default__", size)
        if cache_key in self.video_thumb_cache:
            return self.video_thumb_cache[cache_key]
        for path in (DEFAULT_VIDEO_THUMB, LEGACY_VIDEO_THUMB):
            try:
                if os.path.isfile(path):
                    base = pygame.image.load(path).convert_alpha()
                    surf = self._rounded_image_surface(base, size, radius=6)
                    if surf is not None:
                        self.video_thumb_cache[cache_key] = surf
                        return surf
            except Exception:
                pass
        fallback = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(fallback, (74, 78, 88), (0, 0, size, size), border_radius=6)
        pygame.draw.polygon(
            fallback,
            (205, 210, 220),
            [(size // 2 - 3, size // 2 - 6), (size // 2 - 3, size // 2 + 6), (size // 2 + 7, size // 2)],
        )
        self.video_thumb_cache[cache_key] = fallback
        return fallback

    def video_thumbnail_for(self, path, size=32):
        path = os.fspath(path)
        size = int(clamp(size, 16, 256))
        if not hasattr(self, "video_thumb_cache"):
            self.video_thumb_cache = {}
        cache_key = (path, size)
        if cache_key in self.video_thumb_cache:
            return self.video_thumb_cache[cache_key]

        surf = None
        image_bytes = None
        try:
            if MutagenFile:
                media = MutagenFile(path)
                tags = getattr(media, "tags", None) if media else None
                if tags:
                    if hasattr(tags, "keys"):
                        for k in tags.keys():
                            if str(k).startswith("APIC"):
                                image_bytes = tags[k].data
                                break
                    if not image_bytes and "covr" in tags and tags["covr"]:
                        image_bytes = bytes(tags["covr"][0])
                if not image_bytes and getattr(media, "pictures", None):
                    if media.pictures:
                        image_bytes = media.pictures[0].data
        except Exception:
            image_bytes = None

        if image_bytes:
            try:
                base = pygame.image.load(io.BytesIO(image_bytes)).convert_alpha()
                surf = self._rounded_image_surface(base, size, radius=6)
            except Exception:
                surf = None

        if surf is None:
            try:
                proc = subprocess.run(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-ss",
                        "00:00:01",
                        "-i",
                        path,
                        "-frames:v",
                        "1",
                        "-f",
                        "image2pipe",
                        "-vcodec",
                        "png",
                        "-",
                    ],
                    capture_output=True,
                    timeout=3.0,
                )
                if proc.returncode == 0 and proc.stdout:
                    base = pygame.image.load(io.BytesIO(proc.stdout)).convert_alpha()
                    surf = self._rounded_image_surface(base, size, radius=6)
            except Exception:
                surf = None

        if surf is None:
            surf = self.default_video_thumb(size)
        self.video_thumb_cache[cache_key] = surf
        return surf

    def ensure_mixer(self):
        if self.mixer_ready:
            return True
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_endevent(self.music_event)
            pygame.mixer.music.set_volume(self.music_volume)
            self.mixer_ready = True
        except Exception:
            self.mixer_ready = False
        return self.mixer_ready

    def stop_mpv(self):
        if self.music_proc and self.music_proc.poll() is None:
            self.music_proc.terminate()
        self.music_proc = None

    def play_track_mpv(self, idx, via_prev=False, start=0.0):
        if not self.music_files:
            return
        self.stop_mpv()
        idx = idx % len(self.music_files)
        start_pos = float(max(0.0, start))
        try:
            cmd = ["mpv", "--no-video", "--quiet"]
            if start_pos > 0.05:
                cmd.append(f"--start={start_pos:.3f}")
            cmd.append(self.music_files[idx])
            self.music_proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.music_backend = "mpv"
            self.music_index = idx
            self.music_paused = False
            now = pygame.time.get_ticks()
            self.music_started_at = now - int(start_pos * 1000)
            self.music_pause_started = 0
            self.music_paused_total = 0
            self.prev_chain_active = via_prev
            self.remember_play_state()
        except Exception as e:
            self.toast(self.tr("toast.launch_failed", err=e))

    def get_app_icon(self, app):
        icon_key = str(app.get("icon", "")).strip().lower()
        if icon_key and icon_key in self.icon_map:
            return self.icon_map.get(icon_key)
        by_key = self.icon_map.get(self.app_key(app))
        if by_key is not None:
            return by_key
        return self.icon_map.get("app")

    def toast(self, msg, ms=1200):
        self.message = msg
        self.message_start = pygame.time.get_ticks()
        self.message_duration = ms
        self.message_until = pygame.time.get_ticks() + ms

    def page_buttons(self):
        buttons = []
        self.refresh_home_pages()
        start = self.page * self.per_page
        items = self.home_apps()[start:start + self.per_page]

        grid_top = STATUS_H + 18
        total_grid_w = GRID_COLS * ICON_W + (GRID_COLS - 1) * GAP_X
        x0 = (self.w - total_grid_w) // 2

        for idx, app in enumerate(items):
            row = idx // GRID_COLS
            col = idx % GRID_COLS
            x = x0 + col * (ICON_W + GAP_X)
            y = grid_top + row * (ICON_H + GAP_Y)
            rect = (x, y, ICON_W, ICON_H)
            buttons.append(Button(rect, self.app_label(app), app, self.get_app_icon(app)))
        return buttons

    def run_app(self, app):
        if self.state == "HOME" and self.app_key(app) == "power":
            self.power_confirm_active = True
            self.power_confirm_start = pygame.time.get_ticks()
            return
        if self.app_key(app) in ("calender", "calendar"):
            self.state = "CALENDAR"
            now_tt = time.localtime()
            y = int(now_tt.tm_year)
            m = int(now_tt.tm_mon)
            if (y, m) < self.calendar_min:
                y, m = self.calendar_min
            if (y, m) > self.calendar_max:
                y, m = self.calendar_max
            self.calendar_year = y
            self.calendar_month = m
            return
        if self.app_key(app) == "calculator":
            self.state = "CALC"
            self.reset_calculator()
            return
        if self.app_key(app) == "textviewer":
            self.state = "TEXT"
            self.text_files = self.load_text_files()
            self.text_view = "LIST"
            self.text_index = 0
            self.text_search = ""
            self.editing_text_search = False
            self.text_sort_picker_open = False
            self.text_meta_cache.clear()
            self.text_content_cache.clear()
            self.text_thumb_cache.clear()
            self.text_lines_cache.clear()
            self.set_list_scroll(0, snap=True)
            return
        if self.app_key(app) == "files":
            self.state = "FILES"
            self.files_view = "ROOT"
            self.files_path = ""
            self.files_source = "internal"
            self.files_search = ""
            self.files_sort = "name"
            self.files_sort_desc = False
            self.files_sort_picker_open = False
            self.editing_files_search = False
            self.files_info_entry = None
            self.files_selected = set()
            self.files_delete_confirm_active = False
            self.files_delete_confirm_paths = []
            self.files_delete_confirm_action = ""
            self.files_info_rename_active = False
            self.files_info_rename_text = ""
            self.set_list_scroll(0, snap=True)
            return
        if self.app_key(app) == "photo":
            self.state = "PHOTO"
            self.photo_pick_wallpaper = False
            self.photo_files = self.load_photo_files()
            self.photo_info_cache.clear()
            self.photo_view = "GRID"
            self.photo_index = 0
            self.set_list_scroll(0, snap=True)
            return
        if self.app_key(app) == "video":
            self.stop_video_process()
            self.video_playing = False
            self.video_rotation = 0
            self.state = "VIDEO"
            self.video_files = self.load_video_files()
            self.video_view = "LIST"
            self.editing_video_search = False
            self.video_sort_picker_open = False
            self.set_list_scroll(0, snap=True)
            return
        if self.app_key(app) == "music":
            self.state = "MUSIC"
            self.music_view = "MENU"
            self.music_ctx_artist = None
            self.music_ctx_album = None
            if not self.music_files:
                self.music_files = self.load_music_files()
            if not self.music_files:
                self.toast(self.tr("toast.no_music"))
            return
        if app.get("builtin") == "settings":
            self.state = "SETTINGS"
            return
        if app.get("builtin") == "power":
            self.state = "POWER"
            return

        cmd = app.get("cmd")
        if not cmd:
            self.toast(self.tr("toast.no_command"))
            return

        self.toast(self.tr("toast.launching"))
        try:
            subprocess.Popen(cmd)
        except Exception as e:
            self.toast(self.tr("toast.launch_failed", err=e))

    def power_confirm_rect(self):
        w, h = 260, 146
        return pygame.Rect((self.w - w) // 2, (self.h - h) // 2, w, h)

    def power_confirm_buttons(self):
        r = self.power_confirm_rect()
        y = r.bottom - 42
        return {
            "no": pygame.Rect(r.x + 16, y, 108, 30),
            "yes": pygame.Rect(r.right - 124, y, 108, 30),
        }

    def settings_picker_rects(self):
        count = max(1, len(self.settings_picker_options))
        w = 250
        h = 52 + (count * 42) + 46
        panel = pygame.Rect((self.w - w) // 2, (self.h - h) // 2, w, h)
        btn_h = 34
        options = []
        y = panel.y + 36
        for _i in range(count):
            options.append(pygame.Rect(panel.x + 14, y, panel.w - 28, btn_h))
            y += 42
        cancel = pygame.Rect(panel.x + 14, panel.bottom - 46, panel.w - 28, btn_h)
        return {
            "panel": panel,
            "title_y": panel.y + 10,
            "options": options,
            "cancel": cancel,
        }

    def begin_settings_picker(self, kind):
        self.settings_picker_kind = kind
        if kind == "language":
            self.settings_picker_options = [
                (self.tr("language.ko"), "ko"),
                (self.tr("language.en"), "en"),
                (self.tr("language.ja"), "ja"),
                (self.tr("language.custom", default="사용자 정의"), "custom"),
            ]
        elif kind == "theme":
            self.settings_picker_options = [
                (self.tr("theme.light"), "light"),
                (self.tr("theme.dark"), "dark"),
                (self.tr("theme.transparent"), "transparent"),
            ]
        elif kind == "time24":
            self.settings_picker_options = [
                (self.tr("time.12"), False),
                (self.tr("time.24"), True),
            ]
        elif kind == "brightness":
            self.settings_picker_options = [(f"{v}%", v) for v in range(40, 101, 10)]
        else:
            self.settings_picker_options = []
        self.settings_picker_active = True
        self.settings_picker_start = pygame.time.get_ticks()

    def apply_settings_picker_value(self, kind, value):
        if kind == "language":
            self.set_language(str(value))
            self.save_pref()
            self.toast(self.tr(f"language.{value}", default=str(value)))
        elif kind == "theme":
            self.theme = str(value)
            self.save_pref()
            self.toast(self.tr(f"theme.{value}", default=str(value)))
        elif kind == "time24":
            self.time_24h = bool(value)
            self.save_pref()
            self.toast(self.tr("time.24" if self.time_24h else "time.12"))
        elif kind == "brightness":
            self.brightness = int(clamp(int(value), 40, 100))
            self.save_pref()
            self.toast(f"{self.tr('settings.brightness')}: {self.brightness}%")

    def photo_share_sheet_rects(self):
        w, h = 250, 174
        panel = pygame.Rect((self.w - w) // 2, (self.h - h) // 2, w, h)
        btn_h = 34
        return {
            "panel": panel,
            "title_y": panel.y + 10,
            "copy": pygame.Rect(panel.x + 14, panel.y + 36, panel.w - 28, btn_h),
            "wallpaper": pygame.Rect(panel.x + 14, panel.y + 78, panel.w - 28, btn_h),
            "cancel": pygame.Rect(panel.x + 14, panel.bottom - 46, panel.w - 28, btn_h),
        }

    # 공통 상단 상태바 렌더링(뒤로가기/시간/배터리 등)
    def draw_statusbar(self):
        pal = self.pal()
        home_overlay = self.state in ("HOME", "LOCK")
        if not home_overlay:
            pygame.draw.rect(self.screen, pal["status_bg"], (0, 0, self.w, STATUS_H))
            pygame.draw.line(self.screen, pal["status_line"], (0, STATUS_H - 1), (self.w, STATUS_H - 1))

        if self.state not in ("HOME", "LOCK"):
            br = self.back_button_rect()
            back_bg = pal["button_bg"]
            back_bd = pal["button_border"]
            pygame.draw.rect(self.screen, back_bg, br, border_radius=6)
            pygame.draw.rect(self.screen, back_bd, br, width=1, border_radius=6)
            back_text = self.small_font.render(f"< {self.tr('nav.back')}", True, pal["status_text"])
            self.screen.blit(back_text, (br.x + 6, br.y + 6))
        else:
            dn = norm_text(self.device_name)
            shadow = self.small_font.render(dn, True, (0, 0, 0))
            title = self.small_font.render(dn, True, (255, 255, 255))
            self.screen.blit(shadow, (11, 11))
            self.screen.blit(title, (10, 10))

        now_local = time.localtime()
        if self.state == "LOCK":
            bx = self.w - 10
        else:
            if self.time_24h:
                t = f"{now_local.tm_hour:02d}:{now_local.tm_min:02d}"
            else:
                h12 = now_local.tm_hour % 12
                if h12 == 0:
                    h12 = 12
                ampm = self.tr("time.am" if now_local.tm_hour < 12 else "time.pm")
                t = f"{ampm} {h12:02d}:{now_local.tm_min:02d}"
            if home_overlay:
                time_shadow = self.small_font.render(t, True, (0, 0, 0))
                time_text = self.small_font.render(t, True, (255, 255, 255))
            else:
                time_text = self.small_font.render(t, True, pal["status_text"])
            bx = self.w - 10 - time_text.get_width()
            if home_overlay:
                self.screen.blit(time_shadow, (bx + 1, 11))
            self.screen.blit(time_text, (bx, 10))

        bat_w, bat_h = 26, 12
        bat_x = bx - 10 - bat_w
        bat_y = 12
        is_playing = self.is_music_busy() and not self.music_paused
        indicator_key = "play" if is_playing else "pause"
        ind_rect = pygame.Rect(bat_x - 22, 10, 16, 16)
        if home_overlay:
            self.draw_icon_only(
                pygame.Rect(ind_rect.x + 1, ind_rect.y + 1, ind_rect.w, ind_rect.h),
                indicator_key,
                "",
                False,
                force_color=(0, 0, 0),
            )
        self.draw_icon_only(ind_rect, indicator_key, "", False, force_color=(255, 255, 255) if home_overlay else None)
        bat_col = (255, 255, 255) if home_overlay else pal["status_text"]
        if home_overlay:
            pygame.draw.rect(self.screen, (0, 0, 0), (bat_x + 1, bat_y + 1, bat_w, bat_h), width=2, border_radius=2)
            pygame.draw.rect(self.screen, (0, 0, 0), (bat_x + bat_w + 1, bat_y + 4, 3, bat_h - 6))
        pygame.draw.rect(self.screen, bat_col, (bat_x, bat_y, bat_w, bat_h), width=2, border_radius=2)
        pygame.draw.rect(self.screen, bat_col, (bat_x + bat_w, bat_y + 3, 3, bat_h - 6))
        fill_ratio = clamp(self.fake_battery_level / 100.0, 0.0, 1.0)
        fill = int((bat_w - 4) * fill_ratio)
        pygame.draw.rect(self.screen, bat_col, (bat_x + 2, bat_y + 2, fill, bat_h - 4), border_radius=1)

    def draw_pager(self):
        y = self.h - 24
        total = self.total_pages
        if total <= 1:
            return
        pal = self.pal()
        dot_gap = 10
        dots_w = total * 6 + (total - 1) * dot_gap
        x = (self.w - dots_w) // 2
        for i in range(total):
            r = pygame.Rect(x + i * (6 + dot_gap), y, 6, 6)
            color = pal["pager_active"] if i == self.page else pal["pager_inactive"]
            pygame.draw.ellipse(self.screen, color, r)

    def draw_overlay_background(self, fallback_color):
        if self.wallpaper_img:
            self.screen.blit(self.wallpaper_img, (0, 0))
        else:
            self.screen.fill(fallback_color)
        veil = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 85))
        self.screen.blit(veil, (0, 0))

    def draw_toast(self):
        now = pygame.time.get_ticks()
        if now > self.message_until:
            return
        pal = self.pal()
        fade_ms = 180
        if self.message_duration <= 0:
            alpha_factor = 1.0
        else:
            elapsed = now - self.message_start
            remain = self.message_until - now
            fade_in = clamp(elapsed / fade_ms, 0.0, 1.0)
            fade_out = clamp(remain / fade_ms, 0.0, 1.0)
            alpha_factor = min(fade_in, fade_out)
        alpha = int(255 * alpha_factor)
        msg = self.small_font.render(self.message, True, pal["toast_text"])
        msg.set_alpha(alpha)
        pad = 10
        w = msg.get_width() + pad * 2
        h = msg.get_height() + pad * 2
        x = (self.w - w) // 2
        y = self.h - 70
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(panel, pal["toast_bg"] + (alpha,), (0, 0, w, h), border_radius=8)
        pygame.draw.rect(panel, pal["toast_border"] + (alpha,), (0, 0, w, h), width=1, border_radius=8)
        panel.blit(msg, (pad, pad))
        self.screen.blit(panel, (x, y))

    def language_buttons(self):
        y = STATUS_H + 70
        bw = 70
        gap = 6
        x0 = 14
        return [
            ("ko", pygame.Rect(x0, y, bw, 34)),
            ("en", pygame.Rect(x0 + (bw + gap), y, bw, 34)),
            ("ja", pygame.Rect(x0 + (bw + gap) * 2, y, bw, 34)),
            ("custom", pygame.Rect(x0 + (bw + gap) * 3, y, bw, 34)),
        ]

    def theme_buttons(self):
        y = STATUS_H + 140
        return [
            ("light", pygame.Rect(14, y, 94, 34)),
            ("dark", pygame.Rect(112, y, 94, 34)),
            ("transparent", pygame.Rect(210, y, 96, 34)),
        ]

    def brightness_buttons(self):
        y = STATUS_H + 250
        return {
            "minus": pygame.Rect(14, y, 44, 34),
            "value": pygame.Rect(66, y, 92, 34),
            "plus": pygame.Rect(166, y, 44, 34),
        }

    def name_edit_button(self):
        y = STATUS_H + 320
        return pygame.Rect(210, y, 96, 34)

    def settings_footer_rect(self):
        h = 82
        return pygame.Rect(14, self.h - h - 10, self.w - 28, h)

    def settings_full_rects(self):
        x = 14
        w = self.w - 28
        top = STATUS_H + 48
        row_h = 46
        gap = 8
        language = pygame.Rect(x, top, w, row_h)
        theme = pygame.Rect(x, language.bottom + gap, w, row_h)
        sound = pygame.Rect(x, theme.bottom + gap, w, row_h)
        bright = pygame.Rect(x, sound.bottom + gap, w, row_h)
        by = bright.y + 7
        minus = pygame.Rect(bright.right - 126, by, 34, 32)
        value = pygame.Rect(bright.right - 88, by, 44, 32)
        plus = pygame.Rect(bright.right - 40, by, 34, 32)
        sy = sound.y + 7
        s_minus = pygame.Rect(sound.right - 126, sy, 34, 32)
        s_value = pygame.Rect(sound.right - 88, sy, 44, 32)
        s_plus = pygame.Rect(sound.right - 40, sy, 34, 32)
        return {
            "language": language,
            "theme": theme,
            "brightness": bright,
            "brightness_minus": minus,
            "brightness_value": value,
            "brightness_plus": plus,
            "sound": sound,
            "sound_minus": s_minus,
            "sound_value": s_value,
            "sound_plus": s_plus,
        }

    def settings_full_menu_rows(self):
        rows = [
            ("Bluetooth", "bluetooth"),
            (self.tr("settings.sound", default="소리"), "sound"),
            (self.tr("settings.display", default="디스플레이"), "display"),
            (self.tr("settings.battery", default="배터리"), "battery"),
            (self.tr("settings.wallpaper_style", default="배경화면 및 스타일"), "wallpaper"),
            (self.tr("settings.home_lock", default="홈 화면 및 잠금화면"), "home_lock"),
            (self.tr("settings.general", default="일반"), "general"),
            (self.tr("settings.device_info", default="디바이스 정보"), "info"),
        ]
        x = 14
        w = self.w - 28
        y = STATUS_H + 44
        row_h = 42
        out = []
        for label, key in rows:
            out.append((label, key, pygame.Rect(x, y, w, row_h)))
            y += row_h + 4
        return out

    def settings_bt_toggle_rect(self, row_rect):
        sw_w, sw_h = 42, 22
        return pygame.Rect(row_rect.right - 10 - sw_w, row_rect.centery - sw_h // 2, sw_w, sw_h)

    def settings_sound_rects(self):
        title = pygame.Rect(14, STATUS_H + 54, self.w - 28, 22)
        volume = pygame.Rect(14, title.bottom + 8, self.w - 28, 22)
        eq = pygame.Rect(14, volume.bottom + 14, self.w - 28, 40)
        return {"title": title, "volume": volume, "eq": eq}

    def settings_display_rects(self):
        top = STATUS_H + 48
        mode_label = pygame.Rect(14, top, self.w - 28, 20)
        mode_row = pygame.Rect(14, mode_label.bottom + 6, self.w - 28, 40)
        gap = 8
        bw = (mode_row.w - gap * 2) // 3
        mode_buttons = {
            "light": pygame.Rect(mode_row.x, mode_row.y, bw, mode_row.h),
            "dark": pygame.Rect(mode_row.x + bw + gap, mode_row.y, bw, mode_row.h),
            "transparent": pygame.Rect(mode_row.x + (bw + gap) * 2, mode_row.y, bw, mode_row.h),
        }
        bright_label = pygame.Rect(14, mode_row.bottom + 14, self.w - 28, 20)
        bright_row = pygame.Rect(14, bright_label.bottom + 6, self.w - 28, 40)
        bright_track = pygame.Rect(bright_row.x + 10, bright_row.y + 14, bright_row.w - 68, 12)
        bright_value = pygame.Rect(bright_track.right + 8, bright_row.y + 8, 40, 24)
        return {
            "mode_label": mode_label,
            "mode_buttons": mode_buttons,
            "bright_label": bright_label,
            "bright_row": bright_row,
            "bright_track": bright_track,
            "bright_value": bright_value,
        }

    def settings_homelock_rects(self):
        top = STATUS_H + 48
        home_label = pygame.Rect(14, top, self.w - 28, 20)
        home_row = pygame.Rect(14, home_label.bottom + 6, self.w - 28, 42)
        lock_label = pygame.Rect(14, home_row.bottom + 16, self.w - 28, 20)
        lock_row = pygame.Rect(14, lock_label.bottom + 6, self.w - 28, 42)
        return {
            "home_label": home_label,
            "home_row": home_row,
            "lock_label": lock_label,
            "lock_row": lock_row,
        }

    def settings_general_rows(self):
        rows = [
            ("language", self.tr("settings.language", default="언어")),
            ("datetime", self.tr("settings.datetime", default="날짜 및 시간")),
            ("keyboard", self.tr("settings.keyboard", default="키보드")),
            ("reset", self.tr("settings.device_reset", default="기기 재설정")),
        ]
        y = STATUS_H + 48
        out = []
        for key, label in rows:
            out.append((key, label, pygame.Rect(14, y, self.w - 28, 42)))
            y += 46
        return out

    def settings_general_reset_rows(self):
        rows = [
            ("settings", self.tr("settings.reset.settings", default="모든 설정 재설정")),
            ("wipe", self.tr("settings.reset.wipe", default="모든 콘텐츠 및 설정 지우기")),
        ]
        y = STATUS_H + 48
        out = []
        for key, label in rows:
            out.append((key, label, pygame.Rect(14, y, self.w - 28, 42)))
            y += 46
        return out

    def settings_general_language_rows(self):
        rows = [
            ("ko", self.tr("language.ko", default="한국어")),
            ("en", self.tr("language.en", default="English")),
            ("ja", self.tr("language.ja", default="日本語")),
            ("custom", self.tr("language.custom", default="사용자 정의")),
        ]
        y = STATUS_H + 48
        out = []
        for code, label in rows:
            out.append((code, label, pygame.Rect(14, y, self.w - 28, 42)))
            y += 46
        return out

    def reset_confirm_rect(self):
        w, h = 270, 160
        return pygame.Rect((self.w - w) // 2, (self.h - h) // 2, w, h)

    def reset_confirm_buttons(self):
        r = self.reset_confirm_rect()
        y = r.bottom - 42
        return {
            "no": pygame.Rect(r.x + 16, y, 108, 30),
            "yes": pygame.Rect(r.right - 124, y, 108, 30),
        }

    def reset_confirm_buttons_current(self):
        if not self.general_reset_confirm:
            return self.reset_confirm_buttons()
        p = clamp(
            (pygame.time.get_ticks() - self.general_reset_confirm_start) / max(1, self.general_reset_confirm_ms),
            0.0,
            1.0,
        )
        base = self.reset_confirm_rect()
        scale = 0.92 + 0.08 * p
        ww = int(base.w * scale)
        hh = int(base.h * scale)
        rr = pygame.Rect(base.centerx - ww // 2, base.centery - hh // 2, ww, hh)
        return {
            "no": pygame.Rect(rr.x + 16, rr.bottom - 42, 108, 30),
            "yes": pygame.Rect(rr.right - 124, rr.bottom - 42, 108, 30),
        }

    def settings_general_time_format_buttons(self):
        y = STATUS_H + 120
        w = 96
        h = 34
        left = pygame.Rect(14, y, w, h)
        right = pygame.Rect(left.right, y, w, h)
        return {"12": left, "24": right}

    def settings_info_edit_rects(self, scroll=0.0):
        y = STATUS_H + 48
        y += 24
        name_row = pygame.Rect(14, int(y - scroll), self.w - 28, 42)
        return {"name_row": name_row}

    def settings_info_scroll_rect(self):
        top = STATUS_H + 48
        bottom = self.h - 10
        return pygame.Rect(0, top, self.w, max(1, bottom - top))

    def settings_info_content_height(self):
        y = STATUS_H + 48
        y += 24  # basic label
        y += 42  # name row
        y += 8
        y += 8
        y += 24  # detail label
        y += (46 * 4)  # product/model/serial/bt rows
        y += 8
        y += 24  # software label
        y += 42  # version row
        y += 8
        y += 22  # usage+storage label
        y += (46 * 6)  # usage rows + storage rows
        return y - (STATUS_H + 48)

    def settings_info_scroll_info(self):
        rect = self.settings_info_scroll_rect()
        row_h = 18
        total = max(1, int(math.ceil(self.settings_info_content_height() / float(row_h))))
        return rect, total, row_h

    def settings_info_name_dialog_rects(self):
        w, h = 276, 166
        ky = -int(round(self.vk_lift)) if self.vk_visible else 0
        panel = pygame.Rect((self.w - w) // 2, (self.h - h) // 2 + ky, w, h)
        input_rect = pygame.Rect(panel.x + 14, panel.y + 58, panel.w - 28, 34)
        btn_y = panel.bottom - 42
        return {
            "panel": panel,
            "input": input_rect,
            "cancel": pygame.Rect(panel.x + 16, btn_y, 108, 30),
            "ok": pygame.Rect(panel.right - 124, btn_y, 108, 30),
        }

    def settings_eq_rects(self):
        list_top = STATUS_H + 48
        row_h = 38
        gap = 4
        rows = []
        y = list_top
        for _ in self.eq_presets:
            rows.append(pygame.Rect(14, y, self.w - 28, row_h))
            y += row_h + gap
        bars = pygame.Rect(14, y + 8, self.w - 28, 108)
        return {"rows": rows, "bars": bars}

    def settings_wallstyle_rects(self):
        top = STATUS_H + 52
        wallpaper = pygame.Rect(14, top, self.w - 28, 42)
        accent = pygame.Rect(14, wallpaper.bottom + 8, self.w - 28, 42)
        return {"wallpaper": wallpaper, "accent": accent}

    def settings_accent_rows(self):
        items = [
            ("blue", self.tr("accent.blue", default="블루")),
            ("green", self.tr("accent.green", default="그린")),
            ("pinkred", self.tr("accent.pink", default="핑크")),
            ("warmyellow", self.tr("accent.yellow", default="옐로우")),
            ("orange", self.tr("accent.orange", default="오랜지")),
            ("gray", self.tr("accent.gray", default="그레이")),
        ]
        y = STATUS_H + 48
        out = []
        for key, label in items:
            out.append((key, label, pygame.Rect(14, y, self.w - 28, 42)))
            y += 46
        return out

    def current_accent_label(self):
        labels = {
            "blue": self.tr("accent.blue", default="블루"),
            "green": self.tr("accent.green", default="그린"),
            "pinkred": self.tr("accent.pink", default="핑크"),
            "warmyellow": self.tr("accent.yellow", default="옐로우"),
            "orange": self.tr("accent.orange", default="오랜지"),
            "gray": self.tr("accent.gray", default="그레이"),
        }
        return labels.get(self.accent_key, self.tr("accent.blue", default="블루"))

    def current_wallpaper_label(self):
        cur_abs = os.path.abspath(self.resolve_wallpaper_path())
        for label, rel in (
            (self.tr("wallpaper.default1", default="기본 1"), os.path.join("system", "UI", "default1.png")),
            (self.tr("wallpaper.default2", default="기본 2"), os.path.join("system", "UI", "default2.png")),
            (self.tr("wallpaper.default3", default="기본 3"), os.path.join("system", "UI", "default3.png")),
        ):
            if cur_abs == os.path.abspath(os.path.join(BASE_DIR, rel)):
                return label
        return self.tr("wallpaper.custom", default="사용자 정의")

    def wallpaper_picker_items(self):
        items = []
        default_paths = [
            (self.tr("wallpaper.default1", default="기본 1"), os.path.join("system", "UI", "default1.png")),
            (self.tr("wallpaper.default2", default="기본 2"), os.path.join("system", "UI", "default2.png")),
            (self.tr("wallpaper.default3", default="기본 3"), os.path.join("system", "UI", "default3.png")),
        ]
        for label, rel in default_paths:
            full = os.path.join(BASE_DIR, rel)
            if os.path.isfile(full):
                items.append({
                    "kind": "default",
                    "label": label,
                    "wallpaper_rel": rel,
                    "thumb_path": full,
                })
        custom_thumb = os.path.join(ICON_DIR, "Photo.png")
        items.append({
            "kind": "custom",
            "label": self.tr("wallpaper.custom", default="사용자 정의"),
            "wallpaper_rel": "",
            "thumb_path": custom_thumb if os.path.isfile(custom_thumb) else os.path.join(UI_DIR, "photoimg.png"),
        })
        return items

    def settings_wallpaper_rows(self):
        out = []
        y = STATUS_H + 48
        row_h = 58
        gap = 8
        for item in self.wallpaper_picker_items():
            out.append((item, pygame.Rect(14, y, self.w - 28, row_h)))
            y += row_h + gap
        return out

    def wallpaper_thumb_for_picker(self, path, size):
        key = (path, int(size))
        cached = self.wallpaper_thumb_cache.get(key)
        if cached is not None:
            return cached
        out = pygame.Surface((size, size), pygame.SRCALPHA)
        out.fill((88, 94, 104, 255))
        try:
            if path and os.path.isfile(path):
                base = pygame.image.load(path).convert_alpha()
                iw, ih = base.get_size()
                if iw > 0 and ih > 0:
                    scale = max(size / iw, size / ih)
                    nw = max(1, int(iw * scale))
                    nh = max(1, int(ih * scale))
                    scaled = pygame.transform.smoothscale(base, (nw, nh))
                    x = (nw - size) // 2
                    y = (nh - size) // 2
                    out.blit(scaled, (-x, -y))
        except Exception:
            pass
        self.wallpaper_thumb_cache[key] = out
        return out

    def settings_battery_rects(self):
        top = STATUS_H + 48
        summary = pygame.Rect(14, top, self.w - 28, 58)
        saver = pygame.Rect(14, summary.bottom + 8, self.w - 28, 42)
        health = pygame.Rect(14, saver.bottom + 8, self.w - 28, 42)
        return {"summary": summary, "saver": saver, "health": health}

    def time_format_buttons(self):
        y = STATUS_H + 204
        return {
            "12": pygame.Rect(14, y, 94, 34),
            "24": pygame.Rect(112, y, 94, 34),
        }

    def back_button_rect(self):
        return pygame.Rect(6, 4, 68, 28)

    def lock_bottom_bar_rect(self):
        h = 82
        return pygame.Rect(8, self.h - h - 10, self.w - 16, h)

    def lock_home_button_rect(self):
        bar = self.lock_bottom_bar_rect()
        size = 70
        return pygame.Rect(bar.x + 10, bar.y + (bar.h - size) // 2, size, size)

    def lock_music_bar_rect(self):
        bottom = self.lock_bottom_bar_rect()
        h = 82
        gap = 8
        return pygame.Rect(bottom.x, bottom.y - h - gap, bottom.w, h)

    def calc_display_rect(self):
        return pygame.Rect(8, STATUS_H + 6, self.w - 16, 122)

    def calc_button_rects(self):
        labels = [
            ["C", "()", "%", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["+/-", "0", ".", "="],
        ]
        top = self.calc_display_rect().bottom + 8
        margin = 10
        gap = 8
        cols = 4
        rows = 5
        bw = (self.w - margin * 2 - gap * (cols - 1)) // cols
        bh = (self.h - top - margin - gap * (rows - 1)) // rows
        out = []
        for r in range(rows):
            for c in range(cols):
                x = margin + c * (bw + gap)
                y = top + r * (bh + gap)
                out.append((labels[r][c], pygame.Rect(x, y, bw, bh)))
        return out

    def calc_ce_rect(self):
        d = self.calc_display_rect()
        return pygame.Rect(d.x + 12, d.y + 14, 54, 30)

    def calendar_header_rect(self):
        return pygame.Rect(10, STATUS_H + 10, self.w - 20, 52)

    def calendar_grid_rect(self):
        return pygame.Rect(10, STATUS_H + 76, self.w - 20, self.h - STATUS_H - 88)

    def calendar_nav_rects(self):
        hr = self.calendar_header_rect()
        return {
            "prev": pygame.Rect(hr.x + 2, hr.y + 8, 36, 36),
            "next": pygame.Rect(hr.right - 38, hr.y + 8, 36, 36),
        }

    def calendar_can_prev(self):
        return (self.calendar_year, self.calendar_month) > self.calendar_min

    def calendar_can_next(self):
        return (self.calendar_year, self.calendar_month) < self.calendar_max

    def calendar_title_rect(self):
        hr = self.calendar_header_rect()
        return pygame.Rect(hr.centerx - 90, hr.y + 6, 180, hr.h - 12)

    def calendar_current_pair(self):
        now_tt = time.localtime()
        y = int(now_tt.tm_year)
        m = int(now_tt.tm_mon)
        if (y, m) < self.calendar_min:
            return self.calendar_min
        if (y, m) > self.calendar_max:
            return self.calendar_max
        return (y, m)

    def calendar_shift_month(self, delta):
        y, m = self.calendar_year, self.calendar_month
        if delta < 0:
            y, m = (y - 1, 12) if m == 1 else (y, m - 1)
        elif delta > 0:
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        if (y, m) < self.calendar_min or (y, m) > self.calendar_max:
            return
        self.calendar_year, self.calendar_month = y, m

    def calendar_week_names(self):
        return [
            self.tr("calendar.week.sun", default="일"),
            self.tr("calendar.week.mon", default="월"),
            self.tr("calendar.week.tue", default="화"),
            self.tr("calendar.week.wed", default="수"),
            self.tr("calendar.week.thu", default="목"),
            self.tr("calendar.week.fri", default="금"),
            self.tr("calendar.week.sat", default="토"),
        ]

    def reset_calculator(self):
        self.calc_expr = ""
        self.calc_display = "0"
        self.calc_error = False
        self.calc_just_evaluated = False
        self.calc_prev_expr = ""

    def calc_pretty_expr(self, expr):
        return str(expr).replace("*", "×").replace("/", "÷")

    def calc_fit_text_surface(self, text, base_size, min_size, color, max_w):
        s = str(text)
        size = int(base_size)
        while size >= int(min_size):
            if self.font_path:
                f = pygame.font.Font(self.font_path, size)
            else:
                f = pygame.font.SysFont(None, size)
            surf = f.render(s, True, color)
            if surf.get_width() <= max_w or size == int(min_size):
                if surf.get_width() <= max_w:
                    return surf
                trimmed = s
                while len(trimmed) > 1:
                    trimmed = trimmed[1:]
                    disp = "…" + trimmed
                    surf2 = f.render(disp, True, color)
                    if surf2.get_width() <= max_w:
                        return surf2
                return f.render("…", True, color)
            size -= 1
        return self.small_font.render("…", True, color)

    def calc_format_number(self, value):
        try:
            fv = float(value)
        except Exception:
            return str(value)
        if not math.isfinite(fv):
            return "Error"
        if abs(fv - int(fv)) < 1e-12:
            return str(int(fv))
        text = f"{fv:.12g}"
        return text

    def calc_current_number_start(self):
        i = len(self.calc_expr) - 1
        while i >= 0 and (self.calc_expr[i].isdigit() or self.calc_expr[i] == "."):
            i -= 1
        if i >= 0 and self.calc_expr[i] == "-" and (i == 0 or self.calc_expr[i - 1] in "+-*/("):
            i -= 1
        return i + 1

    def calc_eval(self):
        expr = self.calc_expr.strip()
        if not expr:
            self.calc_display = "0"
            return
        if expr[-1] in "+-*/.":
            expr = expr[:-1]
        if not expr:
            self.calc_display = "0"
            self.calc_expr = ""
            return
        for ch in expr:
            if ch not in "0123456789.+-*/() ":
                self.calc_display = "Error"
                self.calc_error = True
                self.calc_expr = ""
                self.calc_just_evaluated = True
                return
        try:
            value = eval(expr, {"__builtins__": {}}, {})
            shown = self.calc_format_number(value)
            if shown == "Error":
                raise ValueError("invalid number")
            self.calc_prev_expr = self.calc_pretty_expr(expr)
            self.calc_display = shown
            self.calc_expr = shown
            self.calc_error = False
            self.calc_just_evaluated = True
        except ZeroDivisionError:
            self.toast(self.tr("calc.toast.divide_by_zero", default="0으로 나눌 수 없습니다"))
            self.calc_error = False
            self.calc_just_evaluated = False
        except Exception:
            self.calc_display = "Error"
            self.calc_error = True
            self.calc_expr = ""
            self.calc_just_evaluated = True
            self.calc_prev_expr = ""

    def calc_apply_percent(self):
        if not self.calc_expr:
            return
        end = len(self.calc_expr)
        i = end - 1
        while i >= 0 and (self.calc_expr[i].isdigit() or self.calc_expr[i] == "."):
            i -= 1
        if i == end - 1:
            return
        if i >= 0 and self.calc_expr[i] == "-" and (i == 0 or self.calc_expr[i - 1] in "+-*/("):
            i -= 1
        start = i + 1
        segment = self.calc_expr[start:end]
        if not segment:
            return
        self.calc_expr = self.calc_expr[:start] + f"({segment}/100)" + self.calc_expr[end:]
        self.calc_display = self.calc_expr
        self.calc_prev_expr = ""
        self.calc_just_evaluated = False

    def calc_toggle_sign(self):
        if not self.calc_expr:
            self.calc_expr = "-"
            self.calc_display = self.calc_expr
            self.calc_prev_expr = ""
            self.calc_just_evaluated = False
            return
        start = self.calc_current_number_start()
        if start >= len(self.calc_expr):
            if self.calc_expr[-1] in "+-*/(":
                self.calc_expr += "-"
                self.calc_display = self.calc_expr
                self.calc_prev_expr = ""
                self.calc_just_evaluated = False
            return
        if self.calc_expr[start:start + 1] == "-":
            self.calc_expr = self.calc_expr[:start] + self.calc_expr[start + 1:]
        else:
            self.calc_expr = self.calc_expr[:start] + "-" + self.calc_expr[start:]
        self.calc_display = self.calc_expr if self.calc_expr else "0"
        self.calc_prev_expr = ""
        self.calc_just_evaluated = False

    def calc_add_parenthesis(self):
        opens = self.calc_expr.count("(")
        closes = self.calc_expr.count(")")
        if not self.calc_expr or self.calc_expr[-1] in "+-*/(":
            self.calc_expr += "("
        elif opens > closes:
            self.calc_expr += ")"
        else:
            self.calc_expr += "×("
        self.calc_expr = self.calc_expr.replace("×", "*")
        self.calc_display = self.calc_expr
        self.calc_prev_expr = ""
        self.calc_just_evaluated = False

    def calc_append(self, token):
        if self.calc_error:
            self.reset_calculator()
        if token in "0123456789":
            if self.calc_just_evaluated:
                self.calc_expr = token
            else:
                self.calc_expr += token
            self.calc_display = self.calc_expr
            self.calc_prev_expr = ""
            self.calc_just_evaluated = False
            return
        if token == ".":
            if self.calc_just_evaluated:
                self.calc_expr = "0."
                self.calc_display = self.calc_expr
                self.calc_prev_expr = ""
                self.calc_just_evaluated = False
                return
            start = self.calc_current_number_start()
            cur = self.calc_expr[start:]
            if "." in cur:
                return
            if not cur or cur in ("-", "+"):
                self.calc_expr += "0."
            else:
                self.calc_expr += "."
            self.calc_display = self.calc_expr
            self.calc_prev_expr = ""
            return
        if token in "+-×÷":
            op = "*" if token == "×" else "/" if token == "÷" else token
            if not self.calc_expr:
                if op == "-":
                    self.calc_expr = "-"
                    self.calc_display = self.calc_expr
                    self.calc_prev_expr = ""
                return
            if self.calc_expr[-1] in "+-*/":
                self.calc_expr = self.calc_expr[:-1] + op
            else:
                self.calc_expr += op
            self.calc_display = self.calc_expr
            self.calc_prev_expr = ""
            self.calc_just_evaluated = False

    def handle_calc_button(self, label):
        if label == "C":
            self.reset_calculator()
            return
        if label == "CE":
            if self.calc_error:
                self.reset_calculator()
                return
            if self.calc_just_evaluated:
                self.calc_expr = self.calc_display if self.calc_display != "Error" else ""
                self.calc_just_evaluated = False
            if self.calc_expr:
                self.calc_expr = self.calc_expr[:-1]
            self.calc_display = self.calc_expr if self.calc_expr else "0"
            self.calc_prev_expr = ""
            return
        if label == "=":
            self.calc_eval()
            return
        if label == "+/-":
            self.calc_toggle_sign()
            return
        if label == "%":
            self.calc_apply_percent()
            return
        if label == "()":
            self.calc_add_parenthesis()
            return
        self.calc_append(label)

    def music_control_rects(self):
        if self.music_view == "NOW":
            layout = self.now_layout_rects()
            return {
                "prev": layout["prev"],
                "play": layout["play"],
                "next": layout["next"],
                "shuffle": layout["shuffle"],
                "repeat": layout["repeat"],
                "volume": layout["volume"],
                "queue": layout["queue"],
            }
        y = self.h - 52
        return {
            "shuffle": pygame.Rect(14, y - 38, 68, 30),
            "repeat": pygame.Rect(90, y - 38, 68, 30),
            "prev": pygame.Rect(16, y, 66, 34),
            "play": pygame.Rect(92, y, 66, 34),
            "next": pygame.Rect(168, y, 66, 34),
            "volume": pygame.Rect(242, y + 4, 64, 26),
            "queue": pygame.Rect(14, y, 0, 0),
        }

    def now_layout_rects(self):
        title_y = STATUS_H + 8
        artist_y = STATUS_H + 34
        art_y = STATUS_H + 56
        horizontal = self.w - 28
        controls_h = 130
        art_size = int(clamp(min(horizontal, self.h - art_y - controls_h), 150, horizontal))
        art_x = (self.w - art_size) // 2
        art_rect = pygame.Rect(art_x, art_y, art_size, art_size)
        prog = pygame.Rect(art_rect.x, art_rect.bottom + 10, art_rect.w, 8)
        time_y = prog.bottom + 2
        row1_y = time_y + 20
        btn_w = 82
        gap = 10
        row1_total = btn_w * 3 + gap * 2
        row1_x = (self.w - row1_total) // 2
        row2_y = row1_y + 50
        vol_w = 152
        vol_x = self.w // 2 - vol_w // 2
        queue_rect = pygame.Rect(art_rect.right - 30, title_y + 1, 30, 30)
        return {
            "title_y": title_y,
            "artist_y": artist_y,
            "art": art_rect,
            "progress": prog,
            "time_y": time_y,
            "prev": pygame.Rect(row1_x, row1_y, btn_w, 34),
            "play": pygame.Rect(row1_x + btn_w + gap, row1_y, btn_w, 34),
            "next": pygame.Rect(row1_x + (btn_w + gap) * 2, row1_y, btn_w, 34),
            "shuffle": pygame.Rect(art_rect.x, row2_y, 28, 28),
            "volume": pygame.Rect(vol_x, row2_y + 4, vol_w, 22),
            "repeat": pygame.Rect(art_rect.right - 28, row2_y, 28, 28),
            "queue": queue_rect,
        }

    # 음악 메뉴 카드 배치: 지금 재생은 크게, 나머지는 동일 카드 크기
    def music_menu_rects(self):
        gap = 10
        side = 16
        top = STATUS_H + 90
        card_w = (self.w - side * 2 - gap) // 2
        card_h = 82
        now_h = 98
        row2_y = top + now_h + gap
        row3_y = row2_y + card_h + gap
        return {
            "now": pygame.Rect(side, top, self.w - side * 2, now_h),
            "list": pygame.Rect(side, row2_y, card_w, card_h),
            "albums": pygame.Rect(side + card_w + gap, row2_y, card_w, card_h),
            "artists": pygame.Rect(side, row3_y, card_w, card_h),
            "genres": pygame.Rect(side + card_w + gap, row3_y, card_w, card_h),
        }

    def music_list_rect(self):
        if self.music_view in ("LIST", "QUEUE"):
            return pygame.Rect(8, STATUS_H + 98, self.w - 16, self.h - STATUS_H - 112)
        return pygame.Rect(14, STATUS_H + 94, self.w - 28, self.h - STATUS_H - 190)

    def video_list_rect(self):
        return pygame.Rect(8, STATUS_H + 98, self.w - 16, self.h - STATUS_H - 112)

    def video_search_rect(self):
        return pygame.Rect(8, STATUS_H + 62, 188, 30)

    def video_sort_button_rect(self):
        return pygame.Rect(202, STATUS_H + 62, 110, 30)

    def video_sort_option_rects(self):
        b = self.video_sort_button_rect()
        row_h = 26
        return {
            "name": pygame.Rect(b.x, b.y + b.h + 2, b.w, row_h),
            "date": pygame.Rect(b.x, b.y + b.h + 2 + row_h, b.w, row_h),
        }

    def text_list_rect(self):
        return self.video_list_rect()

    def text_search_rect(self):
        return self.video_search_rect()

    def text_sort_button_rect(self):
        return self.video_sort_button_rect()

    def text_sort_option_rects(self):
        b = self.text_sort_button_rect()
        row_h = 26
        return {
            "name": pygame.Rect(b.x, b.y + b.h + 2, b.w, row_h),
            "date": pygame.Rect(b.x, b.y + b.h + 2 + row_h, b.w, row_h),
        }

    def files_list_rect(self):
        return self.video_list_rect()

    def files_effective_list_rect(self):
        rect = self.files_list_rect().copy()
        if self.files_view == "LIST" and self.files_selection_enabled() and self.files_selected:
            rect.h = max(40, rect.h - 44)
        return rect

    def files_search_rect(self):
        return self.video_search_rect()

    def files_sort_button_rect(self):
        return pygame.Rect(202, STATUS_H + 62, 76, 30)

    def files_order_button_rect(self):
        return pygame.Rect(282, STATUS_H + 62, 30, 30)

    def files_sort_option_rects(self):
        b = self.files_sort_button_rect()
        row_h = 26
        return {
            "name": pygame.Rect(b.x, b.y + b.h + 2, b.w, row_h),
            "date": pygame.Rect(b.x, b.y + b.h + 2 + row_h, b.w, row_h),
            "size": pygame.Rect(b.x, b.y + b.h + 2 + row_h * 2, b.w, row_h),
        }

    def files_info_rect(self):
        return pygame.Rect(8, STATUS_H + 42, self.w - 16, self.h - STATUS_H - 106)

    def files_info_action_rects(self, info_rect=None):
        rect = info_rect if info_rect is not None else self.files_info_rect()
        btn_h = 30
        del_w = 62
        ren_w = 92
        gap = 8
        y = min(self.h - btn_h - 10, rect.bottom + 8)
        delete = pygame.Rect(self.w - 10 - del_w, y, del_w, btn_h)
        rename = pygame.Rect(delete.x - gap - ren_w, y, ren_w, btn_h)
        return {"rename": rename, "delete": delete}

    def files_info_rename_dialog_rects(self):
        w, h = 276, 166
        ky = -int(round(self.vk_lift)) if self.vk_visible else 0
        panel = pygame.Rect((self.w - w) // 2, (self.h - h) // 2 + ky, w, h)
        input_rect = pygame.Rect(panel.x + 14, panel.y + 58, panel.w - 28, 34)
        btn_y = panel.bottom - 42
        return {
            "panel": panel,
            "input": input_rect,
            "cancel": pygame.Rect(panel.x + 16, btn_y, 108, 30),
            "ok": pygame.Rect(panel.right - 124, btn_y, 108, 30),
        }

    def files_selection_enabled(self):
        if self.files_source == "trash":
            return True
        if self.files_source != "internal":
            return False
        p = self.files_path.replace("\\", "/").strip("/")
        return bool(p)

    def files_checkbox_rect(self, row_rect, thumb_size):
        cb = 18
        y = row_rect.y + (row_rect.h - cb) // 2
        return pygame.Rect(row_rect.x + 4, y, cb, cb)

    def files_checkbox_hit_rect(self, row_rect, thumb_size):
        return self.files_checkbox_rect(row_rect, thumb_size).inflate(10, 10)

    def files_selected_action_rects(self):
        bar_h = 36
        y = self.h - bar_h - 6
        if self.files_source == "trash":
            btn_w = 76
        else:
            btn_w = 40
        btn_h = 30
        gap = 8
        right = pygame.Rect(self.w - 10 - btn_w, y + (bar_h - btn_h) // 2, btn_w, btn_h)
        left = None
        left_start = 10
        if self.files_source == "trash":
            left = pygame.Rect(10, y + (bar_h - btn_h) // 2, btn_w, btn_h)
            left_start = left.right + gap
        center = pygame.Rect(left_start, y, right.x - left_start - gap, bar_h)
        bar = pygame.Rect(6, y, self.w - 12, bar_h)
        out = {"bar": bar, "right": right, "center": center}
        if left is not None:
            out["left"] = left
        return out

    def begin_files_delete_confirm(self, action="move_trash"):
        if not self.files_selected:
            return
        self.files_delete_confirm_paths = sorted(list(self.files_selected))
        self.files_delete_confirm_action = str(action)
        self.files_delete_confirm_active = True
        self.files_delete_confirm_start = pygame.time.get_ticks()

    def delete_selected_files_to_trash(self, paths=None):
        targets = list(paths) if paths is not None else list(self.files_selected)
        if not targets:
            return 0
        moved = 0
        root = os.path.join(BASE_DIR, "files")
        trash_root = os.path.join(BASE_DIR, "files", ".trash", "files")
        for p in targets:
            try:
                abs_src = os.path.abspath(p)
                if not os.path.exists(abs_src):
                    continue
                rel = os.path.relpath(abs_src, root)
                rel_parent = os.path.dirname(rel)
                target_dir = os.path.join(trash_root, rel_parent)
                os.makedirs(target_dir, exist_ok=True)
                target = self.unique_path_with_suffix(target_dir, os.path.basename(abs_src))
                shutil.move(abs_src, target)
                self.record_trash_meta(abs_src, target)
                moved += 1
            except Exception:
                continue
        self.files_selected = set()
        return moved

    def rename_info_file(self):
        ent = self.files_info_entry if isinstance(self.files_info_entry, dict) else None
        if not ent:
            return False
        src = ent.get("path", "")
        if not src or (not os.path.isfile(src)):
            self.toast(self.tr("files.action.rename_failed", default="이름 변경에 실패했습니다"))
            return False
        dirpath = os.path.dirname(src)
        ext = ent.get("ext", "")
        if not ext:
            _root, ext = os.path.splitext(src)
        new_base = norm_text(self.files_info_rename_text).strip()
        if not new_base:
            self.toast(self.tr("files.action.rename_failed", default="이름 변경에 실패했습니다"))
            return False
        candidate_name = f"{new_base}{ext}"
        candidate_path = os.path.join(dirpath, candidate_name)
        if os.path.abspath(candidate_path) != os.path.abspath(src) and os.path.exists(candidate_path):
            candidate_path = self.unique_path_with_suffix(dirpath, candidate_name)
        try:
            os.rename(src, candidate_path)
        except Exception:
            self.toast(self.tr("files.action.rename_failed", default="이름 변경에 실패했습니다"))
            return False

        st = None
        try:
            st = os.stat(candidate_path)
        except Exception:
            pass
        ent["path"] = candidate_path
        ent["name"] = os.path.basename(candidate_path)
        _root, ent_ext = os.path.splitext(ent["name"])
        ent["ext"] = ent_ext.lower()
        if st:
            ent["size"] = int(getattr(st, "st_size", ent.get("size", 0)))
            ent["modified"] = float(getattr(st, "st_mtime", ent.get("modified", 0)))
            ent["created"] = float(getattr(st, "st_birthtime", getattr(st, "st_ctime", ent.get("created", 0))))
        self.toast(self.tr("files.action.renamed", default="이름을 변경했습니다"))
        return True

    def load_trash_meta_index(self):
        idx = {}
        try:
            if not os.path.isfile(TRASH_META_PATH):
                return idx
            with open(TRASH_META_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = data.get("items", []) if isinstance(data, dict) else []
            if not isinstance(items, list):
                return idx
            for it in items:
                if not isinstance(it, dict):
                    continue
                tp = os.path.abspath(str(it.get("trash_path", "")))
                if not tp:
                    continue
                ds = str(it.get("deleted_at", "")).strip()
                ts = 0.0
                if ds:
                    try:
                        ts = float(time.mktime(time.strptime(ds, "%Y-%m-%d %H:%M:%S")))
                    except Exception:
                        ts = 0.0
                idx[tp] = {
                    "deleted_at": ds,
                    "deleted_ts": ts,
                    "original_path": str(it.get("original_path", "")),
                    "trash_path": str(it.get("trash_path", "")),
                }
        except Exception:
            return {}
        return idx

    def save_trash_meta_items(self, items):
        os.makedirs(os.path.dirname(TRASH_META_PATH), exist_ok=True)
        with open(TRASH_META_PATH, "w", encoding="utf-8") as f:
            json.dump({"items": items}, f, ensure_ascii=False, indent=2)

    def remove_trash_meta_for_paths(self, abs_paths):
        target = {os.path.abspath(p) for p in abs_paths}
        try:
            if not os.path.isfile(TRASH_META_PATH):
                return
            with open(TRASH_META_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = data.get("items", []) if isinstance(data, dict) else []
            if not isinstance(items, list):
                return
            out = []
            for it in items:
                if not isinstance(it, dict):
                    continue
                tp = os.path.abspath(str(it.get("trash_path", "")))
                if tp in target:
                    continue
                out.append(it)
            self.save_trash_meta_items(out)
        except Exception:
            return

    def permanently_delete_selected_trash_files(self, paths):
        removed = 0
        deleted_paths = []
        for p in list(paths):
            try:
                ap = os.path.abspath(p)
                if os.path.isfile(ap):
                    os.remove(ap)
                    removed += 1
                    deleted_paths.append(ap)
            except Exception:
                continue
        if deleted_paths:
            self.remove_trash_meta_for_paths(deleted_paths)
        self.files_selected = set()
        return removed

    def restore_selected_trash_files(self, paths):
        restored = 0
        meta = self.load_trash_meta_index()
        restored_paths = []
        for p in list(paths):
            try:
                src = os.path.abspath(p)
                if not os.path.exists(src):
                    continue
                m = meta.get(src, {})
                original = str(m.get("original_path", "")).strip()
                if not original:
                    original = os.path.join(BASE_DIR, "files", os.path.basename(src))
                target_dir = os.path.dirname(original)
                if target_dir:
                    os.makedirs(target_dir, exist_ok=True)
                target = self.unique_path_with_suffix(target_dir or os.path.dirname(original), os.path.basename(original))
                shutil.move(src, target)
                restored += 1
                restored_paths.append(src)
            except Exception:
                continue
        if restored_paths:
            self.remove_trash_meta_for_paths(restored_paths)
        self.files_selected = set()
        return restored

    def progress_rect(self):
        if self.music_view == "NOW":
            return self.now_layout_rects()["progress"]
        return pygame.Rect(14, STATUS_H + 70, self.w - 28, 12)

    def volume_track_rect(self, volume_rect):
        if self.music_view == "NOW":
            return pygame.Rect(volume_rect.x + 2, volume_rect.y + 2, volume_rect.w - 4, volume_rect.h - 4)
        return volume_rect

    def music_search_rect(self):
        return pygame.Rect(8, STATUS_H + 62, 188, 30)

    def music_sort_button_rect(self):
        return pygame.Rect(202, STATUS_H + 62, 110, 30)

    def music_sort_option_rects(self):
        b = self.music_sort_button_rect()
        row_h = 26
        return {
            "name": pygame.Rect(b.x, b.y + b.h + 2, b.w, row_h),
            "album": pygame.Rect(b.x, b.y + b.h + 2 + row_h, b.w, row_h),
            "artist": pygame.Rect(b.x, b.y + b.h + 2 + row_h * 2, b.w, row_h),
        }

    def music_group_rect(self):
        return pygame.Rect(8, STATUS_H + 98, self.w - 16, self.h - STATUS_H - 112)

    def music_scroll_info(self):
        if self.music_view == "LIST":
            rect = self.music_list_rect()
            total = len(self.filtered_music_indices())
            row_h = 30
            return rect, total, row_h
        if self.music_view == "QUEUE":
            rect = self.music_list_rect()
            total = len(self.play_queue_indices())
            row_h = 30
            return rect, total, row_h
        if self.music_view == "ALBUMS":
            rect = self.music_group_rect()
            total = len(self.group_items("album"))
            row_h = 30
            return rect, total, row_h
        if self.music_view == "ARTIST_ALBUMS":
            rect = self.music_group_rect()
            total = len(self.group_items("album", artist_filter=self.music_ctx_artist))
            row_h = 30
            return rect, total, row_h
        if self.music_view == "ARTISTS":
            rect = self.music_group_rect()
            total = len(self.group_items("artist"))
            row_h = 30
            return rect, total, row_h
        if self.music_view == "GENRES":
            rect = self.music_group_rect()
            total = len(self.group_items("genre"))
            row_h = 30
            return rect, total, row_h
        return None, 0, 30

    def video_scroll_info(self):
        rect = self.video_list_rect()
        total = len(self.filtered_video_files())
        row_h = 48
        return rect, total, row_h

    def text_scroll_info(self):
        rect = self.text_list_rect()
        total = len(self.filtered_text_files())
        row_h = 48
        return rect, total, row_h

    def files_scroll_info(self):
        rect = self.files_effective_list_rect()
        total = len(self.filtered_file_entries()) if self.files_view == "LIST" else len(self.files_root_entries())
        row_h = 48
        return rect, total, row_h

    def files_root_entries(self):
        return [
            {"key": "internal", "label": self.tr("files.storage.internal", default="내부 저장소"), "enabled": True},
            {"key": "external", "label": self.tr("files.storage.external", default="외부 저장소"), "enabled": False},
            {"key": "trash", "label": self.tr("files.storage.trash", default="휴지통"), "enabled": True},
        ]

    def files_root_path(self):
        if self.files_source == "trash":
            return os.path.join(BASE_DIR, "files", ".trash", "files")
        return os.path.join(BASE_DIR, "files")

    def files_safe_join(self, root, subpath):
        root_abs = os.path.abspath(root)
        cand = os.path.abspath(os.path.join(root_abs, subpath))
        try:
            if os.path.commonpath([root_abs, cand]) != root_abs:
                return root_abs
        except Exception:
            return root_abs
        return cand

    def folder_file_count(self, path):
        count = 0
        try:
            for _r, _d, files in os.walk(path):
                count += len(files)
        except Exception:
            return 0
        return count

    def file_size_of(self, path):
        if os.path.isdir(path):
            total = 0
            try:
                for r, _d, files in os.walk(path):
                    for n in files:
                        fp = os.path.join(r, n)
                        try:
                            total += os.path.getsize(fp)
                        except Exception:
                            pass
            except Exception:
                return 0
            return total
        try:
            return int(os.path.getsize(path))
        except Exception:
            return 0

    def file_created_at(self, path):
        try:
            st = os.stat(path)
            return float(getattr(st, "st_birthtime", st.st_ctime))
        except Exception:
            return 0.0

    def file_modified_at(self, path):
        try:
            return float(os.path.getmtime(path))
        except Exception:
            return 0.0

    def format_file_size(self, n):
        size = float(max(0, int(n)))
        units = ["B", "KB", "MB", "GB", "TB"]
        idx = 0
        while size >= 1024.0 and idx < len(units) - 1:
            size /= 1024.0
            idx += 1
        if idx == 0:
            return f"{int(size)}{units[idx]}"
        return f"{size:.1f}{units[idx]}"

    def files_folder_icon_key(self, name):
        ln = norm_text(name).lower()
        if ln in ("document", "documents", "문서"):
            return "folder_document"
        if ln in ("image", "images", "photo", "photos", "사진"):
            return "folder_image"
        if ln in ("music", "muisc", "음악"):
            return "folder_music"
        if ln in ("video", "videos", "비디오"):
            return "folder_video"
        return "folder"

    def files_display_name(self, entry):
        name = norm_text(entry.get("name", ""))
        if entry.get("is_dir"):
            ln = name.lower()
            if ln == "document":
                return self.tr("files.folder.document", default="텍스트")
            if ln == "image":
                return self.tr("files.folder.image", default="사진")
            if ln == "music":
                return self.tr("files.folder.music", default="음악")
            if ln == "video":
                return self.tr("files.folder.video", default="비디오")
        return name

    def file_icon_for_entry(self, entry, size):
        accent = self.ui_accent()
        key = entry.get("icon_key", "file")
        cache_key = (key, int(size), tuple(accent))
        cached = self.files_icon_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self.files_ui_icons.get(key) or self.files_ui_icons.get("file")
        if base is None:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            self.files_icon_cache[cache_key] = surf
            return surf
        iw, ih = base.get_size()
        scale = min(size / max(1, iw), size / max(1, ih))
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        icon = pygame.transform.smoothscale(base, (nw, nh))
        # Keep original colors for PNG-based icons; tint only SVG-style icons.
        keep_original = key in ("folder_document", "folder_image", "folder_music", "folder_video", "file")
        if keep_original:
            self.files_icon_cache[cache_key] = icon
            return icon
        tint = icon.copy()
        tint.fill(accent + (0,), special_flags=pygame.BLEND_RGB_ADD)
        self.files_icon_cache[cache_key] = tint
        return tint

    def default_photo_thumb(self, size):
        size = int(clamp(size, 16, 256))
        key = ("__photo_default__", size)
        cached = self.photo_thumb_cache.get(key)
        if cached is not None:
            return cached
        surf = None
        try:
            if os.path.isfile(DEFAULT_PHOTO_THUMB):
                base = pygame.image.load(DEFAULT_PHOTO_THUMB).convert_alpha()
                surf = self._rounded_image_surface(base, size, radius=6)
        except Exception:
            surf = None
        if surf is None:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(surf, (72, 76, 86), (0, 0, size, size), border_radius=6)
        self.photo_thumb_cache[key] = surf
        return surf

    def file_thumb_for_entry(self, entry, size):
        if entry.get("is_dir"):
            return self.file_icon_for_entry(entry, size)
        path = entry.get("path", "")
        ext = str(entry.get("ext", "")).lower()
        key = ("__files_thumb__", path, int(size))
        cached = self.files_icon_cache.get(key)
        if cached is not None:
            return cached

        audio_exts = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}
        video_exts = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
        image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".heic", ".heif"}

        surf = None
        if ext in audio_exts:
            image_bytes = None
            try:
                if MutagenFile:
                    audio = MutagenFile(path)
                    if audio:
                        tags = getattr(audio, "tags", None)
                        if tags:
                            if hasattr(tags, "keys"):
                                for k in tags.keys():
                                    if str(k).startswith("APIC"):
                                        image_bytes = tags[k].data
                                        break
                            if not image_bytes and "covr" in tags and tags["covr"]:
                                image_bytes = bytes(tags["covr"][0])
                        if not image_bytes and getattr(audio, "pictures", None):
                            if audio.pictures:
                                image_bytes = audio.pictures[0].data
            except Exception:
                image_bytes = None
            if image_bytes:
                try:
                    base = pygame.image.load(io.BytesIO(image_bytes)).convert_alpha()
                    surf = self._rounded_image_surface(base, int(size), radius=6)
                except Exception:
                    surf = None
            if surf is None:
                surf = self.default_album_art(size)
        elif ext in video_exts:
            surf = self.video_thumbnail_for(path, size)
            if surf is None:
                surf = self.default_video_thumb(size)
        elif ext in image_exts:
            try:
                src = self.oriented_photo_surface(path)
                iw, ih = src.get_size()
                if iw <= 0 or ih <= 0:
                    raise ValueError("invalid image size")
                scale = max(size / iw, size / ih)
                nw = max(1, int(iw * scale))
                nh = max(1, int(ih * scale))
                sc = pygame.transform.smoothscale(src, (nw, nh))
                cx = max(0, (nw - size) // 2)
                cy = max(0, (nh - size) // 2)
                surf = sc.subsurface((cx, cy, size, size)).copy()
            except Exception:
                surf = self.default_photo_thumb(size)
        elif ext in (".txt", ".pdf"):
            surf = self.default_text_thumb(size)
        else:
            surf = self.file_icon_for_entry({"icon_key": "file", "is_dir": False}, size)
        self.files_icon_cache[key] = surf
        return surf

    def current_files_entries(self):
        root = self.files_root_path()
        if self.files_source == "trash":
            meta_idx = self.load_trash_meta_index()
            entries = []
            try:
                for r, _dirs, files in os.walk(root):
                    for name in files:
                        if name.startswith("."):
                            continue
                        full = os.path.join(r, name)
                        ext = os.path.splitext(name)[1].lower()
                        ctime = self.file_created_at(full)
                        mtime = self.file_modified_at(full)
                        size = self.file_size_of(full)
                        m = meta_idx.get(os.path.abspath(full), {})
                        deleted_at = str(m.get("deleted_at", "")).strip()
                        deleted_ts = float(m.get("deleted_ts", 0.0) or 0.0)
                        original_path = str(m.get("original_path", "")).strip()
                        entries.append(
                            {
                                "name": norm_text(name),
                                "path": full,
                                "is_dir": False,
                                "ext": ext,
                                "created": ctime,
                                "modified": mtime,
                                "size": int(size),
                                "count": 0,
                                "icon_key": "file",
                                "deleted_at": deleted_at,
                                "deleted_ts": deleted_ts,
                                "original_path": original_path,
                            }
                        )
            except Exception:
                return []
            return entries

        abs_dir = self.files_safe_join(root, self.files_path)
        entries = []
        try:
            names = sorted(os.listdir(abs_dir), key=lambda x: norm_text(x).lower())
        except Exception:
            names = []
        for name in names:
            if name.startswith("."):
                continue
            full = os.path.join(abs_dir, name)
            is_dir = os.path.isdir(full)
            ext = os.path.splitext(name)[1].lower()
            ctime = self.file_created_at(full)
            mtime = self.file_modified_at(full)
            size = self.file_size_of(full) if is_dir else self.file_size_of(full)
            count = self.folder_file_count(full) if is_dir else 0
            icon_key = self.files_folder_icon_key(name) if is_dir else "file"
            entries.append(
                {
                    "name": norm_text(name),
                    "path": full,
                    "is_dir": is_dir,
                    "ext": ext,
                    "created": ctime,
                    "modified": mtime,
                    "size": int(size),
                    "count": int(count),
                    "icon_key": icon_key,
                }
            )
        return entries

    def filtered_file_entries(self):
        items = self.current_files_entries()
        q = self.files_search.strip().lower()
        if q:
            items = [e for e in items if q in e["name"].lower()]
        if self.files_source == "trash":
            reverse = bool(self.files_sort_desc)
            items.sort(key=lambda e: (float(e.get("deleted_ts", 0.0)), e["name"].lower()), reverse=reverse)
            return items
        reverse = bool(self.files_sort_desc)
        if self.files_sort == "date":
            items.sort(key=lambda e: (e["modified"], e["name"].lower()), reverse=reverse)
        elif self.files_sort == "size":
            items.sort(key=lambda e: (e["size"], e["name"].lower()), reverse=reverse)
        else:
            items.sort(key=lambda e: e["name"].lower(), reverse=reverse)
        return items

    def video_file_created_at(self, path):
        try:
            st = os.stat(path)
            return float(getattr(st, "st_birthtime", st.st_ctime))
        except Exception:
            return 0.0

    def photo_file_created_at(self, path):
        try:
            st = os.stat(path)
            return float(getattr(st, "st_birthtime", getattr(st, "st_ctime", st.st_mtime)))
        except Exception:
            return 0.0

    def photo_meta_taken_at(self, path):
        if path in self.photo_meta_time_cache:
            return self.photo_meta_time_cache[path]
        ts = 0.0
        if PILImage is not None:
            try:
                with PILImage.open(path) as img:
                    exif = img.getexif()
                dt_raw = None
                for tag in (36867, 36868, 306):  # DateTimeOriginal, DateTimeDigitized, DateTime
                    v = exif.get(tag) if exif else None
                    if v:
                        dt_raw = str(v).strip()
                        break
                if dt_raw:
                    tt = time.strptime(dt_raw, "%Y:%m:%d %H:%M:%S")
                    ts = float(time.mktime(tt))
            except Exception:
                ts = 0.0
        self.photo_meta_time_cache[path] = ts
        return ts

    def photo_info_for(self, path):
        cached = self.photo_info_cache.get(path)
        if cached:
            return cached
        info = {
            "datetime": self.tr("photo.meta.time.none", default="촬영 시간 정보 없음"),
        }
        if PILImage is not None:
            try:
                with PILImage.open(path) as img:
                    exif = img.getexif()
                if exif:
                    dt_raw = None
                    for tag in (36867, 36868, 306):  # DateTimeOriginal, DateTimeDigitized, DateTime
                        v = exif.get(tag)
                        if v:
                            dt_raw = str(v).strip()
                            break
                    if dt_raw:
                        dt_show = dt_raw
                        if len(dt_raw) >= 10 and dt_raw[4:5] == ":" and dt_raw[7:8] == ":":
                            dt_show = dt_raw[:10].replace(":", "-") + dt_raw[10:]
                        info["datetime"] = dt_show
            except Exception:
                pass

        if info["datetime"] == self.tr("photo.meta.time.none", default="촬영 시간 정보 없음"):
            ts = self.photo_meta_taken_at(path)
            if ts <= 0:
                ts = self.photo_file_created_at(path)
            if ts > 0:
                info["datetime"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

        self.photo_info_cache[path] = info
        return info

    def unique_path_with_suffix(self, directory, filename):
        root, ext = os.path.splitext(filename)
        candidate = os.path.join(directory, filename)
        n = 1
        while os.path.exists(candidate):
            candidate = os.path.join(directory, f"{root} ({n}){ext}")
            n += 1
        return candidate

    def record_trash_meta(self, original_path, trash_path):
        os.makedirs(os.path.dirname(TRASH_META_PATH), exist_ok=True)
        data = {"items": []}
        try:
            if os.path.isfile(TRASH_META_PATH):
                with open(TRASH_META_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        data = loaded
        except Exception:
            data = {"items": []}
        items = data.get("items")
        if not isinstance(items, list):
            items = []
            data["items"] = items
        items.append(
            {
                "deleted_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "original_path": original_path,
                "trash_path": trash_path,
                "original_rel": os.path.relpath(original_path, BASE_DIR),
                "trash_rel": os.path.relpath(trash_path, BASE_DIR),
            }
        )
        with open(TRASH_META_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def delete_photo_to_trash(self, path):
        try:
            os.makedirs(TRASH_IMAGE_DIR, exist_ok=True)
            fname = os.path.basename(path)
            target = self.unique_path_with_suffix(TRASH_IMAGE_DIR, fname)
            shutil.move(path, target)
            self.record_trash_meta(path, target)
            return target
        except Exception:
            return None

    def confirm_delete_current_photo(self):
        files = self.filtered_photo_files()
        if not files:
            return
        self.photo_index = int(clamp(self.photo_index, 0, len(files) - 1))
        self.photo_delete_target_path = files[self.photo_index]
        self.photo_delete_confirm_active = True
        self.photo_delete_confirm_start = pygame.time.get_ticks()

    def execute_photo_delete_confirmed(self):
        src = self.photo_delete_target_path
        self.photo_delete_target_path = ""
        self.photo_delete_confirm_active = False
        if not src:
            return
        try:
            src_abs = os.path.abspath(src)
            wp_abs = os.path.abspath(self.resolve_wallpaper_path())
            if src_abs == wp_abs:
                self.wallpaper = DEFAULT_WALLPAPER
                self.wallpaper_img = self.load_wallpaper(self.wallpaper)
                self.save_pref()
        except Exception:
            pass
        moved = self.delete_photo_to_trash(src)
        if moved:
            self.photo_files = self.load_photo_files()
            self.photo_zoom = 1.0
            self.photo_zoom_anim_active = False
            self.photo_fingers.clear()
            self.update_photo_pinch_state()
            self.photo_thumb_cache.clear()
            self.photo_view_cache.clear()
            self.photo_meta_time_cache.clear()
            self.photo_info_cache.clear()
            self.text_lines_cache.clear()
            remain = self.filtered_photo_files()
            if remain:
                self.photo_index = int(clamp(self.photo_index, 0, len(remain) - 1))
            else:
                self.photo_index = 0
                self.photo_view = "GRID"
            self.toast(self.tr("photo.toast.deleted", default="휴지통으로 이동했습니다"))
        else:
            self.toast(self.tr("photo.toast.delete_failed", default="삭제에 실패했습니다"))

    def copy_photo_action(self, path):
        copied = False
        try:
            proc = subprocess.run(
                ["pbcopy"],
                input=path,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=0.4,
            )
            copied = (proc.returncode == 0)
        except Exception:
            copied = False
        if copied:
            self.toast(self.tr("photo.toast.shared", default="파일 경로를 클립보드에 복사했습니다"))
        else:
            self.toast(self.tr("photo.toast.share_unavailable", default="공유 기능을 사용할 수 없습니다"))

    def set_photo_as_wallpaper(self, path):
        rel = os.path.relpath(path, BASE_DIR)
        self.wallpaper = rel
        loaded = self.load_wallpaper(self.wallpaper)
        if loaded is None:
            self.wallpaper = DEFAULT_WALLPAPER
            loaded = self.load_wallpaper(self.wallpaper)
        self.wallpaper_img = loaded
        self.save_pref()
        self.toast(self.tr("photo.toast.wallpaper_set", default="배경화면으로 지정했습니다"))

    def filtered_video_files(self):
        items = list(self.video_files)
        q = self.video_search.strip().lower()
        if q:
            items = [p for p in items if q in norm_text(os.path.basename(p)).lower()]
        if self.video_sort == "date":
            items.sort(
                key=lambda p: (-self.video_file_created_at(p), norm_text(os.path.basename(p)).lower())
            )
        else:
            items.sort(key=lambda p: norm_text(os.path.basename(p)).lower())
        return items

    def filtered_text_files(self):
        items = list(self.text_files)
        q = self.text_search.strip().lower()
        if q:
            out = []
            for p in items:
                meta = self.text_meta_for(p)
                hay = (meta.get("name", "") + " " + meta.get("preview", "")).lower()
                if q in hay:
                    out.append(p)
            items = out
        if self.text_sort == "date":
            items.sort(
                key=lambda p: (-self.text_file_created_at(p), norm_text(os.path.basename(p)).lower())
            )
        else:
            items.sort(key=lambda p: norm_text(os.path.basename(p)).lower())
        return items

    def text_reader_rect(self):
        return pygame.Rect(8, STATUS_H + 42, self.w - 16, self.h - STATUS_H - 92)

    def text_body_font(self):
        size = int(clamp(round(13 * (self.text_font_percent / 100.0)), 10, 42))
        cached = self.text_font_cache.get(size)
        if cached:
            return cached
        if self.font_path:
            f = pygame.font.Font(self.font_path, size)
        else:
            f = pygame.font.SysFont(None, size)
        self.text_font_cache[size] = f
        return f

    def text_reader_control_rects(self, reader_rect):
        btn_w = 26
        btn_h = 24
        gap = 6
        pct_w = 56
        y = reader_rect.bottom + 8
        plus = pygame.Rect(reader_rect.right - 8 - btn_w, y, btn_w, btn_h)
        pct = pygame.Rect(plus.x - gap - pct_w, y, pct_w, btn_h)
        minus = pygame.Rect(pct.x - gap - btn_w, y, btn_w, btn_h)
        return {"minus": minus, "pct": pct, "plus": plus}

    def text_reader_body_rect(self):
        rect = self.text_reader_rect()
        return pygame.Rect(rect.x + 8, rect.y + 8, rect.w - 16, rect.h - 16)

    def text_reader_row_h(self):
        return max(18, self.text_body_font().get_linesize() + 2)

    def text_reader_lines(self):
        files = self.filtered_text_files()
        if not files:
            return []
        self.text_index = int(clamp(self.text_index, 0, len(files) - 1))
        path = files[self.text_index]
        font = self.text_body_font()
        body_rect = self.text_reader_body_rect()
        cache_key = (path, int(body_rect.w), int(self.text_font_percent))
        cached = self.text_lines_cache.get(cache_key)
        if cached is not None:
            return cached
        raw = self.text_content_for(path).replace("\r\n", "\n").replace("\r", "\n")
        src_lines = raw.split("\n")
        max_w = max(20, body_rect.w - 2)
        out = []
        for ln in src_lines:
            if ln == "":
                out.append(("", 0))
                continue
            core = ln.lstrip(" \t")
            lead = len(ln) - len(core)
            indent_px = min(36, 8 + lead * 4) if lead > 0 else 0
            if core == "":
                out.append(("", indent_px))
                continue
            cur = ""
            wrap_w = max(20, max_w - indent_px)
            for ch in core:
                test = cur + ch
                if cur and font.size(test)[0] > wrap_w:
                    out.append((cur, indent_px))
                    cur = ch
                else:
                    cur = test
            out.append((cur, indent_px))
        self.text_lines_cache[cache_key] = out
        return out

    def filtered_photo_files(self):
        items = list(self.photo_files)
        items.sort(
            key=lambda p: (
                -(
                    self.photo_meta_taken_at(p)
                    if self.photo_meta_taken_at(p) > 0.0
                    else self.photo_file_created_at(p)
                ),
                norm_text(os.path.basename(p)).lower(),
            )
        )
        return items

    def photo_grid_rect(self):
        return pygame.Rect(8, STATUS_H + 42, self.w - 16, self.h - STATUS_H - 50)

    def photo_viewer_rect(self):
        return pygame.Rect(0, 0, self.w, self.h)

    def photo_viewer_ui_rects(self):
        top_h = STATUS_H
        bottom_h = 48
        top_bar = pygame.Rect(0, 0, self.w, top_h)
        bottom_bar = pygame.Rect(0, self.h - bottom_h, self.w, bottom_h)
        back = pygame.Rect(6, 4, 68, 28)
        btn = 30
        btn_y = self.h - bottom_h + (bottom_h - btn) // 2
        share = pygame.Rect(10, btn_y, btn, btn)
        delete = pygame.Rect(self.w - 10 - btn, btn_y, btn, btn)
        content_y = top_bar.bottom
        content_h = max(1, bottom_bar.y - content_y)
        content = pygame.Rect(0, content_y, self.w, content_h)
        return {
            "top_bar": top_bar,
            "bottom_bar": bottom_bar,
            "back": back,
            "share": share,
            "delete": delete,
            "content": content,
            "text_x": back.right + 8,
        }

    def photo_ui_set_visible(self, visible):
        target = 1.0 if visible else 0.0
        if abs(self.photo_ui_anim_to - target) < 1e-6 and abs(self.photo_ui_progress - target) < 1e-6:
            self.photo_ui_visible = visible
            return
        self.photo_ui_anim_from = self.photo_ui_progress
        self.photo_ui_anim_to = target
        self.photo_ui_anim_start = pygame.time.get_ticks()
        self.photo_ui_visible = visible

    def photo_ui_touch_rects(self):
        base = self.photo_viewer_ui_rects()
        p = float(clamp(self.photo_ui_progress, 0.0, 1.0))
        top_h = base["top_bar"].h
        bottom_h = base["bottom_bar"].h
        top_y = int(-(1.0 - p) * top_h)
        bottom_y = int(self.h - bottom_h + (1.0 - p) * bottom_h)
        out = {
            "top_bar": pygame.Rect(base["top_bar"].x, top_y, base["top_bar"].w, top_h),
            "bottom_bar": pygame.Rect(base["bottom_bar"].x, bottom_y, base["bottom_bar"].w, bottom_h),
            "back": base["back"].move(0, top_y - base["top_bar"].y),
            "share": base["share"].move(0, bottom_y - base["bottom_bar"].y),
            "delete": base["delete"].move(0, bottom_y - base["bottom_bar"].y),
            "text_x": base["text_x"],
            "text_y": 10 + (top_y - base["top_bar"].y),
        }
        return out

    def update_photo_ui_overlay(self):
        if self.state != "PHOTO" or self.photo_view != "VIEWER":
            self.photo_ui_progress = self.photo_ui_anim_to
            return
        now = pygame.time.get_ticks()
        if abs(self.photo_ui_progress - self.photo_ui_anim_to) > 1e-5:
            t = clamp((now - self.photo_ui_anim_start) / max(1, self.photo_ui_anim_ms), 0.0, 1.0)
            t = t * t * (3.0 - 2.0 * t)
            self.photo_ui_progress = self.photo_ui_anim_from + (self.photo_ui_anim_to - self.photo_ui_anim_from) * t
        else:
            self.photo_ui_progress = self.photo_ui_anim_to

    def start_photo_slide(self, files, to_index, direction):
        if not files:
            return
        cur = int(clamp(self.photo_index, 0, len(files) - 1))
        dst = int(clamp(to_index, 0, len(files) - 1))
        if dst == cur:
            return
        self.photo_slide_from_path = files[cur]
        self.photo_slide_to_path = files[dst]
        self.photo_slide_dir = 1 if direction >= 0 else -1
        self.photo_slide_start = pygame.time.get_ticks()
        self.photo_slide_active = True
        self.photo_index = dst
        self.photo_zoom = 1.0
        self.photo_zoom_anim_active = False

    def photo_zoom_toggle(self):
        target = 1.0 if self.photo_zoom > 1.05 else 2.0
        self.photo_zoom_anim_from = float(self.photo_zoom)
        self.photo_zoom_anim_to = float(clamp(target, self.photo_zoom_min, self.photo_zoom_max))
        self.photo_zoom_anim_start = pygame.time.get_ticks()
        self.photo_zoom_anim_active = True

    def update_photo_zoom_anim(self):
        if not self.photo_zoom_anim_active:
            return
        t = clamp((pygame.time.get_ticks() - self.photo_zoom_anim_start) / max(1, self.photo_zoom_anim_ms), 0.0, 1.0)
        t = t * t * (3.0 - 2.0 * t)
        self.photo_zoom = self.photo_zoom_anim_from + (self.photo_zoom_anim_to - self.photo_zoom_anim_from) * t
        if t >= 1.0:
            self.photo_zoom = self.photo_zoom_anim_to
            self.photo_zoom_anim_active = False

    def photo_touch_pos_from_finger(self, fx, fy):
        return (int(clamp(fx, 0.0, 1.0) * self.w), int(clamp(fy, 0.0, 1.0) * self.h))

    def update_photo_pinch_state(self):
        if len(self.photo_fingers) < 2:
            self.photo_pinch_ids = []
            self.photo_pinch_start_dist = 0.0
            self.photo_pinch_start_zoom = self.photo_zoom
            return
        ids = list(self.photo_fingers.keys())[:2]
        p1 = self.photo_fingers.get(ids[0], (0.0, 0.0))
        p2 = self.photo_fingers.get(ids[1], (0.0, 0.0))
        dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
        if not self.photo_pinch_ids:
            self.photo_pinch_ids = ids
            self.photo_pinch_start_dist = max(1e-6, dist)
            self.photo_pinch_start_zoom = self.photo_zoom
            return
        if set(self.photo_pinch_ids) != set(ids):
            self.photo_pinch_ids = ids
            self.photo_pinch_start_dist = max(1e-6, dist)
            self.photo_pinch_start_zoom = self.photo_zoom
            return
        ratio = dist / max(1e-6, self.photo_pinch_start_dist)
        self.photo_zoom = float(clamp(self.photo_pinch_start_zoom * ratio, self.photo_zoom_min, self.photo_zoom_max))
        self.photo_zoom_anim_active = False

    def photo_scroll_info(self):
        rect = self.photo_grid_rect()
        gap = 4
        cell = max(24, (rect.w - gap * (PHOTO_COLS - 1)) // PHOTO_COLS)
        row_h = cell + gap
        total = len(self.filtered_photo_files())
        rows = (total + PHOTO_COLS - 1) // PHOTO_COLS
        return rect, rows, row_h

    def photo_thumb_for(self, path, size):
        key = (path, int(size))
        cached = self.photo_thumb_cache.get(key)
        if cached:
            return cached
        try:
            img = self.oriented_photo_surface(path)
            iw, ih = img.get_size()
            if iw <= 0 or ih <= 0:
                raise ValueError("invalid image size")
            scale = max(size / iw, size / ih)
            nw = max(1, int(iw * scale))
            nh = max(1, int(ih * scale))
            sc = pygame.transform.smoothscale(img, (nw, nh))
            x = max(0, (nw - size) // 2)
            y = max(0, (nh - size) // 2)
            out = sc.subsurface((x, y, size, size)).copy()
        except Exception:
            out = pygame.Surface((size, size))
            out.fill((45, 48, 56))
        self.photo_thumb_cache[key] = out
        return out

    def oriented_photo_surface(self, path):
        angle = PHOTO_ROTATION_FIXES.get(os.path.basename(path).lower(), 0)
        if PILImage is not None and PILImageOps is not None:
            with PILImage.open(path) as im:
                im = PILImageOps.exif_transpose(im).convert("RGB")
                mode = im.mode
                data = im.tobytes()
                surf = pygame.image.fromstring(data, im.size, mode).convert()
                if angle:
                    surf = pygame.transform.rotate(surf, angle)
                return surf
        # macOS fallback: sips applies orientation metadata for iPhone photos.
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                tmp_path = tf.name
            proc = subprocess.run(
                ["sips", "-s", "format", "png", path, "--out", tmp_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            if proc.returncode != 0 or (not os.path.isfile(tmp_path)):
                raise RuntimeError("sips failed")
            surf = pygame.image.load(tmp_path).convert()
            if angle:
                surf = pygame.transform.rotate(surf, angle)
            return surf
        finally:
            if tmp_path and os.path.isfile(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def photo_view_surface_for(self, path, target_rect=None):
        rect = target_rect if target_rect is not None else self.photo_viewer_rect()
        key = (path, rect.w, rect.h)
        cached = self.photo_view_cache.get(key)
        if cached:
            return cached
        try:
            img = self.oriented_photo_surface(path)
            iw, ih = img.get_size()
            if iw <= 0 or ih <= 0:
                raise ValueError("invalid image size")
            scale = min(rect.w / iw, rect.h / ih)
            nw = max(1, int(iw * scale))
            nh = max(1, int(ih * scale))
            out = pygame.transform.smoothscale(img, (nw, nh))
        except Exception:
            out = pygame.Surface((rect.w, rect.h))
            out.fill((18, 18, 18))
        self.photo_view_cache[key] = out
        return out

    def stop_video_process(self):
        self.video_decode_running = False
        self.video_audio_started = False
        self.video_audio_start_path = ""
        self.video_audio_start_seek = 0.0
        if self.video_audio_proc and self.video_audio_proc.poll() is None:
            try:
                self.video_audio_proc.terminate()
            except Exception:
                pass
        self.video_audio_proc = None
        if self.video_proc and self.video_proc.poll() is None:
            try:
                self.video_proc.terminate()
            except Exception:
                pass
        if self.video_proc and self.video_proc.stdout:
            try:
                self.video_proc.stdout.close()
            except Exception:
                pass
        self.video_proc = None
        if self.video_decode_thread and self.video_decode_thread.is_alive():
            try:
                self.video_decode_thread.join(timeout=0.2)
            except Exception:
                pass
        self.video_decode_thread = None
        with self.video_frame_lock:
            self.video_latest_frame = None

    # 부팅 화면 진입 전 모든 재생(음악/비디오)을 강제로 중지한다.
    def stop_all_playback(self):
        self.stop_video_process()
        self.video_playing = False
        self.video_pause_pos = 0.0
        self.video_play_base_pos = 0.0
        try:
            if self.mixer_ready:
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.stop_mpv()
        self.music_paused = False
        self.music_started_at = 0
        self.music_pause_started = 0
        self.music_paused_total = 0
        self.video_paused_music = False

    def pause_music_for_video(self):
        self.video_paused_music = False
        if self.music_backend == "mpv":
            if self.music_proc and self.music_proc.poll() is None and not self.music_paused:
                self.stop_mpv()
                self.music_paused = True
                self.video_paused_music = True
            return
        if self.mixer_ready and pygame.mixer.music.get_busy() and not self.music_paused:
            pygame.mixer.music.pause()
            self.music_paused = True
            self.music_pause_started = pygame.time.get_ticks()
            self.video_paused_music = True

    def resume_music_after_video(self):
        if not self.video_paused_music:
            return
        self.video_paused_music = False
        if self.music_backend == "mpv":
            if self.music_paused:
                self.play_track_mpv(self.music_index)
                self.music_paused = False
            return
        if self.music_paused:
            if self.mixer_ready:
                pygame.mixer.music.unpause()
                self.music_paused = False
                if self.music_pause_started:
                    self.music_paused_total += pygame.time.get_ticks() - self.music_pause_started
                    self.music_pause_started = 0
            elif self.music_files:
                self.play_track(self.music_index, push_history=False)

    def video_decode_worker(self, proc, frame_bytes):
        t0 = time.perf_counter()
        frame_idx = 0
        while self.video_decode_running and proc and proc.poll() is None and proc.stdout:
            try:
                data = proc.stdout.read(frame_bytes)
            except Exception:
                break
            if not data or len(data) < frame_bytes:
                break
            frame_idx += 1
            # Pace decoded frames to realtime based on target FPS.
            target_t = t0 + (frame_idx / max(1.0, float(self.video_fps)))
            now_t = time.perf_counter()
            if target_t > now_t:
                time.sleep(target_t - now_t)
            with self.video_frame_lock:
                self.video_latest_frame = data
                self.video_latest_frame_id += 1
        self.video_decode_running = False

    def start_video_audio(self, path, seek=0.0):
        if not self.ffplay_bin:
            return False
        if self.video_audio_proc and self.video_audio_proc.poll() is None:
            try:
                self.video_audio_proc.terminate()
            except Exception:
                pass
        self.video_audio_proc = None
        cmd = [self.ffplay_bin, "-nodisp", "-loglevel", "quiet", "-autoexit", "-volume", str(int(self.music_volume * 100))]
        if seek > 0.05:
            cmd += ["-ss", f"{seek:.3f}"]
        cmd += [path]
        try:
            self.video_audio_proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            self.video_audio_proc = None
            return False

    def start_video_decode(self, path, seek=0.0):
        if not self.ffmpeg_bin:
            return False
        layout = self.video_player_rects()
        base_w, base_h = layout["art"].w, layout["art"].h
        if self.video_rotation in (90, 270):
            # Decode with swapped axes so the rotated frame matches display bounds.
            w, h = base_h, base_w
        else:
            w, h = base_w, base_h
        self.stop_video_process()
        cmd = [self.ffmpeg_bin, "-hide_banner", "-loglevel", "error"]
        if seek > 0.05:
            cmd += ["-ss", f"{seek:.3f}"]
        cmd += [
            "-i",
            path,
            "-vf",
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,fps=30",
            "-an",
            "-sn",
            "-pix_fmt",
            "rgb24",
            "-f",
            "rawvideo",
            "-",
        ]
        try:
            self.video_proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=frame_bytes_for_pipe if (frame_bytes_for_pipe := (w * h * 3)) > 0 else 0,
            )
            self.video_frame_w = w
            self.video_frame_h = h
            self.video_frame_bytes = w * h * 3
            with self.video_frame_lock:
                self.video_latest_frame = None
            self.video_latest_frame_id = 0
            self.video_rendered_frame_id = -1
            self.video_decode_running = True
            self.video_decode_thread = threading.Thread(
                target=self.video_decode_worker,
                args=(self.video_proc, self.video_frame_bytes),
                daemon=True,
            )
            self.video_decode_thread.start()
            self.video_fps = 30.0
            self.video_playing = True
            self.video_play_base_pos = max(0.0, float(seek))
            self.video_pause_pos = self.video_play_base_pos
            self.video_play_started_ms = 0
            self.video_path = path
            self.video_audio_started = False
            self.video_audio_start_path = path
            self.video_audio_start_seek = self.video_play_base_pos
            return True
        except Exception:
            self.video_proc = None
            self.video_playing = False
            return False

    def current_video_meta(self):
        filtered = self.filtered_video_files()
        if not filtered:
            return None, None
        self.video_index = int(clamp(self.video_index, 0, len(filtered) - 1))
        path = filtered[self.video_index]
        return path, self.video_meta_for(path)

    def current_video_pos(self):
        if not self.video_play_started_ms:
            return self.video_play_base_pos if self.video_playing else self.video_pause_pos
        if self.video_playing:
            elapsed = max(0.0, (pygame.time.get_ticks() - self.video_play_started_ms) / 1000.0)
            pos = self.video_play_base_pos + elapsed
        else:
            pos = self.video_pause_pos
        _path, meta = self.current_video_meta()
        if meta:
            length = float(meta.get("length", 0.0))
            if length > 0.0:
                pos = clamp(pos, 0.0, length)
        return pos

    def rotated_video_surface(self, surf):
        if surf is None:
            return None
        if self.video_rotation == 90:
            return pygame.transform.rotate(surf, 90)
        if self.video_rotation == 180:
            return pygame.transform.rotate(surf, 180)
        if self.video_rotation == 270:
            return pygame.transform.rotate(surf, -90)
        return surf

    def pause_video_decode(self):
        self.video_pause_pos = self.current_video_pos()
        self.stop_video_process()
        self.video_playing = False

    def resume_video_decode(self):
        path, _meta = self.current_video_meta()
        if not path:
            return False
        ok = self.start_video_decode(path, seek=self.video_pause_pos)
        if not ok:
            self.toast(self.tr("video.toast.no_backend", default="비디오 플레이어를 찾을 수 없습니다"), 1500)
        return ok

    def update_video_decode(self):
        if self.state != "VIDEO" or self.video_view != "PLAYER" or not self.video_playing or not self.video_proc:
            return
        if self.video_proc.poll() is not None:
            self.video_playing = False
            self.video_pause_pos = self.current_video_pos()
            self.stop_video_process()
            return
        if self.video_frame_bytes <= 0:
            return
        if self.video_rendered_frame_id == self.video_latest_frame_id:
            return
        with self.video_frame_lock:
            frame = self.video_latest_frame
            fid = self.video_latest_frame_id
        if not frame:
            return
        try:
            surf = pygame.image.frombuffer(frame, (self.video_frame_w, self.video_frame_h), "RGB")
            self.video_frame_surface = surf.copy()
            self.video_rendered_frame_id = fid
            if not self.video_audio_started:
                self.video_audio_started = True
                self.video_play_started_ms = pygame.time.get_ticks()
                self.start_video_audio(self.video_audio_start_path, seek=self.video_audio_start_seek)
        except Exception:
            return

    def play_video_at(self, idx, via_prev=False):
        filtered = self.filtered_video_files()
        if not filtered:
            return
        self.pause_music_for_video()
        idx = int(clamp(idx, 0, len(filtered) - 1))
        self.video_index = idx
        self.video_view = "PLAYER"
        path = filtered[idx]
        self.video_frame_surface = None
        self.video_pause_pos = 0.0
        self.video_prev_chain_active = bool(via_prev)
        self.video_ui_progress = 1.0
        self.video_ui_anim_from = 1.0
        self.video_ui_anim_to = 1.0
        self.video_ui_visible = True
        self.video_ui_last_interaction = pygame.time.get_ticks()
        ok = self.start_video_decode(path, seek=0.0)
        if not ok:
            self.toast(self.tr("video.toast.no_backend", default="비디오 플레이어를 찾을 수 없습니다"), 1500)

    def restart_current_video(self):
        filtered = self.filtered_video_files()
        if not filtered:
            return
        self.video_prev_chain_active = False
        self.play_video_at(self.video_index if self.video_index >= 0 else 0, via_prev=False)

    def prev_video_track(self):
        filtered = self.filtered_video_files()
        if not filtered:
            return
        prev_idx = (self.video_index - 1) % len(filtered)
        self.play_video_at(prev_idx, via_prev=True)

    def video_player_rects(self):
        art = pygame.Rect(0, 0, self.w, self.h)
        if self.video_rotation in (90, 270):
            flip = self.video_rotation == 270
            top_w = 48
            bottom_w = 64
            top_x = 0 if not flip else self.w - top_w
            bot_x = self.w - bottom_w if not flip else 0
            top_bar = pygame.Rect(top_x, 0, top_w, self.h)
            bottom_bar = pygame.Rect(bot_x, 0, bottom_w, self.h)
            portrait_y = 10 if flip else (self.h - 38)
            portrait = pygame.Rect(top_bar.x + 5, portrait_y, top_w - 10, 28)
            title_x = top_bar.x + 8
            vol_h = max(72, int(self.h * 0.33))
            vol_y = (self.h - vol_h - 48) if flip else 56
            vol = pygame.Rect(top_bar.x + (top_w - 22) // 2, vol_y, 22, vol_h)
            btn = 34
            time_pad = 28
            if not flip:
                # Top bar on the left: progress upper, controls lower with extra spacing.
                controls_h = btn * 3 + 20
                controls_top = max(18, self.h - controls_h - 24)
                progress_top = 48
                progress_bottom = max(progress_top + 40, controls_top - 52)
                progress = pygame.Rect(
                    bottom_bar.x + (bottom_w - 6) // 2,
                    progress_top,
                    6,
                    max(40, progress_bottom - progress_top),
                )
                prev = pygame.Rect(bottom_bar.x + (bottom_w - btn) // 2, controls_top, btn, btn)
                play = pygame.Rect(prev.x, prev.bottom + 10, btn, btn)
                next_r = pygame.Rect(prev.x, play.bottom + 10, btn, btn)
                time_y = progress.y - time_pad
                time_y2 = progress.bottom + time_pad
            else:
                # Top bar on the right: controls upper, progress lower with clear gaps.
                prev = pygame.Rect(bottom_bar.x + (bottom_w - btn) // 2, 18, btn, btn)
                play = pygame.Rect(prev.x, prev.bottom + 10, btn, btn)
                next_r = pygame.Rect(prev.x, play.bottom + 10, btn, btn)
                progress_top = next_r.bottom + 42
                progress_bottom = max(progress_top + 40, self.h - 50)
                progress = pygame.Rect(
                    bottom_bar.x + (bottom_w - 6) // 2,
                    progress_top,
                    6,
                    max(40, progress_bottom - progress_top),
                )
                time_y = progress.y - time_pad
                time_y2 = progress.bottom + time_pad
            return {
                "mode": "landscape",
                "flip": flip,
                "top_h": self.h,
                "bottom_h": self.h,
                "top_side_w": top_w,
                "bottom_side_w": bottom_w,
                "art": art,
                "top_bar": top_bar,
                "bottom_bar": bottom_bar,
                "portrait": portrait,
                "title_x": title_x,
                "title_y": 42,
                "volume": vol,
                "progress": progress,
                "time_y": time_y,
                "time_y2": time_y2,
                "prev": prev,
                "play": play,
                "next": next_r,
            }

        title_y = 10
        progress = pygame.Rect(14, self.h - 124, self.w - 28, 6)
        time_y = progress.y + 10
        btn_y = self.h - 92
        bw = 78
        gap = 10
        total = bw * 3 + gap * 2
        x0 = (self.w - total) // 2
        row2_y = self.h - 44
        rot_size = 30
        vol_w = self.w - 120
        vol_x = (self.w - vol_w) // 2
        return {
            "mode": "portrait",
            "top_h": STATUS_H,
            "bottom_h": 140,
            "title_y": title_y,
            "art": art,
            "progress": progress,
            "time_y": time_y,
            "prev": pygame.Rect(x0, btn_y, bw, 34),
            "play": pygame.Rect(x0 + bw + gap, btn_y, bw, 34),
            "next": pygame.Rect(x0 + (bw + gap) * 2, btn_y, bw, 34),
            "rot_left": pygame.Rect(14, row2_y, rot_size, rot_size),
            "volume": pygame.Rect(vol_x, row2_y + 4, vol_w, 22),
            "rot_right": pygame.Rect(self.w - 14 - rot_size, row2_y, rot_size, rot_size),
            "back": self.back_button_rect(),
            "title_x": 82,
        }

    def video_ui_set_visible(self, visible, reset_timer=False):
        target = 1.0 if visible else 0.0
        if abs(self.video_ui_anim_to - target) < 1e-6 and abs(self.video_ui_progress - target) < 1e-6:
            if reset_timer and visible:
                self.video_ui_last_interaction = pygame.time.get_ticks()
            self.video_ui_visible = visible
            return
        self.video_ui_anim_from = self.video_ui_progress
        self.video_ui_anim_to = target
        self.video_ui_anim_start = pygame.time.get_ticks()
        self.video_ui_visible = visible
        if reset_timer and visible:
            self.video_ui_last_interaction = self.video_ui_anim_start

    def video_ui_touch_rects(self):
        p = float(clamp(self.video_ui_progress, 0.0, 1.0))
        base = self.video_player_rects()
        if base.get("mode") == "landscape":
            top_w = int(base.get("top_side_w", base["top_bar"].w))
            bottom_w = int(base.get("bottom_side_w", base["bottom_bar"].w))
            flip = bool(base.get("flip", False))
            if not flip:
                top_x = int((0 - top_w) + top_w * p)
                bottom_x = int((self.w - bottom_w) + bottom_w * (1.0 - p))
            else:
                top_x = int((self.w - top_w) + top_w * (1.0 - p))
                bottom_x = int((0 - bottom_w) + bottom_w * p)
            out = {
                "top_bar": base["top_bar"].move(top_x - base["top_bar"].x, 0),
                "bottom_bar": base["bottom_bar"].move(bottom_x - base["bottom_bar"].x, 0),
                "mode": "landscape",
                "flip": flip,
            }
            for key in ("portrait", "volume"):
                if key in base:
                    out[key] = base[key].move(top_x - base["top_bar"].x, 0)
            for key in ("prev", "play", "next", "progress"):
                if key in base:
                    out[key] = base[key].move(bottom_x - base["bottom_bar"].x, 0)
            out["title_x"] = base["title_x"] + (top_x - base["top_bar"].x)
            out["title_y"] = base["title_y"]
            out["time_y"] = base["time_y"]
            out["time_y2"] = base.get("time_y2", base["time_y"] + 20)
            return out

        top_h = int(base.get("top_h", STATUS_H))
        bottom_h = int(base.get("bottom_h", 140))
        top_y = int(-(1.0 - p) * top_h)
        bottom_y = int(self.h - bottom_h + (1.0 - p) * bottom_h)
        out = {}
        for key in ("progress", "prev", "play", "next", "rot_left", "volume", "rot_right"):
            if key in base:
                r = base[key].copy()
                if key in ("progress", "prev", "play", "next", "rot_left", "rot_right", "volume"):
                    out[key] = r.move(0, bottom_y - (self.h - bottom_h))
                else:
                    out[key] = r.move(0, top_y)
        out["top_bar"] = pygame.Rect(0, top_y, self.w, top_h)
        out["bottom_bar"] = pygame.Rect(0, bottom_y, self.w, bottom_h)
        if "back" in base:
            out["back"] = base["back"].move(0, top_y)
        if "portrait" in base:
            out["portrait"] = base["portrait"].move(0, top_y)
        out["title_x"] = base.get("title_x", 82)
        out["title_y"] = base["title_y"] + top_y
        out["time_y"] = base["time_y"] + (bottom_y - (self.h - bottom_h))
        out["mode"] = base.get("mode", "portrait")
        return out

    def update_video_ui_overlay(self):
        now = pygame.time.get_ticks()
        if abs(self.video_ui_progress - self.video_ui_anim_to) > 1e-5:
            t = clamp((now - self.video_ui_anim_start) / max(1, self.video_ui_anim_ms), 0.0, 1.0)
            t = t * t * (3.0 - 2.0 * t)
            self.video_ui_progress = self.video_ui_anim_from + (self.video_ui_anim_to - self.video_ui_anim_from) * t
        else:
            self.video_ui_progress = self.video_ui_anim_to

        if self.state == "VIDEO" and self.video_view == "PLAYER":
            if self.video_ui_visible and (now - self.video_ui_last_interaction >= self.video_ui_auto_hide_ms):
                self.video_ui_set_visible(False, reset_timer=False)

    def video_volume_track_rect(self, volume_rect):
        if volume_rect.h > volume_rect.w:
            return pygame.Rect(volume_rect.x + 2, volume_rect.y + 2, volume_rect.w - 4, volume_rect.h - 4)
        return pygame.Rect(volume_rect.x + 2, volume_rect.y + 2, volume_rect.w - 4, volume_rect.h - 4)

    def video_volume_ratio_at(self, volume_rect, pos):
        track = self.video_volume_track_rect(volume_rect)
        if track.h > track.w:
            if self.video_rotation == 270:
                return clamp((pos[1] - track.y) / max(1, track.h), 0.0, 1.0)
            return clamp((track.bottom - pos[1]) / max(1, track.h), 0.0, 1.0)
        return clamp((pos[0] - track.x) / max(1, track.w), 0.0, 1.0)

    def video_progress_ratio_at(self, progress_rect, pos):
        if progress_rect.h > progress_rect.w:
            if self.video_rotation == 270:
                return clamp((pos[1] - progress_rect.y) / max(1, progress_rect.h), 0.0, 1.0)
            return clamp((progress_rect.bottom - pos[1]) / max(1, progress_rect.h), 0.0, 1.0)
        return clamp((pos[0] - progress_rect.x) / max(1, progress_rect.w), 0.0, 1.0)

    def sync_video_audio_volume(self, force=False):
        if not self.video_playing:
            return
        now = pygame.time.get_ticks()
        if not force and (now - self.video_volume_sync_ms) < 160:
            return
        path, _meta = self.current_video_meta()
        if not path:
            return
        self.video_volume_sync_ms = now
        self.start_video_audio(path, seek=self.current_video_pos())

    def set_list_scroll(self, value, snap=False):
        self.list_scroll_target = float(max(0.0, value))
        if snap:
            self.list_scroll = self.list_scroll_target
        # Keep fling velocity while finger-dragging; clear only for direct programmatic jumps.
        if not self.list_touch_drag:
            self.list_scroll_inertia_active = False
            self.list_scroll_velocity = 0.0

    def list_scroll_index(self):
        return int(round(self.list_scroll_target))

    def visible_rows(self, rect, row_h):
        return max(1, int(math.ceil(rect.h / max(1, row_h))))

    def scroll_page_rows(self, rect, row_h):
        return max(1, rect.h // max(1, row_h))

    def begin_list_touch_drag(self, pos):
        self.list_touch_drag = True
        self.list_touch_start_y = pos[1]
        self.list_touch_start_scroll = self.list_scroll
        self.list_touch_last_y = float(pos[1])
        self.list_touch_smooth_y = float(pos[1])
        self.list_touch_last_ms = pygame.time.get_ticks()
        self.list_scroll_inertia_active = False
        self.list_scroll_velocity = 0.0

    def update_list_scroll_anim(self):
        now_ms = pygame.time.get_ticks()
        dt = clamp((now_ms - self.list_scroll_anim_last_ms) / 1000.0, 1.0 / 240.0, 0.06)
        self.list_scroll_anim_last_ms = now_ms
        if self.state == "VIDEO" and self.video_view == "LIST":
            rect, total, row_h = self.video_scroll_info()
        elif self.state == "TEXT":
            if self.text_view == "LIST":
                rect, total, row_h = self.text_scroll_info()
            elif self.text_view == "READER":
                rect = self.text_reader_body_rect()
                total = max(1, len(self.text_reader_lines()))
                row_h = self.text_reader_row_h()
            else:
                rect, total, row_h = None, 0, 24
        elif self.state == "PHOTO":
            rect, total, row_h = self.photo_scroll_info()
        elif self.state == "FILES" and self.files_view in ("ROOT", "LIST"):
            rect, total, row_h = self.files_scroll_info()
        elif self.state == "MUSIC" and self.music_view in ("LIST", "QUEUE", "ALBUMS", "ARTISTS", "ARTIST_ALBUMS", "GENRES"):
            rect, total, row_h = self.music_scroll_info()
        elif self.state == "SETTINGS_INFO" and not self.settings_info_name_popup_active:
            rect, total, row_h = self.settings_info_scroll_info()
        else:
            self.list_scroll = 0.0 if self.list_scroll < 0 else self.list_scroll
            self.list_scroll_target = 0.0 if self.list_scroll_target < 0 else self.list_scroll_target
            self.list_scroll_inertia_active = False
            self.list_scroll_velocity = 0.0
            return
        if not rect:
            return
        max_rows = self.scroll_page_rows(rect, row_h)
        max_scroll = float(max(0, total - max_rows))
        if self.list_scroll_inertia_active and not self.list_touch_drag:
            self.list_scroll_target += self.list_scroll_velocity * dt
            decay = pow(0.06, dt)
            self.list_scroll_velocity *= decay
            if self.list_scroll_target < 0.0:
                self.list_scroll_target = 0.0
                self.list_scroll_velocity *= 0.35
            elif self.list_scroll_target > max_scroll:
                self.list_scroll_target = max_scroll
                self.list_scroll_velocity *= 0.35
            if abs(self.list_scroll_velocity) < 0.03:
                self.list_scroll_inertia_active = False
                self.list_scroll_velocity = 0.0
        self.list_scroll_target = float(clamp(self.list_scroll_target, 0.0, max_scroll))
        self.list_scroll = float(clamp(self.list_scroll, 0.0, max_scroll))
        if self.list_touch_drag:
            self.list_scroll = self.list_scroll_target
            return
        blend = 1.0 - pow(0.72, dt * 60.0)
        self.list_scroll += (self.list_scroll_target - self.list_scroll) * blend
        if abs(self.list_scroll_target - self.list_scroll) < 0.01:
            self.list_scroll = self.list_scroll_target

    def set_screen_off(self, off):
        target = 1.0 if off else 0.0
        self.screen_off = bool(off)
        if abs(self.screen_off_anim_to - target) < 1e-6 and abs(self.screen_off_progress - target) < 1e-6:
            return
        self.screen_off_anim_from = float(self.screen_off_progress)
        self.screen_off_anim_to = float(target)
        self.screen_off_anim_start = pygame.time.get_ticks()

    def update_screen_off_anim(self):
        if abs(self.screen_off_progress - self.screen_off_anim_to) < 1e-6:
            self.screen_off_progress = self.screen_off_anim_to
            return
        t = clamp((pygame.time.get_ticks() - self.screen_off_anim_start) / max(1, self.screen_off_anim_ms), 0.0, 1.0)
        t = t * t * (3.0 - 2.0 * t)
        self.screen_off_progress = self.screen_off_anim_from + (self.screen_off_anim_to - self.screen_off_anim_from) * t
        if t >= 1.0:
            self.screen_off_progress = self.screen_off_anim_to

    # 부팅 시퀀스 시작: 전환 애니메이션 없이 즉시 부팅 화면으로 전환
    def start_boot_sequence(self):
        self.stop_all_playback()
        self.screen_off = False
        self.screen_off_progress = 0.0
        self.screen_off_anim_from = 0.0
        self.screen_off_anim_to = 0.0
        self.screen_off_anim_start = pygame.time.get_ticks()
        self.lock_unlock_fade_active = False
        self.lock_unlock_fade_alpha = 0.0
        self.lock_unlock_fade_start = 0
        self.boot_active = True
        self.boot_start = pygame.time.get_ticks()
        self.pending_back_transition = False
        self.transition_active = False
        self.transition_from = None
        self.power_confirm_active = False
        self.esc_hold_started = 0
        self.esc_hold_handled = False
        self.state = "HOME"

    # 재부팅 완료 후 디스크 기준으로 런타임 리소스를 다시 읽어온다.
    def reload_runtime_after_boot(self):
        self.cfg = load_config()
        self.lang = normalize_language(self.cfg.get("language", self.lang))
        self.i18n = load_language_pack(self.lang)
        self.theme = self.cfg.get("theme", self.theme)
        if self.theme == "classic":
            self.theme = "light"
        if self.theme not in THEMES:
            self.theme = "light"
        self.brightness = int(clamp(self.cfg.get("brightness", self.brightness), 40, 100))
        self.time_24h = bool(self.cfg.get("time_24h", self.time_24h))
        self.device_name = norm_text(self.cfg.get("device_name", self.device_name))
        self.serial_number = norm_text(str(self.cfg.get("serial_number", self.serial_number)))
        self.bt_address = norm_text(str(self.cfg.get("bt_address", self.bt_address)))
        self.wallpaper = str(self.cfg.get("wallpaper", self.wallpaper))
        self.accent_key = str(self.cfg.get("accent_color", self.accent_key))
        if self.accent_key not in ACCENT_PRESETS:
            self.accent_key = "blue"
        self.home_show_power = bool(self.cfg.get("home_show_power", self.home_show_power))
        self.bt_enabled = bool(self.cfg.get("bt_enabled", self.bt_enabled))
        self.fake_battery_level = int(clamp(self.cfg.get("battery_level", self.fake_battery_level), 0, 100))
        self.fake_battery_health = int(clamp(self.cfg.get("battery_health", self.fake_battery_health), 1, 100))
        self.fake_battery_saver = bool(self.cfg.get("battery_saver", self.fake_battery_saver))
        self.fake_battery_charging = bool(self.cfg.get("battery_charging", self.fake_battery_charging))

        self.icon_map = self.load_icons()
        self.now_icons = self.load_now_icons()
        self.video_ui_icons = self.load_video_ui_icons()
        self.photo_ui_icons = self.load_photo_ui_icons()
        self.files_ui_icons = self.load_files_ui_icons()
        self.lock_home_icon = self.load_lock_home_icon()
        self.settings_footer_icon = self.load_settings_footer_icon()
        self.settings_full_icons = self.load_settings_full_icons()
        self.settings_full_icons_24 = self.prepare_settings_full_icons(24)

        self.wallpaper_img = self.load_wallpaper(self.wallpaper)
        self.ensure_wallpaper_valid()
        self.music_files = self.load_music_files()
        self.video_files = self.load_video_files()
        self.photo_files = self.load_photo_files()
        self.text_files = self.load_text_files()

        # 파일/메타가 바뀌었을 수 있으므로 관련 캐시를 모두 비운다.
        self.track_meta_cache.clear()
        self.album_art_cache.clear()
        self.video_meta_cache.clear()
        self.video_thumb_cache.clear()
        self.photo_thumb_cache.clear()
        self.photo_view_cache.clear()
        self.photo_meta_time_cache.clear()
        self.photo_info_cache.clear()
        self.wallpaper_thumb_cache.clear()
        self.text_meta_cache.clear()
        self.text_content_cache.clear()
        self.text_thumb_cache.clear()
        self.text_lines_cache.clear()
        self.files_icon_cache.clear()

        last_path = self.cfg.get("music_last_path")
        last_idx = int(self.cfg.get("music_last_index", self.music_index))
        if last_path and last_path in self.music_files:
            self.music_index = self.music_files.index(last_path)
        else:
            self.music_index = int(clamp(last_idx, 0, max(0, len(self.music_files) - 1)))
        self.music_likes = set(self.cfg.get("music_likes", list(self.music_likes)))
        self.refresh_home_pages()

    # 부팅 진행 시간을 갱신하고 완료 시 부팅 상태를 해제한다.
    def update_boot_sequence(self):
        if not self.boot_active:
            return
        elapsed = pygame.time.get_ticks() - self.boot_start
        if elapsed >= (self.boot_black_ms + self.boot_load_ms):
            self.boot_active = False
            self.reload_runtime_after_boot()

    # 부팅 화면 렌더링(블랙 스플래시 -> 로고/진행바)
    def draw_boot_sequence(self):
        elapsed = pygame.time.get_ticks() - self.boot_start
        if elapsed < self.boot_black_ms:
            self.screen.fill((0, 0, 0))
            return
        pal = self.pal()
        if self.theme == "light":
            bg = (255, 255, 255)
            fg = (0, 0, 0)
            track = (216, 220, 228)
        else:
            bg = (0, 0, 0)
            fg = (246, 248, 255)
            track = (72, 80, 96)
        self.screen.fill(bg)
        bw = min(220, self.w - 56)
        target_logo_w = max(80, bw - 4)
        title_font = self.title_font
        for sz in range(76, 23, -2):
            try:
                title_font = pygame.font.Font(self.font_path, sz) if self.font_path else pygame.font.SysFont(None, sz)
            except Exception:
                title_font = self.title_font
            if title_font.size("Roy's PMP")[0] <= target_logo_w:
                break
        title = title_font.render("Roy's PMP", True, fg)
        tx = self.w // 2 - title.get_width() // 2
        ty = self.h // 2 - title.get_height() // 2 - 16
        self.screen.blit(title, (tx, ty))

        progress_t = clamp((elapsed - self.boot_black_ms) / max(1, self.boot_load_ms), 0.0, 1.0)
        bh = 8
        bar = pygame.Rect((self.w - bw) // 2, self.h - 74, bw, bh)
        pygame.draw.rect(self.screen, track, bar, border_radius=4)
        fill_w = int(bw * progress_t)
        if fill_w > 0:
            pygame.draw.rect(self.screen, self.ui_accent(), (bar.x, bar.y, fill_w, bar.h), border_radius=4)

    def draw_scroll_hint(self, rect, total_items, row_h):
        visible = max(1, rect.h // max(1, row_h))
        if total_items <= visible:
            return
        track_w = 4
        if self.state == "PHOTO":
            tx = self.w - track_w - 1
        else:
            tx = rect.right - track_w - 3
        ty = rect.y + 4
        th = rect.h - 8
        ratio = clamp(visible / max(1, total_items), 0.08, 1.0)
        thumb_h = max(12, int(th * ratio))
        max_scroll = max(1, total_items - visible)
        scroll = clamp(self.list_scroll, 0.0, max_scroll)
        py = int((scroll / max_scroll) * (th - thumb_h))
        pal = self.pal()
        track_col = self.tone(pal["panel_border"], -15 if self.theme == "light" else 15)
        thumb_col = (110, 110, 118) if self.theme == "light" else (126, 126, 136)
        pygame.draw.rect(self.screen, track_col, (tx, ty, track_w, th), border_radius=3)
        pygame.draw.rect(self.screen, thumb_col, (tx, ty + py, track_w, thumb_h), border_radius=3)

    def current_route_key(self):
        if self.state == "MUSIC":
            return (self.state, self.music_view)
        if self.state == "VIDEO":
            return (self.state, self.video_view)
        if self.state == "TEXT":
            return (self.state, self.text_view)
        if self.state == "PHOTO":
            return (self.state, self.photo_view)
        if self.state == "FILES":
            return (self.state, self.files_view, self.files_source, self.files_path)
        return (self.state,)

    def raw_track_name(self, idx):
        if idx < 0 or idx >= len(self.music_files):
            return ""
        return norm_text(os.path.basename(self.music_files[idx]))

    # 트랙 메타데이터(title/album/artist/album_artist/genre/length) 캐시 조회
    def track_meta_for(self, idx):
        if idx < 0 or idx >= len(self.music_files):
            return {"title": "", "length": 0.0}
        path = self.music_files[idx]
        if path in self.track_meta_cache:
            return self.track_meta_cache[path]
        title = norm_text(os.path.splitext(os.path.basename(path))[0])
        album = norm_text(self.tr("music.album.unknown"))
        artist = norm_text(self.tr("music.artist.unknown"))
        album_artist = ""
        genre = norm_text(self.tr("music.genre.unknown", default="장르 미상"))
        length = 0.0
        try:
            if MutagenFile:
                audio = MutagenFile(path, easy=True)
                if audio:
                    tags = audio.tags
                    if tags and "title" in tags and tags["title"]:
                        title = norm_text(str(tags["title"][0]).strip()) or title
                    if tags and "album" in tags and tags["album"]:
                        album = norm_text(str(tags["album"][0]).strip()) or album
                    if tags and "artist" in tags and tags["artist"]:
                        artist = norm_text(str(tags["artist"][0]).strip()) or artist
                    if tags and "albumartist" in tags and tags["albumartist"]:
                        album_artist = norm_text(str(tags["albumartist"][0]).strip()) or album_artist
                    if tags and "genre" in tags and tags["genre"]:
                        genre = norm_text(str(tags["genre"][0]).strip()) or genre
                    if getattr(audio, "info", None) and getattr(audio.info, "length", None):
                        length = float(audio.info.length)
        except Exception:
            pass
        if length <= 0.0:
            try:
                length = float(pygame.mixer.Sound(path).get_length())
            except Exception:
                length = 0.0
        if not album_artist:
            album_artist = artist
        meta = {
            "title": title,
            "album": album,
            "artist": artist,
            "album_artist": album_artist,
            "genre": genre,
            "length": length,
        }
        self.track_meta_cache[path] = meta
        return meta

    def track_name(self, idx):
        return self.track_meta_for(idx)["title"]

    def track_length_for(self, idx):
        return self.track_meta_for(idx)["length"]

    # 현재 컨텍스트(아티스트/앨범/장르/검색/정렬) 기준 곡 목록 계산
    def filtered_music_indices(self):
        items = list(range(len(self.music_files)))
        q = self.music_search.strip().lower()
        if self.music_ctx_artist:
            items = [i for i in items if self.track_meta_for(i).get("album_artist", "") == self.music_ctx_artist]
        if self.music_ctx_album:
            items = [i for i in items if self.track_meta_for(i).get("album", "") == self.music_ctx_album]
        if self.music_ctx_genre:
            items = [i for i in items if self.track_meta_for(i).get("genre", "") == self.music_ctx_genre]
        if q:
            items = [i for i in items if q in self.track_name(i).lower()]
        if self.music_sort == "album":
            items.sort(key=lambda i: (self.track_meta_for(i).get("album", "").lower(), self.track_name(i).lower()))
        elif self.music_sort == "artist":
            items.sort(
                key=lambda i: (
                    self.track_meta_for(i).get("album_artist", "").lower(),
                    self.track_meta_for(i).get("album", "").lower(),
                    self.track_name(i).lower(),
                )
            )
        else:
            items.sort(key=lambda i: self.track_name(i).lower())
        return items

    # 앨범/아티스트/장르 그룹 목록과 곡 수를 생성한다.
    def group_items(self, kind, artist_filter=None):
        seen = {}
        for i in range(len(self.music_files)):
            meta = self.track_meta_for(i)
            if artist_filter and meta.get("album_artist", "") != artist_filter:
                continue
            if kind == "artist":
                key = meta.get("album_artist", "")
            else:
                key = meta.get(kind, "") if kind in ("album", "artist", "genre") else ""
            if not key:
                if kind == "album":
                    key = self.tr("music.album.unknown")
                elif kind == "artist":
                    key = self.tr("music.artist.unknown")
                else:
                    key = self.tr("music.genre.unknown", default="장르 미상")
            if key not in seen:
                seen[key] = {"count": 0, "first_idx": i}
            seen[key]["count"] += 1
        q = self.music_search.strip().lower()
        rows = []
        for name, data in seen.items():
            if q and q not in name.lower():
                continue
            rows.append((name, data["count"], data["first_idx"]))
        rows.sort(key=lambda x: x[0].lower())
        return rows

    def album_art_for_album(self, album_name, size=22):
        size = int(clamp(size, 16, 512))
        cache_key = (album_name, size)
        if cache_key in self.album_art_cache:
            return self.album_art_cache[cache_key]
        idx = -1
        for i in range(len(self.music_files)):
            if self.track_meta_for(i).get("album", "") == album_name:
                idx = i
                break
        if idx < 0:
            art = self.default_album_art(size)
            self.album_art_cache[cache_key] = art
            return art
        path = self.music_files[idx]
        image_bytes = None
        try:
            if MutagenFile:
                audio = MutagenFile(path)
                if audio:
                    tags = getattr(audio, "tags", None)
                    if tags:
                        if hasattr(tags, "keys"):
                            for k in tags.keys():
                                if str(k).startswith("APIC"):
                                    image_bytes = tags[k].data
                                    break
                        if not image_bytes and "covr" in tags and tags["covr"]:
                            image_bytes = bytes(tags["covr"][0])
                    if not image_bytes and getattr(audio, "pictures", None):
                        if audio.pictures:
                            image_bytes = audio.pictures[0].data
        except Exception:
            image_bytes = None
        surf = None
        if image_bytes:
            try:
                base = pygame.image.load(io.BytesIO(image_bytes)).convert_alpha()
                scaled = pygame.transform.smoothscale(base, (size, size))
                rounded = pygame.Surface((size, size), pygame.SRCALPHA)
                rounded.blit(scaled, (0, 0))
                mask = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, size, size), border_radius=6)
                rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf = rounded
            except Exception:
                surf = None
        if surf is None:
            surf = self.default_album_art(size)
        self.album_art_cache[cache_key] = surf
        return surf

    def album_artist_for_album(self, album_name):
        artists = set()
        for i in range(len(self.music_files)):
            meta = self.track_meta_for(i)
            if meta.get("album", "") == album_name:
                artist = str(meta.get("album_artist", "") or meta.get("artist", "")).strip()
                if artist:
                    artists.add(artist)
        if not artists:
            return self.tr("music.artist.unknown")
        return sorted(artists, key=lambda x: x.lower())[0]

    def default_album_art(self, size):
        size = int(clamp(size, 16, 512))
        cache_key = ("__default__", size)
        if cache_key in self.album_art_cache:
            return self.album_art_cache[cache_key]
        try:
            base = pygame.image.load(DEFAULT_ALBUM_ART).convert_alpha()
            scaled = pygame.transform.smoothscale(base, (size, size))
            rounded = pygame.Surface((size, size), pygame.SRCALPHA)
            rounded.blit(scaled, (0, 0))
            mask = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, size, size), border_radius=8)
            rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.album_art_cache[cache_key] = rounded
            return rounded
        except Exception:
            fallback = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(fallback, (80, 80, 88), (0, 0, size, size), border_radius=8)
            pygame.draw.rect(fallback, (130, 130, 145), (0, 0, size, size), width=1, border_radius=8)
            self.album_art_cache[cache_key] = fallback
            return fallback

    def now_backdrop_surface(self):
        album_name = self.track_meta_for(self.music_index).get("album", "") if self.music_files else ""
        cache_key = (album_name, self.theme, self.w, self.h)
        if cache_key in self.now_backdrop_cache:
            return self.now_backdrop_cache[cache_key]
        base = self.album_art_for_album(album_name, size=max(self.w, self.h))
        if base is None:
            return None
        try:
            iw, ih = base.get_size()
            scale = max(self.w / max(1, iw), self.h / max(1, ih))
            nw = max(1, int(iw * scale))
            nh = max(1, int(ih * scale))
            full = pygame.transform.smoothscale(base, (nw, nh))
            crop = full.subsurface(((nw - self.w) // 2, (nh - self.h) // 2, self.w, self.h)).copy()
            # Fast blur approximation
            blur_small = pygame.transform.smoothscale(crop, (max(1, self.w // 14), max(1, self.h // 14)))
            blurred = pygame.transform.smoothscale(blur_small, (self.w, self.h))
            self.now_backdrop_cache[cache_key] = blurred
            return blurred
        except Exception:
            return None

    def draw_volume_icon(self, rect, color):
        cx = rect.x + 2
        cy = rect.centery
        body = [(cx, cy - 4), (cx + 5, cy - 4), (cx + 10, cy - 8), (cx + 10, cy + 8), (cx + 5, cy + 4), (cx, cy + 4)]
        pygame.draw.polygon(self.screen, color, body)
        pygame.draw.arc(self.screen, color, pygame.Rect(cx + 8, cy - 8, 10, 16), -0.8, 0.8, 2)

    def play_track(self, idx, push_history=True, via_prev=False):
        if not self.music_files:
            return
        idx = idx % len(self.music_files)
        try:
            if push_history and (self.is_music_busy() or self.music_paused):
                self.music_history.append(self.music_index)
            if not self.ensure_mixer():
                raise RuntimeError("mixer not ready")
            pygame.mixer.music.load(self.music_files[idx])
            pygame.mixer.music.play()
            self.stop_mpv()
            self.music_backend = "mixer"
            self.music_index = idx
            self.music_paused = False
            now = pygame.time.get_ticks()
            self.music_started_at = now
            self.music_pause_started = 0
            self.music_paused_total = 0
            self.prev_chain_active = via_prev
            self.remember_play_state()
        except Exception:
            self.play_track_mpv(idx, via_prev=via_prev)

    def restart_current_track(self):
        if not self.music_files:
            return
        self.play_track(self.music_index, push_history=False, via_prev=False)

    def toggle_music(self):
        if not self.music_files:
            return
        if self.music_backend == "mpv":
            if self.music_proc and self.music_proc.poll() is None:
                self.music_pause_started = pygame.time.get_ticks()
                self.stop_mpv()
                self.music_paused = True
            else:
                self.play_track_mpv(self.music_index, start=self.current_track_pos())
                self.music_paused = False
            return
        if not self.mixer_ready:
            self.play_track(self.music_index, push_history=False)
            return
        if pygame.mixer.music.get_busy() and not self.music_paused:
            pygame.mixer.music.pause()
            self.music_paused = True
            self.music_pause_started = pygame.time.get_ticks()
            return
        if self.music_paused:
            pygame.mixer.music.unpause()
            self.music_paused = False
            if self.music_pause_started:
                self.music_paused_total += pygame.time.get_ticks() - self.music_pause_started
                self.music_pause_started = 0
            return
        self.play_track(self.music_index, push_history=False)

    # 현재 큐 소스(전체/앨범/장르/좋아요) 기준 실제 재생 순서를 만든다.
    def play_queue_indices(self):
        if self.queue_source == "album" and self.queue_album:
            items = [i for i in range(len(self.music_files)) if self.track_meta_for(i).get("album", "") == self.queue_album]
            items.sort(key=lambda i: self.track_name(i).lower())
            return items
        if self.queue_source == "genre" and self.queue_genre:
            items = [i for i in range(len(self.music_files)) if self.track_meta_for(i).get("genre", "") == self.queue_genre]
            items.sort(key=lambda i: self.track_name(i).lower())
            return items
        if self.queue_source == "liked":
            items = [i for i in range(len(self.music_files)) if self.music_files[i] in self.music_likes]
            items.sort(key=lambda i: self.track_name(i).lower())
            return items
        items = list(range(len(self.music_files)))
        mode = self.queue_sort if self.queue_sort in ("name", "album", "artist") else "name"
        if mode == "album":
            items.sort(key=lambda i: (self.track_meta_for(i).get("album", "").lower(), self.track_name(i).lower()))
        elif mode == "artist":
            items.sort(
                key=lambda i: (
                    self.track_meta_for(i).get("artist", "").lower(),
                    self.track_meta_for(i).get("album", "").lower(),
                    self.track_name(i).lower(),
                )
            )
        else:
            items.sort(key=lambda i: self.track_name(i).lower())
        return items

    # 화면 컨텍스트(앨범/장르)를 큐 컨텍스트로 반영한다.
    def set_queue_from_current_context(self):
        if self.music_ctx_album:
            self.queue_source = "album"
            self.queue_album = self.music_ctx_album
            self.queue_genre = None
            self.queue_artist = self.music_ctx_artist
            return
        if self.music_ctx_genre:
            self.queue_source = "genre"
            self.queue_genre = self.music_ctx_genre
            self.queue_album = None
            self.queue_artist = None
            return
        self.queue_source = "songs"
        self.queue_album = None
        self.queue_genre = None
        self.queue_artist = None
        self.queue_sort = self.music_sort

    def next_track(self, auto=False):
        queue = self.play_queue_indices()
        if not queue:
            return
        self.prev_chain_active = False
        self.prev_button_last_tap = 0
        if self.repeat_mode == "one":
            self.play_track(self.music_index, push_history=False, via_prev=False)
            return
        if self.shuffle_enabled and len(queue) > 1:
            choices = [i for i in queue if i != self.music_index]
            self.play_track(random.choice(choices), push_history=True, via_prev=False)
            return
        if self.music_index in queue:
            qpos = queue.index(self.music_index)
        else:
            qpos = 0
        if qpos >= len(queue) - 1:
            if self.repeat_mode == "all" or not auto:
                self.play_track(queue[0], push_history=True, via_prev=False)
            else:
                if self.mixer_ready:
                    pygame.mixer.music.stop()
                self.stop_mpv()
                self.music_paused = False
            return
        self.play_track(queue[qpos + 1], push_history=True, via_prev=False)

    def prev_track(self):
        queue = self.play_queue_indices()
        if not queue:
            return
        if self.shuffle_enabled and self.music_history:
            self.play_track(self.music_history.pop(), push_history=False, via_prev=True)
            return
        if self.music_index in queue:
            qpos = queue.index(self.music_index)
        else:
            qpos = 0
        prev_idx = queue[(qpos - 1) % len(queue)]
        self.play_track(prev_idx, push_history=True, via_prev=True)

    def is_music_busy(self):
        if self.music_backend == "mpv":
            return self.music_proc is not None and self.music_proc.poll() is None
        return self.mixer_ready and pygame.mixer.music.get_busy()

    def current_track_len(self):
        if not self.music_files:
            return 0.0
        return self.track_length_for(self.music_index)

    def current_track_pos(self):
        if not self.music_started_at:
            return 0.0
        if self.music_paused and self.music_pause_started:
            ms = self.music_pause_started - self.music_started_at - self.music_paused_total
        else:
            ms = pygame.time.get_ticks() - self.music_started_at - self.music_paused_total
        return max(0.0, ms / 1000.0)

    def clear_seek_hold(self):
        self.seek_hold_kind = None
        self.seek_hold_dir = 0
        self.seek_hold_triggered = False
        self.seek_hold_last_ms = 0
        self.seek_hold_consumed = False

    def begin_seek_hold(self, kind, direction):
        self.seek_hold_kind = kind
        self.seek_hold_dir = -1 if direction < 0 else 1
        self.seek_hold_triggered = False
        self.seek_hold_last_ms = 0
        self.seek_hold_consumed = False

    def seek_music_to(self, target, keep_paused=False):
        if not self.music_files:
            return
        length = self.current_track_len()
        if length <= 0.1:
            return
        target = float(clamp(target, 0.0, max(0.0, length - 0.05)))
        if self.music_backend == "mpv":
            now = pygame.time.get_ticks()
            self.prev_chain_active = False
            self.prev_button_last_tap = 0
            if keep_paused:
                self.stop_mpv()
                self.music_paused = True
                self.music_started_at = now - int(target * 1000)
                self.music_pause_started = now
                self.music_paused_total = 0
            else:
                self.play_track_mpv(self.music_index, start=target)
            return
        if not self.mixer_ready:
            return
        try:
            pygame.mixer.music.play(start=target)
            now = pygame.time.get_ticks()
            self.music_started_at = now - int(target * 1000)
            self.music_paused_total = 0
            self.prev_chain_active = False
            self.prev_button_last_tap = 0
            if keep_paused:
                pygame.mixer.music.pause()
                self.music_paused = True
                self.music_pause_started = now
            else:
                self.music_paused = False
                self.music_pause_started = 0
        except Exception:
            return

    def seek_video_to(self, target):
        filtered = self.filtered_video_files()
        if not filtered:
            return
        _path, meta = self.current_video_meta()
        length = float(meta.get("length", 0.0)) if meta else 0.0
        if length <= 0.1:
            return
        target = float(clamp(target, 0.0, max(0.0, length - 0.05)))
        self.start_video_decode(filtered[self.video_index], seek=target)

    def update_seek_hold(self):
        if not self.touch_down or not self.seek_hold_kind or self.seek_hold_dir == 0:
            return
        now = pygame.time.get_ticks()
        if not self.seek_hold_triggered:
            if now - self.down_time < 320:
                return
            self.seek_hold_triggered = True
            self.seek_hold_consumed = True
            self.seek_hold_last_ms = now
        interval_ms = 120 if self.seek_hold_kind == "music" else 220
        if now - self.seek_hold_last_ms < interval_ms:
            return
        self.seek_hold_last_ms = now
        if self.seek_hold_kind == "music":
            cur = self.current_track_pos()
            self.seek_music_to(cur + (3.2 * self.seek_hold_dir))
        elif self.seek_hold_kind == "video":
            cur = self.current_video_pos()
            self.seek_video_to(cur + (4.5 * self.seek_hold_dir))

    def fmt_time(self, sec):
        total = max(0, int(sec))
        return f"{total // 60:02d}:{total % 60:02d}"

    def draw_select_button(self, rect, text, active):
        pal = self.pal()
        pressed = self.touch_down and rect.collidepoint(pygame.mouse.get_pos()) and not self.list_touch_drag
        r = rect.move(0, 1 if pressed else 0)
        radius = 11
        shadow = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 32), (0, 0, r.w, r.h), border_radius=radius)
        self.screen.blit(shadow, (r.x, r.y + 1))
        if active:
            accent = self.ui_accent()
            bg = self.tone(accent, 120 if self.theme == "light" else -58)
            bd = accent if self.theme == "light" else self.tone(accent, 22)
            txt = (18, 24, 32) if self.theme == "light" else (246, 248, 255)
        else:
            bg = pal["button_bg"]
            bd = pal["button_border"]
            txt = pal["text"]
        if pressed:
            bg = self.tone(bg, -10)
        pygame.draw.rect(self.screen, bg, r, border_radius=radius)
        pygame.draw.rect(self.screen, bd, r, width=1, border_radius=radius)
        text_surf = self.small_font.render(text, True, txt)
        tx = r.centerx - text_surf.get_width() // 2
        ty = r.centery - text_surf.get_height() // 2
        self.screen.blit(text_surf, (tx, ty))

    def vk_active_target(self):
        if self.state in ("SETTINGS", "SETTINGS_FULL", "SETTINGS_INFO") and self.editing_name:
            return ("settings_name", self.device_name, 18)
        if self.state == "MUSIC" and self.music_view in ("LIST", "ALBUMS", "ARTISTS", "ARTIST_ALBUMS", "GENRES") and self.editing_music_search:
            return ("music_search", self.music_search, 40)
        if self.state == "VIDEO" and self.video_view == "LIST" and self.editing_video_search:
            return ("video_search", self.video_search, 40)
        if self.state == "TEXT" and self.text_view == "LIST" and self.editing_text_search:
            return ("text_search", self.text_search, 40)
        if self.state == "FILES" and self.files_view == "LIST" and self.editing_files_search:
            return ("files_search", self.files_search, 40)
        if self.state == "FILES" and self.files_view == "INFO" and self.files_info_rename_active:
            return ("files_rename", self.files_info_rename_text, 64)
        return None

    def vk_set_target_text(self, tid, text):
        if tid == "settings_name":
            self.device_name = text
        elif tid == "music_search":
            self.music_search = text
            self.set_list_scroll(0, snap=True)
        elif tid == "video_search":
            self.video_search = text
            self.set_list_scroll(0, snap=True)
        elif tid == "text_search":
            self.text_search = text
            self.set_list_scroll(0, snap=True)
        elif tid == "files_search":
            self.files_search = text
            self.set_list_scroll(0, snap=True)
        elif tid == "files_rename":
            self.files_info_rename_text = text

    def vk_compose_char(self):
        if not self.vk_h_l:
            return ""
        if not self.vk_h_v:
            return self.vk_h_l
        li = HANGUL_CHOSEONG.find(self.vk_h_l)
        vi = HANGUL_JUNGSEONG.find(self.vk_h_v)
        if li < 0 or vi < 0:
            return self.vk_h_l + self.vk_h_v + (self.vk_h_t or "")
        ti = HANGUL_JONGSEONG.index(self.vk_h_t) if self.vk_h_t in HANGUL_JONGSEONG else 0
        code = 0xAC00 + ((li * 21) + vi) * 28 + ti
        try:
            return chr(code)
        except Exception:
            return self.vk_h_l + self.vk_h_v + (self.vk_h_t or "")

    def vk_render_text(self):
        return self.vk_committed + self.vk_compose_char()

    def vk_sync_target(self):
        tgt = self.vk_active_target()
        if not tgt:
            self.vk_visible = False
            self.vk_target_id = ""
            return
        tid, current, maxlen = tgt
        self.vk_visible = True
        if self.vk_target_id != tid:
            self.vk_target_id = tid
            self.vk_target_max = maxlen
            self.vk_mode = self.vk_lang_pref
            self.vk_shift = False
            self.vk_caps = False
            self.vk_shift_last_tap = 0
            self.vk_committed = str(current)
            self.vk_h_l = ""
            self.vk_h_v = ""
            self.vk_h_t = ""
            self.vk_last_ko_key = ""
            self.vk_last_ko_cycle = 0
            self.vk_last_ko_time = 0
            return
        if str(current) != self.vk_render_text():
            self.vk_committed = str(current)
            self.vk_h_l = ""
            self.vk_h_v = ""
            self.vk_h_t = ""

    def vk_set_mode(self, mode):
        m = str(mode).lower()
        if m not in ("ko", "en", "num"):
            return
        self.vk_mode = m
        self.vk_shift = False
        if m != "en":
            self.vk_caps = False
        self.vk_shift_last_tap = 0
        if m in ("ko", "en") and self.vk_lang_pref != m:
            self.vk_lang_pref = m
            self.save_pref()

    def vk_commit_compose(self):
        ch = self.vk_compose_char()
        if ch:
            self.vk_committed += ch
        self.vk_h_l = ""
        self.vk_h_v = ""
        self.vk_h_t = ""

    def vk_is_consonant(self, ch):
        return ch in ("ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ")

    def vk_jong_combine(self, first, second):
        return HANGUL_JONG_COMBINE.get((first, second), "")

    def vk_jong_split(self, jong):
        return HANGUL_JONG_SPLIT.get(jong, ("", ""))

    def vk_ko_key_choices(self, token):
        return {
            "ㄱㅋ": ["ㄱ", "ㅋ", "ㄲ"],
            "ㄴㄹ": ["ㄴ", "ㄹ"],
            "ㄷㅌ": ["ㄷ", "ㅌ", "ㄸ"],
            "ㅂㅍ": ["ㅂ", "ㅍ", "ㅃ"],
            "ㅅㅎ": ["ㅅ", "ㅎ", "ㅆ"],
            "ㅈㅊ": ["ㅈ", "ㅊ", "ㅉ"],
            "ㅇㅁ": ["ㅇ", "ㅁ"],
        }.get(token, [])

    def vk_build_vowel(self, cur, nxt):
        if nxt == "·":
            nxt = "ㆍ"
        if nxt not in ("ㆍ", "ㅡ", "ㅣ"):
            return nxt
        if not cur:
            if nxt == "ㆍ":
                return "ㆍ"
            if nxt == "ㅡ":
                return "ㅡ"
            return "ㅣ"
        table = {
            ("ㆍ", "ㆍ"): "ㅗ",
            ("ㆍ", "ㅡ"): "ㅗ",
            ("ㆍ", "ㅣ"): "ㅏ",
            ("ㅡ", "ㆍ"): "ㅜ",
            ("ㅣ", "ㆍ"): "ㅓ",
            ("ㅏ", "ㅣ"): "ㅐ",
            ("ㅓ", "ㅣ"): "ㅔ",
            ("ㅑ", "ㅣ"): "ㅒ",
            ("ㅕ", "ㅣ"): "ㅖ",
            ("ㅗ", "ㅣ"): "ㅚ",
            ("ㅜ", "ㅣ"): "ㅟ",
            ("ㅡ", "ㅣ"): "ㅢ",
            ("ㅏ", "ㆍ"): "ㅑ",
            ("ㅓ", "ㆍ"): "ㅕ",
            ("ㅗ", "ㆍ"): "ㅛ",
            ("ㅜ", "ㆍ"): "ㅠ",
            ("ㅗ", "ㅏ"): "ㅘ",
            ("ㅘ", "ㅣ"): "ㅙ",
            ("ㅜ", "ㅓ"): "ㅝ",
            ("ㅝ", "ㅣ"): "ㅞ",
        }
        return table.get((cur, nxt), nxt)

    def vk_insert_ko_consonant(self, ch, replace_current=False):
        if not self.vk_h_l:
            self.vk_h_l = ch
            return
        if self.vk_h_l and (not self.vk_h_v):
            if replace_current:
                self.vk_h_l = ch
            else:
                self.vk_commit_compose()
                self.vk_h_l = ch
            return
        if self.vk_h_l and self.vk_h_v and (not self.vk_h_t):
            if ch in HANGUL_JONGSEONG:
                self.vk_h_t = ch
            else:
                self.vk_commit_compose()
                self.vk_h_l = ch
            return
        if self.vk_h_t:
            if replace_current:
                left, right = self.vk_jong_split(self.vk_h_t)
                if right:
                    alt = self.vk_jong_combine(left, ch)
                    self.vk_h_t = alt if alt else ch
                else:
                    self.vk_h_t = ch
                return
            combined = self.vk_jong_combine(self.vk_h_t, ch)
            if combined:
                self.vk_h_t = combined
                return
        self.vk_commit_compose()
        self.vk_h_l = ch

    def vk_insert_ko_vowel_symbol(self, symbol):
        if symbol == "·":
            symbol = "ㆍ"
        if not self.vk_h_l:
            self.vk_h_l = "ㅇ"
            self.vk_h_v = self.vk_build_vowel("", symbol)
            return
        if not self.vk_h_v:
            self.vk_h_v = self.vk_build_vowel("", symbol)
            return
        if self.vk_h_t:
            left, moved = self.vk_jong_split(self.vk_h_t)
            if moved:
                self.vk_h_t = left
                self.vk_commit_compose()
                self.vk_h_l = moved
            else:
                moved_single = self.vk_h_t
                self.vk_h_t = ""
                self.vk_commit_compose()
                self.vk_h_l = moved_single
            self.vk_h_v = self.vk_build_vowel("", symbol)
            return
        nv = self.vk_build_vowel(self.vk_h_v, symbol)
        if nv in HANGUL_JUNGSEONG or nv in ("ㆍ", "ㅡ", "ㅣ"):
            self.vk_h_v = nv
        else:
            self.vk_commit_compose()
            self.vk_h_l = "ㅇ"
            self.vk_h_v = self.vk_build_vowel("", symbol)

    def vk_apply_backspace(self):
        if self.vk_h_t:
            left, _right = self.vk_jong_split(self.vk_h_t)
            self.vk_h_t = left
        elif self.vk_h_v:
            prev_v = HANGUL_JUNG_BACKSTEP.get(self.vk_h_v, "")
            self.vk_h_v = prev_v
        elif self.vk_h_l:
            self.vk_h_l = ""
        elif self.vk_committed:
            self.vk_committed = self.vk_committed[:-1]
        self.vk_set_target_text(self.vk_target_id, self.vk_render_text())

    def vk_apply_text_char(self, ch):
        if not ch:
            return
        if len(self.vk_render_text()) >= self.vk_target_max:
            return
        self.vk_commit_compose()
        self.vk_committed += ch
        self.vk_set_target_text(self.vk_target_id, self.vk_render_text())

    def vk_confirm(self):
        self.vk_commit_compose()
        final = self.vk_render_text()
        self.vk_set_target_text(self.vk_target_id, final)
        tid = self.vk_target_id
        if tid == "settings_name":
            self.editing_name = False
            self.save_pref()
            self.toast(self.tr("toast.name_saved"))
        elif tid == "music_search":
            self.editing_music_search = False
        elif tid == "video_search":
            self.editing_video_search = False
        elif tid == "text_search":
            self.editing_text_search = False
        elif tid == "files_search":
            self.editing_files_search = False
        elif tid == "files_rename":
            if self.rename_info_file():
                self.files_info_rename_active = False

    def vk_dismiss(self):
        # Hide only keyboard UI; do not apply confirm/save actions.
        tid = self.vk_target_id
        if tid == "settings_name":
            self.editing_name = False
        elif tid == "music_search":
            self.editing_music_search = False
        elif tid == "video_search":
            self.editing_video_search = False
        elif tid == "text_search":
            self.editing_text_search = False
        elif tid == "files_search":
            self.editing_files_search = False
        elif tid == "files_rename":
            self.files_info_rename_active = False

    def vk_layout_rows(self):
        if self.vk_mode == "ko":
            return [
                ["ㅣ", "ㆍ", "ㅡ", "◀"],
                ["ㄱㅋ", "ㄴㄹ", "ㄷㅌ", "."],
                ["ㅂㅍ", "ㅅㅎ", "ㅈㅊ", "123"],
                [self.tr("vk.key.en", default="EN"), "ㅇㅁ", "space", "▼"],
            ]
        if self.vk_mode == "num":
            return [
                list("1234567890"),
                ["-", "/", ":", ";", "(", ")", "&", "@", "\"", "'"],
                ["ABC", ".", ",", "?", "!", "◀"],
                [self.tr("vk.key.korean", default="한글"), "space", "▼"],
            ]
        return [
            list("qwertyuiop"),
            list("asdfghjkl"),
            ["⇧"] + list("zxcvbnm") + ["◀"],
            [self.tr("vk.key.korean", default="한글"), "123", "space", ".", "▼"],
        ]

    def vk_key_width(self, token, avail_w, cols):
        if token == "space":
            return int(avail_w * 0.34)
        if token in ("▼", self.tr("vk.key.en", default="EN"), self.tr("vk.key.korean", default="한글"), "123", "ABC"):
            return int(avail_w * 0.15)
        if token in ("◀", "⇧"):
            return int(avail_w * 0.12)
        return max(22, int((avail_w - 4 * (cols - 1)) / cols))

    def vk_rect(self):
        h = 178
        return pygame.Rect(0, self.h - h, self.w, h)

    def vk_handle_touch(self, pos):
        if not self.vk_visible:
            return False
        for rr, token in self.vk_key_rects:
            if rr.collidepoint(pos):
                now = pygame.time.get_ticks()
                if token == "◀":
                    self.vk_apply_backspace()
                    return True
                if token == "▼":
                    self.vk_dismiss()
                    return True
                if token == "space":
                    self.vk_apply_text_char(" ")
                    return True
                if token == "123":
                    self.vk_set_mode("num")
                    return True
                if token == "ABC":
                    self.vk_set_mode("en")
                    return True
                if token == "EN":
                    self.vk_set_mode("en")
                    return True
                if token == self.tr("vk.key.korean", default="한글"):
                    self.vk_set_mode("ko")
                    return True
                if token == "⇧":
                    if self.vk_mode == "en":
                        if self.vk_caps:
                            self.vk_caps = False
                            self.vk_shift = False
                            self.vk_shift_last_tap = 0
                        elif self.vk_shift_last_tap and (now - self.vk_shift_last_tap <= self.vk_shift_double_ms):
                            self.vk_caps = True
                            self.vk_shift = False
                            self.vk_shift_last_tap = 0
                        else:
                            self.vk_shift = not self.vk_shift
                            self.vk_shift_last_tap = now
                    else:
                        self.vk_shift = not self.vk_shift
                    return True

                if self.vk_mode == "ko":
                    if token in ("ㆍ", "ㅡ", "ㅣ"):
                        self.vk_insert_ko_vowel_symbol(token)
                        self.vk_last_ko_key = ""
                    else:
                        choices = self.vk_ko_key_choices(token)
                        if not choices:
                            self.vk_last_ko_key = ""
                            self.vk_last_ko_cycle = 0
                            self.vk_last_ko_time = 0
                            self.vk_apply_text_char(token)
                            return True
                        pick = choices[0]
                        replace_current = False
                        if token == self.vk_last_ko_key and now - self.vk_last_ko_time <= 700 and len(choices) > 1:
                            self.vk_last_ko_cycle = (self.vk_last_ko_cycle + 1) % len(choices)
                            pick = choices[self.vk_last_ko_cycle]
                            replace_current = True
                        else:
                            self.vk_last_ko_cycle = 0
                            self.vk_last_ko_key = token
                            pick = choices[0]
                        self.vk_last_ko_time = now
                        self.vk_insert_ko_consonant(pick, replace_current=replace_current)
                    self.vk_set_target_text(self.vk_target_id, self.vk_render_text())
                    return True

                ch = token
                if self.vk_mode == "en" and len(ch) == 1 and ch.isalpha():
                    shift_active = self.vk_shift or self.vk_caps
                    ch = ch.upper() if shift_active else ch.lower()
                    if self.vk_shift and (not self.vk_caps):
                        self.vk_shift = False
                self.vk_apply_text_char(ch)
                return True
        return self.vk_rect().collidepoint(pos)

    def draw_virtual_keyboard(self):
        if not self.vk_visible:
            self.vk_key_rects = []
            return
        panel = self.vk_rect()
        pal = self.pal()
        bg = (18, 20, 26, 230) if self.theme != "light" else (245, 248, 252, 235)
        bd = (88, 98, 118, 230) if self.theme != "light" else (198, 206, 222, 230)
        surf = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
        pygame.draw.rect(surf, bg, (0, 0, panel.w, panel.h), border_radius=14)
        pygame.draw.rect(surf, bd, (0, 0, panel.w, panel.h), width=1, border_radius=14)
        self.screen.blit(surf, panel.topleft)

        rows = self.vk_layout_rows()
        self.vk_key_rects = []
        top_pad = 8
        bottom_pad = 8
        gap_y = 6
        row_h = 34
        if rows:
            row_h = max(30, int((panel.h - top_pad - bottom_pad - gap_y * (len(rows) - 1)) / max(1, len(rows))))
        y = panel.y + top_pad
        for row in rows:
            total_w = panel.w - 12
            x = panel.x + 6
            cols = max(1, len(row))
            if self.vk_mode == "ko":
                gap_x = 4
                ww = max(22, int((total_w - gap_x * (cols - 1)) / cols))
                widths = [ww for _ in row]
                used = sum(widths) + gap_x * (len(row) - 1)
            else:
                gap_x = 4
                widths = [self.vk_key_width(tk, total_w, cols) for tk in row]
                used = sum(widths) + gap_x * (len(row) - 1)
                x += max(0, (total_w - used) // 2)
            for token, ww in zip(row, widths):
                rr = pygame.Rect(x, y, ww, row_h)
                shift_active = self.vk_shift or self.vk_caps
                active = (token == "⇧" and shift_active)
                if token == "space":
                    label = "(공백)" if self.vk_mode == "ko" else self.tr("vk.key.space", default="Space")
                else:
                    label = token
                if self.vk_mode == "en" and len(label) == 1 and label.isalpha() and shift_active:
                    label = label.upper()
                self.draw_select_button(rr, label, active)
                self.vk_key_rects.append((rr, token))
                x += ww + gap_x
            y += row_h + gap_y
        # Mode hint text is intentionally hidden to avoid persistent overlay.

    def apply_brightness(self):
        if self.brightness == 100:
            return
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        alpha = int((100 - self.brightness) * 2.2)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

    def content_touch_pos(self, pos):
        lift_px = int(round(self.vk_lift))
        if lift_px <= 0:
            return pos
        if self.vk_visible and self.vk_rect().collidepoint(pos):
            return pos
        return (pos[0], pos[1] + lift_px)

    # 터치 시작: 제스처/드래그/길게누름 상태를 초기화하고 입력 타깃을 결정
    def handle_touch_down(self, pos, raw_pos=None):
        self.touch_down = True
        self.down_pos = pos
        self.down_time = pygame.time.get_ticks()
        self.did_swipe = False
        self.list_touch_drag = False
        self.list_touch_moved = False
        self.video_ui_touch_consumed = False
        self.photo_ui_touch_consumed = False
        self.clear_seek_hold()
        self.video_progress_drag = False
        self.music_progress_drag = False
        rpos = raw_pos if raw_pos is not None else pos
        if self.vk_visible and self.vk_rect().collidepoint(rpos):
            return
        if self.power_confirm_active:
            return
        if self.state == "PHOTO" and self.photo_view == "VIEWER" and self.photo_delete_confirm_active:
            return
        if self.state == "PHOTO" and self.photo_view == "VIEWER" and self.photo_share_sheet_active:
            return

        if self.state == "HOME":
            self.active_button = None
            for b in self.page_buttons():
                if b.rect.collidepoint(pos):
                    self.active_button = b
                    break
        elif self.state == "MUSIC" and self.music_view == "NOW":
            controls = self.music_control_rects()
            if controls["prev"].collidepoint(pos):
                self.begin_seek_hold("music", -1)
            elif controls["next"].collidepoint(pos):
                self.begin_seek_hold("music", +1)
            elif self.progress_rect().collidepoint(pos):
                length = self.current_track_len()
                if length > 0.1:
                    ratio = clamp((pos[0] - self.progress_rect().x) / max(1, self.progress_rect().w), 0.0, 1.0)
                    self.music_progress_drag = True
                    self.music_progress_drag_pos = float(length * ratio)
        elif self.state == "VIDEO" and self.video_view == "PLAYER":
            ui = self.video_ui_touch_rects()
            if self.video_ui_progress <= 0.05:
                self.video_ui_set_visible(True, reset_timer=True)
                self.video_ui_touch_consumed = True
                return
            in_ui = ui["top_bar"].collidepoint(pos) or ui["bottom_bar"].collidepoint(pos)
            if not in_ui:
                self.video_ui_set_visible(False, reset_timer=False)
                self.video_ui_touch_consumed = True
                return
            self.video_ui_last_interaction = pygame.time.get_ticks()
            controls = ui
            if controls["prev"].collidepoint(pos):
                self.begin_seek_hold("video", -1)
            elif controls["next"].collidepoint(pos):
                self.begin_seek_hold("video", +1)
            elif controls["progress"].collidepoint(pos):
                _p, meta = self.current_video_meta()
                length = float(meta.get("length", 0.0)) if meta else 0.0
                if length > 0.0:
                    ratio = self.video_progress_ratio_at(controls["progress"], pos)
                    self.video_progress_drag = True
                    self.video_progress_drag_pos = float(length * ratio)
        elif self.state == "VIDEO" and self.video_view == "LIST":
            rect, _total, _row_h = self.video_scroll_info()
            if rect and rect.collidepoint(pos):
                self.begin_list_touch_drag(pos)
        elif self.state == "TEXT":
            if self.text_view == "LIST":
                rect, _total, _row_h = self.text_scroll_info()
            else:
                rect = self.text_reader_body_rect()
            if rect and rect.collidepoint(pos):
                self.begin_list_touch_drag(pos)
        elif self.state == "FILES":
            if self.files_view in ("ROOT", "LIST"):
                rect, _total, _row_h = self.files_scroll_info()
                if rect and rect.collidepoint(pos):
                    self.begin_list_touch_drag(pos)
        elif self.state == "PHOTO":
            if self.photo_view == "VIEWER":
                # Viewer gestures/buttons are resolved on touch-up.
                return
            if self.photo_view == "GRID":
                rect, _total, _row_h = self.photo_scroll_info()
                if rect and rect.collidepoint(pos):
                    self.begin_list_touch_drag(pos)
        elif self.state == "MUSIC" and self.music_view in ("LIST", "QUEUE", "ALBUMS", "ARTISTS", "ARTIST_ALBUMS", "GENRES"):
            rect, _total, _row_h = self.music_scroll_info()
            if rect and rect.collidepoint(pos):
                self.begin_list_touch_drag(pos)
        elif self.state == "SETTINGS_INFO" and not self.settings_info_name_popup_active:
            rect, _total, _row_h = self.settings_info_scroll_info()
            if rect and rect.collidepoint(pos):
                self.begin_list_touch_drag(pos)

    # 터치 이동: 스와이프/관성 스크롤/진행바 드래그 값을 실시간 갱신
    def handle_touch_move(self, pos, raw_pos=None):
        if not self.touch_down:
            return
        rpos = raw_pos if raw_pos is not None else pos
        if self.vk_visible and self.vk_rect().collidepoint(rpos):
            return
        dx = pos[0] - self.down_pos[0]
        dy = pos[1] - self.down_pos[1]

        if self.state == "HOME" and not self.did_swipe:
            self.refresh_home_pages()
            if abs(dx) > SWIPE_THRESHOLD and abs(dx) > abs(dy):
                self.did_swipe = True
                if dx < 0:
                    self.page = (self.page + 1) % self.total_pages
                    self.toast(self.tr("toast.next"))
                else:
                    self.page = (self.page - 1) % self.total_pages
                    self.toast(self.tr("toast.prev"))
                self.active_button = None
        elif self.state in ("MUSIC", "VIDEO", "PHOTO", "TEXT", "FILES", "SETTINGS_INFO"):
            if self.list_touch_drag and (
                (self.state == "VIDEO" and self.video_view == "LIST")
                or (self.state == "TEXT" and self.text_view in ("LIST", "READER"))
                or (self.state == "FILES" and self.files_view in ("ROOT", "LIST"))
                or (self.state == "PHOTO" and self.photo_view == "GRID")
                or (self.state == "SETTINGS_INFO" and not self.settings_info_name_popup_active)
                or self.music_view in ("LIST", "QUEUE", "ALBUMS", "ARTISTS", "ARTIST_ALBUMS", "GENRES")
            ):
                if self.state == "VIDEO" and self.video_view == "LIST":
                    rect, total_items, row_h = self.video_scroll_info()
                elif self.state == "TEXT":
                    if self.text_view == "LIST":
                        rect, total_items, row_h = self.text_scroll_info()
                    else:
                        rect = self.text_reader_rect()
                        total_items = max(1, len(self.text_reader_lines()))
                        row_h = self.text_reader_row_h()
                elif self.state == "FILES":
                    rect, total_items, row_h = self.files_scroll_info()
                elif self.state == "PHOTO":
                    rect, total_items, row_h = self.photo_scroll_info()
                elif self.state == "SETTINGS_INFO":
                    rect, total_items, row_h = self.settings_info_scroll_info()
                else:
                    rect, total_items, row_h = self.music_scroll_info()
                if rect:
                    max_rows = self.scroll_page_rows(rect, row_h)
                    max_scroll = max(0, total_items - max_rows)
                    now_ms = pygame.time.get_ticks()
                    self.list_touch_smooth_y += (float(pos[1]) - self.list_touch_smooth_y) * 0.42
                    dy_smooth = self.list_touch_smooth_y - self.list_touch_start_y
                    rows = dy_smooth / max(1, row_h)
                    if abs(pos[1] - self.down_pos[1]) >= 6:
                        self.list_touch_moved = True
                    dt_ms = max(1, now_ms - self.list_touch_last_ms)
                    dy_raw = float(pos[1]) - self.list_touch_last_y
                    vel_rows = (-(dy_raw / max(1, row_h))) / (dt_ms / 1000.0)
                    self.list_scroll_velocity = (self.list_scroll_velocity * 0.72) + (vel_rows * 0.28)
                    self.list_touch_last_y = float(pos[1])
                    self.list_touch_last_ms = now_ms
                    self.set_list_scroll(clamp(self.list_touch_start_scroll - rows, 0, max_scroll), snap=True)
                return
            if self.state != "MUSIC" or self.music_view != "NOW":
                if self.state == "VIDEO" and self.video_view == "PLAYER":
                    ui = self.video_ui_touch_rects()
                    _p, meta = self.current_video_meta()
                    length = float(meta.get("length", 0.0)) if meta else 0.0
                    if (self.video_progress_drag or ui["progress"].collidepoint(pos)) and length > 0.0:
                        ratio = self.video_progress_ratio_at(ui["progress"], pos)
                        self.video_progress_drag = True
                        self.video_progress_drag_pos = float(length * ratio)
                        self.video_ui_last_interaction = pygame.time.get_ticks()
                        return
                    vol = self.video_ui_touch_rects()["volume"]
                    if vol.collidepoint(pos):
                        ratio = self.video_volume_ratio_at(vol, pos)
                        self.music_volume = float(ratio)
                        self.video_volume = self.music_volume
                        if self.mixer_ready:
                            pygame.mixer.music.set_volume(self.music_volume)
                        self.sync_video_audio_volume(force=False)
                        return
                return
            vol = self.music_control_rects()["volume"]
            prog = self.progress_rect()
            length = self.current_track_len()
            if (self.music_progress_drag or prog.collidepoint(pos)) and length > 0.1:
                ratio = clamp((pos[0] - prog.x) / max(1, prog.w), 0.0, 1.0)
                self.music_progress_drag = True
                self.music_progress_drag_pos = float(length * ratio)
                return
            if vol.collidepoint(pos):
                track = self.volume_track_rect(vol)
                ratio = clamp((pos[0] - track.x) / track.w, 0.0, 1.0)
                self.music_volume = float(ratio)
                if self.mixer_ready:
                    pygame.mixer.music.set_volume(self.music_volume)
        elif self.state == "SETTINGS_SOUND":
            ui = self.settings_sound_rects()
            if ui["volume"].collidepoint(pos):
                track = self.volume_track_rect(ui["volume"])
                ratio = clamp((pos[0] - track.x) / max(1, track.w), 0.0, 1.0)
                self.music_volume = float(ratio)
                self.video_volume = self.music_volume
                if self.mixer_ready:
                    pygame.mixer.music.set_volume(self.music_volume)
        elif self.state == "SETTINGS_DISPLAY":
            ui = self.settings_display_rects()
            if ui["bright_row"].collidepoint(pos):
                tr = ui["bright_track"]
                ratio = clamp((pos[0] - tr.x) / max(1, tr.w), 0.0, 1.0)
                self.brightness = int(round(40 + ratio * 60))
                self.save_pref()

    # 터치 종료: 버튼 클릭/목록 선택/다이얼로그 확인 등 최종 동작 처리
    def handle_touch_up(self, pos, raw_pos=None):
        if not self.touch_down:
            return
        self.touch_down = False
        rpos = raw_pos if raw_pos is not None else pos

        held_ms = pygame.time.get_ticks() - self.down_time

        if self.power_confirm_active:
            btn = self.power_confirm_buttons()
            if btn["yes"].collidepoint(pos):
                self.exit_requested = True
            elif btn["no"].collidepoint(pos):
                self.power_confirm_active = False
            return

        if self.state == "SETTINGS" and self.settings_picker_active:
            ss = self.settings_picker_rects()
            p = clamp((pygame.time.get_ticks() - self.settings_picker_start) / max(1, self.settings_picker_ms), 0.0, 1.0)
            base = ss["panel"]
            scale = 0.92 + 0.08 * p
            ww = int(base.w * scale)
            hh = int(base.h * scale)
            rr = pygame.Rect(base.centerx - ww // 2, base.centery - hh // 2, ww, hh)
            by = rr.y - base.y
            for i, (_label, value) in enumerate(self.settings_picker_options):
                if i >= len(ss["options"]):
                    break
                opt_r = ss["options"][i].move(0, by)
                if opt_r.collidepoint(pos):
                    self.apply_settings_picker_value(self.settings_picker_kind, value)
                    self.settings_picker_active = False
                    self.settings_picker_kind = ""
                    self.settings_picker_options = []
                    return
            cancel_r = ss["cancel"].move(0, by)
            if cancel_r.collidepoint(pos):
                self.settings_picker_active = False
                self.settings_picker_kind = ""
                self.settings_picker_options = []
            return
        if self.state == "PHOTO" and self.photo_view == "VIEWER" and self.photo_delete_confirm_active:
            btn = self.power_confirm_buttons()
            if btn["yes"].collidepoint(pos):
                self.execute_photo_delete_confirmed()
            elif btn["no"].collidepoint(pos):
                self.photo_delete_confirm_active = False
                self.photo_delete_target_path = ""
            return
        if self.state == "FILES" and self.files_view == "LIST" and self.files_delete_confirm_active:
            btn = self.power_confirm_buttons()
            if btn["yes"].collidepoint(pos):
                action = self.files_delete_confirm_action
                if action == "trash_delete":
                    moved = self.permanently_delete_selected_trash_files(self.files_delete_confirm_paths)
                    if moved > 0:
                        self.toast(self.tr("files.action.permanent_deleted", count=moved, default=f"{moved}개를 영구 삭제했습니다"))
                    else:
                        self.toast(self.tr("files.action.delete_failed", default="삭제할 항목이 없습니다"))
                elif action == "trash_restore":
                    moved = self.restore_selected_trash_files(self.files_delete_confirm_paths)
                    if moved > 0:
                        self.toast(self.tr("files.action.restored", count=moved, default=f"{moved}개를 복원했습니다"))
                    else:
                        self.toast(self.tr("files.action.restore_failed", default="복원할 항목이 없습니다"))
                else:
                    moved = self.delete_selected_files_to_trash(self.files_delete_confirm_paths)
                    if moved > 0:
                        self.toast(self.tr("files.action.deleted", count=moved, default=f"{moved}개를 휴지통으로 이동했습니다"))
                    else:
                        self.toast(self.tr("files.action.delete_failed", default="삭제할 항목이 없습니다"))
                self.files_delete_confirm_active = False
                self.files_delete_confirm_paths = []
                self.files_delete_confirm_action = ""
                self.files_icon_cache.clear()
                self.photo_thumb_cache.clear()
                self.video_thumb_cache.clear()
            elif btn["no"].collidepoint(pos):
                self.files_delete_confirm_active = False
                self.files_delete_confirm_paths = []
                self.files_delete_confirm_action = ""
            return
        if self.state == "PHOTO" and self.photo_view == "VIEWER" and self.photo_share_sheet_active:
            files = self.filtered_photo_files()
            if files:
                self.photo_index = int(clamp(self.photo_index, 0, len(files) - 1))
                src = files[self.photo_index]
            else:
                src = ""
            ss = self.photo_share_sheet_rects()
            p = clamp((pygame.time.get_ticks() - self.photo_share_sheet_start) / max(1, self.photo_share_sheet_ms), 0.0, 1.0)
            base = ss["panel"]
            scale = 0.92 + 0.08 * p
            ww = int(base.w * scale)
            hh = int(base.h * scale)
            rr = pygame.Rect(base.centerx - ww // 2, base.centery - hh // 2, ww, hh)
            by = rr.y - base.y
            copy_r = ss["copy"].move(0, by)
            wall_r = ss["wallpaper"].move(0, by)
            cancel_r = ss["cancel"].move(0, by)
            if copy_r.collidepoint(pos) and src:
                self.copy_photo_action(src)
                self.photo_share_sheet_active = False
                return
            if wall_r.collidepoint(pos) and src:
                self.set_photo_as_wallpaper(src)
                self.photo_share_sheet_active = False
                return
            if cancel_r.collidepoint(pos):
                self.photo_share_sheet_active = False
                return
            return

        if self.vk_visible and self.vk_handle_touch(rpos):
            return

        if self.state in ("MUSIC", "VIDEO", "PHOTO", "TEXT", "FILES", "SETTINGS_INFO") and self.list_touch_drag and self.list_touch_moved:
            self.list_scroll_inertia_active = abs(self.list_scroll_velocity) >= 0.05
            self.list_touch_drag = False
            self.list_touch_moved = False
            self.clear_seek_hold()
            return
        self.list_touch_drag = False
        self.list_touch_moved = False
        hold_consumed = self.seek_hold_consumed
        self.clear_seek_hold()
        if hold_consumed:
            return
        if self.video_ui_touch_consumed:
            self.video_ui_touch_consumed = False
            return
        if self.photo_ui_touch_consumed:
            self.photo_ui_touch_consumed = False
            return

        if self.state == "HOME":
            if self.active_button and held_ms >= LONG_PRESS_MS and not self.did_swipe:
                self.toast(self.tr("toast.options", label=self.active_button.label))
                self.active_button = None
                return

            if self.active_button and self.active_button.rect.collidepoint(pos) and not self.did_swipe:
                self.run_app(self.active_button.app)
            self.active_button = None
        elif self.state == "VIDEO":
            ui = self.video_ui_touch_rects() if self.video_view == "PLAYER" else None
            if self.video_view == "PLAYER" and ui and ("back" in ui) and ui["back"].collidepoint(pos):
                self.pending_back_transition = True
                self.video_view = "LIST"
                self.video_playing = False
                self.stop_video_process()
                self.resume_music_after_video()
                return
            if self.video_view == "PLAYER" and ui and ("portrait" in ui) and ui["portrait"].collidepoint(pos):
                self.video_ui_last_interaction = pygame.time.get_ticks()
                self.video_rotation = 0
                self.save_pref()
                if self.video_playing:
                    filtered = self.filtered_video_files()
                    if filtered and 0 <= self.video_index < len(filtered):
                        cur = self.current_video_pos()
                        self.start_video_decode(filtered[self.video_index], seek=cur)
                else:
                    self.video_frame_surface = None
                return
            if self.video_view != "PLAYER" and self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.editing_video_search = False
                self.video_sort_picker_open = False
                self.video_playing = False
                self.stop_video_process()
                self.state = "HOME"
                return
            if self.video_view == "PLAYER":
                controls = ui
                filtered = self.filtered_video_files()
                if self.video_progress_drag and filtered:
                    self.video_ui_last_interaction = pygame.time.get_ticks()
                    self.video_prev_button_last_tap = 0
                    self.video_prev_chain_active = False
                    self.video_progress_drag = False
                    self.seek_video_to(self.video_progress_drag_pos)
                    return
                if controls["prev"].collidepoint(pos) and filtered:
                    self.video_ui_last_interaction = pygame.time.get_ticks()
                    now_ms = pygame.time.get_ticks()
                    if self.video_prev_chain_active:
                        self.prev_video_track()
                        self.video_prev_button_last_tap = 0
                    elif now_ms - self.video_prev_button_last_tap <= 380:
                        self.prev_video_track()
                        self.video_prev_button_last_tap = 0
                    else:
                        self.restart_current_video()
                        self.video_prev_button_last_tap = now_ms
                    return
                if controls["play"].collidepoint(pos):
                    self.video_ui_last_interaction = pygame.time.get_ticks()
                    self.video_prev_button_last_tap = 0
                    self.video_prev_chain_active = False
                    if filtered:
                        if self.video_playing:
                            self.pause_video_decode()
                        else:
                            self.resume_video_decode()
                    return
                if controls["next"].collidepoint(pos) and filtered:
                    self.video_ui_last_interaction = pygame.time.get_ticks()
                    self.video_prev_button_last_tap = 0
                    self.video_prev_chain_active = False
                    self.play_video_at((self.video_index + 1) % len(filtered), via_prev=False)
                    return
                if ("rot_left" in controls) and controls["rot_left"].collidepoint(pos):
                    self.video_ui_last_interaction = pygame.time.get_ticks()
                    self.video_prev_button_last_tap = 0
                    self.video_prev_chain_active = False
                    self.video_rotation = (self.video_rotation + 90) % 360
                    self.save_pref()
                    if self.video_playing:
                        cur = self.current_video_pos()
                        self.start_video_decode(filtered[self.video_index], seek=cur)
                    else:
                        self.video_frame_surface = None
                    return
                if ("rot_right" in controls) and controls["rot_right"].collidepoint(pos):
                    self.video_ui_last_interaction = pygame.time.get_ticks()
                    self.video_prev_button_last_tap = 0
                    self.video_prev_chain_active = False
                    self.video_rotation = (self.video_rotation - 90) % 360
                    self.save_pref()
                    if self.video_playing:
                        cur = self.current_video_pos()
                        self.start_video_decode(filtered[self.video_index], seek=cur)
                    else:
                        self.video_frame_surface = None
                    return
                if controls["volume"].collidepoint(pos):
                    self.video_ui_last_interaction = pygame.time.get_ticks()
                    self.video_prev_button_last_tap = 0
                    self.video_prev_chain_active = False
                    ratio = self.video_volume_ratio_at(controls["volume"], pos)
                    self.music_volume = float(ratio)
                    self.video_volume = self.music_volume
                    if self.mixer_ready:
                        pygame.mixer.music.set_volume(self.music_volume)
                    self.save_pref()
                    self.sync_video_audio_volume(force=True)
                    return
                if controls["progress"].collidepoint(pos) and filtered:
                    self.video_ui_last_interaction = pygame.time.get_ticks()
                    self.video_prev_button_last_tap = 0
                    self.video_prev_chain_active = False
                    _p, meta = self.current_video_meta()
                    length = float(meta.get("length", 0.0)) if meta else 0.0
                    if length > 0.0:
                        ratio = self.video_progress_ratio_at(controls["progress"], pos)
                        target = length * ratio
                        self.start_video_decode(filtered[self.video_index], seek=target)
                    return
                return
            if self.video_search_rect().collidepoint(pos):
                self.editing_video_search = True
                self.video_sort_picker_open = False
                return
            sort_btn = self.video_sort_button_rect()
            if sort_btn.collidepoint(pos):
                self.video_sort_picker_open = not self.video_sort_picker_open
                self.editing_video_search = False
                return
            if self.video_sort_picker_open:
                opts = self.video_sort_option_rects()
                picked = None
                for key, rect in opts.items():
                    if rect.collidepoint(pos):
                        picked = key
                        break
                if picked:
                    self.video_sort = picked
                    self.set_list_scroll(0, snap=True)
                    self.video_sort_picker_open = False
                    self.save_pref()
                    return
                self.video_sort_picker_open = False
            list_rect = self.video_list_rect()
            if list_rect.collidepoint(pos):
                _rect, _total, row_h = self.video_scroll_info()
                rel_y = pos[1] - list_rect.y
                item_pos = self.list_scroll_index() + rel_y // row_h
                filtered = self.filtered_video_files()
                if 0 <= item_pos < len(filtered):
                    self.play_video_at(item_pos)
            return
        elif self.state == "TEXT":
            if self.text_view == "READER":
                ctr = self.text_reader_control_rects(self.text_reader_rect())
                if ctr["minus"].collidepoint(pos):
                    self.text_font_percent = int(clamp(self.text_font_percent - self.text_font_step, self.text_font_min, self.text_font_max))
                    self.text_lines_cache.clear()
                    self.set_list_scroll(0, snap=True)
                    return
                if ctr["plus"].collidepoint(pos):
                    self.text_font_percent = int(clamp(self.text_font_percent + self.text_font_step, self.text_font_min, self.text_font_max))
                    self.text_lines_cache.clear()
                    self.set_list_scroll(0, snap=True)
                    return
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                if self.text_view == "READER":
                    self.text_view = "LIST"
                    self.editing_text_search = False
                    self.text_sort_picker_open = False
                    self.set_list_scroll(0, snap=True)
                else:
                    self.state = "HOME"
                return
            if self.text_view == "LIST":
                if self.text_search_rect().collidepoint(pos):
                    self.editing_text_search = True
                    self.text_sort_picker_open = False
                    return
                sort_btn = self.text_sort_button_rect()
                if sort_btn.collidepoint(pos):
                    self.text_sort_picker_open = not self.text_sort_picker_open
                    self.editing_text_search = False
                    return
                if self.text_sort_picker_open:
                    opts = self.text_sort_option_rects()
                    picked = None
                    for key, rect in opts.items():
                        if rect.collidepoint(pos):
                            picked = key
                            break
                    if picked:
                        self.text_sort = picked
                        self.set_list_scroll(0, snap=True)
                        self.text_sort_picker_open = False
                        return
                    self.text_sort_picker_open = False
                list_rect = self.text_list_rect()
                if list_rect.collidepoint(pos):
                    _rect, _total, row_h = self.text_scroll_info()
                    rel_y = pos[1] - list_rect.y
                    item_pos = self.list_scroll_index() + rel_y // row_h
                    filtered = self.filtered_text_files()
                    if 0 <= item_pos < len(filtered):
                        self.text_index = item_pos
                        self.text_view = "READER"
                        self.editing_text_search = False
                        self.text_sort_picker_open = False
                        self.set_list_scroll(0, snap=True)
                return
        elif self.state == "PHOTO":
            if self.photo_view == "VIEWER":
                ui = self.photo_ui_touch_rects()
                files = self.filtered_photo_files()
                dx = pos[0] - self.down_pos[0]
                dy = pos[1] - self.down_pos[1]
                down_in_ui = ui["top_bar"].collidepoint(self.down_pos) or ui["bottom_bar"].collidepoint(self.down_pos)
                if (not down_in_ui) and abs(dx) > SWIPE_THRESHOLD and abs(dx) > abs(dy):
                    if files and self.photo_zoom <= 1.05:
                        cur_idx = int(clamp(self.photo_index, 0, len(files) - 1))
                        if dx < 0:
                            next_idx = int(clamp(cur_idx + 1, 0, len(files) - 1))
                            self.start_photo_slide(files, next_idx, +1)
                        else:
                            next_idx = int(clamp(cur_idx - 1, 0, len(files) - 1))
                            self.start_photo_slide(files, next_idx, -1)
                    return
                if (not down_in_ui) and abs(dx) < 10 and abs(dy) < 10:
                    now = pygame.time.get_ticks()
                    lx, ly = self.photo_last_tap_pos
                    if (
                        self.photo_last_tap_ms > 0
                        and (now - self.photo_last_tap_ms) <= 320
                        and abs(pos[0] - lx) <= 24
                        and abs(pos[1] - ly) <= 24
                    ):
                        self.photo_zoom_toggle()
                        self.photo_last_tap_ms = 0
                        return
                    self.photo_last_tap_ms = now
                    self.photo_last_tap_pos = pos
                    if self.photo_ui_progress <= 0.05:
                        self.photo_ui_set_visible(True)
                    else:
                        self.photo_ui_set_visible(False)
                    return
                if ui["back"].collidepoint(pos):
                    self.pending_back_transition = True
                    self.photo_view = "GRID"
                    self.photo_zoom = 1.0
                    self.photo_zoom_anim_active = False
                    self.photo_fingers.clear()
                    self.update_photo_pinch_state()
                    self.photo_slide_active = False
                    self.photo_share_sheet_active = False
                    self.photo_delete_confirm_active = False
                    self.photo_delete_target_path = ""
                    return
                if ui["share"].collidepoint(pos):
                    if files:
                        self.photo_index = int(clamp(self.photo_index, 0, len(files) - 1))
                        self.photo_share_sheet_active = True
                        self.photo_share_sheet_start = pygame.time.get_ticks()
                    return
                if ui["delete"].collidepoint(pos):
                    if files:
                        self.confirm_delete_current_photo()
                    return
                return
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                if self.photo_view == "VIEWER":
                    self.photo_view = "GRID"
                else:
                    if self.photo_pick_wallpaper:
                        self.photo_pick_wallpaper = False
                        self.state = "SETTINGS_WALLPAPER"
                    else:
                        self.state = "HOME"
                return
            if self.photo_view == "GRID":
                files = self.filtered_photo_files()
                rect = self.photo_grid_rect()
                if rect.collidepoint(pos) and files:
                    gap = 4
                    cell = max(24, (rect.w - gap * (PHOTO_COLS - 1)) // PHOTO_COLS)
                    row_h = cell + gap
                    rel_x = pos[0] - rect.x
                    rel_y = pos[1] - rect.y
                    col = rel_x // (cell + gap)
                    row = self.list_scroll_index() + (rel_y // row_h)
                    if 0 <= col < PHOTO_COLS and rel_x % (cell + gap) < cell and rel_y % row_h < cell:
                        idx = int(row * PHOTO_COLS + col)
                        if 0 <= idx < len(files):
                            if self.photo_pick_wallpaper:
                                self.set_photo_as_wallpaper(files[idx])
                                self.photo_pick_wallpaper = False
                                self.pending_back_transition = True
                                self.state = "SETTINGS_WALLPAPER"
                            else:
                                self.photo_index = idx
                                self.photo_view = "VIEWER"
                                self.photo_zoom = 1.0
                                self.photo_zoom_anim_active = False
                                self.photo_fingers.clear()
                                self.update_photo_pinch_state()
                                self.photo_slide_active = False
                                self.photo_share_sheet_active = False
                                self.photo_delete_confirm_active = False
                                self.photo_delete_target_path = ""
                                self.photo_ui_visible = True
                                self.photo_ui_anim_from = 1.0
                                self.photo_ui_anim_to = 1.0
                                self.photo_ui_progress = 1.0
                                self.pending_back_transition = False
                return
        elif self.state == "CALC":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "HOME"
                return
            if self.calc_ce_rect().collidepoint(pos):
                self.handle_calc_button("CE")
                return
            for label, rect in self.calc_button_rects():
                if rect.collidepoint(pos):
                    self.handle_calc_button(label)
                    return
        elif self.state == "CALENDAR":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "HOME"
                return
            if self.calendar_title_rect().collidepoint(pos):
                y, m = self.calendar_current_pair()
                self.calendar_year, self.calendar_month = y, m
                return
            nav = self.calendar_nav_rects()
            if nav["prev"].collidepoint(pos) and self.calendar_can_prev():
                self.calendar_shift_month(-1)
                return
            if nav["next"].collidepoint(pos) and self.calendar_can_next():
                self.calendar_shift_month(+1)
                return
        elif self.state == "FILES":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                if self.files_view == "INFO":
                    self.files_info_rename_active = False
                    self.files_info_rename_text = ""
                    self.files_view = "LIST"
                elif self.files_view == "LIST":
                    if self.files_path:
                        self.files_path = os.path.dirname(self.files_path)
                        self.files_selected = set()
                        self.set_list_scroll(0, snap=True)
                    else:
                        self.files_view = "ROOT"
                        self.files_search = ""
                        self.editing_files_search = False
                        self.files_sort_picker_open = False
                        self.files_selected = set()
                else:
                    self.state = "HOME"
                return

            if self.files_view == "INFO":
                info_rect = self.files_info_rect()
                actions = self.files_info_action_rects(info_rect)
                if self.files_info_rename_active:
                    dlg = self.files_info_rename_dialog_rects()
                    if dlg["cancel"].collidepoint(pos):
                        self.files_info_rename_active = False
                        return
                    if dlg["ok"].collidepoint(pos):
                        if self.rename_info_file():
                            self.files_info_rename_active = False
                        return
                    return
                ent = self.files_info_entry if isinstance(self.files_info_entry, dict) else None
                if (not ent) or (not os.path.isfile(ent.get("path", ""))):
                    self.files_view = "LIST"
                    self.files_info_entry = None
                    return
                if actions["rename"].collidepoint(pos):
                    stem, _ext = os.path.splitext(ent.get("name", ""))
                    self.files_info_rename_text = stem
                    self.files_info_rename_active = True
                    self.files_info_rename_start = pygame.time.get_ticks()
                    return
                if actions["delete"].collidepoint(pos):
                    moved = self.delete_selected_files_to_trash([ent.get("path", "")])
                    if moved > 0:
                        self.files_info_entry = None
                        self.files_view = "LIST"
                        self.toast(self.tr("files.action.deleted", count=moved, default=f"{moved}개를 휴지통으로 이동했습니다"))
                    else:
                        self.toast(self.tr("files.action.delete_failed", default="삭제할 항목이 없습니다"))
                    return

            if self.files_view == "ROOT":
                list_rect = self.files_effective_list_rect()
                if list_rect.collidepoint(pos):
                    _rect, _total, row_h = self.files_scroll_info()
                    rel_y = pos[1] - list_rect.y
                    item_pos = self.list_scroll_index() + rel_y // row_h
                    roots = self.files_root_entries()
                    if 0 <= item_pos < len(roots):
                        picked = roots[item_pos]
                        if not picked.get("enabled"):
                            return
                        if picked["key"] == "internal":
                            self.files_source = "internal"
                            self.files_path = ""
                            self.files_sort_desc = False
                        elif picked["key"] == "trash":
                            self.files_source = "trash"
                            self.files_path = ""
                            self.files_sort_desc = True
                        self.files_delete_confirm_active = False
                        self.files_delete_confirm_paths = []
                        self.files_delete_confirm_action = ""
                        self.files_view = "LIST"
                        self.files_search = ""
                        self.files_sort_picker_open = False
                        self.editing_files_search = False
                        self.files_selected = set()
                        self.set_list_scroll(0, snap=True)
                return

            if self.files_view == "INFO":
                return

            if self.files_search_rect().collidepoint(pos):
                self.editing_files_search = True
                self.files_sort_picker_open = False
                return
            if self.files_selection_enabled() and self.files_selected:
                ar = self.files_selected_action_rects()
                if self.files_source == "trash" and ("left" in ar) and ar["left"].collidepoint(pos):
                    self.begin_files_delete_confirm("trash_restore")
                    return
                if ar["right"].collidepoint(pos):
                    if self.files_source == "trash":
                        self.begin_files_delete_confirm("trash_delete")
                    else:
                        self.begin_files_delete_confirm("move_trash")
                    return
            sort_btn = self.files_sort_button_rect()
            order_btn = self.files_order_button_rect()
            if order_btn.collidepoint(pos):
                self.files_sort_desc = not self.files_sort_desc
                self.set_list_scroll(0, snap=True)
                return
            if self.files_source != "trash" and sort_btn.collidepoint(pos):
                self.files_sort_picker_open = not self.files_sort_picker_open
                self.editing_files_search = False
                return
            if self.files_source != "trash" and self.files_sort_picker_open:
                opts = self.files_sort_option_rects()
                picked = None
                for key, rect in opts.items():
                    if rect.collidepoint(pos):
                        picked = key
                        break
                if picked:
                    self.files_sort = picked
                    self.set_list_scroll(0, snap=True)
                    self.files_sort_picker_open = False
                    return
                self.files_sort_picker_open = False

            list_rect = self.files_effective_list_rect()
            if list_rect.collidepoint(pos):
                _rect, _total, row_h = self.files_scroll_info()
                rel_y = pos[1] - list_rect.y
                item_pos = self.list_scroll_index() + rel_y // row_h
                items = self.filtered_file_entries()
                if 0 <= item_pos < len(items):
                    ent = items[item_pos]
                    if self.files_selection_enabled():
                        y = list_rect.y + (item_pos - self.list_scroll_index()) * row_h - int((self.list_scroll - int(self.list_scroll)) * row_h)
                        row_rect = pygame.Rect(list_rect.x + 4, y + 2, list_rect.w - 8, row_h - 4)
                        thumb_size = row_rect.h - 8
                        cb_rect = self.files_checkbox_hit_rect(row_rect, thumb_size)
                        if cb_rect.collidepoint(pos):
                            p = ent.get("path", "")
                            if p in self.files_selected:
                                self.files_selected.remove(p)
                            else:
                                self.files_selected.add(p)
                            return
                    if ent.get("is_dir"):
                        name = ent.get("name", "")
                        if self.files_path:
                            self.files_path = os.path.join(self.files_path, name)
                        else:
                            self.files_path = name
                        self.files_selected = set()
                        self.set_list_scroll(0, snap=True)
                    else:
                        if self.files_source == "trash":
                            return
                        self.files_info_entry = ent
                        self.files_view = "INFO"
                return
        elif self.state == "SETTINGS":
            if self.settings_picker_active:
                return
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.editing_name = False
                self.settings_picker_active = False
                self.state = "HOME"
                return

            if self.settings_footer_rect().collidepoint(pos):
                self.pending_back_transition = False
                self.editing_name = False
                self.settings_picker_active = False
                self.state = "SETTINGS_FULL"
                return

            if self.handle_settings_full_click(pos):
                return
        elif self.state == "SETTINGS_FULL":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.editing_name = False
                self.state = "SETTINGS"
                return
            for _label, key, rr in self.settings_full_menu_rows():
                if rr.collidepoint(pos):
                    if key == "bluetooth":
                        if self.settings_bt_toggle_rect(rr).inflate(6, 6).collidepoint(pos):
                            self.bt_enabled = not self.bt_enabled
                            self.save_pref()
                            return
                        self.pending_back_transition = False
                        self.state = "SETTINGS_BT"
                    elif key == "sound":
                        self.pending_back_transition = False
                        self.state = "SETTINGS_SOUND"
                    elif key == "display":
                        self.pending_back_transition = False
                        self.state = "SETTINGS_DISPLAY"
                    elif key == "battery":
                        self.pending_back_transition = False
                        self.state = "SETTINGS_BATTERY"
                    elif key == "wallpaper":
                        self.pending_back_transition = False
                        self.state = "SETTINGS_WALLSTYLE"
                    elif key == "home_lock":
                        self.pending_back_transition = False
                        self.state = "SETTINGS_HOMELOCK"
                    elif key == "general":
                        self.pending_back_transition = False
                        self.state = "SETTINGS_GENERAL"
                    elif key == "info":
                        self.pending_back_transition = False
                        self.settings_info_tab = "basic"
                        self.set_list_scroll(0, snap=True)
                        self.state = "SETTINGS_INFO"
                    else:
                        self.toast(self.tr("toast.not_implemented", default="준비 중인 기능입니다"))
                    return
        elif self.state == "SETTINGS_BT":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_FULL"
                return
            top = STATUS_H + 48
            main = pygame.Rect(14, top, self.w - 28, 46)
            scan = pygame.Rect(14, main.bottom + 8, self.w - 28, 40)
            if main.collidepoint(pos):
                self.bt_enabled = not self.bt_enabled
                self.save_pref()
                return
            if scan.collidepoint(pos):
                self.bt_scanning = True
                self.bt_scan_started = pygame.time.get_ticks()
                return
            y = scan.bottom + 10
            for i, dev in enumerate(self.bt_devices):
                rr = pygame.Rect(14, y, self.w - 28, 42)
                if rr.collidepoint(pos):
                    if dev.get("state") != "trying":
                        dev["connected"] = False
                        dev["state"] = "trying"
                        dev["started"] = pygame.time.get_ticks()
                    return
                y += 46
        elif self.state == "SETTINGS_SOUND":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_FULL"
                return
            ui = self.settings_sound_rects()
            if ui["volume"].collidepoint(pos):
                track = self.volume_track_rect(ui["volume"])
                ratio = clamp((pos[0] - track.x) / max(1, track.w), 0.0, 1.0)
                self.music_volume = float(ratio)
                self.video_volume = self.music_volume
                if self.mixer_ready:
                    pygame.mixer.music.set_volume(self.music_volume)
                self.save_pref()
                return
            if ui["eq"].collidepoint(pos):
                self.pending_back_transition = False
                self.state = "SETTINGS_EQ"
                return
        elif self.state == "SETTINGS_DISPLAY":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_FULL"
                return
            ui = self.settings_display_rects()
            for key, rr in ui["mode_buttons"].items():
                if rr.collidepoint(pos):
                    self.theme = key
                    self.save_pref()
                    self.toast(self.tr(f"theme.{key}"))
                    return
            if ui["bright_row"].collidepoint(pos):
                tr = ui["bright_track"]
                ratio = clamp((pos[0] - tr.x) / max(1, tr.w), 0.0, 1.0)
                self.brightness = int(round(40 + ratio * 60))
                self.save_pref()
                self.toast(f"{self.tr('settings.brightness')}: {self.brightness}%")
                return
        elif self.state == "SETTINGS_HOMELOCK":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_FULL"
                return
            ui = self.settings_homelock_rects()
            if ui["home_row"].collidepoint(pos):
                self.home_show_power = not self.home_show_power
                self.refresh_home_pages()
                self.save_pref()
                return
        elif self.state == "SETTINGS_GENERAL":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_FULL"
                return
            for key, _label, rr in self.settings_general_rows():
                if rr.collidepoint(pos):
                    self.pending_back_transition = False
                    if key == "language":
                        self.state = "SETTINGS_GENERAL_LANG"
                    elif key == "datetime":
                        self.state = "SETTINGS_GENERAL_DATETIME"
                    elif key == "reset":
                        self.state = "SETTINGS_GENERAL_RESET"
                    else:
                        self.state = "SETTINGS_GENERAL_KEYBOARD"
                    return
        elif self.state == "SETTINGS_GENERAL_LANG":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_GENERAL"
                return
            for code, _label, rect in self.settings_general_language_rows():
                if rect.collidepoint(pos):
                    self.set_language(code)
                    self.save_pref()
                    self.toast(self.tr(f"language.{code}"))
                    return
        elif self.state == "SETTINGS_GENERAL_DATETIME":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_GENERAL"
                return
            tf = self.settings_general_time_format_buttons()
            if tf["12"].collidepoint(pos):
                self.time_24h = False
                self.save_pref()
                self.toast(self.tr("time.12"))
                return
            if tf["24"].collidepoint(pos):
                self.time_24h = True
                self.save_pref()
                self.toast(self.tr("time.24"))
                return
        elif self.state == "SETTINGS_GENERAL_KEYBOARD":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_GENERAL"
                return
        elif self.state == "SETTINGS_GENERAL_RESET":
            if self.general_reset_confirm:
                btn = self.reset_confirm_buttons_current()
                if btn["no"].collidepoint(pos):
                    self.general_reset_confirm = ""
                    return
                if btn["yes"].collidepoint(pos):
                    if self.general_reset_confirm == "settings_once":
                        self.general_reset_confirm = ""
                        self.apply_factory_settings()
                        self.toast(self.tr("settings.reset.done.settings", default="모든 설정을 재설정했습니다"))
                    elif self.general_reset_confirm == "wipe_step1":
                        self.general_reset_confirm = "wipe_step2"
                        self.general_reset_confirm_start = pygame.time.get_ticks()
                    elif self.general_reset_confirm == "wipe_step2":
                        self.general_reset_confirm = ""
                        self.wipe_all_content_and_settings()
                        self.toast(self.tr("settings.reset.done.wipe", default="모든 콘텐츠 및 설정을 지웠습니다"))
                    return
                return
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_GENERAL"
                return
            for key, _label, rr in self.settings_general_reset_rows():
                if rr.collidepoint(pos):
                    if key == "settings":
                        self.general_reset_confirm = "settings_once"
                    else:
                        self.general_reset_confirm = "wipe_step1"
                    self.general_reset_confirm_start = pygame.time.get_ticks()
                    return
        elif self.state == "SETTINGS_INFO":
            if self.settings_info_name_popup_active:
                dlg = self.settings_info_name_dialog_rects()
                if dlg["cancel"].collidepoint(pos):
                    self.settings_info_name_popup_active = False
                    self.editing_name = False
                    return
                if dlg["ok"].collidepoint(pos):
                    self.settings_info_name_popup_active = False
                    self.editing_name = False
                    self.save_pref()
                    self.toast(self.tr("toast.name_saved"))
                    return
                return
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.editing_name = False
                self.state = "SETTINGS_FULL"
                return
            _r, _t, row_h = self.settings_info_scroll_info()
            ui = self.settings_info_edit_rects(scroll=self.list_scroll * row_h)
            if ui["name_row"].collidepoint(pos):
                self.settings_info_name_popup_active = True
                self.settings_info_name_popup_start = pygame.time.get_ticks()
                self.editing_name = True
                return
        elif self.state == "SETTINGS_BATTERY":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_FULL"
                return
            ui = self.settings_battery_rects()
            if ui["summary"].collidepoint(pos):
                self.fake_battery_charging = not self.fake_battery_charging
                self.save_pref()
                return
            if ui["saver"].collidepoint(pos):
                self.fake_battery_saver = not self.fake_battery_saver
                self.save_pref()
                return
        elif self.state == "SETTINGS_WALLSTYLE":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_FULL"
                return
            rr = self.settings_wallstyle_rects()
            if rr["wallpaper"].collidepoint(pos):
                self.pending_back_transition = False
                self.state = "SETTINGS_WALLPAPER"
                return
            if rr["accent"].collidepoint(pos):
                self.pending_back_transition = False
                self.state = "SETTINGS_ACCENT"
                return
        elif self.state == "SETTINGS_ACCENT":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_WALLSTYLE"
                return
            for key, _label, rr in self.settings_accent_rows():
                if rr.collidepoint(pos):
                    self.accent_key = key
                    self.save_pref()
                    self.toast(self.tr("settings.accent.changed", default="강조색이 변경되었습니다"))
                    return
        elif self.state == "SETTINGS_WALLPAPER":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_WALLSTYLE"
                return
            for item, rr in self.settings_wallpaper_rows():
                if rr.collidepoint(pos):
                    if item["kind"] == "custom":
                        self.photo_pick_wallpaper = True
                        self.state = "PHOTO"
                        self.photo_files = self.load_photo_files()
                        self.photo_info_cache.clear()
                        self.photo_view = "GRID"
                        self.photo_index = 0
                        self.set_list_scroll(0, snap=True)
                    else:
                        self.wallpaper = item["wallpaper_rel"]
                        loaded = self.load_wallpaper(self.wallpaper)
                        if loaded is None:
                            self.wallpaper = DEFAULT_WALLPAPER
                            loaded = self.load_wallpaper(self.wallpaper)
                        self.wallpaper_img = loaded
                        self.save_pref()
                        self.toast(self.tr("photo.toast.wallpaper_set", default="배경화면으로 지정했습니다"))
                    return
        elif self.state == "SETTINGS_EQ":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "SETTINGS_SOUND"
                return
            rows = self.settings_eq_rects()["rows"]
            for i, rr in enumerate(rows):
                if rr.collidepoint(pos):
                    self.eq_selected = i
                    return
        elif self.state == "POWER":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                self.state = "HOME"
        elif self.state == "MUSIC":
            if self.back_button_rect().collidepoint(pos):
                self.pending_back_transition = True
                if self.music_view == "MENU":
                    self.state = "HOME"
                elif self.music_view == "QUEUE":
                    self.music_view = "NOW"
                elif self.music_view == "LIST" and self.music_ctx_artist and self.music_ctx_album:
                    self.music_view = "ARTIST_ALBUMS"
                    self.music_ctx_album = None
                    self.set_list_scroll(0, snap=True)
                    self.music_search = ""
                    self.editing_music_search = False
                    self.sort_picker_open = False
                elif self.music_view == "LIST" and self.music_ctx_genre:
                    self.music_view = "GENRES"
                    self.music_ctx_genre = None
                    self.set_list_scroll(0, snap=True)
                    self.music_search = ""
                    self.editing_music_search = False
                    self.sort_picker_open = False
                else:
                    self.music_view = "MENU"
                    self.editing_music_search = False
                    self.music_ctx_artist = None
                    self.music_ctx_album = None
                    self.music_ctx_genre = None
                    self.sort_picker_open = False
                return

            if self.music_view == "MENU":
                menu = self.music_menu_rects()
                if menu["now"].collidepoint(pos):
                    self.music_view = "NOW"
                    self.editing_music_search = False
                    self.music_ctx_artist = None
                    self.music_ctx_album = None
                    self.music_ctx_genre = None
                    return
                if menu["list"].collidepoint(pos):
                    self.music_view = "LIST"
                    self.music_search = ""
                    self.editing_music_search = False
                    self.music_ctx_artist = None
                    self.music_ctx_album = None
                    self.music_ctx_genre = None
                    self.set_list_scroll(0, snap=True)
                    self.sort_picker_open = False
                    return
                if menu["albums"].collidepoint(pos):
                    self.music_view = "ALBUMS"
                    self.music_search = ""
                    self.editing_music_search = False
                    self.music_ctx_artist = None
                    self.music_ctx_album = None
                    self.music_ctx_genre = None
                    self.set_list_scroll(0, snap=True)
                    return
                if menu["artists"].collidepoint(pos):
                    self.music_view = "ARTISTS"
                    self.music_search = ""
                    self.editing_music_search = False
                    self.music_ctx_artist = None
                    self.music_ctx_album = None
                    self.music_ctx_genre = None
                    self.set_list_scroll(0, snap=True)
                    return
                if menu["genres"].collidepoint(pos):
                    self.music_view = "GENRES"
                    self.music_search = ""
                    self.editing_music_search = False
                    self.music_ctx_artist = None
                    self.music_ctx_album = None
                    self.music_ctx_genre = None
                    self.set_list_scroll(0, snap=True)
                    return
                return

            if self.music_view in ("ALBUMS", "ARTISTS", "ARTIST_ALBUMS", "GENRES"):
                if self.music_search_rect().collidepoint(pos):
                    self.editing_music_search = True
                    return
                rect = self.music_group_rect()
                if rect.collidepoint(pos):
                    row_h = 30
                    rel_y = pos[1] - rect.y
                    item_pos = self.list_scroll_index() + rel_y // row_h
                    if self.music_view == "ALBUMS":
                        kind = "album"
                        groups = self.group_items("album")
                    elif self.music_view == "ARTISTS":
                        kind = "artist"
                        groups = self.group_items("artist")
                    elif self.music_view == "GENRES":
                        kind = "genre"
                        groups = self.group_items("genre")
                    else:
                        kind = "album"
                        groups = self.group_items("album", artist_filter=self.music_ctx_artist)
                    if 0 <= item_pos < len(groups):
                        name, _cnt, _idx = groups[item_pos]
                        if self.music_view == "ARTISTS":
                            self.music_ctx_artist = name
                            self.music_ctx_album = None
                            self.music_ctx_genre = None
                            self.music_view = "ARTIST_ALBUMS"
                        elif self.music_view == "GENRES":
                            self.music_ctx_genre = name
                            self.music_ctx_artist = None
                            self.music_ctx_album = None
                            self.music_view = "LIST"
                        else:
                            if kind == "album":
                                self.music_ctx_album = name
                                self.music_ctx_genre = None
                            self.music_view = "LIST"
                        self.set_list_scroll(0, snap=True)
                        self.music_search = ""
                return

            if self.music_view == "LIST":
                if self.music_ctx_artist is None and self.music_ctx_album is None and self.music_ctx_genre is None:
                    if self.music_search_rect().collidepoint(pos):
                        self.editing_music_search = True
                        self.sort_picker_open = False
                        return
                    sort_btn = self.music_sort_button_rect()
                    if sort_btn.collidepoint(pos):
                        self.sort_picker_open = not self.sort_picker_open
                        self.editing_music_search = False
                        return
                    if self.sort_picker_open:
                        opts = self.music_sort_option_rects()
                        picked = None
                        for key, rect in opts.items():
                            if rect.collidepoint(pos):
                                picked = key
                                break
                        if picked:
                            self.music_sort = picked
                            self.queue_sort = self.music_sort
                            self.set_list_scroll(0, snap=True)
                            self.editing_music_search = False
                            self.sort_picker_open = False
                            self.save_pref()
                            return
                        self.sort_picker_open = False

                list_rect = self.music_list_rect()
                if list_rect.collidepoint(pos):
                    row_h = 30
                    rel_y = pos[1] - list_rect.y
                    filtered = self.filtered_music_indices()
                    item_pos = self.list_scroll_index() + rel_y // row_h
                    if 0 <= item_pos < len(filtered):
                        idx = filtered[item_pos]
                        self.set_queue_from_current_context()
                        self.play_track(idx, push_history=True, via_prev=False)
                        self.music_view = "NOW"
                        self.editing_music_search = False
                return

            if self.music_view == "QUEUE":
                list_rect = self.music_list_rect()
                if list_rect.collidepoint(pos):
                    row_h = 30
                    rel_y = pos[1] - list_rect.y
                    queue = self.play_queue_indices()
                    item_pos = self.list_scroll_index() + rel_y // row_h
                    if 0 <= item_pos < len(queue):
                        self.play_track(queue[item_pos], push_history=True, via_prev=False)
                        self.music_view = "NOW"
                return

            controls = self.music_control_rects()
            if self.music_progress_drag:
                self.music_progress_drag = False
                self.seek_music_to(self.music_progress_drag_pos, keep_paused=False)
                return
            if controls["queue"].collidepoint(pos):
                self.prev_button_last_tap = 0
                self.music_view = "QUEUE"
                queue = self.play_queue_indices()
                target = 0
                if queue and self.music_index in queue:
                    qpos = queue.index(self.music_index)
                    max_rows = max(1, self.music_list_rect().h // 30)
                    max_scroll = max(0, len(queue) - max_rows)
                    target = int(clamp(qpos - (max_rows // 2), 0, max_scroll))
                self.set_list_scroll(target, snap=True)
                return
            if controls["shuffle"].collidepoint(pos):
                self.prev_button_last_tap = 0
                self.shuffle_enabled = not self.shuffle_enabled
                self.save_pref()
                return
            if controls["repeat"].collidepoint(pos):
                self.prev_button_last_tap = 0
                cycle = {"all": "off", "off": "one", "one": "all"}
                self.repeat_mode = cycle[self.repeat_mode]
                self.save_pref()
                return
            if controls["prev"].collidepoint(pos):
                now_ms = pygame.time.get_ticks()
                if self.prev_chain_active:
                    self.prev_track()
                    self.prev_button_last_tap = 0
                elif now_ms - self.prev_button_last_tap <= 380:
                    self.prev_track()
                    self.prev_button_last_tap = 0
                else:
                    self.restart_current_track()
                    self.prev_button_last_tap = now_ms
                return
            if controls["play"].collidepoint(pos):
                self.prev_button_last_tap = 0
                self.prev_chain_active = False
                self.toggle_music()
                return
            if controls["next"].collidepoint(pos):
                self.prev_button_last_tap = 0
                self.next_track()
                return
            if controls["volume"].collidepoint(pos):
                self.prev_button_last_tap = 0
                track = self.volume_track_rect(controls["volume"])
                ratio = clamp((pos[0] - track.x) / track.w, 0.0, 1.0)
                self.music_volume = float(ratio)
                if self.mixer_ready:
                    pygame.mixer.music.set_volume(self.music_volume)
                self.save_pref()
                return

            prog = self.progress_rect()
            if prog.collidepoint(pos):
                ratio = clamp((pos[0] - prog.x) / prog.w, 0.0, 1.0)
                length = self.current_track_len()
                if length > 0.1 and self.music_files:
                    target = length * ratio
                    self.seek_music_to(target, keep_paused=False)
                return

    def draw_calculator(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        self.draw_icon_only(self.back_button_rect(), "back", "", False)

        display = self.calc_display_rect()
        panel = pygame.Surface((display.w, display.h), pygame.SRCALPHA)
        if self.theme == "light":
            panel_bg = (254, 255, 255, 252)
            panel_bd = (214, 220, 232, 255)
            expr_col = (122, 132, 150)
            value_col = (18, 24, 32)
            btn_bg = (245, 248, 253)
            btn_bd = (210, 217, 228)
            btn_txt = (26, 32, 42)
            op_txt = (152, 160, 176)
        elif self.theme == "transparent":
            panel_bg = (16, 20, 28, 176)
            panel_bd = (118, 132, 160, 220)
            expr_col = (194, 206, 228)
            value_col = (246, 248, 255)
            btn_bg = (28, 33, 43)
            btn_bd = (84, 96, 118)
            btn_txt = (242, 246, 255)
            op_txt = (236, 241, 250)
        else:
            panel_bg = (21, 25, 34, 248)
            panel_bd = (46, 54, 70, 255)
            expr_col = (168, 176, 194)
            value_col = (244, 247, 255)
            btn_bg = (28, 33, 43)
            btn_bd = (56, 64, 82)
            btn_txt = (242, 246, 255)
            op_txt = (236, 241, 250)
        pygame.draw.rect(panel, panel_bg, (0, 0, display.w, display.h), border_radius=20)
        pygame.draw.rect(panel, panel_bd, (0, 0, display.w, display.h), width=1, border_radius=20)
        self.screen.blit(panel, (display.x, display.y))

        ce = self.calc_ce_rect()
        ce_pressed = self.touch_down and ce.collidepoint(pygame.mouse.get_pos()) and not self.list_touch_drag
        ce_bg = btn_bg if self.theme != "light" else (240, 245, 252)
        ce_bd = btn_bd
        if ce_pressed:
            ce_bg = self.tone(ce_bg, -10)
        pygame.draw.rect(self.screen, ce_bg, ce, border_radius=10)
        pygame.draw.rect(self.screen, ce_bd, ce, width=1, border_radius=10)
        accent = self.ui_accent()
        ce_text = self.small_font.render("CE", True, accent)
        self.screen.blit(ce_text, (ce.centerx - ce_text.get_width() // 2, ce.centery - ce_text.get_height() // 2))

        if self.calc_prev_expr:
            expr_text = self.calc_prev_expr
            value_text = self.calc_display
            expr_render = self.calc_fit_text_surface(expr_text, 18, 11, expr_col, display.w - 88)
            value_render = self.calc_fit_text_surface(value_text, 40, 18, value_col, display.w - 28)
            self.screen.blit(expr_render, (display.right - 14 - expr_render.get_width(), display.y + 18))
            self.screen.blit(value_render, (display.right - 14 - value_render.get_width(), display.bottom - 16 - value_render.get_height()))
        else:
            big_text = self.calc_pretty_expr(self.calc_expr) if self.calc_expr else self.calc_display
            value_render = self.calc_fit_text_surface(big_text, 40, 18, value_col, display.w - 28)
            self.screen.blit(value_render, (display.right - 14 - value_render.get_width(), display.bottom - 16 - value_render.get_height()))

        for label, rect in self.calc_button_rects():
            pressed = self.touch_down and rect.collidepoint(pygame.mouse.get_pos()) and not self.list_touch_drag
            r = rect.move(0, 1 if pressed else 0)
            if label == "=":
                bg = accent
                bd = self.tone(accent, -20)
                tc = (255, 255, 255)
            else:
                bg = btn_bg
                bd = btn_bd
                if label == "C":
                    tc = accent
                elif label in ("÷", "×", "-", "+"):
                    bg = (220, 224, 230)
                    bd = (188, 195, 206)
                    tc = (0, 0, 0)
                else:
                    tc = btn_txt
            if pressed:
                bg = self.tone(bg, -10)
            pygame.draw.rect(self.screen, bg, r, border_radius=18)
            pygame.draw.rect(self.screen, bd, r, width=1, border_radius=18)
            text = self.title_font.render(label, True, tc)
            tx = r.centerx - text.get_width() // 2
            ty = r.centery - text.get_height() // 2
            self.screen.blit(text, (tx, ty))
        self.draw_toast()

    def draw_calendar(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        self.draw_icon_only(self.back_button_rect(), "back", "", False)

        hr = self.calendar_header_rect()
        nav = self.calendar_nav_rects()
        grid = self.calendar_grid_rect()
        accent = self.ui_accent()

        month_label = self.tr(
            "calendar.month_label",
            year=f"{self.calendar_year:04d}",
            month=f"{self.calendar_month:02d}",
            default=f"{self.calendar_year:04d}-{self.calendar_month:02d}",
        )
        title_rect = self.calendar_title_rect()
        title_pressed = self.touch_down and title_rect.collidepoint(pygame.mouse.get_pos()) and not self.list_touch_drag
        tr = title_rect.move(0, 1 if title_pressed else 0)
        tpanel = pygame.Surface((tr.w, tr.h), pygame.SRCALPHA)
        title_bg = self.tone(pal["button_bg"], -10) if title_pressed else pal["button_bg"]
        pygame.draw.rect(tpanel, title_bg + (110,), (0, 0, tr.w, tr.h), border_radius=12)
        self.screen.blit(tpanel, (tr.x, tr.y))
        title = self.title_font.render(month_label, True, pal["text"])
        self.screen.blit(title, (tr.centerx - title.get_width() // 2, tr.centery - title.get_height() // 2))

        for key in ("prev", "next"):
            enabled = self.calendar_can_prev() if key == "prev" else self.calendar_can_next()
            r = nav[key]
            pressed = self.touch_down and enabled and r.collidepoint(pygame.mouse.get_pos()) and not self.list_touch_drag
            rr = r.move(0, 1 if pressed else 0)
            bg = pal["button_bg"] if enabled else self.tone(pal["button_bg"], -8 if self.theme == "light" else 6)
            bd = pal["button_border"]
            tc = pal["text"] if enabled else self.tone(pal["text"], -70 if self.theme == "light" else -90)
            if pressed:
                bg = self.tone(bg, -10)
            pygame.draw.rect(self.screen, bg, rr, border_radius=10)
            pygame.draw.rect(self.screen, bd, rr, width=1, border_radius=10)
            arrow = "‹" if key == "prev" else "›"
            ts = self.title_font.render(arrow, True, tc)
            self.screen.blit(ts, (rr.centerx - ts.get_width() // 2, rr.centery - ts.get_height() // 2 - 1))

        panel = pygame.Surface((grid.w, grid.h), pygame.SRCALPHA)
        alpha = 236 if self.theme != "transparent" else 172
        pygame.draw.rect(panel, pal["panel_bg"] + (alpha,), (0, 0, grid.w, grid.h), border_radius=14)
        pygame.draw.rect(panel, pal["panel_border"] + (240,), (0, 0, grid.w, grid.h), width=1, border_radius=14)
        self.screen.blit(panel, (grid.x, grid.y))

        week_names = self.calendar_week_names()
        first_wk, day_count = calendar.monthrange(self.calendar_year, self.calendar_month)
        start_col = (first_wk + 1) % 7
        row_h = (grid.h - 30) // 7  # weekday row + 6 week rows
        col_w = grid.w // 7
        top = grid.y + 6
        for i, wd in enumerate(week_names):
            if i == 0:
                col = (214, 86, 86)
            elif i == 6:
                col = (88, 130, 224)
            else:
                col = self.tone(pal["text"], -30 if self.theme == "light" else -14)
            ws = self.small_font.render(wd, True, col)
            cx = grid.x + i * col_w + col_w // 2
            self.screen.blit(ws, (cx - ws.get_width() // 2, top))

        today = time.localtime()
        is_this_month = (today.tm_year == self.calendar_year and today.tm_mon == self.calendar_month)
        day = 1
        y0 = top + row_h
        for r in range(6):
            y = y0 + r * row_h
            for c in range(7):
                x = grid.x + c * col_w
                idx = r * 7 + c
                if idx < start_col or day > day_count:
                    continue
                if is_this_month and day == today.tm_mday:
                    dot = pygame.Rect(x + col_w // 2 - 13, y + row_h // 2 - 14, 26, 26)
                    pygame.draw.ellipse(self.screen, accent, dot)
                    dc = (255, 255, 255)
                else:
                    if c == 0:
                        dc = (214, 86, 86)
                    elif c == 6:
                        dc = (88, 130, 224)
                    else:
                        dc = pal["text"]
                ds = self.font.render(str(day), True, dc)
                self.screen.blit(ds, (x + col_w // 2 - ds.get_width() // 2, y + row_h // 2 - ds.get_height() // 2))
                day += 1

        self.draw_toast()

    def unlock_from_lock(self):
        route = self.lock_resume_route if isinstance(self.lock_resume_route, tuple) and self.lock_resume_route else ("HOME",)
        state = route[0] if route else "HOME"
        self.state = state
        if state == "MUSIC" and len(route) > 1:
            self.music_view = route[1]
        elif state == "VIDEO" and len(route) > 1:
            self.video_view = route[1]
        elif state == "TEXT" and len(route) > 1:
            self.text_view = route[1]
        elif state == "PHOTO" and len(route) > 1:
            self.photo_view = route[1]
        elif state == "FILES":
            if len(route) > 1:
                self.files_view = route[1]
            if len(route) > 2:
                self.files_source = route[2]
            if len(route) > 3:
                self.files_path = route[3]
        self.pending_back_transition = False
        self.power_confirm_active = False
        self.power_confirm_start = 0
        self.esc_hold_started = 0
        self.esc_hold_handled = False
        self.lock_unlock_fade_active = True
        self.lock_unlock_fade_start = pygame.time.get_ticks()
        self.lock_unlock_fade_alpha = 1.0

    def lock_date_text(self, tt):
        wd_ko = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        wd_ja = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        wd_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        mon_en = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        if self.lang == "ja":
            return f"{tt.tm_mon}月 {tt.tm_mday}日 {wd_ja[tt.tm_wday]}"
        if self.lang == "en":
            return f"{wd_en[tt.tm_wday]}, {mon_en[tt.tm_mon - 1]} {tt.tm_mday}"
        return f"{tt.tm_mon}월 {tt.tm_mday}일 {wd_ko[tt.tm_wday]}"

    def draw_lockscreen(self):
        if self.wallpaper_img:
            self.screen.blit(self.wallpaper_img, (0, 0))
        else:
            self.screen.fill((0, 0, 0))
        self.draw_statusbar()

        now = time.localtime()
        hm = time.strftime("%H:%M", now) if self.time_24h else time.strftime("%I:%M", now).lstrip("0") or "0:00"
        date_s = self.lock_date_text(now)
        t_shadow = self.lock_time_font.render(hm, True, (0, 0, 0))
        t = self.lock_time_font.render(hm, True, (246, 248, 255))
        d_shadow = self.lock_date_font.render(date_s, True, (0, 0, 0))
        d = self.lock_date_font.render(date_s, True, (220, 226, 238))
        tx = self.w // 2 - t.get_width() // 2
        ty = 56
        dx = self.w // 2 - d.get_width() // 2
        dy = 132
        self.screen.blit(t_shadow, (tx + 2, ty + 2))
        self.screen.blit(t, (tx, ty))
        self.screen.blit(d_shadow, (dx + 1, dy + 1))
        self.screen.blit(d, (dx, dy))

        is_playing = self.is_music_busy() and not self.music_paused
        if is_playing and self.music_files and (0 <= self.music_index < len(self.music_files)):
            music_bar = self.lock_music_bar_rect()
            panel_m = pygame.Surface((music_bar.w, music_bar.h), pygame.SRCALPHA)
            if self.theme == "light":
                panel_bg_m = (248, 250, 255, 205)
                panel_bd_m = (198, 206, 220, 210)
                title_col = (24, 30, 40)
                artist_col = (62, 72, 90)
                time_col = (52, 60, 76)
                prog_bg = (206, 214, 226)
            else:
                panel_bg_m = (18, 20, 26, 178)
                panel_bd_m = (90, 100, 122, 180)
                title_col = (236, 240, 248)
                artist_col = (190, 198, 214)
                time_col = (216, 222, 236)
                prog_bg = (74, 82, 98)
            prog_fill = self.ui_accent()
            pygame.draw.rect(panel_m, panel_bg_m, (0, 0, music_bar.w, music_bar.h), border_radius=16)
            pygame.draw.rect(panel_m, panel_bd_m, (0, 0, music_bar.w, music_bar.h), width=1, border_radius=16)
            self.screen.blit(panel_m, music_bar.topleft)

            art_size = 58
            art_r = pygame.Rect(music_bar.x + 10, music_bar.y + (music_bar.h - art_size) // 2, art_size, art_size)
            album_name = self.track_meta_for(self.music_index).get("album", "")
            art = self.album_art_for_album(album_name, size=art_size)
            self.screen.blit(art, art_r.topleft)

            meta = self.track_meta_for(self.music_index)
            title = meta.get("title", self.track_name(self.music_index))
            artist = meta.get("artist", self.tr("music.artist.unknown"))
            pos = self.current_track_pos()
            length = self.current_track_len()
            ratio = clamp(pos / max(1e-6, length), 0.0, 1.0) if length > 0.0 else 0.0

            text_x = art_r.right + 10
            text_right = music_bar.right - 10
            text_w = max(10, text_right - text_x)

            def fit_with_ellipsis(text, font, max_w):
                s = norm_text(text)
                if font.size(s)[0] <= max_w:
                    return s
                ell = "…"
                while s and font.size(s + ell)[0] > max_w:
                    s = s[:-1]
                return (s + ell) if s else ell

            title_text = fit_with_ellipsis(title, self.small_font, text_w)
            artist_text = fit_with_ellipsis(artist, self.small_font, text_w)
            title_s = self.small_font.render(title_text, True, title_col)
            artist_s = self.small_font.render(artist_text, True, artist_col)
            self.screen.blit(title_s, (text_x, music_bar.y + 8))
            self.screen.blit(artist_s, (text_x, music_bar.y + 26))

            prog_r = pygame.Rect(text_x, music_bar.y + 48, text_w, 5)
            pygame.draw.rect(self.screen, prog_bg, prog_r, border_radius=3)
            fill_w = max(0, int(prog_r.w * ratio))
            if fill_w > 0:
                pygame.draw.rect(self.screen, prog_fill, (prog_r.x, prog_r.y, fill_w, prog_r.h), border_radius=3)

            left_t = self.small_font.render(self.fmt_time(pos), True, time_col)
            right_t = self.small_font.render(self.fmt_time(length) if length > 0 else "--:--", True, time_col)
            ty = prog_r.bottom + 2
            self.screen.blit(left_t, (text_x, ty))
            self.screen.blit(right_t, (text_right - right_t.get_width(), ty))

        h = 82
        bar = self.lock_bottom_bar_rect()
        panel = pygame.Surface((bar.w, bar.h), pygame.SRCALPHA)
        if self.theme == "light":
            panel_bg = (248, 250, 255, 205)
            panel_bd = (198, 206, 220, 210)
            hint_col = (44, 52, 66)
        else:
            panel_bg = (18, 20, 26, 178)
            panel_bd = (90, 100, 122, 180)
            hint_col = (224, 230, 240)
        pygame.draw.rect(panel, panel_bg, (0, 0, bar.w, bar.h), border_radius=16)
        pygame.draw.rect(panel, panel_bd, (0, 0, bar.w, bar.h), width=1, border_radius=16)
        self.screen.blit(panel, bar.topleft)

        home_r = self.lock_home_button_rect()
        if self.lock_home_icon is not None:
            iw, ih = self.lock_home_icon.get_size()
            shadow = self.lock_home_icon.copy()
            shadow.fill((0, 0, 0, 95), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(shadow, (home_r.centerx - iw // 2, home_r.centery - ih // 2 + 2))
            self.screen.blit(self.lock_home_icon, (home_r.centerx - iw // 2, home_r.centery - ih // 2))
        else:
            pygame.draw.rect(self.screen, (220, 224, 232), home_r, border_radius=10)

        hint = self.tr("lock.hint.unlock", default="홈 버튼을 길게 누르거나 잠금버튼을 길게 눌러서 잠금 헤제")
        max_w = bar.right - (home_r.right + 10) - 4
        lines = []
        cur = ""
        for ch in hint:
            test = cur + ch
            if cur and self.small_font.size(test)[0] > max_w:
                lines.append(cur)
                cur = ch
            else:
                cur = test
        if cur:
            lines.append(cur)
        if len(lines) > 2:
            lines = lines[:2]
            tail = lines[-1]
            while tail and self.small_font.size(tail + "…")[0] > max_w:
                tail = tail[:-1]
            lines[-1] = (tail + "…") if tail else "…"
        line_h = self.small_font.get_linesize()
        start_y = bar.centery - (len(lines) * line_h) // 2
        for i, ln in enumerate(lines):
            hs = self.small_font.render(ln, True, hint_col)
            self.screen.blit(hs, (home_r.right + 10, start_y + i * line_h))

    # 홈 화면 렌더링(배경, 앱 아이콘, 페이지 인디케이터)
    def draw_home(self):
        self.ensure_wallpaper_valid()
        pal = self.pal()
        if self.wallpaper_img:
            self.screen.blit(self.wallpaper_img, (0, 0))
        else:
            self.screen.fill(pal["home_bg"])
        self.draw_statusbar()

        buttons = self.page_buttons()
        for b in buttons:
            if self.active_button and b.label == self.active_button.label:
                b.pressed = True
            b.draw(self.screen, self.small_font, pal)

        self.draw_pager()
        self.draw_toast()

    def draw_power_confirm_overlay(self):
        if not self.power_confirm_active:
            return
        pal = self.pal()
        p = clamp((pygame.time.get_ticks() - self.power_confirm_start) / max(1, self.power_confirm_ms), 0.0, 1.0)
        veil = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        veil.fill((0, 0, 0, int(140 * p)))
        self.screen.blit(veil, (0, 0))

        base = self.power_confirm_rect()
        scale = 0.92 + 0.08 * p
        ww = int(base.w * scale)
        hh = int(base.h * scale)
        rr = pygame.Rect(base.centerx - ww // 2, base.centery - hh // 2, ww, hh)
        pygame.draw.rect(self.screen, pal["panel_bg"], rr, border_radius=14)
        pygame.draw.rect(self.screen, pal["panel_border"], rr, width=1, border_radius=14)

        msg = self.font.render(self.tr("power.confirm", default="전원을 종료하시겠습니까?"), True, pal["text"])
        self.screen.blit(msg, (rr.centerx - msg.get_width() // 2, rr.y + 30))

        b = self.power_confirm_buttons()
        self.draw_select_button(b["no"], self.tr("common.no", default="아니요"), False)
        self.draw_select_button(b["yes"], self.tr("common.yes", default="네"), False)

    def draw_settings(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()

        title = self.title_font.render(self.tr("settings.title.quick", default="간편 설정"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))
        self.draw_settings_full_cards(pal)

        bar = self.settings_footer_rect()
        panel = pygame.Surface((bar.w, bar.h), pygame.SRCALPHA)
        panel_bg = self.tone(pal["panel_bg"], 4)
        panel_bd = pal["panel_border"]
        txt_col = pal["text"]
        pygame.draw.rect(panel, panel_bg, (0, 0, bar.w, bar.h), border_radius=16)
        pygame.draw.rect(panel, panel_bd, (0, 0, bar.w, bar.h), width=1, border_radius=16)
        self.screen.blit(panel, bar.topleft)

        icon_r = pygame.Rect(bar.x + 10, bar.y + 10, 62, 62)
        if self.settings_footer_icon is not None:
            iw, ih = self.settings_footer_icon.get_size()
            self.screen.blit(self.settings_footer_icon, (icon_r.centerx - iw // 2, icon_r.centery - ih // 2))

        footer_title = self.settings_footer_font.render(self.tr("settings.title.full", default="전체 설정"), True, txt_col)
        ty = bar.centery - footer_title.get_height() // 2
        self.screen.blit(footer_title, (icon_r.right + 12, ty))

        if self.settings_picker_active and self.settings_picker_options:
            p = clamp((pygame.time.get_ticks() - self.settings_picker_start) / max(1, self.settings_picker_ms), 0.0, 1.0)
            veil = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            veil.fill((0, 0, 0, int(140 * p)))
            self.screen.blit(veil, (0, 0))
            ss = self.settings_picker_rects()
            base = ss["panel"]
            scale = 0.92 + 0.08 * p
            ww = int(base.w * scale)
            hh = int(base.h * scale)
            rr = pygame.Rect(base.centerx - ww // 2, base.centery - hh // 2, ww, hh)
            pygame.draw.rect(self.screen, pal["panel_bg"], rr, border_radius=14)
            pygame.draw.rect(self.screen, pal["panel_border"], rr, width=1, border_radius=14)
            if self.settings_picker_kind == "language":
                title_txt = self.tr("settings.language")
            elif self.settings_picker_kind == "theme":
                title_txt = self.tr("settings.theme")
            elif self.settings_picker_kind == "time24":
                title_txt = self.tr("settings.time_format")
            else:
                title_txt = self.tr("settings.brightness")
            title = self.font.render(title_txt, True, pal["text"])
            self.screen.blit(title, (rr.centerx - title.get_width() // 2, rr.y + 10))
            by = rr.y - base.y
            selected_value = None
            if self.settings_picker_kind == "language":
                selected_value = self.lang
            elif self.settings_picker_kind == "theme":
                selected_value = self.theme
            elif self.settings_picker_kind == "time24":
                selected_value = self.time_24h
            for i, (label, _value) in enumerate(self.settings_picker_options):
                if i >= len(ss["options"]):
                    break
                self.draw_select_button(ss["options"][i].move(0, by), label, _value == selected_value)
            self.draw_select_button(ss["cancel"].move(0, by), self.tr("common.cancel", default="취소"), False)
        self.draw_toast()

    def draw_settings_full_cards(self, pal):
        rr = self.settings_full_rects()
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        value_col = self.tone(pal["text"], 16)

        def draw_row(rect, label, value):
            pygame.draw.rect(self.screen, row_bg, rect, border_radius=10)
            pygame.draw.rect(self.screen, row_bd, rect, width=1, border_radius=10)
            l = self.font.render(label, True, pal["text"])
            v = self.font.render(value, True, value_col)
            self.screen.blit(l, (rect.x + 10, rect.centery - l.get_height() // 2))
            self.screen.blit(v, (rect.right - 10 - v.get_width(), rect.centery - v.get_height() // 2))

        if self.lang == "ko":
            lang_label = self.tr("settings.language.mix.ko", default="언어/Language")
        elif self.lang == "ja":
            lang_label = self.tr("settings.language.mix.ja", default="言語/Language")
        else:
            lang_label = self.tr("settings.language.mix.en", default="Language")
        draw_row(rr["language"], lang_label, self.tr(f"language.{self.lang}", default=self.lang))
        draw_row(rr["theme"], self.tr("settings.display_mode", default="화면 모드"), self.tr(f"theme.{self.theme}", default=self.theme))

        br = rr["brightness"]
        pygame.draw.rect(self.screen, row_bg, br, border_radius=10)
        pygame.draw.rect(self.screen, row_bd, br, width=1, border_radius=10)
        lbl = self.font.render(self.tr("settings.brightness"), True, pal["text"])
        self.screen.blit(lbl, (br.x + 10, br.centery - lbl.get_height() // 2))
        self.draw_select_button(rr["brightness_minus"], "-", False)
        pygame.draw.rect(self.screen, pal["panel_bg"], rr["brightness_value"], border_radius=8)
        pygame.draw.rect(self.screen, pal["panel_border"], rr["brightness_value"], width=1, border_radius=8)
        bv = self.small_font.render(f"{self.brightness}%", True, pal["text"])
        self.screen.blit(
            bv,
            (rr["brightness_value"].centerx - bv.get_width() // 2, rr["brightness_value"].centery - bv.get_height() // 2),
        )
        self.draw_select_button(rr["brightness_plus"], "+", False)
        sr = rr["sound"]
        pygame.draw.rect(self.screen, row_bg, sr, border_radius=10)
        pygame.draw.rect(self.screen, row_bd, sr, width=1, border_radius=10)
        sl = self.font.render(self.tr("settings.sound", default="소리"), True, pal["text"])
        self.screen.blit(sl, (sr.x + 10, sr.centery - sl.get_height() // 2))
        self.draw_select_button(rr["sound_minus"], "-", False)
        pygame.draw.rect(self.screen, pal["panel_bg"], rr["sound_value"], border_radius=8)
        pygame.draw.rect(self.screen, pal["panel_border"], rr["sound_value"], width=1, border_radius=8)
        sv_pct = int(round(float(clamp(self.music_volume, 0.0, 1.0)) * 100.0))
        sv = self.small_font.render(f"{sv_pct}%", True, pal["text"])
        self.screen.blit(
            sv,
            (rr["sound_value"].centerx - sv.get_width() // 2, rr["sound_value"].centery - sv.get_height() // 2),
        )
        self.draw_select_button(rr["sound_plus"], "+", False)

    def draw_settings_controls(self, pal):
        lang_label = self.font.render(f"{self.tr('settings.language')}:", True, pal["text"])
        self.screen.blit(lang_label, (14, STATUS_H + 46))
        for code, rect in self.language_buttons():
            self.draw_select_button(rect, self.tr(f"language.{code}"), self.lang == code)

        theme_label = self.font.render(f"{self.tr('settings.theme')}:", True, pal["text"])
        self.screen.blit(theme_label, (14, STATUS_H + 116))
        for code, rect in self.theme_buttons():
            self.draw_select_button(rect, self.tr(f"theme.{code}"), self.theme == code)

        tf_label = self.font.render(f"{self.tr('settings.time_format')}:", True, pal["text"])
        self.screen.blit(tf_label, (14, STATUS_H + 180))
        tf = self.time_format_buttons()
        self.draw_select_button(tf["12"], self.tr("time.12"), not self.time_24h)
        self.draw_select_button(tf["24"], self.tr("time.24"), self.time_24h)

        bright_label = self.font.render(f"{self.tr('settings.brightness')}:", True, pal["text"])
        self.screen.blit(bright_label, (14, STATUS_H + 224))
        br = self.brightness_buttons()
        self.draw_select_button(br["minus"], "-", False)
        pygame.draw.rect(self.screen, pal["panel_bg"], br["value"], border_radius=8)
        pygame.draw.rect(self.screen, pal["panel_border"], br["value"], width=2, border_radius=8)
        val = self.small_font.render(f"{self.brightness}%", True, pal["text"])
        self.screen.blit(val, (br["value"].centerx - val.get_width() // 2, br["value"].centery - val.get_height() // 2))
        self.draw_select_button(br["plus"], "+", False)

        name_label = self.font.render(f"{self.tr('settings.name')}:", True, pal["text"])
        self.screen.blit(name_label, (14, STATUS_H + 294))
        name_box = pygame.Rect(14, STATUS_H + 320, 188, 34)
        name_bg = self.tone(pal["panel_bg"], 10) if self.editing_name else pal["panel_bg"]
        name_bd = (40, 120, 190) if (self.editing_name and self.theme == "light") else (
            (160, 200, 230) if self.editing_name else pal["panel_border"]
        )
        pygame.draw.rect(self.screen, name_bg, name_box, border_radius=8)
        pygame.draw.rect(self.screen, name_bd, name_box, width=2, border_radius=8)
        name_text = self.small_font.render(norm_text(self.device_name), True, pal["text"])
        self.screen.blit(name_text, (name_box.x + 8, name_box.y + 9))
        if self.editing_name and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = name_box.x + 8 + name_text.get_width() + 1
            cy = name_box.y + 7
            pygame.draw.line(self.screen, pal["text"], (cx, cy), (cx, cy + 18), 2)
        self.draw_select_button(
            self.name_edit_button(),
            self.tr("settings.done" if self.editing_name else "settings.edit"),
            self.editing_name,
        )

    def draw_settings_full(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.title", default="설정"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        for label, key, rr in self.settings_full_menu_rows():
            pygame.draw.rect(self.screen, row_bg, rr, border_radius=10)
            pygame.draw.rect(self.screen, row_bd, rr, width=1, border_radius=10)
            icon = self.settings_full_icons_24.get(key)
            if icon is not None:
                iw, ih = icon.get_size()
                self.screen.blit(icon, (rr.x + 10, rr.centery - ih // 2))
                tx = rr.x + 42
            else:
                tx = rr.x + 12
            txt = self.font.render(label, True, pal["text"])
            self.screen.blit(txt, (tx, rr.centery - txt.get_height() // 2))
            if key == "bluetooth":
                sw = self.settings_bt_toggle_rect(rr)
                if self.bt_enabled:
                    sw_bg = self.ui_accent()
                    knob_x = sw.right - sw.h + 1
                else:
                    sw_bg = self.tone(pal["panel_border"], 10)
                    knob_x = sw.x + 1
                pygame.draw.rect(self.screen, sw_bg, sw, border_radius=sw.h // 2)
                pygame.draw.rect(self.screen, self.tone(sw_bg, -18), sw, width=1, border_radius=sw.h // 2)
                knob = pygame.Rect(knob_x, sw.y + 1, sw.h - 2, sw.h - 2)
                pygame.draw.ellipse(self.screen, (250, 252, 255), knob)
        self.draw_toast()

    def draw_settings_bluetooth(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.bluetooth", default="Bluetooth"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))

        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        top = STATUS_H + 48
        main = pygame.Rect(14, top, self.w - 28, 46)
        pygame.draw.rect(self.screen, row_bg, main, border_radius=10)
        pygame.draw.rect(self.screen, row_bd, main, width=1, border_radius=10)
        sub = self.small_font.render(self.tr("bt.enabled", default="사용 중") if self.bt_enabled else self.tr("bt.disabled", default="사용 안 함"), True, self.tone(pal["text"], 35))
        self.screen.blit(sub, (main.x + 10, main.centery - sub.get_height() // 2))

        sw_w, sw_h = 46, 24
        sw = pygame.Rect(main.right - 10 - sw_w, main.centery - sw_h // 2, sw_w, sw_h)
        if self.bt_enabled:
            sw_bg = self.ui_accent()
            knob_x = sw.right - sw_h + 1
        else:
            sw_bg = self.tone(pal["panel_border"], 10)
            knob_x = sw.x + 1
        pygame.draw.rect(self.screen, sw_bg, sw, border_radius=sw_h // 2)
        pygame.draw.rect(self.screen, self.tone(sw_bg, -18), sw, width=1, border_radius=sw_h // 2)
        knob = pygame.Rect(knob_x, sw.y + 1, sw_h - 2, sw_h - 2)
        pygame.draw.ellipse(self.screen, (250, 252, 255), knob)

        scan = pygame.Rect(14, main.bottom + 8, self.w - 28, 40)
        self.draw_select_button(scan, self.tr("bt.scan", default="기기 검색"), False)
        if self.bt_scanning:
            p = clamp((pygame.time.get_ticks() - self.bt_scan_started) / max(1, self.bt_scan_ms), 0.0, 1.0)
            t = self.small_font.render(self.tr("bt.scan.progress", pct=int(p * 100), default=f"검색 중... {int(p*100)}%"), True, self.tone(pal["text"], 30))
            self.screen.blit(t, (scan.right - t.get_width() - 8, scan.centery - t.get_height() // 2))

        y = scan.bottom + 10
        for dev in self.bt_devices:
            rr = pygame.Rect(14, y, self.w - 28, 42)
            pygame.draw.rect(self.screen, row_bg, rr, border_radius=10)
            pygame.draw.rect(self.screen, row_bd, rr, width=1, border_radius=10)
            name = self.font.render(dev["name"], True, pal["text"])
            state = dev.get("state", "idle")
            if state == "trying":
                status_txt = self.tr("bt.status.trying", default="연결 시도 중")
            elif state == "failed":
                status_txt = self.tr("bt.status.failed", default="연결 실패")
            elif dev["connected"]:
                status_txt = self.tr("bt.status.connected", default="연결됨")
            else:
                status_txt = self.tr("bt.status.paired", default="페어링됨")
            status = self.small_font.render(status_txt, True, self.tone(pal["text"], 34))
            self.screen.blit(name, (rr.x + 10, rr.y + 6))
            self.screen.blit(status, (rr.x + 10, rr.y + 22))
            if state == "trying":
                action_txt = "..."
            else:
                action_txt = self.tr("bt.action.connect", default="연결") if not dev["connected"] else self.tr("bt.action.disconnect", default="해제")
            action = self.small_font.render(action_txt, True, pal["text"])
            self.screen.blit(action, (rr.right - 10 - action.get_width(), rr.centery - action.get_height() // 2))
            y += 46
        self.draw_toast()

    def draw_settings_sound(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.sound", default="소리"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))

        ui = self.settings_sound_rects()
        label = self.font.render(self.tr("settings.audio", default="음향"), True, pal["text"])
        self.screen.blit(label, (ui["title"].x, ui["title"].y))

        accent = self.ui_accent()
        v = ui["volume"]
        pygame.draw.rect(self.screen, (25, 25, 25), v, border_radius=6)
        pygame.draw.rect(self.screen, pal["panel_border"], v, width=1, border_radius=6)
        vt = self.volume_track_rect(v)
        vw = int(vt.w * self.music_volume)
        if vw > 0:
            pygame.draw.rect(self.screen, accent, (vt.x, vt.y, vw, vt.h), border_radius=6)
        knob_x = vt.x + int(vt.w * self.music_volume)
        pygame.draw.circle(self.screen, accent, (knob_x, vt.centery), 5)
        vol_key = "volume0"
        if self.music_volume >= 0.75:
            vol_key = "volume3"
        elif self.music_volume >= 0.45:
            vol_key = "volume2"
        elif self.music_volume > 0.0:
            vol_key = "volume1"
        self.draw_icon_only(pygame.Rect(v.x + 3, v.y + 1, 18, v.h - 2), vol_key, "", False, force_color=(255, 255, 255))

        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        eq = ui["eq"]
        pygame.draw.rect(self.screen, row_bg, eq, border_radius=10)
        pygame.draw.rect(self.screen, row_bd, eq, width=1, border_radius=10)
        txt = self.font.render(self.tr("settings.equalizer", default="이퀄라이저"), True, pal["text"])
        self.screen.blit(txt, (eq.x + 10, eq.centery - txt.get_height() // 2))
        arrow = self.small_font.render(">", True, self.tone(pal["text"], 40))
        self.screen.blit(arrow, (eq.right - 12 - arrow.get_width(), eq.centery - arrow.get_height() // 2))
        self.draw_toast()

    def draw_settings_eq(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.equalizer", default="이퀄라이저"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))

        ui = self.settings_eq_rects()
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        for i, rr in enumerate(ui["rows"]):
            active = i == self.eq_selected
            bg = self.tone(row_bg, 8) if active else row_bg
            bd = self.ui_accent() if active else row_bd
            pygame.draw.rect(self.screen, bg, rr, border_radius=10)
            pygame.draw.rect(self.screen, bd, rr, width=1, border_radius=10)
            name = self.font.render(self.eq_presets[i][0], True, pal["text"])
            self.screen.blit(name, (rr.x + 10, rr.centery - name.get_height() // 2))
            if active:
                chk = self.small_font.render(self.tr("common.selected", default="선택됨"), True, self.tone(pal["text"], 35))
                self.screen.blit(chk, (rr.right - 10 - chk.get_width(), rr.centery - chk.get_height() // 2))

        bars = ui["bars"]
        pygame.draw.rect(self.screen, row_bg, bars, border_radius=10)
        pygame.draw.rect(self.screen, row_bd, bars, width=1, border_radius=10)
        vals = self.eq_presets[self.eq_selected][1]
        n = len(vals)
        seg_w = bars.w // max(1, n)
        mid_y = bars.y + bars.h // 2
        pygame.draw.line(self.screen, self.tone(pal["text"], 70), (bars.x + 10, mid_y), (bars.right - 10, mid_y), 1)
        for i, v in enumerate(vals):
            cx = bars.x + seg_w * i + seg_w // 2
            h = int((bars.h * 0.35) * (abs(v) / 5.0))
            color = self.ui_accent()
            if v >= 0:
                yy = mid_y - h
                rh = h
            else:
                yy = mid_y
                rh = h
            pygame.draw.rect(self.screen, color, (cx - 10, yy, 20, max(2, rh)), border_radius=4)
        self.draw_toast()

    def draw_settings_display(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.display", default="디스플레이"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))

        ui = self.settings_display_rects()
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]

        mode_l = self.font.render(self.tr("settings.display_mode", default="화면 모드"), True, pal["text"])
        self.screen.blit(mode_l, (ui["mode_label"].x, ui["mode_label"].y))
        for key, rr in ui["mode_buttons"].items():
            self.draw_select_button(rr, self.tr(f"theme.{key}"), self.theme == key)

        bright_l = self.font.render(self.tr("settings.brightness"), True, pal["text"])
        self.screen.blit(bright_l, (ui["bright_label"].x, ui["bright_label"].y))
        br = ui["bright_row"]
        pygame.draw.rect(self.screen, row_bg, br, border_radius=10)
        pygame.draw.rect(self.screen, row_bd, br, width=1, border_radius=10)
        track = ui["bright_track"]
        pygame.draw.rect(self.screen, self.tone(pal["panel_bg"], -6), track, border_radius=6)
        ratio = clamp((self.brightness - 40) / 60.0, 0.0, 1.0)
        fill_w = int(track.w * ratio)
        if fill_w > 0:
            pygame.draw.rect(self.screen, self.ui_accent(), (track.x, track.y, fill_w, track.h), border_radius=6)
        knob_x = track.x + int(track.w * ratio)
        pygame.draw.circle(self.screen, self.ui_accent(), (knob_x, track.centery), 6)
        pygame.draw.rect(self.screen, pal["panel_bg"], ui["bright_value"], border_radius=8)
        pygame.draw.rect(self.screen, pal["panel_border"], ui["bright_value"], width=1, border_radius=8)
        bv = self.small_font.render(f"{self.brightness}", True, pal["text"])
        self.screen.blit(
            bv,
            (ui["bright_value"].centerx - bv.get_width() // 2, ui["bright_value"].centery - bv.get_height() // 2),
        )
        self.draw_toast()

    def draw_settings_homelock(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.home_lock", default="홈 화면 및 잠금화면"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))

        ui = self.settings_homelock_rects()
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]

        home_label = self.font.render(self.tr("settings.home", default="홈 화면"), True, pal["text"])
        self.screen.blit(home_label, (ui["home_label"].x, ui["home_label"].y))

        hr = ui["home_row"]
        pygame.draw.rect(self.screen, row_bg, hr, border_radius=10)
        pygame.draw.rect(self.screen, row_bd, hr, width=1, border_radius=10)
        txt = self.font.render(self.tr("settings.show_power_button", default="전원 버튼 보기"), True, pal["text"])
        self.screen.blit(txt, (hr.x + 10, hr.centery - txt.get_height() // 2))

        sw_w, sw_h = 42, 22
        sw = pygame.Rect(hr.right - 10 - sw_w, hr.centery - sw_h // 2, sw_w, sw_h)
        if self.home_show_power:
            sw_bg = self.ui_accent()
            knob_x = sw.right - sw_h + 1
        else:
            sw_bg = self.tone(pal["panel_border"], 10)
            knob_x = sw.x + 1
        pygame.draw.rect(self.screen, sw_bg, sw, border_radius=sw_h // 2)
        pygame.draw.rect(self.screen, self.tone(sw_bg, -18), sw, width=1, border_radius=sw_h // 2)
        knob = pygame.Rect(knob_x, sw.y + 1, sw_h - 2, sw_h - 2)
        pygame.draw.ellipse(self.screen, (250, 252, 255), knob)

        lock_label = self.font.render(self.tr("settings.lock_screen", default="잠금화면"), True, pal["text"])
        self.screen.blit(lock_label, (ui["lock_label"].x, ui["lock_label"].y))
        self.draw_toast()

    def draw_settings_general(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.general", default="일반"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        for _key, label, rr in self.settings_general_rows():
            pygame.draw.rect(self.screen, row_bg, rr, border_radius=10)
            pygame.draw.rect(self.screen, row_bd, rr, width=1, border_radius=10)
            txt = self.font.render(label, True, pal["text"])
            self.screen.blit(txt, (rr.x + 10, rr.centery - txt.get_height() // 2))
            arrow = self.small_font.render(">", True, self.tone(pal["text"], 40))
            self.screen.blit(arrow, (rr.right - 12 - arrow.get_width(), rr.centery - arrow.get_height() // 2))
        self.draw_toast()

    def draw_settings_general_language(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.language", default="언어"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        for code, label, rr in self.settings_general_language_rows():
            active = (self.lang == code)
            pygame.draw.rect(self.screen, self.tone(row_bg, 8) if active else row_bg, rr, border_radius=10)
            pygame.draw.rect(self.screen, self.ui_accent() if active else row_bd, rr, width=1, border_radius=10)
            txt = self.font.render(label, True, pal["text"])
            self.screen.blit(txt, (rr.x + 10, rr.centery - txt.get_height() // 2))
            if active:
                chk = self.small_font.render(self.tr("common.selected", default="선택됨"), True, self.tone(pal["text"], 35))
                self.screen.blit(chk, (rr.right - 10 - chk.get_width(), rr.centery - chk.get_height() // 2))
        self.draw_toast()

    def draw_settings_general_datetime(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.datetime", default="날짜 및 시간"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))
        now_tt = time.localtime()
        now_label = self.small_font.render(time.strftime("%Y-%m-%d %H:%M:%S", now_tt), True, self.tone(pal["text"], 35))
        self.screen.blit(now_label, (14, STATUS_H + 48))
        tf_label = self.font.render(f"{self.tr('settings.time_format')}:", True, pal["text"])
        self.screen.blit(tf_label, (14, STATUS_H + 86))
        tf = self.settings_general_time_format_buttons()
        self.draw_select_button(tf["12"], self.tr("time.12"), not self.time_24h)
        self.draw_select_button(tf["24"], self.tr("time.24"), self.time_24h)
        self.draw_toast()

    def draw_settings_general_keyboard(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.keyboard", default="키보드"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        rows = [
            (self.tr("settings.keyboard.default", default="기본 키보드"), "PyKey"),
            (self.tr("settings.keyboard.input_lang", default="입력 언어"), self.tr("settings.keyboard.input_lang.value", default="한국어 / English / 日本語")),
        ]
        y = STATUS_H + 48
        for label, value in rows:
            rr = pygame.Rect(14, y, self.w - 28, 42)
            pygame.draw.rect(self.screen, row_bg, rr, border_radius=10)
            pygame.draw.rect(self.screen, row_bd, rr, width=1, border_radius=10)
            lt = self.font.render(label, True, pal["text"])
            vt = self.small_font.render(value, True, self.tone(pal["text"], 35))
            self.screen.blit(lt, (rr.x + 10, rr.centery - lt.get_height() // 2))
            self.screen.blit(vt, (rr.right - 10 - vt.get_width(), rr.centery - vt.get_height() // 2))
            y += 46
        self.draw_toast()

    def draw_settings_general_reset(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.device_reset", default="기기 재설정"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        for _key, label, rr in self.settings_general_reset_rows():
            pygame.draw.rect(self.screen, row_bg, rr, border_radius=10)
            pygame.draw.rect(self.screen, row_bd, rr, width=1, border_radius=10)
            txt = self.font.render(label, True, pal["text"])
            self.screen.blit(txt, (rr.x + 10, rr.centery - txt.get_height() // 2))
            arrow = self.small_font.render(">", True, self.tone(pal["text"], 40))
            self.screen.blit(arrow, (rr.right - 12 - arrow.get_width(), rr.centery - arrow.get_height() // 2))

        if self.general_reset_confirm:
            p = clamp(
                (pygame.time.get_ticks() - self.general_reset_confirm_start) / max(1, self.general_reset_confirm_ms),
                0.0,
                1.0,
            )
            veil = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            veil.fill((0, 0, 0, int(140 * p)))
            self.screen.blit(veil, (0, 0))
            base = self.reset_confirm_rect()
            scale = 0.92 + 0.08 * p
            ww = int(base.w * scale)
            hh = int(base.h * scale)
            rr = pygame.Rect(base.centerx - ww // 2, base.centery - hh // 2, ww, hh)
            pygame.draw.rect(self.screen, pal["panel_bg"], rr, border_radius=14)
            pygame.draw.rect(self.screen, pal["panel_border"], rr, width=1, border_radius=14)
            if self.general_reset_confirm == "settings_once":
                lines = [self.tr("settings.reset.confirm.settings", default="모든 설정을 재설정하시겠습니까?")]
            elif self.general_reset_confirm == "wipe_step1":
                lines = [self.tr("settings.reset.confirm.wipe.1", default="모든 콘텐츠 및 설정을"), self.tr("settings.reset.confirm.wipe.2", default="지우시겠습니까?")]
            else:
                lines = [self.tr("settings.reset.confirm.final.1", default="정말로 계속하시겠습니까?"), self.tr("settings.reset.confirm.final.2", default="이 작업은 되돌릴 수 없습니다.")]
            y = rr.y + 28
            for ln in lines:
                t = self.font.render(ln, True, pal["text"])
                self.screen.blit(t, (rr.centerx - t.get_width() // 2, y))
                y += 22
            b = {
                "no": pygame.Rect(rr.x + 16, rr.bottom - 42, 108, 30),
                "yes": pygame.Rect(rr.right - 124, rr.bottom - 42, 108, 30),
            }
            self.draw_select_button(b["no"], self.tr("common.no", default="아니요"), False)
            self.draw_select_button(b["yes"], self.tr("common.yes", default="네"), False)
        self.draw_toast()

    def draw_settings_info(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.device_info", default="디바이스 정보"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))
        viewport = self.settings_info_scroll_rect()
        rect, total, row_h = self.settings_info_scroll_info()
        max_rows = self.scroll_page_rows(rect, row_h)
        max_scroll = float(max(0, total - max_rows))
        self.list_scroll = float(clamp(self.list_scroll, 0.0, max_scroll))
        self.list_scroll_target = float(clamp(self.list_scroll_target, 0.0, max_scroll))
        scroll = self.list_scroll * row_h
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(viewport)
        y = STATUS_H + 48 - int(scroll)

        basic_label = self.font.render(self.tr("settings.device_info.basic", default="기본 정보"), True, pal["text"])
        self.screen.blit(basic_label, (14, y))
        y += 24
        ui = self.settings_info_edit_rects(scroll=scroll)
        rr = ui["name_row"]
        name_bg = self.tone(row_bg, 8) if self.editing_name else row_bg
        name_bd = self.ui_accent() if self.editing_name else row_bd
        pygame.draw.rect(self.screen, name_bg, rr, border_radius=10)
        pygame.draw.rect(self.screen, name_bd, rr, width=1, border_radius=10)
        lt = self.font.render(self.tr("settings.name", default="기기 이름"), True, pal["text"])
        self.screen.blit(lt, (rr.x + 10, rr.centery - lt.get_height() // 2))
        arrow = self.small_font.render(">", True, self.tone(pal["text"], 40))
        arrow_x = rr.right - 10 - arrow.get_width()
        self.screen.blit(arrow, (arrow_x, rr.centery - arrow.get_height() // 2))
        value_left = rr.x + 10 + lt.get_width() + 12
        value_right = arrow_x - 8
        max_vw = max(16, value_right - value_left)
        value_txt = norm_text(self.device_name)
        if value_txt and self.small_font.size(value_txt)[0] > max_vw:
            ell = "…"
            while value_txt and self.small_font.size(value_txt + ell)[0] > max_vw:
                value_txt = value_txt[:-1]
            value_txt = (value_txt + ell) if value_txt else ell
        vt = self.small_font.render(value_txt, True, self.tone(pal["text"], 35))
        self.screen.blit(vt, (value_right - vt.get_width(), rr.centery - vt.get_height() // 2))
        y = rr.bottom + 8

        y += 8
        detail_label = self.font.render(self.tr("settings.device_info.detail", default="기기 세부 정보"), True, pal["text"])
        self.screen.blit(detail_label, (14, y))
        y += 24
        for label, value in [
            (self.tr("settings.device_info.product"), self.device_model),
            (self.tr("settings.device_info.model_name"), self.device_model_name),
            (self.tr("settings.device_info.serial_number"), self.serial_number),
            (self.tr("settings.device_info.bt_address"), self.bt_address),
        ]:
            rr = pygame.Rect(14, y, self.w - 28, 42)
            pygame.draw.rect(self.screen, row_bg, rr, border_radius=10)
            pygame.draw.rect(self.screen, row_bd, rr, width=1, border_radius=10)
            lt = self.font.render(label, True, pal["text"])
            vt = self.small_font.render(norm_text(value), True, self.tone(pal["text"], 35))
            self.screen.blit(lt, (rr.x + 10, rr.centery - lt.get_height() // 2))
            self.screen.blit(vt, (rr.right - 10 - vt.get_width(), rr.centery - vt.get_height() // 2))
            y += 46

        y += 8
        sw_label = self.font.render(self.tr("settings.device_info.software", default="소프트웨어 정보"), True, pal["text"])
        self.screen.blit(sw_label, (14, y))
        y += 24
        rr = pygame.Rect(14, y, self.w - 28, 42)
        pygame.draw.rect(self.screen, row_bg, rr, border_radius=10)
        pygame.draw.rect(self.screen, row_bd, rr, width=1, border_radius=10)
        lt = self.font.render(self.tr("settings.device_info.version", default="버전"), True, pal["text"])
        vt = self.small_font.render(SOFTWARE_INFO_VERSION, True, self.tone(pal["text"], 35))
        self.screen.blit(lt, (rr.x + 10, rr.centery - lt.get_height() // 2))
        self.screen.blit(vt, (rr.right - 10 - vt.get_width(), rr.centery - vt.get_height() // 2))
        y = rr.bottom + 8

        usage_label = self.font.render(self.tr("settings.device_info.usage_storage"), True, pal["text"])
        self.screen.blit(usage_label, (14, y))
        y += 22
        section_items = [
            (self.tr("settings.device_info.usage.music"), len(self.music_files)),
            (self.tr("settings.device_info.usage.video"), len(self.video_files)),
            (self.tr("settings.device_info.usage.photo"), len(self.photo_files)),
            (self.tr("settings.device_info.usage.document"), len(self.text_files)),
        ]

        storage_root = os.path.join(BASE_DIR, "files")
        if not os.path.isdir(storage_root):
            storage_root = BASE_DIR
        try:
            du = shutil.disk_usage(storage_root)
            total_space = self.format_file_size(du.total)
            free_space = self.format_file_size(du.free)
        except Exception:
            total_space = "0B"
            free_space = "0B"

        storage_items = [
            (self.tr("settings.device_info.storage.total"), total_space),
            (self.tr("settings.device_info.storage.available"), free_space),
        ]
        section_items.extend(storage_items)
        for label, value in section_items:
            item_rr = pygame.Rect(14, y, self.w - 28, 42)
            pygame.draw.rect(self.screen, row_bg, item_rr, border_radius=10)
            pygame.draw.rect(self.screen, row_bd, item_rr, width=1, border_radius=10)
            lt = self.font.render(label, True, pal["text"])
            vt = self.small_font.render(str(value), True, self.tone(pal["text"], 35))
            self.screen.blit(lt, (item_rr.x + 10, item_rr.centery - lt.get_height() // 2))
            self.screen.blit(vt, (item_rr.right - 10 - vt.get_width(), item_rr.centery - vt.get_height() // 2))
            y += 46
        self.screen.set_clip(prev_clip)

        if self.settings_info_name_popup_active:
            p = clamp((pygame.time.get_ticks() - self.settings_info_name_popup_start) / max(1, self.settings_info_name_popup_ms), 0.0, 1.0)
            veil = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            veil.fill((0, 0, 0, int(140 * p)))
            self.screen.blit(veil, (0, 0))
            base = self.settings_info_name_dialog_rects()["panel"]
            scale = 0.92 + 0.08 * p
            ww = int(base.w * scale)
            hh = int(base.h * scale)
            rrp = pygame.Rect(base.centerx - ww // 2, base.centery - hh // 2, ww, hh)
            pygame.draw.rect(self.screen, pal["panel_bg"], rrp, border_radius=14)
            pygame.draw.rect(self.screen, pal["panel_border"], rrp, width=1, border_radius=14)
            title = self.font.render(self.tr("settings.name", default="기기 이름"), True, pal["text"])
            self.screen.blit(title, (rrp.centerx - title.get_width() // 2, rrp.y + 12))
            input_rect = pygame.Rect(rrp.x + 14, rrp.y + 58, rrp.w - 28, 34)
            pygame.draw.rect(self.screen, self.tone(pal["panel_bg"], 8), input_rect, border_radius=8)
            pygame.draw.rect(self.screen, pal["panel_border"], input_rect, width=2, border_radius=8)
            txt = norm_text(self.device_name)
            max_w = input_rect.w - 16
            while txt and self.small_font.size(txt)[0] > max_w:
                txt = txt[1:]
            name_s = self.small_font.render(txt, True, pal["text"])
            self.screen.blit(name_s, (input_rect.x + 8, input_rect.centery - name_s.get_height() // 2))
            if self.editing_name and (pygame.time.get_ticks() // 500) % 2 == 0:
                cx = input_rect.x + 8 + name_s.get_width() + 1
                pygame.draw.line(self.screen, pal["text"], (cx, input_rect.y + 6), (cx, input_rect.y + 26), 2)
            b = {
                "cancel": pygame.Rect(rrp.x + 16, rrp.bottom - 42, 108, 30),
                "ok": pygame.Rect(rrp.right - 124, rrp.bottom - 42, 108, 30),
            }
            self.draw_select_button(b["cancel"], self.tr("common.cancel", default="취소"), False)
            self.draw_select_button(b["ok"], self.tr("common.change", default="변경"), False)
        self.draw_toast()

    def draw_settings_battery(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.battery", default="배터리"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))

        ui = self.settings_battery_rects()
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]

        sm = ui["summary"]
        pygame.draw.rect(self.screen, row_bg, sm, border_radius=10)
        pygame.draw.rect(self.screen, row_bd, sm, width=1, border_radius=10)
        pct = self.title_font.render(f"{self.fake_battery_level}%", True, pal["text"])
        self.screen.blit(pct, (sm.x + 10, sm.y + 6))
        st_txt = self.tr("battery.status.charging", default="충전 중") if self.fake_battery_charging else self.tr("battery.status.in_use", default="사용 중")
        st = self.small_font.render(st_txt, True, self.tone(pal["text"], 35))
        self.screen.blit(st, (sm.x + 12, sm.bottom - 18))
        eta_h = max(1, int((self.fake_battery_level / 100.0) * (self.fake_battery_health / 100.0) * 150))
        eta = self.small_font.render(self.tr("battery.eta.hours", hours=eta_h, default=f"예상 사용 가능: 약 {eta_h}시간"), True, self.tone(pal["text"], 35))
        self.screen.blit(eta, (sm.right - eta.get_width() - 10, sm.centery - eta.get_height() // 2))

        sv = ui["saver"]
        pygame.draw.rect(self.screen, row_bg, sv, border_radius=10)
        pygame.draw.rect(self.screen, row_bd, sv, width=1, border_radius=10)
        sv_t = self.font.render(self.tr("battery.saver", default="절전 모드"), True, pal["text"])
        self.screen.blit(sv_t, (sv.x + 10, sv.centery - sv_t.get_height() // 2))
        sw_w, sw_h = 42, 22
        sw = pygame.Rect(sv.right - 10 - sw_w, sv.centery - sw_h // 2, sw_w, sw_h)
        if self.fake_battery_saver:
            sw_bg = self.ui_accent()
            knob_x = sw.right - sw_h + 1
        else:
            sw_bg = self.tone(pal["panel_border"], 10)
            knob_x = sw.x + 1
        pygame.draw.rect(self.screen, sw_bg, sw, border_radius=sw_h // 2)
        pygame.draw.rect(self.screen, self.tone(sw_bg, -18), sw, width=1, border_radius=sw_h // 2)
        knob = pygame.Rect(knob_x, sw.y + 1, sw_h - 2, sw_h - 2)
        pygame.draw.ellipse(self.screen, (250, 252, 255), knob)

        hl = ui["health"]
        pygame.draw.rect(self.screen, row_bg, hl, border_radius=10)
        pygame.draw.rect(self.screen, row_bd, hl, width=1, border_radius=10)
        hl_t = self.font.render(self.tr("battery.health", default="배터리 성능 상태"), True, pal["text"])
        self.screen.blit(hl_t, (hl.x + 10, hl.centery - hl_t.get_height() // 2))
        hl_v = self.small_font.render(f"{self.fake_battery_health}%", True, self.tone(pal["text"], 35))
        self.screen.blit(hl_v, (hl.right - 10 - hl_v.get_width(), hl.centery - hl_v.get_height() // 2))
        self.draw_toast()

    def draw_settings_wallstyle(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.wallpaper_style", default="배경화면 및 스타일"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        rr = self.settings_wallstyle_rects()
        for key, label, current in (
            ("wallpaper", self.tr("settings.wallpaper", default="배경화면"), self.current_wallpaper_label()),
            ("accent", self.tr("settings.accent", default="강조색"), self.current_accent_label()),
        ):
            r = rr[key]
            pygame.draw.rect(self.screen, row_bg, r, border_radius=10)
            pygame.draw.rect(self.screen, row_bd, r, width=1, border_radius=10)
            txt = self.font.render(label, True, pal["text"])
            self.screen.blit(txt, (r.x + 10, r.centery - txt.get_height() // 2))
            cur = self.small_font.render(current, True, self.tone(pal["text"], 35))
            cx = r.right - 26 - cur.get_width()
            if cx < r.x + 110:
                cx = r.x + 110
            self.screen.blit(cur, (cx, r.centery - cur.get_height() // 2))
            arrow = self.small_font.render(">", True, self.tone(pal["text"], 40))
            self.screen.blit(arrow, (r.right - 12 - arrow.get_width(), r.centery - arrow.get_height() // 2))
        self.draw_toast()

    def draw_settings_accent(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.accent.change", default="강조색 변경"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        for key, label, rr in self.settings_accent_rows():
            active = (self.accent_key == key)
            pygame.draw.rect(self.screen, self.tone(row_bg, 8) if active else row_bg, rr, border_radius=10)
            pygame.draw.rect(self.screen, self.ui_accent() if active else row_bd, rr, width=1, border_radius=10)
            dot = pygame.Rect(rr.x + 10, rr.y + 9, 24, 24)
            pygame.draw.ellipse(self.screen, ACCENT_PRESETS[key], dot)
            txt = self.font.render(label, True, pal["text"])
            self.screen.blit(txt, (rr.x + 42, rr.centery - txt.get_height() // 2))
            if active:
                chk = self.small_font.render(self.tr("common.selected", default="선택됨"), True, self.tone(pal["text"], 35))
                self.screen.blit(chk, (rr.right - 10 - chk.get_width(), rr.centery - chk.get_height() // 2))
        self.draw_toast()

    def draw_settings_wallpaper(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("settings.wallpaper.change", default="배경화면 변경"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 12))
        row_bg = self.tone(pal["panel_bg"], 4)
        row_bd = pal["panel_border"]
        cur_abs = os.path.abspath(self.resolve_wallpaper_path())
        defaults_abs = {
            os.path.abspath(os.path.join(BASE_DIR, os.path.join("system", "UI", "default1.png"))),
            os.path.abspath(os.path.join(BASE_DIR, os.path.join("system", "UI", "default2.png"))),
            os.path.abspath(os.path.join(BASE_DIR, os.path.join("system", "UI", "default3.png"))),
        }
        for item, rr in self.settings_wallpaper_rows():
            if item["kind"] == "custom":
                active = cur_abs not in defaults_abs
            else:
                full = os.path.abspath(os.path.join(BASE_DIR, item["wallpaper_rel"]))
                active = (full == cur_abs)
            pygame.draw.rect(self.screen, self.tone(row_bg, 8) if active else row_bg, rr, border_radius=10)
            pygame.draw.rect(self.screen, self.ui_accent() if active else row_bd, rr, width=1, border_radius=10)
            thumb_size = rr.h - 10
            thumb = self.wallpaper_thumb_for_picker(item["thumb_path"], thumb_size)
            tx = rr.x + 6
            ty = rr.y + (rr.h - thumb_size) // 2
            thumb_rect = pygame.Rect(tx, ty, thumb_size, thumb_size)
            self.screen.blit(thumb, thumb_rect.topleft)
            pygame.draw.rect(self.screen, self.tone(row_bd, 10), thumb_rect, width=1, border_radius=8)
            txt = item["label"]
            max_w = rr.w - (thumb_size + 34)
            while txt and self.font.size(txt)[0] > max_w:
                txt = txt[:-1]
            if txt != item["label"] and len(txt) >= 2:
                txt = txt[:-1] + "…"
            t = self.font.render(txt, True, pal["text"])
            self.screen.blit(t, (thumb_rect.right + 10, rr.centery - t.get_height() // 2))
        self.draw_toast()

    def handle_settings_controls_click(self, pos):
        for code, rect in self.language_buttons():
            if rect.collidepoint(pos):
                self.set_language(code)
                self.save_pref()
                self.toast(self.tr(f"language.{code}"))
                return True

        for code, rect in self.theme_buttons():
            if rect.collidepoint(pos):
                self.theme = code
                self.save_pref()
                self.toast(self.tr(f"theme.{code}"))
                return True

        tf = self.time_format_buttons()
        if tf["12"].collidepoint(pos):
            self.time_24h = False
            self.save_pref()
            self.toast(self.tr("time.12"))
            return True
        if tf["24"].collidepoint(pos):
            self.time_24h = True
            self.save_pref()
            self.toast(self.tr("time.24"))
            return True

        br = self.brightness_buttons()
        if br["minus"].collidepoint(pos):
            self.brightness = int(clamp(self.brightness - 10, 40, 100))
            self.save_pref()
            self.toast(f"{self.tr('settings.brightness')}: {self.brightness}%")
            return True
        if br["plus"].collidepoint(pos):
            self.brightness = int(clamp(self.brightness + 10, 40, 100))
            self.save_pref()
            self.toast(f"{self.tr('settings.brightness')}: {self.brightness}%")
            return True

        if self.name_edit_button().collidepoint(pos):
            self.editing_name = not self.editing_name
            if not self.editing_name:
                self.save_pref()
                self.toast(self.tr("toast.name_saved"))
            return True
        return False

    def handle_settings_full_click(self, pos):
        rr = self.settings_full_rects()
        if rr["language"].collidepoint(pos):
            self.begin_settings_picker("language")
            return True
        if rr["theme"].collidepoint(pos):
            self.begin_settings_picker("theme")
            return True
        if rr["brightness_minus"].collidepoint(pos):
            self.brightness = int(clamp(self.brightness - 10, 40, 100))
            self.save_pref()
            self.toast(f"{self.tr('settings.brightness')}: {self.brightness}%")
            return True
        if rr["brightness_plus"].collidepoint(pos):
            self.brightness = int(clamp(self.brightness + 10, 40, 100))
            self.save_pref()
            self.toast(f"{self.tr('settings.brightness')}: {self.brightness}%")
            return True
        if rr["sound_minus"].collidepoint(pos):
            self.music_volume = float(clamp(self.music_volume - 0.1, 0.0, 1.0))
            self.video_volume = self.music_volume
            if self.mixer_ready:
                pygame.mixer.music.set_volume(self.music_volume)
            self.save_pref()
            return True
        if rr["sound_plus"].collidepoint(pos):
            self.music_volume = float(clamp(self.music_volume + 0.1, 0.0, 1.0))
            self.video_volume = self.music_volume
            if self.mixer_ready:
                pygame.mixer.music.set_volume(self.music_volume)
            self.save_pref()
            return True
        return False

    def draw_power(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["power_bg"])
        else:
            self.screen.fill(pal["power_bg"])
        self.draw_statusbar()
        txt = self.font.render(self.tr("power.hint"), True, pal["power_text"])
        self.screen.blit(txt, (14, STATUS_H + 30))
        self.draw_toast()

    # 비디오 앱 렌더링(목록/플레이어 UI)
    def draw_video(self):
        if self.video_view == "PLAYER":
            pal = THEMES["dark"]
            self.screen.fill((0, 0, 0))
            filtered = self.filtered_video_files()
            if not filtered:
                self.video_view = "LIST"
                self.draw_toast()
                return
            self.video_index = int(clamp(self.video_index, 0, len(filtered) - 1))
            path = filtered[self.video_index]
            meta = self.video_meta_for(path)
            layout = self.video_player_rects()

            frame = None
            if self.video_frame_surface:
                frame = self.video_frame_surface
            else:
                frame = self.video_thumbnail_for(path, layout["art"].w)
            frame = self.rotated_video_surface(frame)
            if frame:
                fw, fh = frame.get_size()
                art = layout["art"]
                scale = min(art.w / max(1, fw), art.h / max(1, fh))
                if abs(scale - 1.0) > 1e-3:
                    nw = max(1, int(fw * scale))
                    nh = max(1, int(fh * scale))
                    frame = pygame.transform.smoothscale(frame, (nw, nh))
                    fw, fh = frame.get_size()
                fx = art.x + (art.w - fw) // 2
                fy = art.y + (art.h - fh) // 2
                self.screen.blit(frame, (fx, fy))

            ui = self.video_ui_touch_rects()
            if self.video_ui_progress > 0.01:
                top_bar = pygame.Surface((ui["top_bar"].w, ui["top_bar"].h), pygame.SRCALPHA)
                top_bar.fill((0, 0, 0, 120))
                self.screen.blit(top_bar, (ui["top_bar"].x, ui["top_bar"].y))
                if ui.get("mode") == "landscape":
                    lx = ui["top_bar"].right - 1 if not ui.get("flip") else ui["top_bar"].x
                    pygame.draw.line(self.screen, (74, 74, 78), (lx, ui["top_bar"].y), (lx, ui["top_bar"].bottom))
                else:
                    pygame.draw.line(
                        self.screen,
                        (74, 74, 78),
                        (ui["top_bar"].x, ui["top_bar"].bottom - 1),
                        (ui["top_bar"].right, ui["top_bar"].bottom - 1),
                    )

                bottom_bar = pygame.Surface((ui["bottom_bar"].w, ui["bottom_bar"].h), pygame.SRCALPHA)
                bottom_bar.fill((0, 0, 0, 120))
                self.screen.blit(bottom_bar, (ui["bottom_bar"].x, ui["bottom_bar"].y))
                if ui.get("mode") == "landscape":
                    lx = ui["bottom_bar"].x if not ui.get("flip") else ui["bottom_bar"].right - 1
                    pygame.draw.line(self.screen, (74, 74, 78), (lx, ui["bottom_bar"].y), (lx, ui["bottom_bar"].bottom))
                else:
                    pygame.draw.line(
                        self.screen,
                        (74, 74, 78),
                        (ui["bottom_bar"].x, ui["bottom_bar"].y),
                        (ui["bottom_bar"].right, ui["bottom_bar"].y),
                    )

                if ui.get("mode") == "landscape":
                    pr = ui["portrait"]
                    ang = 90 if self.video_rotation == 90 else -90
                    self.draw_png_icon_only_rotated(pr, self.video_ui_icons.get("portrait"), force_color=(246, 248, 255), angle=ang)
                else:
                    br = ui["back"]
                    pygame.draw.rect(self.screen, (22, 22, 22), br, border_radius=6)
                    pygame.draw.rect(self.screen, (68, 68, 68), br, width=1, border_radius=6)
                    back_text = self.small_font.render(f"< {self.tr('nav.back')}", True, (246, 248, 255))
                    self.screen.blit(back_text, (br.x + 6, br.y + 6))

                name = meta.get("name", norm_text(os.path.basename(path)))
                if ui.get("mode") == "landscape":
                    pr = ui["portrait"]
                    vol_r = ui["volume"]
                    if ui.get("flip"):
                        # Top bar on right: title between rotate button and volume bar.
                        avail = vol_r.y - pr.bottom - 8
                    else:
                        # Top bar on left: title between volume bar and rotate button.
                        avail = pr.y - vol_r.bottom - 8
                    max_w = max(20, avail)
                else:
                    max_w = self.w - 96
                while name and self.small_font.size(name)[0] > max_w:
                    name = name[:-1]
                if name != meta.get("name", "") and len(name) >= 2:
                    name = name[:-1] + "…"
                if ui.get("mode") == "landscape":
                    ang = 90 if self.video_rotation == 90 else -90
                    pr = ui["portrait"]
                    vol_r = ui["volume"]
                    title_x = pr.centerx
                    title_len = self.small_font.size(name)[0]
                    gap = 4
                    if ui.get("flip"):
                        top = pr.bottom + gap
                        bottom = max(top, vol_r.y - gap)
                        title_y = top + min(title_len // 2, max(0, (bottom - top) // 2))
                    else:
                        top = vol_r.bottom + gap
                        bottom = max(top, pr.y - gap)
                        title_y = bottom - min(title_len // 2, max(0, (bottom - top) // 2))
                    self.draw_text_rotated_center(
                        self.small_font,
                        name,
                        (246, 248, 255),
                        (title_x, title_y),
                        ang,
                    )
                else:
                    name_s = self.small_font.render(name, True, (246, 248, 255))
                    br = ui["back"]
                    title_y = br.y + (br.h - name_s.get_height()) // 2
                    self.screen.blit(name_s, (ui["title_x"], title_y))

            pos_v = self.video_progress_drag_pos if self.video_progress_drag else self.current_video_pos()
            dur_v = float(meta.get("length", 0.0))
            dur_t = self.fmt_time(dur_v) if dur_v > 0.0 else "--:--"
            pos_t = self.fmt_time(pos_v)
            if self.video_ui_progress > 0.01:
                t_left = self.small_font.render(pos_t, True, (230, 233, 240))
                t_right = self.small_font.render(dur_t, True, (230, 233, 240))
                if ui.get("mode") == "landscape":
                    ang = 90 if self.video_rotation == 90 else -90
                    cx = ui["progress"].x + ui["progress"].w // 2
                    if not ui.get("flip"):
                        self.draw_text_rotated_center(self.small_font, dur_t, (230, 233, 240), (cx, ui["time_y"]), ang)
                        self.draw_text_rotated_center(self.small_font, pos_t, (230, 233, 240), (cx, ui["time_y2"]), ang)
                    else:
                        self.draw_text_rotated_center(self.small_font, pos_t, (230, 233, 240), (cx, ui["time_y"]), ang)
                        self.draw_text_rotated_center(self.small_font, dur_t, (230, 233, 240), (cx, ui["time_y2"]), ang)
                else:
                    self.screen.blit(t_left, (14, ui["time_y"]))
                    self.screen.blit(t_right, (self.w - 14 - t_right.get_width(), ui["time_y"]))

                prog = ui["progress"]
                pygame.draw.rect(self.screen, (76, 82, 96), prog, border_radius=4)
                if dur_v > 0.0:
                    ratio = clamp(pos_v / dur_v, 0.0, 1.0)
                    if prog.h > prog.w:
                        fill_h = int(prog.h * ratio)
                        if fill_h > 0:
                            if ui.get("flip"):
                                pygame.draw.rect(
                                    self.screen,
                                    self.ui_accent(),
                                    (prog.x, prog.y, prog.w, fill_h),
                                    border_radius=4,
                                )
                            else:
                                pygame.draw.rect(
                                    self.screen,
                                    self.ui_accent(),
                                    (prog.x, prog.bottom - fill_h, prog.w, fill_h),
                                    border_radius=4,
                                )
                    else:
                        fill_w = int(prog.w * ratio)
                        if fill_w > 0:
                            pygame.draw.rect(self.screen, self.ui_accent(), (prog.x, prog.y, fill_w, prog.h), border_radius=4)

                if ui.get("mode") == "landscape" and not ui.get("flip"):
                    controls = [
                        (ui["prev"], "next"),
                        (ui["play"], "pause" if self.video_playing else "play"),
                        (ui["next"], "prev"),
                    ]
                else:
                    controls = [
                        (ui["prev"], "prev"),
                        (ui["play"], "pause" if self.video_playing else "play"),
                        (ui["next"], "next"),
                    ]
                for rect, icon_key in controls:
                    if ui.get("mode") == "landscape":
                        ang = 90 if self.video_rotation == 90 else -90
                        self.draw_icon_only_rotated(rect, icon_key, force_color=(246, 248, 255), angle=ang)
                    else:
                        self.draw_icon_only(rect, icon_key, "", False, force_color=(246, 248, 255))

                if ui.get("mode") != "landscape":
                    self.draw_png_icon_only(ui["rot_left"], self.video_ui_icons.get("rot_left"), force_color=(246, 248, 255))
                    self.draw_png_icon_only(ui["rot_right"], self.video_ui_icons.get("rot_right"), force_color=(246, 248, 255))

                vol = ui["volume"]
                pygame.draw.rect(self.screen, (25, 25, 25), vol, border_radius=6)
                pygame.draw.rect(self.screen, (68, 68, 68), vol, width=1, border_radius=6)
                vtrack = self.video_volume_track_rect(vol)
                if vtrack.h > vtrack.w:
                    vh = int(vtrack.h * self.music_volume)
                    if vh > 0:
                        if ui.get("flip"):
                            pygame.draw.rect(
                                self.screen,
                                self.ui_accent(),
                                (vtrack.x, vtrack.y, vtrack.w, vh),
                                border_radius=6,
                            )
                        else:
                            pygame.draw.rect(
                                self.screen,
                                self.ui_accent(),
                                (vtrack.x, vtrack.bottom - vh, vtrack.w, vh),
                                border_radius=6,
                            )
                    knob_y = (vtrack.y + int(vtrack.h * self.music_volume)) if ui.get("flip") else (vtrack.bottom - int(vtrack.h * self.music_volume))
                    pygame.draw.circle(self.screen, self.ui_accent(), (vtrack.centerx, knob_y), 5)
                else:
                    vw = int(vtrack.w * self.music_volume)
                    if vw > 0:
                        pygame.draw.rect(self.screen, self.ui_accent(), (vtrack.x, vtrack.y, vw, vtrack.h), border_radius=6)
                    knob_x = vtrack.x + int(vtrack.w * self.music_volume)
                    pygame.draw.circle(self.screen, self.ui_accent(), (knob_x, vtrack.centery), 5)
                vol_key = "volume0"
                if self.music_volume >= 0.75:
                    vol_key = "volume3"
                elif self.music_volume >= 0.45:
                    vol_key = "volume2"
                elif self.music_volume > 0.0:
                    vol_key = "volume1"
                if vtrack.h > vtrack.w:
                    ang = 90 if self.video_rotation == 90 else -90
                    icon_y = (vol.y + 2) if ui.get("flip") else (vol.bottom - 20)
                    self.draw_icon_only_rotated(
                        pygame.Rect(vol.centerx - 9, icon_y, 18, 18),
                        vol_key,
                        force_color=(255, 255, 255),
                        angle=ang,
                    )
                else:
                    self.draw_icon_only(pygame.Rect(vol.x + 3, vol.y + 1, 18, vol.h - 2), vol_key, "", False, force_color=(255, 255, 255))
            self.draw_toast()
            return

        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()

        title = self.title_font.render(self.tr("video.title", default=self.tr("app.video")), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 10))

        search_r = self.video_search_rect()
        search_bg = self.tone(pal["panel_bg"], 10 if self.editing_video_search else 0)
        pygame.draw.rect(self.screen, search_bg, search_r, border_radius=8)
        pygame.draw.rect(self.screen, pal["panel_border"], search_r, width=2, border_radius=8)
        q_text = self.video_search if self.video_search else self.tr("video.search", default=self.tr("music.search"))
        q_color = pal["text"] if self.video_search else self.tone(pal["text"], 70)
        qs = self.small_font.render(q_text, True, q_color)
        self.screen.blit(qs, (search_r.x + 8, search_r.y + 7))
        if self.editing_video_search and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = search_r.x + 8 + qs.get_width() + 1
            pygame.draw.line(self.screen, pal["text"], (cx, search_r.y + 6), (cx, search_r.y + 22), 2)

        sort_btn = self.video_sort_button_rect()
        self.draw_select_button(sort_btn, self.tr(f"video.sort.{self.video_sort}", default=self.tr(f"music.sort.{self.video_sort}")), False)

        list_rect = self.video_list_rect()
        panel_bg = self.tone(pal["panel_bg"], -8) if self.theme != "transparent" else (20, 20, 20, 120)
        if isinstance(panel_bg, tuple) and len(panel_bg) == 4:
            lay = pygame.Surface((list_rect.w, list_rect.h), pygame.SRCALPHA)
            lay.fill(panel_bg)
            self.screen.blit(lay, (list_rect.x, list_rect.y))
        else:
            pygame.draw.rect(self.screen, panel_bg, list_rect, border_radius=8)
        pygame.draw.rect(self.screen, pal["panel_border"], list_rect, width=1, border_radius=8)

        filtered = self.filtered_video_files()
        if not filtered:
            empty = self.small_font.render(self.tr("toast.no_video", default="비디오 파일이 없습니다"), True, self.tone(pal["text"], 40))
            self.screen.blit(empty, (list_rect.x + 10, list_rect.y + 10))
            if self.video_sort_picker_open:
                opts = self.video_sort_option_rects()
                for key in ("name", "date"):
                    self.draw_select_button(
                        opts[key],
                        self.tr(f"video.sort.{key}", default=self.tr(f"music.sort.{key}" if key == "name" else "video.sort.date")),
                        self.video_sort == key,
                    )
            self.draw_toast()
            return

        _vrect, _vtotal, row_h = self.video_scroll_info()
        max_rows = self.visible_rows(list_rect, row_h)
        base = int(self.list_scroll)
        frac = self.list_scroll - base
        y_off = int(frac * row_h)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(list_rect)
        for row in range(max_rows + 1):
            item_pos = base + row
            if item_pos >= len(filtered):
                break
            path = filtered[item_pos]
            y = list_rect.y + row * row_h - y_off
            row_rect = pygame.Rect(list_rect.x + 4, y + 2, list_rect.w - 8, row_h - 4)
            thumb_size = row_rect.h - 8
            try:
                thumb = self.video_thumbnail_for(path, thumb_size)
            except Exception:
                thumb = self.default_video_thumb(thumb_size)
            if thumb is None:
                thumb = self.default_video_thumb(thumb_size)
            self.screen.blit(thumb, (row_rect.x + 4, row_rect.y + (row_rect.h - thumb_size) // 2))
            meta = self.video_meta_for(path)
            label_raw = meta["name"]
            label = label_raw
            text_x = row_rect.x + 10 + thumb_size
            max_w = row_rect.right - text_x - 8
            while label and self.small_font.size(label)[0] > max_w:
                label = label[:-1]
            if label != label_raw and len(label) >= 2:
                label = label[:-1] + "…"
            text = self.small_font.render(label, True, pal["text"])
            self.screen.blit(text, (text_x, row_rect.y + 4))
            if meta["length"] > 0.0:
                dur_str = self.fmt_time(meta["length"])
            else:
                dur_str = "--:--"
            dur = self.small_font.render(dur_str, True, self.tone(pal["text"], 70))
            self.screen.blit(dur, (text_x, row_rect.y + 24))
        self.screen.set_clip(old_clip)
        self.draw_scroll_hint(list_rect, len(filtered), row_h)
        if self.video_sort_picker_open:
            opts = self.video_sort_option_rects()
            for key in ("name", "date"):
                self.draw_select_button(
                    opts[key],
                    self.tr(f"video.sort.{key}", default=self.tr(f"music.sort.{key}" if key == "name" else "video.sort.date")),
                    self.video_sort == key,
                )
        self.draw_toast()

    def draw_textviewer(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()

        files = self.filtered_text_files()
        if self.text_view == "READER":
            if files:
                self.text_index = int(clamp(self.text_index, 0, len(files) - 1))
                path = files[self.text_index]
                meta = self.text_meta_for(path)
                header_name = meta.get("name", norm_text(os.path.basename(path)))
            else:
                header_name = self.tr("app.textviewer", default="텍스트 뷰어")
            title = self.title_font.render(header_name, True, pal["text"])
            self.screen.blit(title, (14, STATUS_H + 8))
            rect = self.text_reader_rect()
            panel_bg = self.tone(pal["panel_bg"], -8) if self.theme != "transparent" else (20, 20, 20, 120)
            if isinstance(panel_bg, tuple) and len(panel_bg) == 4:
                lay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                lay.fill(panel_bg)
                self.screen.blit(lay, (rect.x, rect.y))
            else:
                pygame.draw.rect(self.screen, panel_bg, rect, border_radius=8)
            pygame.draw.rect(self.screen, pal["panel_border"], rect, width=1, border_radius=8)

            if not files:
                empty = self.small_font.render(self.tr("text.empty", default="텍스트 파일이 없습니다"), True, self.tone(pal["text"], 40))
                self.screen.blit(empty, (rect.x + 10, rect.y + 10))
                self.draw_toast()
                return

            self.text_index = int(clamp(self.text_index, 0, len(files) - 1))
            body_rect = self.text_reader_body_rect()
            ctr = self.text_reader_control_rects(rect)
            body_font = self.text_body_font()
            row_h = self.text_reader_row_h()
            lines = self.text_reader_lines()
            max_rows = max(1, body_rect.h // row_h)
            base = int(self.list_scroll)
            frac = self.list_scroll - base
            y_off = int(frac * row_h)
            old_clip = self.screen.get_clip()
            self.screen.set_clip(body_rect)
            for row in range(max_rows + 1):
                i = base + row
                if i >= len(lines):
                    break
                y = body_rect.y + row * row_h - y_off
                ln_text, ln_indent = lines[i]
                if ln_text:
                    ls = body_font.render(ln_text, True, pal["text"])
                    self.screen.blit(ls, (body_rect.x + 2 + int(ln_indent), y))
            self.screen.set_clip(old_clip)
            self.draw_scroll_hint(body_rect, len(lines), row_h)

            self.draw_select_button(ctr["minus"], "-", False)
            pct_s = self.small_font.render(f"{int(self.text_font_percent):02d}%", True, pal["text"])
            self.screen.blit(
                pct_s,
                (
                    ctr["pct"].centerx - pct_s.get_width() // 2,
                    ctr["pct"].centery - pct_s.get_height() // 2,
                ),
            )
            self.draw_select_button(ctr["plus"], "+", False)
            self.draw_toast()
            return

        title = self.title_font.render(self.tr("app.textviewer", default="텍스트 뷰어"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 10))

        search_r = self.text_search_rect()
        search_bg = self.tone(pal["panel_bg"], 10 if self.editing_text_search else 0)
        pygame.draw.rect(self.screen, search_bg, search_r, border_radius=8)
        pygame.draw.rect(self.screen, pal["panel_border"], search_r, width=2, border_radius=8)
        q_text = self.text_search if self.text_search else self.tr("text.search", default=self.tr("music.search"))
        q_color = pal["text"] if self.text_search else self.tone(pal["text"], 70)
        qs = self.small_font.render(q_text, True, q_color)
        self.screen.blit(qs, (search_r.x + 8, search_r.y + 7))
        if self.editing_text_search and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = search_r.x + 8 + qs.get_width() + 1
            pygame.draw.line(self.screen, pal["text"], (cx, search_r.y + 6), (cx, search_r.y + 22), 2)

        sort_btn = self.text_sort_button_rect()
        self.draw_select_button(sort_btn, self.tr(f"video.sort.{self.text_sort}", default=self.tr("music.sort.name")), False)

        list_rect = self.text_list_rect()
        panel_bg = self.tone(pal["panel_bg"], -8) if self.theme != "transparent" else (20, 20, 20, 120)
        if isinstance(panel_bg, tuple) and len(panel_bg) == 4:
            lay = pygame.Surface((list_rect.w, list_rect.h), pygame.SRCALPHA)
            lay.fill(panel_bg)
            self.screen.blit(lay, (list_rect.x, list_rect.y))
        else:
            pygame.draw.rect(self.screen, panel_bg, list_rect, border_radius=8)
        pygame.draw.rect(self.screen, pal["panel_border"], list_rect, width=1, border_radius=8)

        if not files:
            empty = self.small_font.render(self.tr("text.empty", default="텍스트 파일이 없습니다"), True, self.tone(pal["text"], 40))
            self.screen.blit(empty, (list_rect.x + 10, list_rect.y + 10))
            if self.text_sort_picker_open:
                opts = self.text_sort_option_rects()
                for key in ("name", "date"):
                    self.draw_select_button(
                        opts[key],
                        self.tr(f"video.sort.{key}", default=self.tr(f"music.sort.{key}" if key == "name" else "video.sort.date")),
                        self.text_sort == key,
                    )
            self.draw_toast()
            return

        _rect, _total, row_h = self.text_scroll_info()
        max_rows = self.visible_rows(list_rect, row_h)
        base = int(self.list_scroll)
        frac = self.list_scroll - base
        y_off = int(frac * row_h)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(list_rect)
        for row in range(max_rows + 1):
            item_pos = base + row
            if item_pos >= len(files):
                break
            path = files[item_pos]
            y = list_rect.y + row * row_h - y_off
            row_rect = pygame.Rect(list_rect.x + 4, y + 2, list_rect.w - 8, row_h - 4)
            thumb_size = row_rect.h - 8
            thumb = self.text_thumb_for(path, thumb_size)
            self.screen.blit(thumb, (row_rect.x + 4, row_rect.y + (row_rect.h - thumb_size) // 2))

            meta = self.text_meta_for(path)
            label_raw = meta.get("name", norm_text(os.path.basename(path)))
            label = label_raw
            text_x = row_rect.x + 10 + thumb_size
            max_w = row_rect.right - text_x - 8
            while label and self.small_font.size(label)[0] > max_w:
                label = label[:-1]
            if label != label_raw and len(label) >= 2:
                label = label[:-1] + "…"
            text = self.small_font.render(label, True, pal["text"])
            self.screen.blit(text, (text_x, row_rect.y + 4))

            preview_raw = meta.get("preview", "")
            preview = preview_raw
            while preview and self.small_font.size(preview)[0] > max_w:
                preview = preview[:-1]
            if preview != preview_raw and len(preview) >= 2:
                preview = preview[:-1] + "…"
            pv = self.small_font.render(preview, True, self.tone(pal["text"], 70))
            self.screen.blit(pv, (text_x, row_rect.y + 24))
        self.screen.set_clip(old_clip)
        self.draw_scroll_hint(list_rect, len(files), row_h)
        if self.text_sort_picker_open:
            opts = self.text_sort_option_rects()
            for key in ("name", "date"):
                self.draw_select_button(
                    opts[key],
                    self.tr(f"video.sort.{key}", default=self.tr(f"music.sort.{key}" if key == "name" else "video.sort.date")),
                    self.text_sort == key,
                )
        self.draw_toast()

    # 파일 앱 렌더링(루트/목록/상세/선택 모드 포함)
    def draw_filesviewer(self):
        pal = self.pal()
        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        self.draw_icon_only(self.back_button_rect(), "back", "", False)
        title = self.title_font.render(self.tr("app.files", default="파일"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 10))
        if self.files_view == "LIST":
            root_label = self.tr("files.storage.internal", default="내부 저장소") if self.files_source == "internal" else self.tr("files.storage.trash", default="휴지통")
            sub = self.files_path.replace("\\", "/")
            label = root_label if not sub else f"{root_label}/{sub}"
            sub_s = self.small_font.render(label, True, self.tone(pal["text"], 60))
            self.screen.blit(sub_s, (14, STATUS_H + 34))

        list_rect = self.files_effective_list_rect()
        panel_bg = self.tone(pal["panel_bg"], -8) if self.theme != "transparent" else (20, 20, 20, 120)

        if self.files_view == "INFO":
            ent = self.files_info_entry
            if not ent:
                self.files_view = "LIST"
                self.draw_toast()
                return
            info_rect = self.files_info_rect()
            if isinstance(panel_bg, tuple) and len(panel_bg) == 4:
                lay = pygame.Surface((info_rect.w, info_rect.h), pygame.SRCALPHA)
                lay.fill(panel_bg)
                self.screen.blit(lay, (info_rect.x, info_rect.y))
            else:
                pygame.draw.rect(self.screen, panel_bg, info_rect, border_radius=8)
            pygame.draw.rect(self.screen, pal["panel_border"], info_rect, width=1, border_radius=8)

            y = info_rect.y + 10
            line_h = 24
            full = ent.get("path", "")
            rel_dir = os.path.dirname(os.path.relpath(full, BASE_DIR)).replace("\\", "/")
            rel_dir = "." if rel_dir in ("", ".") else f"./{rel_dir}"
            ext = ent.get("ext", "")
            typ = ext[1:].upper() if ext.startswith(".") else self.tr("files.type.unknown", default="알 수 없음")
            rows = [
                (self.tr("files.info.name", default="파일명"), ent.get("name", "")),
                (self.tr("files.info.type", default="종류"), typ),
                (self.tr("files.info.size", default="크기"), self.format_file_size(ent.get("size", 0))),
                (self.tr("files.info.path", default="경로"), rel_dir),
                (self.tr("files.info.created", default="생성일"), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ent.get("created", 0) or 0))),
                (self.tr("files.info.modified", default="수정일"), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ent.get("modified", 0) or 0))),
            ]
            for k, v in rows:
                k_s = self.small_font.render(k, True, self.tone(pal["text"], 70))
                v_s = self.small_font.render(str(v), True, pal["text"])
                self.screen.blit(k_s, (info_rect.x + 12, y))
                self.screen.blit(v_s, (info_rect.x + 100, y))
                y += line_h
            actions = self.files_info_action_rects(info_rect)
            self.draw_select_button(actions["rename"], self.tr("files.action.rename", default="이름 변경"), False)
            self.draw_select_button(actions["delete"], self.tr("files.action.delete", default="삭제"), False)

            if self.files_info_rename_active:
                p = clamp((pygame.time.get_ticks() - self.files_info_rename_start) / max(1, self.files_info_rename_ms), 0.0, 1.0)
                veil = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
                veil.fill((0, 0, 0, int(140 * p)))
                self.screen.blit(veil, (0, 0))
                base = self.files_info_rename_dialog_rects()["panel"]
                scale = 0.92 + 0.08 * p
                ww = int(base.w * scale)
                hh = int(base.h * scale)
                rr = pygame.Rect(base.centerx - ww // 2, base.centery - hh // 2, ww, hh)
                pygame.draw.rect(self.screen, pal["panel_bg"], rr, border_radius=14)
                pygame.draw.rect(self.screen, pal["panel_border"], rr, width=1, border_radius=14)
                title = self.font.render(self.tr("files.action.rename", default="이름 변경"), True, pal["text"])
                self.screen.blit(title, (rr.centerx - title.get_width() // 2, rr.y + 12))
                input_rect = pygame.Rect(rr.x + 14, rr.y + 58, rr.w - 28, 34)
                pygame.draw.rect(self.screen, self.tone(pal["panel_bg"], 8), input_rect, border_radius=8)
                pygame.draw.rect(self.screen, pal["panel_border"], input_rect, width=2, border_radius=8)
                txt = self.files_info_rename_text
                max_w = input_rect.w - 16
                while txt and self.small_font.size(txt)[0] > max_w:
                    txt = txt[1:]
                name_s = self.small_font.render(txt, True, pal["text"])
                self.screen.blit(name_s, (input_rect.x + 8, input_rect.centery - name_s.get_height() // 2))
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    cx = input_rect.x + 8 + name_s.get_width() + 1
                    pygame.draw.line(self.screen, pal["text"], (cx, input_rect.y + 6), (cx, input_rect.y + 26), 2)
                b = {
                    "cancel": pygame.Rect(rr.x + 16, rr.bottom - 42, 108, 30),
                    "ok": pygame.Rect(rr.right - 124, rr.bottom - 42, 108, 30),
                }
                self.draw_select_button(b["cancel"], self.tr("common.cancel", default="취소"), False)
                self.draw_select_button(b["ok"], self.tr("common.change", default="변경"), False)
            self.draw_toast()
            return

        if self.files_view == "LIST":
            search_r = self.files_search_rect()
            search_bg = self.tone(pal["panel_bg"], 10 if self.editing_files_search else 0)
            pygame.draw.rect(self.screen, search_bg, search_r, border_radius=8)
            pygame.draw.rect(self.screen, pal["panel_border"], search_r, width=2, border_radius=8)
            q_text = self.files_search if self.files_search else self.tr("files.search", default=self.tr("music.search"))
            q_color = pal["text"] if self.files_search else self.tone(pal["text"], 70)
            qs = self.small_font.render(q_text, True, q_color)
            self.screen.blit(qs, (search_r.x + 8, search_r.y + 7))
            if self.editing_files_search and (pygame.time.get_ticks() // 500) % 2 == 0:
                cx = search_r.x + 8 + qs.get_width() + 1
                pygame.draw.line(self.screen, pal["text"], (cx, search_r.y + 6), (cx, search_r.y + 22), 2)
            order_btn = self.files_order_button_rect()
            if self.files_source != "trash":
                sort_btn = self.files_sort_button_rect()
                sort_label = self.tr(f"files.sort.{self.files_sort}", default=self.tr("files.sort.name", default="이름순"))
                self.draw_select_button(sort_btn, sort_label, False)
            order_label = "▼" if self.files_sort_desc else "▲"
            self.draw_select_button(order_btn, order_label, False)

        if isinstance(panel_bg, tuple) and len(panel_bg) == 4:
            lay = pygame.Surface((list_rect.w, list_rect.h), pygame.SRCALPHA)
            lay.fill(panel_bg)
            self.screen.blit(lay, (list_rect.x, list_rect.y))
        else:
            pygame.draw.rect(self.screen, panel_bg, list_rect, border_radius=8)
        pygame.draw.rect(self.screen, pal["panel_border"], list_rect, width=1, border_radius=8)

        items = self.files_root_entries() if self.files_view == "ROOT" else self.filtered_file_entries()
        selectable = self.files_selection_enabled()
        if not items:
            empty = self.small_font.render(self.tr("files.empty", default="항목이 없습니다"), True, self.tone(pal["text"], 40))
            self.screen.blit(empty, (list_rect.x + 10, list_rect.y + 10))
            self.draw_toast()
            return

        _r, _t, row_h = self.files_scroll_info()
        max_rows = self.visible_rows(list_rect, row_h)
        base = int(self.list_scroll)
        frac = self.list_scroll - base
        y_off = int(frac * row_h)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(list_rect)
        for row in range(max_rows + 1):
            idx = base + row
            if idx >= len(items):
                break
            y = list_rect.y + row * row_h - y_off
            row_rect = pygame.Rect(list_rect.x + 4, y + 2, list_rect.w - 8, row_h - 4)
            thumb_size = row_rect.h - 8
            item = items[idx]

            if self.files_view == "ROOT":
                key = item.get("key", "internal")
                icon = self.file_icon_for_entry({"icon_key": key if key in ("internal", "external", "trash") else "file"}, thumb_size)
                enabled = bool(item.get("enabled"))
                tx_color = pal["text"] if enabled else self.tone(pal["text"], 70)
                ix = row_rect.x + 4
                iy = row_rect.y + (row_rect.h - icon.get_height()) // 2
                if enabled:
                    self.screen.blit(icon, (ix, iy))
                else:
                    disabled_icon = icon.copy()
                    disabled_icon.fill((125, 130, 140, 0), special_flags=pygame.BLEND_RGB_MULT)
                    disabled_icon.set_alpha(120)
                    self.screen.blit(disabled_icon, (ix, iy))
                text = self.small_font.render(item.get("label", ""), True, tx_color)
                self.screen.blit(text, (row_rect.x + 10 + thumb_size, row_rect.y + 14))
                continue

            icon = self.file_thumb_for_entry(item, thumb_size)
            selected_row = item.get("path", "") in self.files_selected
            if selected_row:
                if self.theme == "light":
                    sel_bg = (232, 236, 242)
                    sel_bd = (206, 214, 226)
                else:
                    sel_bg = (48, 54, 66)
                    sel_bd = (84, 96, 118)
                pygame.draw.rect(self.screen, sel_bg, row_rect, border_radius=8)
                pygame.draw.rect(self.screen, sel_bd, row_rect, width=1, border_radius=8)
            icon_x = row_rect.x + 4
            if selectable:
                cb_rect = self.files_checkbox_rect(row_rect, thumb_size)
                checked = selected_row
                cb_char = "■" if checked else "□"
                cb_color = self.ui_accent() if checked else self.tone(pal["text"], 55)
                cb = self.font.render(cb_char, True, cb_color)
                self.screen.blit(cb, (cb_rect.x + (cb_rect.w - cb.get_width()) // 2, cb_rect.y + (cb_rect.h - cb.get_height()) // 2 - 1))
                icon_x = cb_rect.right + 8
            self.screen.blit(icon, (icon_x, row_rect.y + (row_rect.h - icon.get_height()) // 2))
            text_x = icon_x + thumb_size + 6
            right_value = (
                self.tr("files.folder.count", count=item.get("count", 0), default=f"{int(item.get('count', 0))}개")
                if item.get("is_dir")
                else self.format_file_size(item.get("size", 0))
            )
            right_s = self.small_font.render(right_value, True, self.tone(pal["text"], 70))
            right_x = row_rect.right - 8 - right_s.get_width()

            label_raw = self.files_display_name(item)
            label = label_raw
            max_w = max(20, right_x - text_x - 8)
            while label and self.small_font.size(label)[0] > max_w:
                label = label[:-1]
            if label != label_raw and len(label) >= 2:
                label = label[:-1] + "…"
            text = self.small_font.render(label, True, pal["text"])
            self.screen.blit(text, (text_x, row_rect.y + 4))

            if self.files_source == "trash":
                mod_str = item.get("deleted_at", "") or time.strftime("%Y-%m-%d %H:%M", time.localtime(item.get("modified", 0) or 0))
            else:
                mod_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(item.get("modified", 0) or 0))
            mod = self.small_font.render(mod_str, True, self.tone(pal["text"], 70))
            self.screen.blit(mod, (text_x, row_rect.y + 24))
            self.screen.blit(right_s, (right_x, row_rect.y + 14))
        self.screen.set_clip(old_clip)
        self.draw_scroll_hint(list_rect, len(items), row_h)

        if self.files_view == "LIST" and selectable and self.files_selected:
            ar = self.files_selected_action_rects()
            veil = pygame.Surface((ar["bar"].w, ar["bar"].h), pygame.SRCALPHA)
            veil.fill((0, 0, 0, 70) if self.theme != "light" else (255, 255, 255, 120))
            self.screen.blit(veil, ar["bar"].topleft)
            cnt = len(self.files_selected)
            msg = self.small_font.render(self.tr("files.selected.count", count=cnt, default=f"{cnt}개 선택됨"), True, pal["text"])
            self.screen.blit(msg, (self.w // 2 - msg.get_width() // 2, ar["center"].centery - msg.get_height() // 2))
            if self.files_source == "trash" and ("left" in ar):
                self.draw_select_button(ar["left"], self.tr("files.action.restore", default="복원"), False)
                self.draw_select_button(ar["right"], self.tr("files.action.delete", default="삭제"), False)
            else:
                icon_color = (0, 0, 0) if self.theme == "light" else (246, 248, 255)
                self.draw_png_icon_only(ar["right"], self.files_ui_icons.get("trash"), force_color=icon_color)

        if self.files_view == "LIST" and self.files_source != "trash" and self.files_sort_picker_open:
            opts = self.files_sort_option_rects()
            for key in ("name", "date", "size"):
                self.draw_select_button(
                    opts[key],
                    self.tr(f"files.sort.{key}", default=key),
                    self.files_sort == key,
                )
        if self.files_view == "LIST" and self.files_delete_confirm_active:
            pal_d = THEMES["light"] if self.theme == "light" else THEMES["dark"]
            p = clamp((pygame.time.get_ticks() - self.files_delete_confirm_start) / max(1, self.files_delete_confirm_ms), 0.0, 1.0)
            veil = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            veil.fill((0, 0, 0, int(140 * p)))
            self.screen.blit(veil, (0, 0))
            base = self.power_confirm_rect()
            scale = 0.92 + 0.08 * p
            ww = int(base.w * scale)
            hh = int(base.h * scale)
            rr = pygame.Rect(base.centerx - ww // 2, base.centery - hh // 2, ww, hh)
            pygame.draw.rect(self.screen, pal_d["panel_bg"], rr, border_radius=14)
            pygame.draw.rect(self.screen, pal_d["panel_border"], rr, width=1, border_radius=14)

            cnt = len(self.files_delete_confirm_paths) if self.files_delete_confirm_paths else len(self.files_selected)
            if self.files_delete_confirm_action == "trash_delete":
                msg = self.tr("files.trash.delete.confirm", count=cnt, default=f"{cnt}개의 항목을 영구적으로 삭제하시겠습니까?")
            elif self.files_delete_confirm_action == "trash_restore":
                msg = self.tr("files.trash.restore.confirm", count=cnt, default=f"{cnt}개의 항목을 복원하시겠습니까?")
            else:
                msg = self.tr("files.delete.confirm", count=cnt, default=f"{cnt}개의 항목을 휴지통으로 이동하시겠습니까?")
            max_w = rr.w - 26
            lines = []
            cur = ""
            for ch in msg:
                test = cur + ch
                if cur and self.font.size(test)[0] > max_w:
                    lines.append(cur)
                    cur = ch
                else:
                    cur = test
            if cur:
                lines.append(cur)
            if len(lines) > 3:
                lines = lines[:3]
                tail = lines[-1]
                while tail and self.font.size(tail + "…")[0] > max_w:
                    tail = tail[:-1]
                lines[-1] = (tail + "…") if tail else "…"
            total_h = len(lines) * (self.font.get_linesize() + 2)
            sy = rr.y + 36 - max(0, (total_h - self.font.get_linesize()) // 2)
            for i, line in enumerate(lines):
                msg_s = self.font.render(line, True, pal_d["text"])
                self.screen.blit(msg_s, (rr.centerx - msg_s.get_width() // 2, sy + i * (self.font.get_linesize() + 2)))

            b = self.power_confirm_buttons()
            self.draw_select_button(b["no"], self.tr("common.no", default="아니요"), False)
            self.draw_select_button(b["yes"], self.tr("common.yes", default="네"), False)
        self.draw_toast()

    # 사진 앱 렌더링(그리드/뷰어/공유/삭제 다이얼로그)
    def draw_photo(self):
        pal = self.pal()
        files = self.filtered_photo_files()
        if self.photo_view == "VIEWER":
            self.screen.fill((0, 0, 0))
            if files:
                self.photo_index = int(clamp(self.photo_index, 0, len(files) - 1))
                path = files[self.photo_index]
                ui = self.photo_ui_touch_rects()
                rect = self.photo_viewer_rect()
                if (
                    self.photo_slide_active
                    and self.photo_slide_from_path
                    and self.photo_slide_to_path
                ):
                    p = clamp((pygame.time.get_ticks() - self.photo_slide_start) / max(1, self.photo_slide_ms), 0.0, 1.0)
                    from_s = self.photo_view_surface_for(self.photo_slide_from_path, rect)
                    to_s = self.photo_view_surface_for(self.photo_slide_to_path, rect)
                    off = int(rect.w * p)
                    dir_sign = 1 if self.photo_slide_dir >= 0 else -1
                    from_x = rect.x - (dir_sign * off) + (rect.w - from_s.get_width()) // 2
                    to_x = rect.x + (dir_sign * (rect.w - off)) + (rect.w - to_s.get_width()) // 2
                    fy = rect.y + (rect.h - from_s.get_height()) // 2
                    ty = rect.y + (rect.h - to_s.get_height()) // 2
                    self.screen.blit(from_s, (from_x, fy))
                    self.screen.blit(to_s, (to_x, ty))
                    if p >= 1.0:
                        self.photo_slide_active = False
                        self.photo_slide_from_path = ""
                        self.photo_slide_to_path = ""
                else:
                    surf = self.photo_view_surface_for(path, rect)
                    if self.photo_zoom > 1.001:
                        zw = max(1, int(surf.get_width() * self.photo_zoom))
                        zh = max(1, int(surf.get_height() * self.photo_zoom))
                        surf = pygame.transform.smoothscale(surf, (zw, zh))
                    x = rect.x + (rect.w - surf.get_width()) // 2
                    y = rect.y + (rect.h - surf.get_height()) // 2
                    self.screen.blit(surf, (x, y))
                if self.photo_ui_progress > 0.01:
                    top_bar = pygame.Surface((ui["top_bar"].w, ui["top_bar"].h), pygame.SRCALPHA)
                    top_bar.fill((0, 0, 0, 140))
                    self.screen.blit(top_bar, ui["top_bar"].topleft)
                    pygame.draw.line(
                        self.screen,
                        (74, 74, 78),
                        (ui["top_bar"].x, ui["top_bar"].bottom - 1),
                        (ui["top_bar"].right, ui["top_bar"].bottom - 1),
                    )

                    bottom_bar = pygame.Surface((ui["bottom_bar"].w, ui["bottom_bar"].h), pygame.SRCALPHA)
                    bottom_bar.fill((0, 0, 0, 140))
                    self.screen.blit(bottom_bar, ui["bottom_bar"].topleft)
                    pygame.draw.line(
                        self.screen,
                        (74, 74, 78),
                        (ui["bottom_bar"].x, ui["bottom_bar"].y),
                        (ui["bottom_bar"].right, ui["bottom_bar"].y),
                    )

                    br = ui["back"]
                    pygame.draw.rect(self.screen, (22, 22, 22), br, border_radius=6)
                    pygame.draw.rect(self.screen, (68, 68, 68), br, width=1, border_radius=6)
                    back_text = self.small_font.render(f"< {self.tr('nav.back')}", True, (246, 248, 255))
                    self.screen.blit(back_text, (br.x + 6, br.y + 6))

                    info = self.photo_info_for(path)
                    dt_text = info.get("datetime", "")
                    max_w = self.w - ui["text_x"] - 8
                    while dt_text and self.small_font.size(dt_text)[0] > max_w:
                        dt_text = dt_text[:-1]
                    if dt_text != info.get("datetime", "") and len(dt_text) >= 2:
                        dt_text = dt_text[:-1] + "…"
                    dt_shadow = self.small_font.render(dt_text, True, (0, 0, 0))
                    dt_s = self.small_font.render(dt_text, True, (220, 224, 232))
                    dt_x = self.w - 10 - dt_s.get_width()
                    dt_y = ui["text_y"]
                    self.screen.blit(dt_shadow, (dt_x + 1, dt_y + 1))
                    self.screen.blit(dt_s, (dt_x, dt_y))

                    for key in ("share", "delete"):
                        rr = ui["share"] if key == "share" else ui["delete"]
                        icon_shadow = pygame.Surface((rr.w + 8, rr.h + 8), pygame.SRCALPHA)
                        pygame.draw.ellipse(icon_shadow, (0, 0, 0, 86), icon_shadow.get_rect())
                        self.screen.blit(icon_shadow, (rr.x - 4, rr.y - 1))
                        self.draw_png_icon_only(rr, self.photo_ui_icons.get("share" if key == "share" else "trash"), force_color=(246, 248, 255))
                if self.photo_share_sheet_active:
                    pal_s = THEMES["light"] if self.theme == "light" else THEMES["dark"]
                    p = clamp((pygame.time.get_ticks() - self.photo_share_sheet_start) / max(1, self.photo_share_sheet_ms), 0.0, 1.0)
                    veil = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
                    veil.fill((0, 0, 0, int(130 * p)))
                    self.screen.blit(veil, (0, 0))
                    ss = self.photo_share_sheet_rects()
                    base = ss["panel"]
                    scale = 0.92 + 0.08 * p
                    ww = int(base.w * scale)
                    hh = int(base.h * scale)
                    rr = pygame.Rect(base.centerx - ww // 2, base.centery - hh // 2, ww, hh)
                    pygame.draw.rect(self.screen, pal_s["panel_bg"], rr, border_radius=14)
                    pygame.draw.rect(self.screen, pal_s["panel_border"], rr, width=1, border_radius=14)
                    title = self.font.render(self.tr("photo.share.title", default="공유"), True, pal_s["text"])
                    self.screen.blit(title, (rr.centerx - title.get_width() // 2, rr.y + 10))

                    by = rr.y - base.y
                    self.draw_select_button(ss["copy"].move(0, by), self.tr("photo.share.copy", default="사진 복사"), False)
                    self.draw_select_button(ss["wallpaper"].move(0, by), self.tr("photo.share.wallpaper", default="배경화면 지정"), False)
                    self.draw_select_button(ss["cancel"].move(0, by), self.tr("common.cancel", default="취소"), False)
                if self.photo_delete_confirm_active:
                    pal_d = THEMES["light"] if self.theme == "light" else THEMES["dark"]
                    p = clamp((pygame.time.get_ticks() - self.photo_delete_confirm_start) / max(1, self.photo_delete_confirm_ms), 0.0, 1.0)
                    veil = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
                    veil.fill((0, 0, 0, int(140 * p)))
                    self.screen.blit(veil, (0, 0))

                    base = self.power_confirm_rect()
                    scale = 0.92 + 0.08 * p
                    ww = int(base.w * scale)
                    hh = int(base.h * scale)
                    rr = pygame.Rect(base.centerx - ww // 2, base.centery - hh // 2, ww, hh)
                    pygame.draw.rect(self.screen, pal_d["panel_bg"], rr, border_radius=14)
                    pygame.draw.rect(self.screen, pal_d["panel_border"], rr, width=1, border_radius=14)

                    msg1 = self.font.render(self.tr("photo.delete.confirm.title", default="사진을 삭제하시겠습니까?"), True, pal_d["text"])
                    msg2 = self.small_font.render(self.tr("photo.delete.confirm.desc", default="삭제된 사진은 휴지통으로 이동됩니다."), True, self.tone(pal_d["text"], 40))
                    self.screen.blit(msg1, (rr.centerx - msg1.get_width() // 2, rr.y + 26))
                    self.screen.blit(msg2, (rr.centerx - msg2.get_width() // 2, rr.y + 58))

                    b = self.power_confirm_buttons()
                    self.draw_select_button(b["no"], self.tr("common.no", default="아니요"), False)
                    self.draw_select_button(b["yes"], self.tr("common.yes", default="네"), False)
            self.draw_toast()
            return

        if self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()
        title = self.title_font.render(self.tr("app.photo", default="사진"), True, pal["text"])
        self.screen.blit(title, (14, STATUS_H + 8))

        rect = self.photo_grid_rect()
        if not files:
            empty = self.small_font.render(self.tr("photo.empty", default="사진 파일이 없습니다"), True, self.tone(pal["text"], 40))
            ex = rect.x + max(0, (rect.w - empty.get_width()) // 2)
            ey = rect.y + 8
            self.screen.blit(empty, (ex, ey))
            self.draw_toast()
            return

        gap = 4
        cell = max(24, (rect.w - gap * (PHOTO_COLS - 1)) // PHOTO_COLS)
        row_h = cell + gap
        total_rows = (len(files) + PHOTO_COLS - 1) // PHOTO_COLS
        max_rows = max(1, rect.h // row_h)
        base_row = int(self.list_scroll)
        frac = self.list_scroll - base_row
        y_off = int(frac * row_h)

        old_clip = self.screen.get_clip()
        self.screen.set_clip(rect)
        for r in range(max_rows + 2):
            row_idx = base_row + r
            if row_idx >= total_rows:
                break
            y = rect.y + r * row_h - y_off
            for c in range(PHOTO_COLS):
                idx = row_idx * PHOTO_COLS + c
                if idx >= len(files):
                    break
                x = rect.x + c * (cell + gap)
                thumb = self.photo_thumb_for(files[idx], cell)
                self.screen.blit(thumb, (x, y))
                pygame.draw.rect(self.screen, self.tone(pal["panel_border"], 8 if self.theme == "light" else -8), (x, y, cell, cell), width=1)
        self.screen.set_clip(old_clip)

        self.draw_scroll_hint(rect, total_rows, row_h)
        self.draw_toast()

    # 음악 앱 렌더링(메뉴/목록/그룹/지금 재생)
    def draw_music(self):
        pal = self.pal()
        if self.music_view == "NOW" and self.theme in ("light", "dark"):
            bg = self.now_backdrop_surface()
            if bg:
                self.screen.blit(bg, (0, 0))
                veil = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
                if self.theme == "light":
                    veil.fill((255, 255, 255, 150))
                else:
                    veil.fill((0, 0, 0, 150))
                self.screen.blit(veil, (0, 0))
            else:
                self.screen.fill(pal["settings_bg"])
        elif self.theme == "transparent":
            self.draw_overlay_background(pal["settings_bg"])
        else:
            self.screen.fill(pal["settings_bg"])
        self.draw_statusbar()

        title_text = None
        if self.music_view == "MENU":
            title_text = self.tr("music.title")
        elif self.music_view == "NOW":
            title_text = None
        elif self.music_view == "QUEUE":
            title_text = self.tr("music.queue.current", default="재생 목록")
        elif self.music_view == "ALBUMS":
            title_text = self.tr("music.menu.albums")
        elif self.music_view == "ARTISTS":
            title_text = self.tr("music.menu.artists")
        elif self.music_view == "GENRES":
            title_text = self.tr("music.menu.genres", default="장르")
        elif self.music_view == "ARTIST_ALBUMS":
            title_text = self.music_ctx_artist or self.tr("music.menu.artists")
        elif self.music_view == "LIST":
            if self.music_ctx_album:
                title_text = self.music_ctx_album
            elif self.music_ctx_artist:
                title_text = self.music_ctx_artist
            elif self.music_ctx_genre:
                title_text = self.music_ctx_genre
            else:
                title_text = self.tr("music.menu.list")
        if title_text:
            title_x = 14
            title_y = STATUS_H + 10
            if self.music_view == "LIST" and self.music_ctx_album:
                header_size = 32
                header_art = self.album_art_for_album(self.music_ctx_album, size=header_size)
                if header_art:
                    self.screen.blit(header_art, (14, STATUS_H + 12))
                else:
                    pygame.draw.rect(
                        self.screen,
                        self.tone(pal["panel_border"], -25),
                        (14, STATUS_H + 12, header_size, header_size),
                        border_radius=8,
                    )
                title_x = 52
            title = self.title_font.render(title_text, True, pal["text"])
            self.screen.blit(title, (title_x, title_y))
            if self.music_view == "LIST" and self.music_ctx_album:
                sub_artist = self.music_ctx_artist or self.album_artist_for_album(self.music_ctx_album)
                sub = self.small_font.render(sub_artist, True, self.tone(pal["text"], 40))
                self.screen.blit(sub, (title_x, STATUS_H + 38))

        if self.music_view == "MENU":
            menu = self.music_menu_rects()
            accent = self.ui_accent()
            row_bg = self.tone(pal["panel_bg"], 2)
            row_bd = pal["panel_border"]
            header = pygame.Rect(14, STATUS_H + 42, self.w - 28, 38)
            pygame.draw.rect(self.screen, row_bg, header, border_radius=12)
            pygame.draw.rect(self.screen, row_bd, header, width=1, border_radius=12)
            hs = self.small_font.render(self.tr("music.title", default="음악"), True, self.tone(pal["text"], 35))
            self.screen.blit(hs, (header.x + 12, header.centery - hs.get_height() // 2))
            cnt = self.small_font.render(f"{len(self.music_files)}", True, accent)
            self.screen.blit(cnt, (header.right - 12 - cnt.get_width(), header.centery - cnt.get_height() // 2))

            now_name = self.track_name(self.music_index) if self.music_files else self.tr("music.none", default="재생 대기 없음")
            items = [
                ("now", self.tr("music.menu.now"), now_name),
                ("list", self.tr("music.menu.list"), self.tr("music.count.songs", count=len(self.music_files), default=f"{len(self.music_files)}곡")),
                (
                    "albums",
                    self.tr("music.menu.albums"),
                    self.tr("music.count.albums", count=len(self.group_items("album")), default=f"{len(self.group_items('album'))}개"),
                ),
                (
                    "artists",
                    self.tr("music.menu.artists"),
                    self.tr("music.count.artists", count=len(self.group_items("artist")), default=f"{len(self.group_items('artist'))}명"),
                ),
                (
                    "genres",
                    self.tr("music.menu.genres", default="장르"),
                    self.tr("music.count.genres", count=len(self.group_items("genre")), default=f"{len(self.group_items('genre'))}개"),
                ),
            ]
            for key, label, sub in items:
                rr = menu[key]
                pressed = self.touch_down and rr.collidepoint(pygame.mouse.get_pos())
                card = rr.move(0, 1 if pressed else 0)
                shadow = pygame.Surface((card.w, card.h), pygame.SRCALPHA)
                pygame.draw.rect(shadow, (0, 0, 0, 44), (0, 3, card.w, card.h - 1), border_radius=16)
                self.screen.blit(shadow, card.topleft)
                base = self.tone(row_bg, 4 if self.theme == "light" else -2)
                if pressed:
                    base = self.tone(base, -8)
                pygame.draw.rect(self.screen, base, card, border_radius=16)
                pygame.draw.rect(self.screen, row_bd, card, width=1, border_radius=16)
                pygame.draw.rect(self.screen, accent, (card.x + 8, card.y + 10, 4, card.h - 20), border_radius=3)
                lt = self.font.render(label, True, pal["text"])
                self.screen.blit(lt, (card.x + 18, card.y + 14))
                sub_txt = str(sub)
                max_w = card.w - 40
                while sub_txt and self.small_font.size(sub_txt)[0] > max_w:
                    sub_txt = sub_txt[:-1]
                if sub_txt != str(sub) and len(sub_txt) >= 2:
                    sub_txt = sub_txt[:-1] + "…"
                st = self.small_font.render(sub_txt, True, self.tone(pal["text"], 38))
                self.screen.blit(st, (card.x + 18, card.y + 41))
                arrow = self.small_font.render(">", True, self.tone(pal["text"], 45))
                self.screen.blit(arrow, (card.right - 12 - arrow.get_width(), card.centery - arrow.get_height() // 2))
            self.draw_toast()
            return

        if self.music_view in ("ALBUMS", "ARTISTS", "ARTIST_ALBUMS", "GENRES"):
            search_r = self.music_search_rect()
            if self.music_view == "ARTIST_ALBUMS":
                pass
            else:
                search_bg = self.tone(pal["panel_bg"], 10 if self.editing_music_search else 0)
                pygame.draw.rect(self.screen, search_bg, search_r, border_radius=8)
                pygame.draw.rect(self.screen, pal["panel_border"], search_r, width=2, border_radius=8)
                q_text = self.music_search if self.music_search else self.tr("music.search")
                q_color = pal["text"] if self.music_search else self.tone(pal["text"], 70)
                qs = self.small_font.render(q_text, True, q_color)
                self.screen.blit(qs, (search_r.x + 8, search_r.y + 7))
                if self.editing_music_search and (pygame.time.get_ticks() // 500) % 2 == 0:
                    cx = search_r.x + 8 + qs.get_width() + 1
                    pygame.draw.line(self.screen, pal["text"], (cx, search_r.y + 6), (cx, search_r.y + 22), 2)

            rect = self.music_group_rect()
            panel_bg = self.tone(pal["panel_bg"], -8) if self.theme != "transparent" else (20, 20, 20, 120)
            if isinstance(panel_bg, tuple) and len(panel_bg) == 4:
                lay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                lay.fill(panel_bg)
                self.screen.blit(lay, (rect.x, rect.y))
            else:
                pygame.draw.rect(self.screen, panel_bg, rect, border_radius=8)
            pygame.draw.rect(self.screen, pal["panel_border"], rect, width=1, border_radius=8)

            if self.music_view == "ALBUMS":
                kind = "album"
                groups = self.group_items("album")
            elif self.music_view == "ARTISTS":
                kind = "artist"
                groups = self.group_items("artist")
            elif self.music_view == "GENRES":
                kind = "genre"
                groups = self.group_items("genre")
            else:
                kind = "album"
                groups = self.group_items("album", artist_filter=self.music_ctx_artist)
            row_h = 30
            max_rows = rect.h // row_h
            base = int(self.list_scroll)
            frac = self.list_scroll - base
            y_off = int(frac * row_h)
            old_clip = self.screen.get_clip()
            self.screen.set_clip(rect)
            for row in range(max_rows):
                item_pos = base + row
                if item_pos >= len(groups):
                    break
                name, cnt, _first_idx = groups[item_pos]
                y = rect.y + row * row_h - y_off
                row_rect = pygame.Rect(rect.x + 4, y + 2, rect.w - 8, row_h - 4)
                text_x = row_rect.x + 8
                if kind == "album":
                    art_size = row_rect.h - 4
                    art = self.album_art_for_album(name, size=art_size)
                    if art:
                        self.screen.blit(art, (row_rect.x + 6, row_rect.y + 2))
                    else:
                        pygame.draw.rect(self.screen, self.tone(pal["panel_border"], -25), (row_rect.x + 6, row_rect.y + 2, art_size, art_size), border_radius=6)
                    text_x = row_rect.x + 12 + art_size
                label = self.small_font.render(name, True, pal["text"])
                count = self.small_font.render(str(cnt), True, pal["text"])
                self.screen.blit(label, (text_x, row_rect.y + 6))
                self.screen.blit(count, (row_rect.right - count.get_width() - 8, row_rect.y + 6))
            self.screen.set_clip(old_clip)
            self.draw_scroll_hint(rect, len(groups), row_h)
            self.draw_toast()
            return

        if self.music_view == "QUEUE":
            list_rect = self.music_list_rect()
            panel_bg = self.tone(pal["panel_bg"], -8) if self.theme != "transparent" else (20, 20, 20, 120)
            if isinstance(panel_bg, tuple) and len(panel_bg) == 4:
                lay = pygame.Surface((list_rect.w, list_rect.h), pygame.SRCALPHA)
                lay.fill(panel_bg)
                self.screen.blit(lay, (list_rect.x, list_rect.y))
            else:
                pygame.draw.rect(self.screen, panel_bg, list_rect, border_radius=8)
            pygame.draw.rect(self.screen, pal["panel_border"], list_rect, width=1, border_radius=8)
            row_h = 30
            max_rows = list_rect.h // row_h
            base = int(self.list_scroll)
            frac = self.list_scroll - base
            y_off = int(frac * row_h)
            old_clip = self.screen.get_clip()
            self.screen.set_clip(list_rect)
            queue = self.play_queue_indices()
            for row in range(max_rows):
                item_pos = base + row
                if item_pos >= len(queue):
                    break
                idx = queue[item_pos]
                y = list_rect.y + row * row_h - y_off
                row_rect = pygame.Rect(list_rect.x + 4, y + 2, list_rect.w - 8, row_h - 4)
                if idx == self.music_index:
                    pygame.draw.rect(self.screen, self.ui_accent(), row_rect, border_radius=6)
                text_x = row_rect.x + 8
                if self.queue_source != "album":
                    art_size = row_rect.h - 4
                    art = self.album_art_for_album(self.track_meta_for(idx).get("album", ""), size=art_size)
                    if art:
                        self.screen.blit(art, (row_rect.x + 6, row_rect.y + 2))
                        text_x = row_rect.x + 12 + art_size
                dur = self.small_font.render(self.fmt_time(self.track_length_for(idx)), True, pal["text"])
                dur_x = row_rect.right - dur.get_width() - 8
                name_limit = max(10, dur_x - text_x)
                raw_name = self.track_name(idx)
                name = raw_name
                while name and self.small_font.size(name)[0] > name_limit:
                    name = name[:-1]
                if name != raw_name and len(name) >= 2:
                    name = name[:-1] + "…"
                label = self.small_font.render(name, True, pal["text"])
                self.screen.blit(label, (text_x, row_rect.y + 6))
                self.screen.blit(dur, (dur_x, row_rect.y + 6))
            self.screen.set_clip(old_clip)
            self.draw_scroll_hint(list_rect, len(queue), row_h)
            self.draw_toast()
            return

        if self.music_view == "LIST":
            search_r = self.music_search_rect()
            show_search = self.music_ctx_artist is None and self.music_ctx_album is None and self.music_ctx_genre is None
            if show_search:
                search_bg = self.tone(pal["panel_bg"], 10 if self.editing_music_search else 0)
                pygame.draw.rect(self.screen, search_bg, search_r, border_radius=8)
                pygame.draw.rect(self.screen, pal["panel_border"], search_r, width=2, border_radius=8)
                q_text = self.music_search if self.music_search else self.tr("music.search")
                q_color = pal["text"] if self.music_search else self.tone(pal["text"], 70)
                qs = self.small_font.render(q_text, True, q_color)
                self.screen.blit(qs, (search_r.x + 8, search_r.y + 7))
                if self.editing_music_search and (pygame.time.get_ticks() // 500) % 2 == 0:
                    cx = search_r.x + 8 + qs.get_width() + 1
                    pygame.draw.line(self.screen, pal["text"], (cx, search_r.y + 6), (cx, search_r.y + 22), 2)
                sort_btn = self.music_sort_button_rect()
                sort_key = f"music.sort.{self.music_sort}"
                self.draw_select_button(sort_btn, self.tr(sort_key), False)

            list_rect = self.music_list_rect()
            panel_bg = self.tone(pal["panel_bg"], -8) if self.theme != "transparent" else (20, 20, 20, 120)
            if isinstance(panel_bg, tuple) and len(panel_bg) == 4:
                lay = pygame.Surface((list_rect.w, list_rect.h), pygame.SRCALPHA)
                lay.fill(panel_bg)
                self.screen.blit(lay, (list_rect.x, list_rect.y))
            else:
                pygame.draw.rect(self.screen, panel_bg, list_rect, border_radius=8)
            pygame.draw.rect(self.screen, pal["panel_border"], list_rect, width=1, border_radius=8)
            row_h = 30
            max_rows = list_rect.h // row_h
            base = int(self.list_scroll)
            frac = self.list_scroll - base
            y_off = int(frac * row_h)
            old_clip = self.screen.get_clip()
            self.screen.set_clip(list_rect)
            filtered = self.filtered_music_indices()
            for row in range(max_rows):
                item_pos = base + row
                if item_pos >= len(filtered):
                    break
                idx = filtered[item_pos]
                y = list_rect.y + row * row_h - y_off
                row_rect = pygame.Rect(list_rect.x + 4, y + 2, list_rect.w - 8, row_h - 4)
                if idx == self.music_index and (self.is_music_busy() or self.music_paused):
                    pygame.draw.rect(self.screen, self.ui_accent(), row_rect, border_radius=6)
                text_x = row_rect.x + 8
                if self.music_ctx_album is None:
                    art_size = row_rect.h - 4
                    art = self.album_art_for_album(self.track_meta_for(idx).get("album", ""), size=art_size)
                    if art:
                        self.screen.blit(art, (row_rect.x + 6, row_rect.y + 2))
                        text_x = row_rect.x + 12 + art_size
                dur = self.small_font.render(self.fmt_time(self.track_length_for(idx)), True, pal["text"])
                dur_x = row_rect.right - dur.get_width() - 8
                name_limit = max(10, dur_x - text_x)
                raw_name = self.track_name(idx)
                name = raw_name
                while name and self.small_font.size(name)[0] > name_limit:
                    name = name[:-1]
                if name != raw_name and len(name) >= 2:
                    name = name[:-1] + "…"
                label = self.small_font.render(name, True, pal["text"])
                self.screen.blit(label, (text_x, row_rect.y + 6))
                self.screen.blit(dur, (dur_x, row_rect.y + 6))
            self.screen.set_clip(old_clip)
            self.draw_scroll_hint(list_rect, len(filtered), row_h)
            if show_search and self.sort_picker_open:
                opts = self.music_sort_option_rects()
                for key in ("name", "album", "artist"):
                    self.draw_select_button(opts[key], self.tr(f"music.sort.{key}"), self.music_sort == key)
            self.draw_toast()
            return

        layout = self.now_layout_rects()
        controls = self.music_control_rects()
        title = self.track_name(self.music_index) if self.music_files else self.tr("music.none")
        artist = self.track_meta_for(self.music_index).get("artist", self.tr("music.artist.unknown")) if self.music_files else ""
        length = self.current_track_len()
        pos = self.music_progress_drag_pos if self.music_progress_drag else self.current_track_pos()
        ratio = clamp((pos / length) if length > 0.1 else 0.0, 0.0, 1.0)
        accent = self.ui_accent()
        art_rect = layout["art"]
        queue_rect = controls["queue"]

        title_left = art_rect.x
        max_title_w = max(40, queue_rect.x - 8 - title_left)
        title_show = title
        while title_show and self.title_font.size(title_show)[0] > max_title_w:
            title_show = title_show[:-1]
        if title_show != title and len(title_show) >= 2:
            title_show = title_show[:-1] + "…"
        title_s = self.title_font.render(title_show, True, pal["text"])
        self.screen.blit(title_s, (title_left, layout["title_y"]))

        artist_show = artist
        while artist_show and self.small_font.size(artist_show)[0] > max_title_w:
            artist_show = artist_show[:-1]
        if artist_show != artist and len(artist_show) >= 2:
            artist_show = artist_show[:-1] + "…"
        artist_s = self.small_font.render(artist_show, True, self.tone(pal["text"], 40))
        self.screen.blit(artist_s, (title_left, layout["artist_y"]))

        album_name = self.track_meta_for(self.music_index).get("album", "") if self.music_files else ""
        art = self.album_art_for_album(album_name, size=art_rect.w)
        if art:
            self.screen.blit(art, art_rect.topleft)
        else:
            pygame.draw.rect(self.screen, self.tone(pal["panel_bg"], -8), art_rect, border_radius=12)
            pygame.draw.rect(self.screen, pal["panel_border"], art_rect, width=1, border_radius=12)

        prog = layout["progress"]
        pygame.draw.rect(self.screen, (20, 20, 20), prog, border_radius=6)
        pygame.draw.rect(self.screen, pal["panel_border"], prog, width=1, border_radius=6)
        fill_w = int(prog.w * ratio)
        if fill_w > 0:
            pygame.draw.rect(self.screen, accent, (prog.x, prog.y, fill_w, prog.h), border_radius=6)
        left_t = self.small_font.render(self.fmt_time(pos), True, pal["text"])
        right_t = self.small_font.render(self.fmt_time(length), True, pal["text"])
        self.screen.blit(left_t, (prog.x, layout["time_y"]))
        self.screen.blit(right_t, (prog.right - right_t.get_width(), layout["time_y"]))

        self.draw_icon_only(controls["prev"], "prev", "⏮", False)
        if self.music_paused:
            self.draw_icon_only(controls["play"], "play", "▶", False)
        elif self.is_music_busy():
            self.draw_icon_only(controls["play"], "pause", "⏸", False)
        else:
            self.draw_icon_only(controls["play"], "play", "▶", False)
        self.draw_icon_only(controls["next"], "next", "⏭", False)

        self.draw_icon_only(
            controls["shuffle"],
            "shuffle",
            "⇄",
            False,
            force_color=accent if self.shuffle_enabled else None,
        )
        self.draw_icon_only(
            controls["repeat"],
            "repeat",
            "↻",
            False,
            force_color=accent if self.repeat_mode != "off" else None,
        )
        self.draw_icon_only(controls["queue"], "queue", "☰", False)

        v = controls["volume"]
        pygame.draw.rect(self.screen, (25, 25, 25), v, border_radius=6)
        pygame.draw.rect(self.screen, pal["panel_border"], v, width=1, border_radius=6)
        vt = self.volume_track_rect(v)
        vw = int(vt.w * self.music_volume)
        if vw > 0:
            pygame.draw.rect(self.screen, accent, (vt.x, vt.y, vw, vt.h), border_radius=6)
        knob_x = vt.x + int(vt.w * self.music_volume)
        pygame.draw.circle(self.screen, accent, (knob_x, vt.centery), 5)
        vol_key = "volume0"
        if self.music_volume >= 0.75:
            vol_key = "volume3"
        elif self.music_volume >= 0.45:
            vol_key = "volume2"
        elif self.music_volume > 0.0:
            vol_key = "volume1"
        self.draw_icon_only(pygame.Rect(v.x + 3, v.y + 1, 18, v.h - 2), vol_key, "", False, force_color=(255, 255, 255))
        self.draw_toast()

    # 메인 이벤트 루프: 입력 처리 -> 상태 업데이트 -> 화면 렌더
    def loop(self):
        while True:
            if self.exit_requested:
                self.stop_video_process()
                self.stop_mpv()
                if self.mixer_ready:
                    pygame.mixer.music.stop()
                pygame.quit()
                return
            _dt = self.clock.tick(60)
            self.vk_sync_target()
            self.vk_lift_target = 26.0 if self.vk_visible else 0.0
            self.vk_lift += (self.vk_lift_target - self.vk_lift) * 0.22
            if abs(self.vk_lift_target - self.vk_lift) < 0.05:
                self.vk_lift = self.vk_lift_target

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.stop_video_process()
                    self.stop_mpv()
                    if self.mixer_ready:
                        pygame.mixer.music.stop()
                    pygame.quit()
                    return
                if self.boot_active:
                    continue

                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    if self.esc_hold_started == 0:
                        self.esc_hold_started = pygame.time.get_ticks()
                        self.esc_hold_handled = False
                    if self.screen_off:
                        rk = self.current_route_key()
                        if isinstance(rk, tuple) and rk and rk[0] != "LOCK":
                            self.lock_resume_route = rk
                        self.set_screen_off(False)
                        self.state = "LOCK"
                        self.esc_hold_handled = True
                    continue
                if ev.type == pygame.KEYUP and ev.key == pygame.K_ESCAPE:
                    if self.esc_hold_started > 0:
                        held = pygame.time.get_ticks() - self.esc_hold_started
                        if (not self.esc_hold_handled):
                            if self.state == "LOCK":
                                if held < self.lock_unlock_hold_ms:
                                    self.set_screen_off(True)
                            elif held < self.power_hold_ms:
                                turning_off = bool(self.screen_off or self.screen_off_anim_to >= 0.5)
                                self.set_screen_off(not turning_off)
                        self.esc_hold_started = 0
                        self.esc_hold_handled = False
                    continue

                if self.screen_off:
                    if ev.type == pygame.MOUSEBUTTONDOWN:
                        rk = self.current_route_key()
                        if isinstance(rk, tuple) and rk and rk[0] != "LOCK":
                            self.lock_resume_route = rk
                        self.set_screen_off(False)
                        self.state = "LOCK"
                    elif ev.type == pygame.FINGERDOWN:
                        rk = self.current_route_key()
                        if isinstance(rk, tuple) and rk and rk[0] != "LOCK":
                            self.lock_resume_route = rk
                        self.set_screen_off(False)
                        self.state = "LOCK"
                    continue

                if self.state == "LOCK":
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        if self.lock_home_button_rect().inflate(10, 10).collidepoint(ev.pos):
                            self.unlock_from_lock()
                    elif ev.type == pygame.FINGERDOWN:
                        tx = int(clamp(getattr(ev, "x", 0.0), 0.0, 1.0) * self.w)
                        ty = int(clamp(getattr(ev, "y", 0.0), 0.0, 1.0) * self.h)
                        if self.lock_home_button_rect().inflate(10, 10).collidepoint((tx, ty)):
                            self.unlock_from_lock()
                    continue
                if ev.type == self.music_event:
                    if self.music_backend == "mixer":
                        self.next_track(auto=True)
                    continue
                if self.state == "MUSIC" and self.music_backend == "mpv" and self.music_proc and self.music_proc.poll() is not None:
                    self.music_proc = None
                    self.next_track(auto=True)

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.handle_touch_down(self.content_touch_pos(ev.pos), ev.pos)
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (4, 5, 6, 7) and self.state == "PHOTO" and self.photo_view == "VIEWER" and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    if self.photo_share_sheet_active or self.photo_delete_confirm_active:
                        continue
                    if ev.button in (4, 6):
                        self.photo_zoom = float(clamp(self.photo_zoom + 0.15, self.photo_zoom_min, self.photo_zoom_max))
                    else:
                        self.photo_zoom = float(clamp(self.photo_zoom - 0.15, self.photo_zoom_min, self.photo_zoom_max))
                    self.photo_zoom_anim_active = False
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (4, 5, 6, 7) and self.state == "PHOTO" and self.photo_view == "VIEWER":
                    if self.photo_share_sheet_active or self.photo_delete_confirm_active:
                        continue
                    now_ms = pygame.time.get_ticks()
                    if now_ms - self.photo_wheel_nav_last_ms < self.photo_wheel_nav_gap_ms:
                        continue
                    files = self.filtered_photo_files()
                    if not files:
                        continue
                    cur = int(clamp(self.photo_index, 0, len(files) - 1))
                    if ev.button == 4:  # up wheel
                        nxt = int(clamp(cur - 1, 0, len(files) - 1))
                        self.start_photo_slide(files, nxt, -1)
                    elif ev.button == 6:  # left wheel (macOS reverse)
                        nxt = int(clamp(cur + 1, 0, len(files) - 1))
                        self.start_photo_slide(files, nxt, +1)
                    elif ev.button == 7:  # right wheel (macOS reverse)
                        nxt = int(clamp(cur - 1, 0, len(files) - 1))
                        self.start_photo_slide(files, nxt, -1)
                    else:  # down or right wheel
                        nxt = int(clamp(cur + 1, 0, len(files) - 1))
                        self.start_photo_slide(files, nxt, +1)
                    self.photo_wheel_nav_last_ms = now_ms
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (4, 5, 6, 7) and (
                    (self.state == "MUSIC" and self.music_view in ("LIST", "QUEUE", "ALBUMS", "ARTISTS", "ARTIST_ALBUMS", "GENRES"))
                    or (self.state == "VIDEO" and self.video_view == "LIST")
                    or (self.state == "TEXT" and self.text_view in ("LIST", "READER"))
                    or (self.state == "FILES" and self.files_view in ("ROOT", "LIST"))
                    or (self.state == "PHOTO" and self.photo_view == "GRID")
                    or (self.state == "SETTINGS_INFO" and not self.settings_info_name_popup_active)
                ):
                    if self.state == "VIDEO" and self.video_view == "LIST":
                        rect, total_items, row_h = self.video_scroll_info()
                    elif self.state == "TEXT":
                        if self.text_view == "LIST":
                            rect, total_items, row_h = self.text_scroll_info()
                        else:
                            rect = self.text_reader_body_rect()
                            total_items = max(1, len(self.text_reader_lines()))
                            row_h = self.text_reader_row_h()
                    elif self.state == "FILES":
                        rect, total_items, row_h = self.files_scroll_info()
                    elif self.state == "PHOTO":
                        rect, total_items, row_h = self.photo_scroll_info()
                    elif self.state == "SETTINGS_INFO":
                        rect, total_items, row_h = self.settings_info_scroll_info()
                    else:
                        h = self.music_list_rect().h if self.music_view in ("LIST", "QUEUE") else self.music_group_rect().h
                        row_h = 30
                        if self.music_view == "LIST":
                            total_items = len(self.filtered_music_indices())
                        elif self.music_view == "QUEUE":
                            total_items = len(self.play_queue_indices())
                        elif self.music_view == "ALBUMS":
                            total_items = len(self.group_items("album"))
                        elif self.music_view == "ARTIST_ALBUMS":
                            total_items = len(self.group_items("album", artist_filter=self.music_ctx_artist))
                        elif self.music_view == "GENRES":
                            total_items = len(self.group_items("genre"))
                        else:
                            total_items = len(self.group_items("artist"))
                        rect = pygame.Rect(0, 0, 0, h)
                    max_rows = self.scroll_page_rows(rect, row_h)
                    max_scroll = max(0, total_items - max_rows)
                    if ev.button in (4, 6):
                        self.set_list_scroll(clamp(self.list_scroll_target - 1, 0, max_scroll))
                    else:
                        self.set_list_scroll(clamp(self.list_scroll_target + 1, 0, max_scroll))
                elif ev.type == pygame.MOUSEWHEEL and self.state == "PHOTO" and self.photo_view == "VIEWER":
                    if self.photo_share_sheet_active or self.photo_delete_confirm_active:
                        continue
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_CTRL:
                        amt = getattr(ev, "y", 0)
                        if amt == 0:
                            amt = getattr(ev, "x", 0)
                        if amt > 0:
                            self.photo_zoom = float(clamp(self.photo_zoom + 0.15, self.photo_zoom_min, self.photo_zoom_max))
                        elif amt < 0:
                            self.photo_zoom = float(clamp(self.photo_zoom - 0.15, self.photo_zoom_min, self.photo_zoom_max))
                        self.photo_zoom_anim_active = False
                        continue
                    files = self.filtered_photo_files()
                    if not files:
                        continue
                    x_axis = float(getattr(ev, "x", 0.0))
                    y_axis = float(getattr(ev, "y", 0.0))
                    if abs(x_axis) > abs(y_axis):
                        axis = -x_axis  # macOS horizontal direction reverse
                    else:
                        axis = y_axis
                    if axis == 0:
                        continue
                    self.photo_wheel_nav_accum += float(axis)
                    if abs(self.photo_wheel_nav_accum) < self.photo_wheel_nav_step:
                        continue
                    now_ms = pygame.time.get_ticks()
                    if now_ms - self.photo_wheel_nav_last_ms < self.photo_wheel_nav_gap_ms:
                        continue
                    step = -1 if self.photo_wheel_nav_accum > 0 else +1
                    consume = self.photo_wheel_nav_step if self.photo_wheel_nav_accum > 0 else -self.photo_wheel_nav_step
                    self.photo_wheel_nav_accum -= consume
                    cur = int(clamp(self.photo_index, 0, len(files) - 1))
                    nxt = int(clamp(cur + step, 0, len(files) - 1))
                    self.start_photo_slide(files, nxt, +1 if step > 0 else -1)
                    self.photo_wheel_nav_last_ms = now_ms
                elif ev.type == pygame.MOUSEWHEEL and (
                    (self.state == "MUSIC" and self.music_view in ("LIST", "QUEUE", "ALBUMS", "ARTISTS", "ARTIST_ALBUMS", "GENRES"))
                    or (self.state == "VIDEO" and self.video_view == "LIST")
                    or (self.state == "TEXT" and self.text_view in ("LIST", "READER"))
                    or (self.state == "FILES" and self.files_view in ("ROOT", "LIST"))
                    or (self.state == "PHOTO" and self.photo_view == "GRID")
                    or (self.state == "SETTINGS_INFO" and not self.settings_info_name_popup_active)
                ):
                    if self.state == "VIDEO" and self.video_view == "LIST":
                        rect, total_items, row_h = self.video_scroll_info()
                    elif self.state == "TEXT":
                        if self.text_view == "LIST":
                            rect, total_items, row_h = self.text_scroll_info()
                        else:
                            rect = self.text_reader_body_rect()
                            total_items = max(1, len(self.text_reader_lines()))
                            row_h = self.text_reader_row_h()
                    elif self.state == "FILES":
                        rect, total_items, row_h = self.files_scroll_info()
                    elif self.state == "PHOTO":
                        rect, total_items, row_h = self.photo_scroll_info()
                    elif self.state == "SETTINGS_INFO":
                        rect, total_items, row_h = self.settings_info_scroll_info()
                    else:
                        h = self.music_list_rect().h if self.music_view in ("LIST", "QUEUE") else self.music_group_rect().h
                        row_h = 30
                        if self.music_view == "LIST":
                            total_items = len(self.filtered_music_indices())
                        elif self.music_view == "QUEUE":
                            total_items = len(self.play_queue_indices())
                        elif self.music_view == "ALBUMS":
                            total_items = len(self.group_items("album"))
                        elif self.music_view == "ARTIST_ALBUMS":
                            total_items = len(self.group_items("album", artist_filter=self.music_ctx_artist))
                        elif self.music_view == "GENRES":
                            total_items = len(self.group_items("genre"))
                        else:
                            total_items = len(self.group_items("artist"))
                        rect = pygame.Rect(0, 0, 0, h)
                    if not rect:
                        continue
                    max_rows = self.scroll_page_rows(rect, row_h)
                    max_scroll = max(0, total_items - max_rows)
                    dy = float(getattr(ev, "y", 0.0))
                    if dy == 0:
                        dy = float(getattr(ev, "x", 0.0))
                    if dy == 0:
                        continue
                    step = 1 if dy < 0 else -1
                    amount = max(1.0, abs(dy))
                    self.set_list_scroll(clamp(self.list_scroll_target + (step * amount), 0, max_scroll))
                elif ev.type == pygame.MOUSEMOTION and self.touch_down:
                    self.handle_touch_move(self.content_touch_pos(ev.pos), ev.pos)
                elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                    self.handle_touch_up(self.content_touch_pos(ev.pos), ev.pos)
                elif ev.type == pygame.FINGERDOWN and self.state == "PHOTO" and self.photo_view == "VIEWER":
                    if self.photo_share_sheet_active or self.photo_delete_confirm_active:
                        continue
                    self.photo_fingers[getattr(ev, "finger_id", 0)] = self.photo_touch_pos_from_finger(getattr(ev, "x", 0.0), getattr(ev, "y", 0.0))
                    self.update_photo_pinch_state()
                elif ev.type == pygame.FINGERMOTION and self.state == "PHOTO" and self.photo_view == "VIEWER":
                    if self.photo_share_sheet_active or self.photo_delete_confirm_active:
                        continue
                    fid = getattr(ev, "finger_id", 0)
                    if fid in self.photo_fingers:
                        self.photo_fingers[fid] = self.photo_touch_pos_from_finger(getattr(ev, "x", 0.0), getattr(ev, "y", 0.0))
                        self.update_photo_pinch_state()
                elif ev.type == pygame.FINGERUP and self.state == "PHOTO" and self.photo_view == "VIEWER":
                    fid = getattr(ev, "finger_id", 0)
                    if fid in self.photo_fingers:
                        del self.photo_fingers[fid]
                    self.update_photo_pinch_state()

                if ev.type == pygame.KEYDOWN and self.state == "CALC":
                    if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.handle_calc_button("=")
                        continue
                    if ev.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        self.handle_calc_button("CE")
                        continue
                    if ev.key == pygame.K_c:
                        self.handle_calc_button("C")
                        continue
                    ch = ev.unicode
                    if ch in "0123456789.+-*/()%=":
                        if ch == "*":
                            self.handle_calc_button("×")
                        elif ch == "/":
                            self.handle_calc_button("÷")
                        elif ch == "%":
                            self.handle_calc_button("%")
                        elif ch == "=":
                            self.handle_calc_button("=")
                        elif ch in "()":
                            self.handle_calc_button("()")
                        else:
                            self.handle_calc_button(ch)
                        continue
                if ev.type == pygame.KEYDOWN and self.state == "CALENDAR":
                    if ev.key == pygame.K_LEFT and self.calendar_can_prev():
                        self.calendar_shift_month(-1)
                        continue
                    if ev.key == pygame.K_RIGHT and self.calendar_can_next():
                        self.calendar_shift_month(+1)
                        continue

                if ev.type == pygame.KEYDOWN and self.state in ("SETTINGS", "SETTINGS_FULL", "SETTINGS_INFO") and self.editing_name:
                    if ev.key == pygame.K_BACKSPACE:
                        self.device_name = self.device_name[:-1]
                        self.save_pref()
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.editing_name = False
                        if self.state == "SETTINGS_INFO" and self.settings_info_name_popup_active:
                            self.settings_info_name_popup_active = False
                        self.save_pref()
                        self.toast(self.tr("toast.name_saved"))
                    elif ev.key == pygame.K_ESCAPE and self.state == "SETTINGS_INFO" and self.settings_info_name_popup_active:
                        self.settings_info_name_popup_active = False
                        self.editing_name = False
                    else:
                        ch = ev.unicode
                        if ch and ch.isprintable() and len(self.device_name) < 18:
                            self.device_name += ch
                            self.save_pref()

                if ev.type == pygame.KEYDOWN and self.state == "MUSIC":
                    if self.music_view in ("LIST", "ALBUMS", "ARTISTS", "ARTIST_ALBUMS", "GENRES") and self.editing_music_search:
                        if ev.key == pygame.K_BACKSPACE:
                            self.music_search = self.music_search[:-1]
                            self.set_list_scroll(0, snap=True)
                            continue
                        if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                            self.editing_music_search = False
                            continue
                        ch = ev.unicode
                        if ch and ch.isprintable() and len(self.music_search) < 40:
                            self.music_search += ch
                            self.set_list_scroll(0, snap=True)
                            continue
                    if ev.key == pygame.K_SPACE:
                        self.toggle_music()
                    elif ev.key == pygame.K_RIGHT:
                        self.next_track()
                    elif ev.key == pygame.K_LEFT:
                        self.prev_track()

                if ev.type == pygame.KEYDOWN and self.state == "VIDEO" and self.video_view == "LIST" and self.editing_video_search:
                    if ev.key == pygame.K_BACKSPACE:
                        self.video_search = self.video_search[:-1]
                        self.set_list_scroll(0, snap=True)
                        continue
                    if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                        self.editing_video_search = False
                        continue
                    ch = ev.unicode
                    if ch and ch.isprintable() and len(self.video_search) < 40:
                        self.video_search += ch
                        self.set_list_scroll(0, snap=True)
                        continue
                if ev.type == pygame.KEYDOWN and self.state == "TEXT" and self.text_view == "LIST" and self.editing_text_search:
                    if ev.key == pygame.K_BACKSPACE:
                        self.text_search = self.text_search[:-1]
                        self.set_list_scroll(0, snap=True)
                        continue
                    if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                        self.editing_text_search = False
                        continue
                    ch = ev.unicode
                    if ch and ch.isprintable() and len(self.text_search) < 40:
                        self.text_search += ch
                        self.set_list_scroll(0, snap=True)
                        continue
                if ev.type == pygame.KEYDOWN and self.state == "FILES" and self.files_view == "LIST" and self.editing_files_search:
                    if ev.key == pygame.K_BACKSPACE:
                        self.files_search = self.files_search[:-1]
                        self.set_list_scroll(0, snap=True)
                        continue
                    if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                        self.editing_files_search = False
                        continue
                    ch = ev.unicode
                    if ch and ch.isprintable() and len(self.files_search) < 40:
                        self.files_search += ch
                        self.set_list_scroll(0, snap=True)
                        continue
                if ev.type == pygame.KEYDOWN and self.state == "FILES" and self.files_view == "INFO" and self.files_info_rename_active:
                    if ev.key == pygame.K_BACKSPACE:
                        self.files_info_rename_text = self.files_info_rename_text[:-1]
                        continue
                    if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if self.rename_info_file():
                            self.files_info_rename_active = False
                        continue
                    if ev.key == pygame.K_ESCAPE:
                        self.files_info_rename_active = False
                        continue
                    ch = ev.unicode
                    if ch and ch.isprintable() and len(self.files_info_rename_text) < 64:
                        if ch not in "\\/:*?\"<>|":
                            self.files_info_rename_text += ch
                        continue
                if ev.type == pygame.KEYDOWN and self.state == "VIDEO" and self.video_view == "PLAYER":
                    filtered = self.filtered_video_files()
                    if ev.key == pygame.K_SPACE:
                        if self.video_playing:
                            self.pause_video_decode()
                        else:
                            self.resume_video_decode()
                    elif ev.key == pygame.K_LEFT and filtered:
                        self.play_video_at((self.video_index - 1) % len(filtered))
                    elif ev.key == pygame.K_RIGHT and filtered:
                        self.play_video_at((self.video_index + 1) % len(filtered))

            if self.esc_hold_started > 0 and (not self.esc_hold_handled):
                now_ms = pygame.time.get_ticks()
                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    held_ms = now_ms - self.esc_hold_started
                    if held_ms >= self.boot_hold_ms:
                        self.esc_hold_handled = True
                        self.start_boot_sequence()
                    elif self.state == "LOCK":
                        if held_ms >= self.lock_unlock_hold_ms:
                            self.esc_hold_handled = True
                            self.unlock_from_lock()
                    elif held_ms >= self.power_hold_ms:
                        if not self.power_confirm_active:
                            self.set_screen_off(False)
                            self.power_confirm_active = True
                            self.power_confirm_start = now_ms
                            self.pending_back_transition = False

            self.update_seek_hold()
            self.update_video_decode()
            self.update_video_ui_overlay()
            self.update_photo_ui_overlay()
            self.update_photo_zoom_anim()
            self.update_boot_sequence()
            self.update_list_scroll_anim()
            self.update_screen_off_anim()
            if self.bt_scanning and (pygame.time.get_ticks() - self.bt_scan_started >= self.bt_scan_ms):
                self.bt_scanning = False
                self.toast(self.tr("bt.scan.none", default="새 기기를 찾지 못했습니다"))
            now_ms = pygame.time.get_ticks()
            for dev in self.bt_devices:
                if dev.get("state") == "trying" and (now_ms - int(dev.get("started", 0)) >= self.bt_connect_ms):
                    dev["state"] = "failed"
                    dev["connected"] = False
            if self.lock_unlock_fade_active:
                p = clamp((pygame.time.get_ticks() - self.lock_unlock_fade_start) / max(1, self.lock_unlock_fade_ms), 0.0, 1.0)
                self.lock_unlock_fade_alpha = 1.0 - p
                if p >= 1.0:
                    self.lock_unlock_fade_active = False
                    self.lock_unlock_fade_alpha = 0.0
            route = self.current_route_key()
            if route != self.last_route:
                prev_state = self.last_route[0] if isinstance(self.last_route, tuple) and self.last_route else ""
                next_state = route[0] if isinstance(route, tuple) and route else ""
                skip_slide = (prev_state == "LOCK" or next_state == "LOCK")
                if self.last_frame_surface is not None and not skip_slide:
                    self.transition_active = True
                    self.transition_from = self.last_frame_surface.copy()
                    self.transition_start = pygame.time.get_ticks()
                    self.transition_dir = -1 if self.pending_back_transition else 1
                else:
                    self.transition_active = False
                    self.transition_from = None
                self.last_route = route
                self.pending_back_transition = False

            frame_surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA).convert_alpha()
            frame_surface.fill((0, 0, 0, 0))
            real_screen = self.screen
            self.screen = frame_surface
            if self.boot_active:
                self.draw_boot_sequence()
            elif self.state == "HOME":
                self.draw_home()
            elif self.state == "LOCK":
                self.draw_lockscreen()
            elif self.state == "SETTINGS":
                self.draw_settings()
            elif self.state == "SETTINGS_FULL":
                self.draw_settings_full()
            elif self.state == "SETTINGS_BT":
                self.draw_settings_bluetooth()
            elif self.state == "SETTINGS_SOUND":
                self.draw_settings_sound()
            elif self.state == "SETTINGS_DISPLAY":
                self.draw_settings_display()
            elif self.state == "SETTINGS_HOMELOCK":
                self.draw_settings_homelock()
            elif self.state == "SETTINGS_GENERAL":
                self.draw_settings_general()
            elif self.state == "SETTINGS_GENERAL_LANG":
                self.draw_settings_general_language()
            elif self.state == "SETTINGS_GENERAL_DATETIME":
                self.draw_settings_general_datetime()
            elif self.state == "SETTINGS_GENERAL_KEYBOARD":
                self.draw_settings_general_keyboard()
            elif self.state == "SETTINGS_GENERAL_RESET":
                self.draw_settings_general_reset()
            elif self.state == "SETTINGS_INFO":
                self.draw_settings_info()
            elif self.state == "SETTINGS_BATTERY":
                self.draw_settings_battery()
            elif self.state == "SETTINGS_WALLSTYLE":
                self.draw_settings_wallstyle()
            elif self.state == "SETTINGS_ACCENT":
                self.draw_settings_accent()
            elif self.state == "SETTINGS_WALLPAPER":
                self.draw_settings_wallpaper()
            elif self.state == "SETTINGS_EQ":
                self.draw_settings_eq()
            elif self.state == "POWER":
                self.draw_power()
            elif self.state == "VIDEO":
                self.draw_video()
            elif self.state == "TEXT":
                self.draw_textviewer()
            elif self.state == "FILES":
                self.draw_filesviewer()
            elif self.state == "MUSIC":
                self.draw_music()
            elif self.state == "PHOTO":
                self.draw_photo()
            elif self.state == "CALC":
                self.draw_calculator()
            elif self.state == "CALENDAR":
                self.draw_calendar()
            self.draw_power_confirm_overlay()
            self.screen = real_screen

            if self.transition_active and self.transition_from is not None:
                p = clamp((pygame.time.get_ticks() - self.transition_start) / max(1, self.transition_ms), 0.0, 1.0)
                if self.transition_dir == -1:
                    x_current = int(p * self.w)
                    x_bg = int((p - 1.0) * 24)
                    self.screen.fill((0, 0, 0))
                    self.screen.blit(frame_surface, (x_bg, 0))
                    self.screen.blit(self.transition_from, (x_current, 0))
                    edge = pygame.Surface((8, self.h), pygame.SRCALPHA)
                    edge.fill((0, 0, 0, 80))
                    self.screen.blit(edge, (x_current - 8, 0))
                else:
                    x_new = int((1.0 - p) * self.w)
                    x_old = int(-p * 28)
                    self.screen.fill((0, 0, 0))
                    self.screen.blit(self.transition_from, (x_old, 0))
                    self.screen.blit(frame_surface, (x_new, 0))
                if p >= 1.0:
                    self.transition_active = False
                    self.transition_from = None
            else:
                self.screen.blit(frame_surface, (0, 0))

            if self.vk_lift > 0.5:
                lift_px = int(round(self.vk_lift))
                shifted = self.screen.copy()
                self.screen.fill((0, 0, 0))
                self.screen.blit(shifted, (0, -lift_px))

            self.draw_virtual_keyboard()

            self.last_frame_surface = self.screen.copy()
            if self.screen_off_progress > 0.001:
                ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
                ov.fill((0, 0, 0, int(clamp(self.screen_off_progress, 0.0, 1.0) * 255)))
                self.screen.blit(ov, (0, 0))
            if self.lock_unlock_fade_alpha > 0.001:
                ov2 = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
                ov2.fill((0, 0, 0, int(clamp(self.lock_unlock_fade_alpha, 0.0, 1.0) * 180)))
                self.screen.blit(ov2, (0, 0))
            self.apply_brightness()
            pygame.display.flip()


if __name__ == "__main__":
    cfg = load_config()
    Shell(cfg).loop()
