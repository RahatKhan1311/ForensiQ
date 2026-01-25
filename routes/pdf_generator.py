from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def generate_case_report_pdf(case_id, report_data):
    file_path = f"reports/ForensiQ_Report_{case_id}.pdf"

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    content = []

    # Title
    content.append(Paragraph("<b>ForensiQ – AI Case Analysis Report</b>", styles["Title"]))
    content.append(Spacer(1, 12))

    # Case Overview
    content.append(Paragraph("<b>Case Overview</b>", styles["Heading2"]))
    for k, v in report_data["case_overview"].items():
        content.append(Paragraph(f"{k}: {v}", styles["Normal"]))
    content.append(Spacer(1, 12))

    # Evidence Summary
    content.append(Paragraph("<b>Evidence Summary</b>", styles["Heading2"]))
    for ev in report_data["evidence_summary"]:
        content.append(Paragraph(f"- {ev}", styles["Normal"]))
    content.append(Spacer(1, 12))

    # OCR Results
    content.append(Paragraph("<b>OCR Analysis</b>", styles["Heading2"]))
    for ocr in report_data["ocr_results"]:
        content.append(Paragraph(f"Summary: {ocr['summary']}", styles["Normal"]))
        content.append(Paragraph(f"Confidence: {ocr['confidence']}%", styles["Normal"]))
    content.append(Spacer(1, 12))

    # AI Observations
    content.append(Paragraph("<b>AI Observations</b>", styles["Heading2"]))
    for obs in report_data["ai_observations"]:
        content.append(Paragraph(f"- {obs}", styles["Normal"]))
    content.append(Spacer(1, 12))

    # Conclusion
    content.append(Paragraph("<b>Conclusion</b>", styles["Heading2"]))
    content.append(Paragraph(report_data["conclusion"], styles["Normal"]))

    doc.build(content)

    return file_path
