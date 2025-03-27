import streamlit as st
from src.ui.app_config_functions import (
    authenticate_user, 
    get_img_as_base64
)

login_back = get_img_as_base64("static/background5.jpg")

def login():
    """Trigger login action"""
    st.session_state.login_clicked = True

def login_page():

    # Set up page config
    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{login_back}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    [data-testid="stHeader"], [data-testid="stToolbar"] {{
        background: rgba(0,0,0,0);
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)
        
    cols = st.columns(3)
    with cols[1]:
        st.markdown(
            """
            <style>
            .title-box {
                background: rgba(255, 255, 255, 0.7); /* Translucent white */
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            </style>
            <div class="title-box">
                <h1>Veloflow</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols2 = st.columns([4, 1])
        with cols2[0]:
            st.write("")
            email = st.text_input(
                label="email", 
                label_visibility = "collapsed", 
                placeholder="Enter your email",
                on_change=login
            )
        with cols2[1]:
            st.write("")
            login_button = st.button("Login")

        st.markdown(
            """
            <style>
            .note-box {
                background: rgba(255, 255, 255, 0.7); 
                padding: 5px;
                border-radius: 10px;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            </style>
            <div class="note-box">
                <h3>MVP - Version 1.0</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if login_button or st.session_state.login_clicked:
            user, company = authenticate_user(email)
            if user:
                st.session_state["user"] = user
                st.session_state["company"] = company
                st.session_state["logged_in"] = True  # Mark user as logged in
                st.info("Login successful!")
                st.rerun()
            else:
                st.error("Invalid email.")
                