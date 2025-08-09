import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64

# Page configuration
st.set_page_config(
    page_title="EcoVision Analytics",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def create_sample_dashboard_data():
    """Create sample data for dashboard overview"""
    # Sample temperature data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    temperatures = 25 + 5 * np.sin(2 * np.pi * np.arange(len(dates)) / 365) + np.random.normal(0, 2, len(dates))
    
    temp_data = pd.DataFrame({
        'date': dates,
        'temperature': temperatures
    })
    
    # Sample green space data
    green_spaces = [
        {"name": "Central Park", "area": 15.2, "cooling_effect": 3.2, "type": "Urban Park"},
        {"name": "Riverside Gardens", "area": 8.7, "cooling_effect": 4.1, "type": "Botanical Garden"},
        {"name": "Community Forest", "area": 25.6, "cooling_effect": 5.3, "type": "Forest"}
    ]
    
    # Sample building data
    buildings = [
        {"name": "Green Office Tower", "score": 85, "efficiency": 45, "type": "Office"},
        {"name": "Legacy Commercial", "score": 62, "efficiency": 78, "type": "Commercial"},
        {"name": "Eco Residential", "score": 78, "efficiency": 52, "type": "Residential"},
        {"name": "Industrial Warehouse", "score": 58, "efficiency": 95, "type": "Industrial"}
    ]
    
    return temp_data, green_spaces, buildings

def create_gradient_background():
    """Create a beautiful gradient background with environmental theme"""
    background_css = """
    <style>
    .main-header {
        background: linear-gradient(135deg, 
            #667eea 0%, 
            #764ba2 25%, 
            #f093fb 50%, 
            #f5576c 75%, 
            #4facfe 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        padding: 4rem 2rem;
        border-radius: 20px;
        margin: -1rem -1rem 2rem -1rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.3;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .app-title {
        font-size: 4rem;
        font-weight: 800;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 1rem;
        position: relative;
        z-index: 2;
    }
    
    .app-subtitle {
        font-size: 1.4rem;
        color: rgba(255,255,255,0.95);
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        line-height: 1.6;
        max-width: 800px;
        margin: 0 auto;
        position: relative;
        z-index: 2;
    }
    
    .feature-card {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    .stats-container {
        background: rgba(255,255,255,0.9);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .nav-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 1rem;
    }
    
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    </style>
    """
    return background_css

def main():
    # Apply custom CSS
    st.markdown(create_gradient_background(), unsafe_allow_html=True)
    
    # Main header with gradient background
    st.markdown("""
    <div class="main-header">
        <h1 class="app-title">🌍 EcoVision Analytics</h1>
        <p class="app-subtitle">
            Advanced environmental intelligence platform powered by satellite data and AI.<br>
            Transform urban planning with real-time temperature analysis, green space optimization, and building sustainability assessment.<br>
            Make data-driven decisions for a sustainable future.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick stats section with enhanced styling
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    st.markdown("### 📊 Real-Time Environmental Insights")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🌡️ Surface Temperature",
            value="32.4°C",
            delta="↑ 1.8°C heat island detected"
        )
    
    with col2:
        st.metric(
            label="🌳 Green Coverage",
            value="24.7%",
            delta="↑ 2.3% expansion needed"
        )
    
    with col3:
        st.metric(
            label="🏢 Buildings Analyzed",
            value="1,247",
            delta="↑ 89 new assessments"
        )
    
    with col4:
        st.metric(
            label="💡 Sustainability Score",
            value="78/100",
            delta="↑ 6 points improved"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Main dashboard content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🌡️ Temperature Trends")
        
        # Create sample temperature trend
        temp_data, _, _ = create_sample_dashboard_data()
        
        # Monthly aggregation for cleaner visualization
        temp_data['month'] = temp_data['date'].dt.to_period('M')
        monthly_temp = temp_data.groupby('month')['temperature'].mean().reset_index()
        monthly_temp['month'] = monthly_temp['month'].astype(str)
        
        fig_temp = px.line(
            monthly_temp, 
            x='month', 
            y='temperature',
            title="Monthly Average Temperature Trends",
            markers=True
        )
        fig_temp.update_xaxes(title="Month")
        fig_temp.update_yaxes(title="Temperature (°C)")
        fig_temp.update_layout(height=400)
        
        st.plotly_chart(fig_temp, use_container_width=True)
    
    with col2:
        st.subheader("🌳 Green Space Distribution")
        
        _, green_spaces, _ = create_sample_dashboard_data()
        green_df = pd.DataFrame(green_spaces)
        
        fig_green = px.pie(
            green_df,
            values='area',
            names='type',
            title="Green Space Area by Type"
        )
        fig_green.update_layout(height=400)
        
        st.plotly_chart(fig_green, use_container_width=True)
    
    # Second row of visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Building Performance")
        
        _, _, buildings = create_sample_dashboard_data()
        building_df = pd.DataFrame(buildings)
        
        fig_building = px.scatter(
            building_df,
            x='efficiency',
            y='score',
            color='type',
            size=[20, 25, 22, 28],  # Different sizes for visual appeal
            title="Environmental Score vs Energy Efficiency",
            hover_data=['name']
        )
        fig_building.update_xaxes(title="Energy Efficiency (kWh/m²)")
        fig_building.update_yaxes(title="Environmental Score")
        fig_building.update_layout(height=400)
        
        st.plotly_chart(fig_building, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Performance Summary")
        
        # Performance indicators
        performance_data = {
            'Category': ['Temperature Control', 'Green Coverage', 'Building Efficiency', 'Overall Impact'],
            'Score': [75, 82, 68, 74],
            'Target': [80, 85, 75, 80]
        }
        
        perf_df = pd.DataFrame(performance_data)
        
        fig_perf = go.Figure()
        
        fig_perf.add_trace(go.Bar(
            name='Current Score',
            x=perf_df['Category'],
            y=perf_df['Score'],
            marker_color='lightblue'
        ))
        
        fig_perf.add_trace(go.Bar(
            name='Target',
            x=perf_df['Category'],
            y=perf_df['Target'],
            marker_color='darkblue',
            opacity=0.6
        ))
        
        fig_perf.update_layout(
            title="Performance vs Targets",
            yaxis_title="Score",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig_perf, use_container_width=True)
    
    st.markdown("---")
    
    # Enhanced navigation with feature cards
    st.markdown("### 🚀 Explore Our AI-Powered Analysis Tools")
    st.markdown("<br>", unsafe_allow_html=True)
    
    nav_col1, nav_col2, nav_col3 = st.columns(3, gap="large")
    
    with nav_col1:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🌡️</span>
            <h3>Temperature Intelligence</h3>
            <p><strong>Satellite-powered heat analysis</strong></p>
            <ul>
                <li>🛰️ Real-time LST satellite data processing</li>
                <li>🔥 Urban heat island detection</li>
                <li>📊 Interactive temperature mapping</li>
                <li>🤖 AI-powered pattern recognition</li>
            </ul>
            <p><em>Upload TIFF files or CSV temperature data</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🌡️ Analyze Temperature Patterns", key="temp_btn", use_container_width=True):
            st.switch_page("pages/1_Temperature_Analysis.py")
    
    with nav_col2:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🌳</span>
            <h3>Green Space Optimization</h3>
            <p><strong>Vegetation impact assessment</strong></p>
            <ul>
                <li>🍃 Cooling effect quantification</li>
                <li>🗺️ Boundary analysis & mapping</li>
                <li>📈 Environmental benefit calculation</li>
                <li>🎯 Strategic placement recommendations</li>
            </ul>
            <p><em>Import GeoJSON boundaries & vegetation data</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🌳 Optimize Green Spaces", key="green_btn", use_container_width=True):
            st.switch_page("pages/2_Green_Space_Impact.py")
    
    with nav_col3:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🏢</span>
            <h3>Smart Building Assessment</h3>
            <p><strong>Sustainability & efficiency analysis</strong></p>
            <ul>
                <li>📋 Development plan upload & analysis</li>
                <li>⚡ Energy efficiency scoring</li>
                <li>🎯 AI-generated recommendations</li>
                <li>📊 Comparative performance analysis</li>
            </ul>
            <p><em>Upload plans in PDF, Excel, Word formats</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏢 Assess Building Impact", key="building_btn", use_container_width=True):
            st.switch_page("pages/3_Building_Impact.py")
    
    # Enhanced data status section
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    st.markdown("### 📋 System Status & Capabilities")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.markdown("""
        **🛰️ Satellite Data Integration**
        - ✅ Kilimani LST data loaded
        - ✅ Real-time processing ready
        - ✅ AI analysis engine active
        """)
    
    with status_col2:
        st.markdown("""
        **🤖 AI Analysis Capabilities**
        - ✅ Pattern recognition active
        - ✅ Recommendation engine ready
        - ✅ Multi-format file processing
        """)
    
    with status_col3:
        st.markdown("""
        **📊 Visualization Tools**
        - ✅ Interactive mapping ready
        - ✅ Real-time charts active
        - ✅ Export functionality enabled
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced footer with environmental theme
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 2rem; border-radius: 15px; margin-top: 2rem;'>
        <h3>🌍 EcoVision Analytics</h3>
        <p style='font-size: 1.1rem; margin: 1rem 0;'>Empowering sustainable urban development through advanced environmental intelligence</p>
        <p style='opacity: 0.9;'>Built with ❤️ using Streamlit | Powered by AI & Satellite Technology</p>
        <p style='opacity: 0.8; font-size: 0.9rem;'>🌱 Making cities greener, smarter, and more sustainable</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()