"""
Visualization utilities for environmental analysis
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from folium import plugins
import streamlit as st
from typing import Optional, Dict, List, Tuple, Any
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

def create_temperature_map(data: np.ndarray, bounds: Any, center_coords: Optional[Tuple[float, float]] = None) -> folium.Map:
    """
    Generate interactive temperature maps using Folium
    
    Args:
        data: Temperature data array
        bounds: Raster bounds object
        center_coords: Optional center coordinates (lat, lon)
        
    Returns:
        Folium map object
    """
    try:
        # Calculate center coordinates if not provided
        if center_coords is None:
            center_lat = (bounds.bottom + bounds.top) / 2
            center_lon = (bounds.left + bounds.right) / 2
        else:
            center_lat, center_lon = center_coords
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Add temperature data overlay
        if data is not None and bounds is not None:
            # Create temperature overlay rectangle (simplified visualization)
            folium.Rectangle(
                bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
                popup=f"Temperature Data Coverage<br>Min: {np.nanmin(data):.1f}°C<br>Max: {np.nanmax(data):.1f}°C",
                tooltip="LST Data Area",
                color="red",
                weight=2,
                fill=True,
                fillColor="orange",
                fillOpacity=0.4
            ).add_to(m)
        
        # Add temperature legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Temperature Scale</b></p>
        <p><i class="fa fa-circle" style="color:blue"></i> Cold (&lt;20°C)</p>
        <p><i class="fa fa-circle" style="color:green"></i> Moderate (20-30°C)</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Warm (30-35°C)</p>
        <p><i class="fa fa-circle" style="color:red"></i> Hot (&gt;35°C)</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m
        
    except Exception as e:
        st.error(f"Error creating temperature map: {str(e)}")
        return folium.Map(location=[0, 0], zoom_start=2)

def create_temperature_points_map(df: pd.DataFrame, lat_col: str = 'latitude', lon_col: str = 'longitude', temp_col: str = 'temperature') -> folium.Map:
    """
    Create map with temperature points from DataFrame
    
    Args:
        df: DataFrame with temperature data
        lat_col: Column name for latitude
        lon_col: Column name for longitude  
        temp_col: Column name for temperature
        
    Returns:
        Folium map object
    """
    try:
        if df.empty or lat_col not in df.columns or lon_col not in df.columns or temp_col not in df.columns:
            return folium.Map(location=[0, 0], zoom_start=2)
        
        # Calculate center
        center_lat = df[lat_col].mean()
        center_lon = df[lon_col].mean()
        
        # Create map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Add temperature points
        for idx, row in df.iterrows():
            temp = row[temp_col]
            
            # Color based on temperature
            if temp < 20:
                color = 'blue'
            elif temp < 25:
                color = 'green'
            elif temp < 30:
                color = 'orange'
            else:
                color = 'red'
            
            folium.CircleMarker(
                location=[row[lat_col], row[lon_col]],
                radius=6,
                popup=f"Temperature: {temp:.1f}°C",
                tooltip=f"{temp:.1f}°C",
                color='white',
                weight=1,
                fill=True,
                fillColor=color,
                fillOpacity=0.8
            ).add_to(m)
        
        return m
        
    except Exception as e:
        st.error(f"Error creating temperature points map: {str(e)}")
        return folium.Map(location=[0, 0], zoom_start=2)

def plot_time_series(df: pd.DataFrame, date_col: str, value_col: str, title: str = "Time Series") -> go.Figure:
    """
    Create time series visualizations using Plotly
    
    Args:
        df: DataFrame with time series data
        date_col: Column name for dates
        value_col: Column name for values
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    try:
        fig = go.Figure()
        
        # Add main time series line
        fig.add_trace(go.Scatter(
            x=df[date_col],
            y=df[value_col],
            mode='lines',
            name=value_col.title(),
            line=dict(color='blue', width=2),
            hovertemplate='<b>%{x}</b><br>%{y:.1f}<extra></extra>'
        ))
        
        # Add trend line if enough data points
        if len(df) > 10:
            z = np.polyfit(range(len(df)), df[value_col], 1)
            trend_line = np.poly1d(z)(range(len(df)))
            
            fig.add_trace(go.Scatter(
                x=df[date_col],
                y=trend_line,
                mode='lines',
                name='Trend',
                line=dict(color='red', width=2, dash='dash'),
                hovertemplate='<b>Trend</b><br>%{y:.1f}<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title=value_col.title(),
            hovermode='x unified',
            showlegend=True,
            height=400
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating time series plot: {str(e)}")
        return go.Figure()

def generate_impact_charts(data: Dict[str, Any], chart_type: str = "comparison") -> go.Figure:
    """
    Create impact assessment charts
    
    Args:
        data: Dictionary containing impact data
        chart_type: Type of chart to generate
        
    Returns:
        Plotly figure object
    """
    try:
        if chart_type == "comparison":
            # Before/After comparison chart
            scenarios = list(data.keys())
            values = list(data.values())
            
            fig = go.Figure(data=[
                go.Bar(
                    x=scenarios,
                    y=values,
                    marker_color=['red' if 'before' in s.lower() else 'green' for s in scenarios],
                    text=[f"{v:.1f}" for v in values],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="Impact Comparison",
                yaxis_title="Impact Value",
                showlegend=False,
                height=400
            )
            
        elif chart_type == "gauge":
            # Gauge chart for single metric
            value = list(data.values())[0] if data else 0
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': list(data.keys())[0] if data else "Metric"},
                gauge={
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
            
        else:
            fig = go.Figure()
            
        return fig
        
    except Exception as e:
        st.error(f"Error creating impact chart: {str(e)}")
        return go.Figure()

def style_folium_map(m: folium.Map, style_type: str = "default") -> folium.Map:
    """
    Apply consistent map styling
    
    Args:
        m: Folium map object
        style_type: Style type to apply
        
    Returns:
        Styled Folium map object
    """
    try:
        if style_type == "environmental":
            # Add environmental-themed tile layers
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Satellite',
                overlay=False,
                control=True
            ).add_to(m)
            
        elif style_type == "terrain":
            folium.TileLayer(
                tiles='https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png',
                attr='Map tiles by Stamen Design, CC BY 3.0 — Map data © OpenStreetMap contributors',
                name='Terrain',
                overlay=False,
                control=True
            ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add fullscreen button
        plugins.Fullscreen().add_to(m)
        
        # Add measure control
        plugins.MeasureControl().add_to(m)
        
        return m
        
    except Exception as e:
        st.error(f"Error styling map: {str(e)}")
        return m

def create_correlation_plot(df: pd.DataFrame, x_col: str, y_col: str, title: str = "Correlation Analysis") -> go.Figure:
    """
    Create correlation scatter plot with trend line
    
    Args:
        df: DataFrame with data
        x_col: X-axis column name
        y_col: Y-axis column name
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    try:
        fig = px.scatter(
            df, x=x_col, y=y_col,
            trendline="ols",
            title=title,
            labels={x_col: x_col.replace('_', ' ').title(), y_col: y_col.replace('_', ' ').title()}
        )
        
        # Calculate correlation coefficient
        correlation = df[x_col].corr(df[y_col])
        
        # Add correlation annotation
        fig.add_annotation(
            x=0.05, y=0.95,
            xref="paper", yref="paper",
            text=f"Correlation: {correlation:.3f}",
            showarrow=False,
            bgcolor="white",
            bordercolor="black",
            borderwidth=1
        )
        
        fig.update_layout(height=400)
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating correlation plot: {str(e)}")
        return go.Figure()

def create_heatmap(data: np.ndarray, title: str = "Heatmap") -> go.Figure:
    """
    Create heatmap visualization
    
    Args:
        data: 2D numpy array
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    try:
        fig = go.Figure(data=go.Heatmap(
            z=data,
            colorscale='RdYlBu_r',
            showscale=True
        ))
        
        fig.update_layout(
            title=title,
            height=400
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating heatmap: {str(e)}")
        return go.Figure()

def create_distribution_plot(df: pd.DataFrame, column: str, title: str = "Distribution") -> go.Figure:
    """
    Create distribution plot (histogram with density curve)
    
    Args:
        df: DataFrame with data
        column: Column name to plot
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    try:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add histogram
        fig.add_trace(
            go.Histogram(
                x=df[column],
                name="Frequency",
                nbinsx=30,
                opacity=0.7
            ),
            secondary_y=False,
        )
        
        # Add density curve
        hist, bin_edges = np.histogram(df[column], bins=30, density=True)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        fig.add_trace(
            go.Scatter(
                x=bin_centers,
                y=hist,
                mode='lines',
                name="Density",
                line=dict(color='red', width=2)
            ),
            secondary_y=True,
        )
        
        # Update layout
        fig.update_xaxes(title_text=column.replace('_', ' ').title())
        fig.update_yaxes(title_text="Frequency", secondary_y=False)
        fig.update_yaxes(title_text="Density", secondary_y=True)
        fig.update_layout(title=title, height=400)
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating distribution plot: {str(e)}")
        return go.Figure()

def export_plot_as_html(fig: go.Figure, filename: str) -> str:
    """
    Export Plotly figure as HTML string
    
    Args:
        fig: Plotly figure object
        filename: Name for the exported file
        
    Returns:
        HTML string
    """
    try:
        return fig.to_html(include_plotlyjs='cdn')
    except Exception as e:
        st.error(f"Error exporting plot: {str(e)}")
        return ""