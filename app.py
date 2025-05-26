import os
import re
import base64
import sqlite3
import secrets
import smtplib
from flask_cors import CORS
from sqlite3 import IntegrityError
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from email.mime.text import MIMEText
from urllib.parse import urlencode
import io
import razorpay
import json
from flask import request
import time
from flask import make_response
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import flash
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, session, redirect, url_for, request
from markupsafe import escape

conn = sqlite3.connect("alumni.db")
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  
ADMIN_SECURITY_KEY = "admin123" 
CORS(app, supports_credentials=True)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "keerthanaaprabakaran1@gmail.com" 
EMAIL_PASSWORD = "tpqd ovrc hztf tmkk"  
BASE_URL = "http://localhost:5000"
RAZORPAY_KEY_ID = 'rzp_test_ekuUcHA0UOfU6z'  
RAZORPAY_KEY_SECRET = 'KTu5xQhLEEo0FaKC0uHz2bwW'   
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

DB_PATH = Path(__file__).parent / "alumni.db"
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
def get_user_role(email):
    with get_db() as conn:
        user = conn.execute("SELECT role FROM user WHERE email = ?", (email,)).fetchone()
        return user['role'] if user else 'student'
def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            graduation_year INTEGER,
            verified BOOLEAN DEFAULT 0,
            active BOOLEAN DEFAULT 1,
            failed_attempts INTEGER DEFAULT 0,
            locked_until TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, 
            privacy TEXT DEFAULT 'public'              
        );

        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES user(id),
            bio TEXT,
            current_job TEXT,
            company TEXT,
            skills TEXT,
            profile_pic TEXT
        );
        CREATE TABLE IF NOT EXISTS mentor_session (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            alumni_id INTEGER NOT NULL,
            session_start_time DATETIME NOT NULL,
            session_meet_link TEXT,
            session_description TEXT NOT NULL,
            session_started BOOLEAN DEFAULT 0,
            mentor_name TEXT NOT NULL,
            mentor_field TEXT NOT NULL,
            session_time DATETIME NOT NULL,
            mentor_image TEXT,
            FOREIGN KEY(alumni_id) REFERENCES user(id)
        );

        CREATE TABLE IF NOT EXISTS session_member (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            joined_session BOOLEAN DEFAULT 0,
            FOREIGN KEY(session_id) REFERENCES mentor_session(session_id),
            FOREIGN KEY(student_id) REFERENCES user(id)
        );

        CREATE TABLE IF NOT EXISTS session_message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            content TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES mentor_session(session_id),
            FOREIGN KEY(user_id) REFERENCES user(id)
        );
        
       CREATE TABLE IF NOT EXISTS job (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employer_id INTEGER REFERENCES user(id),
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            description TEXT NOT NULL,
            experience TEXT,  
            skills TEXT,      
            job_type TEXT,   
            posted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            active BOOLEAN DEFAULT 1,
            location TEXT
        );

        CREATE TABLE IF NOT EXISTS event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organizer_id INTEGER REFERENCES user(id),
            title TEXT NOT NULL,
            description TEXT,
            location TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            image TEXT
        );

        CREATE TABLE IF NOT EXISTS job_application (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER REFERENCES job(id),
            applicant_name TEXT NOT NULL,
            applicant_email TEXT NOT NULL,
            applicant_phone TEXT NOT NULL,
            applicant_address TEXT NOT NULL,
            resume TEXT NOT NULL,
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(job_id, applicant_email)
        );

        CREATE TABLE IF NOT EXISTS password_reset_token (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES user(id),
            token TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used BOOLEAN DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS skill (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            percentage INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user(id)
        );
        CREATE TABLE IF NOT EXISTS role_change_request (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            requested_role TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            requested_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id)
        );
                           
            
        CREATE TABLE IF NOT EXISTS connection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL REFERENCES user(id),
            receiver_id INTEGER NOT NULL REFERENCES user(id),
            status TEXT DEFAULT 'pending',  -- 'pending', 'accepted', 'rejected'
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(sender_id, receiver_id)
        );
        CREATE TABLE IF NOT EXISTS notification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES user(id),
            message TEXT NOT NULL,
            related_entity TEXT,  -- 'connection', 'message', etc.
            related_entity_id INTEGER,
            is_read BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_block (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blocker_id INTEGER NOT NULL REFERENCES user(id),
            blocked_id INTEGER NOT NULL REFERENCES user(id),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(blocker_id, blocked_id)  -- Prevents duplicate blocks
        ); 
        CREATE TABLE IF NOT EXISTS message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES user(id),
            FOREIGN KEY (receiver_id) REFERENCES user(id)
        );      
        CREATE TABLE IF NOT EXISTS rsvp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES user(id),
            event_id INTEGER NOT NULL REFERENCES event(id),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, event_id)
        );
                           
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            read BOOLEAN DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES user(id)
        );                 
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES user(id),
            campaign_name TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_id TEXT NOT NULL UNIQUE,
            donation_date TEXT DEFAULT CURRENT_TIMESTAMP,
            receipt_generated BOOLEAN DEFAULT 0
        );   
        CREATE TABLE IF NOT EXISTS event_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES user(id),
            event_id INTEGER NOT NULL REFERENCES event(id),
            reminder_type TEXT NOT NULL,  -- '3day', '2day', '1day'
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, event_id, reminder_type)
        );
        CREATE TABLE IF NOT EXISTS role_change_request (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            requested_role TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            requested_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id)
        );
        CREATE TABLE IF NOT EXISTS deleted_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            role TEXT DEFAULT 'user',
            graduation_year INTEGER,
            verified BOOLEAN DEFAULT 0,
            active BOOLEAN DEFAULT 0,
            created_at TEXT,
            privacy TEXT DEFAULT 'public',
            failed_attempts INTEGER DEFAULT 0,
            locked_until TEXT,
            deleted_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_rsvp_user_event ON rsvp(user_id, event_id);
        CREATE INDEX IF NOT EXISTS idx_event_start_time ON event(start_time);
        """)

try:
    conn.execute("ALTER TABLE user ADD COLUMN first_name TEXT")
except sqlite3.OperationalError:
    pass
try:
    conn.execute("ALTER TABLE user ADD COLUMN last_name TEXT")
except sqlite3.OperationalError:
    pass
try:
    conn.execute("ALTER TABLE user ADD COLUMN department TEXT")
except sqlite3.OperationalError:
    pass
try:
    conn.execute("ALTER TABLE user ADD COLUMN resume BLOB")
except sqlite3.OperationalError:
    pass
try:
    conn.execute("ALTER TABLE user ADD COLUMN privacy TEXT DEFAULT 'public'")
except sqlite3.OperationalError:
    pass  # Column already exists
try:
    conn.execute("ALTER TABLE user ADD COLUMN avatar BLOB")
except sqlite3.OperationalError:
    pass  # column already exists
try:
    conn.execute("ALTER TABLE job ADD COLUMN experience TEXT")
except sqlite3.OperationalError:
    pass
try:
    conn.execute("ALTER TABLE job ADD COLUMN skills TEXT")
except sqlite3.OperationalError:
    pass
try:
    conn.execute("ALTER TABLE job ADD COLUMN job_type TEXT")
except sqlite3.OperationalError:
    pass
try:
    conn.execute("ALTER TABLE job ADD COLUMN location TEXT")
except sqlite3.OperationalError:
    pass
try:
    conn.execute("ALTER TABLE job_application ADD COLUMN applicant_phone TEXT")
except sqlite3.OperationalError:
    pass
try:
    conn.execute("ALTER TABLE job_application ADD COLUMN applicant_address TEXT")
except sqlite3.OperationalError:
    pass
try:
    conn.execute("ALTER TABLE user_block ADD COLUMN notes TEXT")
except sqlite3.OperationalError:
    pass
try:
    conn.execute("ALTER TABLE user ADD COLUMN last_failed_attempt TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass 

try:
    conn.execute("ALTER TABLE deleted_users ADD COLUMN password_hash TEXT")
except sqlite3.OperationalError:
    pass 
conn.commit()


if not conn.execute("SELECT 1 FROM user WHERE email='test@example.com'").fetchone():
    conn.execute(
        "INSERT INTO user (fullname, email, password_hash, verified, active) VALUES (?, ?, ?, ?, ?)",
        ("Test User", "test@example.com", generate_password_hash("password123"), 1, 1)
    )
    conn.execute(
        "INSERT INTO user (fullname, email, password_hash, verified, active) VALUES (?, ?, ?, ?, ?)",
        ("Inactive User", "inactive@example.com", generate_password_hash("password123"), 1, 0)
    )

    conn.execute(
        "INSERT INTO donations (user_id, campaign_name, amount, transaction_id, donation_date) VALUES (?, ?, ?, ?, ?)",
        (1, "Scholarship Fund", 500.00, "test_txn_001", datetime.now().isoformat())
    )
    conn.execute(
        "INSERT INTO donations (user_id, campaign_name, amount, transaction_id, donation_date) VALUES (?, ?, ?, ?, ?)",
        (1, "Campus Renovation", 1000.00, "test_txn_002", datetime.now().isoformat())
    )

conn.commit()


# ===================== App Start =====================
if not DB_PATH.exists():
    init_db()
    print(f"Database initialized at {DB_PATH}")
else:
    # Ensure new tables (like password_reset_token) exist even if DB file already exists
    init_db()


@app.route('/')
def home():

    return render_template('login.html')
def is_strong_password(password):
    """Check if the password meets strength requirements."""
    return bool(re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        fullname = data.get("fullname")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")
        graduation_year = data.get("graduation_year")

        with get_db() as conn:
            existing_user = conn.execute("SELECT verified FROM user WHERE email = ?", (email,)).fetchone()
            if existing_user:
                return jsonify(success=False, message="Email already registered, please log in.")

            if not is_strong_password(password):
                return jsonify(success=False, message="Password must include uppercase, lowercase, numbers, and special characters.")

            conn.execute(
                """INSERT INTO user (fullname, email, password_hash, role, graduation_year, verified, active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (fullname, email, generate_password_hash(password), role, graduation_year, 1, 1, datetime.now())  # ✅ No email verification
            )
            conn.commit()

            return jsonify(success=True, redirect=url_for('login', _external=True))

    return render_template('signup.html')


