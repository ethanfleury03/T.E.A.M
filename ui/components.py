from __future__ import annotations

from collections.abc import Iterable

import streamlit as st


def render_sidebar(active_page: str) -> int:
    with st.sidebar:
        st.markdown('<div class="brand-title">Niagara Pantry</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="brand-subtitle">Track what leaves the pantry through scan-outs</div>',
            unsafe_allow_html=True,
        )

        st.divider()
        st.caption("Demo flow")
        st.markdown("Add items once, then scan items as they leave.")
        st.caption(f"Active: {active_page}")
        st.markdown('<span class="status-pill status-ok">Connected</span>', unsafe_allow_html=True)
    return 0


def render_page_header(title: str, subtitle: str, actions: Iterable[dict] | None = None) -> dict[str, bool]:
    actions = list(actions or [])
    result: dict[str, bool] = {}

    # Extra width on the right when there are several header buttons (avoids label wrap/clipping).
    col_ratio = (2, 3.2) if len(actions) >= 4 else (3, 2)
    left_col, right_col = st.columns(list(col_ratio), vertical_alignment="top")
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
            st.markdown(
                '<div class="page-header-actions-offset" aria-hidden="true"></div>',
                unsafe_allow_html=True,
            )
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
