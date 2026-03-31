"""
Слой базы данных.
SQLite, хранится в папке data/students.db.
"""
import sqlite3
from pathlib import Path
from typing import Optional, List

DB_PATH = Path(__file__).parent / "data" / "students.db"

# ─────────────────────────── соединение ──────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ─────────────────────────── инициализация ───────────────────────────────────

def init_database():
    """Создать таблицы и заполнить справочники при первом запуске."""
    from auth import hash_password

    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        -- ── справочник стран ──────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS countries (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru  TEXT NOT NULL UNIQUE,
            name_lat TEXT
        );

        -- ── пользователи ──────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            salt          TEXT    NOT NULL,
            full_name     TEXT    NOT NULL,
            role          TEXT    NOT NULL
                CHECK(role IN ('admin','operator','viewer')),
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_at    TEXT    DEFAULT (datetime('now','localtime'))
        );

        -- ── студенты (20 полей по приказу) ────────────────────────────────
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- 1. ФИО (кириллица)
            last_name_ru    TEXT NOT NULL,
            first_name_ru   TEXT NOT NULL,
            middle_name_ru  TEXT,

            -- 2. ФИО (латиница)
            last_name_lat   TEXT,
            first_name_lat  TEXT,
            middle_name_lat TEXT,

            -- 3. Дата рождения
            birth_day   INTEGER NOT NULL CHECK(birth_day   BETWEEN 1 AND 31),
            birth_month INTEGER NOT NULL CHECK(birth_month BETWEEN 1 AND 12),
            birth_year  INTEGER NOT NULL,

            -- 4. Гражданство (ссылка на справочник)
            country_id INTEGER REFERENCES countries(id) ON UPDATE CASCADE,

            -- 5. Документ удостоверяющий личность
            id_doc_type   TEXT,
            id_doc_series TEXT,
            id_doc_number TEXT,

            -- 6. Срок действия документа уд. личности
            id_doc_valid_from TEXT,
            id_doc_valid_to   TEXT,

            -- 7. Виза (серия, номер)
            visa_series TEXT,
            visa_number TEXT,

            -- 8. Срок действия визы
            visa_valid_from TEXT,
            visa_valid_to   TEXT,

            -- 9. Контактные данные
            phone TEXT,
            email TEXT,

            -- 10. Форма обучения
            education_form TEXT CHECK(education_form IN
                ('очная','заочная','очно-заочная') OR education_form IS NULL),

            -- 11. Форма оплаты
            payment_form TEXT,

            -- 12. Дистанционные образовательные технологии
            distance_learning INTEGER NOT NULL DEFAULT 0,

            -- 13. Дата фактического прибытия
            arrival_date           TEXT,
            arrival_doc_type       TEXT,
            arrival_doc_date       TEXT,
            arrival_doc_requisites TEXT,

            -- 14. Адрес проживания по месту регистрации
            registration_address TEXT,

            -- 15. Дактилоскопия и фотографирование
            biometrics_doc  TEXT,
            biometrics_date TEXT,

            -- 16. Медицинское освидетельствование
            medical_doc      TEXT,
            medical_date     TEXT,
            medical_repeated INTEGER NOT NULL DEFAULT 0,

            -- 17. Академический отпуск
            academic_leave_doc   TEXT,
            academic_leave_basis TEXT,
            academic_leave_date  TEXT,

            -- 18. Трудовая деятельность
            employment_date TEXT,
            employer_info   TEXT,

            -- 19. Разрешение на временное проживание / ВНЖ
            residence_permit_doc      TEXT,
            residence_permit_type     TEXT,
            residence_permit_valid_to TEXT,

            -- 20. Нарушения миграционного законодательства
            violation_info           TEXT,
            violation_doc_type       TEXT,
            violation_date           TEXT,
            violation_doc_requisites TEXT,

            -- метаданные
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            created_by INTEGER REFERENCES users(id)
        );

        -- ── журнал действий ───────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS audit_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER REFERENCES users(id),
            action     TEXT NOT NULL,
            table_name TEXT,
            record_id  INTEGER,
            details    TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
    """)

    # Первый запуск: создать admin
    cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cur.fetchone()[0] == 0:
        salt, pw_hash = hash_password("admin123")
        cur.execute(
            "INSERT INTO users (username, password_hash, salt, full_name, role) "
            "VALUES (?,?,?,?,?)",
            ("admin", pw_hash, salt, "Администратор системы", "admin"),
        )

    # Первый запуск: заполнить справочник стран
    cur.execute("SELECT COUNT(*) FROM countries")
    if cur.fetchone()[0] == 0:
        countries = [
            ("Алжир", "Algeria"), ("Ангола", "Angola"),
            ("Афганистан", "Afghanistan"), ("Бангладеш", "Bangladesh"),
            ("Беларусь", "Belarus"), ("Вьетнам", "Vietnam"),
            ("Гана", "Ghana"), ("Гвинея", "Guinea"),
            ("Грузия", "Georgia"), ("Египет", "Egypt"),
            ("Индия", "India"), ("Иордания", "Jordan"),
            ("Иран", "Iran"), ("Ирак", "Iraq"),
            ("Камбоджа", "Cambodia"), ("Камерун", "Cameroon"),
            ("Казахстан", "Kazakhstan"), ("Кения", "Kenya"),
            ("Китай", "China"), ("Конго", "Congo"),
            ("Кот-д'Ивуар", "Cote d'Ivoire"), ("Кыргызстан", "Kyrgyzstan"),
            ("Лаос", "Laos"), ("Ливия", "Libya"),
            ("Мали", "Mali"), ("Марокко", "Morocco"),
            ("Молдова", "Moldova"), ("Монголия", "Mongolia"),
            ("Мьянма", "Myanmar"), ("Мозамбик", "Mozambique"),
            ("Непал", "Nepal"), ("Нигерия", "Nigeria"),
            ("Пакистан", "Pakistan"), ("Руанда", "Rwanda"),
            ("Сенегал", "Senegal"), ("Судан", "Sudan"),
            ("Сирия", "Syria"), ("Таджикистан", "Tajikistan"),
            ("Танзания", "Tanzania"), ("Тунис", "Tunisia"),
            ("Туркменистан", "Turkmenistan"), ("Уганда", "Uganda"),
            ("Украина", "Ukraine"), ("Узбекистан", "Uzbekistan"),
            ("Эфиопия", "Ethiopia"), ("Йемен", "Yemen"),
            ("Замбия", "Zambia"), ("Зимбабве", "Zimbabwe"),
            ("Азербайджан", "Azerbaijan"), ("Армения", "Armenia"),
        ]
        cur.executemany(
            "INSERT OR IGNORE INTO countries (name_ru, name_lat) VALUES (?,?)",
            countries,
        )

    conn.commit()
    conn.close()


# ─────────────────────────── пользователи ────────────────────────────────────

def get_all_users() -> List[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, full_name, role, is_active, created_at "
        "FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return row


def create_user(username: str, password: str, full_name: str, role: str):
    """Создать пользователя. Вернуть (ok, msg)."""
    from auth import hash_password

    conn = get_connection()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_active=1"
        ).fetchone()[0]
        if count >= 10:
            return False, "Достигнут лимит пользователей (максимум 10)"
        salt, pw_hash = hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, full_name, role) "
            "VALUES (?,?,?,?,?)",
            (username, pw_hash, salt, full_name, role),
        )
        conn.commit()
        return True, "Пользователь создан"
    except sqlite3.IntegrityError:
        return False, "Пользователь с таким логином уже существует"
    finally:
        conn.close()


def update_user(user_id: int, full_name: str, role: str, is_active: int,
                new_password: Optional[str] = None):
    from auth import hash_password

    conn = get_connection()
    try:
        if new_password:
            salt, pw_hash = hash_password(new_password)
            conn.execute(
                "UPDATE users SET full_name=?, role=?, is_active=?, "
                "password_hash=?, salt=? WHERE id=?",
                (full_name, role, is_active, pw_hash, salt, user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET full_name=?, role=?, is_active=? WHERE id=?",
                (full_name, role, is_active, user_id),
            )
        conn.commit()
        return True, "Пользователь обновлён"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ─────────────────────────── страны ──────────────────────────────────────────

def get_all_countries() -> List[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name_ru, name_lat FROM countries ORDER BY name_ru"
    ).fetchall()
    conn.close()
    return rows


def add_country(name_ru: str, name_lat: str = ""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO countries (name_ru, name_lat) VALUES (?,?)",
            (name_ru.strip(), name_lat.strip()),
        )
        conn.commit()
        return True, "Страна добавлена"
    except sqlite3.IntegrityError:
        return False, "Такая страна уже есть"
    finally:
        conn.close()


def delete_country(country_id: int):
    conn = get_connection()
    try:
        # проверяем есть ли студенты с этой страной
        used = conn.execute(
            "SELECT COUNT(*) FROM students WHERE country_id=?", (country_id,)
        ).fetchone()[0]
        if used:
            return False, f"Нельзя удалить: страна используется в {used} записях"
        conn.execute("DELETE FROM countries WHERE id=?", (country_id,))
        conn.commit()
        return True, "Страна удалена"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ─────────────────────────── студенты ────────────────────────────────────────

def get_all_students() -> List[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            s.id,
            s.last_name_ru || ' ' || s.first_name_ru ||
            CASE WHEN s.middle_name_ru IS NOT NULL AND s.middle_name_ru != ''
                 THEN ' ' || s.middle_name_ru ELSE '' END        AS full_name_ru,
            printf('%02d', s.birth_day) || '.' ||
            printf('%02d', s.birth_month) || '.' || s.birth_year AS birth_date,
            c.name_ru  AS citizenship,
            s.id_doc_type || ' ' || COALESCE(s.id_doc_series,'') ||
            ' ' || COALESCE(s.id_doc_number,'')                  AS doc_info,
            COALESCE(s.phone,'')                                  AS phone,
            COALESCE(s.education_form,'')                         AS education_form,
            s.created_at
        FROM students s
        LEFT JOIN countries c ON s.country_id = c.id
        ORDER BY s.last_name_ru, s.first_name_ru
    """).fetchall()
    conn.close()
    return rows


