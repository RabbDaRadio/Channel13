import sys
import traceback
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QInputDialog

from database import init_db, get_setting, set_setting, get_database_dir
from ui import MainWindow


def log_startup(message):
    try:
        with (get_database_dir() / "prepmate_error.log").open("a", encoding="utf-8") as file:
            file.write(message + "\n")
    except Exception:
        pass


def runtime_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def app_icon():
    for name in ("app_icon.ico", "icon.png"):
        path = runtime_dir() / "asset" / name
        if path.exists():
            return QIcon(str(path))
    return QIcon()


try:
    app = QApplication(sys.argv)
    icon = app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    init_db()

    from database import get_master_setting, set_active_database, set_master_setting
    active_mission = get_master_setting("active_mission", "").strip()
    if active_mission:
        set_active_database(active_mission)
        init_db()
    else:
        set_active_database("NEET")
        init_db()

    window = MainWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.setWindowFlags(
        Qt.Window
        | Qt.WindowMinimizeButtonHint
        | Qt.WindowMaximizeButtonHint
        | Qt.WindowCloseButtonHint
    )
    window.setMinimumSize(1220, 800)
    window.show()
    window.showNormal()
    window.raise_()
    window.activateWindow()
    QTimer.singleShot(250, window.raise_)
    QTimer.singleShot(300, window.activateWindow)

    sys.exit(app.exec())
except Exception:
    log_startup(traceback.format_exc())
    raise
