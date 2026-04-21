"""Shared dark theme — call apply_theme() at the top of every page."""
import streamlit as st


_CSS = """
<style>
/* ── Background gradient (overrides flat dark from config.toml) ───── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%) !important;
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent !important; }

/* ── Sidebar accent border ───────────────────────────────────────── */
[data-testid="stSidebar"],
section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(99, 179, 237, 0.22) !important;
}

/* Sidebar active nav link */
[data-testid="stSidebarNavLink"][aria-selected="true"] {
    background: rgba(99, 179, 237, 0.15) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(99, 179, 237, 0.08) !important;
    border-radius: 8px !important;
}

/* ── Content width ───────────────────────────────────────────────── */
.block-container {
    max-width: 960px !important;
    margin: 0 auto !important;
    padding-top: 2rem !important;
}

/* ── Gradient headings ───────────────────────────────────────────── */
h1 {
    background: linear-gradient(90deg, #e0f2fe 0%, #63b3ed 60%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}
h2, h3, h4 { font-weight: 700 !important; }

/* ── Buttons ─────────────────────────────────────────────────────── */
[data-testid="stButton"] > button,
[data-testid="stFormSubmitButton"] > button {
    background: rgba(99, 179, 237, 0.12) !important;
    border: 1px solid rgba(99, 179, 237, 0.4) !important;
    border-radius: 8px !important;
    color: #63b3ed !important;
    font-weight: 600 !important;
    transition: background 0.2s, color 0.2s, border-color 0.2s !important;
}
[data-testid="stButton"] > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background: rgba(99, 179, 237, 0.28) !important;
    border-color: rgba(99, 179, 237, 0.7) !important;
    color: #e0f2fe !important;
}

/* ── Forms ───────────────────────────────────────────────────────── */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(99, 179, 237, 0.18) !important;
    border-radius: 14px !important;
    padding: 1.2rem 1.4rem !important;
}

/* ── Dataframe border ────────────────────────────────────────────── */
[data-testid="stDataFrame"] > div {
    border-radius: 10px !important;
    border: 1px solid rgba(99, 179, 237, 0.18) !important;
    overflow: hidden !important;
}

/* ── Divider ─────────────────────────────────────────────────────── */
hr { border-color: rgba(99, 179, 237, 0.12) !important; }
</style>
"""

# Plotly dark theme config applied to every chart
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.03)",
    font=dict(color="#94a3b8", family="sans-serif"),
    xaxis=dict(
        gridcolor="rgba(99,179,237,0.08)",
        linecolor="rgba(99,179,237,0.2)",
        tickfont=dict(color="#64748b"),
    ),
    yaxis=dict(
        gridcolor="rgba(99,179,237,0.08)",
        linecolor="rgba(99,179,237,0.2)",
        tickfont=dict(color="#64748b"),
    ),
    colorway=["#63b3ed", "#a78bfa", "#34d399", "#f472b6", "#fbbf24"],
)


def apply_theme() -> None:
    """Inject the shared dark theme CSS into the current page."""
    st.markdown(_CSS, unsafe_allow_html=True)
