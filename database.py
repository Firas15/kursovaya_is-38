"""
Слой базы данных.

Путь к БД берётся из config.ini — может быть локальным или сетевым (UNC).
Шифрование через SQLCipher (пакет sqlcipher3-binary).
Если sqlcipher3-binary не установлен — работает без шифрования с предупреждением.
"""
import sqlite3 as _sqlite3_stdlib
from pathlib import Path
from typing import Optional, List

import config as _cfg

# ── попытка использовать SQLCipher ────────────────────────────────────────────
try:
    from sqlcipher3 import dbapi2 as _sqlite3
    ENCRYPTION_AVAILABLE = True
except ImportError:
    _sqlite3 = _sqlite3_stdlib
    ENCRYPTION_AVAILABLE = False


def get_connection():
    db_path = _cfg.get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = _sqlite3.connect(str(db_path))
    conn.row_factory = _sqlite3.Row

    if ENCRYPTION_AVAILABLE:
        key = _cfg.get_db_key()
        conn.execute(f"PRAGMA key='{key}'")

    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def encryption_status() -> str:
    if ENCRYPTION_AVAILABLE:
        return "Шифрование: SQLCipher (активно)"
    return "Шифрование: не активно (установите sqlcipher3-binary)"


def init_database():
    from auth import hash_password
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS countries (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru  TEXT NOT NULL UNIQUE,
            name_lat TEXT
        );
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
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name_ru    TEXT NOT NULL,
            first_name_ru   TEXT NOT NULL,
            middle_name_ru  TEXT,
            last_name_lat   TEXT,
            first_name_lat  TEXT,
            middle_name_lat TEXT,
            birth_day   INTEGER NOT NULL CHECK(birth_day   BETWEEN 1 AND 31),
            birth_month INTEGER NOT NULL CHECK(birth_month BETWEEN 1 AND 12),
            birth_year  INTEGER NOT NULL,
            country_id INTEGER REFERENCES countries(id) ON UPDATE CASCADE,
            id_doc_type   TEXT,
            id_doc_series TEXT,
            id_doc_number TEXT,
            id_doc_valid_from TEXT,
            id_doc_valid_to   TEXT,
            visa_series TEXT,
            visa_number TEXT,
            visa_valid_from TEXT,
            visa_valid_to   TEXT,
            phone TEXT,
            email TEXT,
            education_form TEXT CHECK(education_form IN
                ('очная','заочная','очно-заочная') OR education_form IS NULL),
            payment_form TEXT,
            distance_learning INTEGER NOT NULL DEFAULT 0,
            arrival_date           TEXT,
            arrival_doc_type       TEXT,
            arrival_doc_date       TEXT,
            arrival_doc_requisites TEXT,
            registration_address TEXT,
            biometrics_doc  TEXT,
            biometrics_date TEXT,
            medical_doc      TEXT,
            medical_date     TEXT,
            medical_repeated INTEGER NOT NULL DEFAULT 0,
            academic_leave_doc   TEXT,
            academic_leave_basis TEXT,
            academic_leave_date  TEXT,
            employment_date TEXT,
            employer_info   TEXT,
            residence_permit_doc      TEXT,
            residence_permit_type     TEXT,
            residence_permit_valid_to TEXT,
            violation_info           TEXT,
            violation_doc_type       TEXT,
            violation_date           TEXT,
            violation_doc_requisites TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            created_by INTEGER REFERENCES users(id)
        );
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

    cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cur.fetchone()[0] == 0:
        salt, pw_hash = hash_password("admin123")
        cur.execute(
            "INSERT INTO users (username, password_hash, salt, full_name, role) VALUES (?,?,?,?,?)",
            ("admin", pw_hash, salt, "Администратор системы", "admin"),
        )

    cur.execute("SELECT COUNT(*) FROM countries")
    if cur.fetchone()[0] == 0:
        countries = [
            ("Алжир","Algeria"),("Ангола","Angola"),("Афганистан","Afghanistan"),
            ("Бангладеш","Bangladesh"),("Беларусь","Belarus"),("Вьетнам","Vietnam"),
            ("Гана","Ghana"),("Гвинея","Guinea"),("Грузия","Georgia"),("Египет","Egypt"),
            ("Индия","India"),("Иордания","Jordan"),("Иран","Iran"),("Ирак","Iraq"),
            ("Камбоджа","Cambodia"),("Камерун","Cameroon"),("Казахстан","Kazakhstan"),
            ("Кения","Kenya"),("Китай","China"),("Конго","Congo"),
            ("Кот-д'Ивуар","Cote d'Ivoire"),("Кыргызстан","Kyrgyzstan"),
            ("Лаос","Laos"),("Ливия","Libya"),("Мали","Mali"),("Марокко","Morocco"),
            ("Молдова","Moldova"),("Монголия","Mongolia"),("Мьянма","Myanmar"),
            ("Мозамбик","Mozambique"),("Непал","Nepal"),("Нигерия","Nigeria"),
            ("Пакистан","Pakistan"),("Руанда","Rwanda"),("Сенегал","Senegal"),
            ("Судан","Sudan"),("Сирия","Syria"),("Таджикистан","Tajikistan"),
            ("Танзания","Tanzania"),("Тунис","Tunisia"),("Туркменистан","Turkmenistan"),
            ("Уганда","Uganda"),("Украина","Ukraine"),("Узбекистан","Uzbekistan"),
            ("Эфиопия","Ethiopia"),("Йемен","Yemen"),("Замбия","Zambia"),
            ("Зимбабве","Zimbabwe"),("Азербайджан","Azerbaijan"),("Армения","Armenia"),
        ]
        cur.executemany("INSERT OR IGNORE INTO countries (name_ru, name_lat) VALUES (?,?)", countries)

    conn.commit()
    conn.close()


