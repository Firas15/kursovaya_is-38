"""
Панель администратора.
Администратор может только: создавать, редактировать, деактивировать пользователей.
Доступ к данным студентов у администратора НЕТ.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import database as db

FONT   = ("Segoe UI", 10)
FONT_H = ("Segoe UI", 11, "bold")
HDR_BG = "#1a3a5c"
HDR_FG = "#ffffff"

ROLE_LABELS = {"admin": "Администратор", "operator": "Оператор",
               "viewer": "Просмотрщик"}
ROLE_VALS   = ["admin", "operator", "viewer"]


class AdminPanel:
    def __init__(self, root: tk.Tk, user: dict, logout_cb):
        self.root      = root
        self.user      = user
        self.logout_cb = logout_cb
        self._build()
        self._load()

    # ── построение ────────────────────────────────────────────────────────────

    def _build(self):
        # верхняя полоса
        top = tk.Frame(self.root, bg=HDR_BG, height=52)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="  Администрирование пользователей  ",
                 bg=HDR_BG, fg=HDR_FG, font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Label(top, text=f"  {self.user['full_name']}  [Администратор]",
                 bg=HDR_BG, fg="#aed6f1", font=FONT).pack(side="left")
        tk.Button(top, text="Выйти", bg="#c0392b", fg="white",
                  activebackground="#a93226", activeforeground="white",
                  font=FONT, relief="flat", cursor="hand2",
                  command=self.logout_cb).pack(side="right", padx=10)

        # справка
        info = tk.Label(self.root,
                        text="Администратор управляет только учётными записями пользователей. "
                             "Максимум активных пользователей: 10.",
                        bg="#fff3cd", fg="#856404", font=("Segoe UI", 9),
                        padx=10, pady=6, anchor="w")
        info.pack(fill="x")

        # кнопки
        btn_bar = tk.Frame(self.root, bg="#ecf0f1", pady=6)
        btn_bar.pack(fill="x")

        for text, color, cmd in [
            ("➕  Создать пользователя", "#27ae60", self._create_user),
            ("✏️  Редактировать",         "#2980b9", self._edit_user),
            ("🔒  Деактивировать",        "#e74c3c", self._deactivate_user),
        ]:
            tk.Button(btn_bar, text=text, bg=color, fg="white",
                      activebackground=color, activeforeground="white",
                      font=("Segoe UI", 9, "bold"), relief="flat",
                      cursor="hand2", padx=10, pady=5,
                      command=cmd).pack(side="left", padx=6)

        tk.Button(btn_bar, text="🔄  Обновить", bg="#546e7a", fg="white",
                  font=FONT, relief="flat", cursor="hand2",
                  padx=8, pady=5,
                  command=self._load).pack(side="left", padx=4)

        self._count_lbl = tk.Label(btn_bar, text="", bg="#ecf0f1",
                                   fg="#555", font=FONT)
        self._count_lbl.pack(side="right", padx=12)

        # таблица
        cols = ("id", "username", "full_name", "role", "status", "created_at")
        col_heads = {"id":"ID","username":"Логин","full_name":"ФИО",
                     "role":"Роль","status":"Статус","created_at":"Создан"}
        col_w    = {"id":40,"username":110,"full_name":200,
                    "role":110,"status":70,"created_at":150}

        frm = tk.Frame(self.root)
        frm.pack(fill="both", expand=True, padx=8, pady=(4,0))

        self._tree = ttk.Treeview(frm, columns=cols, show="headings",
                                  selectmode="browse")
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=24, font=FONT)

        for c in cols:
            self._tree.heading(c, text=col_heads[c])
            self._tree.column(c, width=col_w.get(c, 100),
                              stretch=(c == "full_name"))

        self._tree.tag_configure("inactive", foreground="#999")
        self._tree.tag_configure("admin",    foreground="#8e44ad")

        vsb = ttk.Scrollbar(frm, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        frm.rowconfigure(0, weight=1)
        frm.columnconfigure(0, weight=1)

        self._tree.bind("<Double-1>", lambda _: self._edit_user())

        # справочник стран (бонус для admin)
        self._build_countries_frame()

        # статус
        self._status = tk.Label(self.root, text="Готово", anchor="w",
                                bg="#dde3ec", fg="#333", font=("Segoe UI", 9),
                                padx=8)
        self._status.pack(fill="x", side="bottom")

    def _build_countries_frame(self):
        """Управление справочником гражданств."""
        lf = ttk.LabelFrame(self.root, text="Справочник: Страны / Гражданство",
                             padding=8)
        lf.pack(fill="x", padx=8, pady=6)

        self._clist = tk.Listbox(lf, font=FONT, height=5, selectmode="single",
                                 exportselection=False)
        self._clist.pack(side="left", fill="both", expand=True)
        vsb2 = ttk.Scrollbar(lf, orient="vertical", command=self._clist.yview)
        self._clist.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="left", fill="y")

        btn_frame = tk.Frame(lf)
        btn_frame.pack(side="left", padx=8)

        tk.Button(btn_frame, text="Добавить", bg="#27ae60", fg="white",
                  font=FONT, relief="flat", cursor="hand2", width=14,
                  command=self._add_country).pack(pady=3)
        tk.Button(btn_frame, text="Удалить", bg="#e74c3c", fg="white",
                  font=FONT, relief="flat", cursor="hand2", width=14,
                  command=self._del_country).pack(pady=3)
        tk.Button(btn_frame, text="Обновить", bg="#546e7a", fg="white",
                  font=FONT, relief="flat", cursor="hand2", width=14,
                  command=self._load_countries).pack(pady=3)

        self._load_countries()

    # ── данные ────────────────────────────────────────────────────────────────

    def _load(self):
        self._tree.delete(*self._tree.get_children())
        rows = db.get_all_users()
        for i, r in enumerate(rows):
            status = "Активен" if r["is_active"] else "Отключён"
            tag = "inactive" if not r["is_active"] else (
                  "admin" if r["role"] == "admin" else "")
            self._tree.insert("", "end", iid=str(r["id"]),
                              values=(r["id"], r["username"], r["full_name"],
                                      ROLE_LABELS.get(r["role"], r["role"]),
                                      status, r["created_at"]),
                              tags=(tag,))
        active = sum(1 for r in rows if r["is_active"])
        self._count_lbl.config(text=f"Активных: {active} / 10")

    def _load_countries(self):
        self._clist.delete(0, "end")
        for r in db.get_all_countries():
            self._clist.insert("end", f"{r['name_ru']}  /  {r['name_lat'] or '—'}")
        self._countries = db.get_all_countries()

    def _selected_id(self):
        sel = self._tree.selection()
        return int(sel[0]) if sel else None

    # ── пользователи ──────────────────────────────────────────────────────────

    def _create_user(self):
        _UserDialog(self.root, self.user, on_save=self._load)

    def _edit_user(self):
        uid = self._selected_id()
        if uid is None:
            messagebox.showinfo("Выбор", "Выберите пользователя", parent=self.root)
            return
        rows = db.get_all_users()
        target = next((r for r in rows if r["id"] == uid), None)
        if target:
            _UserDialog(self.root, self.user, existing=dict(target),
                        on_save=self._load)

    def _deactivate_user(self):
        uid = self._selected_id()
        if uid is None:
            messagebox.showinfo("Выбор", "Выберите пользователя", parent=self.root)
            return
        if uid == self.user["id"]:
            messagebox.showwarning("Ошибка", "Нельзя деактивировать себя",
                                   parent=self.root)
            return
        if not messagebox.askyesno("Подтверждение",
                                   "Деактивировать пользователя?",
                                   parent=self.root):
            return
        ok, msg = db.update_user(uid, "", "", 0)
        # получаем актуальные данные
        rows = db.get_all_users()
        target = next((r for r in rows if r["id"] == uid), None)
        if target:
            ok, msg = db.update_user(uid, target["full_name"],
                                     target["role"], 0)
        if ok:
            self._status.config(text="Пользователь деактивирован")
            self._load()
        else:
            messagebox.showerror("Ошибка", msg, parent=self.root)

    # ── страны ────────────────────────────────────────────────────────────────

    def _add_country(self):
        name = simpledialog.askstring("Добавить страну",
                                      "Название на русском:",
                                      parent=self.root)
        if not name:
            return
        lat = simpledialog.askstring("Добавить страну",
                                     "Название на латинице (необязательно):",
                                     parent=self.root) or ""
        ok, msg = db.add_country(name.strip(), lat.strip())
        messagebox.showinfo("Результат", msg, parent=self.root)
        self._load_countries()

    def _del_country(self):
        sel = self._clist.curselection()
        if not sel:
            messagebox.showinfo("Выбор", "Выберите страну", parent=self.root)
            return
        idx = sel[0]
        if idx >= len(self._countries):
            return
        c = self._countries[idx]
        if not messagebox.askyesno("Удаление",
                                   f"Удалить «{c['name_ru']}»?",
                                   parent=self.root):
            return
        ok, msg = db.delete_country(c["id"])
        messagebox.showinfo("Результат", msg, parent=self.root)
        self._load_countries()


# ── диалог создания / редактирования пользователя ────────────────────────────

class _UserDialog(tk.Toplevel):
    def __init__(self, parent, current_user: dict,
                 existing: dict = None, on_save=None):
        super().__init__(parent)
        self.current_user = current_user
        self.existing     = existing
        self.on_save      = on_save

        self.title("Создать пользователя" if not existing else "Редактировать")
        self.grab_set()
        self.resizable(False, False)

        self._build()
        if existing:
            self._fill(existing)
        self._center()

    def _build(self):
        f = tk.Frame(self, padx=20, pady=16)
        f.pack()

        for row, (lbl, attr) in enumerate([
            ("Логин *",      "_v_uname"),
            ("ФИО *",        "_v_fname"),
            ("Пароль *",     "_v_pass"),
            ("Повтор пароля","_v_pass2"),
        ]):
            setattr(self, attr, tk.StringVar())
            tk.Label(f, text=lbl, font=FONT, anchor="e", width=14).grid(
                row=row, column=0, sticky="e", pady=5)
            show = "•" if "Пароль" in lbl else ""
            ttk.Entry(f, textvariable=getattr(self, attr),
                      font=FONT, width=26, show=show).grid(
                row=row, column=1, padx=6)

        tk.Label(f, text="Роль *", font=FONT, anchor="e", width=14).grid(
            row=4, column=0, sticky="e", pady=5)
        self._v_role = tk.StringVar(value="viewer")
        ttk.Combobox(f, textvariable=self._v_role,
                     values=["admin","operator","viewer"],
                     font=FONT, width=24, state="readonly"
                     ).grid(row=4, column=1, padx=6)

        tk.Label(f, text="Активен", font=FONT, anchor="e", width=14).grid(
            row=5, column=0, sticky="e", pady=5)
        self._v_active = tk.IntVar(value=1)
        ttk.Checkbutton(f, variable=self._v_active).grid(
            row=5, column=1, sticky="w", padx=6)

        if self.existing:
            tk.Label(f, text="(оставьте пустым, чтобы\nне менять пароль)",
                     font=("Segoe UI", 8), fg="#888"
                     ).grid(row=3, column=2, sticky="w")

        self._err = tk.Label(f, text="", fg="#e74c3c", font=FONT)
        self._err.grid(row=6, column=0, columnspan=3, pady=4)

        btn_bar = tk.Frame(f)
        btn_bar.grid(row=7, column=0, columnspan=3)
        tk.Button(btn_bar, text="Сохранить", bg="#27ae60", fg="white",
                  font=FONT, relief="flat", padx=12, pady=5,
                  command=self._save).pack(side="left", padx=6)
        tk.Button(btn_bar, text="Отмена", bg="#7f8c8d", fg="white",
                  font=FONT, relief="flat", padx=10, pady=5,
                  command=self.destroy).pack(side="left")

    def _fill(self, u: dict):
        self._v_uname.set(u.get("username",""))
        self._v_fname.set(u.get("full_name",""))
        self._v_role.set(u.get("role","viewer"))
        self._v_active.set(int(u.get("is_active",1)))
        # логин менять нельзя если редактируем существующего
        # (можно запретить редактирование Entry)

    def _save(self):
        uname  = self._v_uname.get().strip()
        fname  = self._v_fname.get().strip()
        role   = self._v_role.get()
        active = self._v_active.get()
        pw     = self._v_pass.get()
        pw2    = self._v_pass2.get()

        if not uname or not fname:
            self._err.config(text="Логин и ФИО обязательны")
            return

        if not self.existing and not pw:
            self._err.config(text="Пароль обязателен для нового пользователя")
            return

        if pw and pw != pw2:
            self._err.config(text="Пароли не совпадают")
            return

        if pw and len(pw) < 6:
            self._err.config(text="Пароль должен содержать ≥ 6 символов")
            return

        if self.existing:
            ok, msg = db.update_user(
                self.existing["id"], fname, role, active,
                pw if pw else None)
        else:
            ok, msg = db.create_user(uname, pw, fname, role)

        if ok:
            messagebox.showinfo("Готово", msg, parent=self)
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            self._err.config(text=msg)

    def _center(self):
        self.update_idletasks()
        w, h = 460, 360
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
