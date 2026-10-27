
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
    QCheckBox, QSlider
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

from PySide6.QtCore import QTimer

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


def type_word_into_target(word):
    """Focus the application underneath and type the selected word."""
    global target_hwnd

    if not target_hwnd or not user32.IsWindow(target_hwnd):
        return

    user32.SetForegroundWindow(target_hwnd)

    # Give Windows a moment to switch focus.
    for character in word.lower():
        pyautogui.write(character, interval=0)
        QTimer.singleShot(
            0,
            lambda: None
        )
        import time
        time.sleep(random.uniform(0.001, 0.1))

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

        self.opacity_button = QPushButton("opacity")
        self.opacity_button.setMaximumWidth(75)
        self.opacity_button.clicked.connect(self.change_opacity)

        header.addWidget(title)
        header.addStretch()
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
        self.results.setMinimumHeight(160)
        self.results.setMaximumHeight(270)
        self.results.itemClicked.connect(self.select_word)
        layout.addWidget(self.results)

        # Definition
        self.definition = QTextBrowser()
        self.definition.setOpenExternalLinks(False)
        self.definition.setMinimumHeight(150)
        layout.addWidget(self.definition)

        # Hotkey instructions
        hint = QLabel(
            "Ctrl+Shift+Space: toggle click-through\n"
            "Drag the header to move the overlay"
        )
        hint.setObjectName("muted")
        layout.addWidget(hint)

        self.resize(510, 690)
        self.move(80, 80)

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
        type_word_into_target(word)

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
        self.move(80, 785)

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

auto_load()
overlay.status_label.setText(
    f"{len(entries):,} words loaded. "
    "Use the separate mode switch to toggle click-through."
)

sys.exit(app.exec())
