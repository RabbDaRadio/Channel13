import random
import sys
import shutil
import threading
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import QTimer, Qt, QUrl, QSize, QRectF, QPoint, QRect, QPointF, QEasingCurve, QPropertyAnimation, QEvent, Property, Signal
from PySide6.QtGui import QPainter, QPixmap, QColor, QPainterPath, QImage, QPen, QIcon, QLinearGradient, QBrush, QRadialGradient, QFont
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QDialog, QDateTimeEdit,
    QDialogButtonBox, QMessageBox, QLineEdit,
    QScrollArea, QCheckBox, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QComboBox, QListWidget, QPlainTextEdit, QGraphicsDropShadowEffect,
    QApplication, QInputDialog, QSlider, QProgressBar, QMenu, QAbstractItemView,
    QTabBar, QStyledItemDelegate, QStyleOptionViewItem, QStyle, QWidgetAction,
    QGridLayout, QSizePolicy
)

from database import (
    get_setting as _orig_get_setting, set_setting as _orig_set_setting,
    add_task, get_tasks, update_task, delete_task,
    add_syllabus_item, get_syllabus_items, update_syllabus_item,
    delete_syllabus_item, get_subject_progress,
    get_quotes, add_quote, delete_quote, get_subjects, add_subject,
    # Dynamic Categories & Sorting
    get_syllabus_items_dynamic, update_syllabus_completion,
    rename_subject, delete_subject, reorder_subjects,
    get_categories, add_category, update_category, delete_category,
    reorder_categories, move_syllabus_item, set_active_database,
    set_master_setting, get_master_setting, get_database_path, init_db, reorder_syllabus_items,
    reset_app_database, reset_progress_database
)

APP_VERSION = "1.2.0"

MODE_SPECIFIC_KEYS = {
    "theme_preset",
    "ui_opacity",
    "wallpaper_path",
    "layout_locked",
    "layout_responsive",
    "theme_presets",
}

def get_setting(key, default=None):
    is_mode_specific = (
        key in MODE_SPECIFIC_KEYS or
        key.startswith("tile_geom_") or
        key.startswith("tile_theme_") or
        key.startswith("tile_font_size_")
    )
    if is_mode_specific:
        current_mode = _orig_get_setting("ui_mode", "aesthetic")
        prefixed_key = f"{current_mode}_{key}"
        
        # Check if setting exists under the mode prefix
        val = _orig_get_setting(prefixed_key, None)
        if val is not None:
            return val
            
        # Fallbacks for empty mode-specific configurations
        if key == "theme_preset":
            return "Walnut" if current_mode == "lite" else "Smoked Glass"
        elif key == "ui_opacity":
            return "1.0" if current_mode == "lite" else "0.19"
        elif key == "wallpaper_path":
            return "" if current_mode == "lite" else "asset/motion/vid1999.mpg"
        elif key == "layout_locked":
            return "1"
        elif key == "layout_responsive":
            return "1"
        elif key == "theme_presets":
            import json
            default_preset = {
                "name": "Preset 1",
                "theme": "Walnut" if current_mode == "lite" else "Smoked Glass",
                "opacity": 1.0 if current_mode == "lite" else 0.19,
                "wallpaper": "" if current_mode == "lite" else "asset/motion/vid1999.mpg",
                "cards": {}
            }
            return json.dumps([default_preset])
        elif key.startswith("tile_theme_"):
            return ""
        elif key.startswith("tile_font_size_"):
            return "0"
            
        return default
        
    return _orig_get_setting(key, default)

def set_setting(key, value):
    is_mode_specific = (
        key in MODE_SPECIFIC_KEYS or
        key.startswith("tile_geom_") or
        key.startswith("tile_theme_") or
        key.startswith("tile_font_size_")
    )
    if is_mode_specific:
        current_mode = _orig_get_setting("ui_mode", "aesthetic")
        prefixed_key = f"{current_mode}_{key}"
        _orig_set_setting(prefixed_key, value)
    else:
        _orig_set_setting(key, value)


def theme(start, end, accent, button, panel, field, border):
    return {
        "start": start,
        "end": end,
        "accent": accent,
        "button": button,
        "panel": panel,
        "field": field,
        "border": border,
    }


THEMES = {
    "Burgundy": theme("#2a0613", "#7f1d1d", "#fca5a5", "#5f1725", "rgba(52, 18, 28, 218)", "rgba(36, 13, 20, 226)", "rgba(252, 165, 165, 56)"),
    "Crimson Night": theme("#19040a", "#991b1b", "#fecaca", "#7f1d1d", "rgba(56, 16, 22, 218)", "rgba(38, 10, 15, 226)", "rgba(254, 202, 202, 54)"),
    "Rosewood": theme("#230812", "#be123c", "#fda4af", "#881337", "rgba(58, 18, 32, 218)", "rgba(37, 11, 20, 226)", "rgba(253, 164, 175, 54)"),
    "Midnight Teal": theme("#021617", "#0f766e", "#5eead4", "#115e59", "rgba(7, 42, 43, 218)", "rgba(4, 27, 28, 226)", "rgba(94, 234, 212, 54)"),
    "Deep Aqua": theme("#061826", "#0369a1", "#7dd3fc", "#075985", "rgba(8, 38, 55, 218)", "rgba(5, 25, 36, 226)", "rgba(125, 211, 252, 54)"),
    "Royal Indigo": theme("#130b2f", "#4338ca", "#c4b5fd", "#3730a3", "rgba(27, 20, 64, 218)", "rgba(18, 13, 42, 226)", "rgba(196, 181, 253, 54)"),
    "Violet Storm": theme("#1e0636", "#7e22ce", "#d8b4fe", "#6b21a8", "rgba(40, 19, 70, 218)", "rgba(27, 13, 46, 226)", "rgba(216, 180, 254, 54)"),
    "Forest": theme("#06160d", "#166534", "#86efac", "#14532d", "rgba(12, 43, 24, 218)", "rgba(7, 28, 15, 226)", "rgba(134, 239, 172, 54)"),
    "Evergreen": theme("#03130c", "#047857", "#6ee7b7", "#065f46", "rgba(6, 39, 28, 218)", "rgba(4, 25, 18, 226)", "rgba(110, 231, 183, 54)"),
    "Olive Slate": theme("#12140b", "#4d7c0f", "#bef264", "#3f6212", "rgba(34, 40, 19, 218)", "rgba(23, 27, 13, 226)", "rgba(190, 242, 100, 50)"),
    "Amber Study": theme("#1c1003", "#b45309", "#fcd34d", "#92400e", "rgba(48, 31, 12, 218)", "rgba(32, 21, 8, 226)", "rgba(252, 211, 77, 50)"),
    "Copper": theme("#1f0b05", "#c2410c", "#fdba74", "#9a3412", "rgba(54, 24, 12, 218)", "rgba(35, 16, 8, 226)", "rgba(253, 186, 116, 50)"),
    "Bronze": theme("#17100b", "#854d0e", "#facc15", "#713f12", "rgba(42, 32, 18, 218)", "rgba(28, 21, 12, 226)", "rgba(250, 204, 21, 46)"),
    "Graphite": theme("#09090b", "#3f3f46", "#d4d4d8", "#27272a", "rgba(31, 31, 35, 218)", "rgba(20, 20, 23, 226)", "rgba(212, 212, 216, 44)"),
    "Carbon": theme("#020617", "#1e293b", "#cbd5e1", "#334155", "rgba(17, 24, 39, 218)", "rgba(10, 15, 25, 226)", "rgba(203, 213, 225, 44)"),
    "Navy": theme("#07111f", "#1d4ed8", "#93c5fd", "#1e40af", "rgba(15, 34, 68, 218)", "rgba(9, 23, 45, 226)", "rgba(147, 197, 253, 54)"),
    "Cobalt": theme("#061124", "#2563eb", "#bfdbfe", "#1d4ed8", "rgba(14, 34, 78, 218)", "rgba(8, 23, 52, 226)", "rgba(191, 219, 254, 54)"),
    "Ocean": theme("#031a24", "#0e7490", "#67e8f9", "#155e75", "rgba(6, 42, 56, 218)", "rgba(4, 27, 37, 226)", "rgba(103, 232, 249, 54)"),
    "Slate Blue": theme("#0f172a", "#475569", "#bae6fd", "#334155", "rgba(29, 39, 58, 218)", "rgba(18, 26, 40, 226)", "rgba(186, 230, 253, 46)"),
    "Plum": theme("#1b1024", "#86198f", "#f0abfc", "#701a75", "rgba(43, 24, 54, 218)", "rgba(29, 16, 36, 226)", "rgba(240, 171, 252, 50)"),
    "Magenta": theme("#21051d", "#c026d3", "#f5d0fe", "#a21caf", "rgba(53, 18, 51, 218)", "rgba(35, 10, 34, 226)", "rgba(245, 208, 254, 50)"),
    "Cherry": theme("#21040d", "#e11d48", "#fecdd3", "#be123c", "rgba(57, 16, 30, 218)", "rgba(37, 9, 19, 226)", "rgba(254, 205, 211, 50)"),
    "Walnut": theme("#170f0b", "#57534e", "#e7e5e4", "#44403c", "rgba(39, 31, 27, 218)", "rgba(25, 20, 17, 226)", "rgba(231, 229, 228, 42)"),
    "Moss": theme("#0d1308", "#365314", "#d9f99d", "#4d7c0f", "rgba(29, 40, 18, 218)", "rgba(19, 26, 12, 226)", "rgba(217, 249, 157, 46)"),
    "Emerald Solid": theme("#052e1b", "#052e1b", "#86efac", "#047857", "rgba(10, 49, 31, 218)", "rgba(6, 31, 20, 226)", "rgba(134, 239, 172, 50)"),
    "Wine Solid": theme("#3f0715", "#3f0715", "#fecdd3", "#9f1239", "rgba(62, 18, 30, 218)", "rgba(40, 11, 20, 226)", "rgba(254, 205, 211, 48)"),
    "Ink Solid": theme("#111827", "#111827", "#e0f2fe", "#374151", "rgba(31, 41, 55, 218)", "rgba(17, 24, 39, 226)", "rgba(224, 242, 254, 42)"),
    "Aubergine Solid": theme("#2e1065", "#2e1065", "#ddd6fe", "#5b21b6", "rgba(52, 33, 93, 218)", "rgba(35, 22, 62, 226)", "rgba(221, 214, 254, 48)"),
    "Teal Solid": theme("#134e4a", "#134e4a", "#99f6e4", "#0f766e", "rgba(24, 78, 74, 218)", "rgba(14, 50, 48, 226)", "rgba(153, 246, 228, 50)"),
    "Blueberry": theme("#10163a", "#312e81", "#c7d2fe", "#3730a3", "rgba(28, 34, 82, 218)", "rgba(18, 23, 54, 226)", "rgba(199, 210, 254, 50)"),
    "Solar Dusk": theme("#1c1204", "#7c2d12", "#fed7aa", "#9a3412", "rgba(49, 29, 12, 218)", "rgba(33, 20, 8, 226)", "rgba(254, 215, 170, 46)"),
    "Deep Pink": theme("#220617", "#9d174d", "#f9a8d4", "#831843", "rgba(53, 18, 38, 218)", "rgba(35, 10, 25, 226)", "rgba(249, 168, 212, 50)"),
    "Ice Dark": theme("#071318", "#164e63", "#a5f3fc", "#155e75", "rgba(14, 39, 48, 218)", "rgba(9, 26, 32, 226)", "rgba(165, 243, 252, 48)"),
    "Vibe": theme("#061826", "#0f766e", "#99f6e4", "#0f766e", "rgba(16, 42, 45, 190)", "rgba(8, 26, 29, 176)", "rgba(153, 246, 228, 42)"),
    "Glass": theme("#071318", "#164e63", "#e0f2fe", "#155e75", "rgba(255, 255, 255, 82)", "rgba(255, 255, 255, 58)", "rgba(255, 255, 255, 32)"),
    "Smoked Glass": theme("#020617", "#0f172a", "#e0f2fe", "#334155", "rgba(8, 12, 18, 128)", "rgba(8, 12, 18, 92)", "rgba(255, 255, 255, 28)"),
}


DEFAULT_GEOMETRIES = {
    "quotes": (0, 10, 1150, 60),
    "focus": (0, 80, 490, 260),
    "countdown": (502, 80, 280, 260),
    "progress": (794, 80, 356, 260),
    "syllabus": (0, 352, 782, 540),
    "extras": (794, 352, 356, 265),
    "daily": (794, 629, 356, 265),
}



