import streamlit as st
import time

# --- Simple user database (for demo) ---
USER_CREDENTIALS = {
    "admin": "1234",
    "user": "password",
    "guest": "guest123"
}

# --- Login Page Function ---
def login_page():
    st.set_page_config(
        page_title="Login | Finance News Simulator",
        page_icon="💼",
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
                padding: 2.5rem 2rem; /* More spacious padding */
            }
            
            /* Constrain the width of the login box */
            .stApp > div[data-testid="stVerticalBlock"] {
                max-width: 450px;
                margin: auto;
            }

            /* --- Custom Title Styles --- */
            .login-title {
                text-align: center;
                font-size: 2rem;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 0.5rem;
            }
            
            .login-subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 2rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- Login Box Layout ---
    with st.container(border=True):
        st.markdown('<div class="login-title">💼 Welcome Back</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Login to the Finance News Simulator</div>', unsafe_allow_html=True)

        username = st.text_input(
            "Username",
            placeholder="Username (e.g., admin)",
            label_visibility="collapsed" # Hides the label, uses placeholder
        )
        password = st.text_input(
            "Password",
            placeholder="Password (e.g., 1234)",
            type="password",
            label_visibility="collapsed" # Hides the label
        )

        st.write("") # Add a little space
        
        login_btn = st.button("Login", use_container_width=True, type="primary")

        if login_btn:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Welcome, {username}! Redirecting...")
                time.sleep(1) # Short delay
                st.rerun() # Use st.rerun() (preferred over experimental_rerun)
            else:
                st.error("Invalid username or password.")

    # --- Demo Credentials Info Box ---
    st.info(
        "**Demo Credentials:**\n\n"
        "| Username | Password |\n"
        "| :--- | :--- |\n"
        "| `admin` | `1234` |\n"
        "| `user` | `password` |\n"
        "| `guest` | `guest123` |",
        icon="🔑"
    )

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
    st.text_input("Enter a news headline to analyze:")
    # ... Add your main app components here ...


# --- Main App Router ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    main_app_page()
else:
    login_page()
