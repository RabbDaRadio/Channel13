import re
import sqlite3
import sys
from pathlib import Path


def is_dir_writeable(path: Path) -> bool:
    try:
        test_file = path / ".prepmate_write_test"
        test_file.touch()
        test_file.unlink()
        return True
    except Exception:
        return False


def get_database_dir() -> Path:
    if getattr(sys, "frozen", False):
        default_dir = Path(sys.executable).resolve().parent
    else:
        default_dir = Path(__file__).resolve().parent

    try:
        default_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    if is_dir_writeable(default_dir):
        return default_dir

    fallback_dir = Path.home() / ".prepmate"
    try:
        fallback_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return fallback_dir


def get_default_database_path():
    exe_name = Path(sys.executable).name.lower() if getattr(sys, "frozen", False) else ""
    if "laliya" in exe_name:
        return get_database_dir() / "prepmate_Laliya.db"
    return get_database_dir() / "prepmate.db"


DB_PATH = get_default_database_path()


def get_database_path():
    global DB_PATH
    return DB_PATH


def set_active_database(name_or_path):
    global DB_PATH
    if isinstance(name_or_path, Path):
        DB_PATH = name_or_path
    else:
        base_dir = get_database_dir()
        if not name_or_path or name_or_path == "NEET":
            DB_PATH = get_default_database_path()
        else:
            safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name_or_path)
            DB_PATH = base_dir / f"prepmate_{safe_name}.db"


EXACT_SYLLABUS = {
    "Physics": [
        "Units & Dimensions",
        "Kinematics",
        "NLM & Friction",
        "Circular Motion",
        "WPE",
        "COM",
        "Rotational Motion",
        "MPOS (Solids)",
        "MPOF (Fluids)",
        "Gravitation",
        "KTG",
        "Thermodynamics",
        "Waves",
        "Oscillations",
        "Electric Charges & Fields",
        "Electric Potential Energy",
        "Capacitance",
        "Current Electricity",
        "Magnetism",
        "EMI",
        "AC",
        "EM Waves",
        "Ray Optics",
        "Wave Optics",
        "Modern Physics",
        "Errors & Measurement",
    ],
    "Chemistry": [
        "Mole Concept",
        "Atomic Structure",
        "Thermodynamics",
        "Solutions",
        "Chemical Equilibrium",
        "Ionic Equilibrium",
        "Redox Rxn",
        "Electrochemistry",
        "Chemical Kinetics",
        "Periodicity",
        "Chemical Bonding",
        "Coordination Compounds",
        "p-Block Elements",
        "d- and f-Block",
        "Salt Analysis",
        "IUPAC Nomenclature",
        "GOC",
        "Isomerism",
        "Hydrocarbons",
        "Haloalkanes & Haloarenes",
        "Alcohols, Phenols & Ethers",
        "Aldehydes, Ketones & Acids",
        "Amines",
        "Biomolecules & Polymers",
    ],
    "Biology": [
        "The Living World",
        "Biological Classification",
        "Plant Kingdom",
        "Animal Kingdom",
        "Morphology of Flowering Plants",
        "Anatomy of Flowering Plants",
        "Structural Organisation in Animals",
        "Cell: The Unit of Life",
        "Biomolecules",
        "Cell Cycle and Cell Division",
        "Photosynthesis in Higher Plants",
        "Respiration in Plants",
        "Plant Growth and Development",
        "Breathing and Exchange of Gases",
        "Body Fluids and Circulation",
        "Excretory Products and their Elimination",
        "Locomotion and Movement",
        "Neural Control and Coordination",
        "Chemical Coordination and Integration",
        "Sexual Reproduction in Flowering Plants",
        "Human Reproduction",
        "Reproductive Health",
        "Principles of Inheritance and Variation",
        "Molecular Basis of Inheritance",
        "Evolution",
        "Human Health and Disease",
        "Microbes in Human Welfare",
        "Biotechnology: Principles and Processes",
        "Biotechnology and its Applications",
        "Organisms and Populations",
        "Ecosystem",
        "Biodiversity and Conservation",
    ],
}