class CountdownEditDialog(QDialog):
    def __init__(self, current_datetime, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Countdown Target")
        self.resize(350, 120)

        layout = QVBoxLayout(self)

        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_edit.setDateTime(current_datetime)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(QLabel("Select NEET exam date/time:"))
        layout.addWidget(self.datetime_edit)
        layout.addWidget(buttons)

    def selected_datetime(self):
        return self.datetime_edit.dateTime().toPython()


class QuoteManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Quotes")
        self.resize(560, 420)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.quote_list = QListWidget()
        self.quote_edit = QPlainTextEdit()
        self.quote_edit.setPlaceholderText("Add a custom quote...")
        self.quote_edit.setMaximumHeight(90)

        button_row = QHBoxLayout()
        add_btn = QPushButton("Add Quote")
        add_btn.setObjectName("AddButton")
        add_btn.clicked.connect(self.add_current_quote)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("DeleteButton")
        delete_btn.clicked.connect(self.delete_selected_quote)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        button_row.addWidget(add_btn)
        button_row.addWidget(delete_btn)
        button_row.addStretch()
        button_row.addWidget(close_btn)

        layout.addWidget(QLabel("Quotes used by the quote area:"))
        layout.addWidget(self.quote_list)
        layout.addWidget(self.quote_edit)
        layout.addLayout(button_row)

        self.reload_quotes()

    def reload_quotes(self):
        self.quote_list.clear()

        for quote_id, text in get_quotes():
            item_text = f"{quote_id}: {text}"
            self.quote_list.addItem(item_text)

    def add_current_quote(self):
        text = self.quote_edit.toPlainText().strip()

        if not text:
            return

        add_quote(text)
        self.quote_edit.clear()
        self.reload_quotes()

    def delete_selected_quote(self):
        item = self.quote_list.currentItem()

        if not item:
            return

        quote_id = int(item.text().split(":", 1)[0])
        delete_quote(quote_id)
        self.reload_quotes()


class TeamMakerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Teammaker")
        self.resize(680, 620)
        self._syncing_player_count = False
        if parent:
            self.setStyleSheet(parent.styleSheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Teammaker")
        title.setProperty("class", "CardTitle")

        self.names_edit = QPlainTextEdit()
        self.names_edit.setPlaceholderText("Player names, one per line or comma-separated")
        self.names_edit.setMinimumHeight(130)
        self.names_edit.textChanged.connect(self.sync_player_count)

        config_row = QHBoxLayout()
        self.player_count_box = QSpinBox()
        self.player_count_box.setRange(1, 500)
        self.player_count_box.setValue(10)

        self.team_size_box = QSpinBox()
        self.team_size_box.setRange(1, 100)
        self.team_size_box.setValue(5)

        self.team_count_box = QSpinBox()
        self.team_count_box.setRange(1, 100)
        self.team_count_box.setValue(2)

        config_row.addWidget(QLabel("Players"))
        config_row.addWidget(self.player_count_box)
        config_row.addWidget(QLabel("Team size"))
        config_row.addWidget(self.team_size_box)
        config_row.addWidget(QLabel("Teams"))
        config_row.addWidget(self.team_count_box)

        self.rules_edit = QPlainTextEdit()
        self.rules_edit.setPlaceholderText("Custom rules, one per line. Example: Player A cannot be with Player B")
        self.rules_edit.setMaximumHeight(90)

        button_row = QHBoxLayout()
        make_btn = QPushButton("Make")
        make_btn.setObjectName("AddButton")
        make_btn.clicked.connect(self.make_teams)

        redo_btn = QPushButton("Randomize Again")
        redo_btn.clicked.connect(self.make_teams)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.clear_result)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        button_row.addWidget(make_btn)
        button_row.addWidget(redo_btn)
        button_row.addWidget(back_btn)
        button_row.addStretch()
        button_row.addWidget(close_btn)

        self.result_edit = QPlainTextEdit()
        self.result_edit.setReadOnly(True)
        self.result_edit.setPlaceholderText("Randomized teams will appear here.")
        self.result_edit.setMinimumHeight(180)

        layout.addWidget(title)
        layout.addWidget(QLabel("Players"))
        layout.addWidget(self.names_edit)
        layout.addLayout(config_row)
        layout.addWidget(QLabel("Custom rules"))
        layout.addWidget(self.rules_edit)
        layout.addLayout(button_row)
        layout.addWidget(self.result_edit)

    def sync_player_count(self):
        if self._syncing_player_count:
            return

        names_count = len(self.player_names())
        if not names_count:
            return

        self._syncing_player_count = True
        self.player_count_box.setValue(names_count)
        self._syncing_player_count = False

    def player_names(self):
        raw = self.names_edit.toPlainText().replace(",", "\n")
        names = []
        seen = set()

        for line in raw.splitlines():
            name = line.strip()
            key = name.casefold()
            if name and key not in seen:
                names.append(name)
                seen.add(key)

        return names

    def forbidden_pairs(self):
        pairs = set()

        for line in self.rules_edit.toPlainText().splitlines():
            text = line.strip()
            if not text:
                continue

            lowered = text.casefold()
            if " cannot be with " in lowered:
                left, right = lowered.split(" cannot be with ", 1)
            elif " can't be with " in lowered:
                left, right = lowered.split(" can't be with ", 1)
            elif "," in lowered:
                left, right = lowered.split(",", 1)
            elif "-" in lowered:
                left, right = lowered.split("-", 1)
            else:
                continue

            a = left.strip()
            b = right.strip()
            if a and b:
                pairs.add(frozenset((a, b)))

        return pairs

    def teams_are_valid(self, teams, forbidden_pairs):
        for team in teams:
            members = [name.casefold() for name in team]
            for index, member in enumerate(members):
                for other in members[index + 1:]:
                    if frozenset((member, other)) in forbidden_pairs:
                        return False
        return True

    def make_teams(self):
        names = self.player_names()
        requested_players = self.player_count_box.value()
        team_size = self.team_size_box.value()
        team_count = self.team_count_box.value()
        capacity = team_size * team_count

        if not names:
            QMessageBox.warning(self, "Missing players", "Enter player names first.")
            return

        if requested_players > len(names):
            QMessageBox.warning(self, "Not enough players", "Player count is higher than the names provided.")
            return

        if requested_players > capacity:
            QMessageBox.warning(self, "Teams too small", "Team size x number of teams cannot fit all selected players.")
            return

        selected_names = names[:requested_players]
        forbidden_pairs = self.forbidden_pairs()

        for _ in range(1000):
            shuffled = selected_names[:]
            random.shuffle(shuffled)
            teams = [[] for _ in range(team_count)]

            for index, name in enumerate(shuffled):
                teams[index % team_count].append(name)

            if any(len(team) > team_size for team in teams):
                continue

            if self.teams_are_valid(teams, forbidden_pairs):
                self.show_result(teams)
                return

        QMessageBox.warning(
            self,
            "No valid result",
            "Could not satisfy the custom rules after many attempts. Try fewer restrictions.",
        )

    def show_result(self, teams):
        lines = []
        for index, team in enumerate(teams, start=1):
            members = ", ".join(team) if team else "Empty"
            lines.append(f"Team {index}: {members}")
        self.result_edit.setPlainText("\n".join(lines))

    def clear_result(self):
        self.result_edit.clear()


class StatusIconButton(QPushButton):
    def __init__(self, parent_window, table, row, item_id, subject, field, state=0):
        super().__init__()
        self.parent_window = parent_window
        self.table = table
        self.row = row
        self.item_id = item_id
        self.subject = subject
        self.field = field
        self.state = int(state or 0)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("class", "StatusIconButton")
        self.setIconSize(QSize(22, 22))
        self.setStyleSheet("background: transparent; border: none; padding: 0px; margin: 0px;")
        self.clicked.connect(self.handle_click)
        self.asset_pixmap = QPixmap()
        self.apply_state()

    @property
    def current_row(self):
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                cell_w = self.table.cellWidget(r, c)
                if cell_w:
                    if cell_w == self or cell_w.findChild(self.__class__) == self:
                        return r
        return self.row

    def enterEvent(self, event):
        super().enterEvent(event)
        if hasattr(self.table, "on_row_hovered"):
            self.table.on_row_hovered(self.current_row)
        if hasattr(self.parent_window, "hover_tooltip") and self.parent_window.hover_tooltip:
            self.parent_window.hover_tooltip.setText(self.field)
            self.parent_window.hover_tooltip.adjustSize()
            pos = self.mapTo(self.parent_window, QPoint(0, 0))
            btn_center_x = pos.x() + self.width() / 2
            tooltip_w = self.parent_window.hover_tooltip.width()
            tooltip_h = self.parent_window.hover_tooltip.height()
            target_x = btn_center_x - tooltip_w / 2
            target_y = pos.y() - tooltip_h - 6
            self.parent_window.hover_tooltip.move(int(target_x), int(target_y))
            self.parent_window.hover_tooltip.show()
            self.parent_window.hover_tooltip.raise_()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if hasattr(self.parent_window, "hover_tooltip") and self.parent_window.hover_tooltip:
            self.parent_window.hover_tooltip.hide()

    def handle_click(self):
        self.set_state(0 if self.state else 1)

    def mousePressEvent(self, event):
        r = self.current_row
        self.table.setCurrentCell(r, 0)
        self.table.selectRow(r)
        if event.button() == Qt.RightButton:
            self.set_state(0 if self.state == 2 else 2)
            event.accept()
            return

        super().mousePressEvent(event)

    def set_state(self, state):
        self.state = state
        self.apply_state()
        update_syllabus_completion(self.item_id, self.field, state)
        self.parent_window.update_subject_progress(self.subject)
        if state == 1:
            self.parent_window.play_interaction_sound("greencheck")
        elif state == 2:
            self.parent_window.play_interaction_sound("orangecheck")
        self.parent_window.update_row_progress(self.subject, self.current_row)

    def apply_state(self):
        if self.state == 1:
            self.asset_pixmap = self.parent_window.get_cached_icon("greencheck")
            self.setToolTip("Complete. Click to uncheck.")
        elif self.state == 2:
            self.asset_pixmap = self.parent_window.get_cached_icon("orangecheck")
            self.setToolTip("Ongoing. Right-click to uncheck.")
        else:
            self.asset_pixmap = QPixmap()
            self.setToolTip("Left-click for complete. Right-click for ongoing.")
        self.setProperty("statusState", str(self.state))
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def with_opacity(self, color, opacity):
        if color.startswith("rgba"):
            values = color[color.find("(") + 1:color.rfind(")")].split(",")
            base_alpha = int(values[3].strip())
            alpha = int(max(0.0, min(1.0, opacity)) * base_alpha)
            return f"rgba({values[0].strip()}, {values[1].strip()}, {values[2].strip()}, {alpha})"

        alpha = int(max(0.0, min(1.0, opacity)) * 255)
        if color.startswith("#") and len(color) == 7:
            red = int(color[1:3], 16)
            green = int(color[3:5], 16)
            blue = int(color[5:7], 16)
            return f"rgba({red}, {green}, {blue}, {alpha})"

        return color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        rect = QRectF(0, 0, self.width(), self.height())

        if self.state in (1, 2):
            # Soft drop shadow offset slightly down
            shadow_rect = QRectF(2, 3.5, 24, 24)
            painter.setBrush(QColor(0, 0, 0, 110))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(shadow_rect)

            # Draw beautiful Vista-style 3D glossy gel circle
            btn_rect = QRectF(2, 2, 24, 24)
            gradient = QRadialGradient(btn_rect.center(), btn_rect.width() / 2, btn_rect.center() - QPointF(btn_rect.width() / 6, btn_rect.height() / 6))
            if self.state == 1:
                gradient.setColorAt(0.0, QColor(74, 222, 128))  # Light green center
                gradient.setColorAt(0.8, QColor(22, 163, 74))   # Emerald green body
                gradient.setColorAt(1.0, QColor(20, 83, 45))    # Dark green edge shadow
            else:
                gradient.setColorAt(0.0, QColor(253, 224, 71))  # Light amber center
                gradient.setColorAt(0.8, QColor(234, 179, 8))   # Amber/yellow body
                gradient.setColorAt(1.0, QColor(133, 77, 14))   # Dark brown edge shadow

            painter.setBrush(gradient)
            # 1px dark border to justify contrast on top of translucent green progress bars
            painter.setPen(QPen(QColor(0, 0, 0, 95), 1.0))
            painter.drawEllipse(btn_rect)

            # Draw white top-crescent gloss reflection
            gloss_rect = QRectF(btn_rect.x() + btn_rect.width() * 0.1, btn_rect.y() + btn_rect.height() * 0.05, btn_rect.width() * 0.8, btn_rect.height() * 0.45)
            gloss_grad = QLinearGradient(0, gloss_rect.top(), 0, gloss_rect.bottom())
            gloss_grad.setColorAt(0.0, QColor(255, 255, 255, 170))
            gloss_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(gloss_grad)
            painter.drawEllipse(gloss_rect)

            # Draw crisp bold white vector checkmark
            pen = QPen(Qt.white, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            w, h = btn_rect.width(), btn_rect.height()
            x, y = btn_rect.x(), btn_rect.y()
            p1 = QPointF(x + w * 0.28, y + h * 0.5)
            p2 = QPointF(x + w * 0.44, y + h * 0.66)
            p3 = QPointF(x + w * 0.72, y + h * 0.34)
            painter.drawPolyline([p1, p2, p3])
        else:
            # Untoggled state: smoked glass circle
            inner_rect = rect.adjusted(2, 2, -2, -2)
            theme_name = self.parent_window.theme_name.lower()
            is_very_dark = any(name in theme_name for name in ["smoked", "carbon", "graphite", "midnight", "dark", "ink"])
            if is_very_dark:
                # Lighter contrast smoked glass for very dark background
                painter.setBrush(QColor(255, 255, 255, 25))
            else:
                # Darker contrast smoked glass for light background
                painter.setBrush(QColor(0, 0, 0, 95))
            painter.drawEllipse(inner_rect)

            # Draw faint, thin vector checkmark outline inside
            pen = QPen(QColor(255, 255, 255, 50) if is_very_dark else QColor(255, 255, 255, 80), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            w, h = inner_rect.width(), inner_rect.height()
            x, y = inner_rect.x(), inner_rect.y()
            p1 = QPointF(x + w * 0.28, y + h * 0.5)
            p2 = QPointF(x + w * 0.44, y + h * 0.66)
            p3 = QPointF(x + w * 0.72, y + h * 0.34)
            painter.drawPolyline([p1, p2, p3])


class SoundToggleButton(QPushButton):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none; padding: 0px; margin: 0px;")
        self.clicked.connect(self.toggle_sound)
        self.sound_enabled = get_setting("sound_enabled", "1") == "1"
        self.setToolTip("Mute all sounds" if self.sound_enabled else "Unmute all sounds")
        
    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        set_setting("sound_enabled", "1" if self.sound_enabled else "0")
        self.setToolTip("Mute all sounds" if self.sound_enabled else "Unmute all sounds")
        self.update()
        if hasattr(self.main_window, "sound_vol_btn") and self.main_window.sound_vol_btn:
            self.main_window.sound_vol_btn.update()
        if self.sound_enabled:
            self.main_window.play_interaction_sound("greencheck")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        rect = self.rect()
        btn_rect = QRectF(2, 2, 28, 28)
        
        # Backlight glow when sound is enabled
        if self.sound_enabled:
            backlight = QRadialGradient(
                rect.center(), 
                max(rect.width(), rect.height()) * 0.7, 
                rect.center()
            )
            backlight.setColorAt(0.0, QColor(249, 115, 22, 130))
            backlight.setColorAt(0.6, QColor(249, 115, 22, 40))
            backlight.setColorAt(1.0, QColor(249, 115, 22, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(backlight))
            painter.drawEllipse(btn_rect)
            
            painter.setBrush(QColor(15, 23, 42, 60))
            painter.drawEllipse(btn_rect)
            
            border_pen = QPen(QColor(249, 115, 22, 200), 1.5)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(btn_rect.adjusted(0.5, 0.5, -0.5, -0.5))
        else:
            # Solid translucent glass when muted
            painter.setBrush(QColor(255, 255, 255, 12))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(btn_rect)
            
            border_pen = QPen(QColor(255, 255, 255, 30), 1.0)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(btn_rect.adjusted(0.5, 0.5, -0.5, -0.5))
            
        # Top gloss
        painter.save()
        clip_path = QPainterPath()
        clip_path.addEllipse(btn_rect)
        painter.setClipPath(clip_path)
        
        gloss = QLinearGradient(0, 2, 0, 2 + rect.height() * 0.4)
        if self.sound_enabled:
            gloss.setColorAt(0.0, QColor(255, 255, 255, 60))
            gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        else:
            gloss.setColorAt(0.0, QColor(255, 255, 255, 25))
            gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gloss))
        painter.drawRect(QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.4))
        painter.restore()
        
        # Speaker icon graphics
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        speaker_path = QPainterPath()
        speaker_path.moveTo(7, 12)
        speaker_path.lineTo(11, 12)
        speaker_path.lineTo(16, 7)
        speaker_path.lineTo(16, 25)
        speaker_path.lineTo(11, 20)
        speaker_path.lineTo(7, 20)
        speaker_path.closeSubpath()
        painter.drawPath(speaker_path)
        
        if self.sound_enabled:
            painter.setPen(QPen(Qt.white, 2.0, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(QRectF(4, 9, 14, 14), -45 * 16, 90 * 16)
            painter.drawArc(QRectF(0, 5, 22, 22), -45 * 16, 90 * 16)
        else:
            painter.setPen(QPen(QColor(239, 68, 68), 2.2, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(8, 8), QPointF(24, 24))



class SoundIconWidget(QWidget):
    def __init__(self, icon_type, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.setFixedSize(20, 20)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        
        # Soft shadow
        shadow_rect = QRectF(1.5, 2.5, 17, 17)
        painter.setBrush(QColor(0, 0, 0, 90))
        painter.drawEllipse(shadow_rect)
        
        # Gel body
        btn_rect = QRectF(1.5, 1.5, 17, 17)
        gradient = QRadialGradient(btn_rect.center(), btn_rect.width() / 2, btn_rect.center() - QPointF(btn_rect.width() / 6, btn_rect.height() / 6))
        
        if self.icon_type == "greencheck":
            gradient.setColorAt(0.0, QColor(74, 222, 128))  # Light green center
            gradient.setColorAt(0.8, QColor(22, 163, 74))   # Emerald green body
            gradient.setColorAt(1.0, QColor(20, 83, 45))    # Dark green edge shadow
        elif self.icon_type == "orangecheck":
            gradient.setColorAt(0.0, QColor(253, 224, 71))  # Light amber center
            gradient.setColorAt(0.8, QColor(234, 179, 8))   # Amber/yellow body
            gradient.setColorAt(1.0, QColor(133, 77, 14))   # Dark brown edge shadow
        elif self.icon_type == "important":
            gradient.setColorAt(0.0, QColor(248, 113, 113)) # Light red center
            gradient.setColorAt(0.8, QColor(220, 38, 38))   # Red body
            gradient.setColorAt(1.0, QColor(127, 29, 29))   # Dark red edge shadow
        else: # plankton / break / tired
            gradient.setColorAt(0.0, QColor(129, 140, 248)) # Light indigo center
            gradient.setColorAt(0.8, QColor(79, 70, 229))   # Indigo body
            gradient.setColorAt(1.0, QColor(49, 46, 129))   # Dark indigo edge shadow
            
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(0, 0, 0, 80), 0.8))
        painter.drawEllipse(btn_rect)
        
        # Crescent reflection
        gloss_rect = QRectF(btn_rect.x() + btn_rect.width() * 0.1, btn_rect.y() + btn_rect.height() * 0.05, btn_rect.width() * 0.8, btn_rect.height() * 0.45)
        gloss_grad = QLinearGradient(0, gloss_rect.top(), 0, gloss_rect.bottom())
        gloss_grad.setColorAt(0.0, QColor(255, 255, 255, 150))
        gloss_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(gloss_grad)
        painter.drawEllipse(gloss_rect)
        
        # Draw symbols
        painter.setPen(QPen(Qt.white, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        w, h = btn_rect.width(), btn_rect.height()
        x, y = btn_rect.x(), btn_rect.y()
        
        if self.icon_type in ("greencheck", "orangecheck"):
            p1 = QPointF(x + w * 0.28, y + h * 0.5)
            p2 = QPointF(x + w * 0.44, y + h * 0.66)
            p3 = QPointF(x + w * 0.72, y + h * 0.34)
            painter.drawPolyline([p1, p2, p3])
        elif self.icon_type == "important":
            painter.setPen(QPen(Qt.white, 1.8, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(x + w * 0.5, y + h * 0.25), QPointF(x + w * 0.5, y + h * 0.55))
            painter.drawPoint(QPointF(x + w * 0.5, y + h * 0.75))
        else: # plankton / break / tired
            painter.setPen(QPen(Qt.white, 1.2, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(x + w * 0.2, y + h * 0.2, w * 0.6, h * 0.6))
            painter.drawLine(QPointF(x + w * 0.5, y + h * 0.5), QPointF(x + w * 0.5, y + h * 0.35))
            painter.drawLine(QPointF(x + w * 0.5, y + h * 0.5), QPointF(x + w * 0.65, y + h * 0.5))


class SoundVolumeButton(QPushButton):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none; padding: 0px; margin: 0px;")
        self.clicked.connect(self.show_volume_popup)
        self.setToolTip("Volume settings for sound effects")
        
    def show_volume_popup(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(15, 23, 42, 240);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 8px;
                padding: 8px;
            }
        """)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        sounds = [
            ("greencheck", "Green Check", "greencheck"),
            ("orangecheck", "Orange Check", "orangecheck"),
            ("important", "Important", "important_active"),
            ("plankton", "Break / Tired", "plankton_icon")
        ]

        for setting_key, label_text, icon_name in sounds:
            row = QHBoxLayout()
            row.setSpacing(8)

            # Icon
            icon_widget = SoundIconWidget(setting_key)
            
            # Label
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")
            lbl.setMinimumWidth(80)

            # Slider
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setFixedWidth(120)
            slider.setValue(int(get_setting(f"volume_{setting_key}", "90")))
            
            # Value change connects to DB, release plays audio
            slider.valueChanged.connect(
                lambda val, key=setting_key: set_setting(f"volume_{key}", str(val))
            )
            slider.sliderReleased.connect(
                lambda key=setting_key: self.main_window.play_interaction_sound(key)
            )

            row.addWidget(icon_widget)
            row.addWidget(lbl)
            row.addWidget(slider)
            layout.addLayout(row)

        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(container)
        menu.addAction(widget_action)

        menu.exec(self.mapToGlobal(QPoint(0, self.height())))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        rect = self.rect()
        btn_rect = QRectF(2, 2, 28, 28)
        
        # Glow matches the global sound_enabled state
        sound_active = getattr(self.main_window, "sound_enabled", True)
        
        if sound_active:
            backlight = QRadialGradient(
                rect.center(), 
                max(rect.width(), rect.height()) * 0.7, 
                rect.center()
            )
            backlight.setColorAt(0.0, QColor(249, 115, 22, 130))
            backlight.setColorAt(0.6, QColor(249, 115, 22, 40))
            backlight.setColorAt(1.0, QColor(249, 115, 22, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(backlight))
            painter.drawEllipse(btn_rect)
            
            painter.setBrush(QColor(15, 23, 42, 60))
            painter.drawEllipse(btn_rect)
            
            border_pen = QPen(QColor(249, 115, 22, 200), 1.5)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(btn_rect.adjusted(0.5, 0.5, -0.5, -0.5))
        else:
            # Solid translucent glass when muted
            painter.setBrush(QColor(255, 255, 255, 12))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(btn_rect)
            
            border_pen = QPen(QColor(255, 255, 255, 30), 1.0)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(btn_rect.adjusted(0.5, 0.5, -0.5, -0.5))
            
        # Top gloss
        painter.save()
        clip_path = QPainterPath()
        clip_path.addEllipse(btn_rect)
        painter.setClipPath(clip_path)
        
        gloss = QLinearGradient(0, 2, 0, 2 + rect.height() * 0.4)
        if sound_active:
            gloss.setColorAt(0.0, QColor(255, 255, 255, 60))
            gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        else:
            gloss.setColorAt(0.0, QColor(255, 255, 255, 25))
            gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gloss))
        painter.drawRect(QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.4))
        painter.restore()
        
        # Speaker icon graphics
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        speaker_path = QPainterPath()
        speaker_path.moveTo(7, 12)
        speaker_path.lineTo(11, 12)
        speaker_path.lineTo(16, 7)
        speaker_path.lineTo(16, 25)
        speaker_path.lineTo(11, 20)
        speaker_path.lineTo(7, 20)
        speaker_path.closeSubpath()
        painter.drawPath(speaker_path)
        
        painter.setPen(QPen(Qt.white, 2.0, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(QRectF(4, 9, 14, 14), -45 * 16, 90 * 16)
        painter.drawArc(QRectF(0, 5, 22, 22), -45 * 16, 90 * 16)
        painter.drawArc(QRectF(-4, 1, 30, 30), -45 * 16, 90 * 16)


class ImportantIconButton(QPushButton):
    def __init__(self, parent_window, table, row, item_id, subject, important=0):
        super().__init__()
        self.parent_window = parent_window
        self.table = table
        self.row = row
        self.item_id = item_id
        self.subject = subject
        self.important = bool(important)
        self.asset_pixmap = parent_window.get_cached_icon("important_active")
        self.inactive_pixmap = parent_window.get_cached_icon("important_inactive")
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("class", "ImportantButton")
        self.setToolTip("Mark important")
        self.setFixedSize(32, 32)
        self.setStyleSheet("background: transparent; border: none; padding: 0px; margin: 0px;")
        self.clicked.connect(self.toggle)
        self.apply_state()

    @property
    def current_row(self):
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                cell_w = self.table.cellWidget(r, c)
                if cell_w:
                    if cell_w == self or cell_w.findChild(self.__class__) == self:
                        return r
        return self.row

    def enterEvent(self, event):
        super().enterEvent(event)
        if hasattr(self.table, "on_row_hovered"):
            self.table.on_row_hovered(self.current_row)

    def mousePressEvent(self, event):
        r = self.current_row
        self.table.setCurrentCell(r, 0)
        self.table.selectRow(r)
        super().mousePressEvent(event)

    def toggle(self):
        self.important = not self.important
        self.apply_state()
        update_syllabus_item(self.item_id, important=self.important)
        self.parent_window.play_interaction_sound("important")

    def apply_state(self):
        self.setProperty("importantState", "true" if self.important else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        rect = QRectF(0, 0, self.width(), self.height())

        if self.important:
            # Soft drop shadow offset slightly down
            shadow_rect = QRectF(2, 3.5, 22, 22)
            painter.setBrush(QColor(0, 0, 0, 110))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(shadow_rect)

            # Draw beautiful Vista-style 3D glossy red/crimson circle
            btn_rect = QRectF(2, 2, 22, 22)
            gradient = QRadialGradient(btn_rect.center(), btn_rect.width() / 2, btn_rect.center() - QPointF(btn_rect.width() / 6, btn_rect.height() / 6))
            gradient.setColorAt(0.0, QColor(248, 113, 113))  # Light red center
            gradient.setColorAt(0.8, QColor(220, 38, 38))    # Crimson red body
            gradient.setColorAt(1.0, QColor(127, 29, 29))    # Dark red edge shadow

            painter.setBrush(gradient)
            # 1px dark border to justify contrast on top of translucent green progress bars
            painter.setPen(QPen(QColor(0, 0, 0, 95), 1.0))
            painter.drawEllipse(btn_rect)

            # Draw white top-crescent gloss reflection
            gloss_rect = QRectF(btn_rect.x() + btn_rect.width() * 0.1, btn_rect.y() + btn_rect.height() * 0.05, btn_rect.width() * 0.8, btn_rect.height() * 0.45)
            gloss_grad = QLinearGradient(0, gloss_rect.top(), 0, gloss_rect.bottom())
            gloss_grad.setColorAt(0.0, QColor(255, 255, 255, 170))
            gloss_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(gloss_grad)
            painter.drawEllipse(gloss_rect)

            # Draw white vector exclamation mark
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.white)
            w, h = btn_rect.width(), btn_rect.height()
            x, y = btn_rect.x(), btn_rect.y()
            
            # Exclamation bar
            bar_path = QPainterPath()
            bar_path.addRoundedRect(x + w * 0.44, y + h * 0.24, w * 0.12, h * 0.36, w * 0.05, w * 0.05)
            painter.drawPath(bar_path)
            
            # Exclamation dot
            painter.drawEllipse(QRectF(x + w * 0.44, y + h * 0.67, w * 0.12, w * 0.12))
        else:
            # Untoggled state: smoked glass circle
            inner_rect = rect.adjusted(2, 2, -2, -2)
            theme_name = self.parent_window.theme_name.lower()
            is_very_dark = any(name in theme_name for name in ["smoked", "carbon", "graphite", "midnight", "dark", "ink"])
            if is_very_dark:
                # Lighter contrast smoked glass for very dark background
                painter.setBrush(QColor(255, 255, 255, 25))
            else:
                # Darker contrast smoked glass for light background
                painter.setBrush(QColor(0, 0, 0, 95))
            painter.drawEllipse(inner_rect)

            # Draw faint, thin vector exclamation mark outline inside
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 55) if is_very_dark else QColor(255, 255, 255, 85))
            w, h = inner_rect.width(), inner_rect.height()
            x, y = inner_rect.x(), inner_rect.y()
            
            bar_path = QPainterPath()
            bar_path.addRoundedRect(x + w * 0.44, y + h * 0.24, w * 0.12, h * 0.36, w * 0.05, w * 0.05)
            painter.drawPath(bar_path)
            painter.drawEllipse(QRectF(x + w * 0.44, y + h * 0.67, w * 0.12, w * 0.12))


class TopicProgressWidget(QFrame):
    def __init__(self, parent_window, table, row, item_id, subject, topic, important, percent):
        super().__init__()
        self.parent_window = parent_window
        self.table = table
        self.row = row
        self.item_id = item_id
        self.subject = subject
        self.topic = topic
        self.percent = percent
        self.setProperty("class", "TopicTile")
        self.setMinimumHeight(38)
        self.setStyleSheet("background: transparent; border: none;")
        self.setMouseTracking(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        self.important_button = ImportantIconButton(parent_window, table, row, item_id, subject, important)
        
        self.topic_label = QLabel(topic)
        self.topic_label.setStyleSheet("background: transparent; border: none; color: white;")
        self.topic_label.setWordWrap(True)
        
        self.percent_label = QLabel(f"{percent}%")
        self.percent_label.setProperty("class", "RowPercent")
        self.percent_label.setStyleSheet("background: transparent; border: none; color: rgba(255, 255, 255, 200); font-weight: bold;")
        self.percent_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.percent_label.setMinimumWidth(42)

        layout.addWidget(self.important_button)
        layout.addWidget(self.topic_label, 1)
        layout.addWidget(self.percent_label)

    def paintEvent(self, event):
        pass

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        r = self.current_row
        self.table.setCurrentCell(r, 0)
        self.table.selectRow(r)

    @property
    def current_row(self):
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                cell_w = self.table.cellWidget(r, c)
                if cell_w:
                    if cell_w == self or cell_w.findChild(self.__class__) == self:
                        return r
        return self.row

    def enterEvent(self, event):
        super().enterEvent(event)
        if hasattr(self.table, "on_row_hovered"):
            self.table.on_row_hovered(self.current_row)

    def start_rename(self):
        self.topic_label.hide()
        self.edit = QLineEdit(self.topic_label.text())
        self.edit.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 240);
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 4px;
                color: white;
                font-weight: bold;
                padding: 0px 4px;
            }
        """)
        self.layout().insertWidget(1, self.edit, 1)
        self.edit.show()
        self.edit.setFocus()
        self.edit.selectAll()
        self.edit.editingFinished.connect(self.finish_rename)

    def finish_rename(self):
        new_text = self.edit.text().strip()
        self.edit.deleteLater()
        self.topic_label.show()
        if new_text and new_text != self.topic_label.text():
            update_syllabus_item(self.item_id, topic=new_text)
        self.parent_window.reload_subject(self.subject)


class ClickableWidget(QWidget):
    def __init__(self, click_callback, parent=None):
        super().__init__(parent)
        self.click_callback = click_callback
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_callback()
            event.accept()
        else:
            super().mousePressEvent(event)


class FlipCardWidget(QWidget):
    def __init__(self, value, label_text, parent=None):
        super().__init__(parent)
        self._value = str(value)
        self._prev_value = str(value)
        self._label_text = label_text
        self._flip_ratio = 1.0
        self.anim = QPropertyAnimation(self, b"flip_ratio")
        self.anim.setDuration(400)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        
    @Property(float)
    def flip_ratio(self):
        return self._flip_ratio
        
    @flip_ratio.setter
    def flip_ratio(self, val):
        self._flip_ratio = val
        self.update()
        
    def set_value(self, val, animate=True):
        val_str = str(val)
        if self._value != val_str:
            self._prev_value = self._value
            self._value = val_str
            if animate:
                self._flip_ratio = 0.0
                self.anim.stop()
                self.anim.setStartValue(0.0)
                self.anim.setEndValue(1.0)
                self.anim.start()
            else:
                self._flip_ratio = 1.0
                self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        rect = self.rect()
        w = rect.width()
        h = rect.height()
        
        card_h = int(h * 0.72)
        card_rect = QRect(0, 0, w, card_h)
        label_rect = QRect(0, card_h, w, h - card_h)
        
        # Draw label
        lbl_font = painter.font()
        lbl_font.setFamily("Segoe UI Variable Display" if "Segoe UI Variable" in lbl_font.family() else lbl_font.family())
        lbl_font.setPointSize(max(10, self.font().pointSize() - 2))
        painter.setFont(lbl_font)
        painter.setPen(QColor(203, 213, 225, 180))
        painter.drawText(label_rect, Qt.AlignCenter, self._label_text)

        # Draw card background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 12))
        painter.drawRoundedRect(card_rect, 8, 8)
        
        border_pen = QPen(QColor(255, 255, 255, 25), 1.0)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(card_rect.adjusted(0, 0, -1, -1), 8, 8)
        
        # Resolve the card's specific theme panel color to clear previous text
        main_win = self.window()
        tile_id = "countdown"
        parent_card = self.parent()
        if parent_card and hasattr(parent_card, "tile_id"):
            tile_id = parent_card.tile_id
            
        card_theme_name = get_setting(f"tile_theme_{tile_id}", "") if main_win else ""
        if not card_theme_name:
            card_theme_name = main_win.theme_name if (main_win and hasattr(main_win, "theme_name")) else "Midnight Teal"
            
        theme = THEMES.get(card_theme_name, THEMES["Midnight Teal"])
        ui_opacity = main_win.ui_opacity if (main_win and hasattr(main_win, "ui_opacity")) else 0.62
        panel_color_str = main_win.with_opacity(theme["panel"], ui_opacity) if (main_win and hasattr(main_win, "with_opacity")) else "rgba(15, 23, 42, 220)"
        
        if panel_color_str.startswith("rgba"):
            parts = panel_color_str[panel_color_str.find("(") + 1:panel_color_str.rfind(")")].split(",")
            panel_color = QColor(int(parts[0]), int(parts[1].strip()), int(parts[2].strip()), int(parts[3].strip()))
        elif panel_color_str.startswith("rgb"):
            parts = panel_color_str[panel_color_str.find("(") + 1:panel_color_str.rfind(")")].split(",")
            panel_color = QColor(int(parts[0]), int(parts[1].strip()), int(parts[2].strip()))
        elif panel_color_str.startswith("#"):
            panel_color = QColor(panel_color_str)
        else:
            panel_color = QColor(15, 23, 42, 220)

        num_font = painter.font()
        num_font.setBold(True)
        num_font.setPointSize(int(card_h * 0.5))
        painter.setFont(num_font)
        
        cx = w / 2
        cy = card_h / 2
        
        top_clip = QRect(0, 0, w, int(cy))
        bottom_clip = QRect(0, int(cy), w, card_h - int(cy))
        
        ratio = self._flip_ratio
        
        if ratio >= 1.0:
            painter.setPen(QColor(255, 255, 255, 240))
            painter.drawText(card_rect, Qt.AlignCenter, self._value)
        else:
            if ratio < 0.5:
                # 1. Static Top (NEW value)
                painter.save()
                painter.setClipRect(top_clip)
                painter.fillRect(top_clip, panel_color)
                painter.setPen(QColor(255, 255, 255, 240))
                painter.drawText(card_rect, Qt.AlignCenter, self._value)
                painter.restore()
                
                # 2. Static Bottom (OLD value)
                painter.save()
                painter.setClipRect(bottom_clip)
                painter.fillRect(bottom_clip, panel_color)
                painter.setPen(QColor(255, 255, 255, 240))
                painter.drawText(card_rect, Qt.AlignCenter, self._prev_value)
                painter.restore()
                
                # 3. Folding Top (OLD value, rotating down)
                painter.save()
                scale_y = 1.0 - 2.0 * ratio
                painter.translate(cx, cy)
                painter.scale(1.0, scale_y)
                painter.translate(-cx, -cy)
                painter.setClipRect(top_clip)
                painter.fillRect(top_clip, panel_color)
                painter.setPen(QColor(255, 255, 255, 240))
                painter.drawText(card_rect, Qt.AlignCenter, self._prev_value)
                painter.restore()
            else:
                # 1. Static Top (NEW value)
                painter.save()
                painter.setClipRect(top_clip)
                painter.fillRect(top_clip, panel_color)
                painter.setPen(QColor(255, 255, 255, 240))
                painter.drawText(card_rect, Qt.AlignCenter, self._value)
                painter.restore()
                
                # 2. Static Bottom (OLD value)
                painter.save()
                painter.setClipRect(bottom_clip)
                painter.fillRect(bottom_clip, panel_color)
                painter.setPen(QColor(255, 255, 255, 240))
                painter.drawText(card_rect, Qt.AlignCenter, self._prev_value)
                painter.restore()
                
                # 3. Folding Bottom (NEW value, rotating down)
                painter.save()
                scale_y = 2.0 * ratio - 1.0
                painter.translate(cx, cy)
                painter.scale(1.0, scale_y)
                painter.translate(-cx, -cy)
                painter.setClipRect(bottom_clip)
                painter.fillRect(bottom_clip, panel_color)
                painter.setPen(QColor(255, 255, 255, 240))
                painter.drawText(card_rect, Qt.AlignCenter, self._value)
                painter.restore()

        # Split line
        painter.setPen(QPen(QColor(0, 0, 0, 100), 1.0))
        painter.drawLine(0, int(cy), w, int(cy))



class ModeToggleButton(QWidget):
    modeChanged = Signal(str)

    def __init__(self, current_mode="aesthetic", parent=None):
        super().__init__(parent)
        self.mode = current_mode
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(140, 28)
        self.setMaximumSize(180, 28)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            new_mode = "lite" if self.mode == "aesthetic" else "aesthetic"
            self.set_mode(new_mode)
            event.accept()
        else:
            super().mousePressEvent(event)

    def set_mode(self, mode, animate=True):
        if self.mode != mode:
            self.mode = mode
            self.update()
            self.modeChanged.emit(self.mode)
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        
        rect = self.rect()
        
        # Glow color corresponding to the active mode (Lite = Green, Aesthetic = Halogen/Orange)
        if self.mode == "lite":
            glow_color = QColor(34, 197, 94)
            text_color = QColor(187, 247, 208)
        else:
            glow_color = QColor(249, 115, 22)
            text_color = QColor(254, 215, 170)
            
        # Backlight glow (always)
        backlight = QRadialGradient(
            rect.center(), 
            max(rect.width(), rect.height()) * 0.7, 
            rect.center()
        )
        backlight.setColorAt(0.0, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 130))
        backlight.setColorAt(0.6, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 40))
        backlight.setColorAt(1.0, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 0))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(backlight))
        painter.drawRoundedRect(rect, 7, 7)
        
        # Translucent glass panel fill
        painter.setBrush(QColor(15, 23, 42, 60))
        painter.drawRoundedRect(rect, 7, 7)
        
        # Glowing border outline
        border_pen = QPen(QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 200), 1.5)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 7, 7)
        
        # Top gloss
        painter.save()
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, 7, 7)
        painter.setClipPath(clip_path)
        
        gloss = QLinearGradient(0, 0, 0, rect.height() * 0.45)
        gloss.setColorAt(0.0, QColor(255, 255, 255, 60))
        gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gloss))
        painter.drawRect(QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.45))
        painter.restore()
        
        # Draw Mode Text
        text_font = painter.font()
        text_font.setPointSize(9)
        text_font.setBold(True)
        painter.setFont(text_font)
        painter.setPen(text_color)
        
        mode_text = "Aesthetic" if self.mode == "aesthetic" else "Lite"
        painter.drawText(rect, Qt.AlignCenter, mode_text)


class ElevatorControlButton(QPushButton):
    def __init__(self, text, btn_type, parent=None):
        super().__init__(text, parent)
        self.btn_type = btn_type
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(28)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        rect = self.rect()
        painter.setPen(Qt.NoPen)
        
        is_pressed = self.isDown()
        
        if is_pressed:
            backlight = QRadialGradient(
                rect.center(), 
                max(rect.width(), rect.height()) * 0.7, 
                rect.center()
            )
            if self.btn_type == "start":
                backlight.setColorAt(0.0, QColor(34, 197, 94, 150))
                backlight.setColorAt(0.6, QColor(34, 197, 94, 50))
                backlight.setColorAt(1.0, QColor(34, 197, 94, 0))
                painter.setBrush(QBrush(backlight))
                painter.drawRoundedRect(rect, 7, 7)
                
                painter.setBrush(QColor(15, 23, 42, 60))
                painter.drawRoundedRect(rect, 7, 7)
                
                border_pen = QPen(QColor(34, 197, 94, 220), 1.5)
                painter.setPen(border_pen)
            else:
                backlight.setColorAt(0.0, QColor(239, 68, 68, 150))
                backlight.setColorAt(0.6, QColor(239, 68, 68, 50))
                backlight.setColorAt(1.0, QColor(239, 68, 68, 0))
                painter.setBrush(QBrush(backlight))
                painter.drawRoundedRect(rect, 7, 7)
                
                painter.setBrush(QColor(15, 23, 42, 60))
                painter.drawRoundedRect(rect, 7, 7)
                
                border_pen = QPen(QColor(239, 68, 68, 220), 1.5)
                painter.setPen(border_pen)
            
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 7, 7)
        else:
            painter.setBrush(QColor(255, 255, 255, 12))
            painter.drawRoundedRect(rect, 7, 7)
            
            border_pen = QPen(QColor(255, 255, 255, 30), 1.0)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 7, 7)

        # Gloss
        gloss = QLinearGradient(0, 0, 0, rect.height() * 0.4)
        if is_pressed:
            gloss.setColorAt(0.0, QColor(255, 255, 255, 60))
            gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        else:
            gloss.setColorAt(0.0, QColor(255, 255, 255, 25))
            gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gloss))
        painter.drawRoundedRect(QRect(rect.x(), rect.y(), rect.width(), int(rect.height() * 0.4)), 7, 7)

        # Text
        text_font = painter.font()
        text_font.setBold(True)
        painter.setFont(text_font)
        
        if is_pressed:
            if self.btn_type == "start":
                painter.setPen(QColor(187, 247, 208))
            else:
                painter.setPen(QColor(254, 202, 202))
        else:
            painter.setPen(QColor(255, 255, 255, 200))
            
        painter.drawText(rect, Qt.AlignCenter, self.text())