def get_student_by_id(student_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM students WHERE id=?", (student_id,)
    ).fetchone()
    conn.close()
    return row


def create_student(data: dict, user_id: int):
    conn = get_connection()
    try:
        data["created_by"] = user_id
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        conn.execute(
            f"INSERT INTO students ({cols}) VALUES ({placeholders})",
            list(data.values()),
        )
        conn.commit()
        return True, "Запись добавлена"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_student(student_id: int, data: dict):
    conn = get_connection()
    try:
        set_parts = [f"{k}=?" for k in data.keys()]
        set_parts.append("updated_at=datetime('now','localtime')")
        set_clause = ", ".join(set_parts)
        conn.execute(
            f"UPDATE students SET {set_clause} WHERE id=?",
            list(data.values()) + [student_id],
        )
        conn.commit()
        return True, "Запись обновлена"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def delete_student(student_id: int):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM students WHERE id=?", (student_id,))
        conn.commit()
        return True, "Запись удалена"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def search_students(query: str) -> List[sqlite3.Row]:
    q = f"%{query}%"
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            s.id,
            s.last_name_ru || ' ' || s.first_name_ru ||
            CASE WHEN s.middle_name_ru IS NOT NULL AND s.middle_name_ru != ''
                 THEN ' ' || s.middle_name_ru ELSE '' END AS full_name_ru,
            printf('%02d', s.birth_day) || '.' ||
            printf('%02d', s.birth_month) || '.' || s.birth_year AS birth_date,
            c.name_ru AS citizenship,
            s.id_doc_type || ' ' || COALESCE(s.id_doc_series,'') ||
            ' ' || COALESCE(s.id_doc_number,'') AS doc_info,
            COALESCE(s.phone,'') AS phone,
            COALESCE(s.education_form,'') AS education_form,
            s.created_at
        FROM students s
        LEFT JOIN countries c ON s.country_id = c.id
        WHERE s.last_name_ru LIKE ? OR s.first_name_ru LIKE ?
           OR s.last_name_lat LIKE ? OR s.id_doc_number LIKE ?
           OR c.name_ru LIKE ?
        ORDER BY s.last_name_ru, s.first_name_ru
    """, (q, q, q, q, q)).fetchall()
    conn.close()
    return rows


# ─────────────────────────── журнал ──────────────────────────────────────────

def log_action(user_id: int, action: str,
               table_name: str = None, record_id: int = None,
               details: str = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (user_id, action, table_name, record_id, details) "
        "VALUES (?,?,?,?,?)",
        (user_id, action, table_name, record_id, details),
    )
    conn.commit()
    conn.close()


def get_audit_log(limit: int = 200) -> List[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.created_at, u.username, a.action, a.table_name,
               a.record_id, a.details
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows
