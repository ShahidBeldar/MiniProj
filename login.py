import streamlit as st
import time

# --- User Database (Demo only - use proper auth in production) ---
USER_CREDENTIALS = {
    "admin": "1234",
    "user": "password",
    "guest": "guest123"
}

# --- Login Page Function ---
def login_page():
    """
    Renders the login page with authentication
    This function can be imported and called from app.py
    """
    
    # --- Minimal Login Page Styling ---
    st.markdown("""
        <style>
            /* Hide default Streamlit elements */
            [data-testid="stHeader"], 
            [data-testid="stFooter"], 
            #MainMenu,
            [data-testid="stToolbar"],
            [data-testid="stDecoration"],
            [data-testid="stStatusWidget"] {
                display: none !important;
            }
            
            /* Clean white background */
            .stApp {
                background: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
            }
            
            /* Main container */
            section[data-testid="stMain"] {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem;
            }
            
            /* Center the entire block */
            .block-container {
                display: flex;
                align-items: center;
                justify-content: center;
                max-width: 100% !important;
                padding: 0 !important;
            }
            
            /* Login card container - Fixed rectangular size */
            .login-card {
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                box-shadow: 0 2px 20px rgba(0, 0, 0, 0.08);
                width: 400px;
                min-height: 520px;
                overflow: hidden;
                position: relative;
            }
            
            /* Header section - minimal red accent */
            .login-header {
                background: #dc3545;
                height: 120px;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
            }
            
            .login-header-content {
                text-align: center;
                color: white;
                padding: 1rem;
            }
            
            .app-title {
                font-size: 1.5rem;
                font-weight: 600;
                margin: 0;
                letter-spacing: 0.3px;
            }
            
            .app-subtitle {
                font-size: 0.88rem;
                margin-top: 0.4rem;
                opacity: 0.95;
                font-weight: 300;
            }
            
            /* Form section */
            .login-body {
                padding: 2.5rem 2rem 2rem 2rem;
            }
            
            .welcome-text {
                text-align: center;
                margin-bottom: 1.8rem;
            }
            
            .welcome-title {
                font-size: 1.3rem;
                color: #333;
                font-weight: 600;
                margin-bottom: 0.3rem;
            }
            
            .welcome-subtitle {
                font-size: 0.88rem;
                color: #666;
                font-weight: 400;
            }
            
            /* Input field styling */
            .stTextInput > div > div > input {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 0.75rem 1rem;
                font-size: 0.95rem;
                transition: all 0.2s ease;
                background: #ffffff;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: #dc3545;
                box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.1);
                outline: none;
            }
            
            .stTextInput > div > div > input::placeholder {
                color: #aaa;
            }
            
            /* Button styling - Red primary button */
            .stButton > button[kind="primary"] {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 0.75rem 1.5rem;
                font-size: 0.95rem;
                font-weight: 500;
                width: 100%;
                transition: all 0.2s ease;
                margin-top: 0.5rem;
            }
            
            .stButton > button[kind="primary"]:hover {
                background: #c82333;
                box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
            }
            
            .stButton > button[kind="primary"]:active {
                background: #bd2130;
            }
            
            /* Alert boxes - minimal */
            .stAlert {
                border-radius: 4px;
                margin-top: 1rem;
                border: none;
                font-size: 0.88rem;
            }
            
            /* Success message */
            .stSuccess {
                background: #d4edda;
                color: #155724;
                border-left: 3px solid #28a745;
            }
            
            /* Error message */
            .stError {
                background: #f8d7da;
                color: #721c24;
                border-left: 3px solid #dc3545;
            }
            
            /* Bottom accent line */
            .login-footer {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: #dc3545;
            }
            
            /* Spacing adjustments */
            .stTextInput {
                margin-bottom: 0.8rem;
            }
            
            /* Label styling */
            .stTextInput > label {
                font-size: 0.88rem;
                color: #555;
                font-weight: 500;
                margin-bottom: 0.3rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- Login Card HTML Structure ---
    st.markdown("""
        <div class="login-card">
            <div class="login-header">
                <div class="login-header-content">
                    <h1 class="app-title">Finance News Impact</h1>
                    <p class="app-subtitle">Market Analysis Platform</p>
                </div>
            </div>
            <div class="login-body">
                <div class="welcome-text">
                    <h2 class="welcome-title">Sign In</h2>
                    <p class="welcome-subtitle">Enter your credentials to continue</p>
                </div>
            </div>
            <div class="login-footer"></div>
        </div>
    """, unsafe_allow_html=True)

    # --- Form Inputs ---
    username = st.text_input(
        "Username",
        placeholder="Username",
        key="username_input"
    )

    password = st.text_input(
        "Password",
        placeholder="Password",
        type="password",
        key="password_input"
    )

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