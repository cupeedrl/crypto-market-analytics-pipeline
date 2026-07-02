import streamlit as st
import pandas as pd

def render_kpi_cards(df_latest, pipeline_stats):
    """Render professional KPI cards"""
    
    # Calculate metrics
    btc_price = df_latest[df_latest['symbol'] == 'BTCUSDT']['current_price'].values
    eth_price = df_latest[df_latest['symbol'] == 'ETHUSDT']['current_price'].values
    avg_change = df_latest['price_change_percent'].mean()
    total_volume = df_latest['volume'].sum()
    
    top_gainer = df_latest.loc[df_latest['price_change_percent'].idxmax()]
    top_loser = df_latest.loc[df_latest['price_change_percent'].idxmin()]
    
    st.markdown('<h2 class="section-title">Key Metrics</h2>', unsafe_allow_html=True)
    
    # Row 1
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="BTC Price",  # Bỏ emoji
            value=f"${btc_price[0]:,.2f}" if len(btc_price) > 0 else "N/A",
            delta=f"{top_gainer['price_change_percent']:+.2f}%"
        )
    
    with col2:
        st.metric(
            label="ETH Price",
            value=f"${eth_price[0]:,.2f}" if len(eth_price) > 0 else "N/A",
            delta=None
        )
    
    with col3:
        st.metric(
            label="24h Volume",
            value=f"${total_volume:,.0f}",
            delta=f"{pipeline_stats['unique_symbols']} coins"
        )
    
    with col4:
        st.metric(
            label="Avg Change",
            value=f"{avg_change:+.2f}%",
            delta="Market Trend"
        )
    
    # Row 2
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric(
            label="Top Gainer",
            value=top_gainer['symbol'].replace('USDT', ''),
            delta=f"{top_gainer['price_change_percent']:+.2f}%"
        )
    
    with col6:
        st.metric(
            label="Top Loser",
            value=top_loser['symbol'].replace('USDT', ''),
            delta=f"{top_loser['price_change_percent']:+.2f}%",
            delta_color="inverse"
        )
    
    with col7:
        st.metric(
            label="Records Today",
            value=f"{pipeline_stats['total_records']:,}",
            delta="Streaming"
        )
    
    with col8:
        st.metric(
            label="Data Freshness",
            value="Live",
            delta="< 1 min"
        )