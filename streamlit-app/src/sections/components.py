# src/sections/components.py

import streamlit as st

def render_flashcard(content):
    st.markdown(f'<div class="flashcard">{content}</div>', unsafe_allow_html=True)

def render_feedback(feedback_message):
    if feedback_message:
        msg_type, msg = feedback_message
        if msg_type == 'success':
            st.success(msg, icon="✅")
        else:
            st.error(msg, icon="❌")

def apply_custom_css():
    st.markdown("""
    <style>
    .flashcard {
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        border-radius: 10px;
        padding: 50px;
        text-align: center;
        font-size: 24px;
        margin: 20px 0;
        border: 1px solid var(--background-color);
    }
    </style>
    """, unsafe_allow_html=True)
