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
              
            /* App background */  
            .stApp {  
                background-color: #f7f9fc;  
            }  
  
            /* Login container styling */  
            [data-testid="stVerticalBlockBorderWrapper"] > div {  
                background-color: white;  
                border: 1px solid #e0e0e0;  
                border-radius: 12px;  
                box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);  
                padding: 2.8rem 2.2rem;  
                transition: all 0.3s ease;  
            }  
  
            [data-testid="stVerticalBlockBorderWrapper"] > div:hover {  
                box-shadow: 0 10px 28px rgba(0, 0, 0, 0.12);  
            }  
  
            /* Center container */  
            .stApp > div[data-testid="stVerticalBlock"] {  
                max-width: 420px;  
                margin: auto;  
            }  
  
            /* Title and subtitle */  
            .login-title {  
                text-align: center;  
                font-size: 1.9rem;  
                font-weight: 700;  
                color: #222;  
                margin-bottom: 0.3rem;  
                letter-spacing: -0.5px;  
            }  
  
            .login-subtitle {  
                text-align: center;  
                color: #555;  
                font-size: 0.95rem;  
                margin-bottom: 2.2rem;  
            }  
  
            /* Red Login Button */  
            div[data-testid="stButton"] > button {  
                background-color: #d90429 !important;  
                color: white !important;  
                border: none !important;  
                font-weight: 600 !important;  
                border-radius: 8px !important;  
                height: 2.8rem !important;  
                transition: all 0.2s ease-in-out !important;  
            }  
  
            div[data-testid="stButton"] > button:hover {  
                background-color: #b20321 !important;  
                transform: scale(1.02);  
            }  
  
            /* Input box styling */  
            input {  
                border-radius: 6px !important;  
                border: 1px solid #ccc !important;  
                padding: 0.6rem 0.8rem !important;  
            }  
  
            input:focus {  
                border-color: #d90429 !important;  
                outline: none !important;  
                box-shadow: 0 0 0 2px rgba(217, 4, 41, 0.2) !important;  
            }  
        </style>  
    """, unsafe_allow_html=True)  
  
    # --- Login Box Layout ---  
    with st.container(border=True):  
        st.markdown('<div class="login-title">Finance News Impact Simulator</div>', unsafe_allow_html=True)  
        st.markdown('<div class="login-subtitle">Access your financial analysis dashboard</div>', unsafe_allow_html=True)  
  
        username = st.text_input("Username", placeholder="Enter username", label_visibility="collapsed")  
        password = st.text_input("Password", placeholder="Enter password", type="password", label_visibility="collapsed")  
          
        st.write("")  # spacing before button  
  
        login_btn = st.button("Login", use_container_width=True)  
  
        if login_btn:  
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:  
                st.session_state["logged_in"] = True  
                st.session_state["username"] = username  
                st.success("Login successful! Redirecting...")  
                time.sleep(1)  
                st.rerun()  
            else:  
                st.error("Invalid username or password.")  
  
# --- Main App Page Function (Placeholder) ---  
def main_app_page():  
    st.set_page_config(page_title="Simulator Dashboard", layout="wide")  
      
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")  
    if st.sidebar.button("Logout"):  
        st.session_state["logged_in"] = False  
        st.session_state["username"] = ""  
        st.rerun()  
  
    st.title("Finance News Impact Simulator")  
    st.write("This is your main application dashboard.")  
    # Add main components here  
  
  
# --- App Router ---  
if "logged_in" not in st.session_state:  
    st.session_state["logged_in"] = False  
  
if st.session_state["logged_in"]:  
    main_app_page()  
else:  
    login_page()