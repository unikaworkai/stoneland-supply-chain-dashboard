import streamlit as st

CSS = """
<style>
[data-testid="stMetric"] {
    background: #F7F9FC;
    border-left: 4px solid #2E5C93;
    border-radius: 8px;
    padding: 14px 16px 10px 16px;
}
[data-testid="stMetricLabel"] {
    font-weight: 600;
    color: #4E82BE;
}[data-testid="stMetricValue"] {
       color: #1A1A1A !important;
   }
   [data-testid="stMetricDelta"] {
       color: #1A1A1A !important;
   }
.stoneland-banner {
    background: linear-gradient(90deg, #2E5C93 0%, #4E82BE 55%, #8DC63F 100%);
    padding: 28px 32px;
    border-radius: 12px;
    color: white;
    margin-bottom: 22px;
}
.stoneland-banner h1 {
    color: white;
    margin: 0 0 6px 0;
    font-size: 32px;
}
.stoneland-banner p {
    color: #EAF2FB;
    margin: 0;
    font-size: 15px;
}
.section-header {
    border-left: 5px solid #8DC63F;
    padding-left: 10px;
    margin: 6px 0 14px 0;
}
.section-header h3 {
    margin: 0;
}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def banner(title: str, subtitle: str):
    st.markdown(f"""
    <div class="stoneland-banner">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def section(title: str, icon: str = ""):
    st.markdown(f'<div class="section-header"><h3>{icon} {title}</h3></div>', unsafe_allow_html=True)
