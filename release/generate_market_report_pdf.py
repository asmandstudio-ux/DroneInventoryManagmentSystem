from __future__ import annotations

import argparse
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


_URL_RE = re.compile(r"(https?://\S+)")


def _linkify(text: str) -> str:
    def _sub(m: re.Match[str]) -> str:
        url = m.group(1).rstrip(").,;")
        return f'<link href="{url}">{url}</link>'

    return _URL_RE.sub(_sub, text)


def _parse_markdown(md: str) -> list:
    styles = getSampleStyleSheet()
    base = styles["BodyText"]
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], spaceAfter=12)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceAfter=10)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], spaceAfter=8)
    mono = ParagraphStyle("Mono", parent=base, fontName="Courier", fontSize=9, leading=11)

    story: list = []
    lines = md.splitlines()

    def flush_paragraph(buf: list[str]) -> None:
        text = " ".join(s.strip() for s in buf if s.strip()).strip()
        if not text:
            return
        story.append(Paragraph(_linkify(text), base))
        story.append(Spacer(1, 0.12 * inch))

    paragraph_buf: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        stripped = line.strip()

        if not stripped:
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            i += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i].rstrip("\n"))
                i += 1
            i += 1
            code_text = "<br/>".join(_linkify(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for s in code_lines)
            story.append(Paragraph(code_text, mono))
            story.append(Spacer(1, 0.12 * inch))
            continue

        if stripped.startswith("# "):
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            story.append(Paragraph(_linkify(stripped[2:].strip()), h1))
            story.append(Spacer(1, 0.14 * inch))
            i += 1
            continue

        if stripped.startswith("## "):
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            story.append(Paragraph(_linkify(stripped[3:].strip()), h2))
            story.append(Spacer(1, 0.12 * inch))
            i += 1
            continue

        if stripped.startswith("### "):
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            story.append(Paragraph(_linkify(stripped[4:].strip()), h3))
            story.append(Spacer(1, 0.10 * inch))
            i += 1
            continue

        if stripped.startswith("- "):
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            items: list[ListItem] = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                bullet = lines[i].strip()[2:].strip()
                items.append(ListItem(Paragraph(_linkify(bullet), base)))
                i += 1
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=18))
            story.append(Spacer(1, 0.12 * inch))
            continue

        if "|" in stripped and stripped.count("|") >= 2:
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if "|" in next_line and set(next_line.replace("|", "").replace(" ", "")) <= {"-"}:
                flush_paragraph(paragraph_buf)
                paragraph_buf = []
                header = [c.strip() for c in stripped.strip("|").split("|")]
                i += 2
                rows: list[list[str]] = []
                while i < len(lines):
                    row_line = lines[i].strip()
                    if not row_line or "|" not in row_line:
                        break
                    rows.append([c.strip() for c in row_line.strip("|").split("|")])
                    i += 1

                data = [header] + rows
                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 0.18 * inch))
                continue

        paragraph_buf.append(stripped)
        i += 1

    flush_paragraph(paragraph_buf)
    return story


def build_pdf(input_md: Path, output_pdf: Path) -> None:
    md = input_md.read_text(encoding="utf-8")
    story = _parse_markdown(md)
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=LETTER,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        title="DroneIMS Market & Competitor Report",
    )
    doc.build(story)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).with_name("MARKET_COMPETITOR_REPORT.md"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("DroneIMS_Features_Competitor_Report.pdf"),
    )
    args = parser.parse_args()

    build_pdf(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
