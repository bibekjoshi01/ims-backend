"""PDF regression: every roster row survives pagination and data is escaped."""

from datetime import date
from io import BytesIO

from django.test import SimpleTestCase
from pypdf import PdfReader

from src.performance.internal_evaluation_pdf import marks_in_words, render_evaluation_pdf


class EvaluationPDFTests(SimpleTestCase):
    def test_words_cover_supported_range(self):
        assert marks_in_words(0) == "Zero"
        assert marks_in_words(40) == "Forty"
        assert marks_in_words(107) == "One hundred and seven"
        assert marks_in_words(1000) == "One thousand"

    def test_large_roster_wraps_names_and_repeats_headings(self):
        sheet = {
            "institution": {
                "name": "Campus & Institute",
                "university_name": "University",
                "institute_name": "Engineering",
            },
            "subject": {
                "code": "EX716",
                "name": "Long subject " * 10,
                "full_marks": 40,
                "pass_marks": 16,
                "component": "Theory",
            },
            "semester": 7,
            "program": "BEI",
            "programme_section": "A <B>",
            "academic_level": "Bachelor",
            "batch": 2079,
            "bs_date": "2083-05-15",
            "sheet_date": date(2026, 8, 31),
            "examiner": "Examiner",
            "head_of_department": "Head",
            "mode": "calculated",
            "rows": [
                {
                    "roll_number": f"THA079BEI{i:03}",
                    "full_name": "Long Name With Multiple Middle Names & <literal>",
                    "mark": 14 if i == 1 else 40,
                    "absent": i == 2,
                    "remarks": "",
                }
                for i in range(1, 76)
            ],
        }
        reader = PdfReader(BytesIO(render_evaluation_pdf(sheet)))
        assert len(reader.pages) >= 3
        text = "\n".join(page.extract_text() for page in reader.pages)
        for index in range(1, 76):
            assert text.count(f"THA079BEI{index:03}") == 1
        for page in reader.pages:
            content = page.extract_text()
            assert "Internal Assessment Examination 2083" in content
            assert "Class Roll No." in content
        assert "Campus & Institute" in text
        assert "<literal>" in text
        assert "Name of Examiner:" in reader.pages[-1].extract_text()
        assert "Name of HOD:" in reader.pages[-1].extract_text()
        sheet["institution"]["name"] = "थापाथली क्याम्पस"
        sheet["rows"][0]["full_name"] = "बिबेक जोशी"
        nepali = PdfReader(BytesIO(render_evaluation_pdf(sheet)))
        content = nepali.pages[0].get_contents().get_data()
        assert b"/ActualText" in content
        assert ("\ufeffबिबेक जोशी").encode("utf-16-be").hex().encode() in content
        fonts = nepali.pages[0]["/Resources"]["/Font"].values()
        assert any("NotoSansDevanagari" in str(font.get_object()["/BaseFont"]) for font in fonts)
        assert b"1 0 0 RG" in reader.pages[0].get_contents().get_data()  # red circles
