import streamlit as st


def configure_page(page_title: str, page_icon: str = ":package:") -> None:
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide")


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.4rem;
                padding-bottom: 2rem;
                max-width: 1380px;
            }

            .brand-title {
                font-size: 1.15rem;
                font-weight: 700;
                margin-bottom: 0.2rem;
            }
            .brand-subtitle {
                color: #a9b2bf;
                font-size: 0.84rem;
                margin-bottom: 0.8rem;
            }

            .page-header {
                padding: 0.9rem 1rem;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
                margin-bottom: 0.9rem;
            }
            .page-title {
                font-size: 1.6rem;
                font-weight: 700;
                margin-bottom: 0.15rem;
                letter-spacing: 0.01em;
            }
            .page-subtitle {
                color: #adb6c3;
                font-size: 0.95rem;
            }

            .kpi-card {
                border: 1px solid rgba(255,255,255,0.09);
                border-radius: 12px;
                padding: 0.85rem 0.95rem;
                background: rgba(255,255,255,0.015);
                min-height: 102px;
            }
            .kpi-label {
                color: #a9b2bf;
                font-size: 0.82rem;
                margin-bottom: 0.35rem;
            }
            .kpi-value {
                font-size: 1.6rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
            }
            .kpi-help {
                color: #91a4b6;
                font-size: 0.78rem;
            }

            .status-pill {
                display: inline-block;
                padding: 0.2rem 0.55rem;
                border-radius: 999px;
                font-size: 0.74rem;
                font-weight: 700;
                letter-spacing: 0.01em;
            }
            .status-ok { background: rgba(55, 186, 112, 0.16); color: #86e3ae; border: 1px solid rgba(55,186,112,0.35); }
            .status-low { background: rgba(245, 166, 35, 0.16); color: #ffd089; border: 1px solid rgba(245,166,35,0.35); }
            .status-out { background: rgba(227, 93, 91, 0.17); color: #ff9b9a; border: 1px solid rgba(227,93,91,0.35); }
            .status-info { background: rgba(112, 166, 255, 0.16); color: #b5d0ff; border: 1px solid rgba(112,166,255,0.35); }

            .panel {
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                padding: 0.8rem 0.9rem;
                background: rgba(255,255,255,0.015);
            }
            .panel-title {
                font-weight: 650;
                margin-bottom: 0.55rem;
            }

            div[data-testid="stButton"] > button {
                border-radius: 9px;
                border: 1px solid rgba(255,255,255,0.15);
            }
            div[data-testid="stTextInput"] input:focus,
            div[data-testid="stNumberInput"] input:focus {
                border-color: #e35d5b !important;
                box-shadow: 0 0 0 1px #e35d5b;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
