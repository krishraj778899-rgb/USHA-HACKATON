from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "carbonfarm.db")


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_name TEXT NOT NULL,
            land_area REAL NOT NULL,
            main_crop TEXT NOT NULL,
            practice TEXT NOT NULL,
            documents TEXT NOT NULL,
            score INTEGER NOT NULL,
            status TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# ASSESSMENT ENGINE
# =========================================================

def calculate_assessment(data):

    farmer_name = str(data.get("farmerName", "")).strip()
    main_crop = str(data.get("mainCrop", "")).strip()
    practice = str(data.get("practice", "")).strip()
    documents = str(data.get("documents", "")).strip()

    try:
        land_area = float(data.get("landArea", 0))
    except (ValueError, TypeError):
        land_area = 0

    # Land
    land_score = 20 if land_area > 0 else 0

    # Crop
    crop_score = 15 if main_crop else 0

    # Farming practice
    if practice == "multiple":
        practice_score = 30
    elif practice in ["organic", "water", "soil"]:
        practice_score = 25
    else:
        practice_score = 0

    # Documents
    if documents == "complete":
        document_score = 35
    elif documents == "partial":
        document_score = 20
    elif documents == "limited":
        document_score = 10
    else:
        document_score = 0

    score = min(
        land_score +
        crop_score +
        practice_score +
        document_score,
        100
    )

    # Status
    if score >= 80:
        status = "🟢 Highly Ready"
        summary = (
            "Your farm shows strong readiness for "
            "carbon credit assessment and documentation."
        )

    elif score >= 60:
        status = "🟡 Moderately Ready"
        summary = (
            "Your farm has a good foundation, but some "
            "improvements and additional evidence are recommended."
        )

    else:
        status = "🔴 Needs Improvement"
        summary = (
            "Your farm needs additional practices and "
            "documentation before it is fully ready."
        )

    # Missing evidence
    missing_evidence = []

    if land_score == 0:
        missing_evidence.append("Valid land information")

    if crop_score == 0:
        missing_evidence.append("Main crop information")

    if practice_score == 0:
        missing_evidence.append("Sustainable farming practice")

    if document_score < 35:
        missing_evidence.append("Complete supporting documents")

    # Recommendations
    recommendations = []

    if practice_score < 30:
        recommendations.append(
            "Adopt more sustainable farming practices."
        )

    if document_score < 35:
        recommendations.append(
            "Maintain complete farm and practice documentation."
        )

    if land_score == 0:
        recommendations.append(
            "Provide accurate land area information."
        )

    if crop_score == 0:
        recommendations.append(
            "Add the primary crop information."
        )

    if not recommendations:
        recommendations.append(
            "Continue maintaining sustainable practices and records."
        )

    return {
        "farmerName": farmer_name,
        "landArea": land_area,
        "mainCrop": main_crop,
        "practice": practice,
        "documents": documents,
        "score": score,
        "status": status,
        "summary": summary,
        "breakdown": {
            "land": land_score,
            "crop": crop_score,
            "practice": practice_score,
            "documents": document_score
        },
        "missingEvidence": missing_evidence,
        "recommendations": recommendations
    }


# =========================================================
# FRONTEND
# =========================================================

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css")
def style():
    return send_from_directory(BASE_DIR, "style.css")


@app.route("/script.js")
def script():
    return send_from_directory(BASE_DIR, "script.js")


# =========================================================
# HEALTH
# =========================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "message": "CarbonFarm backend is running",
        "status": "online"
    })


# =========================================================
# CREATE ASSESSMENT
# =========================================================

