"""Build the downloadable PDF analysis report."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .scorer import Analysis

INK = colors.HexColor("#0F1B33")
ACCENT = colors.HexColor("#2563EB")
GOOD = colors.HexColor("#16A34A")
BAD = colors.HexColor("#DC2626")
MUTED = colors.HexColor("#64748B")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], textColor=INK, fontSize=22, spaceAfter=2),
        "sub": ParagraphStyle("s", parent=base["Normal"], textColor=MUTED, fontSize=9.5, spaceAfter=14),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], textColor=ACCENT, fontSize=12.5, spaceBefore=14, spaceAfter=6
        ),
        "body": ParagraphStyle(
            "b", parent=base["Normal"], fontSize=10, leading=15, alignment=TA_LEFT, textColor=INK
        ),
    }


def _score_table(a: Analysis) -> Table:
    rows = [
        ["Overall match", f"{a.overall}%", a.verdict],
        ["Skill coverage", f"{a.skill_coverage}%", f"{len(a.matched)} of {len(a.matched) + len(a.missing)} required skills"],
        ["Text similarity", f"{a.similarity}%", "TF-IDF cosine, resume vs. job description"],
        ["Resume quality", f"{a.quality}%", "Structure, metrics, action verbs"],
    ]
    t = Table(rows, colWidths=[45 * mm, 25 * mm, 90 * mm])
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (1, 0), (1, 0), GOOD if a.overall >= 65 else BAD),
                ("TEXTCOLOR", (2, 0), (2, -1), MUTED),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#E2E8F0")),
            ]
        )
    )
    return t


def build_report(analysis: Analysis, suggestions: list[str], filename: str, source: str) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
        title="Resume Analysis Report",
    )
    st = _styles()
    story = [
        Paragraph("Resume Analysis Report", st["title"]),
        Paragraph(
            f"{filename} &nbsp;·&nbsp; generated {datetime.now():%d %b %Y, %H:%M} "
            f"&nbsp;·&nbsp; suggestions by {'Gemini' if source == 'gemini' else 'rule engine'}",
            st["sub"],
        ),
        _score_table(analysis),
        Paragraph("Skills you already evidence", st["h2"]),
    ]

    matched = ", ".join(s.name for s in analysis.matched) or "None detected."
    story.append(Paragraph(matched, st["body"]))

    story.append(Paragraph("Skills the job asks for that are missing", st["h2"]))
    missing = ", ".join(s.name for s in analysis.missing) or "None — full coverage."
    story.append(Paragraph(missing, st["body"]))

    story.append(Paragraph("Section scores", st["h2"]))
    sec = Table(
        [[k, f"{v}%"] for k, v in analysis.section_scores.items()], colWidths=[45 * mm, 20 * mm]
    )
    sec.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (1, 0), (1, -1), ACCENT),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(sec)

    story.append(Paragraph("How to improve", st["h2"]))
    story.append(
        ListFlowable(
            [ListItem(Paragraph(s, st["body"]), leftIndent=10) for s in suggestions],
            bulletType="bullet",
            bulletColor=ACCENT,
        )
    )
    story.append(Spacer(1, 10 * mm))
    story.append(
        Paragraph(
            "Scores are advisory. They reflect keyword and structure signals, not hiring decisions.",
            st["sub"],
        )
    )

    doc.build(story)
    return buf.getvalue()
