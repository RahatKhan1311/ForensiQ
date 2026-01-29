from flask import Flask, render_template, request, jsonify, send_file, redirect, send_from_directory, url_for, session
import os
import json
from extensions import mysql
import MySQLdb.cursors
DictCursor = MySQLdb.cursors.DictCursor
from werkzeug.utils import secure_filename
from fpdf import FPDF
from datetime import datetime
from routes.auth import token_required

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

from routes.auth import auth_bp

import pytesseract
from PIL import Image

import re

def extract_key_insights(text):
    return {
        "emails": list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text))),
        "phones": list(set(re.findall(r"\b\d{10}\b", text))),
        "dates": list(set(re.findall(r"\b\d{2}[/-]\d{2}[/-]\d{4}\b", text))),
        "urls": list(set(re.findall(r"https?://\S+", text))),
    }

import spacy
nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    """Extract persons, organizations, locations, money amounts from text"""
    doc = nlp(text)
    entities = {
        "persons": list(set([ent.text for ent in doc.ents if ent.label_ == "PERSON"])),
        "organizations": list(set([ent.text for ent in doc.ents if ent.label_ == "ORG"])),
        "locations": list(set([ent.text for ent in doc.ents if ent.label_ == "GPE"])),
        "money": list(set([ent.text for ent in doc.ents if ent.label_ == "MONEY"]))
    }
    return entities

def extract_keywords(text, top_n=10):
    """Return top N keywords from text using TF-IDF"""
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
    X = vec.fit_transform([text])
    tfidf_scores = dict(zip(vec.get_feature_names_out(), X.toarray()[0]))
    sorted_keywords = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)
    return [kw for kw, score in sorted_keywords[:top_n]]

def highlight_keywords(text, keywords_dict):
    """
    Wrap keywords in <mark> tags for frontend highlighting
    """
    if not text or not keywords_dict:
        return text
    
    highlighted_text = text
    
    # Define which categories to highlight
    categories_to_highlight = ['persons', 'organizations', 'locations', 'money']
    
    for category in categories_to_highlight:
        if category in keywords_dict:
            items = keywords_dict[category]
            if not isinstance(items, list):
                continue
                
            for item in items:
                if not item or not isinstance(item, str):
                    continue
                
                item = item.strip()
                if len(item) < 2:  # Skip single characters
                    continue
                
                try:
                    # Escape special regex characters
                    escaped_item = re.escape(item)
                    # Use word boundaries and case-insensitive matching
                    pattern = rf'\b{escaped_item}\b'
                    highlighted_text = re.sub(
                        pattern, 
                        f'<mark>{item}</mark>', 
                        highlighted_text,
                        flags=re.IGNORECASE
                    )
                except re.error as e:
                    try:
                        highlighted_text = highlighted_text.replace(item, f'<mark>{item}</mark>')
                    except:
                        continue  # Skip if even simple replace fails
    
    return highlighted_text

# PDF handling
from pdf2image import convert_from_path
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def perform_ocr(filepath):
    try:
        ext = os.path.splitext(filepath)[1].lower()
        text = ""

        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            img = Image.open(filepath)
            text = pytesseract.image_to_string(img)

        elif ext == ".pdf":
            pages = convert_from_path(filepath, poppler_path=POPPLER_PATH)
            for page in pages:
                text += pytesseract.image_to_string(page) + "\n"

        else:
            return f"Unsupported file type: {ext}"

        return text

    except Exception as e:
        return f"OCR Error: {str(e)}"

from concurrent.futures import ThreadPoolExecutor

def fast_ocr_pdf(filepath):
    images = convert_from_path(filepath, poppler_path=POPPLER_PATH)

    ocr_texts = []

    def ocr_page(img):
        return pytesseract.image_to_string(img)

    with ThreadPoolExecutor(max_workers=6) as ex:
        ocr_texts = list(ex.map(ocr_page, images))

    return "\n".join(ocr_texts)

def extract_text_from_file(file):
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    text = ""

    if filename.lower().endswith(".pdf"):
        images = convert_from_path(filepath)
        for img in images:
            text += pytesseract.image_to_string(img)

    else:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img)

    return text

app= Flask(__name__, template_folder="templates", static_folder="static")
app.config['UPLOAD_FOLDER'] = 'uploads' 
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.register_blueprint(auth_bp)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'rahat@13'
app.config['MYSQL_DB'] = 'forensiq'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = 'secretkey123'
mysql.init_app(app)
app.mysql = mysql

