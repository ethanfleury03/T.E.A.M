from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    get_busiest_scan_out_day,
    get_checked_out_by_category,
    get_daily_scan_out_summary,
    get_outbound_dashboard_totals,
    get_top_checked_out_items,
    get_transactions,
)
from date_utils import streamlit_date_range_to_iso
from ui.components import render_kpi_cards, render_page_header


CHART_ACCENT = "#ff9b68"
CHART_ACCENT_SECONDARY = "#b798ff"
GRID_COLOR = "rgba(196, 181, 253, 0.16)"
TEXT_COLOR = "#f6f2ff"
MUTED_TEXT_COLOR = "#b8adc9"


def apply_chart_style(fig, height: int = 360):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=12, t=16, b=8),
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


def render_panel_title(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="analytics-panel-heading">
            <div class="analytics-panel-title">{title}</div>
            <div class="analytics-panel-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_chart_state(message: str) -> None:
    st.markdown(
        f"""
        <div class="analytics-empty-state">
            <div class="analytics-empty-title">No scan-outs yet</div>
            <div class="analytics-empty-copy">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_day_label(raw_date: str | None) -> str:
    if raw_date is None:
        return "None yet"
    parsed = pd.to_datetime(raw_date, errors="coerce")
    if pd.isna(parsed):
        return "None yet"
    return f"{parsed.strftime('%b')} {parsed.day}" if hasattr(parsed, "strftime") else str(raw_date)


def add_day_labels(df: pd.DataFrame) -> pd.DataFrame:
    labeled_df = df.copy()
    labeled_df["day_label"] = labeled_df["tx_date"].apply(format_day_label)
    return labeled_df


render_page_header(
    "Analytics",
    "Clean scan-out trends for the pantry demo.",
)

default_end = date.today()
default_start = default_end - timedelta(days=30)

st.markdown('<div class="analytics-filter-label">Date range</div>', unsafe_allow_html=True)
filter_col, context_col = st.columns([1.2, 3], vertical_alignment="bottom")
with filter_col:
    date_range = st.date_input(
        "Date range",
        value=(default_start, default_end),
        label_visibility="collapsed",
    )
with context_col:
    st.markdown(
        '<div class="analytics-filter-note">Charts below only count items scanned out during the selected window.</div>',
        unsafe_allow_html=True,
    )

start_date, end_date = streamlit_date_range_to_iso(date_range)

top_df = get_top_checked_out_items(limit=10, start_date=start_date, end_date=end_date)
category_out_df = get_checked_out_by_category(start_date=start_date, end_date=end_date)
daily_scan_df = get_daily_scan_out_summary(start_date=start_date, end_date=end_date)
busiest_day = get_busiest_scan_out_day(start_date=start_date, end_date=end_date)
tx_df = get_transactions(start_date=start_date, end_date=end_date, tx_type="out")
totals = get_outbound_dashboard_totals()
scan_count = int(tx_df["quantity"].sum()) if not tx_df.empty else 0
unique_scanned = int(tx_df["item_name"].nunique()) if not tx_df.empty else 0
busiest_day_label = format_day_label(busiest_day["tx_date"])
busiest_day_help = (
    f"{busiest_day['total_scanned_out']} scanned out"
    if busiest_day["tx_date"] is not None
    else "No scan-outs in range"
)

render_kpi_cards(
    [
        {"label": "Scanned Out", "value": scan_count, "icon": "📤", "help": "Selected date window"},
        {"label": "Unique Items Scanned", "value": unique_scanned, "icon": "🧾", "help": "Selected date window"},
        {"label": "All-Time Top Item", "value": totals["top_item"], "icon": "🏷️", "help": f"{totals['top_item_count']} scanned out"},
        {"label": "Busiest Day", "value": busiest_day_label, "icon": "📈", "help": busiest_day_help},
    ]
)

st.markdown("")
left, right = st.columns(2)
with left:
    with st.container(border=True):
        render_panel_title("Top scanned items", "The items students took most in this date range.")
        if top_df.empty:
            render_empty_chart_state("Scan items on Take Items, then this ranking will fill in.")
        else:
            chart_df = top_df.sort_values("total_checked_out", ascending=True)
            fig_top = px.bar(
                chart_df,
                x="total_checked_out",
                y="item_name",
                orientation="h",
                text="total_checked_out",
                labels={"item_name": "", "total_checked_out": "Total Scanned Out"},
            )
            fig_top.update_traces(marker_color=CHART_ACCENT, textposition="outside", cliponaxis=False)
            fig_top = apply_chart_style(fig_top, height=380)
            fig_top.update_xaxes(showgrid=True)
            fig_top.update_yaxes(categoryorder="array", categoryarray=chart_df["item_name"].tolist())
            st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False})

with right:
    with st.container(border=True):
        render_panel_title("Category totals", "Which type of food is moving out most often.")
        if category_out_df.empty:
            render_empty_chart_state("Categories will appear after matching items are scanned out.")
        else:
            category_chart_df = category_out_df.sort_values("total_checked_out", ascending=False)
            fig_cat = px.bar(
                category_chart_df,
                x="category",
                y="total_checked_out",
                text="total_checked_out",
                labels={"category": "", "total_checked_out": "Total Scanned Out"},
            )
            fig_cat.update_traces(marker_color=CHART_ACCENT_SECONDARY, textposition="outside", cliponaxis=False)
            fig_cat = apply_chart_style(fig_cat, height=380)
            fig_cat.update_xaxes(showgrid=False)
            fig_cat.update_yaxes(showgrid=True)
            st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})

st.markdown("")
with st.container(border=True):
    render_panel_title("Daily scan-outs", "Each bar shows how many items were scanned out that day.")
    if daily_scan_df.empty:
        render_empty_chart_state("Daily totals will appear once scans exist inside the selected date range.")
    else:
        daily_chart_df = add_day_labels(daily_scan_df)
        fig_trend = px.bar(
            daily_chart_df,
            x="day_label",
            y="total_scanned_out",
            text="total_scanned_out",
            labels={"day_label": "Date", "total_scanned_out": "Total Scanned Out"},
        )
        fig_trend.update_traces(
            marker_color=CHART_ACCENT,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{x}<br>%{y} scanned out<extra></extra>",
        )
        fig_trend = apply_chart_style(fig_trend, height=280)
        fig_trend.update_xaxes(showgrid=False)
        fig_trend.update_yaxes(showgrid=True, rangemode="tozero", tickformat=",d")
        if int(daily_chart_df["total_scanned_out"].max()) <= 10:
            fig_trend.update_yaxes(dtick=1)
        st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