@app.route('/verify-email')
def verify_email():
    """Mock email verification"""
    email = request.args.get('email')
    with get_db() as conn:
        conn.execute("UPDATE user SET verified = 1 WHERE email = ?", (email,))
        conn.commit()
    return jsonify(success=True, message="Email verified successfully. You can now log in.")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    with get_db() as conn:
        # Get user with all needed columns
        user = conn.execute(
            "SELECT id, email, password_hash, active, failed_attempts, last_failed_attempt FROM user WHERE email = ?", 
            (email,)
        ).fetchone()

        if not user:
            return jsonify(success=False, message="Incorrect username or password")

        if not user['active']:
            return jsonify(success=False, message="Your account is suspended. Please contact support.")

        # FIRST check password - correct credentials should always work
        if check_password_hash(user['password_hash'], password):
            # Reset failed attempts on successful login
            conn.execute(
                "UPDATE user SET failed_attempts = 0, last_failed_attempt = NULL WHERE id = ?",
                (user['id'],)
            )
            conn.commit()
            session["user"] = user['email']
            return jsonify(success=True, redirect=url_for('dashboard'))

        # Only process failed attempts if password was wrong
        current_time = datetime.now()
        timeout_minutes = 5  # Changed to 5 minutes as requested
        
        # Check if attempts should be reset due to timeout
        if user['last_failed_attempt']:
            last_attempt = datetime.fromisoformat(user['last_failed_attempt'])
            time_since_last_attempt = current_time - last_attempt
            
            if time_since_last_attempt > timedelta(minutes=timeout_minutes):
                # Reset counter if timeout passed
                conn.execute(
                    "UPDATE user SET failed_attempts = 0, last_failed_attempt = NULL WHERE id = ?",
                    (user['id'],)
                )
                conn.commit()
                failed_attempts = 0
            else:
                failed_attempts = user['failed_attempts']
        else:
            failed_attempts = user['failed_attempts']

        # Check if attempts exceeded (only for failed logins)
        if failed_attempts >= 3:
            remaining_time = timedelta(minutes=timeout_minutes) - (current_time - datetime.fromisoformat(user['last_failed_attempt']))
            remaining_minutes = int(remaining_time.total_seconds() / 60)
            return jsonify(
                success=False, 
                message=f"Too many attempts! Please try again in {remaining_minutes} minutes"
            )

        # Update failed attempts counter
        new_attempts = failed_attempts + 1
        conn.execute(
            "UPDATE user SET failed_attempts = ?, last_failed_attempt = ? WHERE id = ?",
            (new_attempts, current_time.isoformat(), user['id'])
        )
        conn.commit()
        
        return jsonify(success=False, message="Incorrect username or password")


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get("email")

        if not email:
            return "Email is required", 400

        with get_db() as conn:
            user = conn.execute("SELECT * FROM user WHERE email = ?", (email,)).fetchone()

            if not user:
                return redirect(url_for('forgot_password'))  # Silent fail

            # ✅ Generate secure token
            token = secrets.token_urlsafe(32)
            expires_at = (datetime.now() + timedelta(hours=1)).isoformat()

            # ✅ Store token in DB
            conn.execute("""
                INSERT INTO password_reset_token (user_id, token, expires_at)
                VALUES (?, ?, ?)
            """, (user['id'], token, expires_at))
            conn.commit()

            # ✅ Compose reset link
            reset_link = f"{BASE_URL}/reset_password?token={token}"

            # ✅ Send email
            send_reset_email(user['email'], reset_link)

            print(f"[INFO] Sent password reset link: {reset_link}")  # For debug

            return render_template('forgot_password.html', sent=True)

    return render_template('forgot_password.html')

def send_reset_email(to_email, reset_link):
    subject = "Alumnexus Password Reset"
    body = f"Click the link below to reset your password:\n\n{reset_link}\n\nIf you did not request this, ignore this email."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print("[INFO] Reset email sent successfully.")
    except Exception as e:
        print("[ERROR] Failed to send email:", e)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get("token")

    if request.method == 'GET':
        if not token:
            return "Invalid or expired link", 400

        with get_db() as conn:
            token_data = conn.execute("""
                SELECT * FROM password_reset_token
                WHERE token = ? AND used = 0 AND expires_at > ?
            """, (token, datetime.now().isoformat())).fetchone()

            if not token_data:
                return "Invalid or expired token", 400

        return render_template('reset_password.html', token=token)

    elif request.method == 'POST':
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        token = request.form.get("token")

        if new_password != confirm_password:
            return jsonify(success=False, message="Passwords do not match")

        if not is_strong_password(new_password):
            return jsonify(success=False, message="Password too weak")

        with get_db() as conn:
            token_data = conn.execute("""
                SELECT * FROM password_reset_token
                WHERE token = ? AND used = 0 AND expires_at > ?
            """, (token, datetime.now().isoformat())).fetchone()

            if not token_data:
                return jsonify(success=False, message="Invalid or expired token")

            # ✅ Update user password
            hashed_pw = generate_password_hash(new_password)
            conn.execute("UPDATE user SET password_hash = ? WHERE id = ?", (hashed_pw, token_data['user_id']))

            # ✅ Mark token as used
            conn.execute("UPDATE password_reset_token SET used = 1 WHERE id = ?", (token_data['id'],))
            conn.commit()

        return jsonify(success=True, redirect=url_for('login'))


@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db()

        # Get current user ID
        current_user = conn.execute(
            "SELECT id FROM user WHERE email = ?", 
            (session['user'],)
        ).fetchone()

        if not current_user:
            return redirect(url_for('login'))

        user_id = current_user['id']
        print(f"Current user ID: {user_id}")

        # Get suggested alumni connections (full details, excluding already connected users)
        suggested_connections = conn.execute("""
            SELECT u.* FROM user u
            LEFT JOIN user_block b ON (b.blocker_id = ? AND b.blocked_id = u.id)
            WHERE u.id != ?
                AND u.verified = 1
                AND u.active = 1
                AND u.role = 'Alumni'
                AND (u.privacy = 'public' OR u.privacy IS NULL)  -- Only public profiles
                AND b.id IS NULL
                AND u.id NOT IN (
                    SELECT CASE
                        WHEN c.sender_id = ? THEN c.receiver_id
                        WHEN c.receiver_id = ? THEN c.sender_id
                    END
                    FROM connection c
                    WHERE (c.sender_id = ? OR c.receiver_id = ?)
                      AND c.status = 'accepted'
                )
            ORDER BY RANDOM()
            LIMIT 3
        """, (user_id, user_id, user_id, user_id, user_id, user_id)).fetchall()

        print("Suggested alumni:", suggested_connections)

        # Get recent activities
        recent_activities = conn.execute(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
            (user_id,)
        ).fetchall()

        return render_template('dashboard.html',
                               recent_activities=recent_activities,
                               suggested_connections=suggested_connections)

    except Exception as e:
        print("Error in dashboard route:", str(e))
        return render_template('dashboard.html',
                               recent_activities=[],
                               suggested_connections=[])
    
def check_and_send_event_reminders():
    with get_db() as conn:
        now = datetime.now()
        
        # Get events happening in 1 or 2 days
        events = conn.execute("""
            SELECT e.id, e.title, e.start_time, 
                   GROUP_CONCAT(r.user_id) AS rsvp_users
            FROM event e
            JOIN rsvp r ON e.id = r.event_id
            WHERE date(e.start_time) BETWEEN date(?, '+1 day') AND date(?, '+2 day')
            GROUP BY e.id
        """, (now.isoformat(), now.isoformat())).fetchall()
        
        for event in events:
            event_date = datetime.fromisoformat(event['start_time'])
            days_diff = (event_date.date() - now.date()).days
            
            if days_diff not in [1, 2]:
                continue
                
            reminder_type = f"{days_diff}day"
            message = f"Event {event['title']} starts {'tomorrow' if days_diff == 1 else 'day after tomorrow'}"
            
            # Get all users who RSVP'd and haven't received this reminder yet
            users = conn.execute("""
                SELECT r.user_id 
                FROM rsvp r
                LEFT JOIN event_reminders er ON 
                    er.user_id = r.user_id AND 
                    er.event_id = ? AND 
                    er.reminder_type = ?
                WHERE r.event_id = ? AND er.id IS NULL
            """, (event['id'], reminder_type, event['id'])).fetchall()
            
            for user in users:
                # Create notification
                conn.execute("""
                    INSERT INTO notifications (user_id, message, created_at)
                    VALUES (?, ?, ?)
                """, (user['user_id'], message, now.isoformat()))
                
                # Mark reminder as sent
                conn.execute("""
                    INSERT INTO event_reminders (user_id, event_id, reminder_type)
                    VALUES (?, ?, ?)
                """, (user['user_id'], event['id'], reminder_type))
        
        conn.commit()


