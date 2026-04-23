"""Legacy shared theme helpers kept in the Niagara Pantry palette."""
import streamlit as st


_CSS = """
<style>
/* Background gradient (overrides flat dark from config.toml). */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #101216 0%, #1a1026 45%, #221330 100%) !important;
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent !important; }

/* Sidebar accent border. */
[data-testid="stSidebar"],
section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255, 155, 104, 0.22) !important;
}

/* Sidebar active nav link */
[data-testid="stSidebarNavLink"][aria-selected="true"] {
    background: rgba(255, 155, 104, 0.15) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(255, 155, 104, 0.08) !important;
    border-radius: 8px !important;
}

/* Content width. */
.block-container {
    max-width: 960px !important;
    margin: 0 auto !important;
    padding-top: 2rem !important;
}

/* Gradient headings. */
h1 {
    background: linear-gradient(90deg, #ffffff 0%, #b798ff 60%, #ff9b68 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}
h2, h3, h4 { font-weight: 700 !important; }

/* Buttons. */
[data-testid="stButton"] > button,
[data-testid="stFormSubmitButton"] > button {
    background: rgba(255, 155, 104, 0.12) !important;
    border: 1px solid rgba(255, 155, 104, 0.4) !important;
    border-radius: 8px !important;
    color: #ff9b68 !important;
    font-weight: 600 !important;
    transition: background 0.2s, color 0.2s, border-color 0.2s !important;
}
[data-testid="stButton"] > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background: rgba(255, 155, 104, 0.28) !important;
    border-color: rgba(255, 155, 104, 0.7) !important;
    color: #ffffff !important;
}

/* Forms. */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255, 155, 104, 0.18) !important;
    border-radius: 14px !important;
    padding: 1.2rem 1.4rem !important;
}

/* Dataframe border. */
[data-testid="stDataFrame"] > div {
    border-radius: 10px !important;
    border: 1px solid rgba(255, 155, 104, 0.18) !important;
    overflow: hidden !important;
}

/* Divider. */
hr { border-color: rgba(255, 155, 104, 0.12) !important; }
</style>
"""

# Plotly dark theme config applied to every chart
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.03)",
    font=dict(color="#b8adc9", family="sans-serif"),
    xaxis=dict(
        gridcolor="rgba(196,181,253,0.12)",
        linecolor="rgba(196,181,253,0.2)",
        tickfont=dict(color="#b8adc9"),
    ),
    yaxis=dict(
        gridcolor="rgba(196,181,253,0.12)",
        linecolor="rgba(196,181,253,0.2)",
        tickfont=dict(color="#b8adc9"),
    ),
    colorway=["#ff9b68", "#b798ff", "#86e3ae", "#f472b6", "#fbbf24"],
)


def apply_theme() -> None:
    """Inject the shared dark theme CSS into the current page."""
    st.markdown(_CSS, unsafe_allow_html=True)
