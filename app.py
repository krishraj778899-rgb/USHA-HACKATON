from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "carbonfarm.db")


# ================= DATABASE =================

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS farm_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            farm_name TEXT,
            location TEXT,
            land_area REAL,
            land_type TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            farm_id INTEGER,

            land_area REAL,
            land_type TEXT,

            crop_history TEXT,

            farming_practices TEXT,

            irrigation_source TEXT,
            irrigation_method TEXT,

            fertilizer_usage TEXT,
            pesticide_usage TEXT,

            soil_testing TEXT,
            compost_usage TEXT,
            crop_rotation TEXT,

            documents TEXT,

            score INTEGER,
            status TEXT,
            summary TEXT,

            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ================= SCORE ENGINE =================

def calculate_score(data):

    score = 0
    breakdown = {}

    # 1. LAND - 15
    land = float(data.get("landArea") or 0)

    if land > 0:
        breakdown["land"] = 15
        score += 15
    else:
        breakdown["land"] = 0

    # 2. CROP HISTORY - 15
    crop = data.get("cropHistory", "").strip()

    if crop:
        breakdown["crop"] = 15
        score += 15
    else:
        breakdown["crop"] = 0

    # 3. FARMING PRACTICES - 20
    practice = data.get("farmingPractices", "").strip()

    if practice == "multiple":
        practice_score = 20
    elif practice:
        practice_score = 15
    else:
        practice_score = 0

    breakdown["practices"] = practice_score
    score += practice_score

    # 4. IRRIGATION - 10
    irrigation = data.get("irrigationSource", "").strip()

    if irrigation:
        breakdown["irrigation"] = 10
        score += 10
    else:
        breakdown["irrigation"] = 0

    # 5. INPUT USAGE - 10
    fertilizer = data.get("fertilizerUsage", "").strip()
    pesticide = data.get("pesticideUsage", "").strip()

    if fertilizer and pesticide:
        input_score = 10
    elif fertilizer or pesticide:
        input_score = 5
    else:
        input_score = 0

    breakdown["inputs"] = input_score
    score += input_score

    # 6. SOIL MANAGEMENT - 15
    soil_test = data.get("soilTesting", "").strip()
    compost = data.get("compostUsage", "").strip()
    rotation = data.get("cropRotation", "").strip()

    soil_score = 0

    if soil_test:
        soil_score += 5

    if compost:
        soil_score += 5

    if rotation:
        soil_score += 5

    breakdown["soil"] = soil_score
    score += soil_score

    # 7. DOCUMENTS - 15
    documents = data.get("documents", "").strip()

    if documents == "complete":
        document_score = 15
    elif documents == "partial":
        document_score = 10
    elif documents == "limited":
        document_score = 5
    else:
        document_score = 0

    breakdown["documents"] = document_score
    score += document_score

    score = min(score, 100)

    # STATUS
    if score >= 80:
        status = "🟢 Highly Ready"
        summary = "Your farm is highly ready for carbon credit assessment."

    elif score >= 60:
        status = "🟡 Moderately Ready"
        summary = "Your farm has a good foundation but needs some improvements."

    else:
        status = "🔴 Needs Improvement"
        summary = "Your farm needs additional practices and documentation."

    # RECOMMENDATIONS
    recommendations = []

    if breakdown["land"] == 0:
        recommendations.append("Add valid land information.")

    if breakdown["crop"] == 0:
        recommendations.append("Add your crop cultivation history.")

    if breakdown["practices"] < 20:
        recommendations.append("Adopt more sustainable farming practices.")

    if breakdown["irrigation"] == 0:
        recommendations.append("Add irrigation and water management information.")

    if breakdown["inputs"] < 10:
        recommendations.append("Improve and document fertilizer and pesticide management.")

    if breakdown["soil"] < 15:
        recommendations.append("Improve soil testing, composting and crop rotation.")

    if breakdown["documents"] < 15:
        recommendations.append("Maintain complete supporting farm documents.")

    if not recommendations:
        recommendations.append(
            "Continue maintaining sustainable farming practices and records."
        )

    return score, status, summary, breakdown, recommendations


# ================= FRONTEND =================

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css")
def style():
    return send_from_directory(BASE_DIR, "style.css")


@app.route("/script.js")
def script():
    return send_from_directory(BASE_DIR, "script.js")


@app.route("/admin.html")
def admin():
    return send_from_directory(BASE_DIR, "admin.html")


@app.route("/admin.css")
def admin_css():
    return send_from_directory(BASE_DIR, "admin.css")


# ================= HEALTH =================

@app.route("/api/health")
def health():
    return jsonify({
        "success": True,
        "message": "CarbonFarm backend is running"
    })


