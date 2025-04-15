import streamlit as st
import streamlit_authenticator as stauth

def get_authenticator():
    # Check if authentication is disabled via environment variable
    if st.secrets.get("DISABLE_AUTHENTICATION", False):
        st.session_state['authentication_status'] = True
        st.session_state['name'] = "Guest"
        st.session_state['username'] = "guest"
        return None  # Skip creating the authenticator

    # Extract credentials from secrets
    credentials = {
        'usernames': {
            'john': {
                'email': st.secrets["CREDENTIALS"]["USERNAMES"]["JOHN"]["EMAIL"],
                'name': st.secrets["CREDENTIALS"]["USERNAMES"]["JOHN"]["NAME"],
                'password': st.secrets["CREDENTIALS"]["USERNAMES"]["JOHN"]["PASSWORD"]
            },
            'james': {
                'email': st.secrets["CREDENTIALS"]["USERNAMES"]["JAMES"]["EMAIL"],
                'name': st.secrets["CREDENTIALS"]["USERNAMES"]["JAMES"]["NAME"],
                'password': st.secrets["CREDENTIALS"]["USERNAMES"]["JAMES"]["PASSWORD"]
            }
        }
    }

    # Extract cookie configuration from secrets
    cookie = {
        'key': st.secrets["COOKIE"]["KEY"],
        'name': st.secrets["COOKIE"]["NAME"],
        'expiry_days': st.secrets["COOKIE"]["EXPIRE_DAYS"]
    }

    # Initialize and return the authenticator
    return stauth.Authenticate(
        credentials=credentials,
        cookie_name=cookie["name"],
        key=cookie["key"],
        cookie_expiry_days=cookie["expiry_days"]
    )