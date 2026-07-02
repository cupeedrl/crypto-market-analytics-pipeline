import streamlit as st
from datetime import datetime


def render_header():
    """Render professional header - NO external CSS"""

    # Inline CSS only (no file loading)
    st.markdown(
        """
        <style>
        .header-container {
            background-color: #1F2937;
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 24px;
        }
        .header-title {
            color: #F9FAFB;
            font-size: 30px;
            font-weight: 700;
            margin: 0;
        }
        .header-subtitle {
            color: #9CA3AF;
            font-size: 14px;
            margin-top: 8px;
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            background-color: #1F2937;
            border: 1px solid #374151;
            padding: 6px 12px;
            border-radius: 6px;
            margin-right: 8px;
            margin-bottom: 8px;
            color: #F9FAFB;
            font-size: 13px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
            background-color: #10B981;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Header content
    st.markdown(
        """
        <div class="header-container">
            <h1 class="header-title">Crypto Market Analytics Platform</h1>
            <p class="header-subtitle">Real-Time Data Engineering & Advanced Analytics</p>
            <div style="margin-top: 16px;">
                <span class="status-badge">
                    <span class="status-dot"></span>
                    Live Data
                </span>
                <span class="status-badge">
                    <span class="status-dot"></span>
                    Kafka Connected
                </span>
                <span class="status-badge">
                    <span class="status-dot"></span>
                    Airflow Running
                </span>
                <span class="status-badge">
                    <span class="status-dot"></span>
                    BigQuery Synced
                </span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
