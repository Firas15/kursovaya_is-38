"""
Окно настроек — конфигурация пути к базе данных.
Показывается при первом запуске или через меню.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

import config as cfg
import database as db

FONT   = ("Segoe UI", 10)
FONT_H = ("Segoe UI", 11, "bold")
DARK   = "#1a3a5c"
WHITE  = "#ffffff"


class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, on_close=None, first_run=False):
        super().__init__(parent)
        self.on_close   = on_close
        self.first_run  = first_run

        self.title("Настройки — Путь к базе данных")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self._center()

    def _build(self):
        # заголовок
        tk.Label(self, text="Настройка подключения к базе данных",
                 bg=DARK, fg=WHITE, font=FONT_H,
                 padx=16, pady=10).pack(fill="x")

        if self.first_run:
            tk.Label(self,
                text="Первый запуск! Укажите расположение файла базы данных.\n"
                     "Для одного рабочего места оставьте путь по умолчанию.\n"
                     "Для сети укажите UNC-путь: \\\\server\\share\\students.db",
                font=("Segoe UI", 9), bg="#fff3cd", fg="#856404",
                padx=12, pady=8, justify="left").pack(fill="x")

        frame = tk.Frame(self, padx=20, pady=16)
        frame.pack(fill="both")

        # ── текущий путь к БД ─────────────────────────────────────────────────
        tk.Label(frame, text="Путь к файлу базы данных:", font=FONT_H).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))

        self._path_var = tk.StringVar(value=str(cfg.get_db_path()))
        path_entry = ttk.Entry(frame, textvariable=self._path_var,
                               font=FONT, width=52)
        path_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 6))

        tk.Button(frame, text="📂 Обзор...", font=FONT,
                  relief="flat", bg="#dde3ec", cursor="hand2",
                  command=self._browse).grid(row=1, column=2, sticky="w")

        # примеры
        tk.Label(frame,
            text="Примеры:\n"
                 "  Локально:  C:\\ProgramData\\NNGAS\\students.db\n"
                 "  Сеть:      \\\\192.168.1.100\\share\\students.db",
            font=("Segoe UI", 8), fg="#555", justify="left"
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 12))

        ttk.Separator(frame).grid(row=3, column=0, columnspan=3, sticky="ew", pady=6)

        # ── статус шифрования ─────────────────────────────────────────────────
        enc_status = db.encryption_status()
        enc_color  = "#155724" if "активно" in enc_status else "#856404"
        enc_bg     = "#d5f5e3" if "активно" in enc_status else "#fff3cd"
        tk.Label(frame, text=enc_status, font=("Segoe UI", 9),
                 fg=enc_color, bg=enc_bg, padx=8, pady=4
                 ).grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 6))

        if "не активно" in enc_status:
            tk.Label(frame,
                text="Для включения шифрования выполните в Terminal PyCharm:\n"
                     "pip install sqlcipher3-binary",
                font=("Segoe UI", 8), fg="#555"
            ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Separator(frame).grid(row=6, column=0, columnspan=3, sticky="ew", pady=6)

        # ── кнопки ────────────────────────────────────────────────────────────
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=7, column=0, columnspan=3, sticky="ew")

        tk.Button(btn_frame, text="💾  Сохранить и перезапустить БД",
                  bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  command=self._save).pack(side="left", padx=(0, 8))

        tk.Button(btn_frame, text="Отмена",
                  bg="#7f8c8d", fg="white", font=FONT,
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=self._cancel).pack(side="left")

        if not self.first_run:
            tk.Button(btn_frame, text="🔄  Сбросить к умолчанию",
                      bg="#e74c3c", fg="white", font=FONT,
                      relief="flat", cursor="hand2", padx=8, pady=6,
                      command=self._reset).pack(side="right")

        self._err = tk.Label(frame, text="", fg="#e74c3c", font=FONT)
        self._err.grid(row=8, column=0, columnspan=3, pady=(8, 0))

    def _browse(self):
        path = filedialog.asksaveasfilename(
            title="Выберите или создайте файл БД",
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("Все файлы", "*.*")],
            parent=self,
        )
        if path:
            self._path_var.set(path)

    def _save(self):
        raw = self._path_var.get().strip()
        if not raw:
            self._err.config(text="Путь не может быть пустым")
            return

        p = Path(raw)
        # проверить что папка доступна (или создаётся)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._err.config(text=f"Не удаётся создать папку: {e}")
            return

        cfg.save_db_path(raw)
        try:
            db.init_database()
        except Exception as e:
            self._err.config(text=f"Ошибка подключения к БД: {e}")
            return

        messagebox.showinfo("Готово",
            f"Настройки сохранены.\nБаза данных: {raw}", parent=self)

        if self.on_close:
            self.on_close()
        self.destroy()

    def _reset(self):
        import config as cfg2
        default = str(cfg2._app_dir() / "data" / "students.db")
        self._path_var.set(default)

    def _cancel(self):
        if self.first_run:
            # при первом запуске нельзя просто закрыть — применим дефолт
            cfg.mark_configured()
        self.destroy()
        if self.on_close:
            self.on_close()

    def _center(self):
        self.update_idletasks()
        w, h = 560, 420
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
