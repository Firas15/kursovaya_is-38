"""
Окно входа в систему.
"""
import tkinter as tk
from tkinter import ttk, messagebox

import database as db
from auth import verify_password

# ── цвета и шрифты ────────────────────────────────────────────────────────────
BG       = "#1a3a5c"
FG       = "#ffffff"
ENTRY_BG = "#ffffff"
BTN_BG   = "#2980b9"
FONT     = ("Segoe UI", 11)
FONT_H   = ("Segoe UI", 14, "bold")


class LoginWindow:
    """
    Окно авторизации.
    После успешного входа запускает MainWindow.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Вход — Система учёта иностранных студентов")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self._build()
        self._center()

    # ── построение ────────────────────────────────────────────────────────────

    def _build(self):
        outer = tk.Frame(self.root, bg=BG, padx=50, pady=40)
        outer.pack()

        tk.Label(outer, text="ННГАСУ", bg=BG, fg="#aed6f1",
                 font=("Segoe UI", 10)).pack()
        tk.Label(outer, text="Система учёта иностранных студентов",
                 bg=BG, fg=FG, font=FONT_H, wraplength=340,
                 justify="center").pack(pady=(4, 20))

        frame = tk.Frame(outer, bg=BG)
        frame.pack()

        tk.Label(frame, text="Логин:", bg=BG, fg=FG, font=FONT).grid(
            row=0, column=0, sticky="w", pady=6)
        self._username = ttk.Entry(frame, font=FONT, width=26)
        self._username.grid(row=0, column=1, padx=(10, 0), pady=6)

        tk.Label(frame, text="Пароль:", bg=BG, fg=FG, font=FONT).grid(
            row=1, column=0, sticky="w", pady=6)
        self._password = ttk.Entry(frame, font=FONT, width=26, show="•")
        self._password.grid(row=1, column=1, padx=(10, 0), pady=6)

        self._password.bind("<Return>", lambda _: self._login())

        btn = tk.Button(outer, text="  Войти  ", font=("Segoe UI", 12, "bold"),
                        bg=BTN_BG, fg=FG, activebackground="#1a6fa0",
                        activeforeground=FG, relief="flat", cursor="hand2",
                        command=self._login)
        btn.pack(pady=(20, 4))

        self._status = tk.Label(outer, text="", bg=BG, fg="#e74c3c", font=FONT)
        self._status.pack()

        self._username.focus_set()

    def _center(self):
        self.root.update_idletasks()
        w, h = 440, 340
        x = (self.root.winfo_screenwidth()  - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ── логика входа ──────────────────────────────────────────────────────────

    def _login(self):
        username = self._username.get().strip()
        password = self._password.get()

        if not username or not password:
            self._status.config(text="Введите логин и пароль")
            return

        user = db.get_user_by_username(username)
        if user is None or not user["is_active"]:
            self._status.config(text="Пользователь не найден или отключён")
            return

        if not verify_password(password, user["salt"], user["password_hash"]):
            self._status.config(text="Неверный пароль")
            return

        # успешный вход
        db.log_action(user["id"], "LOGIN", details=f"Вход пользователя {username}")
        self._open_main(dict(user))

    def _open_main(self, user: dict):
        """Закрыть окно входа и открыть главное окно."""
        # скрыть текущее окно
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.configure(bg="#ecf0f1")

        from ui.main_window import MainWindow
        MainWindow(self.root, user)
