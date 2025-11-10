import streamlit as st
import time

# --- User Database (Demo only - use proper auth in production) ---
USER_CREDENTIALS = {
    "admin": "1234",
    "user": "password",
    "guest": "guest123"
}

# --- Page Configuration ---
st.set_page_config(
    page_title="Login | Finance News Simulator",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Login Page Styling ---
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
        
        /* Full page background with gradient and pattern */
        .stApp {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
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
        
        /* Login card container - Fixed rectangular size (portrait orientation) */
        .login-card {
            background: rgba(255, 255, 255, 0.98);
            border-radius: 20px;
            box-shadow: 0 25px 70px rgba(0, 0, 0, 0.5);
            width: 420px;
            min-height: 650px;
            overflow: hidden;
            position: relative;
            backdrop-filter: blur(10px);
        }
        
        /* Header section with finance image */
        .login-header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            height: 220px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }
        
        /* Stock market pattern overlay */
        .login-header::before {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            background-image: url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80');
            background-size: cover;
            background-position: center;
            opacity: 0.25;
        }
        
        /* Animated grid overlay */
        .login-header::after {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: grid-move 20s linear infinite;
        }
        
        @keyframes grid-move {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }
        
        .login-header-content {
            position: relative;
            z-index: 2;
            text-align: center;
            color: white;
            padding: 1.5rem;
        }
        
        .logo-icon {
            font-size: 4rem;
            margin-bottom: 0.8rem;
            filter: drop-shadow(0 6px 10px rgba(0, 0, 0, 0.4));
            animation: float 3s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .app-title {
            font-size: 1.65rem;
            font-weight: 700;
            margin: 0;
            text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.4);
            letter-spacing: 0.5px;
        }
        
        .app-subtitle {
            font-size: 0.92rem;
            margin-top: 0.5rem;
            opacity: 0.95;
            font-weight: 300;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        /* Form section */
        .login-body {
            padding: 2.8rem 2.5rem 2.5rem 2.5rem;
        }
        
        .welcome-text {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .welcome-title {
            font-size: 1.5rem;
            color: #1a1a1a;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }
        
        .welcome-subtitle {
            font-size: 0.92rem;
            color: #666;
            font-weight: 400;
        }
        
        /* Input field styling */
        .stTextInput > div > div > input {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 0.85rem 1.2rem;
            font-size: 0.98rem;
            transition: all 0.3s ease;
            background: #fafafa;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #2a5298;
            box-shadow: 0 0 0 4px rgba(42, 82, 152, 0.12);
            background: white;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #999;
        }
        
        /* Add icons to input fields */
        .stTextInput:first-of-type > div > div > input {
            padding-left: 2.8rem;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'%3E%3C/path%3E%3Ccircle cx='12' cy='7' r='4'%3E%3C/circle%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: 1rem center;
            background-size: 20px;
        }
        
        .stTextInput:last-of-type > div > div > input {
            padding-left: 2.8rem;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'%3E%3C/rect%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'%3E%3C/path%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: 1rem center;
            background-size: 20px;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.85rem 1.5rem;
            font-size: 1.05rem;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
            margin-top: 0.8rem;
            box-shadow: 0 4px 15px rgba(30, 60, 114, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(30, 60, 114, 0.5);
        }
        
        .stButton > button:active {
            transform: translateY(0px);
        }
        
        /* Demo credentials button */
        .demo-btn button {
            background: white !important;
            color: #2a5298 !important;
            border: 2px solid #2a5298 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
        }
        
        .demo-btn button:hover {
            background: #f8f9fc !important;
            border-color: #1e3c72 !important;
            color: #1e3c72 !important;
        }
        
        /* Alert boxes */
        .stAlert {
            border-radius: 10px;
            margin-top: 1rem;
            border: none;
            font-size: 0.9rem;
        }
        
        /* Success message */
        .stSuccess {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }
        
        /* Error message */
        .stError {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
            color: white;
        }
        
        /* Info box styling */
        [data-testid="stNotification"] {
            background: white;
            border-left: 4px solid #2a5298;
        }
        
        /* Decorative footer line */
        .login-footer {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 50%, #1e3c72 100%);
            background-size: 200% 100%;
            animation: gradient-shift 3s ease infinite;
        }
        
        @keyframes gradient-shift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        /* Hide extra spacing */
        .element-container {
            margin: 0 !important;
        }
        
        /* Spacing adjustments */
        .stTextInput {
            margin-bottom: 0.8rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Login Card HTML Structure ---
st.markdown("""
    <div class="login-card">
        <div class="login-header">
            <div class="login-header-content">
                <div class="logo-icon">📊</div>
                <h1 class="app-title">Finance News Impact</h1>
                <p class="app-subtitle">Real-time Market Analysis Platform</p>
            </div>
        </div>
        <div class="login-body">
            <div class="welcome-text">
                <h2 class="welcome-title">Welcome Back</h2>
                <p class="welcome-subtitle">Sign in to access your dashboard</p>
            </div>
        </div>
        <div class="login-footer"></div>
    </div>
""", unsafe_allow_html=True)

# --- Form Inputs ---
username = st.text_input(
    "Username",
    placeholder="Enter your username",
    label_visibility="collapsed",
    key="username_input"
)

password = st.text_input(
    "Password",
    placeholder="Enter your password",
    type="password",
    label_visibility="collapsed",
    key="password_input"
)

# --- Login Button ---
login_btn = st.button("Sign In", use_container_width=True, type="primary")

# --- Demo Credentials Button ---
st.markdown('<div class="demo-btn">', unsafe_allow_html=True)
demo_btn = st.button("View Demo Credentials", use_container_width=True, key="demo")
st.markdown('</div>', unsafe_allow_html=True)

if demo_btn:
    st.info("**Demo Access Credentials:**\n\n• Username: admin | Password: 1234\n\n• Username: user | Password: password\n\n• Username: guest | Password: guest123")

# --- Login Logic ---
if login_btn:
    if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.success("Login successful! Redirecting to dashboard...")
        time.sleep(1.5)
        st.rerun()
    else:
        st.error("Invalid credentials. Please check your username and password.")

# --- Additional Info ---
if not login_btn and not demo_btn:
    st.markdown("""
        <div style='text-align: center; margin-top: 1.5rem; color: #999; font-size: 0.85rem;'>
            Secure access to financial market simulation tools
        </div>
    """, unsafe_allow_html=True)