DEFAULT_QUOTES = [
    "Small steps every day become a rank you can be proud of.",
    "Do the next chapter. Let the scoreboard update later.",
    "Consistency is louder than panic.",
    "You do not need a perfect day. You need a completed session.",
    "Revise once more than your doubt wants you to.",
    "Future you is quietly cheering for this exact minute.",
]


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            text TEXT NOT NULL,
            done INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS syllabus_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            module TEXT NOT NULL,
            topic TEXT NOT NULL,
            theory_done INTEGER DEFAULT 0,
            pyq_done INTEGER DEFAULT 0,
            special_done INTEGER DEFAULT 0,
            revision_done INTEGER DEFAULT 0,
            important INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL UNIQUE
        )
    """)

    cur.execute("PRAGMA table_info(syllabus_items)")
    syllabus_columns = {row[1] for row in cur.fetchall()}
    if "important" not in syllabus_columns:
        cur.execute("ALTER TABLE syllabus_items ADD COLUMN important INTEGER DEFAULT 0")
    if "display_order" not in syllabus_columns:
        cur.execute("ALTER TABLE syllabus_items ADD COLUMN display_order INTEGER DEFAULT 0")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS syllabus_categories (
            name TEXT PRIMARY KEY,
            include_in_progress INTEGER DEFAULT 1,
            display_order INTEGER DEFAULT 0
        )
    """)

    cur.execute("PRAGMA table_info(syllabus_categories)")
    cat_columns = {row[1] for row in cur.fetchall()}
    if "is_hidden" not in cat_columns:
        cur.execute("ALTER TABLE syllabus_categories ADD COLUMN is_hidden INTEGER DEFAULT 0")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS syllabus_completions (
            item_id INTEGER,
            category_name TEXT,
            status INTEGER DEFAULT 0,
            PRIMARY KEY (item_id, category_name)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            name TEXT PRIMARY KEY,
            display_order INTEGER DEFAULT 0
        )
    """)

    default_settings = {
        "app_font_family": "Arial",
        "app_font_size": "13",
        "focus_minutes": "25",
        "break_minutes": "5",
        "sessions_completed": "0",
        "study_seconds_total": "0",
        "break_seconds_total": "0",
        "break_sessions_completed": "0",
        "sound_enabled": "1",
        "volume_greencheck": "90",
        "volume_orangecheck": "90",
        "volume_important": "90",
        "volume_plankton": "90",
        "layout_locked": "1",
        "layout_responsive": "1",
        "ui_mode": "aesthetic",
        
        "lite_theme_preset": "Walnut",
        "lite_ui_opacity": "1.0",
        "lite_wallpaper_path": "",
        "lite_layout_locked": "1",
        "lite_layout_responsive": "1",
        
        "aesthetic_theme_preset": "Smoked Glass",
        "aesthetic_ui_opacity": "0.19",
        "aesthetic_wallpaper_path": "asset/motion/vid1999.mpg",
        "aesthetic_layout_locked": "1",
        "aesthetic_layout_responsive": "1",
        "github_username": "RabbDaRadio",
        "github_repo": "Channel13",
    }

    for key, value in default_settings.items():
        cur.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    for quote in DEFAULT_QUOTES:
        cur.execute("INSERT OR IGNORE INTO quotes (text) VALUES (?)", (quote,))

    cur.execute("SELECT COUNT(*) FROM syllabus_categories")
    if cur.fetchone()[0] == 0:
        default_cats = [
            ("Theory", 1, 0),
            ("PYQs", 1, 1),
            ("Special Problems", 1, 2),
            ("Revision", 1, 3),
        ]
        for name, inc, disp in default_cats:
            cur.execute(
                "INSERT INTO syllabus_categories (name, include_in_progress, display_order) VALUES (?, ?, ?)",
                (name, inc, disp),
            )

    cur.execute("SELECT COUNT(*) FROM syllabus_completions")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT id, theory_done, pyq_done, special_done, revision_done FROM syllabus_items")
        old_rows = cur.fetchall()
        for iid, th, py, sp, rv in old_rows:
            if th:
                cur.execute("INSERT OR REPLACE INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'Theory', ?)", (iid, th))
            if py:
                cur.execute("INSERT OR REPLACE INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'PYQs', ?)", (iid, py))
            if sp:
                cur.execute("INSERT OR REPLACE INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'Special Problems', ?)", (iid, sp))
            if rv:
                cur.execute("INSERT OR REPLACE INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'Revision', ?)", (iid, rv))

    cur.execute("SELECT COUNT(*) FROM subjects")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT DISTINCT subject FROM syllabus_items ORDER BY subject COLLATE NOCASE")
        subj_rows = [r[0] for r in cur.fetchall()]
        for idx, subj in enumerate(subj_rows):
            cur.execute("INSERT OR IGNORE INTO subjects (name, display_order) VALUES (?, ?)", (subj, idx))

    # Skip heavy reordering loop on startup to optimize loading time.
    # display_order is already correctly managed on insertion.
    pass

    conn.commit()
    conn.close()

    seed_syllabus_if_empty()


def seed_syllabus_if_empty():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM syllabus_items")
    row_count = cur.fetchone()[0]

    if row_count == 0:
        order_map = {"Physics": 0, "Chemistry": 1, "Biology": 2}
        for s_name, s_order in order_map.items():
            cur.execute("INSERT OR REPLACE INTO subjects (name, display_order) VALUES (?, ?)", (s_name, s_order))

        for subject, topics in EXACT_SYLLABUS.items():
            for idx, topic in enumerate(topics):
                cur.execute(
                    """
                    INSERT INTO syllabus_items (
                        subject, module, topic,
                        theory_done, pyq_done, special_done, revision_done, display_order
                    )
                    VALUES (?, '', ?, 0, 0, 0, 0, ?)
                    """,
                    (subject, topic, idx),
                )
                iid = cur.lastrowid
                cur.execute("INSERT INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'Theory', 0)", (iid,))
                cur.execute("INSERT INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'PYQs', 0)", (iid,))
                cur.execute("INSERT INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'Special Problems', 0)", (iid,))
                cur.execute("INSERT INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'Revision', 0)", (iid,))

    conn.commit()
    conn.close()


def replace_syllabus_with_exact_list():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM syllabus_completions")
    cur.execute("DELETE FROM syllabus_items")
    cur.execute("DELETE FROM subjects")

    order_map = {"Physics": 0, "Chemistry": 1, "Biology": 2}
    for s_name, s_order in order_map.items():
        cur.execute("INSERT OR REPLACE INTO subjects (name, display_order) VALUES (?, ?)", (s_name, s_order))

    for subject, topics in EXACT_SYLLABUS.items():
        for idx, topic in enumerate(topics):
            cur.execute(
                """
                INSERT INTO syllabus_items (
                    subject, module, topic,
                    theory_done, pyq_done, special_done, revision_done, display_order
                )
                VALUES (?, '', ?, 0, 0, 0, 0, ?)
                """,
                (subject, topic, idx),
            )
            iid = cur.lastrowid
            cur.execute("INSERT INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'Theory', 0)", (iid,))
            cur.execute("INSERT INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'PYQs', 0)", (iid,))
            cur.execute("INSERT INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'Special Problems', 0)", (iid,))
            cur.execute("INSERT INTO syllabus_completions (item_id, category_name, status) VALUES (?, 'Revision', 0)", (iid,))

    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default


def set_setting(key, value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, str(value)),
    )
    conn.commit()
    conn.close()


def add_task(category, text):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (category, text, done) VALUES (?, ?, 0)",
        (category, text),
    )
    conn.commit()
    conn.close()


def get_tasks(category):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, text, done FROM tasks WHERE category = ? ORDER BY id DESC",
        (category,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_task(task_id, text=None, done=None):
    conn = get_connection()
    cur = conn.cursor()

    if text is not None:
        cur.execute("UPDATE tasks SET text = ? WHERE id = ?", (text, task_id))

    if done is not None:
        cur.execute(
            "UPDATE tasks SET done = ? WHERE id = ?",
            (1 if done else 0, task_id),
        )

    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def add_syllabus_item(subject, module, topic):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(display_order) FROM syllabus_items WHERE subject = ?", (subject,))
    val = cur.fetchone()[0]
    max_order = int(val) if val is not None else -1

    cur.execute(
        """
        INSERT INTO syllabus_items (
            subject, module, topic,
            theory_done, pyq_done, special_done, revision_done, important, display_order
        )
        VALUES (?, ?, ?, 0, 0, 0, 0, 0, ?)
        """,
        (subject, module, topic, max_order + 1),
    )
    iid = cur.lastrowid

    cur.execute("SELECT name FROM syllabus_categories")
    cats = [r[0] for r in cur.fetchall()]
    for cat in cats:
        cur.execute(
            "INSERT OR IGNORE INTO syllabus_completions (item_id, category_name, status) VALUES (?, ?, 0)",
            (iid, cat),
        )

    conn.commit()
    conn.close()


def get_syllabus_items(subject):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, module, topic, important, display_order
        FROM syllabus_items
        WHERE subject = ?
        ORDER BY display_order ASC, id ASC
        """,
        (subject,),
    )
    rows = cur.fetchall()
    result = []
    for item_id, module, topic, important, display_order in rows:
        theory = 0
        pyq = 0
        special = 0
        revision = 0
        cur.execute("SELECT category_name, status FROM syllabus_completions WHERE item_id = ?", (item_id,))
        for cat, stat in cur.fetchall():
            if cat == "Theory":
                theory = stat
            elif cat == "PYQs":
                pyq = stat
            elif cat == "Special Problems":
                special = stat
            elif cat == "Revision":
                revision = stat
        result.append((item_id, module, topic, theory, pyq, special, revision, important))
    conn.close()
    return result


