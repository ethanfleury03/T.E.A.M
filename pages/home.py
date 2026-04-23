from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    get_daily_scan_out_summary,
    get_outbound_dashboard_totals,
    get_top_checked_out_items,
)
from ui.components import render_kpi_cards


CHART_ACCENT = "#ff9b68"
CHART_ACCENT_SECONDARY = "#b798ff"
GRID_COLOR = "rgba(196, 181, 253, 0.16)"
TEXT_COLOR = "#f6f2ff"
MUTED_TEXT_COLOR = "#b8adc9"


def format_day_label(raw_date: str | None) -> str:
    if raw_date is None:
        return "None yet"
    parsed = pd.to_datetime(raw_date, errors="coerce")
    if pd.isna(parsed):
        return "None yet"
    return f"{parsed.strftime('%b')} {parsed.day}"


def apply_home_chart_style(fig, height: int = 300):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=12, t=12, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_COLOR, size=13),
        hoverlabel=dict(bgcolor="#18121f", bordercolor="rgba(255,255,255,0.14)", font=dict(color=TEXT_COLOR)),
        showlegend=False,
    )
    fig.update_xaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
        linecolor="rgba(255,255,255,0.12)",
        tickfont=dict(color=MUTED_TEXT_COLOR),
        title_font=dict(color=MUTED_TEXT_COLOR),
    )
    fig.update_yaxes(
        gridcolor="rgba(0,0,0,0)",
        zerolinecolor=GRID_COLOR,
        linecolor="rgba(255,255,255,0.12)",
        tickfont=dict(color=MUTED_TEXT_COLOR),
        title_font=dict(color=MUTED_TEXT_COLOR),
    )
    return fig


def render_dashboard_panel(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="home-panel-heading">
            <div class="home-panel-title">{title}</div>
            <div class="home-panel-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


today = date.today()
start_date = (today - timedelta(days=30)).isoformat()
end_date = today.isoformat()

totals = get_outbound_dashboard_totals()
top_df = get_top_checked_out_items(limit=5, start_date=start_date, end_date=end_date)
daily_df = get_daily_scan_out_summary(start_date=start_date, end_date=end_date)

st.markdown(
    """
    <div class="home-hero">
        <div class="home-hero-mark">NIAGARA PANTRY</div>
        <div class="home-hero-content">
            <div class="home-hero-title">Food Pantry Scan Dashboard</div>
            <div class="home-hero-subtitle">Track which pantry items students are taking through barcode scan-outs.</div>
        </div>
        <div class="home-hero-accent">Scan-Out Tracking</div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_kpi_cards(
    [
        {"label": "Known Items", "value": int(totals["known_items"]), "icon": "📦", "help": "Items added to the sheet"},
        {
            "label": "Total Scanned Out",
            "value": int(totals["total_scanned_out"]),
            "icon": "📤",
            "help": "All items recorded as leaving",
        },
        {
            "label": "Unique Items Scanned",
            "value": int(totals["unique_items_scanned"]),
            "icon": "🧾",
            "help": "Different items students have taken",
        },
        {
            "label": "Top Item",
            "value": totals["top_item"],
            "icon": "🏷️",
            "help": f"{totals['top_item_count']} scanned out",
        },
    ]
)

st.markdown("")
left, right = st.columns(2)
with left:
    with st.container(border=True):
        render_dashboard_panel("Top Scanned Items", "Most-used pantry items over the last 30 days.")
        if top_df.empty:
            st.info("Scan items on Take Items to populate this chart.")
        else:
            chart_df = top_df.sort_values("total_checked_out", ascending=True)
            fig_top = px.bar(
                chart_df,
                x="total_checked_out",
                y="item_name",
                orientation="h",
                text="total_checked_out",
                labels={"item_name": "", "total_checked_out": "Scanned Out"},
            )
            fig_top.update_traces(marker_color=CHART_ACCENT, textposition="outside", cliponaxis=False)
            fig_top = apply_home_chart_style(fig_top, height=315)
            fig_top.update_xaxes(showgrid=True)
            fig_top.update_yaxes(categoryorder="array", categoryarray=chart_df["item_name"].tolist())
            st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False})

with right:
    with st.container(border=True):
        render_dashboard_panel("Daily Scan-Outs", "A compact view of pantry activity over time.")
        if daily_df.empty:
            st.info("Daily scan totals will appear after scan-outs are recorded.")
        else:
            daily_chart_df = daily_df.tail(14).copy()
            daily_chart_df["day_label"] = daily_chart_df["tx_date"].apply(format_day_label)
            fig_daily = px.bar(
                daily_chart_df,
                x="day_label",
                y="total_scanned_out",
                text="total_scanned_out",
                labels={"day_label": "Date", "total_scanned_out": "Scanned Out"},
            )
            fig_daily.update_traces(
                marker_color=CHART_ACCENT_SECONDARY,
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{x}<br>%{y} scanned out<extra></extra>",
            )
            fig_daily = apply_home_chart_style(fig_daily, height=315)
            fig_daily.update_xaxes(showgrid=False)
            fig_daily.update_yaxes(showgrid=True, rangemode="tozero", tickformat=",d")
            st.plotly_chart(fig_daily, use_container_width=True, config={"displayModeBar": False})
