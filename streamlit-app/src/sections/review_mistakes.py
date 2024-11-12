import streamlit as st
import json
import pandas as pd
import os


def show():
    username = st.session_state.get('username')
    PROGRESS_DIR = "progress"

    st.header("Review Your Answers")

    # Load progress data
    user_progress_dir = os.path.join(PROGRESS_DIR, username)

    # Get all progress files for the user
    progress_files = [f for f in os.listdir(user_progress_dir) if f.endswith('.json')]
    if not progress_files:
        st.info("No answers to review yet. Start practicing!")
    else:
        # Select which progress file to review
        selected_progress_file = st.selectbox("Select exercise to review", progress_files)
        with open(os.path.join(user_progress_dir, selected_progress_file), 'r') as f:
            progress_data = json.load(f)

        # Filter options
        filter_option = st.selectbox("Filter by:", ["All", "Correct", "Incorrect"])

        # Prepare data for display
        progress_df = pd.DataFrame(progress_data)
        if filter_option == "Correct":
            progress_df = progress_df[progress_df['correct'] == True]
        elif filter_option == "Incorrect":
            progress_df = progress_df[progress_df['correct'] == False]

        if not progress_df.empty:
            st.dataframe(progress_df[['timestamp', 'question', 'your_answer', 'correct_answer', 'correct']].sort_values(by='timestamp', ascending=False))
        else:
            st.info("No records match the selected filter.")

        # Option to reset progress with confirmation
        if st.button("Reset Progress for this Exercise"):
            reset_confirm = st.warning("Are you sure you want to reset progress for this exercise? This cannot be undone.")
            if st.button("Yes, Reset"):
                progress_file_path = os.path.join(user_progress_dir, selected_progress_file)
                if os.path.exists(progress_file_path):
                    os.remove(progress_file_path)
                st.success("Progress has been reset.")
                st.rerun()
            if st.button("Cancel"):
                st.session_state['reset_confirmation'] = False
                
                
show()