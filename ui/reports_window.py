"""
Окно отчётов и экспорта документов.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import platform
from datetime import datetime

import database as db

FONT   = ("Segoe UI", 10)
FONT_H = ("Segoe UI", 11, "bold")


class ReportsWindow(tk.Toplevel):
    def __init__(self, parent, user: dict, selected_student_id=None):
        super().__init__(parent)
        self.user               = user
        self.selected_student_id = selected_student_id

        self.title("Отчёты и экспорт документов")
        self.geometry("820x620")
        self.grab_set()
        self.resizable(True, True)

        self._build()
        self._load_student_list()
        if selected_student_id:
            self._select_student(selected_student_id)
        self._center()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self):
        # заголовок
        tk.Label(self, text="Отчёты и экспорт в Word",
                 font=("Segoe UI", 13, "bold"),
                 bg="#1a3a5c", fg="white", padx=12, pady=8
                 ).pack(fill="x")

        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ── левая панель: список студентов ────────────────────────────────────
        left = ttk.LabelFrame(main_frame, text="Выбор студента", padding=6)
        left.pack(side="left", fill="both", expand=True)

        search_f = tk.Frame(left)
        search_f.pack(fill="x", pady=(0, 4))
        tk.Label(search_f, text="Поиск:", font=FONT).pack(side="left")
        self._sv = tk.StringVar()
        self._sv.trace_add("write", lambda *_: self._load_student_list())
        ttk.Entry(search_f, textvariable=self._sv, font=FONT, width=22).pack(side="left", padx=4)

        self._slist = tk.Listbox(left, font=FONT, selectmode="single",
                                 exportselection=False)
        vsb = ttk.Scrollbar(left, orient="vertical", command=self._slist.yview)
        self._slist.configure(yscrollcommand=vsb.set)
        self._slist.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")
        self._slist.bind("<<ListboxSelect>>", self._on_select)

        # ── правая панель: отчёты ─────────────────────────────────────────────
        right = ttk.LabelFrame(main_frame, text="Действия", padding=10)
        right.pack(side="left", fill="y", padx=(10, 0))

        self._selected_lbl = tk.Label(right, text="Студент не выбран",
                                      font=("Segoe UI", 9, "italic"),
                                      fg="#555", wraplength=200)
        self._selected_lbl.pack(pady=(0, 12))

        ttk.Separator(right).pack(fill="x", pady=4)
        tk.Label(right, text="Word-документы:", font=FONT_H).pack(anchor="w")

        for lbl, color, cmd in [
            ("📋  Справка (для МВД)",         "#1a6fa0", self._gen_spravka),
            ("📋  Визовая анкета",             "#1a6fa0", self._gen_visa_anketa),
        ]:
            tk.Button(right, text=lbl, bg=color, fg="white",
                      activebackground=color, activeforeground="white",
                      font=FONT, relief="flat", cursor="hand2",
                      width=24, pady=6, command=cmd).pack(pady=4)

        ttk.Separator(right).pack(fill="x", pady=8)
        tk.Label(right, text="Табличные отчёты:", font=FONT_H).pack(anchor="w")

        for lbl, color, cmd in [
            ("📊  Все студенты (таблица)",     "#7b68ee", self._report_all),
            ("📊  Истекающие визы (< 30 дн.)", "#e67e22", self._report_visas),
            ("📊  Журнал действий",            "#546e7a", self._report_audit),
        ]:
            tk.Button(right, text=lbl, bg=color, fg="white",
                      activebackground=color, activeforeground="white",
                      font=FONT, relief="flat", cursor="hand2",
                      width=24, pady=6, command=cmd).pack(pady=3)

        ttk.Separator(right).pack(fill="x", pady=8)
        tk.Label(right, text="Папка экспорта:", font=("Segoe UI", 9)).pack(anchor="w")
        tk.Button(right, text="📂  Открыть папку exports",
                  bg="#ecf0f1", fg="#333", font=("Segoe UI", 9),
                  relief="groove", cursor="hand2",
                  command=self._open_exports).pack(pady=2, anchor="w")

        # ── нижняя область: просмотр текстового отчёта ────────────────────────
        report_frame = ttk.LabelFrame(self, text="Текстовый отчёт", padding=6)
        report_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._report_text = tk.Text(report_frame, font=("Courier New", 9),
                                    wrap="none", height=12)
        vsb3 = ttk.Scrollbar(report_frame, orient="vertical",
                              command=self._report_text.yview)
        hsb3 = ttk.Scrollbar(report_frame, orient="horizontal",
                              command=self._report_text.xview)
        self._report_text.configure(yscrollcommand=vsb3.set,
                                    xscrollcommand=hsb3.set)
        self._report_text.grid(row=0, column=0, sticky="nsew")
        vsb3.grid(row=0, column=1, sticky="ns")
        hsb3.grid(row=1, column=0, sticky="ew")
        report_frame.rowconfigure(0, weight=1)
        report_frame.columnconfigure(0, weight=1)

    # ── список студентов ──────────────────────────────────────────────────────

    def _load_student_list(self):
        q = self._sv.get().strip()
        rows = db.search_students(q) if q else db.get_all_students()
        self._students = [dict(r) for r in rows]
        self._slist.delete(0, "end")
        for s in self._students:
            self._slist.insert("end", s["full_name_ru"])

    def _select_student(self, sid: int):
        for i, s in enumerate(self._students):
            if s["id"] == sid:
                self._slist.selection_set(i)
                self._slist.see(i)
                self._current_student = db.get_student_by_id(sid)
                self._current_country = self._get_country_name(self._current_student)
                self._selected_lbl.config(text=self._students[i]["full_name_ru"])
                break

    def _on_select(self, _=None):
        sel = self._slist.curselection()
        if not sel:
            return
        idx = sel[0]
        sid = self._students[idx]["id"]
        self._current_student = db.get_student_by_id(sid)
        self._current_country = self._get_country_name(self._current_student)
        self._selected_lbl.config(text=self._students[idx]["full_name_ru"])

    @staticmethod
    def _get_country_name(student) -> str:
        if student is None:
            return ""
        cid = student["country_id"]
        if not cid:
            return ""
        for c in db.get_all_countries():
            if c["id"] == cid:
                return c["name_ru"]
        return ""

    def _require_student(self) -> bool:
        if not hasattr(self, "_current_student") or self._current_student is None:
            messagebox.showinfo("Выбор", "Выберите студента из списка слева",
                                parent=self)
            return False
        return True

    # ── экспорт Word ──────────────────────────────────────────────────────────

    def _gen_spravka(self):
        if not self._require_student():
            return
        try:
            from word_templates import generate_spravka, check_docx_available
            if not check_docx_available():
                messagebox.showerror("Ошибка",
                    "Библиотека python-docx не установлена.\n"
                    "Выполните: pip install python-docx",
                    parent=self)
                return
            path = generate_spravka(dict(self._current_student),
                                    self._current_country)
            if path:
                messagebox.showinfo("Готово",
                    f"Файл сохранён:\n{path}\n\nОткрыть?",
                    parent=self)
                self._open_file(path)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def _gen_visa_anketa(self):
        if not self._require_student():
            return
        try:
            from word_templates import generate_visa_anketa, check_docx_available
            if not check_docx_available():
                messagebox.showerror("Ошибка",
                    "Библиотека python-docx не установлена.\n"
                    "Выполните: pip install python-docx",
                    parent=self)
                return
            path = generate_visa_anketa(dict(self._current_student),
                                        self._current_country)
            if path:
                messagebox.showinfo("Готово",
                    f"Файл сохранён:\n{path}\n\nОткрыть?",
                    parent=self)
                self._open_file(path)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    # ── текстовые отчёты ──────────────────────────────────────────────────────

    def _report_all(self):
        rows = db.get_all_students()
        lines = [
            "=" * 100,
            f"  ОТЧЁТ: ВСЕ СТУДЕНТЫ  |  Сформирован: {datetime.now():%d.%m.%Y %H:%M}",
            "=" * 100,
            f"{'№':<5} {'ФИО':<35} {'Дата рожд.':<13} {'Гражданство':<18} "
            f"{'Документ':<25} {'Форма обучения':<14}",
            "-" * 100,
        ]
        for i, r in enumerate(rows, 1):
            lines.append(
                f"{i:<5} {r['full_name_ru']:<35} {r['birth_date']:<13} "
                f"{r['citizenship']:<18} {r['doc_info']:<25} {r['education_form']:<14}"
            )
        lines += ["=" * 100, f"Итого: {len(rows)} записей"]
        self._show_report("\n".join(lines))

    def _report_visas(self):
        """Студенты с визой, истекающей в ближайшие 30 дней."""
        today = datetime.today()
        rows  = db.get_all_students()
        warn  = []
        for r in rows:
            s = db.get_student_by_id(r["id"])
            visa_to = s["visa_valid_to"] if s else None
            if visa_to:
                try:
                    dt = datetime.strptime(visa_to, "%d.%m.%Y")
                    delta = (dt - today).days
                    if delta <= 30:
                        warn.append((delta, dict(r), visa_to))
                except ValueError:
                    pass
        warn.sort()
        lines = [
            "=" * 90,
            f"  ОТЧЁТ: ИСТЕКАЮЩИЕ ВИЗЫ (≤ 30 дней)  |  {datetime.now():%d.%m.%Y %H:%M}",
            "=" * 90,
            f"{'ФИО':<35} {'Гражданство':<18} {'Виза по':<13} {'Осталось дней':<14}",
            "-" * 90,
        ]
        for delta, r, visa_to in warn:
            mark = "❗" if delta < 0 else ("⚠️" if delta <= 7 else "")
            lines.append(
                f"{r['full_name_ru']:<35} {r['citizenship']:<18} "
                f"{visa_to:<13} {delta} {mark}"
            )
        if not warn:
            lines.append("  Нет студентов с истекающей визой в ближайшие 30 дней.")
        lines.append("=" * 90)
        self._show_report("\n".join(lines))

    def _report_audit(self):
        if self.user["role"] not in ("admin", "operator"):
            messagebox.showinfo("Доступ", "Только для администраторов/операторов",
                                parent=self)
            return
        rows = db.get_audit_log(100)
        lines = [
            "=" * 90,
            f"  ЖУРНАЛ ДЕЙСТВИЙ (последние 100)  |  {datetime.now():%d.%m.%Y %H:%M}",
            "=" * 90,
            f"{'Время':<20} {'Пользователь':<18} {'Действие':<10} "
            f"{'Таблица':<12} {'ID':<6} {'Подробности':<30}",
            "-" * 90,
        ]
        for r in rows:
            lines.append(
                f"{r['created_at']:<20} {r['username'] or '—':<18} "
                f"{r['action']:<10} {r['table_name'] or '—':<12} "
                f"{r['record_id'] or '—'!s:<6} {r['details'] or '':<30}"
            )
        self._show_report("\n".join(lines))

    def _show_report(self, text: str):
        self._report_text.config(state="normal")
        self._report_text.delete("1.0", "end")
        self._report_text.insert("1.0", text)
        self._report_text.config(state="disabled")

    # ── утилиты ───────────────────────────────────────────────────────────────

    @staticmethod
    def _open_file(path: str):
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def _open_exports(self):
        from pathlib import Path
        exports = Path(__file__).parent.parent / "exports"
        exports.mkdir(exist_ok=True)
        self._open_file(str(exports))

    def _center(self):
        self.update_idletasks()
        w, h = 820, 620
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
