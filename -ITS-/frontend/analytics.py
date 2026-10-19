import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

def render_analytics_dashboard(df: pd.DataFrame):
    if df.empty:
        st.info("Chưa có dữ liệu để phân tích")
        return

    st.markdown("### 📊 Phân tích hệ thống")
    
    # 1. Processing Time Series Data
    df['entry_dt'] = pd.to_datetime(df['entry_time'], errors='coerce')
    df['hour'] = df['entry_dt'].dt.hour
    
    # Traffic over time (hourly)
    hourly_traffic = df.groupby('hour').size().reset_index(name='count')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
        st.markdown("#### Lưu lượng xe theo giờ")
        fig_traffic = px.line(
            hourly_traffic, 
            x='hour', 
            y='count',
            labels={'hour': 'Giờ trong ngày', 'count': 'Số lượng xe'},
            template="plotly_dark"
        )
        fig_traffic.update_traces(line_color='#3b82f6', line_width=3)
        fig_traffic.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0),
            height=300
        )
        st.plotly_chart(fig_traffic, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
        st.markdown("#### Độ chính xác OCR")
        # Confidence distribution
        bins = [0, 0.5, 0.9, 1.0]
        labels = ['Thấp (<50%)', 'Trung bình (50-90%)', 'Cao (>90%)']
        df['conf_cat'] = pd.cut(df['ocr_confidence'], bins=bins, labels=labels)
        conf_counts = df['conf_cat'].value_counts().reset_index()
        conf_counts.columns = ['Category', 'Count']
        
        fig_conf = px.pie(
            conf_counts, 
            values='Count', 
            names='Category',
            color='Category',
            color_discrete_map={
                'Cao (>90%)': '#10b981',
                'Trung bình (50-90%)': '#f59e0b',
                'Thấp (<50%)': '#ef4444'
            },
            hole=0.4,
            template="plotly_dark"
        )
        fig_conf.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0),
            height=300,
            showlegend=True
        )
        st.plotly_chart(fig_conf, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. Match Result Dashboard
    st.markdown("<div class='panel-card' style='margin-top:20px;'>", unsafe_allow_html=True)
    st.markdown("#### Trạng thái đối chiếu biển số")
    match_counts = df['match_result'].value_counts().reset_index()
    match_counts.columns = ['Result', 'Count']
    
    # Rename for display
    result_map = {'MATCH': 'Khớp', 'MISMATCH': 'Sai lệch', 'UNKNOWN': 'Chưa xác định', None: 'Chưa đối chiếu'}
    match_counts['Result'] = match_counts['Result'].map(lambda x: result_map.get(x, str(x)))
    
    fig_match = px.bar(
        match_counts,
        x='Result',
        y='Count',
        color='Result',
        text='Count',
        template="plotly_dark"
    )
    fig_match.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
        height=300
    )
    st.plotly_chart(fig_match, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