# ================= REGISTER =================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "All fields are required."
        }), 400

    conn = db()

    try:

        cursor = conn.execute("""
            INSERT INTO users
            (name, email, password, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            password,
            datetime.now().isoformat()
        ))

        conn.commit()

        user_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Registration successful",
            "userId": user_id
        })

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Email already registered."
        }), 409

    finally:
        conn.close()


# ================= LOGIN =================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    conn = db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE email = ? AND password = ?
    """, (
        email,
        password
    )).fetchone()

    conn.close()

    if not user:

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    })


# ================= FARM PROFILE =================

@app.route("/api/farm-profile", methods=["POST"])
def farm_profile():

    data = request.get_json() or {}

    user_id = data.get("userId")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "User ID required."
        }), 400

    conn = db()

    cursor = conn.execute("""
        INSERT INTO farm_profiles
        (
            user_id,
            farm_name,
            location,
            land_area,
            land_type,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        data.get("farmName", ""),
        data.get("location", ""),
        data.get("landArea", 0),
        data.get("landType", ""),
        datetime.now().isoformat()
    ))

    conn.commit()

    farm_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "success": True,
        "message": "Farm profile saved",
        "farmId": farm_id
    })


# ================= START ASSESSMENT =================

@app.route("/api/assessment", methods=["POST"])
def assessment():

    data = request.get_json() or {}

    score, status, summary, breakdown, recommendations = \
        calculate_score(data)

    conn = db()

    cursor = conn.execute("""
        INSERT INTO assessments
        (
            user_id,
            farm_id,
            land_area,
            land_type,
            crop_history,
            farming_practices,
            irrigation_source,
            irrigation_method,
            fertilizer_usage,
            pesticide_usage,
            soil_testing,
            compost_usage,
            crop_rotation,
            documents,
            score,
            status,
            summary,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        data.get("userId"),

        data.get("farmId"),

        data.get("landArea", 0),

        data.get("landType", ""),

        data.get("cropHistory", ""),

        data.get("farmingPractices", ""),

        data.get("irrigationSource", ""),

        data.get("irrigationMethod", ""),

        data.get("fertilizerUsage", ""),

        data.get("pesticideUsage", ""),

        data.get("soilTesting", ""),

        data.get("compostUsage", ""),

        data.get("cropRotation", ""),

        data.get("documents", ""),

        score,

        status,

        summary,

        datetime.now().isoformat()
    ))

    assessment_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "assessment": {
            "assessmentId": assessment_id,
            "score": score,
            "status": status,
            "summary": summary,
            "breakdown": breakdown,
            "recommendations": recommendations
        }
    })


# ================= GET ASSESSMENT =================

@app.route("/api/assessment/<int:assessment_id>")
def get_assessment(assessment_id):

    conn = db()

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
        "assessment": dict(row)
    })


# ================= ADMIN STATS =================

@app.route("/api/admin/stats")
def admin_stats():

    conn = db()

    total = conn.execute(
        "SELECT COUNT(*) FROM assessments"
    ).fetchone()[0]

    highly = conn.execute(
        "SELECT COUNT(*) FROM assessments WHERE score >= 80"
    ).fetchone()[0]

    moderate = conn.execute(
        "SELECT COUNT(*) FROM assessments WHERE score >= 60 AND score < 80"
    ).fetchone()[0]

    improve = conn.execute(
        "SELECT COUNT(*) FROM assessments WHERE score < 60"
    ).fetchone()[0]

    average = conn.execute(
        "SELECT AVG(score) FROM assessments"
    ).fetchone()[0]

    conn.close()

    return jsonify({
        "success": True,
        "stats": {
            "totalAssessments": total,
            "highlyReady": highly,
            "moderatelyReady": moderate,
            "needsImprovement": improve,
            "averageScore": round(average or 0, 1)
        }
    })


# ================= ADMIN ASSESSMENTS =================

