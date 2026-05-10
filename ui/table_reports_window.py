"""
Окно табличных отчётов (текстовые сводки по студентам и журналу действий).
"""
import os
import platform
import subprocess
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import database as db
from template_engine import EXPORTS_DIR

FONT = ("Segoe UI", 10)
FONT_H = ("Segoe UI", 11, "bold")


class TableReportsWindow(tk.Toplevel):
    def __init__(self, parent, user: dict, selected_student_ids=None):
        super().__init__(parent)
        self.user = user
        if isinstance(selected_student_ids, int):
            self._preselected = [selected_student_ids]
        elif selected_student_ids:
            self._preselected = list(selected_student_ids)
        else:
            self._preselected = []

        self.title("Табличные отчёты")
        self.geometry("880x660")
        self.grab_set()
        self.resizable(True, True)

        self._build()
        self._load_student_list()
        for sid in self._preselected:
            self._select_student(sid)
        self._center()

    def _build(self):
        tk.Label(
            self,
            text="Табличные отчёты",
            font=("Segoe UI", 13, "bold"),
            bg="#1a3a5c",
            fg="white",
            padx=12,
            pady=8,
        ).pack(fill="x")

        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.LabelFrame(
            main_frame,
            text="Выбор студентов (Ctrl+клик — несколько)",
            padding=6,
        )
        left.pack(side="left", fill="both", expand=True)

        sf = tk.Frame(left)
        sf.pack(fill="x", pady=(0, 4))
        tk.Label(sf, text="Поиск:", font=FONT).pack(side="left")
        self._sv = tk.StringVar()
        self._sv.trace_add("write", lambda *_: self._load_student_list())
        ttk.Entry(sf, textvariable=self._sv, font=FONT, width=20).pack(side="left", padx=4)

        bf = tk.Frame(left)
        bf.pack(fill="x", pady=(0, 4))
        tk.Button(
            bf,
            text="Выбрать всех",
            bg="#546e7a",
            fg="white",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            command=self._select_all_students,
        ).pack(side="left", padx=(0, 4))
        tk.Button(
            bf,
            text="Снять выбор",
            bg="#546e7a",
            fg="white",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            command=self._deselect_all_students,
        ).pack(side="left")
        self._sel_count_lbl = tk.Label(bf, text="", font=("Segoe UI", 8), fg="#2980b9")
        self._sel_count_lbl.pack(side="right")

        lf = tk.Frame(left)
        lf.pack(fill="both", expand=True)
        self._slist = tk.Listbox(lf, font=FONT, selectmode="extended", exportselection=False)
        vsb = ttk.Scrollbar(lf, orient="vertical", command=self._slist.yview)
        self._slist.configure(yscrollcommand=vsb.set)
        self._slist.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")
        self._slist.bind("<<ListboxSelect>>", self._on_list_select)

        right = ttk.LabelFrame(main_frame, text="Действия", padding=10)
        right.pack(side="left", fill="y", padx=(10, 0))

        self._selected_lbl = tk.Label(
            right,
            text="Студенты не выбраны",
            font=("Segoe UI", 9, "italic"),
            fg="#555",
            wraplength=210,
        )
        self._selected_lbl.pack(pady=(0, 10))

        tk.Label(right, text="Табличные отчёты:", font=FONT_H).pack(anchor="w")

        for lbl, color, cmd in [
            ("📊  Все студенты", "#7b68ee", self._report_all),
            ("📊  Только выбранные", "#2980b9", self._report_selected),
            ("📊  Истекающие визы", "#e67e22", self._report_visas),
            ("📊  Журнал действий", "#546e7a", self._report_audit),
        ]:
            tk.Button(
                right,
                text=lbl,
                bg=color,
                fg="white",
                font=FONT,
                relief="flat",
                cursor="hand2",
                width=24,
                pady=5,
                command=cmd,
            ).pack(pady=2)

        ttk.Separator(right).pack(fill="x", pady=8)
        tk.Button(
            right,
            text="📂  Открыть папку exports",
            bg="#ecf0f1",
            fg="#333",
            font=("Segoe UI", 9),
            relief="groove",
            cursor="hand2",
            command=self._open_exports,
        ).pack(pady=2, anchor="w")

        rf = ttk.LabelFrame(self, text="Текстовый отчёт", padding=6)
        rf.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._report_text = tk.Text(rf, font=("Courier New", 9), wrap="none", height=10)
        vsb3 = ttk.Scrollbar(rf, orient="vertical", command=self._report_text.yview)
        hsb3 = ttk.Scrollbar(rf, orient="horizontal", command=self._report_text.xview)
        self._report_text.configure(yscrollcommand=vsb3.set, xscrollcommand=hsb3.set)
        self._report_text.grid(row=0, column=0, sticky="nsew")
        vsb3.grid(row=0, column=1, sticky="ns")
        hsb3.grid(row=1, column=0, sticky="ew")
        rf.rowconfigure(0, weight=1)
        rf.columnconfigure(0, weight=1)

    def _load_student_list(self):
        q = self._sv.get().strip()
        rows = db.search_students(q) if q else db.get_all_students()
        self._students = [dict(r) for r in rows]
        self._slist.delete(0, "end")
        for s in self._students:
            self._slist.insert("end", s["full_name_ru"])
        self._update_sel_label()

    def _select_student(self, sid: int):
        for i, s in enumerate(self._students):
            if s["id"] == sid:
                self._slist.selection_set(i)
                self._slist.see(i)
                break
        self._update_sel_label()

    def _select_all_students(self):
        self._slist.selection_set(0, "end")
        self._update_sel_label()

    def _deselect_all_students(self):
        self._slist.selection_clear(0, "end")
        self._update_sel_label()

    def _on_list_select(self, _=None):
        self._update_sel_label()

    def _update_sel_label(self):
        sel = self._slist.curselection()
        n = len(sel)
        if n == 0:
            self._selected_lbl.config(text="Студенты не выбраны")
            self._sel_count_lbl.config(text="")
        elif n == 1:
            idx = sel[0]
            self._selected_lbl.config(text=self._students[idx]["full_name_ru"])
            self._sel_count_lbl.config(text="Выбран: 1")
        else:
            self._selected_lbl.config(text=f"Выбрано: {n} студентов")
            self._sel_count_lbl.config(text=f"Выбрано: {n}")

    def _get_selected_students(self) -> list:
        return [self._students[i] for i in self._slist.curselection()]

    def _report_all(self):
        rows = db.get_all_students()
        self._show_table_report("ВСЕ СТУДЕНТЫ", rows)

    def _report_selected(self):
        selected = self._get_selected_students()
        if not selected:
            messagebox.showinfo("Выбор", "Выберите студентов слева", parent=self)
            return
        ids = [s["id"] for s in selected]
        rows = db.get_students_by_ids(ids)
        self._show_table_report(f"ВЫБРАННЫЕ СТУДЕНТЫ ({len(rows)})", rows)

    def _show_table_report(self, title: str, rows):
        lines = [
            "=" * 100,
            f"  {title}  |  Сформирован: {datetime.now():%d.%m.%Y %H:%M}",
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
        today = datetime.today()
        rows = db.get_all_students()
        warn = []
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
            f"  ИСТЕКАЮЩИЕ ВИЗЫ (<=30 дней)  |  {datetime.now():%d.%m.%Y %H:%M}",
            "=" * 90,
            f"{'ФИО':<35} {'Гражданство':<18} {'Виза по':<13} {'Осталось':<10}",
            "-" * 90,
        ]
        for delta, r, visa_to in warn:
            mark = "ПРОСРОЧЕНА" if delta < 0 else ("!!!" if delta <= 7 else "")
            lines.append(
                f"{r['full_name_ru']:<35} {r['citizenship']:<18} "
                f"{visa_to:<13} {delta} дн. {mark}"
            )
        if not warn:
            lines.append("  Нет студентов с истекающей визой в ближайшие 30 дней.")
        lines.append("=" * 90)
        self._show_report("\n".join(lines))

    def _report_audit(self):
        if self.user["role"] not in ("admin", "operator"):
            messagebox.showinfo(
                "Доступ", "Только для администраторов/операторов", parent=self
            )
            return
        rows = db.get_audit_log(100)
        lines = [
            "=" * 90,
            f"  ЖУРНАЛ ДЕЙСТВИЙ (последние 100)  |  {datetime.now():%d.%m.%Y %H:%M}",
            "=" * 90,
            f"{'Время':<20} {'Пользователь':<18} {'Действие':<10} "
            f"{'Таблица':<12} {'Подробности':<30}",
            "-" * 90,
        ]
        for r in rows:
            lines.append(
                f"{r['created_at']:<20} {r['username'] or '-':<18} "
                f"{r['action']:<10} {r['table_name'] or '-':<12} {r['details'] or '':<30}"
            )
        self._show_report("\n".join(lines))

    def _show_report(self, text: str):
        self._report_text.config(state="normal")
        self._report_text.delete("1.0", "end")
        self._report_text.insert("1.0", text)
        self._report_text.config(state="disabled")

    @staticmethod
    def _open_path(path: str):
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
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self._open_path(str(EXPORTS_DIR))

    def _center(self):
        self.update_idletasks()
        w, h = 880, 660
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
