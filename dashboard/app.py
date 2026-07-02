import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from components.header import render_header
from components.sidebar import render_sidebar
from components.kpi_cards import render_kpi_cards
from components.charts import render_correlation_heatmap, render_risk_analytics, render_anomaly_detection
from components.monitoring import render_monitoring
from components.alerts import render_alerts
from components.data_table import render_data_table
from services.database import DatabaseService
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="Crypto Analytics Pro",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load global CSS
st.markdown("""
    <style>
    /* Global styles */
    .stApp {
        background-color: #111827 !important;
        color: #F9FAFB !important;
    }
    
    /* Section titles */
    .section-title {
        color: #F9FAFB;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #374151;
    }
    
    /* Metrics */
    .stMetric {
        background-color: #1F2937 !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }
    
    .stMetric label {
        color: #9CA3AF !important;
    }
    
    .stMetric div[data-testid="stMetricValue"] {
        color: #F9FAFB !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1F2937 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #3B82F6 !important;
        color: #F9FAFB !important;
        border: none !important;
        border-radius: 6px !important;
    }
    
    /* Hide sidebar toggle */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    """Main application"""
    
    # Render header
    render_header()
    
    # Render sidebar
    selected_coins, days, refresh_interval = render_sidebar()
    
    # Load data
    with st.spinner("Loading data..."):
        try:
            df_latest = DatabaseService.get_latest_prices()
            df_history = DatabaseService.get_price_history(days=days)
            pipeline_stats = DatabaseService.get_pipeline_stats()
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return
    
    # Render components
    render_kpi_cards(df_latest, pipeline_stats)
    render_monitoring(pipeline_stats)
    render_alerts()
    render_correlation_heatmap(df_history)
    render_risk_analytics(df_history)
    render_anomaly_detection(df_history)
    render_data_table(df_latest)
    
    # Footer
    st.markdown("""
        <div style="text-align: center; color: #9CA3AF; padding: 24px 0; border-top: 1px solid #374151; margin-top: 24px;">
            Crypto Market Analytics Platform v1.0.0
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()