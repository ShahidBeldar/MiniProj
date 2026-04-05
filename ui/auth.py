"""
ui/auth.py — Streamlit session management, login/register UI.
FIX: Login form submit check is inside with st.form() context.
FIX: do_logout() only deletes _fi_ prefixed keys, preserving widget state.
FIX: Rate-limit constants configurable via env vars.
FIX: Email validated with basic regex when non-empty.
FIX: bootstrap() guarded with @st.cache_resource so it runs once per process.
FIX: register variable renamed from re_ to email_ to avoid shadowing re module.
FIX: validate_password() centralised so register and change_password share rules.
Session keys prefixed _fi_ so they never clash with widget keys.
"""
from __future__ import annotations
import os
import re
import time
import secrets
import bcrypt
import streamlit as st

from db.schema import ensure_db
from db.ops import get_user, create_user, touch_login, set_password

# ── SESSION TOKEN STORE ───────────────────────────────────────────────────────
# Maps token -> user dict, lives at process level (survives Streamlit reruns).
# On browser refresh, session_state is wiped but the ?sid= query param survives,
# allowing automatic re-hydration of the login session.

@st.cache_resource
def _token_store() -> dict:
    return {}

@st.cache_resource
def _token_expiry() -> dict:
    return {}

_TOKEN_PARAM = "sid"
_TOKEN_TTL   = 60 * 60 * 8   # 8 hours

_MAX_ATTEMPTS    = int(os.environ.get("FI_MAX_ATTEMPTS",    "5"))
_LOCKOUT_SECONDS = int(os.environ.get("FI_LOCKOUT_SECONDS", "300"))


@st.cache_resource
def _attempt_tracker() -> dict:
    return {}


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


def _hash(plain: str) -> str:
    rounds = int(os.environ.get("FI_BCRYPT_ROUNDS", "12"))
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=rounds)).decode()


def _verify(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def validate_password(pwd: str) -> tuple[bool, str]:
    if len(pwd) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    if not email:
        return True, ""
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "Invalid email address format."
    return True, ""


def _try_restore_session() -> bool:
    """Re-hydrate session_state from ?sid= query param on page refresh."""
    if st.session_state.get("_fi_loggedin"):
        return True
    try:
        token = st.query_params.get(_TOKEN_PARAM, "")
    except Exception:
        return False
    if not token:
        return False
    expiry = _token_expiry()
    store  = _token_store()
    if token not in store or time.time() > expiry.get(token, 0):
        # Expired or unknown — clean up
        store.pop(token, None)
        expiry.pop(token, None)
        return False
    user = store[token]
    st.session_state["_fi_loggedin"] = True
    st.session_state["_fi_user"]     = user
    st.session_state["_fi_token"]    = token
    return True


def is_logged_in() -> bool:
    if st.session_state.get("_fi_loggedin"):
        return True
    return _try_restore_session()


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
    user_dict = {
        "id":       user["id"],
        "username": user["username"],
        "email":    user.get("email", ""),
        "role":     user.get("role", "user"),
    }
    token = secrets.token_urlsafe(32)
    _token_store()[token]  = user_dict
    _token_expiry()[token] = time.time() + _TOKEN_TTL
    st.session_state["_fi_loggedin"] = True
    st.session_state["_fi_user"]     = user_dict
    st.session_state["_fi_token"]    = token
    # Embed token in URL so page refresh re-hydrates the session
    try:
        st.query_params[_TOKEN_PARAM] = token
    except Exception:
        pass
    touch_login(user["id"])
    return True, f"Welcome back, {user['username']}."


def do_logout() -> None:
    """Revoke session token and clear all _fi_ session keys."""
    token = st.session_state.get("_fi_token")
    if token:
        _token_store().pop(token, None)
        _token_expiry().pop(token, None)
    try:
        st.query_params.clear()
    except Exception:
        pass
    for k in [k for k in list(st.session_state.keys()) if k.startswith("_fi_")]:
        del st.session_state[k]


def do_register(username: str, password: str, confirm: str, email: str = "") -> tuple[bool, str]:
    username = username.strip().lower()
    if not re.match(r"^[a-z0-9_]{3,30}$", username):
        return False, "Username must be 3-30 chars: letters, numbers, underscores only."
    ok, msg = validate_password(password)
    if not ok:
        return False, msg
    if password != confirm:
        return False, "Passwords do not match."
    ok_e, msg_e = validate_email(email)
    if not ok_e:
        return False, msg_e
    if get_user(username):
        return False, "Username already taken."
    if create_user(username, _hash(password), email):
        return True, "Account created. You may now sign in."
    return False, "Registration failed — please try again."


def do_change_password(user_id: int, old: str, new: str, confirm: str) -> tuple[bool, str]:
    user = current_user()
    if not user:
        return False, "Not authenticated."
    db_user = get_user(user["username"])
    if not db_user or not _verify(old, db_user["password_hash"]):
        return False, "Current password is incorrect."
    ok, msg = validate_password(new)
    if not ok:
        return False, msg
    if new != confirm:
        return False, "New passwords do not match."
    set_password(user_id, _hash(new))
    return True, "Password updated successfully."


@st.cache_resource
def _bootstrap_once() -> bool:
    """Runs once per server process. ensure_db() handles init + seeding atomically."""
    ensure_db()
    return True


def bootstrap() -> None:
    _bootstrap_once()


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
            # FIX: form submit check is INSIDE the with st.form() context
            with st.form("_login_form"):
                lu = st.text_input("Username", placeholder="Username", key="_lf_u")
                lp = st.text_input("Password", type="password", placeholder="Password", key="_lf_p")
                lb = st.form_submit_button("Sign In", use_container_width=True, type="primary")
                if lb:
                    ok, msg = do_login(lu, lp)
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("""
                <div style="text-align:center;margin-top:.8rem;font-size:.68rem;
                            color:#3D5268;font-family:'Manrope',sans-serif;">
                  Demo &nbsp;&middot;&nbsp;
                  <code>admin / admin123</code> &nbsp;&middot;&nbsp;
                  <code>demo / demo1234</code>
                </div>
                """, unsafe_allow_html=True)

        with tab_reg:
            # FIX: renamed re_ to email_ to avoid shadowing the re module
            with st.form("_register_form"):
                ru     = st.text_input("Username",         placeholder="Choose a username (3-30 chars)", key="_rf_u")
                email_ = st.text_input("Email (optional)", placeholder="Optional",                       key="_rf_e")
                rp     = st.text_input("Password",         type="password", placeholder="Min 6 characters", key="_rf_p")
                rc     = st.text_input("Confirm Password", type="password", placeholder="Repeat password",  key="_rf_c")
                rb     = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                if rb:
                    ok, msg = do_register(ru, rp, rc, email_)
                    st.success(msg) if ok else st.error(msg)
