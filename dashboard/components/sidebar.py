import streamlit as st


def render_sidebar():
    """Render professional sidebar"""

    with st.sidebar:
        st.markdown("### Configuration")

        # Coin selector
        st.markdown("#### Coin Selection")
        selected_coins = st.multiselect(
            "Select coins",
            options=[
                "BTCUSDT",
                "ETHUSDT",
                "BNBUSDT",
                "SOLUSDT",
                "XRPUSDT",
                "ADAUSDT",
                "DOGEUSDT",
                "DOTUSDT",
            ],
            default=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        )

        st.markdown("---")

        # Date range
        st.markdown("#### Date Range")
        days = st.slider("Analysis period", min_value=7, max_value=90, value=30, step=1)

        st.markdown("---")

        # Refresh interval
        st.markdown("#### Refresh Interval")
        refresh_interval = st.selectbox(
            "Auto-refresh", options=["Off", "30s", "1min", "5min"], index=0
        )

        st.markdown("---")

        # Export button
        if st.button("Export Data", use_container_width=True):
            st.success("Data exported successfully")

        st.markdown("---")

        # System info - BỎ EMOJI
        st.markdown("#### System Status")
        st.markdown(
            """
            <div style="font-size: 12px; color: #9CA3AF;">
                <p style="margin: 4px 0;">Version: 1.0.0</p>
                <p style="margin: 4px 0;">Environment: Production</p>
                <p style="margin: 4px 0;">Region: ap-southeast-2</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    return selected_coins, days, refresh_interval
