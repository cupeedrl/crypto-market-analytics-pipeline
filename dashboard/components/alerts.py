import streamlit as st
from datetime import datetime, timedelta


def render_alerts():
    """Render professional alerts panel"""

    st.markdown('<h2 class="section-title">Recent Alerts</h2>', unsafe_allow_html=True)

    # Sample alerts data
    alerts = [
        {
            "severity": "critical",
            "severity_label": "CRITICAL",
            "time": "2 min ago",
            "coin": "BTC",
            "message": "Price dropped 5.2% in last hour",
            "status": "Active",
        },
        {
            "severity": "warning",
            "severity_label": "WARNING",
            "time": "15 min ago",
            "coin": "ETH",
            "message": "Volume spike detected (+340%)",
            "status": "Resolved",
        },
        {
            "severity": "info",
            "severity_label": "INFO",
            "time": "1 hour ago",
            "coin": "BNB",
            "message": "Daily report generated successfully",
            "status": "Completed",
        },
        {
            "severity": "warning",
            "severity_label": "WARNING",
            "time": "2 hours ago",
            "coin": "SOL",
            "message": "Anomaly detected: Z-score 3.2",
            "status": "Investigating",
        },
        {
            "severity": "info",
            "severity_label": "INFO",
            "time": "3 hours ago",
            "coin": "XRP",
            "message": "Pipeline batch completed",
            "status": "Completed",
        },
    ]

    for alert in alerts:
        st.markdown(
            f"""
            <div class="alert-item">
                <span class="alert-severity {alert['severity']}">{alert['severity_label']}</span>
                <span class="alert-message">
                    <strong>{alert['coin']}</strong> - {alert['message']}
                </span>
                <span class="alert-time">{alert['time']}</span>
            </div>
        """,
            unsafe_allow_html=True,
        )
