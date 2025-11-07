import streamlit as st
import time

# --- Simple user database (for demo) ---
# NOTE: With the demo credentials box removed,
# you must know these to log in.
USER_CREDENTIALS = {
    "admin": "1234",
    "user": "password",
    "guest": "guest123"
}

# --- Login Page Function ---
def login_page():
    st.set_page_config(
        page_title="Login | Finance News Simulator",
        page_icon="📈",  # Changed to a more relevant icon
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # --- Professional CSS Styling ---
    st.markdown("""
        <style>
            /* Hide Streamlit default elements */
            [data-testid="stHeader"], [data-testid="stFooter"], #MainMenu {
                display: none;
            }
            
            /* Set a clean, light background for the page */
            .stApp {
                background-color: #f0f2f6;
            }
            
            /* Style the login container (card) */
            [data-testid="stVerticalBlockBorderWrapper"] > div {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                padding: 2.5rem 2rem;
            }
            
            /* Constrain the width of the login box */
            .stApp > div[data-testid="stVerticalBlock"] {
                max-width: 450px;
                margin: auto;
            }

            /* --- Custom Title Styles --- */
            .login-title {
                text-align: center;
                font-size: 1.8rem;
                font-weight: 700;
                color: #1a1a1a;
                margin-bottom: 0.5rem;
            }
            
            .login-subtitle {
                text-align: center;
                color: #555;
                margin-bottom: 2rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- Login Box Layout ---
    with st.container(border=True):
        st.markdown('<div class="login-title">📈 Finance News Impact Simulator</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Access your financial news analysis dashboard</div>', unsafe_allow_html=True)

        username = st.text_input(
            "Username",
            placeholder="Username",
            label_visibility="collapsed"
        )
        password = st.text_input(
            "Password",
            placeholder="Password",
            type="password",
            label_visibility="collapsed"
        )
        
        # Add a little space before the button
        st.write("") 

        login_btn = st.button("Login", use_container_width=True, type="primary")

        if login_btn:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Login successful! Redirecting...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username or password.")

# --- Main App Page Function (Placeholder) ---
def main_app_page():
    st.set_page_config(page_title="Simulator Dashboard", page_icon="📈", layout="wide")
    
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

    st.title("📈 Finance News Impact Simulator")
    st.write("This is your main application dashboard.")
    # ... Add your main app components here ...


# --- Main App Router ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    main_app_page()
else:
    login_page()
