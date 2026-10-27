
import sys
import json
import ctypes
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QWidget, QFrame, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QTextBrowser,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog,
    QCheckBox, QSlider, QSizePolicy
)

# ============================================================
# CONFIGURATION
# ============================================================



BASE_DIR = Path(__file__).resolve().parent

FILES = {
    "dictionary": BASE_DIR / "merged.json",
    "starting": BASE_DIR / "starting_stats.json",
    "analysis": BASE_DIR / "letter_analysis.json",
}

WINDOWS = sys.platform == "win32"

# Windows extended window styles
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000

user32 = ctypes.windll.user32 if WINDOWS else None

import ctypes
import pyautogui
import random


user32 = ctypes.windll.user32

overlay_hwnd = None
switch_hwnd = None
target_hwnd = None


def remember_target_window():
    """Remember the last foreground window that isn't our overlay."""
    global target_hwnd

    hwnd = user32.GetForegroundWindow()

    if hwnd and hwnd not in (overlay_hwnd, switch_hwnd):
        target_hwnd = hwnd
        
import ctypes
from ctypes import wintypes
import time
import random

user32 = ctypes.WinDLL("user32", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class INPUTUNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("padding", ctypes.c_byte * 32),  # INPUT union size on 64-bit Windows
    ]


class KEYBOARD_INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", INPUTUNION),
    ]


user32.SendInput.argtypes = [
    wintypes.UINT,
    ctypes.POINTER(KEYBOARD_INPUT),
    ctypes.c_int,
]
user32.SendInput.restype = wintypes.UINT


def send_key_event(character, key_up=False):
    event = KEYBOARD_INPUT()
    event.type = INPUT_KEYBOARD
    event.ki = KEYBDINPUT(
        0,
        ord(character),
        KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if key_up else 0),
        0,
        0,
    )

    ctypes.set_last_error(0)
    sent = user32.SendInput(
        1,
        ctypes.byref(event),
        ctypes.sizeof(KEYBOARD_INPUT),
    )

    if sent != 1:
        error = ctypes.get_last_error()
        raise OSError(
            f"SendInput failed: sent={sent}, "
            f"INPUT size={ctypes.sizeof(KEYBOARD_INPUT)}, "
            f"KEYBDINPUT size={ctypes.sizeof(KEYBDINPUT)}, "
            f"Windows error={error}"
        )


def sendinput_type(text):
    for character in text.lower():
        send_key_event(character)
        send_key_event(character, key_up=True)
        time.sleep(random.uniform(0.001, 0.1))
        
import ctypes
import time
import math
from ctypes import wintypes

user32 = ctypes.windll.user32

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


def send_mouse_event(x, y, flags):
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    abs_x = round(x * 65535 / max(1, screen_width - 1))
    abs_y = round(y * 65535 / max(1, screen_height - 1))

    event = INPUT()
    event.type = INPUT_MOUSE
    event.union.mi = MOUSEINPUT(
        abs_x,
        abs_y,
        0,
        flags | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
        0,
        None,
    )

    user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))

def send_mouse_click(x, y, duration=0.20, steps=35):
    """Teleport left of target, move horizontally, click mid-movement."""

    # 1. Teleport 80 pixels to the left of the target.
    start_x = x + 30
    start_y = y

    send_mouse_event(start_x, start_y, MOUSEEVENTF_MOVE)
    time.sleep(0.02)

    # 2. Select a random click step between 25 and 30.
    click_step = random.randint(25, 30)

    # 3. Move horizontally toward the target.
    for i in range(1, steps + 1):
        t = i / steps
        eased = t * t * (3 - 2 * t)

        current_x = round(start_x + (x - start_x) * eased)

        send_mouse_event(current_x, start_y, MOUSEEVENTF_MOVE)

        if i == click_step:
            send_mouse_event(
                current_x, start_y, MOUSEEVENTF_LEFTDOWN
            )
            time.sleep(0.03)
            send_mouse_event(
                current_x, start_y, MOUSEEVENTF_LEFTUP
            )

        time.sleep(duration / steps)

