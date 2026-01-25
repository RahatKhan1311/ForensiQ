from flask import Blueprint, jsonify, send_file, current_app
from .pdf_generator import generate_case_report_pdf
import json
import MySQLdb

reports_bp = Blueprint('reports', __name__)

def build_case_report(case_id):
    cur = current_app.mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cur.execute("SELECT * FROM cases WHERE id=%s", (case_id,))
    case = cur.fetchone()

    cur.execute("""
        SELECT *
        FROM ai_results
        WHERE case_id=%s
        ORDER BY timestamp DESC
        LIMIT 1
    """, (case_id,))
    ai = cur.fetchone()

    cur.close()

    if not case or not ai:
        return None
    
    parsed_analysis = json.loads(ai["analysis_text"]) if ai["analysis_text"] else {}
    
    report = {
    "case_overview": {
        "case_id": case["id"],
        "title": case["title"],
        "status": case["status"],
        "priority": case["priority"],
        "created_at": str(case["created_at"])
    },
    "evidence_summary": [
        {
            "type": "Digital Evidence",
            "description": "AI-processed forensic artifacts",
            "source": "System analysis engine"
        }
    ],
    "ai_analysis": {
        "analysis_text": ai["analysis_text"],
        "confidence": ai["confidence_score"],
        "similarity_results": json.loads(ai["similarity_results"] or "[]"),
        "timestamp": str(ai["timestamp"])
    },
    "conclusion": "This report is AI-generated and requires investigator validation."
}

    return report

@reports_bp.route('/api/reports/<int:case_id>', methods=['GET'])
def generate_report(case_id):
    report = build_case_report(case_id)

    if not report:
        return jsonify({"error": "Report data incomplete"}), 404

    return jsonify(report)


@reports_bp.route('/api/reports/<int:case_id>/pdf', methods=['GET'])
def download_case_report(case_id):
    report_data = build_case_report(case_id)

    if not report_data:
        return jsonify({"error": "Report data incomplete"}), 404

    pdf_path = generate_case_report_pdf(case_id, report_data)

    return send_file(pdf_path, as_attachment=True)
