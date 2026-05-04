"""
Окно управления Word-шаблонами.
Позволяет добавлять, удалять и применять пользовательские шаблоны.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

import database as db
from template_engine import (
    get_all_templates, add_template, delete_template,
    fill_template, open_templates_folder, create_example_template,
    ensure_bundled_word_templates,
    TEMPLATES_DIR,
)

FONT   = ("Segoe UI", 10)
FONT_H = ("Segoe UI", 11, "bold")


class TemplatesWindow(tk.Toplevel):
    def __init__(self, parent, user: dict, selected_student_id=None):
        super().__init__(parent)
        self.user = user
        self.selected_student_id = selected_student_id

        self.title("Шаблоны Word-документов")
        self.geometry("900x600")
        self.grab_set()
        self.resizable(True, True)

        ensure_bundled_word_templates()
        create_example_template()

        self._build()
        self._load_templates()
        self._load_students()
        if selected_student_id:
            self._select_student(selected_student_id)
        self._center()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self):
        tk.Label(self, text="Шаблоны Word-документов",
                 font=("Segoe UI", 13, "bold"),
                 bg="#1a3a5c", fg="white", padx=12, pady=8
                 ).pack(fill="x")

        # подсказка
        hint = tk.Label(self,
            text="  Создайте .docx файл с метками {{поле}} → добавьте как шаблон → выберите студента → сгенерируйте",
            bg="#d4edda", fg="#155724", font=("Segoe UI", 9), pady=5, anchor="w", padx=10)
        hint.pack(fill="x")

        main = tk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=8)

        # ── левая: шаблоны ────────────────────────────────────────────────────
        left = ttk.LabelFrame(main, text="Шаблоны (папка templates/)", padding=6)
        left.pack(side="left", fill="both", expand=True)

        # кнопки управления шаблонами
        btn_f = tk.Frame(left)
        btn_f.pack(fill="x", pady=(0, 6))

        for text, color, cmd in [
            ("➕ Добавить .docx",    "#27ae60", self._add_template),
            ("🗑 Удалить",           "#e74c3c", self._delete_template),
            ("📂 Открыть папку",     "#546e7a", self._open_folder),
            ("📋 Список меток",      "#2980b9", self._show_markers),
        ]:
            tk.Button(btn_f, text=text, bg=color, fg="white",
                      font=("Segoe UI", 9), relief="flat", cursor="hand2",
                      padx=6, pady=4, command=cmd).pack(side="left", padx=3)

        # список шаблонов
        cols = ("name", "filename", "modified")
        self._tpl_tree = ttk.Treeview(left, columns=cols, show="headings",
                                      selectmode="browse", height=8)
        self._tpl_tree.heading("name",     text="Название")
        self._tpl_tree.heading("filename", text="Файл")
        self._tpl_tree.heading("modified", text="Изменён")
        self._tpl_tree.column("name",     width=160)
        self._tpl_tree.column("filename", width=180)
        self._tpl_tree.column("modified", width=130)

        vsb = ttk.Scrollbar(left, orient="vertical", command=self._tpl_tree.yview)
        self._tpl_tree.configure(yscrollcommand=vsb.set)
        self._tpl_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")

        # ── правая: студенты + действия ───────────────────────────────────────
        right = tk.Frame(main)
        right.pack(side="left", fill="both", padx=(10, 0))

        stud_frame = ttk.LabelFrame(right, text="Выбрать студента", padding=6)
        stud_frame.pack(fill="both", expand=True)

        sv_f = tk.Frame(stud_frame)
        sv_f.pack(fill="x", pady=(0, 4))
        tk.Label(sv_f, text="Поиск:", font=FONT).pack(side="left")
        self._sv = tk.StringVar()
        self._sv.trace_add("write", lambda *_: self._load_students())
        ttk.Entry(sv_f, textvariable=self._sv, font=FONT, width=20).pack(side="left", padx=4)

        self._slist = tk.Listbox(stud_frame, font=FONT, height=10,
                                 selectmode="single", exportselection=False, width=32)
        vsb2 = ttk.Scrollbar(stud_frame, orient="vertical", command=self._slist.yview)
        self._slist.configure(yscrollcommand=vsb2.set)
        self._slist.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="left", fill="y")

        # кнопка генерации
        gen_frame = tk.Frame(right)
        gen_frame.pack(fill="x", pady=8)

        tk.Button(gen_frame,
                  text="▶  Заполнить шаблон\n    данными студента",
                  bg="#1a6fa0", fg="white",
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", cursor="hand2",
                  pady=10, width=22,
                  command=self._generate).pack()

        self._status_lbl = tk.Label(right, text="", font=("Segoe UI", 9),
                                    fg="#27ae60", wraplength=220)
        self._status_lbl.pack()

        # ── нижняя: справка по меткам ─────────────────────────────────────────
        markers_frame = ttk.LabelFrame(self, text="Доступные метки для шаблона", padding=6)
        markers_frame.pack(fill="x", padx=10, pady=(0, 8))

        markers_text = (
            "{{фио}}  {{фамилия}}  {{имя}}  {{отчество}}  {{фамилия_лат}}  {{имя_лат}}  "
            "{{дата_рождения}}  {{день}}  {{месяц}}  {{год}}  {{гражданство}}  "
            "{{тип_документа}}  {{серия_документа}}  {{номер_документа}}  "
            "{{документ_с}}  {{документ_по}}  {{виза_серия}}  {{виза_номер}}  "
            "{{виза_с}}  {{виза_по}}  {{телефон}}  {{email}}  {{форма_обучения}}  "
            "{{форма_оплаты}}  {{адрес}}  {{дата_прибытия}}  {{работодатель}}  "
            "{{сегодня}}  {{университет}}  {{цасиг}}  {{руководитель}}"
        )
        tk.Label(markers_frame, text=markers_text, font=("Courier New", 8),
                 fg="#2c3e50", wraplength=860, justify="left").pack(anchor="w")

    # ── данные ────────────────────────────────────────────────────────────────

    def _load_templates(self):
        self._tpl_tree.delete(*self._tpl_tree.get_children())
        self._templates = get_all_templates()
        for t in self._templates:
            self._tpl_tree.insert("", "end", iid=t["filename"],
                                  values=(t["name"], t["filename"], t["modified"]))
        if self._templates:
            self._tpl_tree.selection_set(self._templates[0]["filename"])

    def _load_students(self):
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
                break

    # ── управление шаблонами ──────────────────────────────────────────────────

    def _add_template(self):
        path = filedialog.askopenfilename(
            title="Выберите шаблон Word",
            filetypes=[("Word документы", "*.docx")],
            parent=self,
        )
        if not path:
            return
        ok, msg = add_template(path)
        if ok:
            self._load_templates()
            self._status_lbl.config(text=msg, fg="#27ae60")
        else:
            messagebox.showerror("Ошибка", msg, parent=self)

    def _delete_template(self):
        sel = self._tpl_tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Выберите шаблон", parent=self)
            return
        filename = sel[0]
        if not messagebox.askyesno("Удаление",
                                   f"Удалить шаблон «{filename}»?",
                                   parent=self):
            return
        ok, msg = delete_template(filename)
        if ok:
            self._load_templates()
            self._status_lbl.config(text=msg, fg="#e74c3c")
        else:
            messagebox.showerror("Ошибка", msg, parent=self)

    def _open_folder(self):
        open_templates_folder()

    def _show_markers(self):
        """Показать справку по меткам."""
        dlg = tk.Toplevel(self)
        dlg.title("Список всех меток")
        dlg.geometry("540x480")
        dlg.grab_set()

        tk.Label(dlg,
                 text="Вставляйте эти метки в свой .docx шаблон.\n"
                      "При генерации они заменятся данными студента.",
                 font=FONT, pady=8).pack()

        txt = tk.Text(dlg, font=("Courier New", 10), padx=10, pady=8)
        txt.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        markers = [
            ("{{фио}}",              "Полное ФИО кириллицей"),
            ("{{фамилия}}",          "Фамилия (кириллица)"),
            ("{{имя}}",              "Имя (кириллица)"),
            ("{{отчество}}",         "Отчество (кириллица)"),
            ("{{фамилия_лат}}",      "Фамилия (латиница)"),
            ("{{имя_лат}}",          "Имя (латиница)"),
            ("{{фио_лат}}",          "ФИО латиницей"),
            ("{{дата_рождения}}",    "Дата рождения (ДД.ММ.ГГГГ)"),
            ("{{день}}",             "День рождения"),
            ("{{месяц}}",            "Месяц рождения"),
            ("{{год}}",              "Год рождения"),
            ("{{гражданство}}",      "Гражданство (из справочника)"),
            ("{{тип_документа}}",    "Тип документа уд. личности"),
            ("{{серия_документа}}", "Серия документа"),
            ("{{номер_документа}}", "Номер документа"),
            ("{{документ_с}}",       "Документ действителен с"),
            ("{{документ_по}}",      "Документ действителен по"),
            ("{{виза_серия}}",       "Серия визы"),
            ("{{виза_номер}}",       "Номер визы"),
            ("{{виза_с}}",           "Виза действительна с"),
            ("{{виза_по}}",          "Виза действительна по"),
            ("{{телефон}}",          "Номер телефона"),
            ("{{email}}",            "Адрес электронной почты"),
            ("{{форма_обучения}}",   "Форма обучения"),
            ("{{форма_оплаты}}",     "Форма оплаты"),
            ("{{адрес}}",            "Адрес регистрации"),
            ("{{дата_прибытия}}",    "Дата прибытия"),
            ("{{работодатель}}",     "Сведения о работодателе"),
            ("{{дата_работы}}",      "Дата приёма на работу"),
            ("", ""),
            ("{{сегодня}}",          "Текущая дата"),
            ("{{университет}}",      "ННГАСУ"),
            ("{{цасиг}}",            "ЦАСИГ"),
            ("{{руководитель}}",     "Белоус Е.А."),
        ]

        for marker, desc in markers:
            if not marker:
                txt.insert("end", "\n")
                continue
            txt.insert("end", f"  {marker:<25}  —  {desc}\n")

        txt.config(state="disabled")

    # ── генерация ─────────────────────────────────────────────────────────────

    def _generate(self):
        # проверить выбор шаблона
        sel_tpl = self._tpl_tree.selection()
        if not sel_tpl:
            messagebox.showinfo("Шаблон", "Выберите шаблон из списка", parent=self)
            return

        # проверить выбор студента
        sel_stu = self._slist.curselection()
        if not sel_stu:
            messagebox.showinfo("Студент", "Выберите студента из списка", parent=self)
            return

        filename   = sel_tpl[0]
        tpl_path   = str(TEMPLATES_DIR / filename)
        student_id = self._students[sel_stu[0]]["id"]

        student = db.get_student_by_id(student_id)
        if not student:
            messagebox.showerror("Ошибка", "Студент не найден", parent=self)
            return

        # определить гражданство
        country_name = ""
        cid = student["country_id"]
        if cid:
            for c in db.get_all_countries():
                if c["id"] == cid:
                    country_name = c["name_ru"]
                    break

        try:
            out_path = fill_template(tpl_path, dict(student), country_name)
            if out_path:
                self._status_lbl.config(
                    text=f"✅ Готово!\n{os.path.basename(out_path)}", fg="#27ae60")
                db.log_action(self.user["id"], "EXPORT", "students",
                              student_id,
                              f"Шаблон: {filename}")
                if messagebox.askyesno("Готово",
                                       f"Файл создан:\n{out_path}\n\nОткрыть?",
                                       parent=self):
                    import subprocess, platform
                    if platform.system() == "Windows":
                        os.startfile(out_path)
                    elif platform.system() == "Darwin":
                        subprocess.Popen(["open", out_path])
                    else:
                        subprocess.Popen(["xdg-open", out_path])
            else:
                messagebox.showerror("Ошибка",
                    "python-docx не установлен.\nВыполните: pip install python-docx",
                    parent=self)
        except Exception as e:
            messagebox.showerror("Ошибка при генерации", str(e), parent=self)

    # ── центрирование ─────────────────────────────────────────────────────────

    def _center(self):
        self.update_idletasks()
        w, h = 900, 600
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
