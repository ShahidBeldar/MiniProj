import streamlit as st
import time

# --- User Database (Demo only) ---
USER_CREDENTIALS = {
    "admin": "1234",
    "user": "password",
    "guest": "guest123"
}

def login_page():
    # --- Simplified CSS ---
    st.markdown("""
        <style>
            /* 1. Hide standard Streamlit Chrome */
            [data-testid="stHeader"],
            [data-testid="stFooter"],
            [data-testid="stToolbar"],
            [data-testid="stStatusWidget"],
            #MainMenu {visibility: hidden;}
            
            /* 2. Center the app and add a light gray background */
            .stApp {
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: #f8f9fa; /* Light gray background for contrast */
            }

            /* 3. CONSTRAIN MAIN CONTAINER - This makes it uniform on all devices */
            .block-container {
                max-width: 350px;       /* Fixed narrow width for desktop & mobile */
                padding: 2.5rem 2rem;   /* Internal spacing */
                background: white;      /* White card background */
                border-radius: 12px;    /* Rounded corners */
                box-shadow: 0 4px 20px rgba(0,0,0,0.08); /* Subtle drop shadow */
            }

            /* 4. Simplify Inputs */
            .stTextInput > div > div > input {
                border: 1px solid #e0e0e0;
                padding: 10px 15px;
                border-radius: 8px;       /* More rounded inputs */
                font-size: 16px;          /* Better readability on mobile */
            }
            .stTextInput > div > div > input:focus {
                border-color: #dc3545;
                box-shadow: none;
            }

            /* 5. Simplify Button */
            .stButton > button {
                width: 100%;
                border-radius: 8px;
                height: 45px;
                background-color: #dc3545;
                border: none;
                font-weight: 600;
                margin-top: 15px; /* Space between password and button */
            }
            .stButton > button:hover {
                background-color: #c82333;
            }
            
            /* 6. Typography adjustments */
            h1 {
                text-align: center;
                font-size: 1.8rem !important;
                font-weight: 700 !important;
                color: #dc3545 !important; /* Red accent color for title */
                padding-bottom: 0px;
            }
            p {
                text-align: center;
                color: #666;
                margin-bottom: 30px !important; /* Space below subtitle */
            }
        </style>
    """, unsafe_allow_html=True)

    # --- Simplified Content ---
    # The CSS above forces this content into a centered 350px card
    
    st.title("Finance News")
    st.write("Sign in to continue")

    username = st.text_input("Username", placeholder="Enter username", label_visibility="collapsed")
    password = st.text_input("Password", placeholder="Enter password", type="password", label_visibility="collapsed")

    if st.button("Sign In", type="primary"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success("Success")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Invalid credentials")

# --- For testing independently ---
if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
    else:
        st.write(f"Welcome back, {st.session_state['username']}!")
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.rerun()
