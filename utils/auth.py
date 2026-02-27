"""
auth.py — Authentication, session management, login UI.
Session is stored in st.session_state and persists across page navigation.
"""

import bcrypt
import streamlit as st
from utils.db import (
    get_user_by_username, create_user,
    update_last_login, update_user_password,
    init_db, seed_default_users,
)


# ── PASSWORDS ─────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ── SESSION HELPERS ───────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in", False))


def current_user() -> dict | None:
    return st.session_state.get("_fi_user", None)


def current_user_id() -> int | None:
    u = current_user()
    return u["id"] if u else None


def current_username() -> str:
    u = current_user()
    return u["username"] if u else "guest"


def require_login():
    """Call at top of every protected page. Stops rendering if not authenticated."""
    if not is_logged_in():
        st.warning("Please sign in to access this page.")
        st.stop()


# ── LOGIN / LOGOUT ────────────────────────────────────────────────────────────

def login(username: str, password: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "Please enter both username and password."
    user = get_user_by_username(username.strip().lower())
    if not user:
        return False, "Invalid username or password."
    if not verify_password(password, user["password_hash"]):
        return False, "Invalid username or password."

    # Persist session — using a stable key so it survives page switches
    st.session_state["logged_in"] = True
    st.session_state["_fi_user"]  = {
        "id":       user["id"],
        "username": user["username"],
        "email":    user["email"] or "",
        "role":     user["role"],
    }
    update_last_login(user["id"])
    return True, f"Welcome back, {user['username']}."


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# ── REGISTER ─────────────────────────────────────────────────────────────────

def register(username: str, password: str, confirm: str, email: str = "") -> tuple[bool, str]:
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
    if create_user(username, hashed, email, role="user"):
        return True, "Account created. You can now sign in."
    return False, "Registration failed. Please try again."


# ── CHANGE PASSWORD ───────────────────────────────────────────────────────────

def change_password(user_id: int, old_pass: str, new_pass: str, confirm: str) -> tuple[bool, str]:
    user = current_user()
    if not user:
        return False, "Not authenticated."
    db_user = get_user_by_username(user["username"])
    if not db_user or not verify_password(old_pass, db_user["password_hash"]):
        return False, "Current password is incorrect."
    if len(new_pass) < 6:
        return False, "New password must be at least 6 characters."
    if new_pass != confirm:
        return False, "New passwords do not match."
    update_user_password(user_id, hash_password(new_pass))
    return True, "Password updated successfully."


# ── BOOTSTRAP ─────────────────────────────────────────────────────────────────

def bootstrap():
    """Run once at startup — ensures DB exists and default users are seeded."""
    init_db()
    seed_default_users()


# ── LOGIN PAGE UI ─────────────────────────────────────────────────────────────

def render_login_page():
    st.markdown("""
        <style>
        [data-testid="stHeader"]{display:none!important;}
        [data-testid="stSidebar"]{display:none!important;}
        footer{display:none!important;}
        .block-container{padding-top:4rem!important;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='text-align:center;margin-bottom:2.5rem;'>
            <div style='font-family:Syne,sans-serif;font-weight:800;font-size:2rem;
                        color:#DDE6F0;letter-spacing:-0.02em;'>
                Finance<span style='color:#00C8F0;'>Impact</span>
            </div>
            <div style='color:#3D5268;font-size:0.72rem;letter-spacing:0.18em;
                        text-transform:uppercase;margin-top:6px;'>
                Market Intelligence Platform
            </div>
        </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        tab_in, tab_reg = st.tabs(["Sign In", "Register"])

        with tab_in:
            with st.form("login_form", clear_on_submit=False):
                username  = st.text_input("Username", placeholder="Enter username")
                password  = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            if submitted:
                ok, msg = login(username, password)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            st.markdown("""
                <div style='text-align:center;margin-top:1rem;font-size:0.72rem;color:#3D5268;'>
                    Demo accounts:
                    <code>admin / admin123</code> &nbsp;&middot;&nbsp;
                    <code>demo / demo1234</code> &nbsp;&middot;&nbsp;
                    <code>guest / guest123</code>
                </div>
            """, unsafe_allow_html=True)

        with tab_reg:
            with st.form("register_form", clear_on_submit=True):
                nu  = st.text_input("Username", placeholder="Choose a username")
                ne  = st.text_input("Email (optional)", placeholder="your@email.com")
                np  = st.text_input("Password", type="password", placeholder="Min. 6 characters")
                nc  = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
                rb  = st.form_submit_button("Create Account", use_container_width=True, type="primary")
            if rb:
                ok, msg = register(nu, np, nc, ne)
                st.success(msg) if ok else st.error(msg)