class ElevatorButton(QPushButton):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title_text = title
        self.stats_text = ""
        self.is_active = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_active(self, active):
        if self.is_active != active:
            self.is_active = active
            self.update()

    def set_stats(self, stats):
        if self.stats_text != stats:
            self.stats_text = stats
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        rect = self.rect()
        painter.setPen(Qt.NoPen)
        
        if self.is_active:
            backlight = QRadialGradient(
                rect.center(), 
                max(rect.width(), rect.height()) * 0.7, 
                rect.center()
            )
            backlight.setColorAt(0.0, QColor(249, 115, 22, 130))
            backlight.setColorAt(0.6, QColor(249, 115, 22, 40))
            backlight.setColorAt(1.0, QColor(249, 115, 22, 0))
            painter.setBrush(QBrush(backlight))
            painter.drawRoundedRect(rect, 10, 10)
            
            painter.setBrush(QColor(15, 23, 42, 60))
            painter.drawRoundedRect(rect, 10, 10)
            
            border_pen = QPen(QColor(249, 115, 22, 200), 1.5)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)
        else:
            painter.setBrush(QColor(255, 255, 255, 12))
            painter.drawRoundedRect(rect, 10, 10)
            
            border_pen = QPen(QColor(255, 255, 255, 30), 1.0)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 10, 10)

        # Gloss
        gloss = QLinearGradient(0, 0, 0, rect.height() * 0.4)
        if self.is_active:
            gloss.setColorAt(0.0, QColor(255, 255, 255, 60))
            gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        else:
            gloss.setColorAt(0.0, QColor(255, 255, 255, 25))
            gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gloss))
        painter.drawRoundedRect(QRect(rect.x(), rect.y(), rect.width(), int(rect.height() * 0.4)), 10, 10)

        # Title
        title_font = painter.font()
        title_font.setFamily("Segoe UI Variable Display" if "Segoe UI Variable" in title_font.family() else title_font.family())
        title_font.setPointSize(14)
        title_font.setBold(True)
        painter.setFont(title_font)
        
        if self.is_active:
            painter.setPen(QColor(249, 115, 22, 100))
            painter.drawText(rect.adjusted(0, -15, 0, -15), Qt.AlignCenter, self.title_text)
            painter.setPen(QColor(255, 255, 255, 255))
        else:
            painter.setPen(QColor(255, 255, 255, 160))
            
        painter.drawText(rect.adjusted(0, -17, 0, -17), Qt.AlignCenter, self.title_text)

        # Stats
        stats_font = title_font
        stats_font.setPointSize(10)
        stats_font.setBold(False)
        painter.setFont(stats_font)
        
        if self.is_active:
            painter.setPen(QColor(255, 220, 200, 200))
        else:
            painter.setPen(QColor(255, 255, 255, 100))
            
        painter.drawText(rect.adjusted(0, 25, 0, 25), Qt.AlignCenter, self.stats_text)


class TimerArrowButton(QPushButton):
    def __init__(self, direction, parent=None):
        super().__init__(parent)
        self.direction = direction
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(40, 20)
        self.setMaximumSize(120, 25)
        self.hovered = False

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        rect = self.rect()
        w = rect.width()
        h = rect.height()
        
        if self.hovered:
            color = QColor(249, 115, 22, 220)
        else:
            color = QColor(255, 255, 255, 140)
            
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        
        path = QPainterPath()
        cx = w / 2
        cy = h / 2
        
        size_w = 16
        size_h = 10
        
        if self.direction == "up":
            path.moveTo(cx, cy - size_h / 2)
            path.lineTo(cx - size_w / 2, cy + size_h / 2)
            path.lineTo(cx + size_w / 2, cy + size_h / 2)
        else:
            path.moveTo(cx, cy + size_h / 2)
            path.lineTo(cx - size_w / 2, cy - size_h / 2)
            path.lineTo(cx + size_w / 2, cy - size_h / 2)
            
        path.closeSubpath()
        painter.drawPath(path)


class TimerLineEdit(QLineEdit):
    def __init__(self, on_change_callback, parent=None):
        super().__init__(parent)
        self.on_change_callback = on_change_callback
        self.setAlignment(Qt.AlignCenter)
        self.returnPressed.connect(self.parse_and_commit)
        
    def focusOutEvent(self, event):
        self.parse_and_commit()
        super().focusOutEvent(event)

    def parse_and_commit(self):
        text = self.text().strip()
        if not text:
            return
        
        seconds = self.parse_time_string(text)
        if seconds is not None and seconds > 0:
            self.on_change_callback(seconds)
        else:
            self.on_change_callback(-1)

    def parse_time_string(self, s):
        try:
            parts = s.split(":")
            if len(parts) == 3:
                h = int(parts[0])
                m = int(parts[1])
                sec = int(parts[2])
                return h * 3600 + m * 60 + sec
            elif len(parts) == 2:
                m = int(parts[0])
                sec = int(parts[1])
                return m * 60 + sec
            elif len(parts) == 1:
                m = int(parts[0])
                return m * 60
        except ValueError:
            pass
        return None


class AeroCard(QFrame):
    def __init__(self, main_window, tile_id):
        super().__init__(main_window.canvas)
        self.main_window = main_window
        self.tile_id = tile_id
        self.setObjectName(f"Card_{tile_id}")
        self.setProperty("class", "Card")
        self.main_window.apply_shadow(self)
        
        # Theme button overlay
        self.theme_btn = QPushButton(self)
        self.theme_btn.setFixedSize(28, 28)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 24);
                border: 1px solid rgba(255, 255, 255, 34);
                border-radius: 14px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 70);
            }
        """)
        picker_icon = QIcon(str(self.main_window.asset_path("themepicker.png")))
        if not picker_icon.isNull():
            self.theme_btn.setIcon(picker_icon)
            self.theme_btn.setIconSize(QSize(18, 18))
        else:
            self.theme_btn.setText("🎨")
        self.theme_btn.setToolTip("Choose theme per tile")
        self.theme_btn.clicked.connect(self.choose_theme)
        
        self.dragging = False
        self.resizing = False
        self.drag_start = None
        self.geom_start = None
        self.resize_dir = None
        
        self.card_theme = get_setting(f"tile_theme_{self.tile_id}", "")
        self.setMouseTracking(True)
        
        # Initialize theme picker visibility and card theme
        self.theme_btn.hide()
        self.apply_card_theme()

    def enterEvent(self, event):
        super().enterEvent(event)
        locked = get_setting("layout_locked", "1") == "1"
        if locked:
            self.theme_btn.show()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        locked = get_setting("layout_locked", "1") == "1"
        if locked:
            self.theme_btn.hide()
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.theme_btn.move(self.width() - 34, 6)

    def mousePressEvent(self, event):
        locked = get_setting("layout_locked", "1") == "1"
        if locked:
            super().mousePressEvent(event)
            return
            
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            if pos.x() >= self.width() - 16 and pos.y() >= self.height() - 16:
                self.resizing = True
                self.resize_dir = "br"
                self.setCursor(Qt.SizeFDiagCursor)
            elif pos.x() >= self.width() - 12:
                self.resizing = True
                self.resize_dir = "r"
                self.setCursor(Qt.SizeHorCursor)
            elif pos.y() >= self.height() - 12:
                self.resizing = True
                self.resize_dir = "b"
                self.setCursor(Qt.SizeVerCursor)
            else:
                self.dragging = True
                self.setCursor(Qt.ClosedHandCursor)

            self.drag_start = event.globalPosition().toPoint()
            self.geom_start = self.geometry()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        locked = get_setting("layout_locked", "1") == "1"
        if locked:
            self.setCursor(Qt.ArrowCursor)
            super().mouseMoveEvent(event)
            return
            
        pos = event.position().toPoint()
        if not self.dragging and not self.resizing:
            if pos.x() >= self.width() - 16 and pos.y() >= self.height() - 16:
                self.setCursor(Qt.SizeFDiagCursor)
            elif pos.x() >= self.width() - 12:
                self.setCursor(Qt.SizeHorCursor)
            elif pos.y() >= self.height() - 12:
                self.setCursor(Qt.SizeVerCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            super().mouseMoveEvent(event)
            return

        delta = event.globalPosition().toPoint() - self.drag_start
        geom = self.geom_start

        if self.dragging:
            new_x = max(0, geom.x() + delta.x())
            new_y = max(0, geom.y() + delta.y())
            self.move(new_x, new_y)
            self.main_window.resize_canvas_to_fit()
        elif self.resizing:
            w = geom.width()
            h = geom.height()
            if self.resize_dir in ("r", "br"):
                w = max(150, geom.width() + delta.x())
            if self.resize_dir in ("b", "br"):
                h = max(80, geom.height() + delta.y())
            self.resize(w, h)
            self.main_window.resize_canvas_to_fit()

        event.accept()

    def mouseReleaseEvent(self, event):
        if self.dragging or self.resizing:
            self.dragging = False
            self.resizing = False
            self.setCursor(Qt.ArrowCursor)
            self.save_geometry()
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def save_geometry(self):
        geom = self.geometry()
        geom_str = f"{geom.x()},{geom.y()},{geom.width()},{geom.height()}"
        set_setting(f"tile_geom_{self.tile_id}", geom_str)
        if hasattr(self.main_window, "update_preset_1_auto_save"):
            self.main_window.update_preset_1_auto_save()
        
    def restore_geometry(self, default_x, default_y, default_w, default_h):
        geom_str = get_setting(f"tile_geom_{self.tile_id}", "")
        if geom_str:
            try:
                parts = [int(p) for p in geom_str.split(",")]
                if len(parts) == 4:
                    self.setGeometry(parts[0], parts[1], parts[2], parts[3])
                    return
            except Exception:
                pass
        self.setGeometry(default_x, default_y, default_w, default_h)
        
    def choose_theme(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(15, 23, 42, 230);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                color: #e5e7eb;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 30);
                border-radius: 4px;
            }
        """)
        action_univ = menu.addAction("Use Universal Theme")
        menu.addSeparator()
        
        for t_name in THEMES.keys():
            menu.addAction(t_name)
            
        menu.addSeparator()
        action_font_up = menu.addAction("A+ (Increase Font Size)")
        action_font_down = menu.addAction("A- (Decrease Font Size)")
        action_font_reset = menu.addAction("Reset Font Size")
            
        action = menu.exec(self.theme_btn.mapToGlobal(QPoint(0, self.theme_btn.height())))
        if action:
            if action == action_font_up:
                current_offset = int(get_setting(f"tile_font_size_{self.tile_id}", "0"))
                set_setting(f"tile_font_size_{self.tile_id}", str(min(10, current_offset + 1)))
                self.apply_card_theme()
            elif action == action_font_down:
                current_offset = int(get_setting(f"tile_font_size_{self.tile_id}", "0"))
                set_setting(f"tile_font_size_{self.tile_id}", str(max(-5, current_offset - 1)))
                self.apply_card_theme()
            elif action == action_font_reset:
                set_setting(f"tile_font_size_{self.tile_id}", "0")
                self.apply_card_theme()
            elif action == action_univ:
                self.card_theme = ""
                set_setting(f"tile_theme_{self.tile_id}", self.card_theme)
                self.apply_card_theme()
                self.main_window.update_overall_progress()
            else:
                self.card_theme = action.text()
                set_setting(f"tile_theme_{self.tile_id}", self.card_theme)
                self.apply_card_theme()
                self.main_window.update_overall_progress()
                
            if hasattr(self.main_window, "update_preset_1_auto_save"):
                self.main_window.update_preset_1_auto_save()
            
    def apply_card_theme(self):
        theme_name = self.card_theme if self.card_theme else self.main_window.theme_name
        theme = THEMES.get(theme_name, THEMES["Burgundy"])
        
        panel = self.main_window.with_opacity(theme["panel"], self.main_window.ui_opacity)
        field = self.main_window.with_opacity(theme["field"], max(0.18, self.main_window.ui_opacity - 0.12))
        tile_hover = f"rgba(255, 255, 255, {int(54 * self.main_window.ui_opacity)})"
        edge = f"rgba(255, 255, 255, {int(48 * self.main_window.ui_opacity)})"
        
        font_size_offset = int(get_setting(f"tile_font_size_{self.tile_id}", "0"))
        card_font_size = self.main_window.app_font_size + font_size_offset
        
        
        self.setStyleSheet(f"""
            QFrame#Card_{self.tile_id} {{
                background-color: {panel};
                border: 1px solid {edge};
                border-radius: 10px;
            }}
            QFrame#Card_{self.tile_id} QWidget {{
                font-family: "{self.main_window.app_font_family}", Segoe UI Variable, Segoe UI;
                font-size: {card_font_size}px;
            }}
            QFrame#Card_{self.tile_id} QPushButton {{
                background-color: {self.main_window.with_opacity(theme["button"], self.main_window.ui_opacity)};
                border: 1px solid {edge};
                border-radius: 4px;
                color: white;
                font-weight: bold;
                padding: 4px 10px;
            }}
            QFrame#Card_{self.tile_id} QPushButton:hover {{
                background-color: {self.main_window.with_opacity(theme["button"], min(0.9, self.main_window.ui_opacity + 0.15))};
            }}
            QFrame#Card_{self.tile_id} QPushButton[class="HoverActionButton"] {{
                background-color: transparent;
                border: none;
                padding: 2px;
            }}
            QFrame#Card_{self.tile_id} QPushButton[class="HoverActionButton"]:hover {{
                background-color: rgba(255, 255, 255, 55);
            }}
            QFrame#Card_{self.tile_id} QLineEdit, 
            QFrame#Card_{self.tile_id} QPlainTextEdit, 
            QFrame#Card_{self.tile_id} QListWidget, 
            QFrame#Card_{self.tile_id} QComboBox, 
            QFrame#Card_{self.tile_id} QSpinBox, 
            QFrame#Card_{self.tile_id} QTableWidget {{
                background-color: {field};
                alternate-background-color: rgba(255, 255, 255, {int(18 * self.main_window.ui_opacity)});
                color: #e5e7eb;
                font-size: {card_font_size}px;
            }}
            QFrame#Card_{self.tile_id} QHeaderView::section {{
                background-color: transparent;
                color: white;
                font-size: {card_font_size}px;
                border: none;
            }}
            QFrame#Card_{self.tile_id} QLabel {{
                color: #e5e7eb;
                background-color: transparent;
                font-size: {card_font_size}px;
            }}
            QFrame#Card_{self.tile_id} QLabel[class="CardTitle"] {{
                color: #ffffff;
                font-size: {card_font_size + 1}px;
            }}
            QFrame#Card_{self.tile_id} QLabel[class="TimerText"] {{
                color: #ffffff;
                font-size: {card_font_size + 22}px;
            }}
            QFrame#Card_{self.tile_id} QLabel[class="CountNumber"] {{
                color: #ffffff;
                font-size: {card_font_size + 20}px;
            }}
            QFrame#Card_{self.tile_id} QLabel[class="CountLabel"] {{
                font-size: {max(9, card_font_size - 3)}px;
            }}
            QFrame#Card_{self.tile_id} QLabel#Quote {{
                color: #f8fafc;
                font-size: {card_font_size + 1}px;
            }}
            QFrame#Card_{self.tile_id} QTabWidget::tab-bar {{
                left: 0px;
            }}
            QFrame#Card_{self.tile_id} QTabWidget::pane {{
                border: 1px solid {edge};
                background-color: {panel};
                border-radius: 8px;
                border-top-left-radius: 0px;
                margin-top: -1px;
            }}
            QFrame#Card_{self.tile_id} QTabBar::tab {{
                background-color: rgba(255, 255, 255, {int(20 * self.main_window.ui_opacity)});
                color: #e5e7eb;
                padding: {max(8, card_font_size - 4)}px 18px;
                border: 1px solid {edge};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: -4px;
            }}
            QFrame#Card_{self.tile_id} QTabBar::tab:first {{
                margin-left: 0px;
            }}
            QFrame#Card_{self.tile_id} QTabBar::tab:selected {{
                background-color: {panel};
                color: #ffffff;
                border: 1px solid {edge};
                border-bottom: 1px solid {panel};
                margin-bottom: -1px;
                margin-right: -4px;
            }}
            QFrame#Card_{self.tile_id} QScrollBar:vertical {{
                border: none;
                background: rgba(0, 0, 0, 40);
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }}
            QFrame#Card_{self.tile_id} QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 70), stop:1 rgba(255, 255, 255, 30));
                min-height: 25px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 40);
            }}
            QFrame#Card_{self.tile_id} QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(140, 200, 150, 180), stop:1 rgba(90, 160, 110, 130));
                border: 1px solid rgba(255, 255, 255, 80);
            }}
            QFrame#Card_{self.tile_id} QScrollBar::add-line:vertical,
            QFrame#Card_{self.tile_id} QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QFrame#Card_{self.tile_id} QScrollBar::add-page:vertical,
            QFrame#Card_{self.tile_id} QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QFrame#Card_{self.tile_id} QScrollBar:horizontal {{
                border: none;
                background: rgba(0, 0, 0, 40);
                height: 12px;
                margin: 0px;
                border-radius: 6px;
            }}
            QFrame#Card_{self.tile_id} QScrollBar::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 70), stop:1 rgba(255, 255, 255, 30));
                min-width: 25px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 40);
            }}
            QFrame#Card_{self.tile_id} QScrollBar::handle:horizontal:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(140, 200, 150, 180), stop:1 rgba(90, 160, 110, 130));
                border: 1px solid rgba(255, 255, 255, 80);
            }}
            QFrame#Card_{self.tile_id} QScrollBar::add-line:horizontal,
            QFrame#Card_{self.tile_id} QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QFrame#Card_{self.tile_id} QScrollBar::add-page:horizontal,
            QFrame#Card_{self.tile_id} QScrollBar::sub-page:horizontal {{
                background: none;
            }}
            QFrame#Card_{self.tile_id} QCheckBox {{
                background: transparent;
                spacing: 4px;
            }}
            QFrame#Card_{self.tile_id} QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255, 255, 255, 40);
                border-radius: 10px;
                background-color: rgba(0, 0, 0, 80);
            }}
            QFrame#Card_{self.tile_id} QCheckBox::indicator:checked {{
                background-color: #22c55e;
                border: 2px solid #22c55e;
                border-radius: 10px;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjIwIDYgOSAxNyA0IDEyIi8+PC9zdmc+);
            }}
        """)


class HoverRowTrackerWidget(QWidget):
    def __init__(self, table, row):
        super().__init__()
        self.table = table
        self.row = row
        self.setMouseTracking(True)
        self.setStyleSheet("background: transparent;")
        
    @property
    def current_row(self):
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                cell_w = self.table.cellWidget(r, c)
                if cell_w:
                    if cell_w == self or cell_w.findChild(self.__class__) == self:
                        return r
        return self.row

    def enterEvent(self, event):
        super().enterEvent(event)
        if hasattr(self.table, "on_row_hovered"):
            self.table.on_row_hovered(self.current_row)


class CircleHoverButton(QPushButton):
    def __init__(self, button_type, callback, parent=None):
        super().__init__(parent)
        self.button_type = button_type
        self.callback = callback
        self.clicked.connect(lambda checked=False: self.callback())
        self.setFixedSize(26, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none; padding: 0px; margin: 0px;")
        if button_type == "rename":
            self.setToolTip("Rename item")
        else:
            self.setToolTip("Delete item")

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()
        if self.parent() and hasattr(self.parent(), "table") and hasattr(self.parent(), "row"):
            table = self.parent().table
            row = self.parent().row
            if hasattr(table, "on_row_hovered"):
                table.on_row_hovered(row)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        
        rect = QRectF(0, 0, self.width(), self.height())
        
        # Soft drop shadow
        shadow_rect = QRectF(2, 3.5, 22, 22)
        painter.setBrush(QColor(0, 0, 0, 110))
        painter.drawEllipse(shadow_rect)
        
        # Glossy circle background
        btn_rect = QRectF(2, 2, 22, 22)
        gradient = QRadialGradient(btn_rect.center(), btn_rect.width() / 2, btn_rect.center() - QPointF(btn_rect.width() / 6, btn_rect.height() / 6))
        is_hovered = self.underMouse()
        if self.button_type == "rename":
            if is_hovered:
                gradient.setColorAt(0.0, QColor(191, 219, 254))  # Brighter blue center
                gradient.setColorAt(0.8, QColor(96, 165, 250))   # Brighter blue body
                gradient.setColorAt(1.0, QColor(37, 99, 235))    # Royal blue edge
            else:
                gradient.setColorAt(0.0, QColor(96, 165, 250))  # Light blue center
                gradient.setColorAt(0.8, QColor(37, 99, 235))   # Royal blue body
                gradient.setColorAt(1.0, QColor(30, 58, 138))   # Dark blue edge shadow
        else:
            if is_hovered:
                gradient.setColorAt(0.0, QColor(254, 202, 202)) # Brighter red center
                gradient.setColorAt(0.8, QColor(248, 113, 113)) # Brighter red body
                gradient.setColorAt(1.0, QColor(220, 38, 38))   # Crimson red edge
            else:
                gradient.setColorAt(0.0, QColor(248, 113, 113)) # Light red center
                gradient.setColorAt(0.8, QColor(220, 38, 38))   # Crimson red body
                gradient.setColorAt(1.0, QColor(127, 29, 29))   # Dark red edge shadow
            
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(0, 0, 0, 95), 1.0))
        painter.drawEllipse(btn_rect)
        
        # Gloss crescent reflection
        gloss_rect = QRectF(btn_rect.x() + btn_rect.width() * 0.1, btn_rect.y() + btn_rect.height() * 0.05, btn_rect.width() * 0.8, btn_rect.height() * 0.45)
        gloss_grad = QLinearGradient(0, gloss_rect.top(), 0, gloss_rect.bottom())
        gloss_grad.setColorAt(0.0, QColor(255, 255, 255, 170))
        gloss_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(gloss_grad)
        painter.drawEllipse(gloss_rect)
        
        # Draw white vector icon inside
        w, h = btn_rect.width(), btn_rect.height()
        x, y = btn_rect.x(), btn_rect.y()
        
        if self.button_type == "delete":
            painter.setPen(QPen(Qt.white, 1.8, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            # Lid
            painter.drawLine(QPointF(x + w*0.26, y + h*0.32), QPointF(x + w*0.74, y + h*0.32))
            painter.drawPolyline([
                QPointF(x + w*0.42, y + h*0.32),
                QPointF(x + w*0.42, y + h*0.22),
                QPointF(x + w*0.58, y + h*0.22),
                QPointF(x + w*0.58, y + h*0.32)
            ])
            # Can body
            painter.drawPolyline([
                QPointF(x + w*0.32, y + h*0.38),
                QPointF(x + w*0.36, y + h*0.78),
                QPointF(x + w*0.64, y + h*0.78),
                QPointF(x + w*0.68, y + h*0.38)
            ])
            # Inner stripes
            painter.drawLine(QPointF(x + w*0.44, y + h*0.44), QPointF(x + w*0.46, y + h*0.72))
            painter.drawLine(QPointF(x + w*0.56, y + h*0.44), QPointF(x + w*0.54, y + h*0.72))
        else:
            # Rename icon (diagonal pen)
            painter.setPen(QPen(Qt.white, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            # Pen shaft lines
            painter.drawLine(QPointF(x + w*0.32, y + h*0.68), QPointF(x + w*0.64, y + h*0.36))
            painter.drawLine(QPointF(x + w*0.38, y + h*0.74), QPointF(x + w*0.70, y + h*0.42))
            # Top eraser line
            painter.drawLine(QPointF(x + w*0.64, y + h*0.36), QPointF(x + w*0.70, y + h*0.42))
            # Pen tip (draw a solid white triangle)
            path = QPainterPath()
            path.moveTo(x + w*0.32, y + h*0.68)
            path.lineTo(x + w*0.24, y + h*0.76)
            path.lineTo(x + w*0.38, y + h*0.74)
            path.closeSubpath()
            painter.setBrush(Qt.white)
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)


class HoverActionsWidget(QWidget):
    def __init__(self, parent_window, table, row, item_id, subject, topic):
        super().__init__()
        self.parent_window = parent_window
        self.table = table
        self.row = row
        self.setMouseTracking(True)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)
        
        self.rename_btn = CircleHoverButton("rename", lambda: parent_window.edit_topic_inline_from_hover(item_id, subject), self)
        self.delete_btn = CircleHoverButton("delete", lambda: parent_window.remove_syllabus_item(item_id, subject), self)
        
        layout.addWidget(self.rename_btn)
        layout.addWidget(self.delete_btn)
        
        self.rename_btn.hide()
        self.delete_btn.hide()
        
    def show_actions(self, show=True):
        self.rename_btn.setVisible(show)
        self.delete_btn.setVisible(show)

    @property
    def current_row(self):
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                cell_w = self.table.cellWidget(r, c)
                if cell_w:
                    if cell_w == self or cell_w.findChild(self.__class__) == self:
                        return r
        return self.row

    def enterEvent(self, event):
        super().enterEvent(event)
        if hasattr(self.table, "on_row_hovered"):
            self.table.on_row_hovered(self.current_row)


class RowProgressDelegate(QStyledItemDelegate):
    def __init__(self, table):
        super().__init__(table)
        self.table = table

    def paint(self, painter, option, index):
        row = index.row()
        
        categories = get_categories(include_hidden=False)
        active_cols = [i for i, cat in enumerate(categories, 1) if cat[1] == 1]
        
        # Read the completion percentage directly from the stored item in Column 0
        id_item = self.table.item(row, 0)
        percent = 0
        if id_item:
            val = id_item.data(Qt.UserRole + 1)
            if val is not None:
                percent = val

        y = option.rect.y()
        h = option.rect.height()
        
        row_left = self.table.columnViewportPosition(0)
        
        # The progress bar background covers the entire row viewport width
        row_width = self.table.viewport().width() - row_left
        
        row_rect = QRectF(row_left, y, row_width, h)
        row_rect = row_rect.adjusted(2, 2, -2, -2)

        painter.save()
        painter.setClipRect(option.rect)
        painter.setRenderHint(QPainter.Antialiasing, True)

        row_path = QPainterPath()
        row_path.addRoundedRect(row_rect, 9, 9)

        # Force aesthetic / elevator button look in both Lite and Aesthetic modes
        is_aesthetic = True


        if is_aesthetic:
            painter.setBrush(QColor(255, 255, 255, 12))
            painter.setPen(QPen(QColor(255, 255, 255, 25), 1.0))
            painter.drawPath(row_path)
            
            gloss_unfilled = QLinearGradient(0, row_rect.top(), 0, row_rect.top() + row_rect.height() * 0.45)
            gloss_unfilled.setColorAt(0.0, QColor(255, 255, 255, 20))
            gloss_unfilled.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gloss_unfilled))
            painter.drawRoundedRect(QRectF(row_rect.x(), row_rect.y(), row_rect.width(), row_rect.height() * 0.45), 9, 9)
        else:
            is_odd = row % 2 == 1
            bg_color = QColor(255, 255, 255, 18) if is_odd else QColor(255, 255, 255, 8)
            painter.setPen(QPen(QColor(255, 255, 255, 22), 1.0))
            painter.setBrush(bg_color)
            painter.drawPath(row_path)

        if percent > 0:
            progress_ratio = min(1.0, max(0.0, percent / 100.0))
            fill_width = progress_ratio * row_rect.width()
            
            if fill_width > 0:
                fill_rect = QRectF(row_rect.x(), row_rect.y(), fill_width, row_rect.height())
                fill_path = QPainterPath()
                fill_path.addRoundedRect(fill_rect, 9, 9)
                
                painter.save()
                painter.setClipPath(fill_path)
                painter.setClipRect(option.rect, Qt.IntersectClip)
                
                if is_aesthetic:
                    if percent < 30:
                        r, g, b = 239, 68, 68
                    elif percent <= 70:
                        r, g, b = 249, 115, 22
                    else:
                        r, g, b = 34, 197, 94

                    glow = QRadialGradient(
                        fill_rect.center(), 
                        max(fill_rect.width(), fill_rect.height()) * 0.7, 
                        fill_rect.center()
                    )
                    glow.setColorAt(0.0, QColor(r, g, b, 180))
                    glow.setColorAt(0.5, QColor(r, g, b, 85))
                    glow.setColorAt(1.0, QColor(r, g, b, 0))
                    painter.setBrush(QBrush(glow))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(fill_rect)
                    
                    painter.setBrush(QColor(15, 23, 42, 60))
                    painter.drawRect(fill_rect)
                    
                    gloss = QLinearGradient(0, fill_rect.top(), 0, fill_rect.top() + fill_rect.height() * 0.45)
                    gloss.setColorAt(0.0, QColor(255, 255, 255, 60))
                    gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
                    painter.setBrush(QBrush(gloss))
                    painter.drawRect(fill_rect)
                    
                    border_pen = QPen(QColor(r, g, b, 230), 1.5)
                    painter.setPen(border_pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawPath(fill_path)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 75), 1.0))
                    painter.drawLine(QPointF(fill_rect.x() + 8, fill_rect.y() + 1.0), QPointF(fill_rect.right() - 8, fill_rect.y() + 1.0))
                else:
                    gradient = QLinearGradient(0, row_rect.top(), 0, row_rect.bottom())
                    gradient.setColorAt(0.0, QColor(160, 210, 170, 45))
                    gradient.setColorAt(0.48, QColor(110, 180, 130, 38))
                    gradient.setColorAt(0.49, QColor(80, 150, 105, 49))
                    gradient.setColorAt(0.85, QColor(60, 125, 85, 42))
                    gradient.setColorAt(1.0, QColor(40, 90, 60, 35))
                    
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(gradient)
                    painter.drawRect(fill_rect)
                    
                    inner_border_pen = QPen(QColor(110, 170, 120, 35), 1.0)
                    painter.setPen(inner_border_pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawPath(fill_path)
                    
                    highlight_rect = QRectF(fill_rect.x(), fill_rect.y() + 1.0, fill_width, fill_rect.height() * 0.45)
                    highlight_grad = QLinearGradient(0, highlight_rect.top(), 0, highlight_rect.bottom())
                    highlight_grad.setColorAt(0.0, QColor(255, 255, 255, 60))
                    highlight_grad.setColorAt(1.0, QColor(255, 255, 255, 10))
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(highlight_grad)
                    painter.drawRoundedRect(highlight_rect, 9, 9)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 75), 1.0))
                    painter.drawLine(QPointF(fill_rect.x() + 8, fill_rect.y() + 1.0), QPointF(fill_rect.right() - 8, fill_rect.y() + 1.0))
                    
                    end_x = fill_rect.right()
                    pen = QPen(QColor(255, 255, 255, 100), 1.5)
                    painter.setPen(pen)
                    painter.drawLine(int(end_x - 1), int(fill_rect.top() + 4), int(end_x - 1), int(fill_rect.bottom() - 4))
                
                painter.restore()

        painter.restore()

        super().paint(painter, option, index)


