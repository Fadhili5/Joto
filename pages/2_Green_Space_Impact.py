import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
from shapely.geometry import Point, Polygon
import json

# Page configuration
st.set_page_config(
    page_title="Green Space Impact",
    page_icon="🌳",
    layout="wide"
)

def create_sample_green_spaces():
    """Create sample green space data for demonstration"""
    # Sample green space polygons (simplified coordinates)
    green_spaces = [
        {
            "name": "Central Park",
            "type": "Urban Park",
            "area_ha": 15.2,
            "vegetation_index": 0.75,
            "cooling_effect": 3.2,
            "coordinates": [[-1.2921, 36.8219], [-1.2901, 36.8219], [-1.2901, 36.8239], [-1.2921, 36.8239]]
        },
        {
            "name": "Riverside Gardens",
            "type": "Botanical Garden", 
            "area_ha": 8.7,
            "vegetation_index": 0.82,
            "cooling_effect": 4.1,
            "coordinates": [[-1.2941, 36.8199], [-1.2931, 36.8199], [-1.2931, 36.8209], [-1.2941, 36.8209]]
        },
        {
            "name": "Community Forest",
            "type": "Forest",
            "area_ha": 25.6,
            "vegetation_index": 0.88,
            "cooling_effect": 5.3,
            "coordinates": [[-1.2961, 36.8179], [-1.2941, 36.8179], [-1.2941, 36.8199], [-1.2961, 36.8199]]
        }
    ]
    return green_spaces