# ---------- Helper functions ----------
def row_to_case(row):
    """Convert DB row (dict) to case dict for JSON responses."""
    if isinstance(row, dict):
        evidence = json.loads(row.get('evidence') or "[]")
        notes = json.loads(row.get('notes') or "[]")
        return {
            "id": row.get("case_id"),
            "title": row.get("title"),
            "date": row.get("date"),
            "status": row.get("status"),
            "priority": row.get("priority"),
            "owner": row.get("owner"),
            "evidence": evidence,
            "notes": notes,
            "created_at": row.get("created_at").isoformat() if row.get("created_at") is not None else None
        }
    else:
        return {
            "id": row[1],
            "title": row[2],
            "date": row[3],
            "status": row[4],
            "priority": row[5],
            "owner": row[6],
            "evidence": json.loads(row[7] or "[]"),
            "notes": json.loads(row[8] or "[]"),
            "created_at": row[9].isoformat() if row[9] is not None else None
        }
    
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/api/cases", methods=["GET"])
def get_cases():
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM cases ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()

    cases = [row_to_case(r) for r in rows]
    return jsonify(cases)  #this will return all cases as JSON.


@app.route("/api/dashboard", methods=["GET"])
@token_required
def dashboard_stats(current_user):
    try:
        cur = mysql.connection.cursor(DictCursor)

        # === Counters ===
        cur.execute("SELECT COUNT(*) AS cnt FROM cases")
        total_cases = cur.fetchone()['cnt']

        cur.execute("SELECT COUNT(*) AS cnt FROM cases WHERE status=%s", ("Open",))
        open_cases = cur.fetchone()['cnt']

        cur.execute("SELECT COUNT(*) AS cnt FROM cases WHERE status=%s", ("Pending Analysis",))
        pending_analysis = cur.fetchone()['cnt']

        cur.execute("SELECT COUNT(*) AS cnt FROM cases WHERE status=%s", ("Closed",))
        closed_cases = cur.fetchone()['cnt']

        # average response
        cur.execute("""
            SELECT AVG(TIMESTAMPDIFF(HOUR,created_at,closed_at)) AS avg_hours
            FROM cases
            WHERE closed_at IS NOT NULL        
        """)
        row = cur.fetchone()
        avg_response = row['avg_hours'] if row and row['avg_hours'] is not None else 0
        avg_response = round(avg_response, 1)

        # === Recent 6 cases ===
        cur.execute("""
            SELECT case_id, title, status, owner, created_at
            FROM cases
            ORDER BY created_at DESC
            LIMIT 6
        """)
        rows = cur.fetchall()

        recent_cases = [
            {
                "case_id": r["case_id"],
                "title": r["title"],
                "status": r["status"],
                "owner": r["owner"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None
            }
            for r in rows
        ]

        cur.close()

        return jsonify({
            "total_cases": total_cases,
            "open_cases": open_cases,
            "pending_analysis": pending_analysis,
            "closed_cases": closed_cases,
            "avg_response": avg_response,
            "recent_cases": recent_cases,
            "current_user": current_user
        })

    except Exception as e:
        print("Dashboard error:", e)
        return jsonify({"error": "Failed to load dashboard", "detail": str(e)}), 500

@app.route("/api/new_case", methods=["POST"])
def new_case():
    # Check content type
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        raw = request.form.get('caseData')
        try:
            case_data = json.loads(raw)
        except Exception:
            return jsonify({'error': 'Invalid caseData JSON'}), 400

        evidence_files = request.files.getlist('evidence')
        saved_files = []
        for file in evidence_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                # avoid overwrite by renaming if exists
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(path):
                    filename = f"{base}_{counter}{ext}"
                    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    counter += 1
                file.save(path)
                saved_files.append(filename)
        case_data['evidence'] = saved_files
    elif request.content_type and request.content_type.startswith('application/json'):
        case_data = request.get_json()
        case_data['evidence'] = case_data.get('evidence', [])
    else:
        return jsonify({'error': 'Unsupported content type'}), 400

    # Normalize fields
    case_id = case_data.get('id') or case_data.get('case_id')
    title = case_data.get('title') or "Untitled"
    date = case_data.get('date') or ""
    status = case_data.get('status') or "Open"
    priority = case_data.get('priority') or ""
    owner = case_data.get('owner') or ""
    evidence = case_data.get('evidence') or []
    notes = case_data.get('notes') or []

    # Insert into DB
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO cases (case_id, title, date, status, priority, owner, evidence, notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (case_id, title, date, status, priority, owner, json.dumps(evidence), json.dumps(notes))
        )
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({"error": "DB insert failed", "detail": str(e)}), 500

    cur.close()
    return jsonify({'id': case_id, 'message': 'Case created successfully'})


@app.route('/api/delete_case/<case_id>', methods=['DELETE'])
def delete_case(case_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT evidence FROM cases WHERE case_id=%s", (case_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        return jsonify({'error': 'Case not found'}), 404

    # row may be dict or tuple depending on cursor type
    evidence_json = row.get('evidence') if isinstance(row, dict) else row[0]
    evidence = json.loads(evidence_json or "[]")

    # delete files
    for filename in evidence:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

    # delete DB row
    cur.execute("DELETE FROM cases WHERE case_id=%s", (case_id,))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': f'Case {case_id} and its evidence deleted successfully'})

@app.route("/api/assign_case/<case_id>", methods=["POST"])
def assign_case(case_id):
    data = request.json
    new_owner = data.get("owner")
    if new_owner is None:
        return jsonify({"error": "No owner provided"}), 400
    cur = mysql.connection.cursor()
    cur.execute("UPDATE cases SET owner=%s WHERE case_id=%s", (new_owner, case_id))
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Assigned successfully", "owner": new_owner})

@app.route("/api/assign_analyst/<case_id>", methods=["POST"])
def assign_analyst(case_id):
    data = request.json
    new_analyst = data.get("analyst")
    if new_analyst is None:
        return jsonify({"error": "No analyst provided"}), 400
    cur = mysql.connection.cursor()
    cur.execute("UPDATE cases SET owner=%s WHERE case_id=%s", (new_analyst, case_id))
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": f"Case {case_id} assigned successfully"}), 200

@app.route("/api/add_note/<case_id>", methods=["POST"])
def add_note(case_id):
    data = request.json
    note = data.get("note")
    if not note:
        return jsonify({"error": "No note provided"}), 400
    
    cur = mysql.connection.cursor()
    # fetch current notes
    cur.execute("SELECT notes FROM cases WHERE case_id=%s", (case_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        return jsonify({"error": "Case not found"}), 404

    notes_json = row.get('notes') if isinstance(row, dict) else row[0]
    notes = json.loads(notes_json or "[]")
    notes.append(note)

    cur.execute("UPDATE cases SET notes=%s WHERE case_id=%s", (json.dumps(notes), case_id))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Note added", "notes": notes})

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/api/export/<case_id>", methods=["GET"])
def export_case(case_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cases WHERE case_id=%s", (case_id,))
    row = cur.fetchone()
    cur.close()

    if not row:
        return jsonify({"error": "Case not found"}), 404

    case = row_to_case(row)

    os.makedirs("exports", exist_ok=True)
    pdf_path = f"exports/{case_id}.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0,10,f"Case report: {case['id']} - {case['title']}", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", '', 12)
    pdf.cell(0,10,f"Title: {case['title']}", ln=True)
    pdf.cell(0,10,f"Date: {case['date']}", ln=True)
    pdf.cell(0,10,f"Status: {case['status']}", ln=True)
    pdf.cell(0,10,f"Priority: {case['priority']}", ln=True)
    pdf.cell(0,10,f"Owner: {case['owner']}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0,10,"Notes:", ln=True)
    pdf.set_font("Arial",'',12)
    for note in case.get("notes", []):
        pdf.multi_cell(0,8,  f" -{note}")
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0,10,"Evidence:", ln=True)
    pdf.set_font("Arial",'',12)
    evidence = case.get("evidence", [])
    for item in evidence:
        pdf.cell(0,8,  f" -{item}", ln=True)

    pdf.output(pdf_path)    

    return send_file(pdf_path, as_attachment=True, download_name=f"Case_{case_id}.pdf", mimetype="application/pdf")


# Run OCR on uploaded file
@app.route("/api/analyze/ocr", methods=["POST"])
def run_ocr():
    # 1️⃣ Get file and case_id
    file = request.files.get("file")
    case_id_str = request.form.get("case_id", "").strip()

    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    if not case_id_str:
        return jsonify({
            "error": "No case selected",
            "detail": "The 'case_id' field is empty",
            "hint": "Check if your dropdown has a value selected"
        }), 400

    # 2️⃣ Save uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # 3️⃣ Perform OCR
    ocr_text = ""
    confidence_score = 0
    data={}

    try:
        if filename.lower().endswith(".pdf"):
            ocr_result = fast_ocr_pdf(filepath)
            ocr_text = str(ocr_result) if ocr_result is not None else ""
            confidence_score = None
            data = {'text': [ocr_text], 'conf': ['0']}
        else:
            img = Image.open(filepath)
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            data['text'] = [str(t) for t in data['text']]
            ocr_text = " ".join(data['text']).strip()

            # Compute average confidence
            confs = []
            for c in data['conf']:
                try:
                    # Convert to string first
                    c_str = str(c)
                    # Check if it's a valid number
                    if re.match(r'^-?\d+(\.\d+)?$', c_str):
                        val = float(c_str)
                        if val >= 0:
                            confs.append(val)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Skipping invalid confidence value '{c}': {e}")
                    continue
            
            confidence_score = round(sum(confs)/len(confs), 2) if confs else 0

    except Exception as e:
        print(f"OCR Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"OCR Error: {str(e)}"}), 500

    # 4️⃣ AI Processing (Key insights & keywords)
    try:
        key_insights = extract_key_insights(ocr_text)        
        entities = extract_entities(ocr_text)         
        key_insights.update(entities)
        top_keywords = extract_keywords(ocr_text, top_n=10)

        summary = ocr_text[:800]
        summary_highlighted = highlight_keywords(summary, key_insights)

        structured_output = {
            "summary": summary_highlighted,
            "key_insights": key_insights,
            "keywords": top_keywords
        }

        analysis_text = json.dumps(structured_output, indent=2)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"AI Processing Error: {str(e)}"}), 500

    # 5️⃣ Get numeric case_id from DB
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT id FROM cases WHERE case_id=%s", (case_id_str,))
        row = cur.fetchone()
        cur.close()

        if not row:
            return jsonify({"error": f"No case found with case_id {case_id_str}"}), 404

        case_id_int = row['id']
    except Exception as e:
        return jsonify({"error": f"Database query error: {str(e)}"}), 500

    # 6️⃣ Insert into ai_results table
    cur = mysql.connection.cursor()
    new_id = None
    try:
        cur.execute("""
            INSERT INTO ai_results (analysis_text, confidence_score, case_id)
            VALUES (%s, %s, %s)
        """, (analysis_text, str(confidence_score), case_id_int))
        mysql.connection.commit()
        new_id = cur.lastrowid
    except Exception as e:
        mysql.connection.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Database insert error", "detail": str(e)}), 500
    finally:
        cur.close()

    # 7️⃣ Return response
    return jsonify({
        "ocr_text": ocr_text[:500] + "..." if len(ocr_text) > 500 else ocr_text,
        "analysis_text": structured_output,
        "inserted_id": new_id,
        "message": "OCR and analysis completed successfully"
    })

def save_ocr_result(case_id_str, analysis_text):
    # Step 1: get numeric case_id from cases table
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT id FROM cases WHERE case_id=%s", (case_id_str,))
    row = cur.fetchone()
    if not row:
        cur.close()
        raise ValueError(f"No case found with case_id {case_id_str}")
    
    numeric_id = row['id']
    cur.close()

    # Step 2: insert into ai_results with numeric case_id
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO ai_results (case_id, analysis_text) VALUES (%s, %s)",
            (numeric_id, analysis_text)
        )
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        raise e
    finally:
        cur.close()


# ----- Placeholder similarity function -----
def perform_similarity(uploaded_text, current_inserted_id=None):
    """
    Calculate similarity between current document and others in database
    current_inserted_id: The ai_results.id of the current document (not case_id!)
    """
    cur = mysql.connection.cursor(DictCursor)

    try:
        # Fetch all other analyzed cases EXCEPT the current one
        # Note: Use 'timestamp' not 'created_at' (based on your table structure)
        query = """
            SELECT ai.id, ai.case_id, c.case_id AS case_code, c.title, ai.analysis_text
            FROM ai_results ai
            JOIN cases c ON ai.case_id = c.id
        """
        
        params = []
        if current_inserted_id:
            query += " WHERE ai.id != %s"
            params.append(current_inserted_id)
        
        cur.execute(query, tuple(params) if params else ())
        rows = cur.fetchall()
        
        if not rows:
            cur.close()
            print("No other analyses found")
            return []

        # Parse uploaded text (current document)
        try:
            parsed = json.loads(uploaded_text)
            base_text = parsed.get("summary", "")
            
            # Also try to get OCR text if summary is empty
            if not base_text or len(base_text.strip()) < 20:
                base_text = parsed.get("ocr_text", "")
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}, using raw text")
            base_text = uploaded_text
        except Exception as e:
            base_text = uploaded_text

        if not base_text or len(base_text.strip()) < 20:
            print(f"Base text too short: {len(base_text.strip()) if base_text else 0} chars")
            cur.close()
            return []

        # Prepare corpus: current text + all other texts
        corpus = [base_text]
        meta = []

        for r in rows:
            analysis_text = r["analysis_text"]
            try:
                parsed = json.loads(analysis_text)
                text = parsed.get("summary", "")
                if not text or len(text.strip()) < 20:
                    text = parsed.get("ocr_text", "")
            except:
                text = analysis_text  # fallback to raw text

            if text and len(text.strip()) >= 20:
                corpus.append(text)
                meta.append({
                    "id": r["id"],
                    "case_id": r["case_code"],  # Use case_code (FQ-2025-XXX)
                    "title": r.get("title", "Untitled Case")
                })
                print(f"Added to corpus: {r['id']} - {len(text)} chars")
            else:
                print(f"Skipping row {r['id']}: text too short ({len(text.strip()) if text else 0} chars)")


        if len(corpus) < 2:
            print("Not enough texts for comparison")
            cur.close()
            return []

        # Compute TF-IDF similarity
        try:
            vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
            tfidf = vectorizer.fit_transform(corpus)
            similarities = cosine_similarity(tfidf[0:1], tfidf[1:])[0]
        except Exception as e:
            import traceback
            traceback.print_exc()
            cur.close()
            return []

        # Prepare results
        results = []
        for i, score in enumerate(similarities):
            if i < len(meta):  # Safety check
                similarity_percent = round(float(score) * 100, 2)
                if similarity_percent > 1:  # 1% threshold (very low for testing)
                    # Compute matching keywords
                    try:
                        parsed_base = set(base_text.lower().split())
                        parsed_other = set(corpus[i+1].lower().split())
                        matching_keywords = list(parsed_base & parsed_other)[:10]
                    except:
                        matching_keywords = []

                    results.append({
                        "case_id": meta[i]["case_id"],  # This should be FQ-2025-XXX
                        "title": meta[i]["title"],
                        "similarity_score": similarity_percent,
                        "matching_keywords": matching_keywords[:5]  # Top 5 keywords
                    })

        # Sort by descending similarity
        results = sorted(results, key=lambda x: x["similarity_score"], reverse=True)
        
        for r in results[:5]:  # Show top 5
            print(f"  - {r['case_id']}: {r['similarity_score']}%")
        
        cur.close()
        return results[:10]  # Return top 10 matches
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        cur.close()
        return []
    
# In your run_similarity route, save the file first:
@app.route("/api/analyze/similarity", methods=["POST"])
def run_similarity_route():
    data = request.json    
    current_analysis_id = data.get("inserted_id")
    
    try:
        # 🔹 Get latest OCR analysis (document-centric)
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT id, analysis_text FROM ai_results WHERE id = %s", (current_analysis_id,))
        row = cur.fetchone()
        cur.close()

        if not row:
            return jsonify({"results": [], "error": "No OCR data found for this analysis"}), 400
                
        # 🔹 Perform similarity against all documents
        results = perform_similarity(row["analysis_text"], current_analysis_id)
        
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE ai_results SET similarity_results=%s WHERE id=%s",
            (json.dumps(results), current_analysis_id)
        )
        mysql.connection.commit()
        cur.close()

        return jsonify({
            "success": True,
            "inserted_id": current_analysis_id,
            "results_count": len(results),
            "results": results
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "results": [], 
            "error": f"Internal similarity error: {str(e)}",
            "detail": traceback.format_exc()
        }), 500
    

