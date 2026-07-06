import streamlit as st
import os

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png")

NAVY = "#2E5C93"
BLUE = "#4E82BE"
GREEN = "#8DC63F"

CATEGORICAL = [NAVY, GREEN, BLUE, "#B7D98C", "#8FB2D9", "#1A3F66"]
SEQUENTIAL_BLUE = ["#DCE8F5", "#4E82BE", "#2E5C93"]
SEQUENTIAL_GREEN = ["#EAF5D6", "#8DC63F", "#5C8A21"]


def show_logo():
    if os.path.exists(LOGO_PATH):
        st.logo(LOGO_PATH, size="large")
