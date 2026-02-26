"""
auth.py — Secure authentication using bcrypt + SQLite
No plaintext passwords anywhere.
"""

import bcrypt
import streamlit as st
from utils.database import (
    get_user_by_username, create_user,
    update_last_login, update_user_password,
    init_db, seed_default_users
)


# ── PASSWORD UTILS ────────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ── SESSION HELPERS ───────────────────────────────────────────────────────────
def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)

def current_user() -> dict | None:
    return st.session_state.get("user", None)

def current_user_id() -> int | None:
    user = current_user()
    return user["id"] if user else None

def current_username() -> str:
    user = current_user()
    return user["username"] if user else "guest"

def require_login():
    """Call at top of any protected page. Redirects to login if not authenticated."""
    if not is_logged_in():
        st.warning("Please log in to access this page.")
        st.stop()


# ── LOGIN / LOGOUT ────────────────────────────────────────────────────────────
def login(username: str, password: str) -> tuple[bool, str]:
    """
    Attempt login. Returns (success, message).
    """
    if not username or not password:
        return False, "Please enter both username and password."

    user = get_user_by_username(username.strip().lower())
    if not user:
        return False, "Invalid username or password."

    if not verify_password(password, user["password_hash"]):
        return False, "Invalid username or password."

    # Set session
    st.session_state["logged_in"] = True
    st.session_state["user"] = {
        "id":       user["id"],
        "username": user["username"],
        "email":    user["email"],
        "role":     user["role"],
    }
    update_last_login(user["id"])
    return True, f"Welcome back, {user['username']}!"

def logout():
    """Clear all session state and force rerun."""
    for key in ["logged_in", "user", "analysis_result", "current_ticker"]:
        st.session_state.pop(key, None)
    st.rerun()


# ── REGISTER ──────────────────────────────────────────────────────────────────
def register(username: str, password: str, confirm: str, email: str = "") -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    username = username.strip().lower()

    if not username or not password:
        return False, "Username and password are required."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if password != confirm:
        return False, "Passwords do not match."
    if get_user_by_username(username):
        return False, "Username already taken."

    hashed = hash_password(password)
    success = create_user(username, hashed, email, role="user")
    if success:
        return True, "Account created! You can now log in."
    return False, "Registration failed. Please try again."


# ── CHANGE PASSWORD ───────────────────────────────────────────────────────────
def change_password(user_id: int, old_pass: str, new_pass: str, confirm: str) -> tuple[bool, str]:
    user = current_user()
    if not user:
        return False, "Not authenticated."
    if not verify_password(old_pass, get_user_by_username(user["username"])["password_hash"]):
        return False, "Current password is incorrect."
    if len(new_pass) < 6:
        return False, "New password must be at least 6 characters."
    if new_pass != confirm:
        return False, "New passwords do not match."
    update_user_password(user_id, hash_password(new_pass))
    return True, "Password updated successfully."


# ── APP BOOTSTRAP ─────────────────────────────────────────────────────────────
def bootstrap():
    """Call once on app start — ensures DB exists and default users are seeded."""
    init_db()
    seed_default_users()


# ── LOGIN PAGE UI ─────────────────────────────────────────────────────────────
def render_login_page():
    """Full login/register page rendered in Streamlit."""
    st.markdown("""
        <style>
        [data-testid="stHeader"]{display:none!important;}
        [data-testid="stSidebar"]{display:none!important;}
        footer{display:none!important;}
        .block-container{padding-top:3rem!important;}
        </style>
    """, unsafe_allow_html=True)

    # Center logo
    st.markdown("""
        <div style='text-align:center;margin-bottom:2rem;'>
            <h1 style='font-size:2.2rem;font-weight:800;color:#DDE6F0;letter-spacing:-0.02em;'>
                Finance<span style='color:#00C8F0;'>Impact</span>
            </h1>
            <p style='color:#3D5268;font-size:0.8rem;letter-spacing:0.15em;text-transform:uppercase;'>
                Market Intelligence Platform
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Tab toggle
    if "auth_tab" not in st.session_state:
        st.session_state["auth_tab"] = "login"

    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        tab1, tab2 = st.tabs(["Sign In", "Register"])

        # ── SIGN IN ──
        with tab1:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

            if submitted:
                ok, msg = login(username, password)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

            st.markdown("""
                <div style='text-align:center;margin-top:1rem;'>
                    <span style='font-size:0.75rem;color:#3D5268;'>
                        Demo: <code>admin / admin123</code> &nbsp;·&nbsp;
                        <code>demo / demo1234</code> &nbsp;·&nbsp;
                        <code>guest / guest123</code>
                    </span>
                </div>
            """, unsafe_allow_html=True)

        # ── REGISTER ──
        with tab2:
            with st.form("register_form", clear_on_submit=True):
                new_user  = st.text_input("Username", placeholder="Choose a username")
                new_email = st.text_input("Email (optional)", placeholder="your@email.com")
                new_pass  = st.text_input("Password", type="password", placeholder="Min. 6 characters")
                new_conf  = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
                reg_btn   = st.form_submit_button("Create Account →", use_container_width=True, type="primary")

            if reg_btn:
                ok, msg = register(new_user, new_pass, new_conf, new_email)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