import threading


def type_word_into_target(word):
    global target_hwnd, target_point

    if not target_hwnd or not user32.IsWindow(target_hwnd):
        return

    # Prevent overlapping typing operations.
    if getattr(type_word_into_target, "busy", False):
        return

    type_word_into_target.busy = True

    point = target_point.target_position()

    X_OFFSET = 30  # Positive = right, negative = left
    point.setX(point.x() + X_OFFSET)

    def worker():
        try:
            user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(target_hwnd)
            time.sleep(0.15)
            

            # Click the center of the draggable marker.
            send_mouse_click(point.x(), point.y())

            # Wait 50 ms after clicking before typing.
            time.sleep(0.05)

            # # Random delay between characters.
            # for character in word.lower():
            #     pyautogui.write(character)
            #     time.sleep(random.uniform(0.001, 0.1))
            sendinput_type(word.lower())

        finally:
            type_word_into_target.busy = False

    threading.Thread(target=worker, daemon=True).start()
        
import time

from PySide6.QtCore import Qt, QTimer


class TargetPoint(QWidget):
    """Small draggable marker for the target application's input field."""

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setFixedSize(42, 42)

        label = QLabel("＋", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: white;
                background: rgba(220, 40, 40, 210);
                border: 2px solid white;
                border-radius: 21px;
                font-size: 24px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)

        self.drag_offset = None
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            self.move(
                event.globalPosition().toPoint() - self.drag_offset
            )

    def mouseReleaseEvent(self, event):
        self.drag_offset = None

    def target_position(self):
        """Return the center of the marker in screen coordinates."""
        return self.mapToGlobal(self.rect().center())

# ============================================================
# DATA
# ============================================================

dictionary = {}
starting_stats = {}
letter_analysis = {}
entries = []

def lower(value):
    return str(value if value is not None else "").lower()

def is_noun(data):
    return any(
        lower(m[0]) == "noun"
        for m in data.get("MEANINGS", [])
        if isinstance(m, list) and m
    )

def load_json(kind):
    global dictionary, starting_stats, letter_analysis, entries

    path, _ = QFileDialog.getOpenFileName(
        None,
        f"Select {kind} JSON",
        str(BASE_DIR),
        "JSON files (*.json)"
    )
    if not path:
        return

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        if kind == "dictionary":
            if not isinstance(data, dict):
                raise ValueError("Dictionary must be a JSON object.")

            dictionary = data
            entries = sorted(
                [
                    {
                        "word": lower(word.strip()),
                        "data": value,
                        "noun": is_noun(value),
                    }
                    for word, value in dictionary.items()
                    if word.strip()
                ],
                key=lambda item: item["word"]
            )

        elif kind == "starting":
            starting_stats = data

        elif kind == "analysis":
            letter_analysis = data

        status_label.setText(f"Loaded {kind}: {Path(path).name}")
        refresh_results()

    except Exception as exc:
        status_label.setText(f"Error loading {kind}: {exc}")

def auto_load():
    global dictionary, starting_stats, letter_analysis, entries

    for kind, path in FILES.items():
        if not path.exists():
            continue

        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)

            if kind == "dictionary" and isinstance(data, dict):
                dictionary = data
                entries = sorted(
                    [
                        {
                            "word": lower(word.strip()),
                            "data": value,
                            "noun": is_noun(value),
                        }
                        for word, value in dictionary.items()
                        if word.strip()
                    ],
                    key=lambda item: item["word"]
                )
            elif kind == "starting":
                starting_stats = data
            elif kind == "analysis":
                letter_analysis = data

        except Exception as exc:
            print(f"Could not load {path.name}: {exc}")

# ============================================================
# RANKING
# ============================================================

