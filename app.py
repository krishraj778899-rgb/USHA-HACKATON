import os
import sqlite3
from functools import wraps
from datetime import datetime

from flask import (
    Flask, request, redirect, url_for,
    session, flash, render_template_string
)
from werkzeug.security import generate_password_hash, check_password_hash


# =========================================================
# CARBONFARM - SINGLE FILE FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "carbonfarm-development-secret-change-later"
)

DATABASE = "carbonfarm.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT UNIQUE NOT NULL,
            email TEXT,
            password TEXT NOT NULL,
            state TEXT NOT NULL,
            district TEXT NOT NULL,
            block TEXT,
            village TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS farms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            area REAL DEFAULT 0,
            ownership TEXT,
            crops TEXT,
            crop_history TEXT,
            practices TEXT,
            input_usage TEXT,
            irrigation TEXT,
            soil_management TEXT,
            documents TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            land INTEGER DEFAULT 0,
            crop INTEGER DEFAULT 0,
            practices INTEGER DEFAULT 0,
            inputs INTEGER DEFAULT 0,
            irrigation INTEGER DEFAULT 0,
            soil INTEGER DEFAULT 0,
            documents INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            status TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================================================
# COMMON HTML
# =========================================================

STYLE = """
<style>

*{
    box-sizing:border-box;
    margin:0;
    padding:0;
    font-family:Arial,Helvetica,sans-serif;
}

body{
    background:#f3faf5;
    color:#173522;
}

a{
    text-decoration:none;
    color:#176b3a;
    font-weight:600;
}

.nav{
    height:72px;
    background:white;
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:0 6%;
    box-shadow:0 2px 15px rgba(0,0,0,.06);
}

.logo{
    font-size:27px;
    font-weight:800;
    color:#176b3a;
}

.logo span{
    color:#8ac926;
}

.nav-links{
    display:flex;
    gap:12px;
    align-items:center;
}

.container{
    width:92%;
    max-width:1150px;
    margin:auto;
}

.btn{
    display:inline-block;
    border:none;
    background:#176b3a;
    color:white;
    padding:13px 20px;
    border-radius:11px;
    font-weight:700;
    cursor:pointer;
}

.btn:hover{
    opacity:.9;
}

.btn-outline{
    background:white;
    color:#176b3a;
    border:1px solid #176b3a;
}

.hero{
    min-height:600px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:50px;
}

.hero-content{
    max-width:650px;
}

.badge{
    display:inline-block;
    padding:9px 15px;
    border-radius:30px;
    background:#e3f5e8;
    color:#176b3a;
    font-weight:700;
    margin-bottom:20px;
}

.hero h1{
    font-size:clamp(42px,6vw,68px);
    line-height:1.04;
    margin-bottom:22px;
}

.hero h1 span{
    color:#238b4b;
}

.hero p{
    color:#68756d;
    font-size:18px;
    line-height:1.7;
    margin-bottom:25px;
}

.actions{
    display:flex;
    gap:12px;
    flex-wrap:wrap;
}

.score-card{
    background:white;
    width:330px;
    padding:30px;
    border-radius:22px;
    box-shadow:0 20px 50px rgba(23,107,58,.12);
}

.score{
    font-size:58px;
    font-weight:800;
    color:#176b3a;
    margin:10px 0;
}

.score span{
    font-size:20px;
    color:#888;
}

.progress{
    height:11px;
    background:#e4ece6;
    border-radius:20px;
    overflow:hidden;
    margin:15px 0;
}

.progress div{
    height:100%;
    background:#35a853;
}

.section{
    background:white;
    padding:65px 0;
}

.section-title{
    text-align:center;
    margin-bottom:35px;
}

.section-title h2{
    font-size:35px;
    margin-bottom:10px;
}

.muted{
    color:#718078;
    line-height:1.6;
}

.cards{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:18px;
}

.card{
    background:#fbfefb;
    border:1px solid #dfeae2;
    border-radius:17px;
    padding:25px;
}

.card .icon{
    font-size:30px;
}

.card h3{
    margin:10px 0;
}

.card p{
    color:#6e7972;
    line-height:1.5;
}

footer{
    text-align:center;
    padding:25px;
    color:#718078;
}


/* AUTH */

.auth{
    min-height:100vh;
    display:grid;
    grid-template-columns:1fr 1fr;
}

.auth-left{
    background:linear-gradient(
        145deg,
        #176b3a,
        #0b4d29
    );
    color:white;
    padding:60px;
    display:flex;
    flex-direction:column;
    justify-content:center;
}

.auth-left h1{
    font-size:42px;
    margin:25px 0;
}

.auth-left p{
    color:#d8ebdc;
    line-height:1.7;
    margin:10px 0;
}

.auth-right{
    background:white;
    padding:50px;
    display:flex;
    align-items:center;
}

.form-box{
    width:100%;
    max-width:600px;
    margin:auto;
}

.form-box h2{
    font-size:35px;
    margin-bottom:10px;
}

label{
    display:block;
    font-weight:600;
    margin:13px 0 7px;
}

input,
select,
textarea{
    width:100%;
    border:1px solid #d4dfd7;
    border-radius:10px;
    padding:13px;
    font-size:15px;
    outline:none;
}

input:focus,
select:focus,
textarea:focus{
    border-color:#208447;
}

textarea{
    resize:vertical;
}

.grid-2{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:15px;
}

.full{
    grid-column:1/-1;
}

.form-button{
    width:100%;
    margin-top:20px;
}

.center{
    text-align:center;
    margin-top:20px;
    line-height:2;
}


/* DASHBOARD */

.topbar{
    background:white;
    min-height:72px;
    padding:0 6%;
    display:flex;
    justify-content:space-between;
    align-items:center;
    box-shadow:0 2px 15px rgba(0,0,0,.06);
}

.page{
    padding:45px 0;
}

.page-title{
    margin:20px 0 30px;
}

.dashboard-grid{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:18px;
}

.dashboard-card{
    background:white;
    padding:25px;
    border-radius:17px;
    box-shadow:0 10px 30px rgba(0,0,0,.05);
    color:#173522;
}

.dashboard-card h3{
    margin:10px 0;
}

.form-card{
    background:white;
    padding:30px;
    border-radius:18px;
    box-shadow:0 10px 35px rgba(0,0,0,.06);
    max-width:850px;
    margin:auto;
}

.form-card h2{
    margin-bottom:20px;
}

.result{
    background:white;
    padding:40px;
    border-radius:22px;
    text-align:center;
    max-width:850px;
    margin:30px auto;
    box-shadow:0 15px 40px rgba(0,0,0,.07);
}

.result-score{
    font-size:70px;
    color:#176b3a;
    font-weight:800;
}

.result-score span{
    font-size:22px;
    color:#888;
}

.recommendation{
    padding:17px;
    background:#f1faf3;
    border-left:5px solid #176b3a;
    margin:12px 0;
    border-radius:8px;
}


/* ADMIN */

.stats{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:20px;
    margin-bottom:30px;
}

.stat{
    background:white;
    padding:25px;
    border-radius:17px;
}

.stat h2{
    font-size:38px;
    color:#176b3a;
}

table{
    width:100%;
    border-collapse:collapse;
    background:white;
}

th,td{
    padding:13px;
    border-bottom:1px solid #e5ebe7;
    text-align:left;
}

.flash{
    position:fixed;
    right:20px;
    top:85px;
    z-index:999;
}

.flash-message{
    background:white;
    padding:15px 20px;
    border-radius:10px;
    box-shadow:0 10px 30px rgba(0,0,0,.15);
    margin-bottom:8px;
}


/* MOBILE */

@media(max-width:900px){

    .hero{
        flex-direction:column;
        text-align:center;
        padding:60px 0;
    }

    .actions{
        justify-content:center;
    }

    .cards{
        grid-template-columns:repeat(2,1fr);
    }

    .auth{
        grid-template-columns:1fr;
    }

    .auth-left{
        display:none;
    }

    .dashboard-grid{
        grid-template-columns:repeat(2,1fr);
    }
}

@media(max-width:600px){

    .cards,
    .dashboard-grid,
    .stats,
    .grid-2{
        grid-template-columns:1fr;
    }

    .full{
        grid-column:auto;
    }

    .score-card{
        width:100%;
    }

    .auth-right{
        padding:25px 18px;
    }

    .hero{
        padding:45px 0;
    }

    .nav{
        padding:0 20px;
    }

}

</style>
"""


