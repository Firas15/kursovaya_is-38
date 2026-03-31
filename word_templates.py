"""
Генерация Word-документов по шаблонам:
  1. СПРАВКА  (для Начальника отдела по вопросам миграции ОП5 МВД)
  2. ВИЗОВАЯ АНКЕТА  (Приложение к приказу МВД, ФСБ, МИД № 233/235/7018)
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

EXPORTS_DIR = Path(__file__).parent / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)

UNIVERSITY_SHORT = "ННГАСУ"
UNIVERSITY_FULL  = ('Федеральное государственное бюджетное образовательное учреждение '
                    'высшего образования «Нижегородский государственный архитектурно-строительный '
                    'университет» (ННГАСУ)')
UNIVERSITY_ADDR  = "г. Нижний Новгород, ул. Ильинская, д. 65, корп. 10, тел. 430-69-80"
CENTER_NAME      = "Центр академического сопровождения иностранных граждан"
CENTER_SHORT     = "ЦАСИГ"
MWD_ADDR         = ("Начальнику отдела по вопросам миграции ОП5\n"
                    "Управления МВД России\nпо г. Нижнему Новгороду")
LEADER           = "Белоус Е.А."


def _safe(val) -> str:
    """Вернуть строку или пустую строку если None."""
    if val is None:
        return ""
    return str(val).strip()


def _fmt_date(day, month, year) -> str:
    try:
        return f"{int(day):02d}.{int(month):02d}.{year}"
    except Exception:
        return ""


def _month_name(month_num) -> str:
    names = {1: "января", 2: "февраля", 3: "марта", 4: "апреля",
             5: "мая", 6: "июня", 7: "июля", 8: "августа",
             9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"}
    try:
        return names.get(int(month_num), "")
    except Exception:
        return ""


def generate_spravka(student: dict, country_name: str = "") -> Optional[str]:
    """
    Генерировать СПРАВКУ для отдела по вопросам миграции.
    Вернуть путь к сохранённому файлу или None при ошибке.
    """
    if not DOCX_AVAILABLE:
        return None

    doc = Document()

    # — поля страницы —
    for sec in doc.sections:
        sec.top_margin    = Cm(2)
        sec.bottom_margin = Cm(2)
        sec.left_margin   = Cm(3)
        sec.right_margin  = Cm(1.5)

    def _para(text="", align=WD_ALIGN_PARAGRAPH.LEFT, bold=False,
              size=12, space_after=0) -> None:
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        run = p.add_run(text)
        run.bold = bold
        run.font.size = Pt(size)
        return p

    # ── шапка ────────────────────────────────────────────────────────────────
    _para("МИНОБРНАУКИ РОССИИ", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)
    _para(UNIVERSITY_FULL, WD_ALIGN_PARAGRAPH.CENTER, size=9)
    _para(CENTER_NAME, WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)
    p_addr = doc.add_paragraph()
    p_addr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_addr.add_run(f"Ильинская ул., д. 65, Нижний Новгород, 603000. "
                       f"Тел./факс: (831) 433-33-70")
    r.font.size = Pt(9)

    # горизонтальная линия
    doc.add_paragraph("_" * 70)

    # блок адресата (таблица 2 колонки)
    t_header = doc.add_table(rows=1, cols=2)
    t_header.style = "Table Grid"
    t_header.allow_autofit = True
    left_cell  = t_header.cell(0, 0)
    right_cell = t_header.cell(0, 1)
    left_cell.text  = "№ ________ от ________________"
    right_cell.text = MWD_ADDR
    for cell in (left_cell, right_cell):
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.size = Pt(11)
    # убрать видимые границы
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    for cell in (left_cell, right_cell):
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        for border_name in ('top','left','bottom','right','insideH','insideV'):
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'none')
            tcBorders.append(border)
        tcPr.append(tcBorders)

    doc.add_paragraph()

    # ── заголовок справки ────────────────────────────────────────────────────
    _para("СПРАВКА", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_after=6)

    # ── тело ─────────────────────────────────────────────────────────────────
    fio_ru  = (f"{_safe(student.get('last_name_ru'))} "
               f"{_safe(student.get('first_name_ru'))} "
               f"{_safe(student.get('middle_name_ru'))}").strip()
    fio_lat = (f"{_safe(student.get('last_name_lat'))} "
               f"{_safe(student.get('first_name_lat'))}").strip()
    birth   = _fmt_date(student.get('birth_day'),
                        student.get('birth_month'),
                        student.get('birth_year'))
    doc_type   = _safe(student.get('id_doc_type'))
    doc_series = _safe(student.get('id_doc_series'))
    doc_num    = _safe(student.get('id_doc_number'))
    doc_from   = _safe(student.get('id_doc_valid_from'))
    doc_to     = _safe(student.get('id_doc_valid_to'))
    edu_form   = _safe(student.get('education_form'))
    arrive     = _safe(student.get('arrival_date'))
    study_end  = _safe(student.get('visa_valid_to'))  # как пример срока

    body = (
        f"Настоящим удостоверяется, что указанное лицо, гражданин(ка) {country_name} "
        f"{fio_ru} ({fio_lat}), {birth} г.р., {doc_type} № {doc_series}{doc_num}, "
        f"сроки действия {doc_from} – {doc_to} гг., является слушателем "
        f"подготовительного отделения {edu_form} формы обучения в "
        f"Нижегородском государственном архитектурно-строительном университете."
    )
    p_body = doc.add_paragraph()
    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body.paragraph_format.first_line_indent = Cm(1.25)
    run = p_body.add_run(body)
    run.font.size = Pt(12)

    doc.add_paragraph()

    # ── подпись ──────────────────────────────────────────────────────────────
    t_sign = doc.add_table(rows=1, cols=2)
    t_sign.cell(0, 0).text = f"Руководитель {CENTER_SHORT}"
    t_sign.cell(0, 1).text = LEADER
    for i, cell in enumerate(t_sign.row_cells(0)):
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.size = Pt(12)
        if i == 1:
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    # без рамок
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    for cell in t_sign.row_cells(0):
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        for bn in ('top','left','bottom','right','insideH','insideV'):
            b = OxmlElement(f'w:{bn}')
            b.set(qn('w:val'), 'none')
            tcBorders.append(b)
        tcPr.append(tcBorders)

    # ── сохранение ───────────────────────────────────────────────────────────
    safe_name = _safe(student.get('last_name_ru')).replace(' ', '_') or "student"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = EXPORTS_DIR / f"spravka_{safe_name}_{ts}.docx"
    doc.save(str(fname))
    return str(fname)


def generate_visa_anketa(student: dict, country_name: str = "") -> Optional[str]:
    """
    Генерировать ВИЗОВУЮ АНКЕТУ.
    Вернуть путь к файлу или None.
    """
    if not DOCX_AVAILABLE:
        return None

    doc = Document()
    for sec in doc.sections:
        sec.top_margin    = Cm(1.5)
        sec.bottom_margin = Cm(1.5)
        sec.left_margin   = Cm(2.5)
        sec.right_margin  = Cm(1.5)

    def _h(text, size=11, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT):
        p = doc.add_paragraph()
        p.alignment = align
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.bold = bold
        return p

    def _field(label: str, value: str, size=11):
        p = doc.add_paragraph()
        r_lbl = p.add_run(label + ": ")
        r_lbl.font.size = Pt(size)
        r_lbl.bold = True
        r_val = p.add_run(value or "___________________________")
        r_val.font.size = Pt(size)

    # шапка
    _h("Приложение к приказу МВД России, ФСБ России, МИД России",
       size=9, align=WD_ALIGN_PARAGRAPH.RIGHT)
    _h("от 27.04.2017 № 233/235/7018", size=9, align=WD_ALIGN_PARAGRAPH.RIGHT)
    doc.add_paragraph()
    _h("ВИЗОВАЯ АНКЕТА", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    _h("Прошу оформить, продлить, восстановить визу:", size=10)
    doc.add_paragraph()
    _h("Кратность: [X] многократная", size=10)
    _h("Категория (вид) визы: [X] обыкновенная  [X] учебная", size=10)
    doc.add_paragraph()

    # сведения о заявителе
    _h("О себе сообщаю следующие сведения:", size=11, bold=True)
    doc.add_paragraph()

    fio_ru  = (f"{_safe(student.get('last_name_ru'))} "
               f"{_safe(student.get('first_name_ru'))} "
               f"{_safe(student.get('middle_name_ru'))}").strip()
    fio_lat = (f"{_safe(student.get('last_name_lat'))} "
               f"{_safe(student.get('first_name_lat'))}").strip()
    birth   = _fmt_date(student.get('birth_day'),
                        student.get('birth_month'),
                        student.get('birth_year'))
    doc_type   = _safe(student.get('id_doc_type'))
    doc_num    = _safe(student.get('id_doc_number'))
    doc_series = _safe(student.get('id_doc_series'))
    doc_to     = _safe(student.get('id_doc_valid_to'))
    address    = _safe(student.get('registration_address'))
    phone      = _safe(student.get('phone'))

    _field("1. Фамилия (кириллица)", _safe(student.get('last_name_ru')))
    _field("   Фамилия (латиница)",  _safe(student.get('last_name_lat')))
    _field("2. Имя (кириллица)",      _safe(student.get('first_name_ru')))
    _field("   Имя (латиница)",       _safe(student.get('first_name_lat')))
    _field("3. Отчество",             _safe(student.get('middle_name_ru')))
    _field("4. Дата рождения",        birth)
    _field("5. Гражданство",          country_name)
    _field("7. Документ, удостоверяющий личность",
           f"{doc_type}  серия {doc_series}  № {doc_num}")
    _field("   Срок действия документа до",  doc_to)

    _field("9. Сведения о приглашающей стороне",
           f"ФГБОУ ВО ННГАСУ, ИНН5260002707, {UNIVERSITY_ADDR}")
    _field("10. Сведения о принимающей стороне",
           f"ФГБОУ ВО ННГАСУ, ИНН5260002707, {UNIVERSITY_ADDR}")
    _field("11. Адрес постановки на миграционный учёт", address)
    _field("12. Маршрут предполагаемого пребывания", "г. Москва, г. Нижний Новгород")
    _field("14. Место учёбы",
           f"ФГБОУ ВО «{UNIVERSITY_SHORT}», {UNIVERSITY_ADDR}")
    _field("15. Родственники на территории РФ", "НЕТ")
    _field("   Контактный телефон", phone)

    doc.add_paragraph()

    # подпись
    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p_sign.add_run("Подпись заявителя: ___________________   "
                       "Дата: ___________________")
    r.font.size = Pt(11)

    safe_name = _safe(student.get('last_name_ru')).replace(' ', '_') or "student"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = EXPORTS_DIR / f"visa_anketa_{safe_name}_{ts}.docx"
    doc.save(str(fname))
    return str(fname)


def check_docx_available() -> bool:
    return DOCX_AVAILABLE