def target_letters():
    return {
        char for char in lower(ending_input.text())
        if "a" <= char <= "z"
    }

def is_target(word):
    targets = target_letters()
    return bool(word and word[-1] in targets)

def starting_rank(word):
    value = starting_stats.get(word[0], {}).get("rank")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("inf")

def commonness(word):
    value = letter_analysis.get(word[0], {}).get("word_count", 0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0

def sort_key(entry):
    word = entry["word"]

    return (
        0 if is_target(word) else 1,  # 1. Target ending
        starting_rank(word),          # 2. Starting rank, low first
        -commonness(word),            # 3. More dictionary words first
        0 if entry["noun"] else 1,    # 4. Nouns first on ties
        word,                         # 5. Alphabetical
    )

# ============================================================
# WINDOWS CLICK-THROUGH
# ============================================================

def set_click_through(widget, enabled):
    if not WINDOWS:
        return

    hwnd = int(widget.winId())

    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_LAYERED

    if enabled:
        style |= WS_EX_TRANSPARENT
    else:
        style &= ~WS_EX_TRANSPARENT

    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    # Tell Windows to refresh the extended styles.
    user32.SetWindowPos(
        hwnd, 0, 0, 0, 0, 0,
        0x0001 | 0x0002 | 0x0004 | 0x0010
    )

# ============================================================
# OVERLAY WINDOW
# ============================================================

class DictionaryOverlay(QWidget):
    def __init__(self):
        super().__init__()

        self.click_through = False
        self.drag_position = None
        self.current_matches = []

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setStyleSheet("""
            QWidget {
                color: #f0f2f6;
                font-family: Segoe UI;
                font-size: 13px;
            }

            QFrame#panel {
                background: rgba(16, 19, 24, 238);
                border: 1px solid rgba(150, 160, 190, 100);
                border-radius: 14px;
            }

            QLineEdit {
                background: rgba(35, 42, 54, 240);
                border: 1px solid #414c60;
                border-radius: 8px;
                padding: 9px;
                color: white;
                selection-background-color: #6366f1;
            }

            QLineEdit:focus {
                border: 1px solid #818cf8;
            }

            QPushButton {
                background: #293345;
                border: 1px solid #414c60;
                border-radius: 7px;
                padding: 7px;
            }

            QPushButton:hover {
                background: #3b4961;
            }

            QListWidget {
                background: rgba(22, 27, 35, 240);
                border: 1px solid #303947;
                border-radius: 8px;
                outline: none;
            }

            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #29313c;
            }

            QListWidget::item:selected {
                background: #394967;
                color: white;
            }

            QTextBrowser {
                background: rgba(28, 34, 43, 245);
                border: 1px solid #303947;
                border-radius: 8px;
                padding: 8px;
            }

            QLabel#muted {
                color: #a0a9ba;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        panel = QFrame()
        panel.setObjectName("panel")
        root.addWidget(panel)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)

        # Header
        header = QHBoxLayout()

        title = QLabel("dictionary")
        title.setStyleSheet("font-size: 17px; font-weight: bold;")

        self.details_button = QPushButton("details: off")
        self.details_button.setMaximumWidth(105)
        self.details_button.clicked.connect(self.toggle_details)

        self.opacity_button = QPushButton("opacity")
        self.opacity_button.setMaximumWidth(75)
        self.opacity_button.clicked.connect(self.change_opacity)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.details_button)
        header.addWidget(self.opacity_button)
        layout.addLayout(header)

        # File loading controls
        files = QGridLayout()

        for i, kind in enumerate(("dictionary", "starting", "analysis")):
            button = QPushButton(kind)
            button.clicked.connect(
                lambda checked=False, k=kind: load_json(k)
            )
            files.addWidget(button, 0, i)

        layout.addLayout(files)

        self.status_label = QLabel("Loading local JSON files...")
        self.status_label.setObjectName("muted")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Target ending letters
        layout.addWidget(QLabel("END_LETTERS — preferred word endings"))

        self.ending_input = QLineEdit()
        self.ending_input.setPlaceholderText("e.g. xzn")
        self.ending_input.textChanged.connect(refresh_results)
        layout.addWidget(self.ending_input)

        # Prefix search
        layout.addWidget(QLabel("SEARCH — starting letters"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type a word...")
        self.search_input.textChanged.connect(refresh_results)
        layout.addWidget(self.search_input)

        # Results
        self.result_count = QLabel("Type a prefix to search.")
        self.result_count.setObjectName("muted")
        layout.addWidget(self.result_count)

        self.results = QListWidget()
        self.results.setMinimumHeight(380)
        self.results.setMaximumHeight(600)
        self.results.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.results.itemClicked.connect(self.select_word)
        layout.addWidget(self.results, 1)

        # Details are hidden by default and can be toggled from the header.
        self.details_visible = False
        self.definition = QTextBrowser()
        self.definition.setOpenExternalLinks(False)
        self.definition.setMinimumHeight(180)
        self.definition.setVisible(False)
        layout.addWidget(self.definition)

        # Hotkey instructions
        hint = QLabel(
            "Ctrl+Shift+Space: toggle click-through\n"
            "Drag the header to move the overlay"
        )
        hint.setObjectName("muted")
        layout.addWidget(hint)

        # Taller overlay gives the word list substantially more room.
        self.resize(510, 900)
        self.move(80, 50)

        # Keyboard shortcuts work when this window is interactive.
        toggle_shortcut = QShortcut(
            QKeySequence("Ctrl+Shift+Space"), self
        )
        toggle_shortcut.activated.connect(self.toggle_click_through)

        self.show()

        # Apply click-through after the native window exists.
        QTimer.singleShot(300, self.apply_click_through)

    def apply_click_through(self):
        set_click_through(self, self.click_through)

    def toggle_click_through(self):
        self.click_through = not self.click_through
        self.apply_click_through()

        if self.click_through:
            self.status_label.setText(
                "CLICK-THROUGH ON — interact with the app underneath."
            )
        else:
            self.status_label.setText(
                "CLICK-THROUGH OFF — interact with the dictionary."
            )

        switch_button.update_mode()

    def change_opacity(self):
        current = self.windowOpacity()
        self.setWindowOpacity(0.65 if current > 0.8 else 0.95)

    def toggle_details(self):
        self.details_visible = not self.details_visible
        self.definition.setVisible(self.details_visible)
        self.details_button.setText(
            "details: on" if self.details_visible else "details: off"
        )

        # Give the definition panel room when enabled; return to the taller
        # results-focused layout when disabled.
        self.resize(510, 1080 if self.details_visible else 900)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if (
            self.drag_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.move(
                event.globalPosition().toPoint() - self.drag_position
            )
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def select_word(self, item):
        index = item.data(Qt.ItemDataRole.UserRole)
        if index is None:
            return

        entry = self.current_matches[index]
        word = entry["word"]
        data = entry["data"]

        html = [
            f"<h2 style='color:#a5b4fc'>{word}</h2>"
        ]

        meanings = list(data.get("MEANINGS", []))
        meanings.sort(
            key=lambda m: (
                0 if m and lower(m[0]) == "noun" else 1
            )
        )

        import html as html_module

        if not meanings:
            html.append("<p>No definitions available.</p>")

        for i, meaning in enumerate(meanings, 1):
            if not isinstance(meaning, list) or len(meaning) < 2:
                continue

            pos = html_module.escape(lower(meaning[0]))
            definition = html_module.escape(str(meaning[1]))

            html.append(
                f"<p><b style='color:#86efac'>{i}. ({pos})</b> "
                f"{definition}</p>"
            )

            # Optional related words from the third array.
            if len(meaning) > 2 and meaning[2]:
                related = ", ".join(
                    html_module.escape(lower(x))
                    for x in meaning[2]
                )
                html.append(
                    f"<p style='color:#a0a9ba'>Related: {related}</p>"
                )

        for key, label in (
            ("SYNONYMS", "synonyms"),
            ("ANTONYMS", "antonyms"),
        ):
            words = data.get(key, [])
            if words:
                safe_words = ", ".join(
                    html_module.escape(lower(x)) for x in words
                )
                html.append(
                    f"<p><b>{label}:</b> {safe_words}</p>"
                )

        self.definition.setHtml("".join(html))
        # Remove the current search prefix before typing.
        prefix = self.search_input.text().strip().lower()
        word_to_type = word.lower()

        if prefix and word_to_type.startswith(prefix):
            word_to_type = word_to_type[len(prefix):]

        type_word_into_target(word_to_type)

# ============================================================
# ALWAYS-CLICKABLE MODE SWITCH
# ============================================================

class ModeSwitch(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.button = QPushButton()
        self.button.setMinimumWidth(190)
        self.button.setMinimumHeight(42)
        self.button.clicked.connect(overlay.toggle_click_through)

        self.button.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(30, 41, 59, 245);
                border: 1px solid rgba(165, 180, 252, 180);
                border-radius: 10px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(67, 56, 202, 245);
            }
        """)

        layout.addWidget(self.button)
        self.update_mode()
        self.show()
        self.move(600, 50)

    def update_mode(self):
        if self.overlay.click_through:
            self.button.setText("CLICK-THROUGH: ON")
        else:
            self.button.setText("CLICK-THROUGH: OFF")

# ============================================================
# SEARCH
# ============================================================

def refresh_results(*args):
    if not hasattr(overlay, "search_input"):
        return

    prefix = lower(overlay.search_input.text().strip())

    overlay.results.clear()
    overlay.definition.clear()
    overlay.current_matches = []

    if not prefix:
        overlay.result_count.setText("Type a prefix to search.")
        return

    # Find matching prefix candidates.
    # Dictionary is already alphabetically sorted.
    lo, hi = 0, len(entries)

    while lo < hi:
        mid = (lo + hi) // 2
        if entries[mid]["word"] < prefix:
            lo = mid + 1
        else:
            hi = mid

    matches = []

    for entry in entries[lo:]:
        if not entry["word"].startswith(prefix):
            break
        matches.append(entry)

    # Apply all priorities.
    matches.sort(key=sort_key)

    total = len(matches)
    matches = matches[:150]
    overlay.current_matches = matches

    overlay.result_count.setText(
        f"{total:,} matches" +
        (" — first 150 shown" if total > 150 else "")
    )

    for index, entry in enumerate(matches):
        word = entry["word"]

        tags = []
        if is_target(word):
            tags.append("★")
        if entry["noun"]:
            tags.append("noun")

        rank = starting_rank(word)
        rank_text = f"r{int(rank)}" if rank != float("inf") else "r?"

        text = word
        if tags:
            text += "    " + " ".join(tags)
        text += f"    {rank_text}"

        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, index)

        overlay.results.addItem(item)

# ============================================================
# START
# ============================================================



app = QApplication(sys.argv)
app.setApplicationName("Dictionary Overlay")

overlay = DictionaryOverlay()

# Give the widgets convenient global names for the callbacks.
ending_input = overlay.ending_input
status_label = overlay.status_label

switch_button = ModeSwitch(overlay)

overlay_hwnd = int(overlay.winId())
switch_hwnd = int(switch_button.winId())

# Periodically remember the last application window.
target_timer = QTimer()
target_timer.timeout.connect(remember_target_window)
target_timer.start(200)

target_point = TargetPoint()
target_point.move(500, 500)  # Initial screen position; drag it where needed.

auto_load()
overlay.status_label.setText(
    f"{len(entries):,} words loaded. "
    "Use the separate mode switch to toggle click-through."
)

sys.exit(app.exec())
