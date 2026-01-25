from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generate_case_report_pdf(case_id, report_data):
    import os
    os.makedirs("exports", exist_ok=True)
    file_path = f"exports/ForensiQ_Report_{case_id}.pdf"

    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    content = []

    # Title
    content.append(Paragraph("<b>ForensiQ – AI Case Analysis Report</b>", styles["Title"]))
    content.append(Spacer(1, 12))

    # Case Overview
    case_overview = report_data.get("case_overview") or {}
    if case_overview:
        content.append(Paragraph("<b>Case Overview</b>", styles["Heading2"]))
        for k, v in case_overview.items():
            content.append(Paragraph(f"<b>{k.replace('_',' ').title()}:</b> {v or 'N/A'}", styles["Normal"]))
        content.append(Spacer(1, 12))

    # Notes
    notes = report_data.get("notes", []) or []
    if notes:
        content.append(Paragraph("<b>Notes</b>", styles["Heading2"]))
        for note in notes:
            content.append(Paragraph(f"- {note}", styles["Normal"]))
        content.append(Spacer(1, 12))

    # Evidence
    evidence = report_data.get("evidence_summary") or []
    if evidence:
        content.append(Paragraph("<b>Evidence Summary</b>", styles["Heading2"]))
        for ev in evidence:
            if isinstance(ev, dict):
                ev_text = ", ".join([f"{key}: {val}" for key, val in ev.items()])
            else:
                ev_text = str(ev)
            content.append(Paragraph(f"- {ev_text}", styles["Normal"]))
        content.append(Spacer(1, 12))

    # OCR Results
    ocr_results = report_data.get("ocr_results") or []
    if ocr_results:
        content.append(Paragraph("<b>OCR Analysis</b>", styles["Heading2"]))
        for ocr in ocr_results:
            summary = ocr.get("summary", "")
            confidence = ocr.get("confidence", "N/A")
            content.append(Paragraph(f"Summary: {summary}", styles["Normal"]))
            content.append(Paragraph(f"Confidence: {confidence}", styles["Normal"]))
            content.append(Spacer(1, 6))

    # AI Observations
    ai_obs = report_data.get("ai_observations") or []
    if ai_obs:
        content.append(Paragraph("<b>AI Observations</b>", styles["Heading2"]))
        for obs in ai_obs:
            content.append(Paragraph(f"- {obs}", styles["Normal"]))
        content.append(Spacer(1, 12))

    # Similarity Results
    similarity = report_data.get("similarity_results") or []
    if similarity:
        content.append(Paragraph("<b>Similarity Results</b>", styles["Heading2"]))
        table_data = [["Case ID", "Title", "Similarity %", "Top Keywords"]]
        for sim in similarity:
            table_data.append([
                sim.get("case_id", "N/A"),
                sim.get("title", "N/A"),
                str(sim.get("similarity_score", 0)),
                ", ".join(sim.get("matching_keywords") or [])
            ])
        table = Table(table_data, colWidths=[80, 180, 60, 180])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.gray),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (2,1), (2,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.black)
        ]))
        content.append(table)
        content.append(Spacer(1, 12))

    # --- Conclusion ---
    conclusion = report_data.get("conclusion") or "No conclusion provided."
    content.append(Paragraph("<b>Conclusion</b>", styles["Heading2"]))
    content.append(Paragraph(conclusion, styles["Normal"]))

    # Build PDF
    doc.build(content)
    return file_path

