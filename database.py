import sqlite3
import hashlib
import uuid
from datetime import datetime

DB_NAME = "app.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    
    # Sessions Table (New!) - Stores the conversation metadata
    c.execute('''CREATE TABLE IF NOT EXISTS sessions 
                 (session_id TEXT PRIMARY KEY, username TEXT, 
                  title TEXT, image_path TEXT, created_at DATETIME)''')
                  
    # Messages Table - Linked to Session ID
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  session_id TEXT, role TEXT, content TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
    user = c.fetchone()
    conn.close()
    return user is not None

# --- Session Management ---

def create_session(username, title, image_path):
    """Creates a new chat session."""
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (session_id, username, title, image_path, created_at) VALUES (?, ?, ?, ?, ?)",
              (session_id, username, title, image_path, datetime.now()))
    conn.commit()
    conn.close()
    return session_id

def get_user_sessions(username):
    """Returns list of sessions for the sidebar."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT session_id, title, created_at FROM sessions WHERE username=? ORDER BY created_at DESC", (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_session_details(session_id):
    """Get image path for a session."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT image_path, title FROM sessions WHERE session_id=?", (session_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_message(session_id, role, content):
    """Save a message to a specific session."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", 
              (session_id, role, content))
    conn.commit()
    conn.close()

def get_session_messages(session_id):
    """Get full chat history for a session."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY id ASC", (session_id,))
    rows = c.fetchall()
    conn.close()
    return rows