@app.route("/api/admin/assessments")
def admin_assessments():

    conn = db()

    rows = conn.execute("""
        SELECT
            id,
            user_id,
            farm_id,
            land_area,
            crop_history,
            farming_practices,
            irrigation_source,
            fertilizer_usage,
            pesticide_usage,
            soil_testing,
            compost_usage,
            crop_rotation,
            documents,
            score,
            status,
            summary,
            created_at
        FROM assessments
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify({
        "success": True,
        "assessments": [dict(row) for row in rows]
    })


# ================= RUN =================

if __name__ == "__main__":

    init_db()

    print("\n================================")
    print("🌱 CARBONFARM")
    print("================================")
    print("Server: http://127.0.0.1:5000")
    print("================================\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
    from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "carbonfarm.db")


# ================= DATABASE =================

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS farm_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            farm_name TEXT,
            location TEXT,
            land_area REAL,
            land_type TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            farm_id INTEGER,

            land_area REAL,
            land_type TEXT,

            crop_history TEXT,

            farming_practices TEXT,

            irrigation_source TEXT,
            irrigation_method TEXT,

            fertilizer_usage TEXT,
            pesticide_usage TEXT,

            soil_testing TEXT,
            compost_usage TEXT,
            crop_rotation TEXT,

            documents TEXT,

            score INTEGER,
            status TEXT,
            summary TEXT,

            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ================= SCORE ENGINE =================

def calculate_score(data):

    score = 0
    breakdown = {}

    # 1. LAND - 15
    land = float(data.get("landArea") or 0)

    if land > 0:
        breakdown["land"] = 15
        score += 15
    else:
        breakdown["land"] = 0

    # 2. CROP HISTORY - 15
    crop = data.get("cropHistory", "").strip()

    if crop:
        breakdown["crop"] = 15
        score += 15
    else:
        breakdown["crop"] = 0

    # 3. FARMING PRACTICES - 20
    practice = data.get("farmingPractices", "").strip()

    if practice == "multiple":
        practice_score = 20
    elif practice:
        practice_score = 15
    else:
        practice_score = 0

    breakdown["practices"] = practice_score
    score += practice_score

    # 4. IRRIGATION - 10
    irrigation = data.get("irrigationSource", "").strip()

    if irrigation:
        breakdown["irrigation"] = 10
        score += 10
    else:
        breakdown["irrigation"] = 0

    # 5. INPUT USAGE - 10
    fertilizer = data.get("fertilizerUsage", "").strip()
    pesticide = data.get("pesticideUsage", "").strip()

    if fertilizer and pesticide:
        input_score = 10
    elif fertilizer or pesticide:
        input_score = 5
    else:
        input_score = 0

    breakdown["inputs"] = input_score
    score += input_score

    # 6. SOIL MANAGEMENT - 15
    soil_test = data.get("soilTesting", "").strip()
    compost = data.get("compostUsage", "").strip()
    rotation = data.get("cropRotation", "").strip()

    soil_score = 0

    if soil_test:
        soil_score += 5

    if compost:
        soil_score += 5

    if rotation:
        soil_score += 5

    breakdown["soil"] = soil_score
    score += soil_score

    # 7. DOCUMENTS - 15
    documents = data.get("documents", "").strip()

    if documents == "complete":
        document_score = 15
    elif documents == "partial":
        document_score = 10
    elif documents == "limited":
        document_score = 5
    else:
        document_score = 0

    breakdown["documents"] = document_score
    score += document_score

    score = min(score, 100)

    # STATUS
    if score >= 80:
        status = "🟢 Highly Ready"
        summary = "Your farm is highly ready for carbon credit assessment."

    elif score >= 60:
        status = "🟡 Moderately Ready"
        summary = "Your farm has a good foundation but needs some improvements."

    else:
        status = "🔴 Needs Improvement"
        summary = "Your farm needs additional practices and documentation."

    # RECOMMENDATIONS
    recommendations = []

    if breakdown["land"] == 0:
        recommendations.append("Add valid land information.")

    if breakdown["crop"] == 0:
        recommendations.append("Add your crop cultivation history.")

    if breakdown["practices"] < 20:
        recommendations.append("Adopt more sustainable farming practices.")

    if breakdown["irrigation"] == 0:
        recommendations.append("Add irrigation and water management information.")

    if breakdown["inputs"] < 10:
        recommendations.append("Improve and document fertilizer and pesticide management.")

    if breakdown["soil"] < 15:
        recommendations.append("Improve soil testing, composting and crop rotation.")

    if breakdown["documents"] < 15:
        recommendations.append("Maintain complete supporting farm documents.")

    if not recommendations:
        recommendations.append(
            "Continue maintaining sustainable farming practices and records."
        )

    return score, status, summary, breakdown, recommendations


# ================= FRONTEND =================

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css")
def style():
    return send_from_directory(BASE_DIR, "style.css")


@app.route("/script.js")
def script():
    return send_from_directory(BASE_DIR, "script.js")


@app.route("/admin.html")
def admin():
    return send_from_directory(BASE_DIR, "admin.html")


@app.route("/admin.css")
def admin_css():
    return send_from_directory(BASE_DIR, "admin.css")


# ================= HEALTH =================

@app.route("/api/health")
def health():
    return jsonify({
        "success": True,
        "message": "CarbonFarm backend is running"
    })


# ================= REGISTER =================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "All fields are required."
        }), 400

    conn = db()

    try:

        cursor = conn.execute("""
            INSERT INTO users
            (name, email, password, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            password,
            datetime.now().isoformat()
        ))

        conn.commit()

        user_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Registration successful",
            "userId": user_id
        })

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Email already registered."
        }), 409

    finally:
        conn.close()


