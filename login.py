import streamlit as st
import time

# --- User Database (Demo only) ---
USER_CREDENTIALS = {
    "admin": "1234",
    "user": "password",
    "guest": "guest123"
}

# --- Login Page Function ---
def login_page():
    """
    Renders a minimalist, professional, and responsive login page.
    """
    
    # --- Minimalist Styling ---
    # This CSS is minimal:
    # 1. Hides the default Streamlit "chrome" (header, footer, etc.)
    # 2. Ensures the login form is vertically centered.
    st.markdown("""
        <style>
            /* Hide Streamlit default elements */
            [data-testid="stHeader"],
            [data-testid="stFooter"],
            #MainMenu,
            [data-testid="stToolbar"],
            [data-testid="stStatusWidget"] {
                display: none !important;
                visibility: hidden !important;
            }
            
            /* Center the main content vertically */
            .stApp {
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                background-color: #FFFFFF; /* Clean white background */
            }
            
            /* Style inputs */
            .stTextInput > div > div > input {
                border-radius: 6px;
                border: 1px solid #e0e0e0;
                padding: 0.75rem 1rem;
                font-size: 0.95rem;
            }
            
            /* Style button */
            .stButton > button {
                border-radius: 6px;
                height: 45px;
                font-weight: 500;
                background-color: #dc3545;
                border: none;
            }
            
            /* Center-align title and subtitle */
            .login-title {
                text-align: center;
                color: #222;
                font-weight: 600;
                font-size: 1.8rem;
                margin-bottom: 0.5rem;
            }
            
            .login-subtitle {
                text-align: center;
                color: #555;
                font-size: 0.95rem;
                margin-bottom: 2rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- Layout: Solves the Width Problem ---
    # We create 3 columns: [gutter_left, main_content, gutter_right]
    # This makes the main_content column (col2) narrow on desktop
    # and full-width on mobile (as columns stack).
    
    col1, col2, col3 = st.columns([1, 1.5, 1])

    # All content goes into the central column (col2)
    with col2:
        
        # --- Header ---
        # Using markdown for centered text
        st.markdown('<h1 class="login-title">Finance Impact</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Sign in to your account</p>', unsafe_allow_html=True)

        # --- Form Inputs ---
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
        
        st.write("") # Small spacer
        
        # --- Login Button ---
        login_btn = st.button("Sign In", use_container_width=True, type="primary")

        # --- Login Logic ---
        if login_btn:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("Login successful! Redirecting...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username or password")


# --- Main App Logic (for testing) ---
if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
    else:
        # This is your main app page
        st.set_page_config(layout="wide") # Re-enable standard layout
        st.title("Welcome to the Main Application")
        st.write(f"You are logged in as: **{st.session_state['username']}**")
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.rerun()
