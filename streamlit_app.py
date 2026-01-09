import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Configure page
st.set_page_config(
    page_title="Gold Price Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "dataset"
DAILY_PATH = DATA_DIR / "gold_daily.parquet"
BACKUP_PATH = DATA_DIR / "gold_backup.parquet"

# Title
st.title("📈 Gold Price Dashboard")
st.markdown("Historical gold prices tracking and analysis")

# Load data
@st.cache_data
def load_data():
    """Load gold price data from parquet files"""
    if DAILY_PATH.exists():
        df = pd.read_parquet(DAILY_PATH)
    elif BACKUP_PATH.exists():
        df = pd.read_parquet(BACKUP_PATH)
    else:
        return None
    
    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date')

# Load data
df = load_data()

if df is None or df.empty:
    st.error("❌ No data available. Run the pipeline first.")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")
date_range = st.sidebar.date_input(
    "Date Range",
    value=(df['date'].min().date(), df['date'].max().date()),
    min_value=df['date'].min().date(),
    max_value=df['date'].max().date()
)

# Filter data
start_date = pd.to_datetime(date_range[0])
end_date = pd.to_datetime(date_range[1]) + timedelta(days=1)
df_filtered = df[(df['date'] >= start_date) & (df['date'] < end_date)].copy()

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    latest_price = df_filtered['closed_price'].iloc[-1]
    st.metric(
        "Latest Price",
        f"${latest_price:.2f}",
        f"{latest_price - df_filtered['closed_price'].iloc[0]:.2f}"
    )

with col2:
    avg_price = df_filtered['closed_price'].mean()
    st.metric("Average Price", f"${avg_price:.2f}")

with col3:
    max_price = df_filtered['max_price'].max()
    st.metric("Highest Price", f"${max_price:.2f}")

with col4:
    min_price = df_filtered['min_price'].min()
    st.metric("Lowest Price", f"${min_price:.2f}")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Chart", "Table", "Statistics", "Analysis"])

# Tab 1: Chart
with tab1:
    st.subheader("Price Trend")
    
    # Create line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_filtered['date'],
        y=df_filtered['closed_price'],
        mode='lines',
        name='Closing Price',
        line=dict(color='#1f77b4', width=2),
        fill=None
    ))
    
    fig.add_trace(go.Scatter(
        x=df_filtered['date'],
        y=df_filtered['max_price'],
        mode='lines',
        name='Max Price',
        line=dict(color='#2ca02c', width=1),
        opacity=0.5
    ))
    
    fig.add_trace(go.Scatter(
        x=df_filtered['date'],
        y=df_filtered['min_price'],
        mode='lines',
        name='Min Price',
        line=dict(color='#d62728', width=1),
        opacity=0.5
    ))
    
    fig.update_layout(
        title="Gold Price Trend",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, width='stretch')

# Tab 2: Table
with tab2:
    st.subheader("Data Table")
    
    # Format display
    df_display = df_filtered.copy()
    df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d')
    df_display = df_display[['date', 'max_price', 'min_price', 'closed_price']]
    df_display.columns = ['Date', 'Max Price', 'Min Price', 'Closed Price']
    
    # Format prices
    for col in ['Max Price', 'Min Price', 'Closed Price']:
        df_display[col] = df_display[col].apply(lambda x: f"${x:.2f}")
    
    st.dataframe(df_display, width='stretch', hide_index=True)
    
    # Download button
    csv = df_filtered.to_csv(index=False)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="gold_prices.csv",
        mime="text/csv"
    )

# Tab 3: Statistics
with tab3:
    st.subheader("Statistical Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Price Statistics:**")
        stats = {
            'Mean': df_filtered['closed_price'].mean(),
            'Median': df_filtered['closed_price'].median(),
            'Std Dev': df_filtered['closed_price'].std(),
            'Min': df_filtered['closed_price'].min(),
            'Max': df_filtered['closed_price'].max(),
            'Q1': df_filtered['closed_price'].quantile(0.25),
            'Q3': df_filtered['closed_price'].quantile(0.75),
        }
        
        for key, value in stats.items():
            st.write(f"- **{key}:** ${value:.2f}")
    
    with col2:
        st.write("**Daily Range Statistics:**")
        df_filtered['daily_range'] = df_filtered['max_price'] - df_filtered['min_price']
        
        range_stats = {
            'Average Range': df_filtered['daily_range'].mean(),
            'Max Range': df_filtered['daily_range'].max(),
            'Min Range': df_filtered['daily_range'].min(),
            'Total Records': len(df_filtered)
        }
        
        for key, value in range_stats.items():
            if 'Records' in key:
                st.write(f"- **{key}:** {int(value)}")
            else:
                st.write(f"- **{key}:** ${value:.2f}")

# Tab 4: Analysis
with tab4:
    st.subheader("Daily Price Change Analysis")
    
    df_analysis = df_filtered.copy()
    df_analysis['price_change'] = df_analysis['closed_price'].diff()
    df_analysis['price_change_pct'] = (df_analysis['price_change'] / df_analysis['closed_price'].shift()) * 100
    
    # Distribution chart
    fig = px.histogram(
        df_analysis[df_analysis['price_change'].notna()],
        x='price_change',
        nbins=30,
        title='Distribution of Daily Price Changes',
        labels={'price_change': 'Price Change (USD)'},
        color_discrete_sequence=['#1f77b4']
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # Summary
    positive_days = (df_analysis['price_change'] > 0).sum()
    negative_days = (df_analysis['price_change'] < 0).sum()
    neutral_days = (df_analysis['price_change'] == 0).sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Up Days", f"{positive_days} ({positive_days/len(df_analysis)*100:.1f}%)")
    
    with col2:
        st.metric("Down Days", f"{negative_days} ({negative_days/len(df_analysis)*100:.1f}%)")
    
    with col3:
        st.metric("Neutral Days", f"{neutral_days} ({neutral_days/len(df_analysis)*100:.1f}%)")

# Footer
st.divider()
st.markdown("""
**Data Information:**
- Last Update: """ + df['date'].max().strftime('%Y-%m-%d') + """
- Total Records: """ + str(len(df)) + """
- Date Range: """ + df['date'].min().strftime('%Y-%m-%d') + """ to """ + df['date'].max().strftime('%Y-%m-%d') + """
""")
