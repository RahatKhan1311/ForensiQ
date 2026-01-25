from flask import Blueprint, jsonify, send_file, current_app
from .pdf_generator import generate_case_report_pdf
import os
import json
import MySQLdb

reports_bp = Blueprint('reports', __name__)

# --- Build report by numeric case ID ---
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

# --- Build report by case code (FQ-2025-XXX) ---
def generate_case_report(case_code):
    cur = current_app.mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cur.execute("SELECT * FROM cases WHERE case_id=%s", (case_code,))
    case = cur.fetchone()
    if not case:
        cur.close()
        return None

    numeric_case_id = case["id"]

    cur.execute("""
        SELECT analysis_text, confidence_score, similarity_results, timestamp
        FROM ai_results
        WHERE case_id=%s
        ORDER BY timestamp DESC
        LIMIT 1
    """, (numeric_case_id,))
    ai_row = cur.fetchone()
    cur.close()

    ocr_results = []
    ai_observations = []
    similarity = []

    if ai_row:
        try:
            parsed = json.loads(ai_row["analysis_text"])
        except:
            parsed = {}

        ocr_results.append({
            "summary": parsed.get("summary", ""),
            "key_insights": parsed.get("key_insights", {}),
            "keywords": parsed.get("keywords", []),
            "confidence": ai_row.get("confidence_score"),
            "timestamp": ai_row["timestamp"].isoformat() if ai_row["timestamp"] else None
        })

        for k, v in parsed.get("key_insights", {}).items():
            if v:
                ai_observations.append(f"{k.title()} detected: {', '.join(v)}")

        if ai_row.get("similarity_results"):
            try:
                similarity = json.loads(ai_row["similarity_results"])
            except:
                similarity = []

    report = {
        "case_overview": {
            "case_id": case["case_id"],
            "title": case["title"],
            "status": case["status"],
            "priority": case["priority"],
            "owner": case["owner"],
            "created_at": case["created_at"].isoformat() if case["created_at"] else None
        },
        "evidence_summary": json.loads(case.get("evidence") or "[]"),
        "ocr_results": ocr_results,
        "ai_observations": list(set(ai_observations)),
        "similarity_results": similarity,
        "conclusion": "This report is AI-generated and requires investigator validation."
    }

    return report

# --- API Routes ---
@reports_bp.route('/api/reports/<int:case_id>', methods=['GET'])
def generate_report(case_id):
    report = build_case_report(case_id)
    if not report:
        return jsonify({"error": "Report data incomplete"}), 404
    return jsonify(report)

@reports_bp.route('/api/reports/<case_id>/pdf', methods=['GET'])
def download_case_report(case_id):
    report_data = generate_case_report(case_id)
    if not report_data:
        return jsonify({"error": "Report data incomplete or case not found"}), 404

    try:
        pdf_path = generate_case_report_pdf(case_id, report_data)
        if os.path.exists(pdf_path):
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"Case_{case_id}.pdf",
                mimetype="application/pdf"
            )
        else:
            return jsonify({"error": "PDF generation failed"}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error during PDF generation", "detail": str(e)}), 500
