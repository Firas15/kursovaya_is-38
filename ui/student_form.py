"""
Форма добавления / редактирования студента.
Все 20 полей по п.2 приказа разбиты по вкладкам Notebook.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import calendar

import database as db

FONT     = ("Segoe UI", 10)
FONT_LBL = ("Segoe UI", 10)
FONT_H   = ("Segoe UI", 11, "bold")
PAD_LR   = 14
PAD_TB   = 5


# ── вспомогательные виджеты ───────────────────────────────────────────────────

def _lbl(parent, text, row, col, sticky="e", padx=(0, 6), pady=4):
    tk.Label(parent, text=text, font=FONT_LBL, anchor="e").grid(
        row=row, column=col, sticky=sticky, padx=padx, pady=pady)


def _entry(parent, var, row, col, width=28, colspan=1, state="normal"):
    e = ttk.Entry(parent, textvariable=var, font=FONT, width=width, state=state)
    e.grid(row=row, column=col, sticky="w", pady=4,
           columnspan=colspan, padx=(0, 10))
    return e


def _combo(parent, var, values, row, col, width=26, state="readonly"):
    c = ttk.Combobox(parent, textvariable=var, values=values,
                     font=FONT, width=width, state=state)
    c.grid(row=row, column=col, sticky="w", pady=4, padx=(0, 10))
    return c


def _check(parent, text, var, row, col, state="normal"):
    cb = ttk.Checkbutton(parent, text=text, variable=var, state=state)
    cb.grid(row=row, column=col, sticky="w", pady=4, padx=(0, 10))
    return cb


class StudentForm(tk.Toplevel):
    """
    Модальное окно для ввода/редактирования данных студента.
    """

    def __init__(self, parent, user: dict, student_id=None,
                 readonly=False, on_save=None):
        super().__init__(parent)
        self.user       = user
        self.student_id = student_id
        self.readonly   = readonly
        self.on_save    = on_save

        title = "Просмотр записи" if readonly else (
            "Редактировать запись" if student_id else "Новый студент")
        self.title(title)
        self.resizable(True, True)
        self.grab_set()          # модальность

        self._init_vars()
        self._build_ui()
        self._load_countries()

        if student_id:
            self._load_student(student_id)

        if readonly:
            self._set_readonly()

        self._center()

    # ── переменные ────────────────────────────────────────────────────────────

    def _init_vars(self):
        sv = tk.StringVar
        iv = tk.IntVar

        # 1. ФИО кириллица
        self.v_last_ru  = sv(); self.v_first_ru = sv(); self.v_mid_ru = sv()
        # 2. ФИО латиница
        self.v_last_lat = sv(); self.v_first_lat = sv(); self.v_mid_lat = sv()
        # 3. Дата рождения
        self.v_bday = sv(); self.v_bmon = sv(); self.v_byear = sv()
        # 4. Гражданство
        self.v_country    = sv()
        self._country_map = {}   # name_ru -> id

        # 5-6. Документ
        self.v_doc_type   = sv(); self.v_doc_series = sv()
        self.v_doc_num    = sv()
        self.v_doc_from   = sv(); self.v_doc_to = sv()
        # 7-8. Виза
        self.v_visa_ser   = sv(); self.v_visa_num = sv()
        self.v_visa_from  = sv(); self.v_visa_to  = sv()
        # 9. Контакты
        self.v_phone = sv(); self.v_email = sv()
        # 10. Форма обучения
        self.v_edu_form = sv()
        # 11. Форма оплаты
        self.v_pay_form = sv()
        # 12. Дистанционное
        self.v_distance = iv()
        # 13. Прибытие
        self.v_arr_date  = sv(); self.v_arr_doc_type  = sv()
        self.v_arr_date2 = sv(); self.v_arr_req       = sv()
        # 14. Адрес
        self.v_reg_addr = sv()
        # 15. Дактилоскопия
        self.v_bio_doc  = sv(); self.v_bio_date = sv()
        # 16. Медицина
        self.v_med_doc  = sv(); self.v_med_date = sv(); self.v_med_rep = iv()
        # 17. Акад. отпуск
        self.v_al_doc   = sv(); self.v_al_basis = sv(); self.v_al_date = sv()
        # 18. Трудовая деят.
        self.v_emp_date = sv(); self.v_emp_info = sv()
        # 19. Разрешение на проживание
        self.v_rp_doc   = sv(); self.v_rp_type = sv(); self.v_rp_to = sv()
        # 20. Нарушения
        self.v_vio_info = sv(); self.v_vio_type = sv()
        self.v_vio_date = sv(); self.v_vio_req  = sv()

    # ── построение UI ─────────────────────────────────────────────────────────

    def _build_ui(self):
        self.configure(bg="#ecf0f1")
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        self._nb = nb

        self._tab1 = self._make_tab(nb, "1. Личные данные")
        self._tab2 = self._make_tab(nb, "2. Документы и виза")
        self._tab3 = self._make_tab(nb, "3. Контакты / Обучение")
        self._tab4 = self._make_tab(nb, "4. Прибытие / Адрес")
        self._tab5 = self._make_tab(nb, "5. Регистрация / Медицина")
        self._tab6 = self._make_tab(nb, "6. Занятость / Статус")
        self._tab7 = self._make_tab(nb, "7. Нарушения")

        self._fill_tab1()
        self._fill_tab2()
        self._fill_tab3()
        self._fill_tab4()
        self._fill_tab5()
        self._fill_tab6()
        self._fill_tab7()

        # кнопки
        btn_bar = tk.Frame(self, bg="#ecf0f1")
        btn_bar.pack(fill="x", padx=10, pady=(0, 10))

        if not self.readonly:
            tk.Button(btn_bar, text="💾  Сохранить",
                      bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"),
                      relief="flat", cursor="hand2", padx=14, pady=6,
                      command=self._save).pack(side="left", padx=6)
        tk.Button(btn_bar, text="✖  Закрыть",
                  bg="#7f8c8d", fg="white", font=FONT,
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=self.destroy).pack(side="left")

        self._err_lbl = tk.Label(btn_bar, text="", fg="#e74c3c", bg="#ecf0f1",
                                 font=FONT)
        self._err_lbl.pack(side="left", padx=10)

    @staticmethod
    def _make_tab(nb, text) -> ttk.Frame:
        f = ttk.Frame(nb, padding=12)
        nb.add(f, text=text)
        return f

    # ── вкладка 1 — Личные данные (поля 1-4) ─────────────────────────────────

    def _fill_tab1(self):
        t = self._tab1
        tk.Label(t, text="Поля 1–4  ·  ФИО, дата рождения, гражданство",
                 font=FONT_H).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        # 1. ФИО кириллица
        tk.Label(t, text="── ФИО (кириллица) ──", font=("Segoe UI", 9, "italic"),
                 fg="#555").grid(row=1, column=0, columnspan=4, sticky="w")
        _lbl(t, "Фамилия *", 2, 0); _entry(t, self.v_last_ru,  2, 1, 24)
        _lbl(t, "Имя *",     2, 2); _entry(t, self.v_first_ru, 2, 3, 20)
        _lbl(t, "Отчество",  3, 0); _entry(t, self.v_mid_ru,   3, 1, 24)

        # 2. ФИО латиница
        tk.Label(t, text="── ФИО (латиница) ──", font=("Segoe UI", 9, "italic"),
                 fg="#555").grid(row=4, column=0, columnspan=4, sticky="w", pady=(8,0))
        _lbl(t, "Фамилия",  5, 0); _entry(t, self.v_last_lat,  5, 1, 24)
        _lbl(t, "Имя",      5, 2); _entry(t, self.v_first_lat, 5, 3, 20)
        _lbl(t, "Отчество", 6, 0); _entry(t, self.v_mid_lat,   6, 1, 24)

        # 3. Дата рождения
        tk.Label(t, text="── Дата рождения (поле 3) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=7, column=0, columnspan=4, sticky="w", pady=(8,0))
        _lbl(t, "День *", 8, 0)
        day_spin = ttk.Spinbox(t, from_=1, to=31, textvariable=self.v_bday,
                               width=5, font=FONT)
        day_spin.grid(row=8, column=1, sticky="w", pady=4)

        _lbl(t, "Месяц *", 8, 2)
        mon_spin = ttk.Spinbox(t, from_=1, to=12, textvariable=self.v_bmon,
                               width=5, font=FONT)
        mon_spin.grid(row=8, column=3, sticky="w", pady=4)

        _lbl(t, "Год *", 9, 0)
        yr_spin = ttk.Spinbox(t, from_=1930, to=datetime.now().year - 15,
                              textvariable=self.v_byear, width=7, font=FONT)
        yr_spin.grid(row=9, column=1, sticky="w", pady=4)

        # 4. Гражданство
        tk.Label(t, text="── Гражданство (поле 4, справочник) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=10, column=0, columnspan=4, sticky="w", pady=(8,0))
        _lbl(t, "Гражданство", 11, 0)
        self._country_cb = _combo(t, self.v_country, [], 11, 1, width=30)
        tk.Button(t, text="+ Добавить страну", font=("Segoe UI", 9),
                  relief="flat", bg="#2980b9", fg="white", cursor="hand2",
                  command=self._add_country_dialog
                  ).grid(row=11, column=2, sticky="w")

    # ── вкладка 2 — Документы (поля 5-8) ─────────────────────────────────────

    def _fill_tab2(self):
        t = self._tab2
        tk.Label(t, text="Поля 5–8  ·  Документ, удостоверяющий личность, и виза",
                 font=FONT_H).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        tk.Label(t, text="── Документ, удостоверяющий личность (поля 5–6) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=1, column=0, columnspan=4, sticky="w")

        _lbl(t, "Тип документа", 2, 0)
        _combo(t, self.v_doc_type,
               ["паспорт", "заграничный паспорт", "иной документ"],
               2, 1, width=22, state="normal")

        _lbl(t, "Серия", 3, 0); _entry(t, self.v_doc_series, 3, 1, 12)
        _lbl(t, "Номер", 3, 2); _entry(t, self.v_doc_num,    3, 3, 16)

        _lbl(t, "Действителен с", 4, 0)
        _entry(t, self.v_doc_from, 4, 1, 14)
        tk.Label(t, text="(ДД.ММ.ГГГГ)", font=("Segoe UI", 8), fg="#888"
                 ).grid(row=4, column=2, sticky="w")

        _lbl(t, "Действителен по", 5, 0)
        _entry(t, self.v_doc_to, 5, 1, 14)
        tk.Label(t, text="(ДД.ММ.ГГГГ)", font=("Segoe UI", 8), fg="#888"
                 ).grid(row=5, column=2, sticky="w")

        # Виза
        tk.Label(t, text="── Виза (поля 7–8) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=6, column=0, columnspan=4, sticky="w", pady=(10,0))

        _lbl(t, "Серия визы",  7, 0); _entry(t, self.v_visa_ser, 7, 1, 12)
        _lbl(t, "Номер визы",  7, 2); _entry(t, self.v_visa_num, 7, 3, 16)
        _lbl(t, "Виза с",      8, 0); _entry(t, self.v_visa_from, 8, 1, 14)
        tk.Label(t, text="(ДД.ММ.ГГГГ)", font=("Segoe UI", 8), fg="#888"
                 ).grid(row=8, column=2, sticky="w")
        _lbl(t, "Виза по",     9, 0); _entry(t, self.v_visa_to,  9, 1, 14)
        tk.Label(t, text="(ДД.ММ.ГГГГ)", font=("Segoe UI", 8), fg="#888"
                 ).grid(row=9, column=2, sticky="w")

    # ── вкладка 3 — Контакты / Обучение (поля 9-12) ──────────────────────────

    def _fill_tab3(self):
        t = self._tab3
        tk.Label(t, text="Поля 9–12  ·  Контакты, форма обучения и оплаты",
                 font=FONT_H).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        # 9. Контакты
        tk.Label(t, text="── Контактные данные (поле 9) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=1, column=0, columnspan=4, sticky="w")
        _lbl(t, "Телефон", 2, 0); _entry(t, self.v_phone, 2, 1, 22)
        _lbl(t, "E-mail",  3, 0); _entry(t, self.v_email, 3, 1, 32)

        # 10. Форма обучения
        tk.Label(t, text="── Форма обучения (поле 10) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=4, column=0, columnspan=4, sticky="w", pady=(10,0))

        edu_frame = tk.Frame(t)
        edu_frame.grid(row=5, column=0, columnspan=4, sticky="w", pady=4)
        for val, txt in [("очная","Очная"), ("заочная","Заочная"),
                          ("очно-заочная","Очно-заочная")]:
            ttk.Radiobutton(edu_frame, text=txt, variable=self.v_edu_form,
                            value=val).pack(side="left", padx=8)

        # 11. Форма оплаты
        tk.Label(t, text="── Форма оплаты (поле 11) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=6, column=0, columnspan=4, sticky="w", pady=(10,0))
        _lbl(t, "Форма оплаты", 7, 0)
        _combo(t, self.v_pay_form,
               ["бюджет", "договор", "квота Правительства РФ",
                "целевое обучение", "иное"],
               7, 1, width=28, state="normal")

        # 12. Дистанционное
        tk.Label(t, text="── Дистанционные технологии (поле 12) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=8, column=0, columnspan=4, sticky="w", pady=(10,0))
        _check(t, "Обучение исключительно с применением ДОТ", self.v_distance, 9, 0)

    # ── вкладка 4 — Прибытие / Адрес (поля 13-14) ────────────────────────────

    def _fill_tab4(self):
        t = self._tab4
        tk.Label(t, text="Поля 13–14  ·  Прибытие и адрес регистрации",
                 font=FONT_H).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        # 13. Прибытие
        tk.Label(t, text="── Дата фактического прибытия (поле 13) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=1, column=0, columnspan=4, sticky="w")

        _lbl(t, "Дата прибытия",       2, 0); _entry(t, self.v_arr_date,  2, 1, 14)
        _lbl(t, "Вид документа",        3, 0); _entry(t, self.v_arr_doc_type, 3, 1, 28)
        _lbl(t, "Дата документа",       4, 0); _entry(t, self.v_arr_date2, 4, 1, 14)
        tk.Label(t, text="(ДД.ММ.ГГГГ)", font=("Segoe UI", 8), fg="#888"
                 ).grid(row=4, column=2, sticky="w")
        _lbl(t, "Реквизиты документа",  5, 0); _entry(t, self.v_arr_req, 5, 1, 40, colspan=3)

        # 14. Адрес
        tk.Label(t, text="── Адрес проживания по месту регистрации (поле 14) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=6, column=0, columnspan=4, sticky="w", pady=(12,0))
        _lbl(t, "Адрес", 7, 0)
        addr_entry = ttk.Entry(t, textvariable=self.v_reg_addr,
                               font=FONT, width=54)
        addr_entry.grid(row=7, column=1, columnspan=3, sticky="w", pady=4)

    # ── вкладка 5 — Рег. / Медицина (поля 15-17) ─────────────────────────────

    def _fill_tab5(self):
        t = self._tab5
        tk.Label(t,
                 text="Поля 15–17  ·  Дактилоскопия, медосвидетельствование, академотпуск",
                 font=FONT_H).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        # 15. Дактилоскопия
        tk.Label(t, text="── Дактилоскопия и фотографирование (поле 15) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=1, column=0, columnspan=4, sticky="w")
        _lbl(t, "Документ", 2, 0); _entry(t, self.v_bio_doc,  2, 1, 36)
        _lbl(t, "Дата",     3, 0); _entry(t, self.v_bio_date, 3, 1, 14)
        tk.Label(t, text="(ДД.ММ.ГГГГ)", font=("Segoe UI", 8), fg="#888"
                 ).grid(row=3, column=2, sticky="w")

        # 16. Медицина
        tk.Label(t, text="── Медицинское освидетельствование (поле 16) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=4, column=0, columnspan=4, sticky="w", pady=(10,0))
        _lbl(t, "Документ", 5, 0); _entry(t, self.v_med_doc,  5, 1, 36)
        _lbl(t, "Дата",     6, 0); _entry(t, self.v_med_date, 6, 1, 14)
        tk.Label(t, text="(ДД.ММ.ГГГГ)", font=("Segoe UI", 8), fg="#888"
                 ).grid(row=6, column=2, sticky="w")
        _check(t, "Повторное прохождение", self.v_med_rep, 7, 1)

        # 17. Академический отпуск
        tk.Label(t, text="── Академический отпуск (поле 17) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=8, column=0, columnspan=4, sticky="w", pady=(10,0))
        _lbl(t, "Документ",  9,  0); _entry(t, self.v_al_doc,   9, 1, 36)
        _lbl(t, "Основание", 10, 0); _entry(t, self.v_al_basis, 10, 1, 36)
        _lbl(t, "Дата",      11, 0); _entry(t, self.v_al_date,  11, 1, 14)
        tk.Label(t, text="(ДД.ММ.ГГГГ)", font=("Segoe UI", 8), fg="#888"
                 ).grid(row=11, column=2, sticky="w")

    # ── вкладка 6 — Занятость / Статус (поля 18-19) ──────────────────────────

    def _fill_tab6(self):
        t = self._tab6
        tk.Label(t, text="Поля 18–19  ·  Трудовая деятельность и разрешение на проживание",
                 font=FONT_H).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        # 18. Занятость
        tk.Label(t, text="── Трудовая деятельность (поле 18) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=1, column=0, columnspan=4, sticky="w")
        _lbl(t, "Дата приёма на работу",   2, 0); _entry(t, self.v_emp_date, 2, 1, 14)
        tk.Label(t, text="(ДД.ММ.ГГГГ)", font=("Segoe UI", 8), fg="#888"
                 ).grid(row=2, column=2, sticky="w")
        _lbl(t, "Сведения о работодателе", 3, 0); _entry(t, self.v_emp_info, 3, 1, 46, colspan=3)

        # 19. Разрешение на проживание
        tk.Label(t, text="── Разрешение на временное проживание / ВНЖ (поле 19) ──",
                 font=("Segoe UI", 9, "italic"), fg="#555"
                 ).grid(row=4, column=0, columnspan=4, sticky="w", pady=(14,0))
        _lbl(t, "Документ", 5, 0); _entry(t, self.v_rp_doc,  5, 1, 36)
        _lbl(t, "Тип",      6, 0)
        _combo(t, self.v_rp_type,
               ["РВП", "ВНЖ", "РВП + ВНЖ"],
               6, 1, width=16, state="normal")
        _lbl(t, "Действует по", 7, 0); _entry(t, self.v_rp_to, 7, 1, 14)
        tk.Label(t, text="(ДД.ММ.ГГГГ)", font=("Segoe UI", 8), fg="#888"
                 ).grid(row=7, column=2, sticky="w")

    # ── вкладка 7 — Нарушения (поле 20) ──────────────────────────────────────

    def _fill_tab7(self):
        t = self._tab7
        tk.Label(t, text="Поле 20  ·  Нарушения миграционного законодательства",
                 font=FONT_H).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        _lbl(t, "Сведения о нарушении",     1, 0, sticky="ne")
        txt_vio = tk.Text(t, font=FONT, width=52, height=4, wrap="word")
        txt_vio.grid(row=1, column=1, columnspan=3, pady=4, sticky="w")
        self._txt_vio = txt_vio

        _lbl(t, "Вид нарушения",            2, 0); _entry(t, self.v_vio_type, 2, 1, 36)
        _lbl(t, "Дата нарушения",           3, 0); _entry(t, self.v_vio_date, 3, 1, 14)
        tk.Label(t, text="(ДД.ММ.ГГГГ)", font=("Segoe UI", 8), fg="#888"
                 ).grid(row=3, column=2, sticky="w")
        _lbl(t, "Реквизиты документа",      4, 0); _entry(t, self.v_vio_req,  4, 1, 36)

    # ── загрузка справочников ─────────────────────────────────────────────────

    def _load_countries(self):
        rows = db.get_all_countries()
        names = [r["name_ru"] for r in rows]
        self._country_map = {r["name_ru"]: r["id"] for r in rows}
        self._country_cb["values"] = names

    # ── загрузка записи студента ──────────────────────────────────────────────

    def _load_student(self, sid: int):
        s = db.get_student_by_id(sid)
        if s is None:
            return
        s = dict(s)

        self.v_last_ru.set(s.get("last_name_ru") or "")
        self.v_first_ru.set(s.get("first_name_ru") or "")
        self.v_mid_ru.set(s.get("middle_name_ru") or "")
        self.v_last_lat.set(s.get("last_name_lat") or "")
        self.v_first_lat.set(s.get("first_name_lat") or "")
        self.v_mid_lat.set(s.get("middle_name_lat") or "")

        self.v_bday.set(str(s.get("birth_day") or ""))
        self.v_bmon.set(str(s.get("birth_month") or ""))
        self.v_byear.set(str(s.get("birth_year") or ""))

        # найти название страны по id
        cid = s.get("country_id")
        if cid:
            rev_map = {v: k for k, v in self._country_map.items()}
            self.v_country.set(rev_map.get(cid, ""))

        self.v_doc_type.set(s.get("id_doc_type") or "")
        self.v_doc_series.set(s.get("id_doc_series") or "")
        self.v_doc_num.set(s.get("id_doc_number") or "")
        self.v_doc_from.set(s.get("id_doc_valid_from") or "")
        self.v_doc_to.set(s.get("id_doc_valid_to") or "")

        self.v_visa_ser.set(s.get("visa_series") or "")
        self.v_visa_num.set(s.get("visa_number") or "")
        self.v_visa_from.set(s.get("visa_valid_from") or "")
        self.v_visa_to.set(s.get("visa_valid_to") or "")

        self.v_phone.set(s.get("phone") or "")
        self.v_email.set(s.get("email") or "")
        self.v_edu_form.set(s.get("education_form") or "")
        self.v_pay_form.set(s.get("payment_form") or "")
        self.v_distance.set(int(s.get("distance_learning") or 0))

        self.v_arr_date.set(s.get("arrival_date") or "")
        self.v_arr_doc_type.set(s.get("arrival_doc_type") or "")
        self.v_arr_date2.set(s.get("arrival_doc_date") or "")
        self.v_arr_req.set(s.get("arrival_doc_requisites") or "")
        self.v_reg_addr.set(s.get("registration_address") or "")

        self.v_bio_doc.set(s.get("biometrics_doc") or "")
        self.v_bio_date.set(s.get("biometrics_date") or "")

        self.v_med_doc.set(s.get("medical_doc") or "")
        self.v_med_date.set(s.get("medical_date") or "")
        self.v_med_rep.set(int(s.get("medical_repeated") or 0))

        self.v_al_doc.set(s.get("academic_leave_doc") or "")
        self.v_al_basis.set(s.get("academic_leave_basis") or "")
        self.v_al_date.set(s.get("academic_leave_date") or "")

        self.v_emp_date.set(s.get("employment_date") or "")
        self.v_emp_info.set(s.get("employer_info") or "")

        self.v_rp_doc.set(s.get("residence_permit_doc") or "")
        self.v_rp_type.set(s.get("residence_permit_type") or "")
        self.v_rp_to.set(s.get("residence_permit_valid_to") or "")

        vio_info = s.get("violation_info") or ""
        self._txt_vio.delete("1.0", "end")
        self._txt_vio.insert("1.0", vio_info)
        self.v_vio_type.set(s.get("violation_doc_type") or "")
        self.v_vio_date.set(s.get("violation_date") or "")
        self.v_vio_req.set(s.get("violation_doc_requisites") or "")

    def _set_readonly(self):
        """Перевести все поля в режим только для чтения."""
        def _disable(widget):
            cls = widget.winfo_class()
            try:
                if cls in ("TEntry", "TCombobox", "TSpinbox"):
                    widget.config(state="disabled")
                elif cls in ("TCheckbutton", "TRadiobutton"):
                    widget.config(state="disabled")
                elif cls == "Text":
                    widget.config(state="disabled")
            except Exception:
                pass
            for child in widget.winfo_children():
                _disable(child)
        _disable(self)

    # ── валидация ─────────────────────────────────────────────────────────────

    def _validate(self) -> bool:
        errors = []

        if not self.v_last_ru.get().strip():
            errors.append("Фамилия (кириллица) обязательна")
        if not self.v_first_ru.get().strip():
            errors.append("Имя (кириллица) обязательно")

        # Дата рождения
        try:
            d = int(self.v_bday.get())
            m = int(self.v_bmon.get())
            y = int(self.v_byear.get())
            if not (1 <= d <= 31 and 1 <= m <= 12 and 1930 <= y <= datetime.now().year - 14):
                raise ValueError
            # Проверить реальную дату
            calendar.monthrange(y, m)  # вернёт число дней в месяце
            if d > calendar.monthrange(y, m)[1]:
                errors.append(f"В месяце {m}.{y} нет дня {d}")
        except (ValueError, TypeError):
            errors.append("Некорректная дата рождения")

        # Даты в формате ДД.ММ.ГГГГ
        date_fields = [
            (self.v_doc_from,  "Срок действия документа «с»"),
            (self.v_doc_to,    "Срок действия документа «по»"),
            (self.v_visa_from, "Виза с"),
            (self.v_visa_to,   "Виза по"),
            (self.v_arr_date,  "Дата прибытия"),
        ]
        for var, label in date_fields:
            val = var.get().strip()
            if val:
                try:
                    datetime.strptime(val, "%d.%m.%Y")
                except ValueError:
                    errors.append(f"{label}: неверный формат, нужно ДД.ММ.ГГГГ")

        if errors:
            self._err_lbl.config(text=errors[0])
            self._nb.select(0 if "Фамилия" in errors[0] or "Имя" in errors[0]
                              or "дата рождения" in errors[0] else 0)
            return False

        self._err_lbl.config(text="")
        return True

    # ── сбор данных и сохранение ──────────────────────────────────────────────

    def _collect_data(self) -> dict:
        country_name = self.v_country.get().strip()
        country_id   = self._country_map.get(country_name)

        vio_info = self._txt_vio.get("1.0", "end").strip()

        def sv(v):
            val = v.get().strip()
            return val if val else None

        data = {
            "last_name_ru":    sv(self.v_last_ru),
            "first_name_ru":   sv(self.v_first_ru),
            "middle_name_ru":  sv(self.v_mid_ru),
            "last_name_lat":   sv(self.v_last_lat),
            "first_name_lat":  sv(self.v_first_lat),
            "middle_name_lat": sv(self.v_mid_lat),

            "birth_day":   int(self.v_bday.get()),
            "birth_month": int(self.v_bmon.get()),
            "birth_year":  int(self.v_byear.get()),

            "country_id":    country_id,

            "id_doc_type":       sv(self.v_doc_type),
            "id_doc_series":     sv(self.v_doc_series),
            "id_doc_number":     sv(self.v_doc_num),
            "id_doc_valid_from": sv(self.v_doc_from),
            "id_doc_valid_to":   sv(self.v_doc_to),

            "visa_series":     sv(self.v_visa_ser),
            "visa_number":     sv(self.v_visa_num),
            "visa_valid_from": sv(self.v_visa_from),
            "visa_valid_to":   sv(self.v_visa_to),

            "phone":          sv(self.v_phone),
            "email":          sv(self.v_email),
            "education_form": sv(self.v_edu_form),
            "payment_form":   sv(self.v_pay_form),
            "distance_learning": int(self.v_distance.get()),

            "arrival_date":            sv(self.v_arr_date),
            "arrival_doc_type":        sv(self.v_arr_doc_type),
            "arrival_doc_date":        sv(self.v_arr_date2),
            "arrival_doc_requisites":  sv(self.v_arr_req),
            "registration_address":    sv(self.v_reg_addr),

            "biometrics_doc":  sv(self.v_bio_doc),
            "biometrics_date": sv(self.v_bio_date),

            "medical_doc":      sv(self.v_med_doc),
            "medical_date":     sv(self.v_med_date),
            "medical_repeated": int(self.v_med_rep.get()),

            "academic_leave_doc":   sv(self.v_al_doc),
            "academic_leave_basis": sv(self.v_al_basis),
            "academic_leave_date":  sv(self.v_al_date),

            "employment_date": sv(self.v_emp_date),
            "employer_info":   sv(self.v_emp_info),

            "residence_permit_doc":      sv(self.v_rp_doc),
            "residence_permit_type":     sv(self.v_rp_type),
            "residence_permit_valid_to": sv(self.v_rp_to),

            "violation_info":           vio_info if vio_info else None,
            "violation_doc_type":       sv(self.v_vio_type),
            "violation_date":           sv(self.v_vio_date),
            "violation_doc_requisites": sv(self.v_vio_req),
        }
        return data

    def _save(self):
        if not self._validate():
            return

        data = self._collect_data()

        if self.student_id:
            ok, msg = db.update_student(self.student_id, data)
            action = "UPDATE"
        else:
            ok, msg = db.create_student(data, self.user["id"])
            action = "CREATE"

        if ok:
            db.log_action(self.user["id"], action, "students",
                          self.student_id,
                          f"{data['last_name_ru']} {data['first_name_ru']}")
            messagebox.showinfo("Готово", msg, parent=self)
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Ошибка", msg, parent=self)

    # ── диалог добавления страны ──────────────────────────────────────────────

    def _add_country_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Добавить страну")
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(dlg, text="Название (рус.):", font=FONT).grid(row=0, column=0,
                                                                padx=10, pady=8, sticky="e")
        v_name = tk.StringVar()
        ttk.Entry(dlg, textvariable=v_name, font=FONT, width=22).grid(row=0, column=1, padx=6)

        tk.Label(dlg, text="Название (лат.):", font=FONT).grid(row=1, column=0,
                                                                padx=10, pady=4, sticky="e")
        v_lat = tk.StringVar()
        ttk.Entry(dlg, textvariable=v_lat, font=FONT, width=22).grid(row=1, column=1, padx=6)

        def _do_add():
            name = v_name.get().strip()
            if not name:
                messagebox.showwarning("Ошибка", "Введите название", parent=dlg)
                return
            ok, msg = db.add_country(name, v_lat.get())
            if ok:
                self._load_countries()
                self.v_country.set(name)
                dlg.destroy()
            else:
                messagebox.showerror("Ошибка", msg, parent=dlg)

        tk.Button(dlg, text="Добавить", bg="#27ae60", fg="white", font=FONT,
                  relief="flat", command=_do_add).grid(row=2, column=0,
                                                       columnspan=2, pady=10)

    # ── центрирование ─────────────────────────────────────────────────────────

    def _center(self):
        self.update_idletasks()
        w, h = 680, 560
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
