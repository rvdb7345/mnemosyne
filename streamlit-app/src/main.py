import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import os
import pandas as pd
from utils.helpers import create_dir 
from utils.file_paths import add_project_to_path, ProjectPaths

pp = ProjectPaths()
add_project_to_path(pp)

# Initialize base directories
EXERCISES_DIR = 'exercises'
PROGRESS_DIR = 'progress'
create_dir(EXERCISES_DIR)
create_dir(PROGRESS_DIR)

st.set_page_config(page_title="Language Learning App", layout="wide")

authenticator = stauth.Authenticate(
    st.secrets['credentials'].to_dict(),
    st.secrets['cookie']['name'],
    st.secrets['cookie']['key'],
    st.secrets['cookie']['expiry_days'],
    st.secrets['preauthorized']
)

def main():

    if st.session_state["authentication_status"]:
        # Define pages
        st.sidebar.title(f"Welcome, {st.session_state['name']}!")
        st.sidebar.markdown("---")

        # Logout button
        authenticator.logout('Logout', 'sidebar')

        # # Optional: Update user details
        # with st.sidebar.expander("Update Details"):
        #     if authenticator.update_user_details(st.session_state["username"], 'main'):
        #         st.sidebar.success('Details updated successfully')
        #         # Save updated config
        #         with open('config.yaml', 'w') as file:
        #             yaml.dump(config, file, default_flow_style=False)

        # # Optional: Reset password
        # with st.sidebar.expander("Reset Password"):
        #     try:
        #         if authenticator.reset_password(st.session_state["username"], 'main'):
        #             st.sidebar.success('Password modified successfully')
        #             # Save updated config
        #             with open('config.yaml', 'w') as file:
        #                 yaml.dump(config, file, default_flow_style=False)
        #     except Exception as e:
        #         st.sidebar.error(e)
        
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
        # with st.expander('Register'):
        #     if authenticator.register_user('main', clear_on_submit=True):
        #         save_config(config)

        # # Optional: Forgot Password
        # with st.sidebar.expander("Forgot Password"):
        #     try:
        #         username_forgot, email_forgot, new_password = authenticator.forgot_password('main')
        #         if username_forgot:
        #             st.sidebar.success('New password generated and sent securely')

        #             with open('config.yaml', 'w') as file:
        #                 yaml.dump(config, file, default_flow_style=False)
        #         elif username_forgot == False:
        #             st.sidebar.error('Username not found')
        #     except Exception as e:
        #         st.sidebar.error(e)

if __name__ == "__main__":
    main()
