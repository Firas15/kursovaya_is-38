"""
Главное окно приложения.
Изменения:
  - Мультивыбор студентов (Ctrl/Shift+клик)
  - Кнопки «Выбрать всех» и «Снять выбор»
  - Отчёты/Шаблоны передают список выбранных id
  - Кнопка Настройки в шапке
"""
import tkinter as tk
from tkinter import ttk, messagebox

import database as db

ROLE_LABELS = {"admin": "Администратор", "operator": "Оператор", "viewer": "Просмотрщик"}

COL_NAMES = {
    "id":            "№",
    "full_name_ru":  "ФИО (кириллица)",
    "birth_date":    "Дата рождения",
    "citizenship":   "Гражданство",
    "doc_info":      "Документ",
    "phone":         "Телефон",
    "education_form":"Форма обучения",
    "created_at":    "Дата записи",
}
COL_WIDTHS = {
    "id": 40, "full_name_ru": 220, "birth_date": 90,
    "citizenship": 100, "doc_info": 140, "phone": 110,
    "education_form": 90, "created_at": 130,
}

HDR_BG  = "#1a3a5c"
HDR_FG  = "#ffffff"
BTN_ADD = "#27ae60"
BTN_EDT = "#2980b9"
BTN_DEL = "#e74c3c"
BTN_REP = "#8e44ad"
FONT    = ("Segoe UI", 10)


