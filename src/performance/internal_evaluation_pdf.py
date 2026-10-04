"""A4 internal assessment register, with repeated headings and signature space."""

from functools import lru_cache
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape, unescape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_SMALL = (
    "Zero",
    "One",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Eleven",
    "Twelve",
    "Thirteen",
    "Fourteen",
    "Fifteen",
    "Sixteen",
    "Seventeen",
    "Eighteen",
    "Nineteen",
)
_TENS = ("", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety")


def marks_in_words(number):
    if number < 20:
        return _SMALL[number]
    if number < 100:
        return _TENS[number // 10] + (" " + _SMALL[number % 10].lower() if number % 10 else "")
    if number < 1000:
        return (
            _SMALL[number // 100]
            + " hundred"
            + (" and " + marks_in_words(number % 100).lower() if number % 100 else "")
        )
    return "One thousand"


@lru_cache(maxsize=1)
def register_nepali_font():
    font = Path(__file__).resolve().parent / "fonts" / "NotoSansDevanagari.ttf"
    registerFont(TTFont("SPAS-Devanagari", str(font), shapable=True))


class NepaliParagraph(Paragraph):
    """Retain logical Unicode text alongside HarfBuzz's reordered glyphs."""

    def draw(self):
        if self.text is None:
            return super().draw()
        actual_text = ("\ufeff" + unescape(self.text)).encode("utf-16-be").hex()
        self.canv.addLiteral(f"/Span << /ActualText <{actual_text}> >> BDC")
        try:
            super().draw()
        finally:
            self.canv.addLiteral("EMC")


class CircledMark(Flowable):
    def __init__(self, value, circle):
        super().__init__()
        self.value = str(value)
        self.circle = circle
        self.height = 13

    def wrap(self, width, height):
        self.width = width
        return width, self.height

    def draw(self):
        canvas = self.canv
        canvas.setFont("Times-Roman", 11)
        canvas.setFillColor(colors.black)
        canvas.drawCentredString(self.width / 2, 3, self.value)
        if self.circle:
            width = max(15, stringWidth(self.value, "Times-Roman", 11) + 9)
            canvas.setStrokeColor(colors.red)
            canvas.setLineWidth(1)
            canvas.ellipse(self.width / 2 - width / 2, 0, self.width / 2 + width / 2, 14)


def render_evaluation_pdf(sheet):
    buffer = BytesIO()
    width = A4[0] - 30 * mm
    body = ParagraphStyle("body", fontName="Times-Roman", fontSize=10.5, leading=12)
    bold = ParagraphStyle("bold", parent=body, fontName="Times-Bold")
    center = ParagraphStyle("center", parent=body, alignment=TA_CENTER)
    title = ParagraphStyle("title", parent=bold, alignment=TA_CENTER, fontSize=12, leading=14)
    campus = ParagraphStyle("campus", parent=title, fontSize=15, leading=17)

    def paragraph(text, style=body):
        # Labels and names are data, never ReportLab markup.
        text = str(text)
        if any("\u0900" <= character <= "\u097f" for character in text):
            register_nepali_font()
            style = style.clone(f"{style.name}-nepali", fontName="SPAS-Devanagari", shaping=True)
            return NepaliParagraph(escape(text), style)
        return Paragraph(escape(text), style)

    institution = sheet["institution"]
    headings = [paragraph(institution["university_name"], title)]
    if institution["institute_name"]:
        headings.append(paragraph(institution["institute_name"], title))
    headings += [
        paragraph(institution["name"], campus),
        paragraph(f"Internal Assessment Examination {sheet['bs_date'].split('-')[0]}", title),
    ]
    semester = sheet["semester"]
    year_part = f"{('I', 'II', 'III', 'IV')[(semester - 1) // 2]}/{'I' if semester % 2 else 'II'}"
    programme = sheet["program"] + (
        f" '{sheet['programme_section']}'" if sheet["programme_section"] else ""
    )
    left = [
        f"Batch: {sheet['batch']}",
        f"Year/Part: {year_part}",
        f"Subject Code No.: {sheet['subject']['code']}",
        f"Subject: {sheet['subject']['name']}",
    ]
    right = [
        f"Level: {sheet['academic_level']}",
        f"Programme: {programme}",
        sheet["subject"]["component"],
        f"Full Marks: {sheet['subject']['full_marks']}",
        f"Pass Marks: {sheet['subject']['pass_marks']:02d}",
    ]
    metadata = Table(
        [
            [paragraph(left[index], bold) if index < len(left) else "", paragraph(value, bold)]
            for index, value in enumerate(right)
        ],
        colWidths=[width * 0.66, width * 0.34],
    )
    metadata.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    header_parts = [*headings, Spacer(1, 5 * mm), metadata]
    header_height = sum(part.wrap(width, A4[1])[1] for part in header_parts)

    def page_heading(canvas, doc):
        canvas.saveState()
        y = A4[1] - 14 * mm
        for part in header_parts:
            _, height = part.wrap(width, A4[1])
            y -= height
            part.drawOn(canvas, 15 * mm, y)
        canvas.setFont("Times-Roman", 8)
        canvas.drawRightString(A4[0] - 15 * mm, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()

    column_style = ParagraphStyle("column", parent=bold, alignment=TA_CENTER)
    data = [
        [
            paragraph(label, column_style)
            for label in (
                "Class Roll No.",
                "Student Full Name",
                "Marks In Figures",
                "Marks In Words",
                "Remarks",
            )
        ]
    ]
    styles = [
        ("GRID", (0, 0), (-1, -1), 0.7, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for row in sheet["rows"]:
        status = row["remarks"]
        figure = ""
        words = ""
        if status:
            words = status
            styles.append(
                ("BACKGROUND", (0, len(data)), (-1, len(data)), colors.Color(0.86, 0.86, 0.86))
            )
        elif sheet["mode"] == "calculated":
            if row["absent"]:
                figure, words = CircledMark("A", True), "Absent"
            elif row["mark"] is not None:
                figure = CircledMark(row["mark"], row["mark"] < sheet["subject"]["pass_marks"])
                words = marks_in_words(row["mark"])
        data.append(
            [
                paragraph(row["roll_number"]),
                paragraph(row["full_name"]),
                figure,
                paragraph(words, center),
                paragraph(status, center),
            ]
        )
    table = Table(
        data,
        colWidths=[width * share for share in (0.18, 0.30, 0.14, 0.23, 0.15)],
        repeatRows=1,
        minRowHeights=[8 * mm] + [6 * mm] * len(sheet["rows"]),
    )
    table.setStyle(TableStyle(styles))
    footer = Table(
        [
            [
                paragraph(f"Date: {sheet['bs_date'].replace('-', '/')}", bold),
                paragraph(f"Name of Examiner: {sheet['examiner']}", bold),
                paragraph("Signature:", bold),
            ],
            [
                "",
                paragraph(f"Name of HOD: {sheet['head_of_department']}", bold),
                paragraph("Signature:", bold),
            ],
            [
                paragraph("NOTE: Absentees-A and failed marks must be encircled in red.", bold),
                "",
                Paragraph("Received Date:<br/>(Exam Section)", bold),
            ],
        ],
        colWidths=[width * 0.22, width * 0.55, width * 0.23],
    )
    footer.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("SPAN", (0, 2), (1, 2)),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=14 * mm + header_height + 5 * mm,
        bottomMargin=15 * mm,
        title=f"Internal evaluation — {sheet['subject']['code']}",
        author=institution["name"],
    )
    document.build(
        [table, KeepTogether([Spacer(1, 3 * mm), footer])],
        onFirstPage=page_heading,
        onLaterPages=page_heading,
    )
    return buffer.getvalue()
