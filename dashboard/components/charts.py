import streamlit as st
import plotly.express as px
import numpy as np
from services.analytics import AnalyticsService


def render_correlation_heatmap(df_history):
    """Render correlation heatmap with debugging"""
    
    st.markdown('<h2 class="section-title">Market Correlation</h2>', unsafe_allow_html=True)
    
    try:
        if df_history.empty:
            st.warning("No historical data available")
            return
        
        # Group by DATE and symbol
        daily_prices = df_history.copy()
        daily_prices['date'] = daily_prices['processed_at'].dt.date
        
        # DEBUG: Show data stats
        st.write(f"**Data stats:** {daily_prices['symbol'].nunique()} coins, {daily_prices['date'].nunique()} days")
        
        # Get average price per day per symbol
        daily_avg = daily_prices.groupby(['date', 'symbol'])['current_price'].mean().reset_index()
        
        # Pivot
        pivot_df = daily_avg.pivot(
            index='date',
            columns='symbol',
            values='current_price'
        )
        
        # DEBUG: Show pivot info
        with st.expander("Debug: Pivot Table Info"):
            st.write(f"Shape: {pivot_df.shape}")
            st.write("First 5 rows:")
            st.dataframe(pivot_df.head())
            st.write(f"NaN count per column:")
            st.write(pivot_df.isna().sum())
        
        # Drop columns with too many NaN
        pivot_df = pivot_df.dropna(axis=1, thresh=len(pivot_df) * 0.5)
        
        if pivot_df.shape[1] < 2:
            st.warning(f"Not enough coins. Only {pivot_df.shape[1]} coin(s) available.")
            return
        
        # Calculate daily returns
        returns = pivot_df.pct_change().dropna()
        
        # DEBUG: Show returns
        with st.expander("Debug: Returns Data"):
            st.write(f"Shape: {returns.shape}")
            st.write("Returns stats:")
            st.dataframe(returns.describe())
            st.write("Sample returns:")
            st.dataframe(returns.head(10))
        
        if returns.empty or len(returns) < 2:
            st.warning("Not enough data points")
            return
        
        # Calculate correlation
        corr_matrix = returns.corr()
        
        # DEBUG: Show correlation before fillna
        with st.expander("Debug: Correlation Matrix (before fillna)"):
            st.write(f"Shape: {corr_matrix.shape}")
            st.write(f"NaN count: {corr_matrix.isna().sum().sum()}")
            st.dataframe(corr_matrix)
        
        # Fill NaN with 0 (but this might be causing the issue!)
        corr_matrix_filled = corr_matrix.fillna(0)
        
        # CHECK: If correlation is all 1.0, something is wrong
        if (corr_matrix_filled == 1.0).all().all():
            st.error("All correlations are 1.0 - this indicates a data problem!")
            st.info("**Possible causes:**")
            st.info("- All coins have identical price patterns")
            st.info("- Pivot table has duplicate columns")
            st.info("- Not enough variation in returns data")
            
            # Try using raw correlation without fillna
            st.write("**Trying correlation without fillna:**")
            st.dataframe(corr_matrix)
            return
        
        # Create heatmap
        fig = px.imshow(
            corr_matrix_filled,
            text_auto='.2f',
            aspect='auto',
            color_continuous_scale='RdBu_r',
            zmin=-1,
            zmax=1,
            title='Cryptocurrency Price Correlation (Daily Returns)'
        )
        
        fig.update_layout(
            plot_bgcolor='#111827',
            paper_bgcolor='#111827',
            font_color='#F9FAFB',
            height=500,
            margin=dict(l=50, r=50, t=50, b=50),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        
# RISK ANALYTICS
# ===========================

def render_risk_analytics(df_history):
    """Render risk analytics"""

    st.markdown(
        '<h2 class="section-title">Risk Analytics</h2>',
        unsafe_allow_html=True
    )

    try:

        volatility_df = AnalyticsService.calculate_volatility_metrics(
            df_history
        )

        if volatility_df.empty:
            st.warning("Not enough data.")
            return

        for col in [
            "avg_return",
            "volatility",
            "sharpe_ratio"
        ]:
            volatility_df[col] = (
                volatility_df[col]
                .replace([np.inf, -np.inf], 0)
                .fillna(0)
            )

        volatility_df["sharpe_ratio_abs"] = (
            volatility_df["sharpe_ratio"].abs()
        )

        col1, col2 = st.columns(2)

        with col1:

            fig = px.scatter(
                volatility_df,
                x="volatility",
                y="avg_return",
                size="sharpe_ratio_abs",
                color="sharpe_ratio",
                hover_data=["symbol"],
                color_continuous_scale="RdYlGn",
                size_max=20
            )

            fig.update_layout(
                plot_bgcolor="#111827",
                paper_bgcolor="#111827",
                font_color="#F9FAFB",
                height=420,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:

            sharpe = volatility_df.sort_values(
                "sharpe_ratio",
                ascending=False
            )

            fig = px.bar(
                sharpe,
                x="symbol",
                y="sharpe_ratio",
                color="sharpe_ratio",
                color_continuous_scale="Viridis"
            )

            fig.update_layout(
                plot_bgcolor="#111827",
                paper_bgcolor="#111827",
                font_color="#F9FAFB",
                height=420,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")


# ANOMALY DETECTION

def render_anomaly_detection(df_history):
    """Render anomaly detection"""

    st.markdown(
        '<h2 class="section-title">Anomaly Detection</h2>',
        unsafe_allow_html=True
    )

    try:

        threshold = st.slider("Z-Score Threshold", 2.0, 5.0, 3.5)

        anomalies_df = AnalyticsService.detect_anomalies(
            df_history,
            threshold=threshold
        )

        if anomalies_df.empty:
            st.success(
                f"No anomalies detected (threshold={threshold})"
            )
            return

        col1, col2 = st.columns(2)

        col1.metric(
            "Anomalies",
            len(anomalies_df)
        )

        col2.metric(
            "Affected Coins",
            anomalies_df["symbol"].nunique()
        )

        display_df = anomalies_df[
            ["symbol", "date", "z_score"]
        ].copy()

        display_df["z_score"] = (
            display_df["z_score"].round(2)
        )

        st.dataframe(
            display_df.sort_values(
                "date",
                ascending=False
            ),
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error: {e}")