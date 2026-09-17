import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from cases.models import Case
from ledger.models import LedgerEntry
from ledger.services import verify_case_integrity

def generate_case_audit_pdf(case_id: str) -> bytes:
    """
    Generates a court-ready audit PDF report for a case.
    """
    case = Case.objects.get(id=case_id)
    integrity = verify_case_integrity(case_id)
    entries = LedgerEntry.objects.filter(case=case).order_by('server_timestamp')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor('#0B1220'))
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#333333'))

    story.append(Paragraph(f"COURT AUDIT REPORT: CASE {case.case_number}", title_style))
    story.append(Spacer(1, 10))

    ver_status = "VERIFIED INTACT ✅" if integrity['verified'] else f"TAMPER DETECTED ❌ ({integrity.get('broken_reason')})"
    meta_text = f"""
    <b>Case Title:</b> {case.title}<br/>
    <b>Status:</b> {case.status}<br/>
    <b>Chain Integrity:</b> {ver_status}<br/>
    <b>Total Ledger Entries:</b> {integrity['total_entries']}<br/>
    <b>Generated At:</b> {case.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
    """
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 15))

    # Table of ledger entries
    table_data = [["Action", "Actor", "Document Hash (SHA-256)", "Timestamp"]]
    for e in entries:
        table_data.append([
            e.action,
            e.actor.badge_id,
            f"{e.document_hash[:16]}...",
            e.server_timestamp.strftime('%Y-%m-%d %H:%M')
        ])

    table = Table(table_data, colWidths=[80, 90, 240, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E2A44')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))

    story.append(table)
    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()