@app.route('/api/notifications')
def get_notifications():
    if "user" not in session:
        return jsonify([])
    
    with get_db() as conn:
        user = conn.execute(
            "SELECT id FROM user WHERE email = ?", 
            (session['user'],)
        ).fetchone()
        
        if not user:
            return jsonify([])
            
        # Check for new reminders before fetching
        check_and_send_event_reminders()
        
        # Modified to fetch both read and unread notifications
        notifications = conn.execute("""
            SELECT * FROM notifications 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (user['id'],)).fetchall()
        
        return jsonify([dict(n) for n in notifications])


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if "user" not in session:
        return redirect(url_for('login'))

    session_email = session["user"]

    if request.method == 'GET':
        with get_db() as conn:
            user = conn.execute("SELECT * FROM user WHERE email = ?", (session_email,)).fetchone()
            if not user:
                return redirect(url_for('login'))

            user = dict(user)
            if user["avatar"]:
                user["avatar"] = base64.b64encode(user["avatar"]).decode("utf-8")
            
            # Get role from user data
            role = user['role']
            
            resume_url = None
            if user["resume"]:
                resume_url = "/download_resume/{}".format(user['id'])

            skills = conn.execute("SELECT name, percentage FROM skill WHERE user_id = ?", (user['id'],)).fetchall()

            # Get sessions based on role - modified to use new table structure
            if role.lower() == 'student':
                sessions = conn.execute("""
                    SELECT ms.session_id, ms.session_time as session_start_time, 
                        ms.session_description, ms.mentor_name,
                        ms.mentor_image
                    FROM mentor_session ms
                    JOIN session_member sm ON ms.session_id = sm.session_id
                    WHERE sm.student_id = ?
                """, (user['id'],)).fetchall()
            else:  # Alumni
                sessions = conn.execute("""
                    SELECT session_id, session_time as session_start_time, 
                           session_description, mentor_name, mentor_field,
                           mentor_image
                    FROM mentor_session
                    WHERE alumni_id = ?
                """, (user['id'],)).fetchall()

            # Get accepted connections
            connections = conn.execute("""
                SELECT u.id, u.fullname, u.graduation_year
                FROM connection c
                JOIN user u ON (c.sender_id = u.id OR c.receiver_id = u.id) AND u.id != ?
                WHERE (c.sender_id = ? OR c.receiver_id = ?) 
                    AND c.status = 'accepted'
                    AND u.privacy != 'private'
            """, (user['id'], user['id'], user['id'])).fetchall()

            return render_template('profile.html', 
                user=user, 
                skills=skills, 
                resume_url=resume_url,
                role=role,
                sessions=sessions,
                connections=connections
            )
    
    # POST request handling remains exactly the same
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    department = request.form.get("department", "").strip()
    new_email = request.form.get("email", "").strip()
    privacy = request.form.get("privacy", "public").strip()
    resume = request.files.get("resume")
    avatar = request.files.get("avatar")

    # Validate required fields
    required_fields = {
        "First Name": first_name,
        "Last Name": last_name,
        "Department": department,
        "Email": new_email
    }
    
    missing_fields = [field for field, value in required_fields.items() if not value]
    if missing_fields:
        return jsonify(
            success=False,
            message=f"Please fill all required fields: {', '.join(missing_fields)}"
        )

    try:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM user WHERE email = ?", (session_email,)).fetchone()
            if not row:
                return jsonify(success=False, message="User not found.")
            current_user = dict(row)

            user_id = current_user['id']

            # Check for duplicate email (excluding current user)
            if new_email != session_email:
                existing = conn.execute("SELECT * FROM user WHERE email = ? AND id != ?", (new_email, user_id)).fetchone()
                if existing:
                    return jsonify(success=False, message="This email is already registered with another account.")
                
            # Validate profile picture: Check if avatar is provided or already exists in the current user
            if not avatar and not current_user['avatar']:
                return jsonify(success=False, message="Please upload a profile picture.")

            # If avatar is uploaded, use it, otherwise retain the current user's avatar
            resume_data = resume.read() if resume else current_user.get('resume')
            avatar_data = avatar.read() if avatar else current_user['avatar']

            privacy = request.form.get("privacy", "public").strip()

            # Update user data
            conn.execute('''
                UPDATE user SET
                    first_name = ?,
                    last_name = ?,
                    department = ?,
                    email = ?,
                    resume = ?,
                    avatar = ?,
                    privacy = ?
                WHERE id = ?
            ''', (
                first_name,
                last_name,
                department,
                new_email,
                resume_data,
                avatar_data if avatar_data else current_user.get('avatar'),  # Keep existing if no new upload
                privacy,
                user_id
            ))

            conn.commit()

            # 👉 Save updated skills
            skills_data = request.form.get("skills", "[]")
            skills = json.loads(skills_data)

            conn.execute("DELETE FROM skill WHERE user_id = ?", (user_id,))
            for skill in skills:
                name = skill.get("name")
                percentage = int(skill.get("percentage", 0))
                conn.execute("INSERT INTO skill (user_id, name, percentage) VALUES (?, ?, ?)", (user_id, name, percentage))

            conn.commit()

        # Update session if email changed
        session["user"] = new_email

        return jsonify(success=True, message="Profile updated successfully.")

    except IntegrityError:
        return jsonify(success=False, message="A user with this email already exists.")
    except Exception as e:
        return jsonify(success=False, message=f"An error occurred: {str(e)}")
    
@app.route('/create_mentor_session', methods=['POST'])
def create_mentor_session():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        session_email = session["user"]
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
            
        session_time = data.get('session_time') or data.get('session_date')
        if not session_time:
            return jsonify({
                'success': False,
                'message': 'Missing required field: session_time/session_date'
            }), 400

        required_fields = {
            'session_description': data.get('session_description'),
            'mentor_field': data.get('mentor_field', 'General')
        }
        
        missing = [field for field, value in required_fields.items() if not value]
        if missing:
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing)}'
            }), 400

        with get_db() as conn:
            user = conn.execute(
                "SELECT id, role, fullname FROM user WHERE email = ?", 
                (session_email,)
            ).fetchone()
            
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404

            if user['role'].lower() != 'alumni':
                return jsonify({
                    'success': False,
                    'message': 'Only alumni can create sessions'
                }), 403
            
            # Always use the alumni's actual name from the database
            conn.execute(
                """INSERT INTO mentor_session (
                    alumni_id, 
                    session_time, 
                    session_description,
                    mentor_name,
                    mentor_field,
                    session_start_time
                ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    user['id'], 
                    session_time, 
                    required_fields['session_description'],
                    user['fullname'],  # Always use real name from database
                    required_fields['mentor_field'],
                    session_time
                )
            )
            
            conn.commit()
            return jsonify({
                'success': True,
                'message': 'Session created successfully',
                'session_id': conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            })

    except sqlite3.IntegrityError as e:
        return jsonify({
            'success': False,
            'message': 'Session already exists or database error'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }), 500
        
@app.route('/alunet')  
def alunet():
    if "user" in session:
        return render_template('alunet.html')

@app.route('/alunetmssg')
def alunetmssg():
    if "user" not in session:
        return redirect(url_for('login'))
    
    alumni_name = request.args.get("name", "Unknown")
    return render_template('alunetmssg.html', alumni_name=alumni_name)

@app.route('/get_alumni')
def get_alumni():
    if "user" not in session:
        return jsonify([])
    
    search_query = request.args.get('search', '')
    
    with get_db() as conn:
        # Get current user's ID
        current_user = conn.execute("SELECT id FROM user WHERE email = ?", (session["user"],)).fetchone()
        if not current_user:
            return jsonify([])
        
        # Base query
        query = """
            SELECT u.id, u.fullname, u.graduation_year, p.current_job, p.company 
            FROM user u
            LEFT JOIN profile p ON u.id = p.user_id
            WHERE u.email != ? 
            AND u.role = 'Alumni'
            AND (u.privacy = 'public' OR u.privacy IS NULL)
        """
        params = [session["user"]]
        
        # Add search conditions if query exists
        if search_query:
            query += """
                AND (u.fullname LIKE ? OR 
                     p.current_job LIKE ? OR 
                     p.company LIKE ?)
            """
            search_param = f"%{search_query}%"
            params.extend([search_param, search_param, search_param])
        
        alumni = conn.execute(query, params).fetchall()
        
        return jsonify([dict(row) for row in alumni])
    