def create_green_space_map(green_spaces):
    """Create interactive map showing green spaces"""
    # Center map on Nairobi (approximate)
    m = folium.Map(
        location=[-1.2921, 36.8219],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Color mapping for different green space types
    type_colors = {
        "Urban Park": "green",
        "Botanical Garden": "darkgreen", 
        "Forest": "forestgreen"
    }
    
    for space in green_spaces:
        # Create polygon for green space
        coords = [[coord[0], coord[1]] for coord in space["coordinates"]]
        coords.append(coords[0])  # Close the polygon
        
        folium.Polygon(
            locations=coords,
            popup=f"""
            <b>{space['name']}</b><br>
            Type: {space['type']}<br>
            Area: {space['area_ha']} ha<br>
            Vegetation Index: {space['vegetation_index']}<br>
            Cooling Effect: {space['cooling_effect']}°C
            """,
            tooltip=space['name'],
            color=type_colors.get(space['type'], 'green'),
            weight=2,
            fill=True,
            fillColor=type_colors.get(space['type'], 'green'),
            fillOpacity=0.6
        ).add_to(m)
        
        # Add center marker
        center_lat = sum([coord[0] for coord in space["coordinates"]]) / len(space["coordinates"])
        center_lon = sum([coord[1] for coord in space["coordinates"]]) / len(space["coordinates"])
        
        folium.CircleMarker(
            location=[center_lat, center_lon],
            radius=5,
            popup=f"{space['name']}: {space['cooling_effect']}°C cooling",
            color='white',
            fill=True,
            fillColor=type_colors.get(space['type'], 'green'),
            fillOpacity=0.8
        ).add_to(m)
    
    return m

def generate_correlation_data():
    """Generate sample correlation data between vegetation and temperature"""
    np.random.seed(42)
    n_points = 100
    
    vegetation_index = np.random.uniform(0.1, 0.9, n_points)
    # Negative correlation: higher vegetation = lower temperature
    temperature = 35 - (vegetation_index * 10) + np.random.normal(0, 2, n_points)
    
    return pd.DataFrame({
        'vegetation_index': vegetation_index,
        'temperature': temperature,
        'cooling_effect': (0.9 - vegetation_index) * 8 + np.random.normal(0, 0.5, n_points)
    })

def main():
    st.title("🌳 Green Space Impact Analysis")
    st.markdown("---")
    
    # Sidebar controls
    st.sidebar.header("Analysis Controls")
    
    analysis_type = st.sidebar.selectbox(
        "Select Analysis Type",
        ["Green Space Overview", "Cooling Effect Analysis", "Vegetation Correlation", "Impact Comparison"]
    )
    
    # Main content area
    if analysis_type == "Green Space Overview":
        st.header("Green Space Distribution and Characteristics")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Green Space Map")
            
            # Create and display green space map
            green_spaces = create_sample_green_spaces()
            green_map = create_green_space_map(green_spaces)
            map_data = st_folium(green_map, width=700, height=500)
        
        with col2:
            st.subheader("Green Space Summary")
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(green_spaces)
            
            # Summary metrics
            total_area = df['area_ha'].sum()
            avg_vegetation = df['vegetation_index'].mean()
            avg_cooling = df['cooling_effect'].mean()
            
            st.metric("Total Green Area", f"{total_area:.1f} ha")
            st.metric("Avg Vegetation Index", f"{avg_vegetation:.2f}")
            st.metric("Avg Cooling Effect", f"{avg_cooling:.1f}°C")
            
            # Green space types
            st.subheader("Green Space Types")
            type_counts = df['type'].value_counts()
            fig = px.pie(values=type_counts.values, names=type_counts.index,
                        title="Distribution by Type")
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("Green Space Details")
        display_df = df[['name', 'type', 'area_ha', 'vegetation_index', 'cooling_effect']]
        st.dataframe(display_df, use_container_width=True)
    
    elif analysis_type == "Cooling Effect Analysis":
        st.header("Green Space Cooling Effect Analysis")
        
        green_spaces = create_sample_green_spaces()
        df = pd.DataFrame(green_spaces)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Cooling Effect by Area")
            
            fig = px.scatter(df, x='area_ha', y='cooling_effect', 
                           color='type', size='vegetation_index',
                           title="Cooling Effect vs Green Space Area",
                           hover_data=['name'])
            fig.update_xaxis(title="Area (hectares)")
            fig.update_yaxis(title="Cooling Effect (°C)")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Vegetation Index Impact")
            
            fig = px.scatter(df, x='vegetation_index', y='cooling_effect',
                           color='type', size='area_ha',
                           title="Cooling Effect vs Vegetation Index",
                           hover_data=['name'])
            fig.update_xaxis(title="Vegetation Index")
            fig.update_yaxis(title="Cooling Effect (°C)")
            st.plotly_chart(fig, use_container_width=True)
        
        # Cooling effectiveness analysis
        st.subheader("Cooling Effectiveness Analysis")
        
        # Calculate cooling per hectare
        df['cooling_per_ha'] = df['cooling_effect'] / df['area_ha']
        
        effectiveness_col1, effectiveness_col2, effectiveness_col3 = st.columns(3)
        
        with effectiveness_col1:
            st.metric("Most Effective", 
                     df.loc[df['cooling_per_ha'].idxmax(), 'name'],
                     f"{df['cooling_per_ha'].max():.2f}°C/ha")
        
        with effectiveness_col2:
            st.metric("Largest Impact", 
                     df.loc[df['cooling_effect'].idxmax(), 'name'],
                     f"{df['cooling_effect'].max():.1f}°C")
        
        with effectiveness_col3:
            st.metric("Best Vegetation", 
                     df.loc[df['vegetation_index'].idxmax(), 'name'],
                     f"{df['vegetation_index'].max():.2f}")
    
    elif analysis_type == "Vegetation Correlation":
        st.header("Vegetation-Temperature Correlation Analysis")
        
        # Generate correlation data
        corr_data = generate_correlation_data()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Vegetation vs Temperature")
            
            fig = px.scatter(corr_data, x='vegetation_index', y='temperature',
                           trendline="ols",
                           title="Temperature vs Vegetation Index",
                           labels={'vegetation_index': 'Vegetation Index',
                                  'temperature': 'Temperature (°C)'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate correlation
            correlation = corr_data['vegetation_index'].corr(corr_data['temperature'])
            st.metric("Correlation Coefficient", f"{correlation:.3f}")
        
        with col2:
            st.subheader("Cooling Effect Distribution")
            
            fig = px.histogram(corr_data, x='cooling_effect', nbins=20,
                             title="Distribution of Cooling Effects")
            fig.update_xaxis(title="Cooling Effect (°C)")
            fig.update_yaxis(title="Frequency")
            st.plotly_chart(fig, use_container_width=True)
        
        # Statistical analysis
        st.subheader("Statistical Analysis")
        
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        with stats_col1:
            st.metric("Mean Temperature", f"{corr_data['temperature'].mean():.1f}°C")
        with stats_col2:
            st.metric("Mean Vegetation Index", f"{corr_data['vegetation_index'].mean():.2f}")
        with stats_col3:
            st.metric("Max Cooling Effect", f"{corr_data['cooling_effect'].max():.1f}°C")
        with stats_col4:
            st.metric("Temperature Range", f"{corr_data['temperature'].max() - corr_data['temperature'].min():.1f}°C")
    
    elif analysis_type == "Impact Comparison":
        st.header("Before/After Impact Comparison")
        
        # Scenario comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Scenario Settings")
            
            baseline_temp = st.slider("Baseline Temperature (°C)", 25, 40, 32)
            green_coverage = st.slider("Green Coverage (%)", 0, 100, 30)
            vegetation_quality = st.slider("Vegetation Quality", 0.1, 1.0, 0.6)
            
            # Calculate impact
            cooling_effect = (green_coverage / 100) * vegetation_quality * 8
            final_temp = baseline_temp - cooling_effect
            
            st.metric("Predicted Cooling", f"{cooling_effect:.1f}°C")
            st.metric("Final Temperature", f"{final_temp:.1f}°C")
        
        with col2:
            st.subheader("Impact Visualization")
            
            # Create before/after comparison
            scenarios = ['Before', 'After']
            temperatures = [baseline_temp, final_temp]
            
            fig = go.Figure(data=[
                go.Bar(x=scenarios, y=temperatures, 
                      marker_color=['red', 'green'],
                      text=[f"{temp:.1f}°C" for temp in temperatures],
                      textposition='auto')
            ])
            
            fig.update_layout(
                title="Temperature Before/After Green Space Implementation",
                yaxis_title="Temperature (°C)",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Recommendations
        st.subheader("Recommendations")
        
        if cooling_effect < 2:
            st.warning("⚠️ Low cooling effect. Consider increasing green coverage or vegetation quality.")
        elif cooling_effect < 4:
            st.info("ℹ️ Moderate cooling effect. Good progress, but room for improvement.")
        else:
            st.success("✅ Excellent cooling effect! This green space implementation is highly effective.")
        
        # Action items
        st.subheader("Suggested Actions")
        
        recommendations = []
        if green_coverage < 20:
            recommendations.append("🌱 Increase green space coverage to at least 20%")
        if vegetation_quality < 0.5:
            recommendations.append("🌳 Improve vegetation quality through better species selection")
        if cooling_effect < 3:
            recommendations.append("💧 Consider adding water features to enhance cooling")
        
        if recommendations:
            for rec in recommendations:
                st.write(f"• {rec}")
        else:
            st.success("🎉 Current green space plan is well-optimized!")

if __name__ == "__main__":
    main()