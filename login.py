import streamlit as st

# --- Simple user database (for demo) ---
USER_CREDENTIALS = {
    "admin": "1234",
    "user": "password",
    "guest": "guest123"
}

def login_page():
    st.set_page_config(page_title="Login | Fake News Impact Simulator", page_icon="🔐", layout="centered")

    # --- Centered Layout ---
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #141E30, #243B55);
            color: white;
        }
        .login-box {
            background-color: rgba(255,255,255,0.1);
            padding: 3rem 2rem;
            border-radius: 20px;
            box-shadow: 0 0 25px rgba(0,0,0,0.4);
            width: 400px;
            margin: auto;
            margin-top: 10vh;
        }
        input {
            border-radius: 10px !important;
        }
        .title {
            text-align: center;
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Login Box ---
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<div class="title">🔐 Login to Continue</div>', unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", placeholder="Enter password", type="password")

        login_btn = st.button("Login", use_container_width=True)

        if login_btn:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Welcome, {username}! Redirecting...")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown("</div>", unsafe_allow_html=True)