@app.route("/api/assessment", methods=["POST"])
def create_assessment():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No assessment data received"
            }), 400

        result = calculate_assessment(data)

        if not result["farmerName"]:
            return jsonify({
                "success": False,
                "message": "Farmer name is required"
            }), 400

        if result["landArea"] <= 0:
            return jsonify({
                "success": False,
                "message": "Valid land area is required"
            }), 400

        if not result["mainCrop"]:
            return jsonify({
                "success": False,
                "message": "Main crop is required"
            }), 400

        conn = get_db()

        cursor = conn.execute("""
            INSERT INTO assessments (
                farmer_name,
                land_area,
                main_crop,
                practice,
                documents,
                score,
                status,
                summary,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result["farmerName"],
            result["landArea"],
            result["mainCrop"],
            result["practice"],
            result["documents"],
            result["score"],
            result["status"],
            result["summary"],
            datetime.now().isoformat()
        ))

        assessment_id = cursor.lastrowid

        conn.commit()
        conn.close()

        result["assessmentId"] = assessment_id

        return jsonify({
            "success": True,
            "message": "Assessment completed successfully",
            "assessment": result
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Assessment failed",
            "error": str(e)
        }), 500


# =========================================================
# GET SINGLE ASSESSMENT
# =========================================================

@app.route("/api/assessment/<int:assessment_id>", methods=["GET"])
def get_assessment(assessment_id):

    conn = get_db()

    row = conn.execute("""
        SELECT *
        FROM assessments
        WHERE id = ?
    """, (assessment_id,)).fetchone()

    conn.close()

    if not row:
        return jsonify({
            "success": False,
            "message": "Assessment not found"
        }), 404

    return jsonify({
        "success": True,
        "assessment": {
            "assessmentId": row["id"],
            "farmerName": row["farmer_name"],
            "landArea": row["land_area"],
            "mainCrop": row["main_crop"],
            "practice": row["practice"],
            "documents": row["documents"],
            "score": row["score"],
            "status": row["status"],
            "summary": row["summary"],
            "createdAt": row["created_at"]
        }
    })


# =========================================================
# ADMIN - ALL ASSESSMENTS
# =========================================================

@app.route("/api/admin/assessments", methods=["GET"])
def admin_assessments():

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM assessments
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    assessments = []

    for row in rows:

        assessments.append({
            "id": row["id"],
            "farmerName": row["farmer_name"],
            "landArea": row["land_area"],
            "mainCrop": row["main_crop"],
            "practice": row["practice"],
            "documents": row["documents"],
            "score": row["score"],
            "status": row["status"],
            "summary": row["summary"],
            "createdAt": row["created_at"]
        })

    return jsonify({
        "success": True,
        "count": len(assessments),
        "assessments": assessments
    })


# =========================================================
# ADMIN - DASHBOARD STATISTICS
# =========================================================

@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():

    conn = get_db()

    total = conn.execute("""
        SELECT COUNT(*) AS total
        FROM assessments
    """).fetchone()["total"]

    highly_ready = conn.execute("""
        SELECT COUNT(*) AS total
        FROM assessments
        WHERE score >= 80
    """).fetchone()["total"]

    moderately_ready = conn.execute("""
        SELECT COUNT(*) AS total
        FROM assessments
        WHERE score >= 60 AND score < 80
    """).fetchone()["total"]

    needs_improvement = conn.execute("""
        SELECT COUNT(*) AS total
        FROM assessments
        WHERE score < 60
    """).fetchone()["total"]

    average_score = conn.execute("""
        SELECT AVG(score) AS average
        FROM assessments
    """).fetchone()["average"]

    conn.close()

    return jsonify({
        "success": True,
        "stats": {
            "totalAssessments": total,
            "highlyReady": highly_ready,
            "moderatelyReady": moderately_ready,
            "needsImprovement": needs_improvement,
            "averageScore": round(average_score or 0, 1)
        }
    })


# =========================================================
# ADMIN - RECENT ASSESSMENTS
# =========================================================

@app.route("/api/admin/recent", methods=["GET"])
def admin_recent():

    conn = get_db()

    rows = conn.execute("""
        SELECT
            id,
            farmer_name,
            land_area,
            main_crop,
            score,
            status,
            created_at
        FROM assessments
        ORDER BY id DESC
        LIMIT 10
    """).fetchall()

    conn.close()

    data = []

    for row in rows:

        data.append({
            "id": row["id"],
            "farmerName": row["farmer_name"],
            "landArea": row["land_area"],
            "mainCrop": row["main_crop"],
            "score": row["score"],
            "status": row["status"],
            "createdAt": row["created_at"]
        })

    return jsonify({
        "success": True,
        "assessments": data
    })


# =========================================================
# ADMIN - DELETE ASSESSMENT
# =========================================================

@app.route("/api/admin/assessment/<int:assessment_id>", methods=["DELETE"])
def delete_assessment(assessment_id):

    conn = get_db()

    cursor = conn.execute("""
        DELETE FROM assessments
        WHERE id = ?
    """, (assessment_id,))

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    if deleted == 0:
        return jsonify({
            "success": False,
            "message": "Assessment not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Assessment deleted successfully"
    })


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    init_db()

    print("")
    print("========================================")
    print("        🌱 CARBONFARM BACKEND")
    print("========================================")
    print("Server : http://127.0.0.1:5000")
    print("Health : http://127.0.0.1:5000/api/health")
    print("Admin  : /api/admin/stats")
    print("========================================")
    print("")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )