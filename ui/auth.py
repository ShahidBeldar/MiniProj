"""
ui/auth.py — Streamlit session management, login/register UI.
FIX: do_logout() no longer calls st.rerun() — callers decide whether to rerun.
FIX: Login rate-limiting via @st.cache_resource tracker.
FIX: Username validated (alphanumeric + underscore, 3-30 chars).
Session keys prefixed _fi_ so they never clash with widget keys.
"""
from __future__ import annotations
import os
import re
import time
import bcrypt
import streamlit as st

from db.schema import init_db, seed_users
from db.ops import get_user, create_user, touch_login, set_password


# ── RATE-LIMIT TRACKER ────────────────────────────────────────────────────────
# @st.cache_resource persists the dict across reruns and sessions on the same
# server process — exactly the right scope for brute-force protection.

@st.cache_resource
def _attempt_tracker() -> dict:
    """Returns a mutable dict {username: (fail_count, first_fail_ts)}."""
    return {}


_MAX_ATTEMPTS    = 5
_LOCKOUT_SECONDS = 300   # 5 minutes


def _check_rate_limit(username: str) -> tuple[bool, str]:
    tracker = _attempt_tracker()
    now = time.time()
    count, first_ts = tracker.get(username, (0, now))
    if count >= _MAX_ATTEMPTS and (now - first_ts) < _LOCKOUT_SECONDS:
        remaining = int(_LOCKOUT_SECONDS - (now - first_ts))
        return False, f"Too many failed attempts. Try again in {remaining}s."
    return True, ""


def _record_failure(username: str) -> None:
    tracker = _attempt_tracker()
    count, first_ts = tracker.get(username, (0, time.time()))
    tracker[username] = (count + 1, first_ts)


def _clear_failures(username: str) -> None:
    _attempt_tracker().pop(username, None)


# ── PASSWORD HELPERS ──────────────────────────────────────────────────────────

def _hash(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── SESSION QUERIES ───────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    return bool(st.session_state.get("_fi_loggedin", False))


def current_user() -> dict:
    return st.session_state.get("_fi_user") or {}


def uid() -> int:
    return current_user().get("id", 0)


def uname() -> str:
    return current_user().get("username", "guest")


def require_login() -> None:
    if not is_logged_in():
        st.error("Authentication required. Please sign in.")
        st.stop()


# ── AUTH ACTIONS ──────────────────────────────────────────────────────────────

def do_login(username: str, password: str) -> tuple[bool, str]:
    if not username.strip() or not password:
        return False, "Please enter both username and password."

    un = username.strip().lower()
    allowed, msg = _check_rate_limit(un)
    if not allowed:
        return False, msg

    user = get_user(un)
    if not user or not _verify(password, user["password_hash"]):
        _record_failure(un)
        return False, "Invalid credentials."

    _clear_failures(un)
    st.session_state["_fi_loggedin"] = True
    st.session_state["_fi_user"] = {
        "id":       user["id"],
        "username": user["username"],
        "email":    user.get("email", ""),
        "role":     user.get("role", "user"),
    }
    touch_login(user["id"])
    return True, f"Welcome back, {user['username']}."


def do_logout() -> None:
    """Clear all session state. Caller is responsible for st.rerun()."""
    for k in list(st.session_state.keys()):
        del st.session_state[k]


def do_register(
    username: str, password: str, confirm: str, email: str = ""
) -> tuple[bool, str]:
    username = username.strip().lower()
    if not re.match(r"^[a-z0-9_]{3,30}$", username):
        return False, "Username must be 3–30 chars: letters, numbers, underscores only."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if password != confirm:
        return False, "Passwords do not match."
    if get_user(username):
        return False, "Username already taken."
    if create_user(username, _hash(password), email):
        return True, "Account created. You may now sign in."
    return False, "Registration failed — please try again."


def do_change_password(
    user_id: int, old: str, new: str, confirm: str
) -> tuple[bool, str]:
    user = current_user()
    if not user:
        return False, "Not authenticated."
    db_user = get_user(user["username"])
    if not db_user or not _verify(old, db_user["password_hash"]):
        return False, "Current password is incorrect."
    if len(new) < 6:
        return False, "New password must be at least 6 characters."
    if new != confirm:
        return False, "New passwords do not match."
    set_password(user_id, _hash(new))
    return True, "Password updated successfully."


# ── BOOTSTRAP ─────────────────────────────────────────────────────────────────

def bootstrap() -> None:
    init_db()
    seed_users()


# ── LOGIN PAGE ────────────────────────────────────────────────────────────────

def render_login_page() -> None:
    st.markdown("""
    <style>
      [data-testid="stSidebar"] { display:none !important; }
      [data-testid="stHeader"]  { display:none !important; }
      footer { display:none !important; }
      .block-container { padding-top: 4.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:2.5rem;">
      <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:2.4rem;
                  color:#DDE6F0;letter-spacing:-.025em;">
        Finance<span style="color:#00C8F0;">Impact</span>
      </div>
      <div style="font-family:'Manrope',sans-serif;color:#3D5268;font-size:.67rem;
                  letter-spacing:.22em;text-transform:uppercase;margin-top:7px;">
        Market Intelligence Platform
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        tab_in, tab_reg = st.tabs(["Sign In", "Register"])

        with tab_in:
            with st.form("_login_form"):
                lu = st.text_input("Username", placeholder="Username",  key="_lf_u")
                lp = st.text_input("Password", type="password",
                                   placeholder="Password", key="_lf_p")
                lb = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            if lb:
                ok, msg = do_login(lu, lp)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)

            # Only show hint in dev mode
            if os.environ.get("FI_DEV_MODE", "0") == "1":
                st.markdown("""
                <div style="text-align:center;margin-top:.8rem;font-size:.68rem;
                            color:#3D5268;font-family:'Manrope',sans-serif;">
                  Demo &nbsp;·&nbsp;
                  <code>admin / admin123</code> &nbsp;·&nbsp;
                  <code>demo / demo1234</code>
                </div>
                """, unsafe_allow_html=True)

        with tab_reg:
            with st.form("_register_form"):
                ru  = st.text_input("Username",         placeholder="Choose a username (3-30 chars)", key="_rf_u")
                re_ = st.text_input("Email (optional)", placeholder="Optional",                       key="_rf_e")
                rp  = st.text_input("Password",         type="password", placeholder="Min 6 characters", key="_rf_p")
                rc  = st.text_input("Confirm Password", type="password", placeholder="Repeat password",  key="_rf_c")
                rb  = st.form_submit_button("Create Account", use_container_width=True, type="primary")
            if rb:
                ok, msg = do_register(ru, rp, rc, re_)
                st.success(msg) if ok else st.error(msg)
