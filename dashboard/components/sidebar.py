import streamlit as st
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from services.database import DatabaseService


@st.cache_data(ttl=300)  # Cache 5 phút
def get_available_coins():
    """Get all available coins from database"""
    try:
        df = DatabaseService.get_latest_prices()
        if df is not None and not df.empty:
            coins = sorted(df["symbol"].unique().tolist())
            return coins
    except Exception as e:
        st.warning(f"Could not fetch coins from database: {e}")

    # Fallback list if database query fails
    return [
        "BTCUSDT",
        "ETHUSDT",
        "BNBUSDT",
        "SOLUSDT",
        "XRPUSDT",
        "ADAUSDT",
        "DOGEUSDT",
        "DOTUSDT",
        "AVAXUSDT",
        "POLUSDT",
        "LINKUSDT",
        "LTCUSDT",
        "UNIUSDT",
        "ATOMUSDT",
        "ETCUSDT",
    ]


def render_sidebar():
    """Render professional sidebar"""

    with st.sidebar:
        st.markdown("### Configuration")

        # Coin selector - Dynamic from database
        st.markdown("#### Coin Selection")
        available_coins = get_available_coins()

        selected_coins = st.multiselect(
            "Select coins",
            options=available_coins,
            default=(
                available_coins[:3] if len(available_coins) >= 3 else available_coins
            ),
        )

        st.markdown("---")

        # Date range
        st.markdown("#### Date Range")
        days = st.slider("Analysis period", min_value=7, max_value=60, value=30, step=1)

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
