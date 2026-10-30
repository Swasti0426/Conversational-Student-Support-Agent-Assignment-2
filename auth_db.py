
import sqlite3
import hashlib
import hmac
import secrets
from pathlib import Path

# Database will be stored inside the data folder.
DB_FILE = Path(__file__).parent / "data" / "student_support.db"


# --------------------------------------------------
# 1. DATABASE CONNECTION
# --------------------------------------------------

def get_connection():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# --------------------------------------------------
# 2. PASSWORD SECURITY
# --------------------------------------------------

def hash_password(password, salt=None):
    """Store a salted password hash, not the plain password."""

    if salt is None:
        salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200_000
    )

    return salt.hex(), password_hash.hex()


def verify_password(password, salt_hex, hash_hex):
    """Verify a password against its stored hash."""

    salt = bytes.fromhex(salt_hex)
    _, calculated_hash = hash_password(password, salt)

    return hmac.compare_digest(calculated_hash, hash_hex)


# --------------------------------------------------
# 3. CREATE DATABASE TABLES
# --------------------------------------------------

def initialize_database():
    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('student', 'admin')),
                student_id TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT 'New conversation',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)


# --------------------------------------------------
# 4. CREATE USER ACCOUNT
# --------------------------------------------------

def create_user(username, password, role="student", student_id=None):
    """Create an account with a securely hashed password."""

    username = username.strip().lower()

    if not username or len(password) < 8:
        return False, (
            "Username is required and password must be "
            "at least 8 characters."
        )

    if role not in {"student", "admin"}:
        return False, "Invalid account role."

    if role == "student" and not student_id:
        return False, "A student account must have a student ID."

    if role == "admin":
        student_id = None

    salt, password_hash = hash_password(password)

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users
                    (username, password_salt, password_hash, role, student_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, salt, password_hash, role, student_id)
            )

        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "Username or student ID is already registered."


# --------------------------------------------------
# 5. AUTHENTICATE USER
# --------------------------------------------------

def authenticate_user(username, password):
    """Return account details only after password verification."""

    with get_connection() as connection:
        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username.strip().lower(),)
        ).fetchone()

    if user is None:
        return None

    if not verify_password(
        password,
        user["password_salt"],
        user["password_hash"]
    ):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "student_id": user["student_id"]
    }


# --------------------------------------------------
# 6. CREATE CONVERSATION
# --------------------------------------------------

def create_conversation(user_id, title="New conversation"):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO conversations (user_id, title)
            VALUES (?, ?)
            """,
            (user_id, title)
        )

        return cursor.lastrowid


# --------------------------------------------------
# 7. LIST A USER'S CONVERSATIONS
# --------------------------------------------------

def list_conversations(user_id):
    """Return only conversations belonging to this user."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,)
        ).fetchall()

    return [dict(row) for row in rows]


# --------------------------------------------------
# 8. LOAD CONVERSATION MESSAGES
# --------------------------------------------------

def get_messages(user_id, conversation_id):
    """Check ownership before returning any conversation messages."""

    with get_connection() as connection:
        conversation = connection.execute(
            """
            SELECT id FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id)
        ).fetchone()

        if conversation is None:
            return None

        rows = connection.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id
            """,
            (conversation_id,)
        ).fetchall()

    return [dict(row) for row in rows]


# --------------------------------------------------
# 9. SAVE A MESSAGE
# --------------------------------------------------

def add_message(user_id, conversation_id, role, content):
    """Save a message only when the user owns the conversation."""

    if role not in {"user", "assistant"}:
        raise ValueError("Invalid message role.")

    with get_connection() as connection:
        conversation = connection.execute(
            """
            SELECT id FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id)
        ).fetchone()

        if conversation is None:
            raise PermissionError("Conversation access denied.")

        connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content)
        )

        connection.execute(
            """
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id)
        )


# --------------------------------------------------
# 10. RENAME A CONVERSATION
# --------------------------------------------------

def rename_conversation(user_id, conversation_id, title):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE conversations
            SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (title[:80], conversation_id, user_id)
        )

        return cursor.rowcount == 1


# --------------------------------------------------
# 11. DELETE A CONVERSATION
# --------------------------------------------------

def delete_conversation(user_id, conversation_id):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id)
        )

        return cursor.rowcount == 1


# Create the database tables when this module is imported.
initialize_database()