# =========================================================
# FLASH
# =========================================================

def flashes():

    messages = ""

    for category, message in session.pop("_flashes", []):

        messages += f"""
        <div class="flash-message">
            {message}
        </div>
        """

    if messages:

        return f"""
        <div class="flash">
            {messages}
        </div>
        """

    return ""


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            flash("Please login first.", "warning")

            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper


def admin_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if not session.get("admin"):

            return redirect(url_for("admin_login"))

        return func(*args, **kwargs)

    return wrapper


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template_string(

        STYLE
        + flashes()
        + """

<!DOCTYPE html>

<html>

<head>

<title>CarbonFarm</title>

</head>

<body>

<nav class="nav">

<div class="logo">
Carbon<span>Farm</span>
</div>

<div class="nav-links">

<a href="/login">Login</a>

<a class="btn" href="/register">
Register
</a>

</div>

</nav>


<section class="hero container">

<div class="hero-content">

<div class="badge">
🌱 Carbon Credit Readiness Platform
</div>

<h1>

Check Your Farm's

<span>
Carbon Readiness
</span>

</h1>

<p>

Understand whether your farming practices,
land information, crop history and documentation
are ready for carbon-credit programs.

</p>

<div class="actions">

<a class="btn" href="/register">
Start Assessment →
</a>

<a class="btn btn-outline" href="/login">
Login
</a>

</div>

</div>


<div class="score-card">

<p class="muted">
Example Readiness Score
</p>

<div class="score">
72<span>/100</span>
</div>

<div class="progress">
<div style="width:72%"></div>
</div>

<b>
Good Readiness
</b>

<p class="muted">

Complete your farm information
and documentation to improve
your readiness.

</p>

</div>

</section>


<section class="section">

<div class="container">

<div class="section-title">

<h2>
What We Assess
</h2>

<p class="muted">
Important information used for your readiness assessment.
</p>

</div>


<div class="cards">

<div class="card">
<div class="icon">🌾</div>
<h3>Land Information</h3>
<p>Farm area and ownership information.</p>
</div>

<div class="card">
<div class="icon">🌱</div>
<h3>Crop History</h3>
<p>Previous crops and crop rotation.</p>
</div>

<div class="card">
<div class="icon">♻️</div>
<h3>Farm Practices</h3>
<p>Sustainable farming practices.</p>
</div>

<div class="card">
<div class="icon">💧</div>
<h3>Irrigation</h3>
<p>Irrigation and water management.</p>
</div>

<div class="card">
<div class="icon">🧪</div>
<h3>Input Usage</h3>
<p>Fertilizer and manure information.</p>
</div>

<div class="card">
<div class="icon">🌍</div>
<h3>Soil Management</h3>
<p>Soil management practices.</p>
</div>

<div class="card">
<div class="icon">📄</div>
<h3>Documentation</h3>
<p>Supporting farm documents.</p>
</div>

<div class="card">
<div class="icon">📊</div>
<h3>Readiness Score</h3>
<p>Overall carbon readiness score.</p>
</div>

</div>

</div>

</section>


<footer>

© 2026 CarbonFarm —
Farmer Carbon Credit Readiness Assessment Platform

</footer>

</body>

</html>

"""

    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        email = request.form.get("email", "").strip()
        state = request.form.get("state", "").strip()
        district = request.form.get("district", "").strip()
        block = request.form.get("block", "").strip()
        village = request.form.get("village", "").strip()

        password = request.form.get("password", "")
        confirm = request.form.get("confirmPassword", "")

        if password != confirm:

            flash("Passwords do not match.", "danger")

            return redirect(url_for("register"))

        conn = get_db()

        existing = conn.execute(
            "SELECT id FROM users WHERE mobile=?",
            (mobile,)
        ).fetchone()

        if existing:

            conn.close()

            flash(
                "Mobile number already registered.",
                "danger"
            )

            return redirect(url_for("register"))

        conn.execute(
            """
            INSERT INTO users
            (name,mobile,email,password,state,district,block,village,created_at)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                name,
                mobile,
                email,
                generate_password_hash(password),
                state,
                district,
                block,
                village,
                datetime.now().isoformat()
            )
        )

        conn.commit()
        conn.close()

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect(url_for("login"))


    return render_template_string(

        STYLE
        + flashes()
        + """

<div class="auth">

<div class="auth-left">

<div class="logo">
Carbon<span>Farm</span>
</div>

<h1>
Start Your Carbon-Ready Farming Journey 🌱
</h1>

<p>
📊 Farm Assessment
</p>

<p>
🌱 Readiness Score
</p>

<p>
💡 Recommendations
</p>

</div>


<div class="auth-right">

<div class="form-box">

<h2>
Create Account
</h2>

<p class="muted">
Register as a farmer to start your assessment.
</p>


<form method="POST">

<div class="grid-2">

<div>

<label>
Full Name *
</label>

<input
name="name"
required
placeholder="Enter full name">

</div>


<div>

<label>
Mobile Number *
</label>

<input
name="mobile"
required
pattern="[0-9]{10}"
maxlength="10"
placeholder="10-digit mobile">

</div>


<div class="full">

<label>
Email Address
</label>

<input
name="email"
type="email"
placeholder="Optional">

</div>


<div>

<label>
State *
</label>

<input
name="state"
required
placeholder="Enter state">

</div>


<div>

<label>
District *
</label>

<input
name="district"
required
placeholder="Enter district">

</div>


<div>

<label>
Block
</label>

<input
name="block"
placeholder="Enter block">

</div>


<div>

<label>
Village *
</label>

<input
name="village"
required
placeholder="Enter village">

</div>


<div>

<label>
Password *
</label>

<input
id="password"
name="password"
type="password"
required
minlength="6">

</div>


<div>

<label>
Confirm Password *
</label>

<input
id="confirmPassword"
name="confirmPassword"
type="password"
required
minlength="6">

</div>

</div>


<br>

<label>

<input
type="checkbox"
required
style="width:auto">

I understand that this is a readiness
assessment and does not guarantee
carbon credits or payment.

</label>


<button
class="btn form-button"
type="submit">

Create Account

</button>

</form>


<div class="center">

Already have an account?

<a href="/login">
Login
</a>

<br>

<a href="/">
← Back to Home
</a>

</div>

</div>

</div>

</div>


<script>

document.querySelector("form")
.addEventListener("submit", function(e){

const p =
document.getElementById("password").value;

const cp =
document.getElementById("confirmPassword").value;

if(p !== cp){

e.preventDefault();

alert("Passwords do not match.");

}

});

</script>

"""

    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        identity = request.form.get(
            "identity",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE mobile=? OR email=?
            """,
            (identity, identity)
        ).fetchone()

        conn.close()


        if user and check_password_hash(
            user["password"],
            password
        ):

            session.clear()

            session["user_id"] = user["id"]

            return redirect(
                url_for("dashboard")
            )


        flash(
            "Invalid mobile/email or password.",
            "danger"
        )


    return render_template_string(

        STYLE
        + flashes()
        + """

<div class="auth">

<div class="auth-left">

<div class="logo">
Carbon<span>Farm</span>
</div>

<h1>
Welcome Back, Farmer 🌱
</h1>

<p>
📊 Track Your Readiness
</p>

<p>
🌾 Manage Your Farm
</p>

<p>
💡 Get Recommendations
</p>

</div>


<div class="auth-right">

<div class="form-box">

<h2>
Login
</h2>

<p class="muted">
Login to access your CarbonFarm account.
</p>


<form method="POST">

<label>
Mobile Number / Email
</label>

<input
name="identity"
required
placeholder="Mobile or email">


<label>
Password
</label>

<input
name="password"
type="password"
required
placeholder="Password">


<div style="margin:15px 0">

<a href="/forgot-password">
Forgot Password?
</a>

</div>


<button
class="btn form-button"
type="submit">

Login

</button>

</form>


<div class="center">

Don't have an account?

<a href="/register">
Create Account
</a>

<br>

<a href="/">
← Back to Home
</a>

</div>

</div>

</div>

</div>

"""

    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        flash(
            "Password recovery will be connected later.",
            "info"
        )

        return redirect(
            url_for("login")
        )


    return render_template_string(

        STYLE
        + flashes()
        + """

<div class="container page">

<div class="form-card">

<h2>
Forgot Password
</h2>

<p class="muted">
Enter your registered mobile number or email.
</p>

<form method="POST">

<label>
Mobile / Email
</label>

<input
name="identity"
required>

<button class="btn form-button">
Continue
</button>

</f