def get_syllabus_items_dynamic(subject):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, module, topic, important, display_order
        FROM syllabus_items
        WHERE subject = ?
        ORDER BY display_order ASC, id ASC
        """,
        (subject,),
    )
    items = cur.fetchall()
    if not items:
        conn.close()
        return []

    item_ids = [r[0] for r in items]
    placeholders = ",".join("?" for _ in item_ids)
    cur.execute(
        f"""
        SELECT item_id, category_name, status 
        FROM syllabus_completions 
        WHERE item_id IN ({placeholders})
        """,
        item_ids,
    )
    completions_map = {}
    for item_id, cat_name, status in cur.fetchall():
        if item_id not in completions_map:
            completions_map[item_id] = {}
        completions_map[item_id][cat_name] = status

    result = []
    for item_id, module, topic, important, display_order in items:
        completions = completions_map.get(item_id, {})
        result.append((item_id, module, topic, important, display_order, completions))
    conn.close()
    return result


def update_syllabus_item(
    item_id,
    module=None,
    topic=None,
    theory_done=None,
    pyq_done=None,
    special_done=None,
    revision_done=None,
    important=None,
):
    conn = get_connection()
    cur = conn.cursor()

    updates = []
    values = []

    fields = {
        "module": module,
        "topic": topic,
        "important": important,
    }

    for field, value in fields.items():
        if value is not None:
            updates.append(f"{field} = ?")
            if field == "important":
                values.append(1 if value else 0)
            else:
                values.append(value)

    if updates:
        values.append(item_id)
        cur.execute(
            f"UPDATE syllabus_items SET {', '.join(updates)} WHERE id = ?",
            values,
        )

    legacy_completions = {
        "Theory": theory_done,
        "PYQs": pyq_done,
        "Special Problems": special_done,
        "Revision": revision_done,
    }
    for cat_name, done_val in legacy_completions.items():
        if done_val is not None:
            cur.execute(
                "INSERT OR REPLACE INTO syllabus_completions (item_id, category_name, status) VALUES (?, ?, ?)",
                (item_id, cat_name, int(done_val)),
            )

    conn.commit()
    conn.close()


def update_syllabus_completion(item_id, category_name, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO syllabus_completions (item_id, category_name, status) VALUES (?, ?, ?)",
        (item_id, category_name, int(status)),
    )
    conn.commit()
    conn.close()


def delete_syllabus_item(item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM syllabus_items WHERE id = ?", (item_id,))
    cur.execute("DELETE FROM syllabus_completions WHERE item_id = ?", (item_id,))
    conn.commit()
    conn.close()


def get_subject_progress(subject):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT name FROM syllabus_categories WHERE include_in_progress = 1 AND (is_hidden IS NULL OR is_hidden = 0)")
    active_cats = [r[0] for r in cur.fetchall()]

    if not active_cats:
        conn.close()
        return 0, 0, 0

    cur.execute("SELECT id FROM syllabus_items WHERE subject = ?", (subject,))
    items = [r[0] for r in cur.fetchall()]

    if not items:
        conn.close()
        return 0, 0, 0

    total_boxes = len(items) * len(active_cats)

    placeholders = ",".join("?" for _ in items)
    cat_placeholders = ",".join("?" for _ in active_cats)
    query = f"""
        SELECT status FROM syllabus_completions 
        WHERE item_id IN ({placeholders}) 
          AND category_name IN ({cat_placeholders})
    """
    cur.execute(query, items + active_cats)
    completed = 0.0
    for (status,) in cur.fetchall():
        if status == 1:
            completed += 1.0
        elif status == 2:
            completed += 0.5

    conn.close()
    percent = int((completed / total_boxes) * 100) if total_boxes > 0 else 0
    return percent, completed, total_boxes


def get_quotes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, text FROM quotes ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_subjects():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM subjects ORDER BY display_order ASC")
    rows = [row[0] for row in cur.fetchall()]
    if not rows:
        cur.execute("SELECT DISTINCT subject FROM syllabus_items ORDER BY subject COLLATE NOCASE")
        rows = [row[0] for row in cur.fetchall()]
    conn.close()
    return rows


def add_subject(subject):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(display_order) FROM subjects")
    val = cur.fetchone()[0]
    max_order = int(val) if val is not None else -1

    cur.execute(
        "INSERT OR IGNORE INTO subjects (name, display_order) VALUES (?, ?)",
        (subject, max_order + 1),
    )

    cur.execute(
        """
        INSERT INTO syllabus_items (
            subject, module, topic,
            theory_done, pyq_done, special_done, revision_done, important, display_order
        )
        VALUES (?, '', 'First topic', 0, 0, 0, 0, 0, 0)
        """,
        (subject,),
    )
    iid = cur.lastrowid

    cur.execute("SELECT name FROM syllabus_categories")
    cats = [r[0] for r in cur.fetchall()]
    for cat in cats:
        cur.execute(
            "INSERT OR IGNORE INTO syllabus_completions (item_id, category_name, status) VALUES (?, ?, 0)",
            (iid, cat),
        )

    conn.commit()
    conn.close()


def rename_subject(old_name, new_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE subjects SET name = ? WHERE name = ?", (new_name, old_name))
    cur.execute("UPDATE syllabus_items SET subject = ? WHERE subject = ?", (new_name, old_name))
    conn.commit()
    conn.close()


def delete_subject(subject_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM subjects WHERE name = ?", (subject_name,))
    cur.execute("SELECT id FROM syllabus_items WHERE subject = ?", (subject_name,))
    item_ids = [r[0] for r in cur.fetchall()]
    for item_id in item_ids:
        cur.execute("DELETE FROM syllabus_completions WHERE item_id = ?", (item_id,))
    cur.execute("DELETE FROM syllabus_items WHERE subject = ?", (subject_name,))
    conn.commit()
    conn.close()


def reorder_subjects(subject_list):
    conn = get_connection()
    cur = conn.cursor()
    for idx, name in enumerate(subject_list):
        cur.execute("UPDATE subjects SET display_order = ? WHERE name = ?", (idx, name))
    conn.commit()
    conn.close()


def get_categories(include_hidden=True):
    conn = get_connection()
    cur = conn.cursor()
    if include_hidden:
        cur.execute("SELECT name, include_in_progress, display_order, is_hidden FROM syllabus_categories ORDER BY display_order ASC")
    else:
        cur.execute("SELECT name, include_in_progress, display_order, is_hidden FROM syllabus_categories WHERE is_hidden = 0 ORDER BY display_order ASC")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_category(name, include_in_progress=1):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(display_order) FROM syllabus_categories")
    val = cur.fetchone()[0]
    max_order = int(val) if val is not None else -1

    cur.execute(
        "INSERT OR IGNORE INTO syllabus_categories (name, include_in_progress, display_order) VALUES (?, ?, ?)",
        (name, int(include_in_progress), max_order + 1),
    )

    cur.execute("SELECT id FROM syllabus_items")
    item_ids = [r[0] for r in cur.fetchall()]
    for iid in item_ids:
        cur.execute(
            "INSERT OR IGNORE INTO syllabus_completions (item_id, category_name, status) VALUES (?, ?, 0)",
            (iid, name),
        )

    conn.commit()
    conn.close()


def update_category(old_name, new_name, include_in_progress=None, is_hidden=None):
    conn = get_connection()
    cur = conn.cursor()
    if include_in_progress is not None:
        cur.execute(
            "UPDATE syllabus_categories SET include_in_progress = ? WHERE name = ?",
            (int(include_in_progress), old_name),
        )
    if is_hidden is not None:
        cur.execute(
            "UPDATE syllabus_categories SET is_hidden = ? WHERE name = ?",
            (int(is_hidden), old_name),
        )
    if new_name and new_name != old_name:
        cur.execute("UPDATE syllabus_categories SET name = ? WHERE name = ?", (new_name, old_name))
        cur.execute("UPDATE syllabus_completions SET category_name = ? WHERE category_name = ?", (new_name, old_name))
    conn.commit()
    conn.close()


def delete_category(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM syllabus_categories WHERE name = ?", (name,))
    cur.execute("DELETE FROM syllabus_completions WHERE category_name = ?", (name,))
    conn.commit()
    conn.close()


def reorder_categories(category_list):
    conn = get_connection()
    cur = conn.cursor()
    for idx, name in enumerate(category_list):
        cur.execute("UPDATE syllabus_categories SET display_order = ? WHERE name = ?", (idx, name))
    conn.commit()
    conn.close()


def reorder_syllabus_items(item_ids):
    conn = get_connection()
    cur = conn.cursor()
    for idx, item_id in enumerate(item_ids):
        cur.execute("UPDATE syllabus_items SET display_order = ? WHERE id = ?", (idx, item_id))
    conn.commit()
    conn.close()


def move_syllabus_item(item_id, direction):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT subject, display_order FROM syllabus_items WHERE id = ?", (item_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return

    subject, current_order = row

    if direction == "up":
        cur.execute(
            """
            SELECT id, display_order FROM syllabus_items 
            WHERE subject = ? AND display_order < ? 
            ORDER BY display_order DESC LIMIT 1
            """,
            (subject, current_order),
        )
    else:
        cur.execute(
            """
            SELECT id, display_order FROM syllabus_items 
            WHERE subject = ? AND display_order > ? 
            ORDER BY display_order ASC LIMIT 1
            """,
            (subject, current_order),
        )

    other = cur.fetchone()
    if other:
        other_id, other_order = other
        cur.execute("UPDATE syllabus_items SET display_order = ? WHERE id = ?", (other_order, item_id))
        cur.execute("UPDATE syllabus_items SET display_order = ? WHERE id = ?", (current_order, other_id))
        conn.commit()

    conn.close()


def add_quote(text):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO quotes (text) VALUES (?)", (text,))
    conn.commit()
    conn.close()


def delete_quote(quote_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))
    conn.commit()
    conn.close()


def set_master_setting(key, value):
    base_dir = get_default_database_path().parent
    default_db = base_dir / "prepmate.db"
    conn = sqlite3.connect(default_db)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()


def get_master_setting(key, default=None):
    base_dir = get_default_database_path().parent
    default_db = base_dir / "prepmate.db"
    if not default_db.exists():
        return default
    conn = sqlite3.connect(default_db)
    cur = conn.cursor()
    try:
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        val = row[0] if row else default
    except Exception:
        val = default
    conn.close()
    return val


def reset_app_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks")
    cur.execute("DELETE FROM syllabus_completions")
    cur.execute("DELETE FROM syllabus_items")
    cur.execute("DELETE FROM subjects")
    cur.execute("DELETE FROM settings")
    conn.commit()
    conn.close()
    init_db()
    replace_syllabus_with_exact_list()


def reset_progress_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE syllabus_completions SET status = 0")
    cur.execute("UPDATE syllabus_items SET theory_done=0, pyq_done=0, special_done=0, revision_done=0, important=0")
    cur.execute("DELETE FROM tasks")
    cur.execute("DELETE FROM settings WHERE key LIKE 'notes_subject_%' OR key LIKE 'notes_item_%'")
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('sessions_completed', '0')")
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('study_seconds_total', '0')")
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('break_seconds_total', '0')")
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('break_sessions_completed', '0')")
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('exam_datetime', '2026-05-03 14:00:00')")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    replace_syllabus_with_exact_list()
    print("Database created/updated successfully.")
    print("Syllabus replaced with your exact list.")