# Get latest AI analysis from DB
@app.route("/api/analyze/latest", methods=["GET"])
def latest_analysis():
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT * FROM ai_results ORDER BY timestamp DESC LIMIT 1")
        row = cur.fetchone()
        cur.close()

        if not row:
            return jsonify({"analysis_text": "", "similarity_results": []})

        sim_results = []
        if row.get("similarity_results"):
            try:
                sim_results = json.loads(row["similarity_results"])
            except:
                sim_results = []

        return jsonify({
            "analysis_text": row.get("analysis_text", ""),
            "similarity_results": sim_results
        })

    except Exception as e:
        return jsonify({"ocr_text": "", "similarity_results": [], "error": str(e)})


def generate_case_report(case_code):
    cur = mysql.connection.cursor(DictCursor)

    # 1️⃣ Get case
    cur.execute("SELECT * FROM cases WHERE case_id=%s", (case_code,))
    case = cur.fetchone()
    if not case:
        cur.close()
        return None

    numeric_case_id = case["id"]

    # 2️⃣ Get LATEST AI analysis for this case
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

    # 3️⃣ Final report
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

@app.route("/api/reports/<case_id>", methods=["GET"])
def get_case_report(case_id):
    report = generate_case_report(case_id)
    if not report:
        return jsonify({"error": "Case not found"}), 404
    return jsonify(report)

from routes.reports import reports_bp
app.register_blueprint(reports_bp)

if __name__ == "__main__":
    app.run(debug=True)