class MainWindow:
    def __init__(self, root: tk.Tk, user: dict):
        self.root = root
        self.user = user
        self.role = user["role"]

        w, h = 1280, 720
        root.geometry(f"{w}x{h}")
        root.title("Система учёта иностранных студентов ННГАСУ")
        root.minsize(900, 560)
        self._center(w, h)

        if self.role == "admin":
            self._build_admin_view()
        else:
            self._build_student_view()

    def _center(self, w, h):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _make_btn(self, parent, text, color, cmd, width=16):
        return tk.Button(parent, text=text, bg=color, fg="white",
            activebackground=color, activeforeground="white",
            font=("Segoe UI", 9, "bold"), relief="flat",
            cursor="hand2", width=width, pady=5, command=cmd)

    def _build_admin_view(self):
        from ui.admin_panel import AdminPanel
        AdminPanel(self.root, self.user, self._logout)

    def _build_student_view(self):
        # ── верхняя панель ────────────────────────────────────────────────────
        top = tk.Frame(self.root, bg=HDR_BG, height=52)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="  Учёт иностранных студентов  ",
                 bg=HDR_BG, fg=HDR_FG,
                 font=("Segoe UI", 13, "bold")).pack(side="left")

        role_lbl = ROLE_LABELS.get(self.role, self.role)
        tk.Label(top, text=f"  {self.user['full_name']}  [{role_lbl}]",
                 bg=HDR_BG, fg="#aed6f1", font=FONT).pack(side="left")

        tk.Button(top, text="Выйти", bg="#c0392b", fg="white",
                  font=FONT, relief="flat", cursor="hand2",
                  command=self._logout).pack(side="right", padx=6)

        tk.Button(top, text="⚙ Настройки", bg="#2c3e50", fg="white",
                  font=FONT, relief="flat", cursor="hand2",
                  command=self._open_settings).pack(side="right", padx=4)

        # ── строка поиска ─────────────────────────────────────────────────────
        search_bar = tk.Frame(self.root, bg="#dde3ec", pady=6)
        search_bar.pack(fill="x")

        tk.Label(search_bar, text="  Поиск:", bg="#dde3ec", font=FONT).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._load_students())
        ttk.Entry(search_bar, textvariable=self._search_var,
                  font=FONT, width=36).pack(side="left", padx=4)
        tk.Label(search_bar,
                 text="(по фамилии, номеру документа, гражданству)",
                 bg="#dde3ec", fg="#555", font=("Segoe UI", 9)).pack(side="left")

        # ── кнопки действий ───────────────────────────────────────────────────
        btn_bar = tk.Frame(self.root, bg="#ecf0f1", pady=6)
        btn_bar.pack(fill="x")

        if self.role == "operator":
            self._make_btn(btn_bar, "➕  Добавить", BTN_ADD,
                           self._add_student).pack(side="left", padx=6)
            self._make_btn(btn_bar, "✏️  Редактировать", BTN_EDT,
                           self._edit_student).pack(side="left", padx=2)
            self._make_btn(btn_bar, "🗑  Удалить", BTN_DEL,
                           self._delete_student).pack(side="left", padx=2)

        self._make_btn(btn_bar, "📄  Отчёты / Экспорт", BTN_REP,
                       self._open_reports, width=20).pack(side="left", padx=6)
        self._make_btn(btn_bar, "📝  Шаблоны Word", "#8e44ad",
                       self._open_templates, width=16).pack(side="left", padx=2)

        # кнопки мультивыбора
        tk.Button(btn_bar, text="☑ Выбрать всех", bg="#546e7a", fg="white",
                  font=("Segoe UI", 9), relief="flat", cursor="hand2",
                  pady=5, padx=8,
                  command=self._select_all).pack(side="left", padx=(10, 2))
        tk.Button(btn_bar, text="☐ Снять выбор", bg="#546e7a", fg="white",
                  font=("Segoe UI", 9), relief="flat", cursor="hand2",
                  pady=5, padx=8,
                  command=self._deselect_all).pack(side="left", padx=2)

        self._make_btn(btn_bar, "🔄  Обновить", "#546e7a",
                       self._load_students, width=12).pack(side="left", padx=6)

        self._count_lbl = tk.Label(btn_bar, text="", bg="#ecf0f1",
                                   fg="#555", font=FONT)
        self._count_lbl.pack(side="right", padx=12)

        # ── таблица (мультивыбор: extended) ───────────────────────────────────
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        cols = list(COL_NAMES.keys())
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                  selectmode="extended")   # ← мультивыбор

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=24, font=FONT)

        for c in cols:
            self._tree.heading(c, text=COL_NAMES[c],
                               command=lambda _c=c: self._sort_by(_c))
            self._tree.column(c, width=COL_WIDTHS.get(c, 100),
                              stretch=(c == "full_name_ru"))

        self._tree.tag_configure("odd",  background="#f8f9fa")
        self._tree.tag_configure("even", background="#ffffff")
        self._tree.tag_configure("selected_row", background="#aed6f1")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self._tree.bind("<Double-1>", lambda _: self._edit_student())
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # ── строка статуса ────────────────────────────────────────────────────
        self._status = tk.Label(self.root, text="Готово", anchor="w",
                                bg="#dde3ec", fg="#333", font=("Segoe UI", 9),
                                padx=8)
        self._status.pack(fill="x", side="bottom")

        self._sort_col = None
        self._sort_rev = False
        self._load_students()

    # ── данные ────────────────────────────────────────────────────────────────

    def _load_students(self):
        q = self._search_var.get().strip() if hasattr(self, "_search_var") else ""
        rows = db.search_students(q) if q else db.get_all_students()

        self._tree.delete(*self._tree.get_children())
        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self._tree.insert("", "end", iid=str(row["id"]),
                              values=[row[c] for c in COL_NAMES.keys()],
                              tags=(tag,))

        n = len(rows)
        self._count_lbl.config(text=f"Записей: {n}")
        self._status.config(text=f"Загружено {n} записей  |  Ctrl+клик или Shift+клик для выбора нескольких")

    def _on_select(self, _=None):
        sel = self._tree.selection()
        n = len(sel)
        if n > 1:
            self._status.config(text=f"Выбрано: {n} записей")
        elif n == 1:
            self._status.config(text="Выбрана 1 запись")

    def _selected_ids(self) -> list:
        return [int(iid) for iid in self._tree.selection()]

    def _select_all(self):
        self._tree.selection_set(self._tree.get_children())

    def _deselect_all(self):
        self._tree.selection_remove(self._tree.get_children())

    def _sort_by(self, col):
        items = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        rev = (self._sort_col == col) and not self._sort_rev
        items.sort(reverse=rev)
        for idx, (_, k) in enumerate(items):
            self._tree.move(k, "", idx)
            tag = "even" if idx % 2 == 0 else "odd"
            self._tree.item(k, tags=(tag,))
        self._sort_col = col
        self._sort_rev = rev

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add_student(self):
        from ui.student_form import StudentForm
        StudentForm(self.root, self.user, student_id=None, on_save=self._load_students)

    def _edit_student(self):
        ids = self._selected_ids()
        if not ids:
            messagebox.showinfo("Выбор", "Выберите запись в таблице", parent=self.root)
            return
        sid = ids[0]   # редактируем первую выбранную
        readonly = (self.role == "viewer")
        from ui.student_form import StudentForm
        StudentForm(self.root, self.user, student_id=sid,
                    readonly=readonly, on_save=self._load_students)

    def _delete_student(self):
        ids = self._selected_ids()
        if not ids:
            messagebox.showinfo("Выбор", "Выберите запись(и)", parent=self.root)
            return
        word = f"{len(ids)} записей" if len(ids) > 1 else "1 запись"
        if not messagebox.askyesno("Удаление",
                                   f"Удалить {word}?\nОтменить нельзя.",
                                   parent=self.root):
            return
        for sid in ids:
            ok, msg = db.delete_student(sid)
            if ok:
                db.log_action(self.user["id"], "DELETE", "students", sid)
        self._status.config(text=f"Удалено: {len(ids)}")
        self._load_students()

    def _open_reports(self):
        from ui.reports_window import ReportsWindow
        ids = self._selected_ids()
        ReportsWindow(self.root, self.user, selected_student_ids=ids)

    def _open_templates(self):
        from ui.templates_window import TemplatesWindow
        ids = self._selected_ids()
        TemplatesWindow(self.root, self.user,
                        selected_student_id=ids[0] if ids else None)

    def _open_settings(self):
        from ui.settings_window import SettingsWindow
        SettingsWindow(self.root)

    # ── выход ─────────────────────────────────────────────────────────────────

    def _logout(self):
        db.log_action(self.user["id"], "LOGOUT",
                      details=f"Выход: {self.user['username']}")
        for w in self.root.winfo_children():
            w.destroy()
        self.root.configure(bg="#1a3a5c")
        from ui.login_window import LoginWindow
        LoginWindow(self.root)
