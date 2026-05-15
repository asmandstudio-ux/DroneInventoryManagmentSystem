from __future__ import annotations

import io
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import anyio
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.report_job import ReportJobStatus
from app.repositories.report_jobs import ReportJobsRepository
from app.services.s3_service import _client


_URL_RE = re.compile(r"(https?://\S+)")


class ReportService:
    """
    MVP "report generation hook".

    In production, replace `run_job_inline()` with:
    - a message queue (SQS/RabbitMQ/Kafka) + worker, or
    - Temporal/Durable Functions, or
    - Celery/RQ.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.jobs = ReportJobsRepository(session)

    def _render_markdown_pdf(self, md: str, title: str) -> bytes:
        def _linkify(text: str) -> str:
            def _sub(m: re.Match[str]) -> str:
                url = m.group(1).rstrip(").,;")
                return f'<link href="{url}">{url}</link>'

            return _URL_RE.sub(_sub, text)

        def _parse_markdown(src: str) -> list:
            styles = getSampleStyleSheet()
            base = styles["BodyText"]
            h1 = ParagraphStyle("H1", parent=styles["Heading1"], spaceAfter=12)
            h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceAfter=10)
            h3 = ParagraphStyle("H3", parent=styles["Heading3"], spaceAfter=8)
            mono = ParagraphStyle("Mono", parent=base, fontName="Courier", fontSize=9, leading=11)

            story: list = []
            lines = src.splitlines()

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
                    code_text = "<br/>".join(
                        _linkify(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        for s in code_lines
                    )
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

        buf = io.BytesIO()
        story = _parse_markdown(md)
        doc = SimpleDocTemplate(
            buf,
            pagesize=LETTER,
            leftMargin=0.8 * inch,
            rightMargin=0.8 * inch,
            topMargin=0.8 * inch,
            bottomMargin=0.8 * inch,
            title=title,
        )
        doc.build(story)
        return buf.getvalue()

    def _render_pdf(self, payload: dict) -> bytes:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=LETTER)
        width, height = LETTER

        x = 72
        y = height - 72

        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y, "DroneIMS Report")
        y -= 28

        c.setFont("Helvetica", 10)
        c.drawString(x, y, f"Generated at (UTC): {payload.get('generated_at', '')}")
        y -= 18

        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y, "Report Type:")
        c.setFont("Helvetica", 11)
        c.drawString(x + 90, y, str(payload.get("report_type", "")))
        y -= 18

        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y, "Parameters:")
        y -= 16

        c.setFont("Courier", 9)
        params_text = json.dumps(payload.get("params", {}), indent=2, sort_keys=True, ensure_ascii=False)
        for line in params_text.splitlines():
            if y < 72:
                c.showPage()
                y = height - 72
                c.setFont("Courier", 9)
            c.drawString(x, y, line[:120])
            y -= 12

        c.showPage()
        c.save()
        return buf.getvalue()

    async def run_job_inline(self, job_id: uuid.UUID) -> None:
        job = await self.jobs.get(job_id)
        if not job:
            return

        job.status = ReportJobStatus.running.value
        await self.session.commit()

        try:
            payload = {
                "report_type": job.report_type,
                "params": job.params,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            report_type = (job.report_type or "").strip()
            if report_type in {"market_competitor_report", "market_competitor"}:
                root = Path(__file__).resolve().parents[2]
                md_path = root / "release" / "MARKET_COMPETITOR_REPORT.md"
                md = md_path.read_text(encoding="utf-8")
                md = re.sub(
                    r"^Generated:.*$",
                    f"Generated: {datetime.now(timezone.utc).date().isoformat()}",
                    md,
                    flags=re.MULTILINE,
                )
                pdf_bytes = self._render_markdown_pdf(md, "DroneIMS Market & Competitor Report")
                payload["source_document"] = str(md_path)
            else:
                pdf_bytes = self._render_pdf(payload)

            pdf_object_key = f"reports/{job.id}.pdf"
            json_object_key = f"reports/{job.id}.json"

            def _upload() -> None:
                _client().put_object(
                    Bucket=settings.S3_BUCKET,
                    Key=pdf_object_key,
                    Body=pdf_bytes,
                    ContentType="application/pdf",
                )
                _client().put_object(
                    Bucket=settings.S3_BUCKET,
                    Key=json_object_key,
                    Body=json.dumps(payload).encode("utf-8"),
                    ContentType="application/json",
                )

            await anyio.to_thread.run_sync(_upload)
            job.status = ReportJobStatus.completed.value
            job.result_object_key = pdf_object_key
            job.error_message = None
        except Exception as exc:  # noqa: BLE001
            job.status = ReportJobStatus.failed.value
            job.error_message = str(exc)[:1024]

        await self.session.commit()