@app.route('/api/current_user')
def get_current_user():
    if "user" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    with get_db() as conn:
        user = conn.execute("SELECT id, fullname FROM user WHERE email = ?", (session["user"],)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(dict(user))


@app.route('/api/get_user_by_name')
def get_user_by_name():
    name = request.args.get('name')
    if not name:
        return jsonify({'error': 'Name parameter required'}), 400
    
    with get_db() as conn:
        user = conn.execute("SELECT id, fullname FROM user WHERE fullname = ?", (name,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(dict(user))


@app.route('/send_connection_request', methods=['POST'])
def send_connection_request():
    if "user" not in session:
        return jsonify(success=False, message="Not logged in")
    
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    receiver_name = data.get('receiver_name')
    
    with get_db() as conn:
        # Get sender info
        sender = conn.execute("SELECT id, fullname FROM user WHERE email = ?", (session["user"],)).fetchone()
        if not sender:
            return jsonify(success=False, message="User not found")
        
        # Check if connection already exists
        existing = conn.execute(
            "SELECT 1 FROM connection WHERE sender_id = ? AND receiver_id = ?",
            (sender['id'], receiver_id)
        ).fetchone()
        
        if existing:
            return jsonify(success=False, message="Connection request already sent")
        
        # Create new connection request
        conn.execute(
            "INSERT INTO connection (sender_id, receiver_id, status) VALUES (?, ?, ?)",
            (sender['id'], receiver_id, 'pending')
        )
        
        # Create notification for the receiver
        message = f"{sender['fullname']} sent you a connection request"
        conn.execute(
            "INSERT INTO notification (user_id, message, related_entity, related_entity_id) VALUES (?, ?, ?, ?)",
            (receiver_id, message, 'connection', sender['id'])
        )
        
        conn.commit()
        
    return jsonify(success=True)

@app.route('/get_connection_requests')
def get_connection_requests():
    if "user" not in session:
        return jsonify([])
    
    with get_db() as conn:
        # Get current user's ID
        current_user = conn.execute("SELECT id FROM user WHERE email = ?", (session["user"],)).fetchone()
        if not current_user:
            return jsonify([])
        
        # Get pending connection requests
        requests = conn.execute("""
            SELECT u.id, u.fullname, c.created_at 
            FROM connection c
            JOIN user u ON c.sender_id = u.id
            WHERE c.receiver_id = ? AND c.status = 'pending'
        """, (current_user['id'],)).fetchall()
        
        return jsonify([dict(row) for row in requests])

@app.route('/handle_connection_request', methods=['POST'])
def handle_connection_request():
    if "user" not in session:
        return jsonify(success=False, message="Not logged in")
    
    data = request.get_json()
    sender_id = data.get('sender_id')
    action = data.get('action')
    
    with get_db() as conn:
        # Get current user's ID
        receiver = conn.execute("SELECT id, fullname FROM user WHERE email = ?", (session["user"],)).fetchone()
        if not receiver:
            return jsonify(success=False, message="User not found")
        
        # Update connection status
        new_status = 'accepted' if action == 'accept' else 'rejected'
        conn.execute(
            "UPDATE connection SET status = ? WHERE sender_id = ? AND receiver_id = ?",
            (new_status, sender_id, receiver['id'])
        )
        
        # Create notification for the sender
        message = f"{receiver['fullname']} {new_status} your connection request"
        conn.execute(
            "INSERT INTO notification (user_id, message, related_entity, related_entity_id) VALUES (?, ?, ?, ?)",
            (sender_id, message, 'connection', receiver['id'])
        )
        
        conn.commit()
        
    return jsonify(success=True)

    
@app.route('/events')
def events():
    return render_template('emr.html')


@app.route('/eventdetails')
def event_details():
    # Check if this is a database event
    if request.args.get('type') == 'db':
        event_id = request.args.get('id', '').replace('db-event-', '')
        already_rsvped = False
        
        if 'user_id' in session:
            with get_db() as conn:
                rsvp = conn.execute(
                    "SELECT 1 FROM rsvp WHERE user_id = ? AND event_id = ?",
                    (session['user_id'], event_id)
                ).fetchone()
                already_rsvped = bool(rsvp)
        
        return render_template('eventdetails.html', 
            event={
                "title": request.args.get('title'),
                "date": request.args.get('date'),
                "location": request.args.get('location'),
                "description": request.args.get('description'),
                "image": "eventicon.png"
            },
            event_id=event_id,
            already_rsvped=already_rsvped
        )
    
@app.route('/api/events/reminders')
def get_event_reminders():
    if 'user' not in session:
        return jsonify([])
    
    with get_db() as conn:
        try:
            user = conn.execute(
                "SELECT id FROM user WHERE email = ?",
                (session['user'],)
            ).fetchone()
            
            if not user:
                return jsonify([])
            
            now = datetime.now()
            one_day_later = now + timedelta(days=1)
            
            # Get events happening in exactly 1 day (±1 hour window)
            events = conn.execute("""
                SELECT e.id, e.title, e.start_time, e.location 
                FROM event e
                JOIN rsvp r ON e.id = r.event_id
                WHERE r.user_id = ? 
                AND datetime(e.start_time) BETWEEN datetime(?) AND datetime(?)
                ORDER BY e.start_time ASC
            """, (user['id'], 
                 (now + timedelta(hours=23)).isoformat(), 
                 (now + timedelta(hours=25)).isoformat())).fetchall()
            
            reminders = []
            
            for event in events:
                event_time = datetime.fromisoformat(event['start_time'])
                time_diff = event_time - now
                hours_left = int(time_diff.total_seconds() / 3600)
                
                reminders.append({
                    'id': event['id'],
                    'title': event['title'],
                    'days_left': 1,  # Since we're specifically checking for 1-day reminders
                    'hours_left': hours_left,
                    'date': event_time.strftime('%Y-%m-%d'),
                    'time': event_time.strftime('%H:%M'),
                    'location': event['location']
                })
            
            return jsonify(reminders)
            
        except Exception as e:
            print(f"Error in get_event_reminders: {str(e)}")
            return jsonify([])

@app.route('/api/rsvp', methods=['POST'])
def handle_rsvp():
    # Debug: Print current session
    print(f"Current Session: {dict(session)}")  
    
    # 1. Check for logged-in user (using 'user' key as your system does)
    if 'user' not in session:
        return jsonify({
            'error': 'Please login first',
            'redirect': url_for('login')
        }), 401

    # 2. Get user_id from database using the email in session
    with get_db() as conn:
        try:
            # 2a. Find user by email (session['user'])
            user = conn.execute(
                "SELECT id FROM user WHERE email = ?",
                (session['user'],)
            ).fetchone()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            user_id = user['id']
            data = request.get_json()
            
            # 2b. Validate event data
            if not data or 'event_id' not in data:
                return jsonify({'error': 'Missing event data'}), 400

            event_id = data['event_id']
            
            # 3. Check for existing RSVP
            existing = conn.execute(
                "SELECT 1 FROM rsvp WHERE user_id = ? AND event_id = ?",
                (user_id, event_id)
            ).fetchone()
            
            if existing:
                return jsonify({
                    'message': 'You already RSVP\'d for this event',
                    'status': 'duplicate'
                })
            
            # 4. Create new RSVP
            conn.execute(
                "INSERT INTO rsvp (user_id, event_id) VALUES (?, ?)",
                (user_id, event_id)
            )
            conn.commit()
            
            return jsonify({
                'message': 'RSVP successful!',
                'status': 'new'
            })
            
        except sqlite3.IntegrityError as e:
            print(f"Database Error: {str(e)}")
            return jsonify({'error': 'Failed to process RSVP'}), 500

@app.route('/check_login')
def check_login():
    return jsonify({
        'is_logged_in': 'user_id' in session,
        'user_id': session.get('user_id')
    })
        
@app.route('/api/events/cancelled')
def get_cancelled_events():
    if 'user' not in session:
        return jsonify([])
    
    with get_db() as conn:
        # Get user ID
        user = conn.execute(
            "SELECT id FROM user WHERE email = ?",
            (session['user'],)
        ).fetchone()
        
        if not user:
            return jsonify([])
            
        # Get cancelled events this user RSVP'd to
        cancelled_events = conn.execute("""
            SELECT e.title FROM event e
            JOIN cancelled_events ce ON e.id = ce.event_id
            JOIN rsvp r ON e.id = r.event_id
            WHERE r.user_id = ?
        """, (user['id'],)).fetchall()
        
        return jsonify([dict(e) for e in cancelled_events])

@app.route('/api/events/cancelled-for-user')
def get_cancelled_events_for_user():
    if 'user' not in session:
        return jsonify([])
    
    with get_db() as conn:
        try:
            # Get user ID from session email
            user = conn.execute(
                "SELECT id FROM user WHERE email = ?",
                (session['user'],)
            ).fetchone()
            
            if not user:
                return jsonify([])
            
            # Get cancelled events this user RSVP'd to
            cancelled_events = conn.execute("""
                SELECT e.id, e.title, e.start_time, e.location 
                FROM event e
                JOIN cancelled_events ce ON e.id = ce.event_id
                JOIN rsvp r ON e.id = r.event_id
                WHERE r.user_id = ?
                ORDER BY ce.cancelled_at DESC
            """, (user['id'],)).fetchall()
            
            return jsonify([dict(e) for e in cancelled_events])
            
        except Exception as e:
            print(f"Error in cancelled-for-user: {str(e)}")
            return jsonify([])
    
@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        with get_db() as conn:
            # Get event details
            event = conn.execute("SELECT * FROM event WHERE id = ?", (event_id,)).fetchone()
            if not event:
                return jsonify({'error': 'Event not found'}), 404
            
            print(f"DEBUG: Cancelling event: {event['title']} (ID: {event_id})")  # Debug log
            
            # Get RSVP'd users
            rsvp_users = conn.execute("SELECT user_id FROM rsvp WHERE event_id = ?", (event_id,)).fetchall()
            print(f"DEBUG: Found {len(rsvp_users)} RSVP'd users")  # Debug log
            
            # Create notifications
            for user in rsvp_users:
                user_id = user['user_id']
                message = f"Event '{event['title']}' has been cancelled."
                print(f"DEBUG: Creating notification for user {user_id}: {message}")  # Debug log
                conn.execute("""
                    INSERT INTO notifications (user_id, message)
                    VALUES (?, ?)
                """, (user_id, message))
            
            # Delete the event and RSVPs
            conn.execute("DELETE FROM event WHERE id = ?", (event_id,))
            conn.execute("DELETE FROM rsvp WHERE event_id = ?", (event_id,))
            conn.commit()
            
            print("DEBUG: Event cancellation completed successfully")  # Debug log
            return jsonify({'success': True}), 200
            
    except Exception as e:
        print(f"ERROR in event cancellation: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500
        
@app.route('/test-cancelled')
def test_cancelled():
    with get_db() as conn:
        # Check if event 10 is in cancelled_events
        cancelled = conn.execute("SELECT * FROM cancelled_events WHERE event_id = 10").fetchone()
        # Check if any users RSVP'd to event 10
        rsvps = conn.execute("SELECT * FROM rsvp WHERE event_id = 10").fetchall()
        
        return jsonify({
            "event_10_cancelled": bool(cancelled),
            "rsvps_for_event_10": [dict(r) for r in rsvps],
            "cancelled_events_for_user": conn.execute("""
                SELECT e.id, e.title FROM event e
                JOIN cancelled_events ce ON e.id = ce.event_id
                JOIN rsvp r ON e.id = r.event_id
                WHERE r.user_id = (SELECT id FROM user WHERE email = ?)
            """, (session.get('user'),)).fetchall()
        })
    
@app.route('/debug-cancelled')
def debug_cancelled():
    with get_db() as conn:
        return jsonify({
            # Check if event 15 is marked as cancelled
            "cancelled_events": conn.execute(
                "SELECT * FROM cancelled_events WHERE event_id = 15"
            ).fetchall(),
            
            # Check if harsitha@gmail.com RSVP'd to event 15
            "rsvps": conn.execute("""
                SELECT r.* FROM rsvp r
                JOIN user u ON r.user_id = u.id
                WHERE r.event_id = 15 AND u.email = 'harsitha@gmail.com'
            """).fetchall(),
            
            # Check notifications created for this user
            "notifications": conn.execute("""
                SELECT n.* FROM notifications n
                JOIN user u ON n.user_id = u.id
                WHERE u.email = 'harsitha@gmail.com'
            """).fetchall()
        })
    
@app.route('/debug-rsvp')
def debug_rsvp():
    with get_db() as conn:
        return jsonify({
            "current_user": session.get('user'),
            "rsvps": conn.execute("""
                SELECT e.id, e.title, r.created_at 
                FROM rsvp r
                JOIN event e ON r.event_id = e.id
                JOIN user u ON r.user_id = u.id
                WHERE u.email = ?
            """, (session.get('user'),)).fetchall(),
            "cancelled_events": conn.execute("""
                SELECT e.id, e.title, ce.cancelled_at 
                FROM cancelled_events ce
                JOIN event e ON ce.event_id = e.id
            """).fetchall()
        })

@app.route('/job')
def job():
    if "user" not in session:
        return redirect(url_for('login'))

    with get_db() as conn:
        conn.execute("UPDATE job SET active=0 WHERE expires_at <= ?", (datetime.now().isoformat(),))
        conn.commit()
        job_list = conn.execute("SELECT * FROM job WHERE active=1 ORDER BY posted_at DESC").fetchall()

    if not job_list:
        print("No jobs found.")  # Debugging: Check if jobs are found

    return render_template('job.html', jobs=job_list)


@app.route('/api/job')
def api_job():
    with get_db() as conn:
        jobs = conn.execute("SELECT id, title, company, description FROM job WHERE active=1 ORDER BY posted_at DESC").fetchall()
    return jsonify([dict(job) for job in jobs])



@app.route('/job_post', methods=['GET', 'POST'])
def job_post():
    if "user" not in session:
        return redirect(url_for('login'))

    with get_db() as conn:
        user = conn.execute("SELECT id, role, password_hash FROM user WHERE email = ?", (session["user"],)).fetchone()
        if not user:
            return redirect(url_for('home'))

        # 🚫 Restrict access to only recruiters (changed from admin)
        if user['role'].lower() != 'recruiter':
            return jsonify({"success": False, "message": "Access denied: You must be a recruiter to post jobs."}), 403

        if request.method == 'POST':
            try:
                data = request.get_json()

                job_title = data.get("title")
                job_company = data.get("company")
                job_description = data.get("description")
                job_location = data.get("location")
                job_experience = data.get("experience")
                job_skills = data.get("skills")
                job_type = data.get("job_type")  # 🛠 Match key from frontend (was `type`)

                # ✅ Validate
                if not job_title or not job_company or not job_description:
                    return jsonify({"success": False, "message": "All required fields must be filled."}), 400

                # ✅ Insert into DB
                conn.execute(
                    """INSERT INTO job 
                    (employer_id, title, company, description, location, experience, skills, job_type, expires_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user['id'], job_title, job_company, job_description,
                        job_location, job_experience, job_skills, job_type,
                        (datetime.now() + timedelta(days=30)).isoformat()
                    )
                )
                conn.commit()

                return jsonify({"success": True, "message": "Job posted successfully!"})
            except Exception as e:
                print("Error posting job:", e)
                return jsonify({"success": False, "message": "Server error occurred while posting the job."}), 500

        # If GET request, render the form page
        return render_template('job_post.html')
    
@app.route('/debug/jobs')
def debug_jobs():
    with get_db() as conn:
        jobs = conn.execute("""
            SELECT id, title, expires_at, active, 
                   datetime(expires_at) as expires_datetime,
                   datetime('now') as current_datetime,
                   datetime(expires_at) <= datetime('now') as should_be_expired
            FROM job
            ORDER BY expires_at DESC
        """).fetchall()
        
        return jsonify([dict(job) for job in jobs])

@app.route('/debug/force_expire')
def debug_force_expire():
    with get_db() as conn:
        # Force expire all jobs that should be expired
        result = conn.execute("""
            UPDATE job SET active=0 
            WHERE datetime(expires_at) <= datetime('now') AND active=1
        """)
        conn.commit()
        return jsonify({"message": f"Expired {result.rowcount} jobs"})
    
@app.route('/job_apply', methods=['GET', 'POST'])
def submit_application():
    if "user" not in session:
        return jsonify({"success": False, "error": "Please login to apply"}), 401

    if request.method == 'GET':
        with get_db() as conn:
            jobs = conn.execute("SELECT * FROM job WHERE active=1 ORDER BY posted_at DESC").fetchall()
        return render_template('job_apply.html', jobs=jobs)

    if request.method == 'POST':
        try:
            job_id = request.form.get("job_id")
            applicant_name = request.form.get("applicant_name")
            applicant_email = request.form.get("applicant_email")
            applicant_phone = request.form.get("applicant_phone")
            applicant_address = request.form.get("applicant_address")
            resume = request.files.get("resume")

            if not all([job_id, applicant_name, applicant_email, resume, applicant_phone, applicant_address]):
                return jsonify({
                    "success": False,
                    "error": "All fields are required!"
                }), 400
            
            resume_dir = os.path.join(os.getcwd(), 'static', 'resume')
            os.makedirs(resume_dir, exist_ok=True)

            resume_filename = secure_filename(resume.filename)
            resume_path = os.path.join(resume_dir, resume_filename)
            resume.save(resume_path)
            resume_url = f"/static/resume/{resume_filename}"

            with get_db() as conn:
                # Check for existing application
                existing = conn.execute(
                    """SELECT * FROM job_application 
                    WHERE job_id = ? AND applicant_email = ?""",
                    (job_id, applicant_email)
                ).fetchone()

                if existing:
                    return jsonify({
                        "success": False,
                        "error": "You have already applied for this job."
                    }), 409

                # Insert new application
                conn.execute(
                    """INSERT INTO job_application 
                    (job_id, applicant_name, applicant_email, applicant_phone, applicant_address, resume) 
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (job_id, applicant_name, applicant_email, applicant_phone, applicant_address, resume_url)
                )
                conn.commit()

            return jsonify({
                "success": True,
                "message": "Job application submitted successfully!"
            }), 200

        except Exception as e:
            print(f"Error submitting application: {e}")
            return jsonify({
                "success": False,
                "error": "An error occurred while submitting your application."
            }), 500
        
@app.route('/api/job/<int:job_id>/apply', methods=['POST'])
def applyForJob(job_id):
    try:
        # Check if user is logged in
        if "user" not in session:
            return jsonify({
                "success": False,
                "error": "Please login to apply"
            }), 401

        # Check required fields
        if 'resume' not in request.files:
            return jsonify({
                "success": False,
                "error": "Resume file is required"
            }), 400

        # Get form data
        name = request.form.get("applicant_name")
        email = request.form.get("applicant_email")
        phone = request.form.get("applicant_phone")
        address = request.form.get("applicant_address")
        resume = request.files.get("resume")

        if not all([name, email, phone, address]):
            return jsonify({
                "success": False,
                "error": "All fields are required"
            }), 400

        # Process resume
        resume_dir = os.path.join(os.getcwd(), 'static', 'resume')
        os.makedirs(resume_dir, exist_ok=True)
        resume_filename = secure_filename(resume.filename)
        resume_url = f"static/resume/{resume_filename}"
        resume.save(resume_url)

        # Database operations
        with get_db() as conn:
            # Verify job exists
            if not conn.execute("SELECT 1 FROM job WHERE id = ?", (job_id,)).fetchone():
                return jsonify({
                    "success": False,
                    "error": "Job not found."
                }), 404

            # Check for duplicate application
            if conn.execute(
                """SELECT 1 FROM job_application 
                WHERE job_id = ? AND applicant_email = ?""",
                (job_id, email)
            ).fetchone():
                return jsonify({
                    "success": False,
                    "error": "You have already applied for this job."
                }), 409

            # Insert application
            conn.execute(
                """INSERT INTO job_application 
                (job_id, applicant_name, applicant_email, applicant_phone, applicant_address, resume) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (job_id, name, email, phone, address, resume_url)
            )
            conn.commit()

        return jsonify({
            "success": True,
            "message": "Application submitted successfully!"
        }), 200

    except Exception as e:
        print(f"Error submitting application: {e}")
        return jsonify({
            "success": False,
            "error": "An error occurred while submitting your application."
        }), 500
    
@app.route('/job_details/<int:job_id>')
def job_details(job_id):
    with get_db() as conn:
        job = conn.execute("SELECT * FROM job WHERE id = ?", (job_id,)).fetchone()
        if not job:
            return "Job not found", 404
    return render_template('job-details.html', job=job)

@app.route('/api/check_role')
def check_role():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    with get_db() as conn:
        user = conn.execute("SELECT role FROM user WHERE email = ?", (session["user"],)).fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
            
    return jsonify({"role": user['role'].lower()})

@app.route('/search')
def search():
    query = request.args.get("q", "").lower()
    experience = request.args.get("exp", "").lower()
    location = request.args.get("loc", "").lower()

    with get_db() as conn:
        jobs = conn.execute("SELECT * FROM job WHERE active=1 ORDER BY posted_at DESC").fetchall()

    # Apply filtering manually in Python
    filtered_jobs = []
    for job in jobs:
        if (
            (not query or query in job["title"].lower() or query in job["company"].lower() or query in job["description"].lower()) and
            (not experience or (job["experience"] and experience in job["experience"].lower())) and
            (not location or (job["location"] and location in job["location"].lower()))
        ):
            filtered_jobs.append(job)
    return render_template('job_apply.html', jobs=filtered_jobs)

@app.route('/feedback')
def feedback():
    if "user" in session:
        return render_template('feedback.html')
   

@app.route('/donations')  # FIXED ROUTE NAME
def donations():
    if "user" in session:
        return render_template('donationandfund.html')
    return redirect(url_for('home'))

@app.route('/create-order', methods=['POST'])
def create_order():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.json
    amount = data['amount']  # Amount is expected in paise (1 INR = 100 paise)
    
    # Create a Razorpay Order
    order_data = {
        'amount': amount,
        'currency': 'INR',
        'receipt': data.get('receipt', 'donation_'+str(int(time.time()))),
        'notes': data.get('notes', {})
    }
    
    try:
        order = razorpay_client.order.create(data=order_data)
        return jsonify(order)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.json
    
    try:
        # First verify the payment signature
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })
        
        # Then check the payment status
        payment = razorpay_client.payment.fetch(data['razorpay_payment_id'])
        if payment['status'] != 'captured':
            return jsonify({'error': 'Payment not captured', 'status': 'failure'}), 400
        
        # Get the order details
        order = razorpay_client.order.fetch(data['razorpay_order_id'])
        
        # Record the donation only if payment was successful
        with get_db() as conn:
            conn.execute(
                "INSERT INTO donations (user_id, campaign_name, amount, transaction_id) VALUES (?, ?, ?, ?)",
                (session['user']['id'], 
                 order['notes']['campaign'], 
                 order['amount']/100,  # Convert from paise to rupees
                 data['razorpay_payment_id'])
            )
            conn.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"Payment verification error: {str(e)}")
        return jsonify({'error': str(e), 'status': 'failure'}), 400
    

@app.route('/get-donation-history')
def get_donation_history():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Ensure user data is properly structured
        if not isinstance(session['user'], dict):
            session['user'] = {'id': session['user']}  # Handle case where only ID is stored
        
        user_id = session['user'].get('id')
        if not user_id:
            return jsonify({'error': 'User ID not found in session'}), 400
        
        with get_db() as conn:
            # Explicitly convert rows to dictionaries
            donations = conn.execute(
                "SELECT campaign_name, amount, transaction_id, donation_date FROM donations WHERE user_id = ? ORDER BY donation_date DESC",
                (user_id,)
            ).fetchall()
            
            # Convert each row to a dictionary properly
            donations_list = []
            for donation in donations:
                donations_list.append({
                    'campaign_name': donation[0],
                    'amount': donation[1],
                    'transaction_id': donation[2],
                    'donation_date': donation[3]
                })
            
        return jsonify(donations_list)
        
    except Exception as e:
        print(f"Error in get_donation_history: {str(e)}")
        return jsonify({'error': 'Server error', 'details': str(e)}), 500


@app.route('/generate-receipt/<transaction_id>')
def generate_receipt(transaction_id):
    # EMERGENCY OVERRIDE - Generates receipt without DB check
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    
    p.drawString(100, 800, "DONATION RECEIPT")
    p.drawString(100, 780, f"Transaction ID: {transaction_id}")
    p.drawString(100, 760, "Date: " + datetime.now().strftime("%Y-%m-%d"))
    p.drawString(100, 740, "Status: Verified Payment")
    p.drawString(100, 720, "Thank you for your donation!")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Receipt_{transaction_id}.pdf"
    )
    
@app.route('/test-donation-history')
def test_donation_history():
    # Simulate logged in user (test@example.com has id=1)
    with get_db() as conn:
        user = conn.execute("SELECT * FROM user WHERE email='test@example.com'").fetchone()
        if user:
            session['user'] = dict(user)
            return redirect(url_for('donations'))
    return "Test user not found", 404

@app.route('/get-campaign-totals')
def get_campaign_totals():
    try:
        with get_db() as conn:
            # Get total raised for each campaign
            campaigns = conn.execute(
                "SELECT campaign_name, SUM(amount) as total_raised FROM donations GROUP BY campaign_name"
            ).fetchall()
            
            # Convert to dictionary for easy access
            campaign_totals = {campaign['campaign_name']: campaign['total_raised'] for campaign in campaigns}
            
        return jsonify(campaign_totals)
        
    except Exception as e:
        print(f"Error getting campaign totals: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/success_stories')
def success_stories():
    if "user" in session:
        return render_template('success-stories.html')
    return redirect(url_for('home'))


@app.route('/mentorship')
def mentorship():
    if "user" not in session:
        return redirect(url_for('login'))

    with get_db() as conn:
        # Keep your existing mentors query exactly as is
        mentors = conn.execute("""
            SELECT 
                ms.session_id,
                u.fullname,
                u.graduation_year,
                u.privacy,
                ms.session_time as session_start_time,
                ms.session_meet_link,
                ms.session_description,
                ms.session_started,
                ms.mentor_name,
                ms.mentor_field,
                ms.mentor_image
            FROM mentor_session ms
            JOIN user u ON ms.alumni_id = u.id
            WHERE u.privacy = 'public' AND u.verified = 1 AND u.active = 1
        """).fetchall()
        
        # Modified query for upcoming sessions to use new table structure
        sessions = conn.execute("""
            SELECT 
                ms.session_id,
                ms.mentor_name,
                ms.mentor_field,
                ms.session_time as session_start_time,
                ms.session_meet_link,
                ms.session_description,
                ms.session_started,
                ms.mentor_image
            FROM mentor_session ms
            JOIN user u ON ms.alumni_id = u.id
            WHERE ms.session_time > datetime('now')
            ORDER BY ms.session_time ASC
        """).fetchall()

    return render_template('mentorship.html', mentors=mentors, sessions=sessions)

@app.route('/book_session', methods=['POST'])
def book_session():
    if "user" not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    user_email = session['user']
    try:
        with get_db() as conn:
            # Retrieve the user ID and role using the email stored in the session
            result = conn.execute("""
                SELECT id, role FROM user WHERE email = ?
            """, (user_email,)).fetchone()

            if not result:
                return jsonify({'success': False, 'message': 'User not found.'})

            user_id = result['id']
            role = result['role'].lower()

            # Only students can book sessions
            if role != 'student':
                return jsonify({'success': False, 'message': 'Only students can book sessions.'})

            data = request.get_json()
            session_id = data.get('session_id')

            if not session_id:
                return jsonify({'success': False, 'message': 'Session ID is missing.'})

            # Prevent double booking
            existing = conn.execute("""
                SELECT * FROM session_member
                WHERE session_id = ? AND student_id = ?
            """, (session_id, user_id)).fetchone()

            if existing:
                return jsonify({'success': False, 'message': 'You already booked this session.'})

            # Book the session
            conn.execute("""
                INSERT INTO session_member (session_id, student_id)
                VALUES (?, ?)
            """, (session_id, user_id))
            conn.commit()

        return jsonify({'success': True, 'message': 'Session booked successfully.'})

    except Exception as e:
        print("Error booking session:", e)
        return jsonify({'success': False, 'message': 'Internal server error'}), 500






@app.route('/direct-session')
def direct_session():
    if "user" not in session:
        return redirect(url_for('login'))

    user_role = get_user_role(session['user'])

    # Example: dynamically fetch mentor name or session_id
    mentor_name = "Your Alumni Mentor"  # You should fetch this based on session/user

    if user_role in ['student', 'alumni']:
        return redirect(f"/session-details?mentor={mentor_name}")
    return redirect(url_for('mentorship'))

@app.route('/session-details/<int:session_id>', methods=['GET', 'POST'])
def session_details(session_id):
    if "user" not in session:
        return redirect(url_for('login'))

    user_role = get_user_role(session['user'])

    # Fetch session details including mentor name and session status
    with get_db() as conn:
        session_data = conn.execute(
            "SELECT ms.*, u.fullname as mentor_name FROM mentor_session ms "
            "JOIN user u ON ms.alumni_id = u.id WHERE ms.session_id = ?",
            (session_id, )
        ).fetchone()

    if not session_data:
        return redirect(url_for('mentorship'))

    if request.method == 'POST' and user_role.lower() == 'alumni':
        # Ensure the session has not started yet
        if session_data['session_started']:
            return jsonify({'success': False, 'message': 'Session already started'}), 400
        
        # Generate meet link and update session in the databases
        meet_code = secrets.token_urlsafe(8)[:10]
        meet_link = f"https://meet.google.com/{meet_code}"
        start_time = datetime.now()

        with get_db() as conn:
            conn.execute(
                "UPDATE mentor_session SET session_meet_link = ?, session_started = 1, session_start_time = ? WHERE session_id = ?",
                (meet_link, start_time, session_id)
            )
            conn.commit()

        # Fetch updated session data
        session_data = conn.execute(
            "SELECT ms.*, u.fullname as mentor_name FROM mentor_session ms "
            "JOIN user u ON ms.alumni_id = u.id WHERE ms.session_id = ?",
            (session_id,)
        ).fetchone()

        return jsonify({
            'meet_link': meet_link,
            'session_started': session_data['session_started'],
            'session_start_time': session_data['session_start_time']
        })

    return render_template(
        'session-details.html',
        mentor_name=session_data['mentor_name'],
        user_role=user_role,
        session_id=session_id,
        meet_link=session_data['session_meet_link'],
        session_started=session_data['session_started']
    )

def normalize_meet_link(link: str) -> str:
    link = link.strip()
    if not link.startswith("http://") and not link.startswith("https://"):
        print(link)
        link = "https://" + link
    return link

    
@app.route('/save_meet_link/<int:session_id>', methods=['POST'])
def save_meet_link(session_id):
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    user_role = get_user_role(session['user'])
    if user_role.lower() != 'alumni':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json()
    meet_link = data.get('meet_link', '')
    normalized_link = normalize_meet_link(meet_link)
    
    if not meet_link:
        return jsonify({'success': False, 'message': 'Meet link is required'}), 400

    try:
        with get_db() as conn:
            session_data = conn.execute(
                "SELECT session_started FROM mentor_session WHERE session_id = ?",
                (session_id,)
            ).fetchone()

            if session_data['session_started']:
                return jsonify({'success': False, 'message': 'Session already started'}), 400

            start_time = datetime.now()
            
            conn.execute(
                "UPDATE mentor_session SET session_meet_link = ?, session_started = 1, session_start_time = ? WHERE session_id = ?",
                (normalized_link, start_time, session_id)
            )
            conn.commit()

        return jsonify({'success': True, 'message': 'Meeting link saved successfully'})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'Internal Server Error'}), 500


@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json()
    session_id = data.get('session_id')
    content = data.get('content', '').strip()

    if not session_id or not content:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400

    user_email = session['user']
    try:
        with get_db() as conn:
            user = conn.execute("SELECT id FROM user WHERE email = ?", (user_email,)).fetchone()
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404

            user_id = user['id']

            conn.execute("""
                INSERT INTO session_message (session_id, user_id, content)
                VALUES (?, ?, ?)
            """, (session_id, user_id, content))
            conn.commit()

        return jsonify({'success': True})

    except Exception as e:
        print("Error saving message:", e)
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/get_messages/<int:session_id>', methods=['GET'])
def get_message(session_id):
    try:
        with get_db() as conn:
            messages = conn.execute("""
                SELECT sm.content, sm.timestamp, u.fullname, u.role
                FROM session_message sm
                JOIN user u ON sm.user_id = u.id
                WHERE sm.session_id = ?
                ORDER BY sm.timestamp ASC
            """, (session_id,)).fetchall()

            result = [{
                'user': msg['fullname'],
                'role': msg['role'].lower(),
                'content': msg['content'],
                'timestamp': msg['timestamp']
            } for msg in messages]

        return jsonify({'success': True, 'messages': result})

    except Exception as e:
        print("Error fetching messages:", e)
        return jsonify({'success': False, 'message': 'Server error'}), 500




# import random
# import string

# def generate_fake_meet_code():
#     def random_group(length):
#         return ''.join(random.choices(string.ascii_lowercase, k=length))

#     return f"{random_group(3)}-{random_group(4)}-{random_group(3)}"

# @app.route('/generate_meet_link/<int:session_id>', methods=['POST'])
# def generate_meet_link(session_id):
#     print(f"Session ID: {session_id}")
#     if 'user' not in session:
#         print("User not found in session.")
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     user_role = get_user_role(session['user'])
#     print(f"User role: {user_role}")
#     if user_role.lower() != 'alumni':
#         print(f"Unauthorized: User role is {user_role}")
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     try:
#         meet_code = secrets.token_urlsafe(8)[:10]
#         meet_link = f"https://meet.google.com/{meet_code}"
#         start_time = datetime.now()

#         with get_db() as conn:
#             conn.execute(
#                 "UPDATE mentor_session SET session_meet_link = ?, session_started = 1, session_start_time = ? WHERE session_id = ?",
#                 (meet_link, start_time, session_id)
#             )
#             conn.commit()

#         student_ids = conn.execute(
#             "SELECT student_id FROM session_member WHERE session_id = ?",
#             (session_id,)
#         ).fetchall()

#         sender_id = session['user']
#         content = f"Your session has started. Join the meeting here: {meet_link}"

#         for row in student_ids:
#             conn.execute(
#                 "INSERT INTO message (sender_id, receiver_id, content) VALUES (?, ?, ?)",
#                 (sender_id, row['student_id'], content)
#             )

#         conn.commit()

#         return jsonify({
#             'success': True,
#             'meet_link': meet_link
#         })
#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({'success': False, 'message': 'Internal Server Error'}), 500





@app.route('/get_meet_link/<int:session_id>')
def get_meet_link(session_id):
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    with get_db() as conn:
        session_data = conn.execute(
            "SELECT session_meet_link FROM mentor_session WHERE session_id = ?",
            (session_id,)
        ).fetchone()
    
    if session_data and session_data['meet_link']:
        return jsonify({
            'success': True,
            'meet_link': session_data['meet_link']
        })
    return jsonify({
        'success': False,
        'message': 'No active session'
    })

@app.route('/admin')
def admin():
    if "user" not in session:
        return redirect(url_for('login'))

    with get_db() as conn:
        # Verify admin status (note case sensitivity)
        admin_check = conn.execute(
            "SELECT role FROM user WHERE email = ?",
            (session['user'],)
        ).fetchone()
        
        if not admin_check or admin_check['role'] != 'Admin':
            flash("Access Denied: Admin only.", "danger")
            return redirect(url_for('home'))

        # Get all the existing stats
        total_users = conn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
        active_sessions = conn.execute("SELECT COUNT(*) FROM user WHERE active = 1").fetchone()[0]
        donations_count = conn.execute("SELECT COUNT(*) FROM donations").fetchone()[0]
        job_applications_count = conn.execute("SELECT COUNT(*) FROM job_application").fetchone()[0]
        rsvp_count = conn.execute("SELECT COUNT(*) FROM rsvp").fetchone()[0]

        # NEW: Get pending role change requests
        pending_requests = conn.execute('''
            SELECT r.id, u.fullname, u.email, r.requested_role, 
                   r.requested_at, u.role as current_role
            FROM role_change_request r
            JOIN user u ON r.user_id = u.id
            WHERE r.status = 'pending'
            ORDER BY r.requested_at DESC
        ''').fetchall()

    return render_template("admin.html",
        total_users=total_users,
        active_sessions=active_sessions,
        donations_count=donations_count,
        job_applications_count=job_applications_count,
        rsvp_count=rsvp_count,
        pending_requests=pending_requests  # Pass requests to template
    )

@app.route('/admin/role_requests')
def get_role_change_requests():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    with get_db() as conn:
        # Check if user is admin
        admin_check = conn.execute(
            "SELECT role FROM user WHERE email = ?",
            (session['user'],)
        ).fetchone()
        
        if not admin_check or admin_check['role'].lower() != 'admin':
            return redirect(url_for('login'))

        requests = conn.execute('''
            SELECT r.id, u.fullname, u.email, r.requested_role, r.status, r.requested_at
            FROM role_change_request r
            JOIN user u ON r.user_id = u.id
            WHERE r.status = 'pending'
            ORDER BY r.requested_at DESC
        ''').fetchall()

    return render_template('admin.html', requests=requests)

@app.route('/admin/handle_role_change', methods=['POST'])
def handle_role_change():
    if "user" not in session:
        return redirect(url_for('login'))

    with get_db() as conn:
        # Verify admin status
        admin_check = conn.execute(
            "SELECT role FROM user WHERE email = ?",
            (session['user'],)
        ).fetchone()
        
        if not admin_check or admin_check['role'] != 'Admin':
            flash("Access Denied: Admin only.", "danger")
            return redirect(url_for('home'))

        request_id = request.form['request_id']
        action = request.form['action']
        requested_role = request.form.get('role', '')

        # Get the request details
        role_request = conn.execute(
            "SELECT user_id FROM role_change_request WHERE id = ?",
            (request_id,)
        ).fetchone()

        if not role_request:
            flash("Invalid request ID", "danger")
            return redirect(url_for('admin'))

        user_id = role_request['user_id']

        if action == 'approve':
            # Update user role
            conn.execute(
                "UPDATE user SET role = ? WHERE id = ?",
                (requested_role, user_id)
            )
            # Update request status
            conn.execute(
                "UPDATE role_change_request SET status = 'approved' WHERE id = ?",
                (request_id,)
            )
            flash("Role change approved successfully!", "success")
            
        elif action == 'reject':
            # Update request status only
            conn.execute(
                "UPDATE role_change_request SET status = 'rejected' WHERE id = ?",
                (request_id,)
            )
            flash("Role change request rejected.", "info")

        conn.commit()

    return redirect(url_for('admin'))

@app.route('/admin/job_data')
def get_job_data():
    conn = get_db()
    jobs = conn.execute("""
        SELECT job.id, title, company, location, fullname AS posted_by
        FROM job
        JOIN user ON job.employer_id = user.id
        WHERE job.active = 1
    """).fetchall()

    applications = conn.execute("""
        SELECT ja.id, applicant_name, applicant_email, title AS job_title
        FROM job_application ja
        JOIN job ON ja.job_id = job.id
    """).fetchall()

    return jsonify({
        'jobs': [dict(job) for job in jobs],
        'applications': [dict(app) for app in applications]
    })

@app.route('/admin/delete_job/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    conn = get_db()
    conn.execute("UPDATE job SET active = 0 WHERE id = ?", (job_id,))
    conn.commit()
    return jsonify({'message': 'Job marked as inactive'})

@app.route('/admin/users')
def get_users():
    conn = get_db()
    try:
        # Get active users
        active_users = conn.execute("""
            SELECT id, fullname, email, role, graduation_year, verified, active 
            FROM user
            ORDER BY fullname
        """).fetchall()
        
        # Get deleted users
        deleted_users = conn.execute("""
            SELECT id, fullname, email, role 
            FROM deleted_users
            ORDER BY fullname
        """).fetchall()
        
        return render_template('users.html', 
                            users=active_users,
                            deleted_users=deleted_users)
    finally:
        conn.close()

@app.route('/admin/users', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        role = request.form.get('role', 'user')
        graduation_year = request.form.get('graduation_year')

        conn = sqlite3.connect('alumni.db')
        c = conn.cursor()
        c.execute("INSERT INTO user (fullname, email, password_hash, role, graduation_year) VALUES (?, ?, ?, ?, ?)",
                  (fullname, email, 'default_hash', role, graduation_year))
        conn.commit()
        conn.close()

        return redirect(url_for('get_users'))

    return render_template('users.html')
    
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    from datetime import datetime
    conn = sqlite3.connect('alumni.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Step 1: Get full user info
    c.execute("SELECT * FROM user WHERE id = ?", (user_id,))
    user = c.fetchone()

    if user:
        # Step 2: Insert into deleted_users (all fields needed for full restoration)
        c.execute("""
            INSERT INTO deleted_users (
                id, fullname, email, role, graduation_year,
                verified, active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user['id'], user['fullname'], user['email'],
            user['role'], user['graduation_year'], user['verified'],
            user['active']
        ))

        # Step 3: Delete from user table
        c.execute("DELETE FROM user WHERE id = ?", (user_id,))
        conn.commit()

    conn.close()
    return redirect(url_for('get_users'))

@app.route('/admin/undelete_user/<int:user_id>', methods=['POST'])
def undelete_user(user_id):
    conn = None
    try:
        conn = get_db()  # Use your existing get_db() function
        
        # Debug print
        print(f"Attempting to restore user ID: {user_id}")
        
        # 1. Get the user from deleted_users
        user = conn.execute("SELECT * FROM deleted_users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            flash('User not found in deleted records', 'error')
            print(f"User {user_id} not found in deleted_users")
            return redirect(url_for('get_users'))

        # Debug print user data
        print(f"Found user to restore: {dict(user)}")
        
        # 2. Check if user ID already exists in main table (prevent duplicates)
        existing = conn.execute("SELECT 1 FROM user WHERE id = ?", (user_id,)).fetchone()
        if existing:
            flash('User ID already exists in active users', 'error')
            print(f"User ID {user_id} already exists in user table")
            return redirect(url_for('get_users'))

        # 3. Insert into user table with all required fields
        conn.execute("""
            INSERT INTO user (
                id, fullname, email, password_hash, role,
                graduation_year, verified, active, created_at, privacy,
                failed_attempts, locked_until
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user['id'],
            user['fullname'],
            user['email'],
            user.get('password_hash', generate_password_hash('temp_password_'+str(user_id))),
            user['role'],
            user.get('graduation_year'),
            user.get('verified', 0),
            1,  # Set as active
            user.get('created_at', datetime.now().isoformat()),
            user.get('privacy', 'public'),
            0,  # Reset failed attempts
            None  # Clear lock status
        ))

        # 4. Delete from deleted_users
        conn.execute("DELETE FROM deleted_users WHERE id = ?", (user_id,))
        conn.commit()
        
        print(f"Successfully restored user {user_id}")
        flash(f"User {user['fullname']} restored successfully", 'success')

    except sqlite3.IntegrityError as e:
        if conn: conn.rollback()
        print(f"Integrity error restoring user: {str(e)}")
        flash('Could not restore user - database constraint violated', 'error')
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error restoring user: {str(e)}")
        flash(f'Error restoring user: {str(e)}', 'error')
    finally:
        if conn: conn.close()

    return redirect(url_for('get_users'))

@app.route('/admin/donation')
def donation():
    if "user" not in session:
        return redirect(url_for('home'))
    
    try:
        conn = sqlite3.connect('alumni.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Debug: Check if tables exist
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        print("Tables:", [row['name'] for row in c.fetchall()])

        # Alternative query if you're having JOIN issues
        c.execute("""
            SELECT 
                d.id,
                u.fullname,
                d.campaign_name,
                d.amount,
                d.donation_date,
                d.transaction_id,
                d.receipt_generated
            FROM donations d
            LEFT JOIN user u ON d.user_id = u.id
            ORDER BY d.donation_date DESC
        """)
        
        donations = c.fetchall()
        
        # Debug: Print retrieved data
        if not donations:
            print("No donations found in database")
        else:
            print(f"Found {len(donations)} donation records")
            for donation in donations:
                print(dict(donation))
        
        conn.close()
        return render_template('donation.html', donations=donations)

    except sqlite3.Error as e:
        print("Database error:", str(e))
        return "Error accessing donation data", 500
    except Exception as e:
        print("Unexpected error:", str(e))
        return "An unexpected error occurred", 500
    
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)  # Remove the user from the session
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/verify-admin-key', methods=['POST'])
def verify_admin_key():
    if not session.get('user'):
        return jsonify({'valid': False})
    
    data = request.get_json()
    if not data or 'key' not in data:
        return jsonify({'valid': False})
    
    # In a real application, you might want to:
    # 1. Check if the user has admin privileges
    # 2. Use a more secure key verification method
    if data['key'] == ADMIN_SECURITY_KEY:
        return jsonify({'valid': True})
    
    return jsonify({'valid': False})


@app.route('/dashfeed')
def dashfeed():
    if "user" in session:
        return render_template('dashfeed.html')  # Make sure dashfeed.html exists in templates folder




@app.route('/events_admin')
def events_admin():
    return render_template('events_admin.html')


@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        with get_db() as conn:
            print("Fetching events from database...")  # Debug print
            
            # Remove any # comments from the SQL query
            events = conn.execute("""
                SELECT e.id, e.title, e.description, e.location, 
                       e.start_time, e.end_time, 
                       u.fullname as organizer_name
                FROM event e
                JOIN user u ON e.organizer_id = u.id
                ORDER BY e.start_time DESC
            """).fetchall()
            
            print(f"Found {len(events)} events")  # Debug print
            return jsonify([dict(event) for event in events])
            
    except Exception as e:
        print(f"Error fetching events: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

@app.route('/api/events', methods=['POST'])
def create_event():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.get_json()
    required_fields = ['title', 'description', 'location', 'start_time', 'end_time']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        with get_db() as conn:
            # Get actual user ID from session
            user = conn.execute(
                "SELECT id FROM user WHERE email = ?", 
                (session['user'],)
            ).fetchone()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            conn.execute("""
                INSERT INTO event (organizer_id, title, description, location, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user['id'],  # Use actual user ID
                data['title'],
                data['description'],
                data['location'],
                data['start_time'],
                data['end_time']
            ))
            conn.commit()
        return jsonify({'success': True}), 201
    except Exception as e:
        print(f"Error creating event: {str(e)}")  # Add error logging
        return jsonify({'error': str(e)}), 500
    
@app.route('/jobp')
def jobp():
    if "user" in session:
        return render_template('jobp.html')

@app.route('/settings')
def settings():
    if "user" not in session:
        return redirect(url_for('login'))

    with get_db() as conn:
        # Verify admin status
        admin_check = conn.execute(
            "SELECT role FROM user WHERE email = ?",
            (session['user'],)
        ).fetchone()
        
        if not admin_check or admin_check['role'] != 'Admin':
            flash("Access Denied: Admin only.", "danger")
            return redirect(url_for('home'))

        # Get pending role change requests
        pending_requests = conn.execute('''
            SELECT r.id, u.fullname, u.email, r.requested_role, 
                   r.requested_at, u.role as current_role
            FROM role_change_request r
            JOIN user u ON r.user_id = u.id
            WHERE r.status = 'pending'
            ORDER BY r.requested_at DESC
        ''').fetchall()

    return render_template("settings.html", pending_requests=pending_requests)


alumniData = [
    { 
        "name": "Mr.Ravikumar",
        "image": "alumni1.png",
        "gradYear": 2008,
        "achievements": "Built a billion-dollar AI healthcare startup.",
        "industryImpact": "Revolutionized AI-driven medical diagnostics.",
        "milestones": ["Founded HealthTech AI", "Awarded Top Innovator 2018", "Expanded to 20 countries"],
        "testimonial": "The best decision of my life was joining this university. It shaped my vision."
    },
    { 
        "name": "Dr.Prabakaran",
        "image": "alumni2.png",
        "gradYear": 2012,
        "achievements": "Pioneered AI ethics research, influencing global policies.",
        "industryImpact": "Helped create ethical AI frameworks adopted by major tech firms.",
        "milestones": ["Published 10 AI research papers", "Advised UN on AI Ethics", "Won AI Innovator Award"],
        "testimonial": "The faculty and research facilities here ignited my passion for AI ethics."
    },
    { 
        "name": "Mr.Vijaykumar",
        "image": "alumni3.png",
        "gradYear": 2015,
        "achievements": "Led human rights cases worldwide.",
        "industryImpact": "Shaped global policies on social justice and equity.",
        "milestones": ["Fought landmark case for refugee rights", "Published book on human rights", "Worked with UN Human Rights Council"],
        "testimonial": "My time here equipped me with the skills to bring justice to those in need."
    },
    { 
        "name": "Dr.Parthiban",
        "image": "alumni4.png",
        "gradYear": 2010,
        "achievements": "Transformed finance sector with blockchain innovations.",
        "industryImpact": "Created secure digital banking solutions for developing nations.",
        "milestones": ["Founded FinTech startup", "Partnered with global banks", "Featured in Forbes 30 Under 30"],
        "eliftestimonial": "I owe my success to the education and mentorship I received here."
    },
    { 
        "name": "Mr.Vinayagam",
        "image": "alumni5.png",
        "gradYear": 2011,
        "achievements": "Made breakthroughs in cancer treatment with biotechnology.",
        "industryImpact": "Developed revolutionary cancer detection methods.",
        "milestones": ["Discovered novel cancer biomarker", "Published 50+ research papers", "Received Nobel Prize in Medicine"],
        "testimonial": "The research culture here nurtured my curiosity and drive for medical innovation."
    }
]

@app.route('/alumni-profile')
def alumni_profile():
    alumni_name = request.args.get('name')
    
    # Find the alumni based on the name passed in the URL
    alumni_data = next((alumni for alumni in alumniData if alumni['name'] == alumni_name), None)
    
    if alumni_data:
        return render_template('alumni-profile.html', alumni=alumni_data)
    else:
        return "Alumni not found", 404

@app.route('/request_role_change', methods=['POST']) 
def request_role_change():
    if 'user' not in session:
        return jsonify(success=False, message="You must be logged in.")

    data = request.get_json()
    requested_role = data.get('role')

    # Updated allowed roles list (note case sensitivity)
    allowed_roles = ['student', 'Alumni', 'faculty', 'recruiter']
    if requested_role not in allowed_roles:
        return jsonify(success=False, message=f"Invalid role request. Allowed roles: {', '.join(allowed_roles)}")

    with get_db() as conn:
        # Get user ID from email in session
        user = conn.execute(
            "SELECT id FROM user WHERE email = ?", 
            (session['user'],)
        ).fetchone()
        
        if not user:
            return jsonify(success=False, message="User not found.")
            
        user_id = user['id']

        # Check for existing pending request
        existing = conn.execute(
            "SELECT id FROM role_change_request WHERE user_id = ? AND status = 'pending'",
            (user_id,)
        ).fetchone()
        
        if existing:
            return jsonify(success=False, message="You already have a pending request.")

        # Insert new request
        conn.execute(
            "INSERT INTO role_change_request (user_id, requested_role) VALUES (?, ?)",
            (user_id, requested_role)
        )
        conn.commit()

    return jsonify(success=True, message="Your request has been submitted for admin approval.")

@app.route('/block_user', methods=['POST'])
def block_user():
    if "user" not in session:
        return jsonify(status='error', message="You must be logged in")

    try:
        data = request.get_json()
        alumni_id = data.get('alumni_id')

        current_email = session['user']

        with get_db() as conn:
            # Get current user's ID
            user_row = conn.execute("SELECT id FROM user WHERE email = ?", (current_email,)).fetchone()
            if not user_row:
                return jsonify(status='error', message="Current user not found")

            current_user_id = user_row['id']

            # Insert into blocked_users
            conn.execute("INSERT OR IGNORE INTO user_block (blocker_id, blocked_id) VALUES (?, ?)",
                         (current_user_id, alumni_id))

            # Remove connection both ways
            conn.execute("""
                DELETE FROM connection
                WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
            """, (current_user_id, alumni_id, alumni_id, current_user_id))

            conn.commit()
            return jsonify(status='success')

    except Exception as e:
        return jsonify(status='error', message=str(e))

@app.template_filter('escapejs')
def escapejs_filter(s):
    return escape(s)  # Or use a more specific escaping logic for JavaScript if needed

@app.route('/api/connections')
def get_connections():
    if "user" not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    with get_db() as conn:
        # Get current user's ID
        current_user = conn.execute("SELECT id FROM user WHERE email = ?", (session["user"],)).fetchone()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = current_user['id']

        # Get accepted connections
        query = """
        SELECT 
            u.id,
            u.fullname as name,
            u.email,
            p.current_job as position,
            p.company,
            u.graduation_year
        FROM connection c
        JOIN user u ON (
            (c.sender_id = u.id AND c.receiver_id = ?) OR 
            (c.receiver_id = u.id AND c.sender_id = ?)
        )
        LEFT JOIN profile p ON u.id = p.user_id
        WHERE c.status = 'accepted'
        """
        results = conn.execute(query, (user_id, user_id)).fetchall()
        
        return jsonify([dict(row) for row in results])
    
@app.route('/api/get_conversations')
def get_conversations():
    if "user" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    with get_db() as conn:
        current_user = conn.execute("SELECT id FROM user WHERE email = ?", (session["user"],)).fetchone()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get all conversations (users you've messaged or received messages from)
        conversations = conn.execute("""
            SELECT DISTINCT u.id, u.fullname, 
                   (SELECT content FROM message 
                    WHERE (sender_id = ? AND receiver_id = u.id) OR (sender_id = u.id AND receiver_id = ?)
                    ORDER BY timestamp DESC LIMIT 1) as last_message
            FROM user u
            JOIN message m ON (m.sender_id = u.id OR m.receiver_id = u.id)
            WHERE (m.sender_id = ? OR m.receiver_id = ?) AND u.id != ?
            ORDER BY (SELECT MAX(timestamp) FROM message 
                     WHERE (sender_id = ? AND receiver_id = u.id) OR (sender_id = u.id AND receiver_id = ?)) DESC
        """, (current_user['id'], current_user['id'], current_user['id'], current_user['id'], current_user['id'], 
            current_user['id'], current_user['id'])).fetchall()
        
        return jsonify([dict(conv) for conv in conversations])

@app.route('/api/get_user_details')
def get_user_details():
    if "user" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    with get_db() as conn:
        user = conn.execute("""
            SELECT fullname, email FROM user 
            WHERE id = ?
        """, (user_id,)).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(dict(user))

@app.route('/api/get_messages')
def get_messages():
    if "user" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    with get_db() as conn:
        current_user = conn.execute("SELECT id FROM user WHERE email = ?", (session["user"],)).fetchone()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        other_user_id = request.args.get('other_user_id')
        if not other_user_id:
            return jsonify({'error': 'Other user ID required'}), 400
        
        messages = conn.execute("""
            SELECT m.*, 
                   CASE WHEN m.sender_id = ? THEN 1 ELSE 0 END as is_sender
            FROM message m
            WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.timestamp ASC
        """, (current_user['id'], current_user['id'], other_user_id, other_user_id, current_user['id'])).fetchall()
        
        return jsonify([dict(msg) for msg in messages])

@app.route('/api/send_message', methods=['POST'])
def send_messages():
    if "user" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    if not data or 'receiver_id' not in data or 'content' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    with get_db() as conn:
        current_user = conn.execute("SELECT id FROM user WHERE email = ?", (session["user"],)).fetchone()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if users are connected
        is_connected = conn.execute("""
            SELECT 1 FROM connection 
            WHERE ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?))
            AND status = 'accepted'
            LIMIT 1
        """, (current_user['id'], data['receiver_id'], data['receiver_id'], current_user['id'])).fetchone()
        
        if not is_connected:
            return jsonify({'error': 'You must be connected to message this user'}), 403
        
        # Insert message
        conn.execute(
            "INSERT INTO message (sender_id, receiver_id, content) VALUES (?, ?, ?)",
            (current_user['id'], data['receiver_id'], data['content'])
        )
        conn.commit()
        
        return jsonify({'status': 'success'})
    
if __name__ == '__main__':
    app.run(debug=True)
