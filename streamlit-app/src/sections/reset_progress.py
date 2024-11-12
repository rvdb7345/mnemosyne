import streamlit as st
import os

def show():
    st.header("Reset Progress")
    st.write("Select an exercise to reset your progress.")

    username = st.session_state.get('username')
    PROGRESS_DIR = "progress"
    user_progress_dir = os.path.join(PROGRESS_DIR, username)
    if not os.path.exists(user_progress_dir):
        st.info("No progress to reset.")
        return

    progress_files = [f for f in os.listdir(user_progress_dir) if f.endswith('.json')]
    if not progress_files:
        st.info("No progress to reset.")
        return

    selected_progress_file = st.selectbox("Select exercise to reset", progress_files)
    if st.button("Reset Progress"):
        progress_file_path = os.path.join(user_progress_dir, selected_progress_file)
        if os.path.exists(progress_file_path):
            os.remove(progress_file_path)
        st.session_state['progress'] = []
        st.session_state['current_index'] = 0
        st.session_state['mistakes'] = []
        st.session_state['feedback_message'] = None
        st.session_state['user_input'] = ''
        st.session_state['clear_input'] = False
        st.success("Progress has been reset.")
        st.rerun()
        
show()