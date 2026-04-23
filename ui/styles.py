import streamlit as st


def configure_page(page_title: str, page_icon: str = ":package:") -> None:
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide")


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --nu-purple-950: #140d1f;
                --nu-purple-900: #221330;
                --nu-purple-800: #37185b;
                --nu-purple-650: #5c3690;
                --nu-lavender: #b798ff;
                --nu-peach: #ff9b68;
                --nu-text: #f6f2ff;
                --nu-muted: #b8adc9;
                --nu-card: rgba(255,255,255,0.032);
                --nu-border: rgba(255,255,255,0.115);
            }

            /* Streamlit 1.4x: main content is [data-testid="stMainBlockContainer"] + .block-container.
               Use high-specificity selectors so this wins over Emotion after reruns. */
            section[data-testid="stMain"] {
                background:
                    radial-gradient(circle at 88% 0%, rgba(92, 54, 144, 0.22), transparent 30rem),
                    linear-gradient(180deg, #101216 0%, #111018 52%, #0f1117 100%);
            }
            section[data-testid="stMain"] [data-testid="stMainBlockContainer"] {
                padding-top: 4.5rem !important;
                padding-bottom: 2rem !important;
            }
            section[data-testid="stMain"] [data-testid="stMainBlockContainer"].block-container {
                padding-top: 4.5rem !important;
            }
            .block-container {
                padding-top: 4.5rem !important;
                padding-bottom: 2rem !important;
                max-width: 1380px;
            }
            section[data-testid="stSidebar"] {
                background:
                    radial-gradient(circle at 80% 0%, rgba(255, 155, 104, 0.16), transparent 14rem),
                    linear-gradient(180deg, #1a1026 0%, #111018 100%);
                border-right: 1px solid rgba(255,255,255,0.08);
            }
            div[data-testid="stVerticalBlockBorderWrapper"] {
                border-color: var(--nu-border) !important;
                border-radius: 12px !important;
                background:
                    linear-gradient(180deg, rgba(255,255,255,0.032), rgba(255,255,255,0.015)) !important;
                box-shadow: 0 10px 28px rgba(0,0,0,0.11);
            }

            /* Aligns action buttons with the title line inside .page-header (same top padding). */
            .page-header-actions-offset {
                display: block;
                height: 0;
                padding-top: 0.9rem;
                margin: 0;
            }

            .brand-title {
                font-size: 1.15rem;
                font-weight: 800;
                margin-bottom: 0.2rem;
                color: var(--nu-text);
                letter-spacing: 0.01em;
            }
            .brand-subtitle {
                color: var(--nu-muted);
                font-size: 0.84rem;
                margin-bottom: 0.8rem;
            }

            .page-header {
                position: relative;
                overflow: hidden;
                padding: 1rem 1.1rem;
                border: 1px solid var(--nu-border);
                border-radius: 12px;
                background:
                    radial-gradient(circle at 88% 0%, rgba(255, 155, 104, 0.18), transparent 18rem),
                    linear-gradient(118deg, rgba(55, 24, 91, 0.86), rgba(34, 19, 48, 0.94));
                margin-bottom: 1rem;
                box-shadow: 0 14px 34px rgba(0,0,0,0.18);
            }
            .page-header::after {
                content: "";
                position: absolute;
                top: 0;
                right: 1rem;
                width: 44px;
                height: 54px;
                background: var(--nu-peach);
                clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 84%, 0 100%);
                opacity: 0.92;
            }
            .page-title {
                position: relative;
                z-index: 1;
                color: var(--nu-text);
                font-size: 1.55rem;
                font-weight: 800;
                margin-bottom: 0.15rem;
            }
            .page-subtitle {
                position: relative;
                z-index: 1;
                color: rgba(255,255,255,0.78);
                font-size: 0.95rem;
            }

            .kpi-card {
                border: 1px solid var(--nu-border);
                border-radius: 12px;
                padding: 0.85rem 0.95rem;
                background:
                    linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.018));
                min-height: 102px;
                box-shadow: 0 10px 28px rgba(0,0,0,0.12);
            }
            .kpi-label {
                color: var(--nu-muted);
                font-size: 0.82rem;
                margin-bottom: 0.35rem;
            }
            .kpi-value {
                color: var(--nu-text);
                font-size: 1.6rem;
                font-weight: 800;
                margin-bottom: 0.25rem;
            }
            .kpi-help {
                color: rgba(184, 173, 201, 0.82);
                font-size: 0.78rem;
            }

            .home-hero {
                position: relative;
                overflow: hidden;
                min-height: 210px;
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 14px;
                padding: 1.35rem 1.45rem;
                margin-bottom: 1rem;
                background:
                    radial-gradient(circle at 82% 22%, rgba(255, 155, 104, 0.22), transparent 22rem),
                    linear-gradient(118deg, rgba(55, 24, 91, 0.98) 0%, rgba(92, 54, 144, 0.96) 46%, rgba(189, 176, 231, 0.78) 100%);
                box-shadow: 0 18px 46px rgba(0,0,0,0.24);
            }
            .home-hero::before {
                content: "";
                position: absolute;
                inset: auto -8% -42% 28%;
                height: 170px;
                background:
                    linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent),
                    repeating-linear-gradient(90deg, rgba(255,255,255,0.16) 0 1px, transparent 1px 72px);
                transform: rotate(-4deg);
                opacity: 0.5;
            }
            .home-hero::after {
                content: "";
                position: absolute;
                right: 1.3rem;
                top: 1.2rem;
                width: 76px;
                height: 88px;
                background: #ff9b68;
                clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 84%, 0 100%);
                opacity: 0.95;
            }
            .home-hero-mark {
                position: relative;
                z-index: 1;
                color: rgba(255,255,255,0.88);
                font-size: 0.86rem;
                font-weight: 800;
                letter-spacing: 0.18em;
                text-transform: uppercase;
            }
            .home-hero-content {
                position: relative;
                z-index: 1;
                max-width: 760px;
                margin-top: 2.25rem;
            }
            .home-hero-title {
                color: #ffffff;
                font-size: 2.7rem;
                font-weight: 850;
                line-height: 1.04;
                margin-bottom: 0.5rem;
                text-shadow: 0 2px 16px rgba(0,0,0,0.22);
            }
            .home-hero-subtitle {
                color: rgba(255,255,255,0.86);
                font-size: 1.06rem;
                line-height: 1.45;
                max-width: 620px;
            }
            .home-hero-accent {
                position: absolute;
                z-index: 1;
                right: 1.45rem;
                bottom: 1.25rem;
                color: #23113a;
                background: #ff9b68;
                border: 1px solid rgba(255,255,255,0.22);
                border-radius: 7px;
                padding: 0.58rem 0.75rem;
                font-size: 0.76rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }
            .home-panel-heading {
                margin-bottom: 0.75rem;
            }
            .home-panel-title {
                color: #f6f2ff;
                font-size: 1.05rem;
                font-weight: 750;
                line-height: 1.25;
                margin-bottom: 0.15rem;
            }
            .home-panel-subtitle {
                color: #a9b2bf;
                font-size: 0.82rem;
                line-height: 1.35;
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
                border: 1px solid var(--nu-border);
                border-radius: 12px;
                padding: 0.8rem 0.9rem;
                background: var(--nu-card);
            }
            .panel-title {
                color: var(--nu-text);
                font-weight: 650;
                margin-bottom: 0.55rem;
            }

            .analytics-filter-label {
                color: #a9b2bf;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.02em;
                margin: 0.3rem 0 0.25rem;
                text-transform: uppercase;
            }
            .analytics-filter-note {
                color: #91a4b6;
                font-size: 0.86rem;
                padding-bottom: 0.45rem;
            }
            .analytics-panel-heading {
                margin-bottom: 0.75rem;
            }
            .analytics-panel-title {
                color: #f4f7fb;
                font-size: 1.02rem;
                font-weight: 700;
                line-height: 1.25;
                margin-bottom: 0.15rem;
            }
            .analytics-panel-subtitle {
                color: #91a4b6;
                font-size: 0.82rem;
                line-height: 1.35;
            }
            .analytics-empty-state {
                min-height: 260px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                border: 1px dashed rgba(255,255,255,0.14);
                border-radius: 8px;
                background: rgba(255,255,255,0.015);
                padding: 1rem;
            }
            .analytics-empty-title {
                color: #dfe6ee;
                font-weight: 700;
                margin-bottom: 0.25rem;
            }
            .analytics-empty-copy {
                color: #91a4b6;
                font-size: 0.86rem;
                max-width: 28rem;
            }

            div[data-testid="stButton"] > button {
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,0.15);
            }
            div[data-testid="stButton"] > button[kind="primary"],
            div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
                background: var(--nu-peach);
                border-color: rgba(255,255,255,0.18);
                color: #241036;
                font-weight: 800;
            }
            div[data-testid="stTextInput"] input:focus,
            div[data-testid="stNumberInput"] input:focus,
            div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
                border-color: var(--nu-peach) !important;
                box-shadow: 0 0 0 1px var(--nu-peach);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
