import streamlit as st
import pandas as pd


def render_data_table(df_latest):
    """Render professional data table with search and sort"""

    st.markdown('<h2 class="section-title">Raw Data</h2>', unsafe_allow_html=True)

    # Search box
    search_term = st.text_input("Search coins", placeholder="Enter coin symbol...")

    # Filter data
    if search_term:
        df_filtered = df_latest[
            df_latest["symbol"].str.contains(search_term, case=False, na=False)
        ]
    else:
        df_filtered = df_latest

    # Display table
    st.dataframe(
        df_filtered[
            [
                "symbol",
                "current_price",
                "price_change_percent",
                "volume",
                "processed_at",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