class ChecklistHeaderView(QHeaderView):
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setMouseTracking(True)
        self.hovered_index = -1
        self.setFixedHeight(54)

    def sizeHint(self):
        sz = super().sizeHint()
        return QSize(sz.width(), 54)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        pos = event.position().toPoint()
        idx = self.logicalIndexAt(pos)
        if idx != self.hovered_index:
            self.hovered_index = idx
            self.viewport().update()
            
        # Tooltip display
        main_win = None
        if hasattr(self.parent(), "_main_window"):
            main_win = self.parent()._main_window
            
        if main_win and hasattr(main_win, "hover_tooltip") and main_win.hover_tooltip:
            categories = get_categories(include_hidden=False)
            if 1 <= idx <= len(categories):
                cat_name = categories[idx - 1][0]
                main_win.hover_tooltip.setText(cat_name)
                main_win.hover_tooltip.adjustSize()
                
                sect_pos = self.mapTo(main_win, QPoint(self.sectionPosition(idx), 0))
                sect_width = self.sectionSize(idx)
                center_x = sect_pos.x() + sect_width / 2
                
                tooltip_w = main_win.hover_tooltip.width()
                tooltip_h = main_win.hover_tooltip.height()
                target_x = center_x - tooltip_w / 2
                target_y = sect_pos.y() - tooltip_h - 6
                
                main_win.hover_tooltip.move(int(target_x), int(target_y))
                main_win.hover_tooltip.show()
                main_win.hover_tooltip.raise_()
            else:
                main_win.hover_tooltip.hide()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.hovered_index = -1
        self.viewport().update()
        
        main_win = None
        if hasattr(self.parent(), "_main_window"):
            main_win = self.parent()._main_window
        if main_win and hasattr(main_win, "hover_tooltip") and main_win.hover_tooltip:
            main_win.hover_tooltip.hide()

    def paintSection(self, painter, rect, logicalIndex):
        from PySide6.QtGui import QFont, QPainterPath
        categories = get_categories(include_hidden=False)
        
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        is_hovered = (self.hovered_index == logicalIndex)
        
        # Only draw background box for column 0 (topic column)
        if logicalIndex == 0:
            # Draw topic text
            painter.setPen(QColor(255, 255, 255, 220) if is_hovered else QColor(255, 255, 255, 160))
            font = QFont("Segoe UI", 10, QFont.Bold)
            painter.setFont(font)
            text_rect = QRectF(rect.left() + 12, rect.top(), rect.width() - 24, rect.height())
            metrics = painter.fontMetrics()
            elided_text = metrics.elidedText("Module / Chapter / Topic", Qt.ElideRight, int(text_rect.width()))
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, elided_text)
            
        painter.restore()
        
        # Draw category flat icon if it's a category column
        if 1 <= logicalIndex <= len(categories):
            cat_name = categories[logicalIndex - 1][0]
            cat_name_lower = cat_name.lower()
            cx = rect.left() + rect.width() / 2
            cy = rect.top() + rect.height() / 2
            
            color = QColor(51, 65, 85) # Slate 700 for a mature, flat look
            hover_color = QColor(71, 85, 105) # Slate 600 for hover
            
            fill_color = hover_color if is_hovered else color

            if "theory" in cat_name_lower:
                self.draw_flat_circle(painter, cx, cy, fill_color, "theory")
            elif "pyq" in cat_name_lower:
                self.draw_flat_circle(painter, cx, cy, fill_color, "pyq")
            elif "special" in cat_name_lower or "problem" in cat_name_lower or "bulb" in cat_name_lower or "imp" in cat_name_lower:
                self.draw_flat_circle(painter, cx, cy, fill_color, "special")
            elif "rev" in cat_name_lower or "refresh" in cat_name_lower or "repeat" in cat_name_lower:
                self.draw_flat_circle(painter, cx, cy, fill_color, "revision")
            else:
                self.draw_flat_circle(painter, cx, cy, fill_color, "custom", cat_name)

    def draw_flat_circle(self, painter, cx, cy, fill_color, symbol_type, custom_char=None):
        from PySide6.QtGui import QFont, QPainterPath
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        r = 22.0
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)

        painter.setPen(Qt.NoPen)
        painter.setBrush(fill_color)
        painter.drawEllipse(rect)

        painter.restore()
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setPen(QPen(Qt.white, 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)

        if symbol_type == "theory":
            path = QPainterPath()
            path.moveTo(cx - 8, cy - 10)
            path.lineTo(cx + 2, cy - 10)
            path.lineTo(cx + 8, cy - 4)
            path.lineTo(cx + 8, cy + 10)
            path.lineTo(cx - 8, cy + 10)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(QPointF(cx - 4, cy - 2), QPointF(cx + 4, cy - 2))
            painter.drawLine(QPointF(cx - 4, cy + 4), QPointF(cx + 4, cy + 4))
        elif symbol_type == "pyq":
            font = QFont("Segoe UI", 16, QFont.Bold)
            painter.setFont(font)
            painter.setPen(Qt.white)
            painter.drawText(QRectF(cx - r, cy - r, r * 2, r * 2), Qt.AlignCenter, "?")
        elif symbol_type == "special":
            path = QPainterPath()
            path.moveTo(cx, cy - 10)
            path.lineTo(cx + 4, cy - 2)
            path.lineTo(cx + 12, cy - 2)
            path.lineTo(cx + 6, cy + 4)
            path.lineTo(cx + 8, cy + 12)
            path.lineTo(cx, cy + 8)
            path.lineTo(cx - 8, cy + 12)
            path.lineTo(cx - 6, cy + 4)
            path.lineTo(cx - 12, cy - 2)
            path.lineTo(cx - 4, cy - 2)
            path.closeSubpath()
            painter.setBrush(Qt.white)
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)
        elif symbol_type == "revision":
            path = QPainterPath()
            painter.drawArc(QRectF(cx - 9.0, cy - 9.0, 18, 18), 45 * 16, 270 * 16)
            arrow = QPainterPath()
            arrow.moveTo(cx + 9, cy - 6)
            arrow.lineTo(cx + 13, cy - 2)
            arrow.lineTo(cx + 5, cy - 2)
            arrow.closeSubpath()
            painter.setBrush(Qt.white)
            painter.setPen(Qt.NoPen)
            painter.drawPath(arrow)
        else:
            font = QFont("Segoe UI", 14, QFont.Bold)
            painter.setFont(font)
            painter.setPen(Qt.white)
            char_str = custom_char[0].upper() if custom_char else "X"
            painter.drawText(QRectF(cx - r, cy - r, r * 2, r * 2), Qt.AlignCenter, char_str)

        painter.restore()


class DragDropTableWidget(QTableWidget):
    """QTableWidget subclass that supports internal drag-and-drop row reordering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().setSectionsMovable(True)
        self.verticalHeader().setDragEnabled(True)
        self.verticalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        self._main_window = None
        self._subject = None
        self._drag_enabled = False
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.cellEntered.connect(lambda row, col: self.on_row_hovered(row))

    def configure(self, main_window, subject):
        self._main_window = main_window
        self._subject = subject
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

    def on_row_hovered(self, row):
        for r in range(self.rowCount()):
            widget = self.cellWidget(r, self.columnCount() - 1)
            if isinstance(widget, HoverActionsWidget):
                widget.show_actions(r == row)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        for r in range(self.rowCount()):
            widget = self.cellWidget(r, self.columnCount() - 1)
            if isinstance(widget, HoverActionsWidget):
                widget.show_actions(False)

    def set_drag_enabled(self, enabled):
        self._drag_enabled = enabled
        self.setDragEnabled(enabled)
        self.setAcceptDrops(enabled)
        self.verticalHeader().setVisible(enabled)
        if enabled:
            self.setDragDropMode(QAbstractItemView.InternalMove)
            self.verticalHeader().setDragEnabled(True)
            self.verticalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        else:
            self.setDragDropMode(QAbstractItemView.NoDragDrop)
            self.verticalHeader().setDragEnabled(False)

    def dropEvent(self, event):
        if not (self._main_window and self._subject):
            event.ignore()
            return
            
        source_row = self.currentRow()
        if source_row < 0:
            event.ignore()
            return
            
        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        target_row = self.rowAt(pos.y())
        
        if target_row == -1:
            target_row = self.rowCount() - 1
            
        if target_row == source_row:
            event.ignore()
            return
            
        item_ids = []
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item:
                iid = item.data(Qt.UserRole)
                if iid is not None:
                    item_ids.append(iid)
                    
        if not item_ids or source_row >= len(item_ids) or target_row >= len(item_ids):
            event.ignore()
            return
            
        moved_id = item_ids.pop(source_row)
        item_ids.insert(target_row, moved_id)
        
        reorder_syllabus_items(item_ids)
        self._main_window.reload_subject(self._subject)
        event.accept()


class WallpaperPickerDialog(QDialog):
    """Dialog that shows thumbnail previews of static and motion wallpapers in tabs."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("Choose Wallpaper")
        self.resize(760, 560)
        self.original_wallpaper = main_window.wallpaper_path
        self.selected_path = main_window.wallpaper_path
        if parent:
            self.setStyleSheet(parent.styleSheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Wallpaper Gallery")
        title.setProperty("class", "CardTitle")
        layout.addWidget(title)

        # Tab Widget setup
        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet("""
            QTabWidget::panel {
                border: 1px solid rgba(255, 255, 255, 20);
                background-color: rgba(15, 23, 42, 120);
                border-radius: 8px;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 14);
                border: 1px solid rgba(255, 255, 255, 20);
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                color: #d1d5db;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: rgba(255, 255, 255, 34);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 40);
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background: rgba(255, 255, 255, 24);
            }
        """)
        layout.addWidget(self.tabs, 1)

        # Tab 1: Static Wallpapers
        static_tab = QWidget()
        static_layout = QVBoxLayout(static_tab)
        static_layout.setContentsMargins(8, 8, 8, 8)

        static_scroll = QScrollArea()
        static_scroll.setWidgetResizable(True)
        static_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        static_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        static_grid_widget = QWidget()
        static_grid_layout = QVBoxLayout(static_grid_widget)
        static_grid_layout.setContentsMargins(0, 0, 0, 0)
        static_grid_layout.setSpacing(10)

        wallpaper_dir = main_window.asset_path("wallpapers")
        static_thumbs = []
        if wallpaper_dir and Path(wallpaper_dir).is_dir():
            for f in sorted(Path(wallpaper_dir).iterdir()):
                if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp"):
                    static_thumbs.append(f)

        cols = 4
        row_layout = None
        for idx, thumb_path in enumerate(static_thumbs):
            if idx % cols == 0:
                row_layout = QHBoxLayout()
                row_layout.setSpacing(10)
                static_grid_layout.addLayout(row_layout)

            btn = QPushButton()
            btn.setFixedSize(160, 110)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(thumb_path.stem.replace("_", " ").title())

            pixmap = QPixmap(str(thumb_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(160, 110, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                x_off = (scaled.width() - 160) // 2
                y_off = (scaled.height() - 110) // 2
                cropped = scaled.copy(max(0, x_off), max(0, y_off), 160, 110)
                btn.setIcon(QIcon(cropped))
                btn.setIconSize(QSize(154, 104))

            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 14);
                    border: 2px solid rgba(255, 255, 255, 24);
                    border-radius: 8px;
                    padding: 2px;
                }
                QPushButton:hover {
                    border: 2px solid rgba(255, 255, 255, 90);
                    background-color: rgba(255, 255, 255, 30);
                }
            """)
            btn.clicked.connect(lambda checked=False, p=str(thumb_path): self.preview_wallpaper(p))
            row_layout.addWidget(btn)

        if row_layout and len(static_thumbs) % cols != 0:
            for _ in range(cols - (len(static_thumbs) % cols)):
                spacer = QWidget()
                spacer.setFixedSize(160, 110)
                row_layout.addWidget(spacer)

        static_grid_layout.addStretch()
        static_scroll.setWidget(static_grid_widget)
        static_layout.addWidget(static_scroll)
        self.tabs.addTab(static_tab, "Static Wallpapers")

        # Tab 2: Live & Motion Wallpapers
        motion_tab = QWidget()
        motion_layout = QVBoxLayout(motion_tab)
        motion_layout.setContentsMargins(8, 8, 8, 8)

        motion_scroll = QScrollArea()
        motion_scroll.setWidgetResizable(True)
        motion_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        motion_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        motion_grid_widget = QWidget()
        motion_grid_layout = QVBoxLayout(motion_grid_widget)
        motion_grid_layout.setContentsMargins(0, 0, 0, 0)
        motion_grid_layout.setSpacing(10)

        motion_dir = main_window.asset_path("motion")
        motion_files = []
        if motion_dir and Path(motion_dir).is_dir():
            for f in sorted(Path(motion_dir).iterdir()):
                if f.suffix.lower() in (".mpg", ".mpeg", ".mp4", ".wmv", ".avi", ".mov"):
                    motion_files.append(f)

        row_layout = None
        for idx, file_path in enumerate(motion_files):
            if idx % cols == 0:
                row_layout = QHBoxLayout()
                row_layout.setSpacing(10)
                motion_grid_layout.addLayout(row_layout)

            btn = QPushButton()
            btn.setFixedSize(160, 110)
            btn.setCursor(Qt.PointingHandCursor)

            name = file_path.stem.replace("_", " ").title()
            btn.setText(f"🎬\n\n{name}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(15, 23, 42, 180);
                    border: 2px solid rgba(255, 255, 255, 24);
                    border-radius: 8px;
                    color: #f3f4f6;
                    font-weight: bold;
                    font-size: 13px;
                    text-align: center;
                }
                QPushButton:hover {
                    border: 2px solid rgba(255, 255, 255, 90);
                    background-color: rgba(255, 255, 255, 30);
                }
            """)
            btn.clicked.connect(lambda checked=False, p=str(file_path): self.preview_wallpaper(p))
            row_layout.addWidget(btn)

        if row_layout and len(motion_files) % cols != 0:
            for _ in range(cols - (len(motion_files) % cols)):
                spacer = QWidget()
                spacer.setFixedSize(160, 110)
                row_layout.addWidget(spacer)

        motion_grid_layout.addStretch()
        motion_scroll.setWidget(motion_grid_widget)
        motion_layout.addWidget(motion_scroll)
        self.tabs.addTab(motion_tab, "Live & Motion")

        # Custom & Action buttons
        custom_row = QHBoxLayout()
        custom_btn = QPushButton("Browse Custom File...")
        custom_btn.clicked.connect(self.browse_custom)
        clear_btn = QPushButton("Clear Wallpaper")
        clear_btn.setObjectName("DeleteButton")
        clear_btn.clicked.connect(self.clear_wallpaper)
        custom_row.addWidget(custom_btn)
        custom_row.addWidget(clear_btn)
        custom_row.addStretch()
        layout.addLayout(custom_row)

        action_row = QHBoxLayout()
        save_btn = QPushButton("Save && Apply")
        save_btn.setObjectName("AddButton")
        save_btn.clicked.connect(self.save_and_close)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.cancel_and_close)
        action_row.addStretch()
        action_row.addWidget(save_btn)
        action_row.addWidget(cancel_btn)
        layout.addLayout(action_row)

    def preview_wallpaper(self, path):
        self.selected_path = path
        self.main_window.wallpaper_path = path
        self.main_window.update_wallpaper_media()

    def browse_custom(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Wallpaper or Live Wallpaper",
            "",
            "Images/Videos (*.png *.jpg *.jpeg *.gif *.mp4 *.mpg *.avi *.mov *.wmv *.mkv)",
        )
        if path:
            self.preview_wallpaper(path)

    def clear_wallpaper(self):
        self.selected_path = ""
        self.main_window.wallpaper_path = ""
        self.main_window.wallpaper_pixmap = QPixmap()
        self.main_window.stop_live_wallpaper()
        self.main_window.update()

    def save_and_close(self):
        self.main_window.wallpaper_path = self.selected_path
        set_setting("wallpaper_path", self.selected_path)
        self.main_window.update_wallpaper_media()
        self.accept()

    def cancel_and_close(self):
        self.main_window.wallpaper_path = self.original_wallpaper
        self.main_window.update_wallpaper_media()
        self.reject()

    def closeEvent(self, event):
        if self.result() != QDialog.Accepted:
            self.main_window.wallpaper_path = self.original_wallpaper
            self.main_window.update_wallpaper_media()
        super().closeEvent(event)


