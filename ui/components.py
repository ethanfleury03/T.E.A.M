from __future__ import annotations

from collections.abc import Iterable

import streamlit as st

from database import SETTINGS


def render_sidebar(active_page: str) -> int:
    with st.sidebar:
        st.markdown('<div class="brand-title">Niagara Pantry</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-subtitle">Food Inventory Dashboard</div>', unsafe_allow_html=True)

        st.divider()
        st.caption("Utilities")
        default_threshold = int(st.session_state.get("low_stock_threshold", SETTINGS["LOW_STOCK_THRESHOLD"]))
        threshold = st.slider(
            "Low stock threshold",
            min_value=0,
            max_value=50,
            value=default_threshold,
            help="Used for visual warnings across pages.",
        )
        st.session_state["low_stock_threshold"] = threshold

        st.divider()
        st.caption(f"Active: {active_page}")
        st.markdown('<span class="status-pill status-ok">Connected</span>', unsafe_allow_html=True)
    return threshold


def render_page_header(title: str, subtitle: str, actions: Iterable[dict] | None = None) -> dict[str, bool]:
    actions = list(actions or [])
    result: dict[str, bool] = {}

    left_col, right_col = st.columns([3, 2], vertical_alignment="center")
    with left_col:
        st.markdown(
            f"""
            <div class="page-header">
                <div class="page-title">{title}</div>
                <div class="page-subtitle">{subtitle}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right_col:
        if actions:
            action_cols = st.columns(len(actions))
            for col, action in zip(action_cols, actions):
                with col:
                    action_key = action.get("key", action["label"])
                    is_primary = action.get("type", "secondary") == "primary"
                    clicked = st.button(
                        action["label"],
                        key=action_key,
                        type="primary" if is_primary else "secondary",
                        use_container_width=True,
                        help=action.get("help"),
                    )
                    result[action_key] = clicked
    return result


def render_kpi_cards(metrics: list[dict]) -> None:
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{metric.get("icon", "")} {metric["label"]}</div>
                    <div class="kpi-value">{metric["value"]}</div>
                    <div class="kpi-help">{metric.get("help", "")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def badge(text: str, variant: str) -> str:
    class_map = {
        "ok": "status-ok",
        "low": "status-low",
        "out": "status-out",
        "info": "status-info",
    }
    css_class = class_map.get(variant, "status-info")
    return f'<span class="status-pill {css_class}">{text}</span>'


def render_empty_state(title: str, description: str, primary_label: str, secondary_label: str) -> tuple[bool, bool]:
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{title}</div>
            <div style="color:#a9b2bf; margin-bottom:0.75rem;">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    a_col, b_col, _ = st.columns([1, 1, 4])
    with a_col:
        primary = st.button(primary_label, type="primary", use_container_width=True, key=f"empty_{primary_label}")
    with b_col:
        secondary = st.button(secondary_label, use_container_width=True, key=f"empty_{secondary_label}")
    return primary, secondary