# ================= LOGIN =================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    conn = db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE email = ? AND password = ?
    """, (
        email,
        password
    )).fetchone()

    conn.close()

    if not user:

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    })


# ================= FARM PROFILE =================

@app.route("/api/farm-profile", methods=["POST"])
def farm_profile():

    data = request.get_json() or {}

    user_id = data.get("userId")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "User ID required."
        }), 400

    conn = db()

    cursor = conn.execute("""
        INSERT INTO farm_profiles
        (
            user_id,
            farm_name,
            location,
            land_area,
            land_type,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        data.get("farmName", ""),
        data.get("location", ""),
        data.get("landArea", 0),
        data.get("landType", ""),
        datetime.now().isoformat()
    ))

    conn.commit()

    farm_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "success": True,
        "message": "Farm profile saved",
        "farmId": farm_id
    })


# ================= START ASSESSMENT =================

@app.route("/api/assessment", methods=["POST"])
def assessment():

    data = request.get_json() or {}

    score, status, summary, breakdown, recommendations = \
        calculate_score(data)

    conn = db()

    cursor = conn.execute("""
        INSERT INTO assessments
        (
            user_id,
            farm_id,
            land_area,
            land_type,
            crop_history,
            farming_practices,
            irrigation_source,
            irrigation_method,
            fertilizer_usage,
            pesticide_usage,
            soil_testing,
            compost_usage,
            crop_rotation,
            documents,
            score,
            status,
            summary,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        data.get("userId"),

        data.get("farmId"),

        data.get("landArea", 0),

        data.get("landType", ""),

        data.get("cropHistory", ""),

        data.get("farmingPractices", ""),

        data.get("irrigationSource", ""),

        data.get("irrigationMethod", ""),

        data.get("fertilizerUsage", ""),

        data.get("pesticideUsage", ""),

        data.get("soilTesting", ""),

        data.get("compostUsage", ""),

        data.get("cropRotation", ""),

        data.get("documents", ""),

        score,

        status,

        summary,

        datetime.now().isoformat()
    ))

    assessment_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "assessment": {
            "assessmentId": assessment_id,
            "score": score,
            "status": status,
            "summary": summary,
            "breakdown": breakdown,
            "recommendations": recommendations
        }
    })


# ================= GET ASSESSMENT =================

@app.route("/api/assessment/<int:assessment_id>")
def get_assessment(assessment_id):

    conn = db()

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
        "assessment": dict(row)
    })


# ================= ADMIN STATS =================

@app.route("/api/admin/stats")
def admin_stats():

    conn = db()

    total = conn.execute(
        "SELECT COUNT(*) FROM assessments"
    ).fetchone()[0]

    highly = conn.execute(
        "SELECT COUNT(*) FROM assessments WHERE score >= 80"
    ).fetchone()[0]

    moderate = conn.execute(
        "SELECT COUNT(*) FROM assessments WHERE score >= 60 AND score < 80"
    ).fetchone()[0]

    improve = conn.execute(
        "SELECT COUNT(*) FROM assessments WHERE score < 60"
    ).fetchone()[0]

    average = conn.execute(
        "SELECT AVG(score) FROM assessments"
    ).fetchone()[0]

    conn.close()

    return jsonify({
        "success": True,
        "stats": {
            "totalAssessments": total,
            "highlyReady": highly,
            "moderatelyReady": moderate,
            "needsImprovement": improve,
            "averageScore": round(average or 0, 1)
        }
    })


# ================= ADMIN ASSESSMENTS =================

@app.route("/api/admin/assessments")
def admin_assessments():

    conn = db()

    rows = conn.execute("""
        SELECT
            id,
            user_id,
            farm_id,
            land_area,
            crop_history,
            farming_practices,
            irrigation_source,
            fertilizer_usage,
            pesticide_usage,
            soil_testing,
            compost_usage,
            crop_rotation,
            documents,
            score,
            status,
            summary,
            created_at
        FROM assessments
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify({
        "success": True,
        "assessments": [dict(row) for row in rows]
    })


# ================= RUN =================

if __name__ == "__main__":

    init_db()

    print("\n================================")
    print("🌱 CARBONFARM")
    print("================================")
    print("Server: http://127.0.0.1:5000")
    print("================================\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )