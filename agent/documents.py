"""Word documents (MoU, bid checklist) written to outputs/<tender-id>/."""
import re

from docx import Document
from docx.shared import Pt

from .config import OUTPUT_DIR


def tender_dir(tender_id):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", tender_id)
    path = OUTPUT_DIR / safe
    path.mkdir(parents=True, exist_ok=True)
    return path


def _doc():
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    return doc


def write_mou(tender, pkg, company):
    doc = _doc()
    doc.add_heading(pkg["mou_title"], level=1)
    doc.add_paragraph("DRAFT FOR DISCUSSION – NOT SIGNED").runs[0].italic = True
    doc.add_paragraph(f"Tender: {tender['title']} ({tender['id']}) – {tender['url']}")
    for clause in pkg["mou_clauses"]:
        doc.add_heading(clause["heading"], level=2)
        for para in clause["text"].split("\n"):
            if para.strip():
                doc.add_paragraph(para.strip())
    doc.add_heading("Signatures", level=2)
    doc.add_paragraph(f"For {company['name']}: ____________________   Name: {company['signatory']}   Date: ________")
    doc.add_paragraph("For [Partner Company]: ____________________   Name: ________________   Date: ________")
    path = tender_dir(tender["id"]) / "MoU-draft.docx"
    doc.save(path)
    return path


def write_checklist(tender, items, title="چک‌لیست شرکت در مناقصه"):
    doc = _doc()
    doc.add_heading(title, level=1)
    doc.add_paragraph(f"{tender['title']} – {tender['id']} – مهلت: {tender['deadline']}")
    for item in items:
        doc.add_paragraph(item, style="List Bullet")
    path = tender_dir(tender["id"]) / "checklist.docx"
    doc.save(path)
    return path
