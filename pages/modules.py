import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Modules Overview",
    page_icon="🔧",
    layout="wide"
)

def main():
    st.title("🔧 Modules Overview")
    st.markdown("---")
    
    st.markdown("""
    This page provides an overview of all available modules in the Environmental Analysis App. 
    Each module contains specialized functions for different aspects of environmental data analysis.
    """)
    
    # Module overview cards
    st.subheader("📦 Available Modules")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📊 Data Processing Module
        
        **Purpose:** Handles data validation, loading, and preprocessing
        
        **Key Functions:**
        - `validate_geospatial_data()` - Validate GeoJSON/Shapefile uploads
        - `process_temperature_data()` - Clean temperature datasets
        - `load_lst_data()` - Load LST raster data
        - `handle_file_upload()` - Generic file validation
        - `create_sample_temperature_data()` - Generate demo data
        
        **Supported Formats:**
        - CSV, Excel files
        - GeoJSON files
        - TIFF raster data
        """)
    
    with col2:
        st.markdown("""
        ### 📈 Visualization Module
        
        **Purpose:** Creates interactive maps, charts, and visualizations
        
        **Key Functions:**
        - `create_temperature_map()` - Interactive temperature maps
        - `plot_time_series()` - Time series charts
        - `generate_impact_charts()` - Impact assessment plots
        - `create_correlation_plot()` - Correlation analysis
        - `style_folium_map()` - Map styling
        
        **Technologies:**
        - Folium for interactive maps
        - Plotly for charts
        - Matplotlib for static plots
        """)
    
    with col3:
        st.markdown("""
        ### 🧮 Calculations Module
        
        **Purpose:** Environmental calculations and analysis algorithms
        
        **Key Functions:**
        - `calculate_heat_island_intensity()` - Heat island metrics
        - `assess_cooling_effect()` - Green space cooling impact
        - `compute_building_score()` - Environmental scoring
        - `statistical_analysis()` - Statistical calculations
        - `vegetation_index_calculation()` - NDVI and other indices
        
        **Applications:**
        - Environmental impact scoring
        - Climate analysis
        - Sustainability metrics
        """)
    
    st.markdown("---")
    
    # Interactive demo section
    st.subheader("🧪 Module Demo")
    
    demo_type = st.selectbox(
        "Select Demo Type",
        ["Environmental Score Calculator", "Temperature Data Generator", "Visualization Demo"]
    )
    
    if demo_type == "Environmental Score Calculator":
        st.markdown("### Building Environmental Score Calculator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Building Characteristics:**")
            building_age = st.slider("Building Age (years)", 0, 50, 15)
            building_size = st.slider("Building Size (m²)", 500, 10000, 2000)
            insulation_rating = st.slider("Insulation Rating (1-5)", 1, 5, 3)
            energy_source = st.selectbox("Energy Source", ["Grid", "Solar", "Mixed"])
            green_features = st.slider("Green Features (0-5)", 0, 5, 2)
        
        with col2:
            # Calculate environmental score
            score = 100  # Start with perfect score
            
            # Age factor
            if building_age > 30:
                score -= 20
            elif building_age > 15:
                score -= 10
            
            # Size factor
            if building_size > 5000:
                score -= 15
            elif building_size > 2000:
                score -= 8
            
            # Insulation factor
            score += (insulation_rating - 3) * 10
            
            # Energy source factor
            if energy_source == "Solar":
                score += 15
            elif energy_source == "Mixed":
                score += 8
            
            # Green features
            score += green_features * 5
            
            # Ensure score is between 0 and 100
            final_score = max(0, min(100, score))
            
            st.markdown("**Environmental Score:**")
            
            # Create gauge chart
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = final_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Environmental Score"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            # Score interpretation
            if final_score >= 80:
                st.success(f"🌟 Excellent Score: {final_score}/100")
            elif final_score >= 60:
                st.warning(f"⚠️ Good Score: {final_score}/100")
            else:
                st.error(f"❌ Needs Improvement: {final_score}/100")
    
    elif demo_type == "Temperature Data Generator":
        st.markdown("### Sample Temperature Data Generation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date", value=pd.to_datetime("2024-01-01"))
            end_date = st.date_input("End Date", value=pd.to_datetime("2024-03-31"))
            base_temp = st.slider("Base Temperature (°C)", 15, 35, 25)
            
            if st.button("Generate Sample Data"):
                # Generate sample data
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                seasonal_variation = 5 * np.sin(2 * np.pi * np.arange(len(dates)) / 365)
                daily_variation = np.random.normal(0, 2, len(dates))
                temperatures = base_temp + seasonal_variation + daily_variation
                
                sample_data = pd.DataFrame({
                    'date': dates,
                    'temperature': temperatures,
                    'location': [f"Point_{i%5}" for i in range(len(dates))]
                })
                
                st.session_state.demo_data = sample_data
                st.success(f"Generated {len(sample_data)} temperature records!")
        
        with col2:
            if 'demo_data' in st.session_state:
                st.markdown("**Generated Data Preview:**")
                st.dataframe(st.session_state.demo_data.head(10), use_container_width=True)
                
                st.markdown("**Temperature Statistics:**")
                temp_stats = st.session_state.demo_data['temperature'].describe()
                st.write(temp_stats)
    
    elif demo_type == "Visualization Demo":
        st.markdown("### Interactive Chart Generation")
        
        # Generate sample data for visualization
        sample_data = pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            'temperature': [22, 24, 27, 29, 31, 33, 35, 34, 30, 28, 25, 23],
            'green_coverage': [15, 18, 22, 25, 28, 30, 32, 30, 26, 22, 18, 16]
        })
        
        chart_type = st.selectbox("Chart Type", ["Line Chart", "Bar Chart", "Scatter Plot", "Area Chart"])
        
        if chart_type == "Line Chart":
            fig = px.line(sample_data, x='month', y='temperature', 
                         title="Monthly Temperature Trend", markers=True)
        elif chart_type == "Bar Chart":
            fig = px.bar(sample_data, x='month', y='green_coverage',
                        title="Green Coverage by Month", color='green_coverage')
        elif chart_type == "Scatter Plot":
            fig = px.scatter(sample_data, x='green_coverage', y='temperature',
                           title="Temperature vs Green Coverage", size='temperature')
        else:  # Area Chart
            fig = px.area(sample_data, x='month', y='temperature',
                         title="Temperature Area Chart")
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Usage examples
    st.subheader("💡 Code Examples")
    
    example_col1, example_col2, example_col3 = st.columns(3)
    
    with example_col1:
        st.markdown("""
        ### 📊 Data Processing Example
        ```python
        from utils.data_processing import process_temperature_data
        
        # Process uploaded temperature file
        is_valid, message, df = process_temperature_data(uploaded_file)
        
        if is_valid:
            st.success(message)
            st.dataframe(df)
        else:
            st.error(message)
        ```
        """)
    
    with example_col2:
        st.markdown("""
        ### 📈 Visualization Example
        ```python
        from utils.visualization import plot_time_series
        
        # Create time series plot
        fig = plot_time_series(
            df=temperature_data,
            date_col='date',
            value_col='temperature',
            title='Temperature Trends'
        )
        
        st.plotly_chart(fig)
        ```
        """)
    
    with example_col3:
        st.markdown("""
        ### 🧮 Calculations Example
        ```python
        from utils.calculations import compute_building_score
        
        # Calculate building score
        characteristics = {
            'age': 15,
            'size_sqm': 2000,
            'insulation_rating': 4,
            'energy_source': 'solar'
        }
        
        score = compute_building_score(characteristics)
        st.metric("Score", f"{score}/100")
        ```
        """)
    
    st.markdown("---")
    
    # Module status
    st.subheader("📋 Module Status")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.success("✅ **Data Processing Module**\nFully implemented and tested")
    
    with status_col2:
        st.success("✅ **Visualization Module**\nFully implemented and tested")
    
    with status_col3:
        st.info("🔧 **Calculations Module**\nIn development - basic functions available")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>Modules Overview</strong> | Environmental Analysis App | 🔧 Modular Architecture</p>
        <p>Each module is designed to be reusable and extensible for various environmental analysis tasks</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()