class WallpaperSidebar(QFrame):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setObjectName("WallpaperSidebar")
        self.thumbnail_cache = {}

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Wallpapers")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        header_layout.addWidget(title)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_custom)
        header_layout.addWidget(browse_btn)
        layout.addLayout(header_layout)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(10)

        self.load_wallpapers()

        self.scroll.setWidget(scroll_widget)
        layout.addWidget(self.scroll, 1)

        # Clear button
        clear_btn = QPushButton("Clear Wallpaper")
        clear_btn.setObjectName("DeleteButton")
        clear_btn.clicked.connect(self.clear_wallpaper)
        layout.addWidget(clear_btn)

    def load_wallpapers(self):
        # Static wallpapers
        wp_dir = self.main_window.asset_path("wallpapers")
        static_files = []
        if wp_dir and Path(wp_dir).is_dir():
            for f in sorted(Path(wp_dir).iterdir()):
                if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
                    static_files.append(f)

        # Motion wallpapers
        motion_dir = self.main_window.asset_path("motion")
        motion_files = []
        if motion_dir and Path(motion_dir).is_dir():
            for f in sorted(Path(motion_dir).iterdir()):
                if f.suffix.lower() in (".mp4", ".mpg", ".mpeg", ".avi", ".mov", ".wmv", ".mkv"):
                    motion_files.append(f)

        if motion_files:
            sec_lbl = QLabel("Live & Motion")
            sec_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #10b981; margin-top: 6px;")
            self.scroll_layout.addWidget(sec_lbl)
            for f in motion_files:
                self.add_wallpaper_item(f, is_motion=True)

        if static_files:
            sec_lbl = QLabel("Static Wallpapers")
            sec_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #3b82f6; margin-top: 6px;")
            self.scroll_layout.addWidget(sec_lbl)
            for f in static_files:
                self.add_wallpaper_item(f, is_motion=False)

        self.scroll_layout.addStretch()

    def add_wallpaper_item(self, file_path, is_motion=False):
        btn = QPushButton()
        btn.setFixedSize(240, 130)
        btn.setCursor(Qt.PointingHandCursor)
        
        name = file_path.stem.replace("_", " ").title()
        btn.setToolTip(name)
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 14);
                border: 2px solid rgba(255, 255, 255, 24);
                border-radius: 8px;
                color: white;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                border: 2px solid rgba(255, 255, 255, 90);
                background-color: rgba(255, 255, 255, 30);
            }
        """)

        if is_motion:
            btn.setText(f"🎬\n\n{name}")
        else:
            thumb_key = str(file_path)
            if thumb_key not in self.thumbnail_cache:
                pixmap = QPixmap(str(file_path))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(240, 130, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    cropped = scaled.copy((scaled.width() - 240) // 2, (scaled.height() - 130) // 2, 240, 130)
                    self.thumbnail_cache[thumb_key] = cropped
                else:
                    self.thumbnail_cache[thumb_key] = QPixmap()
            
            thumb_pix = self.thumbnail_cache[thumb_key]
            if not thumb_pix.isNull():
                btn.setIcon(QIcon(thumb_pix))
                btn.setIconSize(QSize(236, 126))

        btn.clicked.connect(lambda checked=False, p=str(file_path): self.select_wallpaper(p))
        self.scroll_layout.addWidget(btn)

    def select_wallpaper(self, path):
        self.main_window.wallpaper_path = path
        set_setting("wallpaper_path", path)
        self.main_window.update_wallpaper_media()
        self.main_window.update_preset_1_auto_save()

    def clear_wallpaper(self):
        self.main_window.wallpaper_path = ""
        set_setting("wallpaper_path", "")
        self.main_window.update_wallpaper_media()
        self.main_window.update_preset_1_auto_save()

    def browse_custom(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Wallpaper or Live Wallpaper",
            "",
            "Images/Videos (*.png *.jpg *.jpeg *.gif *.mp4 *.mpg *.avi *.mov *.wmv *.mkv)",
        )
        if path:
            self.select_wallpaper(path)


class ChecklistCategoryManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Checklist Categories")
        self.resize(500, 400)
        if parent:
            self.setStyleSheet(parent.styleSheet())
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        title = QLabel("Checklist Categories")
        title.setProperty("class", "CardTitle")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Category Name", "Include in Progress", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        layout.addWidget(self.table)
        
        add_row = QHBoxLayout()
        self.new_cat_input = QLineEdit()
        self.new_cat_input.setPlaceholderText("New Category Name...")
        add_btn = QPushButton("Add Category")
        add_btn.setObjectName("AddButton")
        add_btn.clicked.connect(self.add_new_category)
        add_row.addWidget(self.new_cat_input)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)
        
        order_row = QHBoxLayout()
        up_btn = QPushButton("Move Up")
        up_btn.clicked.connect(lambda: self.move_category("up"))
        down_btn = QPushButton("Move Down")
        down_btn.clicked.connect(lambda: self.move_category("down"))
        order_row.addWidget(up_btn)
        order_row.addWidget(down_btn)
        order_row.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        order_row.addWidget(close_btn)
        layout.addLayout(order_row)
        
        self.reload_categories()
        
    def reload_categories(self):
        self.categories = get_categories(include_hidden=True)
        self.table.setRowCount(0)
        for idx, (name, inc, disp, is_hidden) in enumerate(self.categories):
            self.table.insertRow(idx)
            self.table.setRowHeight(idx, 40)
            
            # Name Edit
            name_edit = QLineEdit(name)
            name_edit.editingFinished.connect(lambda n=name, edit=name_edit: self.rename_category(n, edit.text()))
            self.table.setCellWidget(idx, 0, name_edit)
            
            # Progress checkbox
            chk = QCheckBox()
            chk.setChecked(bool(inc))
            chk.stateChanged.connect(lambda state, n=name: self.toggle_progress(n, state == Qt.Checked.value))
            
            chk_holder = QWidget()
            chk_layout = QHBoxLayout(chk_holder)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk_layout.setAlignment(Qt.AlignCenter)
            chk_layout.addWidget(chk)
            self.table.setCellWidget(idx, 1, chk_holder)
            
            # Delete Action
            del_btn = QPushButton("Delete")
            del_btn.setObjectName("DeleteButton")
            del_btn.clicked.connect(lambda checked=False, n=name: self.delete_category_action(n))
            self.table.setCellWidget(idx, 2, del_btn)
            
    def add_new_category(self):
        name = self.new_cat_input.text().strip()
        if not name:
            return
        add_category(name, 1)
        self.new_cat_input.clear()
        self.reload_categories()
        
    def rename_category(self, old_name, new_name):
        new_name = new_name.strip()
        if not new_name or old_name == new_name:
            return
        update_category(old_name, new_name)
        self.reload_categories()
        
    def toggle_progress(self, name, include):
        update_category(name, name, include)
        
    def delete_category_action(self, name):
        confirm = QMessageBox.question(self, "Delete Category", f"Are you sure you want to delete category '{name}'? This will delete all completions for this category.")
        if confirm == QMessageBox.Yes:
            delete_category(name)
            self.reload_categories()
            
    def move_category(self, direction):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.categories[row][0]
        
        idx = next(i for i, cat in enumerate(self.categories) if cat[0] == name)
        if direction == "up" and idx > 0:
            self.categories[idx], self.categories[idx-1] = self.categories[idx-1], self.categories[idx]
        elif direction == "down" and idx < len(self.categories) - 1:
            self.categories[idx], self.categories[idx+1] = self.categories[idx+1], self.categories[idx]
        else:
            return
            
        reorder_categories([cat[0] for cat in self.categories])
        self.reload_categories()
        new_row = row - 1 if direction == "up" else row + 1
        self.table.setCurrentCell(new_row, 0)


class SubjectManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Subjects / Courses")
        self.resize(450, 400)
        if parent:
            self.setStyleSheet(parent.styleSheet())
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        title = QLabel("Subjects & Courses")
        title.setProperty("class", "CardTitle")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Subject / Course Name", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        layout.addWidget(self.table)
        
        add_row = QHBoxLayout()
        self.new_subj_input = QLineEdit()
        self.new_subj_input.setPlaceholderText("New Subject Name...")
        add_btn = QPushButton("Add Subject")
        add_btn.setObjectName("AddButton")
        add_btn.clicked.connect(self.add_new_subject)
        add_row.addWidget(self.new_subj_input)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)
        
        order_row = QHBoxLayout()
        up_btn = QPushButton("Move Up")
        up_btn.clicked.connect(lambda: self.move_subject("up"))
        down_btn = QPushButton("Move Down")
        down_btn.clicked.connect(lambda: self.move_subject("down"))
        order_row.addWidget(up_btn)
        order_row.addWidget(down_btn)
        order_row.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        order_row.addWidget(close_btn)
        layout.addLayout(order_row)
        
        self.reload_subjects()
        
    def reload_subjects(self):
        self.subjects = get_subjects()
        self.table.setRowCount(0)
        for idx, name in enumerate(self.subjects):
            self.table.insertRow(idx)
            self.table.setRowHeight(idx, 40)
            
            # Name Edit
            name_edit = QLineEdit(name)
            name_edit.editingFinished.connect(lambda n=name, edit=name_edit: self.rename_subject_action(n, edit.text()))
            self.table.setCellWidget(idx, 0, name_edit)
            
            # Delete Action
            del_btn = QPushButton("Delete")
            del_btn.setObjectName("DeleteButton")
            del_btn.clicked.connect(lambda checked=False, n=name: self.delete_subject_action(n))
            self.table.setCellWidget(idx, 1, del_btn)
            
    def add_new_subject(self):
        name = self.new_subj_input.text().strip()
        if not name:
            return
        add_subject(name)
        self.new_subj_input.clear()
        self.reload_subjects()
        
    def rename_subject_action(self, old_name, new_name):
        new_name = new_name.strip()
        if not new_name or old_name == new_name:
            return
        rename_subject(old_name, new_name)
        self.reload_subjects()
        
    def delete_subject_action(self, name):
        confirm = QMessageBox.question(self, "Delete Subject", f"Are you sure you want to delete subject '{name}'? This will delete all chapters/topics and progress associated with it.")
        if confirm == QMessageBox.Yes:
            delete_subject(name)
            self.reload_subjects()
            
    def move_subject(self, direction):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.subjects[row]
        
        idx = self.subjects.index(name)
        if direction == "up" and idx > 0:
            self.subjects[idx], self.subjects[idx-1] = self.subjects[idx-1], self.subjects[idx]
        elif direction == "down" and idx < len(self.subjects) - 1:
            self.subjects[idx], self.subjects[idx+1] = self.subjects[idx+1], self.subjects[idx]
        else:
            return
            
        reorder_subjects(self.subjects)
        self.reload_subjects()
        new_row = row - 1 if direction == "up" else row + 1
        self.table.setCurrentCell(new_row, 0)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setObjectName("MainWindowRoot")
        self.setWindowTitle("PrepMate")
        self.resize(1200, 900)

        self.subject_tables = {}
        self.subject_progress_labels = {}
        self.subjects = []
        self.app_font_size = int(get_setting("app_font_size", "13"))
        self.app_font_family = get_setting("app_font_family", "Arial")
        self.wallpaper_pixmap = QPixmap()
        self.live_wallpaper_pixmap = QPixmap()
        self.cached_scaled_wallpaper = QPixmap()
        self.last_paint_size = QSize()
        self.wallpaper_player = None
        self.wallpaper_audio = None
        self.wallpaper_video_sink = None
        self.audio_players = []
        self.current_quote_id = None
        self.icon_cache = {}
        self.theme_name = "Midnight Teal"
        self.ui_opacity = 0.62
        self.wallpaper_path = ""
        self.ui_mode = "aesthetic"

        self.hover_tooltip = QLabel(self)
        self.hover_tooltip.setObjectName("HoverTooltip")
        self.hover_tooltip.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.hover_tooltip.hide()

        # Outer layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 18, 26, 18)
        outer.setSpacing(14)

        # Header area
        header = QHBoxLayout()
        header.setSpacing(14)

        title_box = QFrame()
        title_box.setProperty("class", "HeaderTile")
        self.apply_shadow(title_box, blur=18, alpha=140)

        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(18, 12, 18, 12)
        title_layout.setSpacing(2)

        # Title row with mission button
        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        self.title_label = QLabel("Operation")
        self.title_label.setObjectName("Title")
        self.apply_shadow(self.title_label, blur=18, alpha=180)

        self.mission_btn = QPushButton("Missions ▾")
        self.mission_btn.setCursor(Qt.PointingHandCursor)
        self.mission_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: bold;
                color: #ffffff;
                background-color: rgba(255, 255, 255, 24);
                border: 1px solid rgba(255, 255, 255, 34);
                border-radius: 6px;
                padding: 5px 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 50);
            }
        """)
        self.mission_btn.clicked.connect(self.show_mission_menu)

        title_row.addWidget(self.title_label)
        title_row.addStretch()
        title_row.addWidget(self.mission_btn)
        title_layout.addLayout(title_row)

        subtitle = QLabel("Prepare. Perform. Prevail.")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignLeft)
        self.apply_shadow(subtitle, blur=14, alpha=160)
        title_layout.addWidget(subtitle)

        # Settings tile
        title_box.setFixedWidth(625)
        self.settings_tile = self.make_settings_tile()
        header.addWidget(title_box)
        header.addWidget(self.settings_tile, 1)
        outer.addLayout(header)

        # Scroll area & absolute positioned canvas
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.canvas = QWidget()
        self.canvas.setObjectName("PageContainer")
        self.canvas.setMinimumSize(1150, 920)
        self.scroll.setWidget(self.canvas)
        outer.addWidget(self.scroll)

        # Instantiate cards as AeroCards
        self.quote_area = self.make_quote_area()
        self.countdown_card = self.make_countdown_card()
        self.focus_card = self.make_focus_hub()
        self.syllabus_card = self.make_syllabus_card()
        self.daily_card = self.make_task_card("Daily Log", "daily", "Chapter / Topic...")
        self.progress_card = self.make_progress_card()
        self.extras_card = self.make_extras_card()

        # Timers
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)

        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self.tick_focus_hub)

        # Load workspace settings, populate missions and layout geometries
        self.reload_workspace()

    def set_app_style(self, reload_wallpaper=False):
        theme = THEMES.get(self.theme_name, THEMES["Burgundy"])
        if reload_wallpaper:
            self.update_wallpaper_media()
        panel = self.with_opacity(theme["panel"], self.ui_opacity)
        field = self.with_opacity(theme["field"], max(0.18, self.ui_opacity - 0.12))
        tile = f"rgba(255, 255, 255, {int(34 * self.ui_opacity)})"
        tile_hover = f"rgba(255, 255, 255, {int(54 * self.ui_opacity)})"
        edge = f"rgba(255, 255, 255, {int(48 * self.ui_opacity)})"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                color: #e5e7eb;
                font-family: "{self.app_font_family}", Segoe UI Variable, Segoe UI;
                font-size: {self.app_font_size}px;
            }}

            QWidget#MainWindowRoot {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {theme["start"]}, stop: 1 {theme["end"]});
            }}

            QWidget#PageContainer {{
                background-color: transparent;
            }}

            QLabel {{
                background: transparent;
                color: #e5e7eb;
            }}

            QLabel#HoverTooltip {{
                background-color: rgba(15, 23, 42, 235);
                color: #f8fafc;
                border: 1px solid rgba(255, 255, 255, 45);
                border-radius: 6px;
                padding: 4px 10px;
                font-size: {self.app_font_size - 1}px;
                font-weight: bold;
            }}

            QLabel#Title {{
                font-size: {self.app_font_size + 17}px;
                font-weight: bold;
                color: #ffffff;
            }}

            QLabel#Subtitle {{
                font-size: {self.app_font_size}px;
                color: {theme["accent"]};
            }}

            QFrame[class="HeaderTile"], QFrame#SettingsTile {{
                background-color: {panel};
                border: 1px solid {edge};
                border-radius: 10px;
            }}

            QFrame#WallpaperSidebar {{
                background-color: rgba(15, 23, 42, 230);
                border-left: 1px solid {edge};
                border-top: none;
                border-bottom: none;
                border-right: none;
            }}

            QLabel#Quote {{
                color: #f8fafc;
                font-style: italic;
                font-size: {self.app_font_size + 1}px;
                padding: 6px;
            }}

            QFrame#QuoteFrame {{
                background-color: {field};
                border: 1px solid {edge};
                border-radius: 10px;
            }}

            QFrame#CountTile {{
                background-color: {tile};
                border: none;
                border-radius: 8px;
            }}

            QFrame[class="TopicTile"] {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }}

            QLabel[class="CardTitle"] {{
                font-size: {self.app_font_size + 1}px;
                font-weight: bold;
                color: #ffffff;
            }}

            QLabel[class="CountNumber"] {{
                font-size: {self.app_font_size + 20}px;
                font-weight: bold;
                color: #ffffff;
            }}

            QLabel[class="CountLabel"] {{
                font-size: {max(10, self.app_font_size - 3)}px;
                letter-spacing: 1px;
                color: #cbd5e1;
            }}

            QLabel[class="TimerText"] {{
                font-size: {self.app_font_size + 22}px;
                font-weight: bold;
                color: #ffffff;
            }}

            QPushButton {{
                background-color: {self.with_opacity(theme["button"], max(0.35, self.ui_opacity - 0.10))};
                color: white;
                border: none;
                border-radius: 7px;
                padding: 6px 10px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {tile_hover};
            }}

            QPushButton#AddButton {{
                background-color: #2f3a3f;
                border: 1px solid rgba(255, 255, 255, 22);
            }}

            QPushButton#DeleteButton {{
                background-color: #3a2222;
                border: 1px solid rgba(239, 68, 68, 62);
            }}



            QPushButton[class="StatusIconButton"] {{
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
                padding: 0;
                border: none;
                background-color: transparent;
            }}

            QPushButton[class="ImportantButton"] {{
                min-width: 26px;
                max-width: 26px;
                min-height: 26px;
                max-height: 26px;
                padding: 0;
                border: none;
                background-color: transparent;
            }}

            QLineEdit {{
                background-color: {field};
                border: none;
                border-radius: 7px;
                padding: 7px;
                color: #e5e7eb;
            }}

            QPlainTextEdit, QListWidget, QComboBox, QSpinBox {{
                background-color: {field};
                border: none;
                border-radius: 7px;
                padding: 6px;
                color: #e5e7eb;
            }}

            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #555c64;
                border-bottom: 1px solid #555c64;
                background-color: #3b424a;
            }}

            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 24px;
                border-left: 1px solid #555c64;
                background-color: #3b424a;
            }}

            QSpinBox::up-arrow {{
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'><polygon points='0,8 10,8 5,2' fill='white'/></svg>");
                width: 10px;
                height: 10px;
            }}

            QSpinBox::down-arrow {{
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'><polygon points='0,2 10,2 5,8' fill='white'/></svg>");
                width: 10px;
                height: 10px;
            }}

            QCheckBox {{
                background: transparent;
                spacing: 4px;
            }}

            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255, 255, 255, 40);
                border-radius: 9px;
                background-color: rgba(0, 0, 0, 80);
            }}

            QCheckBox::indicator:checked {{
                background-color: #22c55e;
                border: 2px solid #22c55e;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjIwIDYgOSAxNyA0IDEyIi8+PC9zdmc+);
            }}

            QScrollArea {{
                border: none;
                background: transparent;
            }}

            QTabWidget::tab-bar {{
                left: 0px;
            }}

            QTabWidget::pane {{
                border: 1px solid {edge};
                background-color: {panel};
                border-radius: 8px;
                border-top-left-radius: 0px;
                margin-top: -1px;
            }}

            QTabBar::tab {{
                background-color: {tile};
                color: #9ca3af;
                padding: {max(6, self.app_font_size - 6)}px 16px;
                border: 1px solid {edge};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: -4px;
                font-weight: 500;
            }}

            QTabBar::tab:first {{
                margin-left: 0px;
            }}

            QTabBar::tab:selected {{
                background-color: {panel};
                color: #ffffff;
                border-color: {edge};
                border-bottom: 1px solid {panel};
                font-weight: bold;
                padding-bottom: {max(7, self.app_font_size - 5)}px;
                margin-bottom: -1px;
                margin-right: -4px;
            }}

            QTabBar::tab:hover:!selected {{
                background-color: rgba(255, 255, 255, 18);
                color: #ffffff;
            }}

            QTableWidget {{
                background-color: transparent;
                alternate-background-color: rgba(255, 255, 255, {int(10 * self.ui_opacity)});
                gridline-color: rgba(255, 255, 255, 24);
                border: none;
                border-radius: 8px;
                selection-background-color: #334155;
            }}

            QHeaderView::section {{
                background-color: rgba(255, 255, 255, 18);
                color: white;
                padding: 7px;
                border: none;
                font-weight: bold;
            }}

            QHeaderView#ChecklistHeader::section {{
                background-color: transparent;
                border: none;
            }}

            QTableWidget::item {{
                background: transparent;
                padding: 4px;
            }}

            QScrollBar:vertical {{
                border: none;
                background: rgba(0, 0, 0, 40);
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 70), stop:1 rgba(255, 255, 255, 30));
                min-height: 25px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 40);
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(140, 200, 150, 180), stop:1 rgba(90, 160, 110, 130));
                border: 1px solid rgba(255, 255, 255, 80);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}

            QScrollBar:horizontal {{
                border: none;
                background: rgba(0, 0, 0, 40);
                height: 12px;
                margin: 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 70), stop:1 rgba(255, 255, 255, 30));
                min-width: 25px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 40);
            }}
            QScrollBar::handle:horizontal:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(140, 200, 150, 180), stop:1 rgba(90, 160, 110, 130));
                border: 1px solid rgba(255, 255, 255, 80);
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}

        """)
        self.update()

    def with_opacity(self, color, opacity):
        is_solid = get_setting("solid_mode", "0") == "1"
        if is_solid:
            if color.startswith("#") and len(color) == 7:
                red = int(color[1:3], 16)
                green = int(color[3:5], 16)
                blue = int(color[5:7], 16)
                return f"rgb({red}, {green}, {blue})"
            if color.startswith("rgba"):
                values = color[color.find("(") + 1:color.rfind(")")].split(",")
                return f"rgb({values[0].strip()}, {values[1].strip()}, {values[2].strip()})"
            return color

        if color.startswith("rgba"):
            values = color[color.find("(") + 1:color.rfind(")")].split(",")
            base_alpha = int(values[3].strip())
            alpha = int(max(0.0, min(1.0, opacity)) * base_alpha)
            return f"rgba({values[0].strip()}, {values[1].strip()}, {values[2].strip()}, {alpha})"

        alpha = int(max(0.0, min(1.0, opacity)) * 255)
        if color.startswith("#") and len(color) == 7:
            red = int(color[1:3], 16)
            green = int(color[3:5], 16)
            blue = int(color[5:7], 16)
            return f"rgba({red}, {green}, {blue}, {alpha})"

        return color

    def paintEvent(self, event):
        super().paintEvent(event)
        if getattr(self, "ui_mode", "aesthetic") == "lite":
            return
        painter = QPainter(self)

        pix = None
        is_live = False
        if not self.live_wallpaper_pixmap.isNull():
            pix = self.live_wallpaper_pixmap
            is_live = True
        elif not self.wallpaper_pixmap.isNull():
            pix = self.wallpaper_pixmap

        if pix and not pix.isNull():
            if is_live:
                # GPU-accelerated direct scaling to avoid CPU bottlenecks with video frames
                img_w = pix.width()
                img_h = pix.height()
                scale = max(self.width() / img_w, self.height() / img_h)
                w = int(img_w * scale)
                h = int(img_h * scale)
                x = (self.width() - w) // 2
                y = (self.height() - h) // 2
                painter.drawPixmap(x, y, w, h, pix)
            else:
                # Standard caching for static wallpapers
                if self.size() != self.last_paint_size or self.cached_scaled_wallpaper.isNull():
                    self.cached_scaled_wallpaper = pix.scaled(
                        self.size(),
                        Qt.KeepAspectRatioByExpanding,
                        Qt.SmoothTransformation,
                    )
                    self.last_paint_size = self.size()
                x = (self.width() - self.cached_scaled_wallpaper.width()) // 2
                y = (self.height() - self.cached_scaled_wallpaper.height()) // 2
                painter.drawPixmap(x, y, self.cached_scaled_wallpaper)
            
            painter.fillRect(self.rect(), QColor(4, 6, 10, 118))


    def apply_shadow(self, widget, blur=24, alpha=130):
        if getattr(self, "ui_mode", "aesthetic") == "lite":
            widget.setGraphicsEffect(None)
            return
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, alpha))
        widget.setGraphicsEffect(shadow)

    def update_graphics_shadows(self):
        is_lite = (getattr(self, "ui_mode", "aesthetic") == "lite")
        cards = [self.quote_area, self.countdown_card, self.focus_card, 
                 self.syllabus_card, self.daily_card["frame"], 
                 self.progress_card, self.extras_card]
        for card in cards:
            if is_lite:
                card.setGraphicsEffect(None)
            else:
                self.apply_shadow(card)

    def asset_path(self, *parts):
        relative = Path("asset").joinpath(*parts)
        roots = []

        if getattr(sys, "frozen", False):
            # Check _MEIPASS first so bundled assets take priority
            if hasattr(sys, "_MEIPASS"):
                roots.append(Path(sys._MEIPASS))
            roots.append(Path(sys.executable).resolve().parent)
        else:
            roots.append(Path(__file__).resolve().parent)

        roots.append(Path.cwd())

        for root in roots:
            candidate = root / relative
            if candidate.exists():
                return candidate

        return None

    def update_wallpaper_media(self):
        self.cached_scaled_wallpaper = QPixmap()
        self.last_paint_size = QSize()
        
        wp_path = self.wallpaper_path
        if wp_path:
            p = Path(wp_path)
            if not p.exists():
                parts = p.parts
                if "asset" in parts:
                    idx = parts.index("asset")
                    sub_parts = parts[idx+1:]
                    candidate = self.asset_path(*sub_parts)
                    if candidate:
                        wp_path = str(candidate)
                        
        if self.ui_mode == "lite":
            self.stop_live_wallpaper()
            self.wallpaper_pixmap = QPixmap()
            self.live_wallpaper_pixmap = QPixmap()
            return

        suffix = Path(wp_path).suffix.lower() if wp_path else ""

        if suffix in {".mpg", ".mpeg", ".mp4", ".wmv", ".avi", ".mov"} and wp_path and Path(wp_path).exists():
            self.wallpaper_pixmap = QPixmap()
            self.live_wallpaper_pixmap = QPixmap()
            self.start_live_wallpaper(Path(wp_path))
            return

        self.stop_live_wallpaper()
        self.live_wallpaper_pixmap = QPixmap()
        if wp_path and Path(wp_path).exists():
            pix = QPixmap(wp_path)
            if not pix.isNull():
                screen = QApplication.primaryScreen()
                if screen:
                    sz = screen.size()
                    if pix.width() > sz.width() or pix.height() > sz.height():
                        pix = pix.scaled(sz, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.wallpaper_pixmap = pix
            else:
                self.wallpaper_pixmap = QPixmap()
        else:
            self.wallpaper_pixmap = QPixmap()

    def on_video_frame_changed(self, frame):
        if frame.isValid():
            image = frame.toImage()
            self.live_wallpaper_pixmap = QPixmap.fromImage(image)
            self.update()

    def start_live_wallpaper(self, path):
        if self.wallpaper_player is None:
            self.wallpaper_player = QMediaPlayer(self)
            self.wallpaper_audio = QAudioOutput(self)
            self.wallpaper_audio.setVolume(0)
            self.wallpaper_player.setAudioOutput(self.wallpaper_audio)
            
            self.wallpaper_video_sink = QVideoSink(self)
            self.wallpaper_video_sink.videoFrameChanged.connect(self.on_video_frame_changed)
            self.wallpaper_player.setVideoOutput(self.wallpaper_video_sink)
            
            self.wallpaper_player.setLoops(QMediaPlayer.Infinite)
            self.wallpaper_player.errorOccurred.connect(self.handle_wallpaper_error)

        self.wallpaper_player.setSource(QUrl.fromLocalFile(str(path)))
        self.wallpaper_player.play()

    def stop_live_wallpaper(self):
        if self.wallpaper_player:
            self.wallpaper_player.stop()
        if hasattr(self, "video_widget") and self.video_widget:
            self.video_widget.hide()
        if hasattr(self, "video_overlay") and self.video_overlay:
            self.video_overlay.hide()
        self.live_wallpaper_pixmap = QPixmap()
        self.update()


    def handle_wallpaper_error(self, error, error_string):
        print(f"Live Wallpaper Media Error: {error_string}")
        try:
            self.stop_live_wallpaper()
        except Exception:
            pass

    def play_audio_file(self, path, volume=0.9):
        if not path or not Path(path).exists():
            return False

        # Try Windows MCI first for reliable playback in frozen builds
        try:
            import ctypes
            winmm = ctypes.windll.winmm
            alias = f"nm_{id(path)}_{id(self)}"
            p = str(Path(path).resolve())
            winmm.mciSendStringW(f'open "{p}" type mpegvideo alias {alias}', None, 0, 0)
            winmm.mciSendStringW(f'setaudio {alias} volume to {int(volume * 1000)}', None, 0, 0)
            winmm.mciSendStringW(f'play {alias}', None, 0, 0)
            # Schedule cleanup after 3 seconds
            QTimer.singleShot(3000, lambda: winmm.mciSendStringW(f'close {alias}', None, 0, 0))
            return True
        except Exception:
            pass

        # Fallback to Qt multimedia
        player = QMediaPlayer(self)
        audio = QAudioOutput(self)
        audio.setVolume(volume)
        player.setAudioOutput(audio)
        player.setSource(QUrl.fromLocalFile(str(path)))
        player.mediaStatusChanged.connect(
            lambda status, p=player, a=audio:
            self.cleanup_audio_player(p, a)
            if status in (QMediaPlayer.EndOfMedia, QMediaPlayer.InvalidMedia)
            else None
        )
        self.audio_players.append((player, audio))
        player.play()
        return True

    def cleanup_audio_player(self, player, audio):
        self.audio_players = [
            pair for pair in self.audio_players
            if pair[0] is not player and pair[1] is not audio
        ]
        player.deleteLater()
        audio.deleteLater()

    def play_interaction_sound(self, sound_name):
        if get_setting("sound_enabled", "1") != "1":
            return

        vol_val = int(get_setting(f"volume_{sound_name}", "90"))
        volume = vol_val / 100.0

        paths = {
            "greencheck": self.asset_path("audio", "greencheck.mp3"),
            "orangecheck": self.asset_path("audio", "orangecheck.mp3"),
            "important": self.asset_path("audio", "important.mp3"),
            "plankton": self.asset_path("plankton.mp3"),
        }

        sound_path = paths.get(sound_name)
        if not sound_path or not Path(sound_path).exists():
            return

        if not self.play_audio_file(sound_path, volume=volume):
            QApplication.beep()

    def get_cached_icon(self, name):
        if name in self.icon_cache:
            return self.icon_cache[name]

        paths = {
            "greencheck": self.asset_path("greencheck.png"),
            "orangecheck": self.asset_path("orangecheck.png"),
            "important_active": self.asset_path("Important.png") or self.asset_path("important.png"),
        }

        if name == "important_inactive":
            active = self.get_cached_icon("important_active")
            pixmap = self.make_inactive_pixmap(active)
        else:
            pixmap = QPixmap(str(paths.get(name) or ""))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    96,
                    96,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )

        self.icon_cache[name] = pixmap
        return pixmap

    def make_inactive_pixmap(self, pixmap):
        if pixmap.isNull():
            return QPixmap()

        small = pixmap.scaled(
            96,
            96,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        image = small.toImage().convertToFormat(QImage.Format_ARGB32)
        for y in range(image.height()):
            for x in range(image.width()):
                color = image.pixelColor(x, y)
                gray = int((color.red() + color.green() + color.blue()) / 3)
                color.setRed(gray)
                color.setGreen(gray)
                color.setBlue(gray)
                color.setAlpha(int(color.alpha() * 0.48))
                image.setPixelColor(x, y, color)
        return QPixmap.fromImage(image)

    def ensure_exam_name(self):
        existing = get_setting("exam_name", "").strip()

        if existing:
            return existing

        exam_name, ok = QInputDialog.getText(
            self,
            "Exam Setup",
            "What specific exam are you preparing for?",
            text="NEET",
        )

        exam_name = exam_name.strip() if ok and exam_name.strip() else "NEET"
        set_setting("exam_name", exam_name)
        return exam_name

    def make_rename_icon(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(Qt.white, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(10, 22, 22, 10)
        painter.drawLine(12, 24, 24, 12)
        path = QPainterPath()
        path.moveTo(8, 24)
        path.lineTo(12, 24)
        path.lineTo(10, 22)
        path.closeSubpath()
        painter.setBrush(Qt.white)
        painter.drawPath(path)
        painter.setBrush(QColor(239, 68, 68))
        painter.drawEllipse(21, 7, 4, 4)
        painter.end()
        return QIcon(pixmap)

    def make_delete_icon(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor(239, 68, 68), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(8, 10, 24, 10)
        painter.drawRect(13, 7, 6, 3)
        painter.drawRect(10, 12, 12, 14)
        painter.drawLine(13, 15, 13, 23)
        painter.drawLine(16, 15, 16, 23)
        painter.drawLine(19, 15, 19, 23)
        painter.end()
        return QIcon(pixmap)

    def make_settings_tile(self):
        frame = QFrame()
        frame.setObjectName("SettingsTile")
        self.apply_shadow(frame, blur=18, alpha=130)

        main_layout = QHBoxLayout(frame)
        main_layout.setContentsMargins(14, 8, 14, 8)
        main_layout.setSpacing(14)

        # Helper to create vertical separators
        def create_separator():
            sep = QFrame()
            sep.setFrameShape(QFrame.VLine)
            sep.setFrameShadow(QFrame.Sunken)
            sep.setStyleSheet("background-color: rgba(255, 255, 255, 20); width: 1px; border: none;")
            sep.setFixedWidth(1)
            return sep

        # --- SECTION 1: FONT & LAYOUT ---
        sec1 = QWidget()
        sec1_layout = QVBoxLayout(sec1)
        sec1_layout.setContentsMargins(0, 0, 0, 0)
        sec1_layout.setSpacing(4)

        sec1_title = QLabel("Font & Layout")
        sec1_title.setStyleSheet("font-size: 11px; font-weight: bold; color: rgba(255, 255, 255, 140);")
        sec1_layout.addWidget(sec1_title)

        font_row = QHBoxLayout()
        font_row.setSpacing(4)
        
        font_down = QPushButton("A-")
        font_down.setFixedSize(30, 26)
        font_down.setStyleSheet("QPushButton { padding: 0px 2px; font-size: 11px; font-weight: bold; }")
        font_down.clicked.connect(self.decrease_font)
        
        font_up = QPushButton("A+")
        font_up.setFixedSize(30, 26)
        font_up.setStyleSheet("QPushButton { padding: 0px 2px; font-size: 11px; font-weight: bold; }")
        font_up.clicked.connect(self.increase_font)
        
        self.font_combo = QComboBox()
        self.font_combo.addItems([
            "Segoe UI Variable", "Segoe UI", "Inter", "Roboto", "Outfit", "Arial", "Consolas"
        ])
        self.font_combo.setFixedWidth(130)
        self.font_combo.setCurrentText(self.app_font_family)
        self.font_combo.currentTextChanged.connect(self.change_font_family)
        
        font_row.addWidget(font_down)
        font_row.addWidget(font_up)
        font_row.addWidget(self.font_combo)
        font_row.addStretch()
        sec1_layout.addLayout(font_row)

        chk_layout = QHBoxLayout()
        chk_layout.setSpacing(8)
        self.reset_layout_btn = QPushButton("Reset Layout")
        self.reset_layout_btn.setStyleSheet("font-size: 11px;")
        self.reset_layout_btn.clicked.connect(self.reset_layout)
        
        chk_layout.addWidget(self.reset_layout_btn)
        chk_layout.addStretch()
        sec1_layout.addLayout(chk_layout)

        # --- SECTION 2: THEME & SOUND ---
        sec2 = QWidget()
        sec2_layout = QVBoxLayout(sec2)
        sec2_layout.setContentsMargins(0, 0, 0, 0)
        sec2_layout.setSpacing(4)

        sec2_title = QLabel("Theme, Wallpaper & Sound")
        sec2_title.setStyleSheet("font-size: 11px; font-weight: bold; color: rgba(255, 255, 255, 140);")
        sec2_layout.addWidget(sec2_title)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(4)
        
        self.theme_box = QComboBox()
        self.theme_box.addItems(THEMES.keys())
        self.theme_box.setFixedWidth(130)
        self.theme_box.setCurrentText(self.theme_name)
        self.theme_box.currentTextChanged.connect(self.change_theme)
        
        self.wallpaper_btn = QPushButton("Wallpaper")
        self.wallpaper_btn.clicked.connect(self.toggle_wallpaper_sidebar)

        clear_wallpaper_btn = QPushButton("Clear")
        clear_wallpaper_btn.clicked.connect(self.clear_wallpaper)

        self.settings_gear_btn = QPushButton()
        self.settings_gear_btn.setIcon(self.make_gear_icon())
        self.settings_gear_btn.setIconSize(QSize(22, 22))
        self.settings_gear_btn.setFixedSize(30, 26)
        self.settings_gear_btn.setToolTip("Deep UI Settings")
        self.settings_gear_btn.clicked.connect(self.open_deep_settings_dialog)
        
        theme_row.addWidget(self.theme_box)
        theme_row.addWidget(self.wallpaper_btn)
        theme_row.addWidget(clear_wallpaper_btn)
        theme_row.addWidget(self.settings_gear_btn)
        theme_row.addStretch()
        sec2_layout.addLayout(theme_row)

        opacity_sound_row = QHBoxLayout()
        opacity_sound_row.setSpacing(6)
        
        opacity_label = QLabel("UI Glass")
        opacity_label.setStyleSheet("font-size: 11px;")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(28, 100)
        self.opacity_slider.setFixedWidth(90)
        self.opacity_slider.setValue(int(float(self.ui_opacity) * 100))
        self.opacity_slider.valueChanged.connect(self.change_ui_opacity)
        self.opacity_slider.sliderReleased.connect(self.save_ui_opacity)
        
        self.sound_toggle_btn = SoundToggleButton(self)
        self.sound_vol_btn = SoundVolumeButton(self)
        
        opacity_sound_row.addWidget(opacity_label)
        opacity_sound_row.addWidget(self.opacity_slider)
        opacity_sound_row.addWidget(self.sound_toggle_btn)
        opacity_sound_row.addWidget(self.sound_vol_btn)
        opacity_sound_row.addStretch()
        sec2_layout.addLayout(opacity_sound_row)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(6)
        
        preset_label = QLabel("Presets")
        preset_label.setStyleSheet("font-size: 11px;")
        
        self.presets_combo = QComboBox()
        self.presets_combo.setFixedWidth(110)
        self.presets_combo.currentTextChanged.connect(self.load_selected_preset)
        
        save_preset_btn = QPushButton("Save Preset")
        save_preset_btn.setStyleSheet("QPushButton { font-size: 10px; padding: 2px 8px; }")
        save_preset_btn.clicked.connect(self.save_theme_preset)
        
        preset_row.addWidget(preset_label)
        preset_row.addWidget(self.presets_combo)
        preset_row.addWidget(save_preset_btn)
        preset_row.addStretch()
        sec2_layout.addLayout(preset_row)
        
        self.load_presets_combo()

        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        self.mode_toggle = ModeToggleButton(self.ui_mode, self)
        self.mode_toggle.modeChanged.connect(self.on_ui_mode_changed)
        mode_row.addWidget(self.mode_toggle)
        mode_row.addStretch()
        sec2_layout.addLayout(mode_row)

        # --- SECTION 3: SYSTEM & BACKUPS ---
        sec3 = QWidget()
        sec3_layout = QVBoxLayout(sec3)
        sec3_layout.setContentsMargins(0, 0, 0, 0)
        sec3_layout.setSpacing(4)

        sec3_title = QLabel("System & Backups")
        sec3_title.setStyleSheet("font-size: 11px; font-weight: bold; color: rgba(255, 255, 255, 140);")
        sec3_layout.addWidget(sec3_title)

        backup_row1 = QHBoxLayout()
        backup_row1.setSpacing(4)
        
        data_backup_btn = QPushButton("Data Backup")
        data_backup_btn.clicked.connect(self.data_backup)
        
        snapshot_btn = QPushButton("Save Snapshot")
        snapshot_btn.clicked.connect(self.save_snapshot)
        
        backup_row1.addWidget(data_backup_btn)
        backup_row1.addWidget(snapshot_btn)
        backup_row1.addStretch()
        sec3_layout.addLayout(backup_row1)

        backup_row2 = QHBoxLayout()
        backup_row2.setSpacing(4)
        
        self.upgrade_btn = QPushButton("Upgrade App...")
        self.upgrade_btn.clicked.connect(self.upgrade_app)
        
        reset_btn = QPushButton("Reset...")
        reset_btn.clicked.connect(self.show_reset_options_dialog)
        
        backup_row2.addWidget(self.upgrade_btn)
        backup_row2.addWidget(reset_btn)
        backup_row2.addStretch()
        sec3_layout.addLayout(backup_row2)

        main_layout.addWidget(sec1)
        main_layout.addWidget(create_separator())
        main_layout.addWidget(sec2)
        main_layout.addWidget(create_separator())
        main_layout.addWidget(sec3)

        return frame

    def increase_font(self):
        self.app_font_size = min(20, self.app_font_size + 1)
        set_setting("app_font_size", str(self.app_font_size))
        self.set_app_style()
        for card in self.canvas.findChildren(AeroCard):
            card.apply_card_theme()
        self.update_table_row_heights()

    def decrease_font(self):
        self.app_font_size = max(10, self.app_font_size - 1)
        set_setting("app_font_size", str(self.app_font_size))
        self.set_app_style()
        for card in self.canvas.findChildren(AeroCard):
            card.apply_card_theme()
        self.update_table_row_heights()

    def change_font_family(self, font_name):
        self.app_font_family = font_name
        set_setting("app_font_family", font_name)
        self.set_app_style()
        for card in self.canvas.findChildren(AeroCard):
            card.apply_card_theme()
        self.update_table_row_heights()

    def update_table_row_heights(self):
        row_h = max(46, self.app_font_size + 32)
        for table in self.subject_tables.values():
            for r in range(table.rowCount()):
                table.setRowHeight(r, row_h)

    def change_theme(self, theme_name):
        self.theme_name = theme_name
        set_setting("theme_preset", theme_name)
        for card in self.canvas.findChildren(AeroCard):
            card.card_theme = ""
            set_setting(f"tile_theme_{card.tile_id}", "")
        self.set_app_style()
        for card in self.canvas.findChildren(AeroCard):
            card.apply_card_theme()
        self.update_overall_progress()
        self.update_preset_1_auto_save()

    def change_ui_opacity(self, value):
        self.ui_opacity = value / 100.0
        self.set_app_style(reload_wallpaper=False)
        for card in self.canvas.findChildren(AeroCard):
            card.apply_card_theme()

    def save_ui_opacity(self):
        set_setting("ui_opacity", f"{self.ui_opacity:.2f}")
        self.update_preset_1_auto_save()

    def update_preset_1_auto_save(self):
        import json
        raw = get_setting("theme_presets", "[]")
        try:
            presets = json.loads(raw)
        except Exception:
            presets = []
            
        preset_1 = None
        for p in presets:
            if isinstance(p, dict) and p.get("name") == "Preset 1":
                preset_1 = p
                break
                
        if not preset_1:
            preset_1 = {"name": "Preset 1"}
            presets.insert(0, preset_1)
            
        current_cards = {}
        for card in self.canvas.findChildren(AeroCard):
            current_cards[card.tile_id] = card.card_theme if card.card_theme else ""
            
        preset_1["theme"] = self.theme_name
        preset_1["opacity"] = round(self.ui_opacity, 2)
        preset_1["wallpaper"] = self.wallpaper_path
        preset_1["cards"] = current_cards
        
        set_setting("theme_presets", json.dumps(presets))
        
        if hasattr(self, "presets_combo"):
            self.load_presets_combo()

    def load_presets_combo(self):
        import json
        self.presets_combo.blockSignals(True)
        self.presets_combo.clear()
        self.presets_combo.addItem("Select Preset...")
        
        raw = get_setting("theme_presets", "[]")
        try:
            presets = json.loads(raw)
        except Exception:
            presets = []
            
        for preset in presets:
            if isinstance(preset, dict) and "name" in preset:
                self.presets_combo.addItem(preset["name"])
        self.presets_combo.blockSignals(False)

    def save_theme_preset(self):
        import json
        raw = get_setting("theme_presets", "[]")
        try:
            presets = json.loads(raw)
        except Exception:
            presets = []

        current_cards = {}
        for card in self.canvas.findChildren(AeroCard):
            current_cards[card.tile_id] = card.card_theme if card.card_theme else ""

        current_state = {
            "theme": self.theme_name,
            "opacity": round(self.ui_opacity, 2),
            "wallpaper": self.wallpaper_path,
            "cards": current_cards
        }

        for preset in presets:
            if not isinstance(preset, dict):
                continue
            if preset.get("theme") == current_state["theme"] and \
               abs(float(preset.get("opacity", 0.0)) - current_state["opacity"]) < 0.01 and \
               preset.get("wallpaper") == current_state["wallpaper"]:
                preset_cards = preset.get("cards", {})
                cards_match = True
                for tile_id, card_theme in current_cards.items():
                    if preset_cards.get(tile_id, "") != card_theme:
                        cards_match = False
                        break
                if cards_match:
                    preset_name = preset.get("name", "PRESET X").upper()
                    QMessageBox.information(
                        self, 
                        "Theme Presets", 
                        f"This theme is already saved as {preset_name}"
                    )
                    return

        preset_num = 1
        existing_nums = []
        for preset in presets:
            if isinstance(preset, dict) and "name" in preset:
                name = preset["name"]
                if name.startswith("Preset "):
                    try:
                        existing_nums.append(int(name[7:]))
                    except ValueError:
                        pass
        if existing_nums:
            preset_num = max(existing_nums) + 1

        new_name = f"Preset {preset_num}"
        current_state["name"] = new_name
        presets.append(current_state)

        set_setting("theme_presets", json.dumps(presets))
        self.load_presets_combo()
        self.presets_combo.setCurrentText(new_name)
        QMessageBox.information(self, "Theme Presets", f"Theme configuration saved as '{new_name}'")

    def load_selected_preset(self, preset_name):
        if not preset_name or preset_name == "Select Preset...":
            return
            
        import json
        raw = get_setting("theme_presets", "[]")
        try:
            presets = json.loads(raw)
        except Exception:
            return

        target_preset = None
        for preset in presets:
            if isinstance(preset, dict) and preset.get("name") == preset_name:
                target_preset = preset
                break

        if not target_preset:
            return

        self.theme_name = target_preset.get("theme", "Midnight Teal")
        self.ui_opacity = float(target_preset.get("opacity", 0.62))
        self.wallpaper_path = target_preset.get("wallpaper", "")

        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(int(self.ui_opacity * 100))
        self.opacity_slider.blockSignals(False)
        self.save_ui_opacity()

        self.theme_box.blockSignals(True)
        self.theme_box.setCurrentText(self.theme_name)
        self.theme_box.blockSignals(False)
        set_setting("theme_preset", self.theme_name)
        set_setting("wallpaper_path", self.wallpaper_path)

        preset_cards = target_preset.get("cards", {})
        for card in self.canvas.findChildren(AeroCard):
            theme_val = preset_cards.get(card.tile_id, "")
            card.card_theme = theme_val
            set_setting(f"tile_theme_{card.tile_id}", theme_val)

        self.set_app_style(reload_wallpaper=True)
        for card in self.canvas.findChildren(AeroCard):
            card.apply_card_theme()
        self.update_overall_progress()

    def toggle_wallpaper_sidebar(self):
        if not hasattr(self, "wallpaper_sidebar"):
            self.wallpaper_sidebar = WallpaperSidebar(self, self)
            QApplication.instance().installEventFilter(self)

        w = 280
        start_x = self.width()
        end_x = self.width() - w

        # If already visible, animate it out
        if self.wallpaper_sidebar.isVisible() and self.wallpaper_sidebar.x() < self.width():
            self.animate_sidebar_out()
        else:
            self.wallpaper_sidebar.setGeometry(start_x, 0, w, self.height())
            self.wallpaper_sidebar.show()
            self.wallpaper_sidebar.raise_()

            self.sidebar_anim = QPropertyAnimation(self.wallpaper_sidebar, b"geometry")
            self.sidebar_anim.setDuration(250)
            self.sidebar_anim.setStartValue(QRect(start_x, 0, w, self.height()))
            self.sidebar_anim.setEndValue(QRect(end_x, 0, w, self.height()))
            self.sidebar_anim.setEasingCurve(QEasingCurve.OutCubic)
            self.sidebar_anim.start()

    def animate_sidebar_out(self):
        if not hasattr(self, "wallpaper_sidebar") or not self.wallpaper_sidebar.isVisible():
            return

        w = self.wallpaper_sidebar.width()
        start_x = self.wallpaper_sidebar.x()
        end_x = self.width()

        self.sidebar_anim = QPropertyAnimation(self.wallpaper_sidebar, b"geometry")
        self.sidebar_anim.setDuration(200)
        self.sidebar_anim.setStartValue(QRect(start_x, 0, w, self.height()))
        self.sidebar_anim.setEndValue(QRect(end_x, 0, w, self.height()))
        self.sidebar_anim.setEasingCurve(QEasingCurve.InCubic)
        self.sidebar_anim.finished.connect(self.wallpaper_sidebar.hide)
        self.sidebar_anim.start()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            gp = event.globalPosition().toPoint()
            
            if hasattr(self, "wallpaper_sidebar") and self.wallpaper_sidebar.isVisible():
                local_sidebar_pos = self.wallpaper_sidebar.mapFromGlobal(gp)
                if not self.wallpaper_sidebar.rect().contains(local_sidebar_pos):
                    wp_btn = getattr(self, "wallpaper_btn", None)
                    click_on_btn = False
                    if wp_btn:
                        local_btn_pos = wp_btn.mapFromGlobal(gp)
                        if wp_btn.rect().contains(local_btn_pos):
                            click_on_btn = True
                    if not click_on_btn:
                        self.animate_sidebar_out()
                        

                        
        return super().eventFilter(obj, event)

    def clear_wallpaper(self):
        self.wallpaper_path = ""
        set_setting("wallpaper_path", "")
        self.update_wallpaper_media()

    def make_quote_area(self):
        card = AeroCard(self, "quotes")
        self.apply_shadow(card, blur=20, alpha=120)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 9, 10, 9)
        layout.setSpacing(10)

        self.quote_label = QLabel()
        self.quote_label.setObjectName("Quote")
        self.quote_label.setAlignment(Qt.AlignCenter)
        self.quote_label.setWordWrap(True)

        manage_btn = QPushButton("Quotes")
        manage_btn.clicked.connect(self.open_quote_manager)

        layout.addWidget(self.quote_label, 1)
        layout.addWidget(manage_btn)

        card.mousePressEvent = lambda event: self.advance_quote()
        return card

    def advance_quote(self, initial=False):
        quotes = get_quotes()
        if not quotes:
            self.quote_label.setText('"No quotes yet. Add one from Quotes."')
            return

        if initial:
            val = get_setting("quote_index", "-1")
            idx = int(val) if val else -1
            if idx < 0 or idx >= len(quotes):
                idx = random.randint(0, len(quotes) - 1)
            self.current_quote_id = quotes[idx][0]
            self.quote_label.setText(f'"{quotes[idx][1]}"')
            set_setting("quote_index", str(idx))
        else:
            options = [q for q in quotes if q[0] != self.current_quote_id]
            if not options:
                options = quotes
            chosen = random.choice(options)
            self.current_quote_id = chosen[0]
            self.quote_label.setText(f'"{chosen[1]}"')
            idx = quotes.index(chosen)
            set_setting("quote_index", str(idx))

    def open_quote_manager(self):
        dialog = QuoteManagerDialog(self)
        dialog.exec()

    def make_count_card(self, number, label):
        frame = QFrame()
        frame.setObjectName("CountTile")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        num = QLabel(number)
        num.setProperty("class", "CountNumber")
        num.setAlignment(Qt.AlignCenter)
        self.apply_shadow(num, blur=10, alpha=150)

        lbl = QLabel(label)
        lbl.setProperty("class", "CountLabel")
        lbl.setAlignment(Qt.AlignCenter)

        layout.addWidget(num)
        layout.addWidget(lbl)
        return {"frame": frame, "number": num, "label": lbl}

    def make_countdown_card(self):
        card = AeroCard(self, "countdown")
        self.apply_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel("Countdown")
        title.setProperty("class", "CardTitle")
        edit_button = QPushButton("Set Date")
        edit_button.clicked.connect(self.edit_countdown)
        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch()
        header.addWidget(edit_button)
        header.addSpacing(28)
        layout.addLayout(header)

        grid = QHBoxLayout()
        grid.setSpacing(10)

        self.days_label = FlipCardWidget("0", "Days", self)
        self.hours_label = FlipCardWidget("0", "Hours", self)
        self.minutes_label = FlipCardWidget("0", "Minutes", self)

        # Set minimum sizes to make sure they expand nicely and look proportionate
        self.days_label.setMinimumSize(80, 100)
        self.hours_label.setMinimumSize(80, 100)
        self.minutes_label.setMinimumSize(80, 100)

        grid.addWidget(self.days_label, 4)
        grid.addWidget(self.hours_label, 3)
        grid.addWidget(self.minutes_label, 3)
        layout.addLayout(grid)

        self.target_label = QLabel("")
        self.target_label.setAlignment(Qt.AlignCenter)
        self.target_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.target_label)
        return card


    def make_task_card(self, title_text, category, placeholder):
        card = AeroCard(self, category)
        self.apply_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel(title_text)
        title.setProperty("class", "CardTitle")
        counter = QLabel("0/0")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(counter)
        header.addSpacing(28)

        input_row = QHBoxLayout()
        input_box = QLineEdit()
        input_box.setPlaceholderText(placeholder)

        add_btn = QPushButton("+")
        add_btn.setObjectName("AddButton")
        add_btn.clicked.connect(lambda: self.add_task_from_input(category))

        input_row.addWidget(input_box)
        input_row.addWidget(add_btn)

        list_layout = QVBoxLayout()
        list_layout.setAlignment(Qt.AlignTop)
        list_layout.setSpacing(4)

        layout.addLayout(header)
        layout.addLayout(input_row)
        layout.addLayout(list_layout)
        layout.addStretch()

        self.daily_widgets = {
            "frame": card,
            "counter": counter,
            "input": input_box,
            "list": list_layout
        }
        return self.daily_widgets

    def make_progress_card(self):
        card = AeroCard(self, "progress")
        self.apply_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Total Progress")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        layout.addStretch()

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        self.subject_breakdown_layout = QVBoxLayout()
        self.subject_breakdown_layout.setSpacing(14)
        content_layout.addLayout(self.subject_breakdown_layout, 1)

        self.total_progress_label = QLabel("0%")
        self.total_progress_label.setStyleSheet("font-size: 72px; font-weight: bold; color: white; padding-right: 6px;")
        self.total_progress_label.setAlignment(Qt.AlignCenter)
        self.total_progress_label.setMinimumWidth(130)
        content_layout.addWidget(self.total_progress_label, 0, Qt.AlignVCenter | Qt.AlignRight)

        layout.addLayout(content_layout)
        layout.addStretch()
        return card


    def make_extras_card(self):
        card = AeroCard(self, "extras")
        self.apply_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel("Notes")
        title.setProperty("class", "CardTitle")
        
        self.notes_target_label = QLabel("No Selection")
        self.notes_target_label.setStyleSheet("color: rgba(255, 255, 255, 140); font-weight: bold; font-size: 11px;")
        self.notes_target_label.setWordWrap(True)

        self.notes_text_edit = QPlainTextEdit()
        self.notes_text_edit.setPlaceholderText("Select a subject tab or click a checklist row to edit notes...")
        self.notes_text_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: rgba(0, 0, 0, 45);
                border: 1px solid rgba(255, 255, 255, 22);
                border-radius: 6px;
                color: #e5e7eb;
                padding: 4px;
            }
        """)

        save_btn_layout = QHBoxLayout()
        save_btn_layout.setContentsMargins(0, 0, 0, 0)
        save_btn_layout.addStretch()
        
        self.save_notes_btn = QPushButton("Save Notes")
        self.save_notes_btn.setObjectName("AddButton")
        self.save_notes_btn.clicked.connect(self.save_current_notes)
        save_btn_layout.addWidget(self.save_notes_btn)

        layout.addWidget(title)
        layout.addWidget(self.notes_target_label)
        layout.addWidget(self.notes_text_edit, 1)
        layout.addLayout(save_btn_layout)

        self.current_notes_key = None
        return card

    def open_team_maker(self):
        if getattr(self, "team_maker_dialog", None) and self.team_maker_dialog.isVisible():
            self.team_maker_dialog.raise_()
            self.team_maker_dialog.activateWindow()
            return
        self.team_maker_dialog = TeamMakerDialog(self)
        self.team_maker_dialog.show()
        self.team_maker_dialog.raise_()
        self.team_maker_dialog.activateWindow()

    def update_overall_progress(self):
        if not hasattr(self, "total_progress_label"):
            return

        total_done = 0
        total_boxes = 0

        while self.subject_breakdown_layout.count():
            item = self.subject_breakdown_layout.takeAt(0)
            child = item.widget()
            if child:
                child.deleteLater()

        for subject in get_subjects():
            percent, done, total = get_subject_progress(subject)
            total_done += done
            total_boxes += total

            row = QFrame()
            row.setObjectName("CountTile")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 10, 12, 10)
            name = QLabel(subject)
            name.setMinimumHeight(self.app_font_size + 16)
            name.setStyleSheet("background: transparent; color: white; font-weight: bold; font-size: 13px;")
            value = QLabel(f"{percent}%")
            value.setMinimumHeight(self.app_font_size + 16)
            value.setStyleSheet("background: transparent; color: white; font-weight: bold; font-size: 13px;")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(name, 1)
            row_layout.addWidget(value)
            self.subject_breakdown_layout.addWidget(row)

        overall = int((total_done / total_boxes) * 100) if total_boxes else 0
        self.total_progress_label.setText(f"{overall}%")

    def make_focus_hub(self):
        card = AeroCard(self, "focus")
        self.apply_shadow(card)

        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(6)

        title = QLabel("Focus Hub")
        title.setProperty("class", "CardTitle")
        title.setMinimumHeight(self.app_font_size + 10)
        main_layout.addWidget(title)

        split_layout = QHBoxLayout()
        split_layout.setSpacing(8)

        # LEFT COLUMN (Start Button & Focus Elevator Button)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)
        self.start_btn = ElevatorControlButton("Start", "start", self)
        self.start_btn.clicked.connect(self.start_focus_hub_timer)

        self.focus_btn = ElevatorButton("FOCUS", self)
        self.focus_btn.clicked.connect(self.select_focus_mode)

        left_layout.addWidget(self.start_btn)
        left_layout.addWidget(self.focus_btn, 1)

        # CENTER COLUMN (Up Arrow, Timer stage, Down Arrow)
        center_layout = QVBoxLayout()
        center_layout.setSpacing(4)
        
        self.up_arrow = TimerArrowButton("up", self)
        self.up_arrow.clicked.connect(lambda: self.adjust_timer(1))

        center_box = QFrame()
        center_box.setObjectName("TimerCenterBox")
        center_box.setStyleSheet("background: transparent; border: none;")
        center_box_layout = QVBoxLayout(center_box)
        center_box_layout.setContentsMargins(0, 0, 0, 0)
        center_box_layout.setSpacing(4)

        self.focus_mode_label = QLabel("READY")
        self.focus_mode_label.setAlignment(Qt.AlignCenter)
        self.focus_mode_label.setStyleSheet(f"font-size: {self.app_font_size + 8}px; font-weight: bold; color: rgba(255,255,255,220); text-transform: uppercase; letter-spacing: 1px;")

        # Fibonacci Display
        self.fib_container = ClickableWidget(self.enter_timer_edit_mode, self)
        self.fib_container.setStyleSheet("background: transparent; border: none;")
        fib_layout = QHBoxLayout(self.fib_container)
        fib_layout.setContentsMargins(0, 0, 0, 0)
        fib_layout.setSpacing(6)
        fib_layout.setAlignment(Qt.AlignCenter)

        self.hours_lbl = QLabel("00")
        self.hours_lbl.setAlignment(Qt.AlignCenter)
        self.hours_lbl.setStyleSheet(f"font-size: {self.app_font_size + 30}px; font-weight: bold; color: white;")

        self.right_col = QWidget()
        self.right_col.setStyleSheet("background: transparent; border: none;")
        self.right_col_layout = QVBoxLayout(self.right_col)
        self.right_col_layout.setContentsMargins(0, 0, 0, 0)
        self.right_col_layout.setSpacing(2)

        self.minutes_lbl = QLabel("25m")
        self.minutes_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.minutes_lbl.setStyleSheet(f"font-size: {self.app_font_size + 12}px; font-weight: bold; color: rgba(255,255,255,220);")

        self.seconds_lbl = QLabel("00s")
        self.seconds_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.seconds_lbl.setStyleSheet(f"font-size: {self.app_font_size + 2}px; font-weight: bold; color: rgba(255,255,255,160);")

        self.right_col_layout.addWidget(self.minutes_lbl)
        self.right_col_layout.addWidget(self.seconds_lbl)

        fib_layout.addWidget(self.hours_lbl, 0, Qt.AlignCenter)
        fib_layout.addWidget(self.right_col, 0, Qt.AlignCenter)

        # Single input field for editing
        self.focus_timer_label = TimerLineEdit(self.on_timer_edited, self)
        self.focus_timer_label.setFont(QFont(self.app_font_family, self.app_font_size + 24, QFont.Bold))
        self.focus_timer_label.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: white;
                font-family: '{self.app_font_family}';
                font-size: {self.app_font_size + 24}px;
                font-weight: bold;
                padding: 4px;
                margin: 0px;
                qproperty-alignment: AlignCenter;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(249, 115, 22, 120);
                border-radius: 6px;
                background: rgba(15, 23, 42, 120);
            }}
        """)
        self.focus_timer_label.hide() # Hidden by default, only shown when editing

        center_box_layout.addStretch(1)
        center_box_layout.addWidget(self.focus_mode_label)
        center_box_layout.addWidget(self.fib_container)
        center_box_layout.addWidget(self.focus_timer_label)
        center_box_layout.addStretch(1)

        self.down_arrow = TimerArrowButton("down", self)
        self.down_arrow.clicked.connect(lambda: self.adjust_timer(-1))

        center_layout.addWidget(self.up_arrow, 0, Qt.AlignCenter)
        center_layout.addWidget(center_box, 1)
        center_layout.addWidget(self.down_arrow, 0, Qt.AlignCenter)

        # RIGHT COLUMN (Reset Button & Break Elevator Button)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(6)
        self.reset_btn = ElevatorControlButton("Reset", "reset", self)
        self.reset_btn.clicked.connect(self.reset_focus_hub)

        self.break_btn = ElevatorButton("BREAK", self)
        self.break_btn.clicked.connect(self.select_break_mode)

        right_layout.addWidget(self.reset_btn)
        right_layout.addWidget(self.break_btn, 1)

        split_layout.addLayout(left_layout, 33)
        split_layout.addLayout(center_layout, 34)
        split_layout.addLayout(right_layout, 33)

        # BOTTOM ROW (Overall cumulative stats)
        info_row = QHBoxLayout()
        self.sessions_label = QLabel()
        self.sessions_label.setMinimumHeight(self.app_font_size + 8)
        self.sessions_label.setStyleSheet("color: rgba(255,255,255,180); font-weight: 500;")
        
        self.study_time_label = QLabel()
        self.study_time_label.setMinimumHeight(self.app_font_size + 8)
        self.study_time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.study_time_label.setStyleSheet("color: rgba(255,255,255,180); font-weight: 500;")

        info_row.addWidget(self.sessions_label)
        info_row.addStretch()
        info_row.addWidget(self.study_time_label)

        main_layout.addLayout(split_layout, 1)
        main_layout.addLayout(info_row, 0)

        return card

    def make_syllabus_card(self):
        card = AeroCard(self, "syllabus")
        card.setMinimumHeight(520)
        self.apply_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel("Syllabus Checklist")
        title.setProperty("class", "CardTitle")

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Tabs placeholder
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        return card

    def build_subject_tabs(self):
        tabs = QTabWidget()
        self.subjects = get_subjects() or ["Physics", "Chemistry", "Biology"]

        for subject in self.subjects:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.setContentsMargins(10, 10, 10, 10)
            tab_layout.setSpacing(8)

            progress_label = QLabel("Progress: 0%")
            progress_label.setAlignment(Qt.AlignRight)
            self.subject_progress_labels[subject] = progress_label

            input_row = QHBoxLayout()
            topic_input = QLineEdit()
            topic_input.setPlaceholderText("Module / Chapter / Topic")

            add_btn = QPushButton("+ Add")
            add_btn.setObjectName("AddButton")
            add_btn.clicked.connect(
                lambda checked=False, s=subject, ti=topic_input:
                self.add_syllabus_from_input(s, ti)
            )

            input_row.addWidget(topic_input)
            input_row.addWidget(add_btn)

            table = DragDropTableWidget()
            header = ChecklistHeaderView(table)
            header.setObjectName("ChecklistHeader")
            table.setHorizontalHeader(header)
            table.configure(self, subject)
            table.setItemDelegate(RowProgressDelegate(table))
            table.setMouseTracking(True)
            table.viewport().setMouseTracking(True)
            table.verticalHeader().setVisible(False)
            table.setAlternatingRowColors(True)
            table.setShowGrid(False)
            table.setWordWrap(True)

            header.setContextMenuPolicy(Qt.CustomContextMenu)
            header.customContextMenuRequested.connect(
                lambda pos, t=table, s=subject: self.show_column_context_menu(pos, t, s)
            )
            
            table.itemSelectionChanged.connect(
                lambda t=table, s=subject: self.handle_table_selection_changed(t, s)
            )

            self.subject_tables[subject] = table

            tab_layout.addWidget(progress_label)
            tab_layout.addLayout(input_row)
            tab_layout.addWidget(table)
            tabs.addTab(tab, subject)

        tabs.addTab(QWidget(), "+")
        tabs.currentChanged.connect(self.handle_tab_change)

        tabs.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        tabs.tabBar().customContextMenuRequested.connect(self.show_subject_tab_context_menu)

        return tabs

    def add_syllabus_from_input(self, subject, topic_input):
        text = topic_input.text().strip()
        if not text:
            QMessageBox.warning(self, "Missing Info", "Enter a module/chapter/topic.")
            return

        add_syllabus_item(subject, "", text)
        topic_input.clear()
        self.reload_subject(subject)

    def add_subject_dialog(self):
        subject, ok = QInputDialog.getText(
            self,
            "Add Subject / Course",
            "Subject or course name:",
        )
        subject = subject.strip() if ok else ""
        if not subject:
            return
        if subject not in self.subjects:
            add_subject(subject)
            self.rebuild_syllabus_tabs()

    def rebuild_syllabus_tabs(self):
        # Save active tab index
        current_tab_idx = self.tabs.currentIndex() if hasattr(self, "tabs") and self.tabs else 0

        self.subject_tables.clear()
        self.subject_progress_labels.clear()
        index = self.syllabus_card.layout().indexOf(self.tabs)
        self.syllabus_card.layout().takeAt(index)
        self.tabs.deleteLater()
        self.tabs = self.build_subject_tabs()
        self.syllabus_card.layout().addWidget(self.tabs)

        # Restore active tab index (ensuring we don't land on the '+' tab at the end)
        if current_tab_idx >= 0 and current_tab_idx < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(current_tab_idx)

        self.reload_all_subjects()

    def handle_tab_change(self, index):
        if index == len(self.subjects):
            base_name = "New Subject"
            name = base_name
            counter = 1
            while name in self.subjects:
                counter += 1
                name = f"{base_name} {counter}"
            add_subject(name)
            self.rebuild_syllabus_tabs()
            if name in self.subjects:
                new_idx = self.subjects.index(name)
                self.tabs.setCurrentIndex(new_idx)
                self.edit_subject_tab_inline(new_idx)

    def show_subject_tab_context_menu(self, pos):
        tab_bar = self.tabs.tabBar()
        tab_index = tab_bar.tabAt(pos)
        if tab_index < 0 or tab_index >= len(self.subjects):
            return

        subject = self.subjects[tab_index]
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(15, 23, 42, 230);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                color: #e5e7eb;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 30);
                border-radius: 4px;
            }
        """)

        rename_action = menu.addAction("Rename Subject")
        delete_action = menu.addAction("Delete Subject")
        menu.addSeparator()
        move_left_action = menu.addAction("Move Left")
        move_right_action = menu.addAction("Move Right")

        if tab_index == 0:
            move_left_action.setEnabled(False)
        if tab_index == len(self.subjects) - 1:
            move_right_action.setEnabled(False)

        action = menu.exec(tab_bar.mapToGlobal(pos))
        if action == rename_action:
            self.edit_subject_tab_inline(tab_index)
        elif action == delete_action:
            confirm = QMessageBox.question(
                self, "Delete Subject",
                f"Are you sure you want to delete subject '{subject}'? This will delete all chapters/topics and progress associated with it."
            )
            if confirm == QMessageBox.Yes:
                delete_subject(subject)
                self.rebuild_syllabus_tabs()
        elif action == move_left_action:
            self.subjects[tab_index], self.subjects[tab_index - 1] = self.subjects[tab_index - 1], self.subjects[tab_index]
            reorder_subjects(self.subjects)
            self.rebuild_syllabus_tabs()
            self.tabs.setCurrentIndex(tab_index - 1)
        elif action == move_right_action:
            self.subjects[tab_index], self.subjects[tab_index + 1] = self.subjects[tab_index + 1], self.subjects[tab_index]
            reorder_subjects(self.subjects)
            self.rebuild_syllabus_tabs()
            self.tabs.setCurrentIndex(tab_index + 1)

    def edit_subject_tab_inline(self, tab_index):
        tab_bar = self.tabs.tabBar()
        rect = tab_bar.tabRect(tab_index)
        
        line_edit = QLineEdit(tab_bar)
        line_edit.setText(self.subjects[tab_index])
        line_edit.setGeometry(rect)
        line_edit.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 240);
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 4px;
                color: white;
                font-weight: bold;
                padding: 0px 4px;
            }
        """)
        line_edit.show()
        line_edit.setFocus()
        line_edit.selectAll()
        
        self._editing_tab_index = tab_index
        self._tab_editor = line_edit
        line_edit.editingFinished.connect(self.finish_subject_tab_edit)
        
    def finish_subject_tab_edit(self):
        if not hasattr(self, "_tab_editor") or not self._tab_editor:
            return
        editor = self._tab_editor
        tab_index = self._editing_tab_index
        self._tab_editor = None
        
        new_name = editor.text().strip()
        editor.deleteLater()
        
        if tab_index < len(self.subjects):
            old_name = self.subjects[tab_index]
            if new_name and new_name != old_name:
                rename_subject(old_name, new_name)
        self.rebuild_syllabus_tabs()

    def handle_header_click(self, col, table):
        categories = get_categories(include_hidden=False)
        plus_idx = len(categories) + 1
        if col == plus_idx:
            base_name = "New Column"
            name = base_name
            counter = 1
            existing = [cat[0] for cat in get_categories(include_hidden=True)]
            while name in existing:
                counter += 1
                name = f"{base_name} {counter}"
            add_category(name, 1)
            self.rebuild_syllabus_tabs()
            
            new_col_idx = len(categories) + 1
            self.edit_column_header_inline(table, new_col_idx, name)

    def edit_column_header_inline(self, table, col_idx, cat_name):
        header = table.horizontalHeader()
        rect = QRect(header.sectionPosition(col_idx), 0, header.sectionSize(col_idx), header.height())
        
        line_edit = QLineEdit(header)
        line_edit.setText(cat_name)
        line_edit.setGeometry(rect)
        line_edit.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 240);
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 4px;
                color: white;
                font-weight: bold;
                padding: 0px 4px;
            }
        """)
        line_edit.show()
        line_edit.setFocus()
        line_edit.selectAll()
        
        self._editing_col_idx = col_idx
        self._editing_cat_name = cat_name
        self._col_editor = line_edit
        self._col_editor_table = table
        
        line_edit.editingFinished.connect(self.finish_column_header_edit)
        
    def finish_column_header_edit(self):
        if not hasattr(self, "_col_editor") or not self._col_editor:
            return
        editor = self._col_editor
        old_name = self._editing_cat_name
        self._col_editor = None
        
        new_name = editor.text().strip()
        editor.deleteLater()
        
        if new_name and new_name != old_name:
            update_category(old_name, new_name)
        self.rebuild_syllabus_tabs()

    def show_column_context_menu(self, pos, table, subject):
        col_idx = table.horizontalHeader().logicalIndexAt(pos)
        categories = get_categories(include_hidden=False)

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(15, 23, 42, 230);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                color: #e5e7eb;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 30);
                border-radius: 4px;
            }
        """)

        add_col_action = menu.addAction("Add New Column")
        
        progress_action = None
        edit_action = None
        hide_action = None
        remove_action = None
        
        if 1 <= col_idx <= len(categories):
            cat_name, include_in_progress, display_order, is_hidden = categories[col_idx - 1]
            menu.addSeparator()
            if include_in_progress:
                progress_action = menu.addAction("Ignore from Progress")
            else:
                progress_action = menu.addAction("Consider for Progress")

            edit_action = menu.addAction("Edit Name")
            hide_action = menu.addAction("Hide Column")
            remove_action = menu.addAction("Remove Column")
        else:
            cat_name = None

        all_cats = get_categories(include_hidden=True)
        hidden_cats = [cat for cat in all_cats if cat[3]]
        if hidden_cats:
            menu.addSeparator()
            show_submenu = menu.addMenu("Show Hidden Columns")
            for cat in hidden_cats:
                act = show_submenu.addAction(cat[0])
                act.triggered.connect(lambda checked=False, name=cat[0]: self.unhide_column(name))

        action = menu.exec(table.horizontalHeader().mapToGlobal(pos))
        if action == add_col_action:
            self.add_new_category_column(table)
        elif action == progress_action:
            new_inc = 0 if include_in_progress else 1
            update_category(cat_name, cat_name, include_in_progress=new_inc)
            self.rebuild_syllabus_tabs()
            self.update_overall_progress()
        elif action == edit_action:
            self.edit_column_header_inline(table, col_idx, cat_name)
        elif action == hide_action:
            update_category(cat_name, cat_name, is_hidden=1)
            self.rebuild_syllabus_tabs()
            self.update_overall_progress()
        elif action == remove_action:
            delete_category(cat_name)
            self.rebuild_syllabus_tabs()
            self.update_overall_progress()

    def add_new_category_column(self, table):
        categories = get_categories(include_hidden=False)
        base_name = "New Column"
        name = base_name
        counter = 1
        existing = [cat[0] for cat in get_categories(include_hidden=True)]
        while name in existing:
            counter += 1
            name = f"{base_name} {counter}"
        add_category(name, 1)
        self.rebuild_syllabus_tabs()
        
        current_subject = self.subjects[self.tabs.currentIndex()]
        rebuilt_table = self.subject_tables.get(current_subject)
        if rebuilt_table:
            new_col_idx = len(get_categories(include_hidden=False))
            self.edit_column_header_inline(rebuilt_table, new_col_idx, name)

    def unhide_column(self, name):
        update_category(name, name, is_hidden=0)
        self.rebuild_syllabus_tabs()
        self.update_overall_progress()

    def reload_all_subjects(self):
        for subject in self.subjects:
            self.reload_subject(subject)

    def reload_subject(self, subject):
        table = self.subject_tables.get(subject)
        if not table:
            return

        # Save current scroll positions
        v_scroll = table.verticalScrollBar().value()
        h_scroll = table.horizontalScrollBar().value()

        categories = get_categories(include_hidden=False)
        rows = get_syllabus_items_dynamic(subject)

        table.setRowCount(0)
        table.setColumnCount(1 + len(categories) + 1) # Topic, Categories, Actions

        headers = ["Module / Chapter / Topic"] + ["" for _ in categories] + [""]
        table.setHorizontalHeaderLabels(headers)

        # Topic column stretches
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # Category columns are fixed at 64px width for perfect uniformity
        for col in range(1, len(categories) + 1):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Fixed)
            table.setColumnWidth(col, 64)
        # Actions column at the far right is set to a fixed width of 75px
        actions_col = len(categories) + 1
        table.horizontalHeader().setSectionResizeMode(actions_col, QHeaderView.Fixed)
        table.setColumnWidth(actions_col, 75)

        for row_index, row_data in enumerate(rows):
            item_id, module, topic, important, display_order, completions = row_data

            table.insertRow(row_index)
            table.setRowHeight(row_index, max(46, self.app_font_size + 32))

            # Weight calculations matching get_subject_progress
            active_cats = [cat[0] for cat in categories if cat[1] == 1]
            row_completed = 0.0
            for cat_name in active_cats:
                status = completions.get(cat_name, 0)
                if status == 1:
                    row_completed += 1.0
                elif status == 2:
                    row_completed += 0.5
            row_total = len(active_cats)
            percent = int((row_completed / row_total) * 100) if row_total > 0 else 0

            # Set items
            id_item = QTableWidgetItem()
            id_item.setData(Qt.UserRole, item_id)
            id_item.setData(Qt.UserRole + 1, percent)
            table.setItem(row_index, 0, id_item)

            # Topic cell
            table.setCellWidget(
                row_index,
                0,
                TopicProgressWidget(self, table, row_index, item_id, subject, topic, important, percent),
            )

            # Category cells
            for col_idx, (cat_name, include, _, _) in enumerate(categories, 1):
                status = completions.get(cat_name, 0)
                button = StatusIconButton(self, table, row_index, item_id, subject, cat_name, status)

                holder = HoverRowTrackerWidget(table, row_index)
                holder_layout = QHBoxLayout(holder)
                holder_layout.setContentsMargins(0, 0, 0, 0)
                holder_layout.setAlignment(Qt.AlignCenter)
                holder_layout.addWidget(button)
                table.setCellWidget(row_index, col_idx, holder)

            # Actions column cell
            actions_widget = HoverActionsWidget(self, table, row_index, item_id, subject, topic)
            table.setCellWidget(row_index, len(categories) + 1, actions_widget)

        self.update_subject_progress(subject)

        # Restore scroll positions deferredly
        QTimer.singleShot(0, lambda: table.verticalScrollBar().setValue(v_scroll))
        QTimer.singleShot(0, lambda: table.horizontalScrollBar().setValue(h_scroll))

    def add_topic_cell(self, table, row, item_id, subject, topic, important, percent):
        table.setCellWidget(
            row,
            0,
            TopicProgressWidget(self, table, row, item_id, subject, topic, important, percent),
        )

    def update_subject_progress(self, subject):
        percent, done, total = get_subject_progress(subject)
        self.subject_progress_labels[subject].setText(
            f"Progress: {percent}%  ({done:g}/{total})"
        )
        self.update_overall_progress()

    def update_row_progress(self, subject, row):
        table = self.subject_tables.get(subject)
        if not table:
            return

        categories = get_categories(include_hidden=False)
        active_cats = [cat[0] for cat in categories if cat[1] == 1]
        
        row_completed = 0.0
        for col_idx, (cat_name, include, _, _) in enumerate(categories, 1):
            if cat_name in active_cats:
                widget = table.cellWidget(row, col_idx)
                if widget:
                    button = widget.findChild(StatusIconButton)
                    if button:
                        status = button.state
                        if status == 1:
                            row_completed += 1.0
                        elif status == 2:
                            row_completed += 0.5

        row_total = len(active_cats)
        percent = int((row_completed / row_total) * 100) if row_total > 0 else 0

        # Update percent in the Item
        id_item = table.item(row, 0)
        if id_item:
            id_item.setData(Qt.UserRole + 1, percent)

        # Update TopicProgressWidget label
        topic_widget = table.cellWidget(row, 0)
        if isinstance(topic_widget, TopicProgressWidget):
            topic_widget.percent = percent
            topic_widget.percent_label.setText(f"{percent}%")

        table.viewport().update()

    def edit_topic_inline_from_hover(self, item_id, subject):
        table = self.subject_tables.get(subject)
        if not table:
            return
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.data(Qt.UserRole) == item_id:
                widget = table.cellWidget(row, 0)
                if isinstance(widget, TopicProgressWidget):
                    widget.start_rename()
                    break

    def remove_syllabus_item(self, item_id, subject):
        delete_syllabus_item(item_id)
        self.reload_subject(subject)

    def move_topic_item(self, item_id, direction, subject):
        move_syllabus_item(item_id, direction)
        self.reload_subject(subject)

    def enter_timer_edit_mode(self):
        if self.active_timer_mode is not None:
            return
        self.fib_container.hide()
        self.focus_timer_label.show()
        self.focus_timer_label.setFocus()
        self.focus_timer_label.selectAll()

    def select_focus_mode(self):
        if self.active_timer_mode is not None:
            return
        self.selected_mode = "focus"
        self.refresh_focus_hub()

    def select_break_mode(self):
        if self.active_timer_mode is not None:
            return
        self.selected_mode = "break"
        self.refresh_focus_hub()

    def adjust_timer(self, delta_minutes):
        if self.active_timer_mode is not None:
            return
        if self.selected_mode == "focus":
            minutes = self.focus_seconds_left // 60 + delta_minutes
            minutes = max(1, min(180, minutes))
            self.focus_seconds_left = minutes * 60
            set_setting("focus_minutes", str(minutes))
        else:
            minutes = self.break_seconds_left // 60 + delta_minutes
            minutes = max(1, min(60, minutes))
            self.break_seconds_left = minutes * 60
            set_setting("break_minutes", str(minutes))
        self.refresh_focus_hub()

    def on_timer_edited(self, seconds):
        self.focus_timer_label.hide()
        self.fib_container.show()
        
        if self.active_timer_mode is not None:
            return
        if seconds == -1:
            self.refresh_focus_hub()
            return
            
        if self.selected_mode == "focus":
            self.focus_seconds_left = seconds
            set_setting("focus_minutes", str(seconds // 60))
        else:
            self.break_seconds_left = seconds
            set_setting("break_minutes", str(seconds // 60))
        self.refresh_focus_hub()

    def start_focus(self):
        self.select_focus_mode()
        self.start_focus_hub_timer()

    def start_break(self):
        self.select_break_mode()
        self.start_focus_hub_timer()

    def start_focus_hub_timer(self):
        if self.active_timer_mode is not None:
            return
        self.active_timer_mode = self.selected_mode
        if self.active_timer_mode == "focus":
            self.focus_mode_label.setText("FOCUS RUNNING")
        else:
            self.focus_mode_label.setText("BREAK RUNNING")
            self.play_interaction_sound("plankton")
        self.focus_timer.start(1000)
        self.refresh_focus_hub()

    def play_tired_sound(self):
        self.play_interaction_sound("plankton")

    def find_tired_sound(self):
        search_dirs = [
            Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent,
            Path.cwd(),
        ]
        for folder in search_dirs:
            for name in ("plankton.mp3", "planton_meme.wav", "plankton_meme.wav", "tired.wav"):
                candidate = folder / name
                if candidate.exists():
                    return candidate
        return None

    def reset_focus_hub(self):
        self.focus_timer.stop()
        self.active_timer_mode = None
        self.focus_seconds_left = int(get_setting("focus_minutes", "25")) * 60
        self.break_seconds_left = int(get_setting("break_minutes", "5")) * 60
        self.focus_mode_label.setText("READY")
        self.refresh_focus_hub()

    def tick_focus_hub(self):
        if self.active_timer_mode == "focus":
            self.focus_seconds_left -= 1
            current_total = int(get_setting("study_seconds_total", "0"))
            set_setting("study_seconds_total", current_total + 1)
            if self.focus_seconds_left <= 0:
                self.focus_timer.stop()
                sessions = int(get_setting("sessions_completed", "0")) + 1
                set_setting("sessions_completed", sessions)
                QApplication.beep()
                QMessageBox.information(self, "Done", "Focus session completed.")
                self.reset_focus_hub()
        elif self.active_timer_mode == "break":
            self.break_seconds_left -= 1
            current_break_total = int(get_setting("break_seconds_total", "0"))
            set_setting("break_seconds_total", current_break_total + 1)
            if self.break_seconds_left <= 0:
                self.focus_timer.stop()
                break_sessions = int(get_setting("break_sessions_completed", "0")) + 1
                set_setting("break_sessions_completed", break_sessions)
                QApplication.beep()
                QMessageBox.information(self, "Done", "Break completed.")
                self.reset_focus_hub()
        self.refresh_focus_hub()

    def refresh_focus_hub(self):
        current_mode = self.active_timer_mode if self.active_timer_mode is not None else self.selected_mode
        
        seconds = self.break_seconds_left if current_mode == "break" else self.focus_seconds_left
        h = max(0, seconds) // 3600
        m = (max(0, seconds) % 3600) // 60
        s = max(0, seconds) % 60
        
        self.hours_lbl.setText(f"{h:02d}")
        self.minutes_lbl.setText(f"{m:02d}m")
        self.seconds_lbl.setText(f"{s:02d}s")
        
        self.focus_timer_label.blockSignals(True)
        if h > 0:
            self.focus_timer_label.setText(f"{h:02d}:{m:02d}:{s:02d}")
        else:
            self.focus_timer_label.setText(f"{m:02d}:{s:02d}")
        self.focus_timer_label.blockSignals(False)
        
        is_editable = (self.active_timer_mode is None)
        
        if self.active_timer_mode is not None:
            self.focus_btn.set_active(self.active_timer_mode == "focus")
            self.break_btn.set_active(self.active_timer_mode == "break")
            self.focus_mode_label.setText("FOCUS RUNNING" if self.active_timer_mode == "focus" else "BREAK RUNNING")
        else:
            self.focus_btn.set_active(self.selected_mode == "focus")
            self.break_btn.set_active(self.selected_mode == "break")
            self.focus_mode_label.setText("READY")
            
        self.up_arrow.setEnabled(is_editable)
        self.down_arrow.setEnabled(is_editable)
        
        focus_seconds = int(get_setting("study_seconds_total", "0"))
        focus_minutes = focus_seconds // 60
        focus_sessions = int(get_setting("sessions_completed", "0"))
        self.focus_btn.set_stats(f"{focus_minutes}m / {focus_sessions} sess")
        
        break_seconds = int(get_setting("break_seconds_total", "0"))
        break_minutes = break_seconds // 60
        break_sessions = int(get_setting("break_sessions_completed", "0"))
        self.break_btn.set_stats(f"{break_minutes}m / {break_sessions} sess")
        
        sessions = int(get_setting("sessions_completed", "0"))
        total_seconds = int(get_setting("study_seconds_total", "0"))
        total_minutes = total_seconds // 60
        self.sessions_label.setText(f"Sessions completed: {sessions}")
        self.study_time_label.setText(f"Total study time: {total_minutes} min")

    def save_focus_settings(self):
        pass

    def rebuild_countdown_card(self):
        geom = self.countdown_card.geometry()
        self.countdown_card.hide()
        self.countdown_card.deleteLater()
        self.countdown_card = self.make_countdown_card()
        self.countdown_card.setGeometry(geom)
        self.countdown_card.show()
        self.update_countdown()

    def show_first_run_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Welcome to PrepMate!")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: rgba(15, 23, 42, 245);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
            }
            QLabel {
                color: #e5e7eb;
                font-size: 13px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                color: white;
                padding: 6px;
                font-size: 13px;
            }
            QRadioButton {
                color: #e5e7eb;
                font-size: 12px;
                spacing: 8px;
            }
            QPushButton {
                background-color: rgba(34, 197, 94, 150);
                color: white;
                font-weight: bold;
                border: 1px solid rgba(255,255,255,30);
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: rgba(34, 197, 94, 220);
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)
        
        layout.addWidget(QLabel("Enter your tracked Goal/Mission (e.g. NEET, JEE):"))
        mission_input = QLineEdit("NEET")
        layout.addWidget(mission_input)
        
        layout.addWidget(QLabel("Choose UI Mode (Can be changed in settings later):"))
        
        from PySide6.QtWidgets import QRadioButton
        aes_radio = QRadioButton("Aesthetic Mode (Highly animated, backlit glow, flip-cards)")
        aes_radio.setChecked(True)
        lite_radio = QRadioButton("Lite Mode (Fast response, minimal animations, static timer)")
        
        layout.addWidget(aes_radio)
        layout.addWidget(lite_radio)
        
        save_btn = QPushButton("Save & Begin")
        save_btn.clicked.connect(dialog.accept)
        layout.addWidget(save_btn)
        
        if dialog.exec() == QDialog.Accepted:
            m_text = mission_input.text().strip() or "NEET"
            mode = "aesthetic" if aes_radio.isChecked() else "lite"
            
            import re
            safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", m_text)
            if not safe_name:
                safe_name = "NEET"
                m_text = "NEET"
            
            set_active_database(safe_name)
            init_db()
            
            set_setting("exam_name", m_text)
            set_setting("ui_mode", mode)
            set_setting("first_run_completed", "1")
            set_master_setting("first_run_completed", "1")
            set_master_setting("active_mission", safe_name)
            
            self.ui_mode = mode
        else:
            set_setting("first_run_completed", "1")
            set_master_setting("first_run_completed", "1")

    def show_reset_options_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Reset PrepMate")
        dialog.setMinimumWidth(380)
        dialog.setStyleSheet("""
            QDialog {
                background-color: rgba(15, 23, 42, 245);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
            }
            QLabel {
                color: #e5e7eb;
                font-size: 13px;
            }
            QPushButton {
                color: white;
                font-weight: bold;
                border: 1px solid rgba(255,255,255,30);
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton#ResetProgressBtn {
                background-color: rgba(234, 179, 8, 140);
            }
            QPushButton#ResetProgressBtn:hover {
                background-color: rgba(234, 179, 8, 200);
            }
            QPushButton#ResetAppBtn {
                background-color: rgba(239, 68, 68, 140);
            }
            QPushButton#ResetAppBtn:hover {
                background-color: rgba(239, 68, 68, 200);
            }
            QPushButton#CancelBtn {
                background-color: rgba(255, 255, 255, 20);
            }
            QPushButton#CancelBtn:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel(
            "Choose a reset option:\n\n"
            "1. RESET PROGRESS: Resets your study progress (checkmarks, notes, "
            "timer metrics, countdown target) but retains your subject tabs and checklist items.\n\n"
            "2. RESET APP: Wipes all data and returns PrepMate to its original default shipping state."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        progress_btn = QPushButton("Reset Progress")
        progress_btn.setObjectName("ResetProgressBtn")
        
        app_btn = QPushButton("Reset App Entirely")
        app_btn.setObjectName("ResetAppBtn")
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("CancelBtn")
        
        btn_layout.addWidget(progress_btn)
        btn_layout.addWidget(app_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        cancel_btn.clicked.connect(dialog.reject)
        
        def handle_progress_reset():
            confirm = QMessageBox.question(
                dialog, "Confirm Reset",
                "Are you sure you want to reset all progress? This action cannot be undone."
            )
            if confirm == QMessageBox.Yes:
                reset_progress_database()
                dialog.accept()
                self.reload_workspace()
                QMessageBox.information(self, "Reset Success", "Progress has been reset successfully.")
                
        def handle_app_reset():
            confirm = QMessageBox.question(
                dialog, "Confirm Reset",
                "Are you sure you want to reset the entire app to the shipping state? This will wipe all missions, progress, and settings."
            )
            if confirm == QMessageBox.Yes:
                set_active_database("NEET")
                reset_app_database()
                set_master_setting("active_mission", "NEET")
                try:
                    base_dir = get_database_path().parent
                    for path in base_dir.glob("prepmate_*.db"):
                        try:
                            path.unlink()
                        except Exception:
                            pass
                except Exception:
                    pass
                dialog.accept()
                self.reload_workspace()
                QMessageBox.information(self, "Reset Success", "App has been reset to the default shipping state.")
                
        progress_btn.clicked.connect(handle_progress_reset)
        app_btn.clicked.connect(handle_app_reset)
        
        dialog.exec()

    def on_ui_mode_changed(self, mode):
        self.ui_mode = mode
        set_setting("ui_mode", mode)
        if mode == "lite":
            self.stop_live_wallpaper()
        else:
            self.update_wallpaper_media()
            
        self.reload_workspace()
        
        for card in self.canvas.findChildren(AeroCard):
            card.apply_card_theme()
            
        self.rebuild_countdown_card()
        for table in self.subject_tables.values():
            table.viewport().update()

    def add_task_from_input(self, category):
        text = self.daily_widgets["input"].text().strip()
        if not text:
            return
        add_task(category, text)
        self.daily_widgets["input"].clear()
        self.reload_tasks(category)

    def reload_tasks(self, category):
        layout = self.daily_widgets["list"]
        while layout.count():
            item = layout.takeAt(0)
            child = item.widget()
            if child:
                child.deleteLater()

        rows = get_tasks(category)
        done_count = 0
        for task_id, text, done in rows:
            if done:
                done_count += 1

            row = QFrame()
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)

            checkbox = QCheckBox(text)
            checkbox.setChecked(bool(done))
            checkbox.stateChanged.connect(
                lambda state, tid=task_id, cat=category:
                self.toggle_task(tid, cat, state)
            )

            rename_btn = QPushButton("Rename")
            rename_btn.clicked.connect(
                lambda checked=False, tid=task_id, old=text, cat=category:
                self.rename_task(tid, old, cat)
            )

            delete_btn = QPushButton("X")
            delete_btn.setObjectName("DeleteButton")
            delete_btn.clicked.connect(
                lambda checked=False, tid=task_id, cat=category:
                self.remove_task(tid, cat)
            )

            row_layout.addWidget(checkbox)
            row_layout.addStretch()
            row_layout.addWidget(rename_btn)
            row_layout.addWidget(delete_btn)
            layout.addWidget(row)

        self.daily_widgets["counter"].setText(f"{done_count}/{len(rows)}")

    def toggle_task(self, task_id, category, state):
        update_task(task_id, done=(state == Qt.Checked.value))
        self.update_daily_counter(category)

    def update_daily_counter(self, category):
        rows = get_tasks(category)
        done_count = sum(1 for _, _, done in rows if done)
        self.daily_widgets["counter"].setText(f"{done_count}/{len(rows)}")

    def rename_task(self, task_id, old_text, category):
        dialog = QDialog(self)
        dialog.setWindowTitle("Rename Task")
        dialog.resize(350, 120)
        layout = QVBoxLayout(dialog)
        edit = QLineEdit(old_text)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(QLabel("Rename item:"))
        layout.addWidget(edit)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted:
            new_text = edit.text().strip()
            if new_text:
                update_task(task_id, text=new_text)
                self.reload_tasks(category)

    def remove_task(self, task_id, category):
        confirm = QMessageBox.question(self, "Delete", "Delete this item?")
        if confirm == QMessageBox.Yes:
            delete_task(task_id)
            self.reload_tasks(category)

    def load_exam_datetime(self):
        value = get_setting("exam_datetime", "2026-05-03 14:00:00")
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

    def save_exam_datetime(self):
        set_setting("exam_datetime", self.exam_datetime.strftime("%Y-%m-%d %H:%M:%S"))

    def edit_countdown(self):
        dialog = CountdownEditDialog(self.exam_datetime, self)
        if dialog.exec() == QDialog.Accepted:
            self.exam_datetime = dialog.selected_datetime()
            self.save_exam_datetime()
            self.update_countdown()
            QMessageBox.information(self, "Saved", "Countdown target updated.")

    def update_countdown(self):
        now = datetime.now()
        remaining = self.exam_datetime - now
        if remaining.total_seconds() <= 0:
            days = hours = minutes = 0
        else:
            days = remaining.days
            seconds_total = remaining.seconds
            hours = seconds_total // 3600
            minutes = (seconds_total % 3600) // 60
        self.days_label.set_value(str(days))
        self.hours_label.set_value(str(hours))
        self.minutes_label.set_value(str(minutes))
        self.target_label.setText(
            "Target: " + self.exam_datetime.strftime("%A, %d %B %Y at %I:%M %p")
        )

    # Canvas absolute layout system & custom overlay managers
    def resize_canvas_to_fit(self):
        max_x = 0
        max_y = 0
        for child in self.canvas.findChildren(AeroCard):
            r = child.geometry()
            max_x = max(max_x, r.right())
            max_y = max(max_y, r.bottom())
        self.canvas.setMinimumSize(max_x + 12, max_y + 20)

    def restore_all_geometries(self):
        locked = get_setting("layout_locked", "1") == "1"
        responsive = get_setting("layout_responsive", "1") == "1"
        if locked and responsive:
            self.apply_responsive_layout()
            return
            
        for card in [self.quote_area, self.countdown_card, self.focus_card, 
                     self.syllabus_card, self.daily_card["frame"], 
                     self.progress_card, self.extras_card]:
            geom = DEFAULT_GEOMETRIES.get(card.tile_id)
            if geom:
                card.restore_geometry(*geom)
        self.resize_canvas_to_fit()

    def reset_layout(self):
        set_setting("layout_locked", "1")
        set_setting("layout_responsive", "1")
        for card in [self.quote_area, self.countdown_card, self.focus_card, 
                     self.syllabus_card, self.daily_card["frame"], 
                     self.progress_card, self.extras_card]:
            set_setting(f"tile_geom_{card.tile_id}", "")
        self.apply_responsive_layout()

    def apply_responsive_layout(self):
        """Dynamically position cards based on the viewport size when the layout is locked."""
        vw = self.scroll.viewport().width()
        vh = self.scroll.viewport().height()

        # Ensure minimum usable area
        vw = max(vw, 1150)
        vh = max(vh, 920)

        pad = 12
        quote_h = 60

        # Quote bar spans the full width of the viewport
        self.quote_area.setGeometry(0, pad, vw, quote_h)

        top_y = pad + quote_h + pad
        top_h = 260

        # Width budgeting:
        # We have 3 columns on row 3, separated by 2 gaps (2 * pad).
        # We budget Column 1 + Column 2 (syllabus_w) as 68% of the total width.
        syllabus_w = int((vw - pad) * 0.68)
        sidebar_w = vw - syllabus_w - pad

        # Column 1 (Focus Hub) and Column 2 (Countdown) separation
        focus_w = int((syllabus_w - pad) * 0.64)
        countdown_w = syllabus_w - focus_w - pad
        progress_w = sidebar_w

        # Position Row 3 (top row of body)
        self.focus_card.setGeometry(0, top_y, focus_w, top_h)
        self.countdown_card.setGeometry(focus_w + pad, top_y, countdown_w, top_h)
        self.progress_card.setGeometry(syllabus_w + pad, top_y, progress_w, top_h)

        # Position Row 4 (bottom row of body)
        mid_y = top_y + top_h + pad
        remaining_h = vh - mid_y - pad

        # Syllabus card takes the bottom-left
        self.syllabus_card.setGeometry(0, mid_y, syllabus_w, remaining_h)

        # Right sidebar containing Notes (extras) on top, and Daily Log (daily) on bottom
        sidebar_x = syllabus_w + pad
        notes_h = int((remaining_h - pad) * 0.52)
        daily_h = remaining_h - notes_h - pad

        self.extras_card.setGeometry(sidebar_x, mid_y, sidebar_w, notes_h)
        self.daily_card["frame"].setGeometry(sidebar_x, mid_y + notes_h + pad, sidebar_w, daily_h)

        self.resize_canvas_to_fit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        locked = get_setting("layout_locked", "1") == "1"
        responsive = get_setting("layout_responsive", "1") == "1"
        if locked and responsive and hasattr(self, "scroll"):
            self.apply_responsive_layout()
        if hasattr(self, "wallpaper_sidebar") and self.wallpaper_sidebar.isVisible():
            w = 280
            self.wallpaper_sidebar.setGeometry(self.width() - w, 0, w, self.height())
            self.wallpaper_sidebar.raise_()
        if hasattr(self, "video_widget") and self.video_widget and self.video_widget.isVisible():
            self.video_widget.setGeometry(self.rect())
        if hasattr(self, "video_overlay") and self.video_overlay and self.video_overlay.isVisible():
            self.video_overlay.setGeometry(self.rect())

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                if self.wallpaper_player and self.wallpaper_player.playbackState() == QMediaPlayer.PlayingState:
                    self.wallpaper_player.pause()
                    self._video_paused_by_minimize = True
            else:
                if getattr(self, "_video_paused_by_minimize", False):
                    if self.wallpaper_player:
                        self.wallpaper_player.play()
                    self._video_paused_by_minimize = False

    def save_row_order(self, subject):
        """Read item_ids from the current table row order and save to database."""
        table = self.subject_tables.get(subject)
        if not table:
            return
        item_ids = []
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item:
                iid = item.data(Qt.UserRole)
                if iid is not None:
                    item_ids.append(iid)
        if item_ids:
            reorder_syllabus_items(item_ids)
            self.reload_subject(subject)

    def show_mission_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(15, 23, 42, 235);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 6px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 24px;
                color: #e5e7eb;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 30);
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 20);
                margin: 4px 8px;
            }
        """)

        base_dir = get_database_path().parent
        missions = ["NEET"]
        for path in base_dir.glob("prepmate_*.db"):
            name = path.stem[len("prepmate_"):]
            if name and name not in missions:
                missions.append(name)

        current = self.get_current_mission_name()
        for m in missions:
            action = menu.addAction(f"{'● ' if m == current else '   '}{m}")
            action.setData(m)

        menu.addSeparator()
        new_action = menu.addAction("+ New Mission...")
        new_action.setData("__new__")
        
        delete_action = menu.addAction("- Delete Mission...")
        delete_action.setData("__delete__")

        action = menu.exec(self.mission_btn.mapToGlobal(
            QPoint(0, self.mission_btn.height())
        ))
        if action:
            data = action.data()
            if data == "__new__":
                self.create_new_mission()
            elif data == "__delete__":
                self.delete_mission()
            elif data != current:
                self.switch_mission(data)

    def create_new_mission(self):
        name, ok = QInputDialog.getText(
            self,
            "New Mission",
            "Enter name for the new mission:"
        )
        name = name.strip() if ok else ""
        if not name:
            return
        import re
        safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
        if not safe_name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid mission name.")
            return
        set_active_database(safe_name)
        init_db()
        set_setting("exam_name", name)
        set_setting("first_run_completed", "1")
        current_ui_mode = getattr(self, "ui_mode", "aesthetic")
        set_setting("ui_mode", current_ui_mode)
        set_master_setting("active_mission", safe_name)
        self.reload_workspace()

    def switch_mission(self, name):
        set_active_database(name)
        init_db()
        set_master_setting("active_mission", name)
        self.reload_workspace()

    def delete_mission(self):
        base_dir = get_database_path().parent
        missions = ["NEET"]
        for path in base_dir.glob("prepmate_*.db"):
            name = path.stem[len("prepmate_"):]
            if name and name not in missions:
                missions.append(name)
        
        current = self.get_current_mission_name()
        deletable = [m for m in missions if m != current]
        if not deletable:
            QMessageBox.warning(
                self, 
                "Delete Mission Flow", 
                "There are no other missions to delete. Create a new mission first if you wish to delete the current one."
            )
            return
            
        item, ok = QInputDialog.getItem(
            self,
            "Delete Mission Flow",
            "Select the mission flow to delete (this will delete all progress and data for it):",
            deletable,
            0,
            False
        )
        if ok and item:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to permanently delete the mission '{item}'?\nAll progress, syllabus completions, and settings for this mission will be lost forever.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                import os
                import gc
                gc.collect()
                
                if item == "NEET":
                    db_file = base_dir / "prepmate.db"
                else:
                    db_file = base_dir / f"prepmate_{item}.db"
                
                try:
                    if db_file.exists():
                        db_file.unlink()
                    QMessageBox.information(self, "Delete Success", f"Mission flow '{item}' has been deleted successfully.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete mission file:\n{str(e)}")

    def get_accent_color(self):
        t = THEMES.get(self.theme_name, THEMES["Midnight Teal"])
        return t["accent"]

    def data_backup(self):
        active_db_path = get_database_path()
        if not active_db_path.exists():
            QMessageBox.critical(self, "Error", "Database file not found.")
            return

        suggested_name = f"prepmate_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        selected_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Data Backup",
            suggested_name,
            "SQLite Databases (*.db);;All Files (*)"
        )
        if not selected_file:
            return

        try:
            shutil.copy2(active_db_path, selected_file)
            QMessageBox.information(
                self,
                "Backup Saved",
                f"Successfully backed up database to:\n{selected_file}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data backup: {str(e)}")

    def save_snapshot(self):
        try:
            import zipfile
            base_dir = get_database_path().parent
            snapshots_dir = base_dir / "snapshots"
            snapshots_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = snapshots_dir / f"prepmate_snapshot_{timestamp}.zip"
            active_db_path = get_database_path()
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if active_db_path.exists():
                    zipf.write(active_db_path, active_db_path.name)
                default_db_path = base_dir / "prepmate.db"
                if default_db_path.exists() and default_db_path != active_db_path:
                    zipf.write(default_db_path, default_db_path.name)
                asset_dir = base_dir / "asset"
                if asset_dir.exists():
                    for file in asset_dir.rglob("*"):
                        if file.is_file():
                            zipf.write(file, file.relative_to(base_dir))
            QMessageBox.information(
                self,
                "Snapshot Saved",
                f"Successfully saved snapshot to:\n{zip_filename}"
            )
            return zip_filename
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save snapshot: {str(e)}")
            return None

    def upgrade_app(self):
        self.start_update_check(self.upgrade_btn)

    def open_subject_manager(self):
        dialog = SubjectManagerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.rebuild_syllabus_tabs()
            self.update_overall_progress()

    def open_checklist_category_manager(self):
        dialog = ChecklistCategoryManagerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.rebuild_syllabus_tabs()
            self.update_overall_progress()

    def get_current_mission_name(self):
        db_path = get_database_path()
        name = db_path.stem
        if name == "prepmate":
            return "NEET"
        elif name.startswith("prepmate_"):
            return name[len("prepmate_"):]
        return "NEET"

    def reload_workspace(self):
        self.exam_name = self.get_current_mission_name()
        db_exam_name = get_setting("exam_name", self.exam_name)
        self.title_label.setText(f"Operation {db_exam_name}")
        self.exam_datetime = self.load_exam_datetime()
        self.focus_seconds_left = int(get_setting("focus_minutes", "25")) * 60
        self.break_seconds_left = int(get_setting("break_minutes", "5")) * 60
        self.active_timer_mode = None
        self.selected_mode = "focus"
        self.ui_mode = get_setting("ui_mode", "aesthetic")
        if hasattr(self, "mode_toggle") and self.mode_toggle:
            self.mode_toggle.set_mode(self.ui_mode, animate=False)
        if get_master_setting("first_run_completed", "0") == "0":
            self.show_first_run_dialog()
            self.exam_name = self.get_current_mission_name()
            db_exam_name = get_setting("exam_name", self.exam_name)
            self.title_label.setText(f"Operation {db_exam_name}")
            self.exam_datetime = self.load_exam_datetime()
            self.focus_seconds_left = int(get_setting("focus_minutes", "25")) * 60
            self.break_seconds_left = int(get_setting("break_minutes", "5")) * 60
            self.ui_mode = get_setting("ui_mode", "aesthetic")
            if hasattr(self, "mode_toggle") and self.mode_toggle:
                self.mode_toggle.set_mode(self.ui_mode, animate=False)
        self.theme_name = get_setting("theme_preset", "Midnight Teal")
        self.ui_opacity = max(0.28, min(1.0, float(get_setting("ui_opacity", "0.62"))))
        self.wallpaper_path = get_setting("wallpaper_path", "")
        if not self.wallpaper_path:
            default_wallpaper = self.asset_path("motion", "vid1337.mpg")
            if default_wallpaper:
                self.wallpaper_path = str(default_wallpaper)
                set_setting("wallpaper_path", self.wallpaper_path)
        self.theme_box.blockSignals(True)
        self.theme_box.setCurrentText(self.theme_name if self.theme_name in THEMES else "Burgundy")
        self.theme_box.blockSignals(False)
        self.opacity_slider.setValue(int(self.ui_opacity * 100))
        self.set_app_style(reload_wallpaper=True)
        self.rebuild_syllabus_tabs()
        self.reload_tasks("daily")
        self.refresh_focus_hub()
        self.restore_all_geometries()
        self.update_graphics_shadows()
        self.advance_quote(initial=True)
        self.update_overall_progress()
        
        # Enable drag-drop reordering on all subject tables
        for table in self.subject_tables.values():
            if isinstance(table, DragDropTableWidget):
                table.set_drag_enabled(True)

    def make_gear_icon(self):
        from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(Qt.white, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        
        cx, cy = 16.0, 16.0
        r_inner = 5.0
        r_outer = 9.0
        
        painter.drawEllipse(QPointF(cx, cy), r_inner, r_inner)
        
        import math
        num_teeth = 8
        for i in range(num_teeth):
            angle = i * (2 * math.pi / num_teeth)
            x1 = cx + r_inner * math.cos(angle)
            y1 = cy + r_inner * math.sin(angle)
            x2 = cx + r_outer * math.cos(angle)
            y2 = cy + r_outer * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            
            cap_angle1 = angle - 0.2
            cap_angle2 = angle + 0.2
            cx1 = cx + r_outer * math.cos(cap_angle1)
            cy1 = cy + r_outer * math.sin(cap_angle1)
            cx2 = cx + r_outer * math.cos(cap_angle2)
            cy2 = cy + r_outer * math.sin(cap_angle2)
            painter.drawLine(QPointF(cx1, cy1), QPointF(cx2, cy2))
            
        painter.end()
        return QIcon(pixmap)

    def open_deep_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Deep UI Settings")
        dialog.setMinimumWidth(380)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: rgba(15, 23, 42, 245);
                border: 1px solid rgba(255, 255, 255, 40);
            }}
            QLabel {{
                color: white;
                font-weight: bold;
                font-size: 13px;
            }}
            QCheckBox {{
                color: white;
                font-size: 13px;
            }}
            QLineEdit {{
                background-color: rgba(0, 0, 0, 100);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 4px;
                color: white;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QPushButton {{
                background-color: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 4px;
                color: white;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 50);
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        
        title = QLabel("Deep UI Customization")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title)
        
        solid_chk = QCheckBox("Solid Tiles Mode (Opaque Card Backgrounds)")
        solid_mode_active = get_setting("solid_mode", "0") == "1"
        solid_chk.setChecked(solid_mode_active)
        layout.addWidget(solid_chk)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 20); height: 1px; border: none; margin-top: 4px; margin-bottom: 4px;")
        layout.addWidget(sep)
        
        # Updates Section
        title_updates = QLabel("Updates & Hosting")
        title_updates.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(title_updates)
        
        # Check Updates Row
        updates_row = QHBoxLayout()
        self.version_label = QLabel(f"Current Version: {APP_VERSION}")
        self.version_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,180); font-weight: normal;")
        self.check_updates_btn = QPushButton("Check for Updates")
        self.check_updates_btn.setStyleSheet("font-size: 11px; font-weight: bold; padding: 4px 10px;")
        self.check_updates_btn.clicked.connect(self.trigger_update_check)
        updates_row.addWidget(self.version_label)
        updates_row.addWidget(self.check_updates_btn)
        layout.addLayout(updates_row)
        
        # Separator line
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background-color: rgba(255, 255, 255, 20); height: 1px; border: none; margin-top: 4px;")
        layout.addWidget(sep2)
        
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        ok_btn = QPushButton("Apply Settings")
        ok_btn.clicked.connect(dialog.accept)
        btn_box.addWidget(ok_btn)
        layout.addLayout(btn_box)
        
        if dialog.exec() == QDialog.Accepted:
            new_solid = "1" if solid_chk.isChecked() else "0"
            set_setting("solid_mode", new_solid)
            self.reload_all_subject_themes()

    def reload_all_subject_themes(self):
        self.set_app_style(reload_wallpaper=False)
        for card in self.canvas.findChildren(AeroCard):
            card.apply_card_theme()
 
    def start_update_check(self, button_widget=None):
        self._current_update_btn = button_widget
        if button_widget:
            button_widget.setEnabled(False)
            button_widget.setText("Checking...")
        
        thread = threading.Thread(target=self.run_update_check)
        thread.daemon = True
        thread.start()

    def trigger_update_check(self):
        self.start_update_check(self.check_updates_btn)

    def run_update_check(self):
        import urllib.request
        import json
        
        username = "RabbDaRadio"
        repo = "Channel13"
        api_url = f"https://api.github.com/repos/{username}/{repo}/releases/latest"
        req = urllib.request.Request(
            api_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode())
                tag_name = data.get("tag_name", "")
                clean_tag = tag_name.lstrip("vV")
                
                assets = data.get("assets", [])
                zip_url = ""
                for asset in assets:
                    if asset.get("name", "").lower().endswith(".zip"):
                        zip_url = asset.get("browser_download_url", "")
                        break
                
                if self.is_newer_version(clean_tag, APP_VERSION) and zip_url:
                    body = data.get("body", "No release notes provided.")
                    QTimer.singleShot(0, lambda: self.prompt_for_update(clean_tag, zip_url, body))
                else:
                    QTimer.singleShot(0, lambda: self.show_update_message("No Updates", "You are already running the latest version."))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.show_update_message("Update Check Failed", f"Could not contact GitHub repository.\nError: {str(e)}"))

    def is_newer_version(self, new_ver, current_ver):
        try:
            new_parts = [int(x) for x in new_ver.split(".")]
            curr_parts = [int(x) for x in current_ver.split(".")]
            while len(new_parts) < 3: new_parts.append(0)
            while len(curr_parts) < 3: curr_parts.append(0)
            return new_parts > curr_parts
        except Exception:
            return False

    def prompt_for_update(self, new_version, zip_url, body):
        if hasattr(self, "_current_update_btn") and self._current_update_btn:
            self._current_update_btn.setEnabled(True)
            if self._current_update_btn == getattr(self, "upgrade_btn", None):
                self._current_update_btn.setText("Upgrade App...")
            else:
                self._current_update_btn.setText("Check for Updates")
        
        dialog = QDialog(self)
        dialog.setWindowTitle("New Version Available!")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel(f"Version {new_version} is available!")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        notes = QLabel("Release Notes:")
        notes.setStyleSheet("font-weight: bold; font-size: 12px; color: white;")
        layout.addWidget(notes)
        
        notes_text = QPlainTextEdit()
        notes_text.setPlainText(body)
        notes_text.setReadOnly(True)
        notes_text.setStyleSheet("background-color: rgba(0,0,0,50); border: 1px solid rgba(255,255,255,30); color: rgba(255,255,255,220);")
        layout.addWidget(notes_text)
        
        del_chk = QCheckBox("Delete the older version after importing data")
        del_chk.setChecked(True)
        del_chk.setStyleSheet("font-size: 12px; color: rgba(255,255,255,200);")
        layout.addWidget(del_chk)
        
        help_label = QLabel("(If unchecked, the old version will be archived in a ZIP file)")
        help_label.setStyleSheet("font-size: 10px; color: rgba(255,255,255,120); font-style: italic;")
        layout.addWidget(help_label)
        
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        cancel_btn = QPushButton("Later")
        cancel_btn.clicked.connect(dialog.reject)
        update_btn = QPushButton("Update Now")
        update_btn.clicked.connect(dialog.accept)
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(update_btn)
        layout.addLayout(btn_box)
        
        if dialog.exec() == QDialog.Accepted:
            delete_old = del_chk.isChecked()
            self.start_download_flow(zip_url, delete_old)

    def start_download_flow(self, zip_url, delete_old):
        dialog = QDialog(self)
        dialog.setWindowTitle("Downloading Update")
        dialog.setMinimumWidth(300)
        dialog.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        label = QLabel("Downloading update file...")
        label.setStyleSheet("font-size: 13px; color: white;")
        layout.addWidget(label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(0,0,0,80);
                border: 1px solid rgba(255,255,255,30);
                border-radius: 4px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: rgba(34, 197, 94, 200);
                border-radius: 4px;
            }
        """)
        layout.addWidget(progress_bar)
        
        dialog.show()
        
        def update_progress(percent):
            progress_bar.setValue(percent)
            
        def download_finished(temp_file_path):
            dialog.accept()
            self.launch_updater_process(temp_file_path, delete_old)
            
        def download_failed(err_msg):
            dialog.reject()
            self.show_update_message("Download Failed", f"Could not download update.\nError: {err_msg}")
            
        thread = threading.Thread(target=self.run_download_thread, args=(zip_url, update_progress, download_finished, download_failed))
        thread.daemon = True
        thread.start()

    def run_download_thread(self, zip_url, progress_callback, success_callback, failure_callback):
        import urllib.request
        import tempfile
        import os
        
        req = urllib.request.Request(
            zip_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                total_size = int(response.info().get('Content-Length', 0))
                block_size = 8192
                downloaded = 0
                
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, "prepmate_update.zip")
                
                with open(temp_file_path, "wb") as f:
                    while True:
                        block = response.read(block_size)
                        if not block:
                            break
                        f.write(block)
                        downloaded += len(block)
                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                            QTimer.singleShot(0, lambda p=percent: progress_callback(p))
                
                QTimer.singleShot(0, lambda path=temp_file_path: success_callback(path))
        except Exception as e:
            QTimer.singleShot(0, lambda msg=str(e): failure_callback(msg))

    def launch_updater_process(self, temp_file_path, delete_old):
        import os
        import subprocess
        import sys
        
        if getattr(sys, "frozen", False):
            app_dir = os.path.dirname(sys.executable)
            exe_name = os.path.basename(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            exe_name = "PrepMate.exe"
            
        app_dir = os.path.abspath(app_dir)
        temp_file_path = os.path.abspath(temp_file_path)
        
        ps_script_path = os.path.join(os.path.dirname(temp_file_path), "updater.ps1")
        
        backup_zip_name = f"PrepMate_Backup_{APP_VERSION}.zip"
        backup_dir = os.path.join(app_dir, "backup")
        backup_zip_path = os.path.join(backup_dir, backup_zip_name)
        
        app_dir_ps = app_dir.replace("'", "''")
        temp_zip_ps = temp_file_path.replace("'", "''")
        backup_dir_ps = backup_dir.replace("'", "''")
        backup_zip_ps = backup_zip_path.replace("'", "''")
        exe_name_ps = os.path.splitext(exe_name)[0]
        
        ps_content = f"""
# PowerShell Updater for PrepMate
$appDir = '{app_dir_ps}'
$tempZip = '{temp_zip_ps}'
$exeName = '{exe_name_ps}'

# 1. Wait for process to exit
Write-Host "Waiting for PrepMate to close..."
while (Get-Process -Name $exeName -ErrorAction SilentlyContinue) {{
    Start-Sleep -Milliseconds 200
}}
Start-Sleep -Seconds 1

# 2. Backup Databases if any exist
$tempDbDir = Join-Path $env:TEMP "prepmate_temp_dbs"
if (Test-Path $tempDbDir) {{ Remove-Item -Path $tempDbDir -Recurse -Force }}
New-Item -ItemType Directory -Path $tempDbDir | Out-Null
$dbFiles = Get-ChildItem -Path $appDir -Filter "prepmate*.db"
foreach ($db in $dbFiles) {{
    Copy-Item -Path $db.FullName -Destination $tempDbDir -Force
    Write-Host "Backed up database: $($db.Name)"
}}

# 3. Archive or Delete old files
$exePath = Join-Path $appDir ($exeName + ".exe")
$assetPath = Join-Path $appDir "asset"

if ('{str(delete_old).lower()}' -eq 'false') {{
    if (!(Test-Path '{backup_dir_ps}')) {{
        New-Item -ItemType Directory -Force -Path '{backup_dir_ps}' | Out-Null
    }}
    Write-Host "Archiving old version..."
    $targets = @()
    if (Test-Path $exePath) {{ $targets += $exePath }}
    if (Test-Path $assetPath) {{ $targets += $assetPath }}
    if ($targets.Count -gt 0) {{
        Compress-Archive -Path $targets -DestinationPath '{backup_zip_ps}' -Force
    }}
}}

Write-Host "Deleting old files..."
if (Test-Path $exePath) {{ Remove-Item -Path $exePath -Force }}
if (Test-Path $assetPath) {{ Remove-Item -Path $assetPath -Recurse -Force }}

# 4. Extract new ZIP
Write-Host "Extracting new version..."
Expand-Archive -Path $tempZip -DestinationPath $appDir -Force

# Rename PrepMate.exe to the custom executable name if they differ
$extractedExe = Join-Path $appDir "PrepMate.exe"
if (($exeName -ne "PrepMate") -and (Test-Path $extractedExe)) {{
    Rename-Item -Path $extractedExe -NewName ($exeName + ".exe") -Force
    Write-Host "Renamed new executable to custom name: $($exeName).exe"
}}

# 5. Restore Databases
if (Test-Path $tempDbDir) {{
    $backedDbs = Get-ChildItem -Path $tempDbDir -Filter "prepmate*.db"
    foreach ($db in $backedDbs) {{
        Copy-Item -Path $db.FullName -Destination $appDir -Force
        Write-Host "Restored database: $($db.Name)"
    }}
    Remove-Item -Path $tempDbDir -Recurse -Force
}}

# 6. Relaunch app
Write-Host "Restarting PrepMate..."
$newExe = Join-Path $appDir ($exeName + ".exe")
if (Test-Path $newExe) {{
    Start-Process -FilePath $newExe -WorkingDirectory $appDir
}}

Remove-Item -Path $tempZip -Force
Remove-Item -Path $MyInvocation.MyCommand.Path -Force
"""
        with open(ps_script_path, "w", encoding="utf-8") as f:
            f.write(ps_content)
            
        subprocess.Popen([
            "powershell.exe", 
            "-NoProfile",
            "-WindowStyle", "Hidden",
            "-ExecutionPolicy", "Bypass", 
            "-File", ps_script_path
        ])
        
        QApplication.quit()

    def show_update_message(self, title, msg):
        if hasattr(self, "_current_update_btn") and self._current_update_btn:
            self._current_update_btn.setEnabled(True)
            if self._current_update_btn == getattr(self, "upgrade_btn", None):
                self._current_update_btn.setText("Upgrade App...")
            else:
                self._current_update_btn.setText("Check for Updates")
        QMessageBox.information(self, title, msg)

    def save_current_notes(self):
        if hasattr(self, "current_notes_key") and self.current_notes_key:
            if hasattr(self, "notes_text_edit") and self.notes_text_edit:
                notes_text = self.notes_text_edit.toPlainText()
                set_setting(self.current_notes_key, notes_text)

    def select_notes_subject(self, subject_name):
        self.save_current_notes()
        self.current_notes_key = f"notes_subject_{subject_name}"
        if hasattr(self, "notes_target_label") and self.notes_target_label:
            self.notes_target_label.setText(f"Subject: {subject_name}")
            notes_val = get_setting(self.current_notes_key, "")
            self.notes_text_edit.setPlainText(notes_val)

    def select_notes_item(self, item_id, topic_name):
        self.save_current_notes()
        self.current_notes_key = f"notes_item_{item_id}"
        if hasattr(self, "notes_target_label") and self.notes_target_label:
            self.notes_target_label.setText(f"Topic: {topic_name}")
            notes_val = get_setting(self.current_notes_key, "")
            self.notes_text_edit.setPlainText(notes_val)

    def handle_table_selection_changed(self, table, subject):
        selected_ranges = table.selectedRanges()
        if not selected_ranges:
            return
        row = selected_ranges[0].topRow()
        id_item = table.item(row, 0)
        if id_item:
            item_id = id_item.data(Qt.UserRole)
            cell_widget = table.cellWidget(row, 0)
            topic_name = ""
            if isinstance(cell_widget, TopicProgressWidget):
                topic_name = cell_widget.topic
            self.select_notes_item(item_id, topic_name)
