import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import os
import pandas as pd
from utils.helpers import create_dir  # Ensure this module exists and has necessary functions



# Initialize base directories
EXERCISES_DIR = 'exercises'
PROGRESS_DIR = 'progress'
create_dir(EXERCISES_DIR)
create_dir(PROGRESS_DIR)

# Load configuration
# with open('config.yaml') as file:
#     config = yaml.load(file, Loader=SafeLoader)


st.set_page_config(page_title="Language Learning App", layout="wide")

# Load the config
def load_config():
    with open('config.yaml') as file:
        return yaml.load(file, Loader=SafeLoader)

# Helper to determine if password is alredy hashed
def is_bcrypt_hash(s):
    return s.startswith(('$2a$', '$2b$', '$2x$', '$2y$')) and len(s) == 60


# Hash new plaintext passwords only
def hash_plaintext_passwords(config):
    plaintext_passwords = {}
    for user, details in config['credentials']['usernames'].items():
        # Check if the password is not a bcrypt hash
        if not is_bcrypt_hash(details['password']):
            plaintext_passwords[user] = details['password']

    if plaintext_passwords:
        hashed_passwords = stauth.Hasher(list(plaintext_passwords.values())).generate()
        for user, hashed_pw in zip(plaintext_passwords.keys(), hashed_passwords):
            config['credentials']['usernames'][user]['password'] = hashed_pw

    return config


# Save the config
def save_config(config):
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

config = load_config()

if 'hashed_done' not in st.session_state:
    config = hash_plaintext_passwords(config)
    save_config(config)
    st.session_state.hashed_done = True

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

def main():

    if st.session_state["authentication_status"]:
        # Define pages
        st.sidebar.title(f"Welcome, {st.session_state['name']}!")
        st.sidebar.markdown("---")

        # Logout button
        authenticator.logout('Logout', 'sidebar')

        # Optional: Update user details
        with st.sidebar.expander("Update Details"):
            if authenticator.update_user_details(st.session_state["username"], 'main'):
                st.sidebar.success('Details updated successfully')
                # Save updated config
                with open('config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)

        # Optional: Reset password
        with st.sidebar.expander("Reset Password"):
            try:
                if authenticator.reset_password(st.session_state["username"], 'main'):
                    st.sidebar.success('Password modified successfully')
                    # Save updated config
                    with open('config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
            except Exception as e:
                st.sidebar.error(e)
        
        pages = [
        st.Page("sections/practice.py", title="Practice"),
        st.Page("sections/review_mistakes.py", title="Review Mistakes"),
        st.Page("sections/reset_progress.py", title="Reset Progress"),
        st.Page("sections/upload_exercise.py", title="Upload Exercise"),
        ]

        # Use st.navigation
        page = st.navigation(pages)
        
        # Run the selected page
        page.run()

    elif st.session_state["authentication_status"] == False:
        # Main app content
        st.title("Vocabulary Practice App")

        
        st.error('Username/password is incorrect')
        # Render the login widget
        authenticator.login('main')

    elif st.session_state["authentication_status"] is None:
        # Main app content
        st.title("Vocabulary Practice App")
        
        # Render the login widget
        authenticator.login('main')
    
        st.warning('Please enter your username and password')
                # Define pages
        pages = [
                st.Page("main.py", title="Login"),
            ]
        
        # Use st.navigation
        page = st.navigation(pages)

        # Registration
        with st.expander('Register'):
            if authenticator.register_user('main', clear_on_submit=True):
                save_config(config)

        # Optional: Forgot Password
        with st.sidebar.expander("Forgot Password"):
            try:
                username_forgot, email_forgot, new_password = authenticator.forgot_password('main')
                if username_forgot:
                    st.sidebar.success('New password generated and sent securely')

                    with open('config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
                elif username_forgot == False:
                    st.sidebar.error('Username not found')
            except Exception as e:
                st.sidebar.error(e)

if __name__ == "__main__":
    main()
