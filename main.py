"""
Система учёта иностранных студентов ННГАСУ
==========================================
Точка входа в приложение.

Запуск:
    python main.py

Требования:
    pip install python-docx
"""
import sys
import os
import tkinter as tk
from tkinter import messagebox

# Добавляем корень проекта в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    # ── Проверить зависимости ─────────────────────────────────────────────────
    try:
        import docx  # noqa: F401
    except ImportError:
        # Не критично — Word-экспорт просто будет недоступен
        pass

    # ── Инициализировать БД ───────────────────────────────────────────────────
    try:
        from database import init_database
        init_database()
    except Exception as e:
        root_err = tk.Tk()
        root_err.withdraw()
        messagebox.showerror("Ошибка инициализации",
                             f"Не удалось открыть базу данных:\n{e}")
        root_err.destroy()
        sys.exit(1)

    # ── Создать главное окно ──────────────────────────────────────────────────
    root = tk.Tk()
    root.configure(bg="#1a3a5c")

    # ── Установить иконку (если есть) ─────────────────────────────────────────
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    # ── Запустить экран входа ─────────────────────────────────────────────────
    from ui.login_window import LoginWindow
    LoginWindow(root)

    root.mainloop()


if __name__ == "__main__":
    main()
