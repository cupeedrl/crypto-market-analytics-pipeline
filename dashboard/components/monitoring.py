import streamlit as st
from datetime import datetime, timedelta
import random

def render_monitoring(pipeline_stats):
    """Render professional pipeline monitoring panel"""
    
    st.markdown('<h2 class="section-title">Pipeline Health</h2>', unsafe_allow_html=True)
    
    # Services data
    services = [
        {
            "name": "Airflow",
            "status": "Running",
            "status_class": "healthy",
            "last_update": "2 min ago",
            "latency": "45ms"
        },
        {
            "name": "Kafka",
            "status": "Healthy",
            "status_class": "healthy",
            "last_update": "1 min ago",
            "latency": "12ms"
        },
        {
            "name": "Spark",
            "status": "Streaming",
            "status_class": "healthy",
            "last_update": "30 sec ago",
            "latency": "8ms"
        },
        {
            "name": "PostgreSQL",
            "status": "Connected",
            "status_class": "healthy",
            "last_update": "1 min ago",
            "latency": "23ms"
        },
        {
            "name": "BigQuery",
            "status": "Synced",
            "status_class": "healthy",
            "last_update": "5 min ago",
            "latency": "156ms"
        },
        {
            "name": "dbt",
            "status": "Success",
            "status_class": "healthy",
            "last_update": "1 hour ago",
            "latency": "N/A"
        }
    ]
    
    # Display services in 3 columns
    cols = st.columns(3)
    
    for i, service in enumerate(services):
        with cols[i % 3]:
            st.markdown(f"""
                <div class="monitoring-card">
                    <div class="monitoring-service">{service['name']}</div>
                    <div class="monitoring-status">
                        <span class="status-dot {service['status_class']}"></span>
                        {service['status']}
                    </div>
                    <div class="monitoring-latency">
                        Last update: {service['last_update']} | Latency: {service['latency']}
                    </div>
                </div>
            """, unsafe_allow_html=True)