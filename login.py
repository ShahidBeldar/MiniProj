import streamlit as st
import time

--- Global Page Config (Must be the first Streamlit command) ---
st.set_page_config(
page_title="Finance News Simulator",
layout="wide", # Default to wide for the main dashboard
initial_sidebar_state="collapsed"
)

--- Simple user database ---
USER_CREDENTIALS = {
"admin": "1234",
"user": "password",
"guest": "guest123"
}

--- CSS Functions ---
def load_login_css():
st.markdown("""
<style>
/* Hide standard Streamlit elements */
[data-testid="stHeader"], [data-testid="stFooter"] { display: none; }

        /* App background image */
        .stApp {
            background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), 
                              url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=2070&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }

        /* Centering the login box specifically and making it SMALLER */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            max-width: 380px; /* Reduced from 420px */
            margin: 6rem auto; /* Increased top margin for better vertical centering */
        }

        /* Login container styling */
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            background-color: rgba(255, 255, 255, 0.95); /* Slightly transparent white */
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
            padding: 2rem 2rem;
            backdrop-filter: blur(8px); /* Frosted glass effect if supported */
            border: 1px solid rgba(255, 255, 255, 0.18);
        }

        /* Title and subtitle */
        .login-title {
            text-align: center;
            font-size: 1.6rem;
            font-weight: 700;
            color: #1a1a1a;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
            text-align: center;
            color: #555;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }

        /* CONSTANT Textbox Styling - forcing standard height and look */
        .stTextInput input {
            height: 45px !important;
            padding: 10px 15px !important;
            font-size: 1rem !important;
            border: 1px solid #ccc !important;
            border-radius: 8px !important;
            color: #333 !important;
            background-color: #fff !important;
        }
        .stTextInput input:focus {
            border-color: #d90429 !important;
            box-shadow: 0 0 0 2px rgba(217, 4, 41, 0.1) !important;
        }
        /* Hide the small labels above inputs for a cleaner look in login */
        div[data-testid="stTextInput"] label {
            display: none;
        }

        /* Red Login Button */
        div[data-testid="stButton"] > button {
            background-color: #d90429 !important;
            color: white !important;
            border: none !important;
            width: 100%;
            height: 45px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            border-radius: 8px !important;
            margin-top: 1rem !important;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #b20321 !important;
            box-shadow: 0 4px 12px rgba(217, 4, 41, 0.3);
        }
        div[data-testid="stButton"] > button:active {
             background-color: #900 !important;
        }
        
        /* Logo Placeholder Style */
        .login-logo {
            display: flex;
            justify-content: center;
            margin-bottom: 1rem;
        }
        .login-logo img {
            height: 60px;
        }
    </style>
""", unsafe_allow_html=True)
def load_main_css():
# Reset background for main app to be clean
st.markdown("""
<style>
.stApp {
background-image: none;
background-color: #f7f9fc;
}
</style>
""", unsafe_allow_html=True)

--- Page Functions ---
def login_page():
load_login_css()

# Use columns to help center horizontally if the CSS margin auto misses
_, col2, _ = st.columns([1, 2, 1])

with st.container(border=True):
    # Placeholder Logo (replace URL with your actual logo if you have one)
    st.markdown("""
        <div class="login-logo">
            <img src="https://cdn-icons-png.flaticon.com/512/781/781760.png" alt="Finance Logo">
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-title">Impact Simulator</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Sign in to continue</div>', unsafe_allow_html=True)

    username = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
    password = st.text_input("Password", placeholder="Password", type="password", label_visibility="collapsed")

    if st.button("LOGIN"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success("Authentication successful")
            time.sleep(0.8)
            st.rerun()
        else:
            st.error("Invalid username or password")
def main_app_page():
load_main_css()

# Sidebar for navigation/logout
with st.sidebar:
    st.title(f"Welcome, {st.session_state['username']}")
    st.divider()
    st.write("Navigation")
    page = st.radio("Go to", ["Dashboard", "News Input", "Simulation History"])
    st.divider()
    if st.button("Logout", type="primary"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

# Main Content Area
st.title("Finance News Impact Simulator")

if page == "Dashboard":
    st.subheader("Market Overview")
    st.info("Integration with Level 1 DFD Process 5.0 (Display Results) will go here.")
    # Placeholder for charts/graphs
    st.bar_chart({"Metric A": [10, 20, 30, 40], "Metric B": [15, 10, 25, 30]})

elif page == "News Input":
    st.subheader("Analyze New Scenario")
    st.write("Enter financial news to simulate its market impact.")
    news_input = st.text_area("Paste News Text or URL", height=150)
    if st.button("Run Simulation (DistilBERT)"):
        st.write("Running Process 2.0 (Preprocessing) -> 3.0 (Sentiment Analysis)...")
        # This is where you will call your DistilBERT model

elif page == "Simulation History":
    st.subheader("Past Simulations")
    st.write("Review previous impact analysis reports.")
--- App Router ---
if "logged_in" not in st.session_state:
st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
main_app_page()
else:
login_page()