"""
Система учёта иностранных студентов ННГАСУ
Точка входа.
"""
import sys
import os
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    root = tk.Tk()
    root.withdraw()   # скрыть до настройки

    # ── 1. Проверить / создать config.ini ────────────────────────────────────
    import config
    first_run = not config.is_configured()

    # ── 2. Если первый запуск — показать окно настройки пути к БД ────────────
    if first_run:
        root.deiconify()
        root.configure(bg="#1a3a5c")
        from ui.settings_window import SettingsWindow

        done = tk.BooleanVar(value=False)

        def on_settings_close():
            done.set(True)

        sw = SettingsWindow(root, on_close=on_settings_close, first_run=True)
        root.wait_variable(done)

    # ── 3. Инициализировать БД ────────────────────────────────────────────────
    try:
        import database
        database.init_database()
    except Exception as e:
        messagebox.showerror("Ошибка БД",
            f"Не удалось открыть базу данных:\n{e}\n\n"
            f"Путь: {config.get_db_path()}\n\n"
            "Откройте Настройки и укажите правильный путь.")
        # дать возможность исправить путь
        root.deiconify()
        from ui.settings_window import SettingsWindow
        SettingsWindow(root, first_run=True)
        root.mainloop()
        return

    # ── 4. Запустить окно входа ───────────────────────────────────────────────
    root.deiconify()
    root.configure(bg="#1a3a5c")

    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    from ui.login_window import LoginWindow
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
