import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import glob
import os

# ========== CONFIG ==========

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'inference_result')

st.set_page_config(
    page_title="Ron 88 QC Dashboard",
    page_icon="🏭",
    layout="wide",
)

# ========== CUSTOM CSS ==========

st.markdown("""
<style>
    /* metric cards */
    div[data-testid="stMetric"] {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 16px 20px;
    }
    div[data-testid="stMetric"] label {
        font-size: 0.85rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }

    /* header */
    .main-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 4px;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .main-header span {
        font-size: 1.8rem;
    }
    .sub-header {
        color: #6c757d;
        font-size: 0.95rem;
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)

# ========== HEADER ==========

st.markdown("""
<div class="main-header">
    <span>🏭</span>
    <h1>Ron 88 Quality Control Dashboard</h1>
</div>
<p class="sub-header">Production inspection report viewer</p>
""", unsafe_allow_html=True)

# ========== LOAD DATA ==========

report_files = sorted(glob.glob(os.path.join(REPORT_DIR, 'report_*.csv')), reverse=True)

if not report_files:
    st.warning("No report files found in `inference_result/` folder.")
    st.stop()

# Sidebar
with st.sidebar:
    st.header("Session")
    selected = st.selectbox(
        "Select report file",
        report_files,
        format_func=lambda x: os.path.basename(x).replace('report_', '').replace('.csv', '').replace('_', ' @ '),
    )

    # Check for matching summary file
    summary_file = selected.replace('report_', 'summary_')
    has_summary = os.path.exists(summary_file)

df = pd.read_csv(selected)

if df.empty:
    st.info("This report has no bottle data.")
    st.stop()

df['defects'] = df['defects'].fillna('')

# ========== SUMMARY METRICS ==========

total = len(df)
passed = len(df[df['result'] == 'PASS'])
rejected = len(df[df['result'] == 'REJECT'])
quality_rate = (passed / total * 100) if total > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Inspected", total)
col2.metric("Passed", passed)
col3.metric("Rejected", rejected)
col4.metric("Quality Rate", f"{quality_rate:.1f}%")

# Show session info from summary if available
if has_summary:
    summary_df = pd.read_csv(summary_file)
    summary_dict = dict(zip(summary_df['metric'], summary_df['value']))
    duration = summary_dict.get('session_duration_s', '?')
    session_date = summary_dict.get('session_date', '?')
    st.caption(f"Session: {session_date}  ·  Duration: {duration}s")

st.divider()

# ========== CHARTS ==========

chart_col1, chart_col2 = st.columns(2)

# Pass/Reject pie chart
with chart_col1:
    st.subheader("Result Distribution")
    result_counts = df['result'].value_counts()
    fig_pie = px.pie(
        names=result_counts.index,
        values=result_counts.values,
        color=result_counts.index,
        color_discrete_map={'PASS': '#28a745', 'REJECT': '#dc3545'},
        hole=0.4,
    )
    fig_pie.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=300,
        legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5),
    )
    fig_pie.update_traces(textinfo='value+percent', textfont_size=14)
    st.plotly_chart(fig_pie, use_container_width=True)

# Defect breakdown bar chart
with chart_col2:
    st.subheader("Defect Breakdown")
    reject_df = df[df['defects'] != ''].copy()
    if not reject_df.empty:
        all_defects = reject_df['defects'].str.split(' \\+ ').explode()
        defect_counts = all_defects.value_counts().reset_index()
        defect_counts.columns = ['Defect', 'Count']

        fig_bar = px.bar(
            defect_counts,
            x='Defect',
            y='Count',
            color='Count',
            color_continuous_scale=['#ffc107', '#dc3545'],
            text='Count',
        )
        fig_bar.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            height=300,
            showlegend=False,
            coloraxis_showscale=False,
            xaxis_title='',
            yaxis_title='',
        )
        fig_bar.update_traces(textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.success("No defects detected in this session!")

st.divider()

# ========== BOTTLE LOG TABLE ==========

st.subheader("Inspection Log")

# Filter controls
filter_col1, filter_col2 = st.columns([1, 4])
with filter_col1:
    result_filter = st.selectbox("Filter by result", ["All", "PASS", "REJECT"])

display_df = df[['bottle_id', 'timestamp', 'bottle_number', 'result', 'bottle_type', 'defects']].copy()
display_df['defects'] = display_df['defects'].replace('', '-')

if result_filter != "All":
    display_df = display_df[display_df['result'] == result_filter]

display_df.columns = ['Bottle ID', 'Timestamp', '#', 'Result', 'Type', 'Defects']

def highlight_result(row):
    if row['Result'] == 'PASS':
        return ['background-color: #d4edda; color: #155724'] * len(row)
    return ['background-color: #f8d7da; color: #721c24'] * len(row)

st.dataframe(
    display_df.style.apply(highlight_result, axis=1),
    use_container_width=True,
    hide_index=True,
    height=400,
)

st.caption(f"Showing {len(display_df)} of {total} bottles")