def get_all_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, full_name, role, is_active, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def get_user_by_username(username: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return row


def create_user(username: str, password: str, full_name: str, role: str):
    from auth import hash_password
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM users WHERE is_active=1").fetchone()[0]
        if count >= 10:
            return False, "Достигнут лимит пользователей (максимум 10)"
        salt, pw_hash = hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, full_name, role) VALUES (?,?,?,?,?)",
            (username, pw_hash, salt, full_name, role),
        )
        conn.commit()
        return True, "Пользователь создан"
    except Exception as e:
        return False, "Пользователь с таким логином уже существует"
    finally:
        conn.close()


def update_user(user_id: int, full_name: str, role: str, is_active: int,
                new_password=None):
    from auth import hash_password
    conn = get_connection()
    try:
        if new_password:
            salt, pw_hash = hash_password(new_password)
            conn.execute(
                "UPDATE users SET full_name=?, role=?, is_active=?, password_hash=?, salt=? WHERE id=?",
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


def get_all_countries():
    conn = get_connection()
    rows = conn.execute("SELECT id, name_ru, name_lat FROM countries ORDER BY name_ru").fetchall()
    conn.close()
    return rows


def add_country(name_ru: str, name_lat: str = ""):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO countries (name_ru, name_lat) VALUES (?,?)",
                     (name_ru.strip(), name_lat.strip()))
        conn.commit()
        return True, "Страна добавлена"
    except Exception:
        return False, "Такая страна уже есть"
    finally:
        conn.close()


def delete_country(country_id: int):
    conn = get_connection()
    try:
        used = conn.execute("SELECT COUNT(*) FROM students WHERE country_id=?",
                            (country_id,)).fetchone()[0]
        if used:
            return False, f"Нельзя удалить: страна используется в {used} записях"
        conn.execute("DELETE FROM countries WHERE id=?", (country_id,))
        conn.commit()
        return True, "Страна удалена"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


_STUDENT_SELECT = """
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
"""

def get_all_students():
    conn = get_connection()
    rows = conn.execute(_STUDENT_SELECT + " ORDER BY s.last_name_ru, s.first_name_ru").fetchall()
    conn.close()
    return rows


def get_student_by_id(student_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    conn.close()
    return row


def get_students_by_ids(ids: list):
    """Вернуть несколько студентов по списку id."""
    if not ids:
        return []
    placeholders = ",".join(["?"] * len(ids))
    conn = get_connection()
    rows = conn.execute(
        _STUDENT_SELECT + f" WHERE s.id IN ({placeholders}) ORDER BY s.last_name_ru, s.first_name_ru",
        ids
    ).fetchall()
    conn.close()
    return rows


def create_student(data: dict, user_id: int):
    conn = get_connection()
    try:
        data["created_by"] = user_id
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        conn.execute(f"INSERT INTO students ({cols}) VALUES ({placeholders})", list(data.values()))
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
        conn.execute(
            f"UPDATE students SET {', '.join(set_parts)} WHERE id=?",
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


def search_students(query: str):
    q = f"%{query}%"
    conn = get_connection()
    rows = conn.execute(
        _STUDENT_SELECT +
        " WHERE s.last_name_ru LIKE ? OR s.first_name_ru LIKE ?"
        " OR s.last_name_lat LIKE ? OR s.id_doc_number LIKE ?"
        " OR c.name_ru LIKE ?"
        " ORDER BY s.last_name_ru, s.first_name_ru",
        (q, q, q, q, q)
    ).fetchall()
    conn.close()
    return rows


def log_action(user_id: int, action: str,
               table_name: str = None, record_id: int = None, details: str = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (user_id, action, table_name, record_id, details) VALUES (?,?,?,?,?)",
        (user_id, action, table_name, record_id, details),
    )
    conn.commit()
    conn.close()


def get_audit_log(limit: int = 200):
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.created_at, u.username, a.action, a.table_name, a.record_id, a.details
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows
