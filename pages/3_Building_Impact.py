import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
import os
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont
import re
import requests
import json
from datetime import datetime

# Azure OpenAI Endpoint Setup
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://gpt-image-1-resource.cognitiveservices.azure.com/")
deployment = os.getenv("DEPLOYMENT_NAME", "FLUX-1.1-pro")
api_version = os.getenv("OPENAI_API_VERSION", "2025-04-01-preview")
api_key = os.getenv("AZURE_OPENAI_API_KEY")

# LST Data for Kilimani (replacing load_lst_prediction_data function)
KILIMANI_LST_DATA = {
    "location": "Kilimani area, Nairobi, Kenya",
    "data_type": "Land Surface Temperature (LST) from satellite imagery",
    "analysis_timestamp": "2025-08-09 08:39:34",
    "statistics": {
        "min_temperature": 31.03,
        "max_temperature": 45.23,
        "mean_temperature": 38.18,
        "median_temperature": 37.87,
        "temperature_range": 14.21,
        "standard_deviation": 2.23,
        "percentile_25": 36.85,
        "percentile_75": 38.79,
        "percentile_90": 41.87,
        "percentile_10": 35.85,
        "hot_pixels_count": 3010,
        "cold_pixels_count": 3010,
        "hot_pixels_percentage": 10.0,
        "cold_pixels_percentage": 10.0,
        "total_pixels": 30096,
        "heat_island_intensity": 7.05,
        "temperature_variability_index": 5.9
    },
    "environmental_insights": {
        "heat_classification": {
            "extreme_hot_threshold": 43.36,
            "very_hot_threshold": 41.87,
            "hot_threshold": 38.79,
            "moderate_range": "36.85°C - 38.79°C",
            "cool_threshold": 36.85,
            "very_cool_threshold": 35.85
        },
        "spatial_distribution": {
            "distribution_shape": "right-skewed",
            "skewness_value": 0.914,
            "kurtosis_value": 4.061,
            "distribution_type": "heavy-tailed",
            "data_concentration": "dispersed"
        },
        "climate_indicators": {
            "uhi_intensity": 14.21,
            "uhi_level": "Very Strong",
            "temperature_stress_level": "Extreme Heat Stress",
            "thermal_comfort_index": "Significant Discomfort",
            "environmental_risk_level": "Moderate Risk"
        }
    }
}

# Inject custom CSS
def inject_css():
    st.markdown("""
    <style>
    .main-header {
        color: #2E86AB;
        text-align: center;
        font-size: 3rem;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        color: #A23B72;
        text-align: center;
        font-size: 1.5rem;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 1rem;
    }
    .metric-container h4 {
        margin-top: 0;
        font-size: 1rem;
        opacity: 0.9;
    }
    .metric-container h2 {
        margin: 0.5rem 0;
        font-size: 2.5rem;
        font-weight: bold;
    }
    .insight-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    .insight-box h4 {
        margin-top: 0;
    }
    .insight-box ul {
        margin-bottom: 0;
    }
    .stExpander {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

inject_css()

# Page configuration
st.set_page_config(
    page_title="Building Impact - Kilimani Heat Island",
    page_icon="🏢",
    layout="wide"
)

# Page header
st.markdown('<h1 class="main-header">🏢 AI-Enhanced Building Impact Analysis</h1>', unsafe_allow_html=True)
st.markdown('<h2 class="sub-header">Kilimani Heat Island Assessment & Document Processing</h2>', unsafe_allow_html=True)

# Function to generate synthetic building data for demonstration
def generate_sample_data():
    """Generate sample building data for analysis"""
    np.random.seed(42)  # For reproducible results
    n_buildings = 150
    
    data = {
        'building_id': range(1, n_buildings + 1),
        'building_density': np.random.uniform(30, 85, n_buildings),
        'building_coverage': np.random.uniform(40, 80, n_buildings),
        'building_height': np.random.randint(3, 25, n_buildings),
        'green_space_ratio': np.random.uniform(5, 35, n_buildings),
        'LST_Prediction': np.random.uniform(
            KILIMANI_LST_DATA['statistics']['min_temperature'],
            KILIMANI_LST_DATA['statistics']['max_temperature'],
            n_buildings
        )
    }
    
    # Add correlation between building density and temperature
    temp_adjustment = (data['building_density'] - 50) * 0.15
    green_adjustment = (data['green_space_ratio'] - 20) * -0.1
    data['LST_Prediction'] = data['LST_Prediction'] + temp_adjustment + green_adjustment
    
    return pd.DataFrame(data)

# Function to request image generation (placeholder - would need actual Azure implementation)
def generate_image_via_azure(prompt):
    """Placeholder for Azure image generation"""
    # This would contain the actual Azure API call
    # For now, we'll return None to avoid errors
    return None

# Document processing functions
def extract_text_from_pdf(pdf_file):
    """Extract text from PDF - placeholder implementation"""
    return f"Sample PDF content from {pdf_file.name}. Building specifications: 15 floors, high density development, 70% coverage, sustainable features include solar panels and green roof systems."

def extract_text_from_docx(docx_file):
    """Extract text from DOCX - placeholder implementation"""
    return f"Sample DOCX content from {docx_file.name}. Commercial building with 12 floors, 65% site coverage, includes parking for 200 vehicles, green building certified."

def extract_text_from_image(image_file):
    """Extract text from image - placeholder implementation"""
    return f"Sample image analysis from {image_file.name}. Architectural plans showing multi-story building with green spaces."

def process_document(uploaded_file):
    """Process uploaded document and extract meaningful content"""
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        return extract_text_from_docx(uploaded_file)
    elif uploaded_file.type.startswith('image/'):
        return extract_text_from_image(uploaded_file)
    else:
        try:
            return uploaded_file.getvalue().decode('utf-8')
        except:
            return f"Content from {uploaded_file.name}"

def analyze_extracted_content(text):
    """AI-powered analysis of extracted text"""
    analysis = {
        'building_density': extract_building_metrics(text),
        'environmental_impact': assess_environmental_factors(text),
        'thermal_impact': calculate_thermal_effects(text),
        'recommendations': generate_recommendations(text)
    }
    return analysis

def extract_building_metrics(text):
    """Extract building-related metrics from text"""
    patterns = {
        'density': re.search(r'building density[:\s]*(\d+(?:\.\d+)?)', text, re.IGNORECASE),
        'coverage': re.search(r'coverage[:\s]*(\d+(?:\.\d+)?)%?', text, re.IGNORECASE),
        'height': re.search(r'(\d+)\s*floors?|(\d+)\s*storeys?', text, re.IGNORECASE),
        'units': re.search(r'(\d+)\s*units', text, re.IGNORECASE)
    }
    
    return {
        'density': float(patterns['density'].group(1)) if patterns['density'] else np.random.uniform(40, 80),
        'coverage': float(patterns['coverage'].group(1)) if patterns['coverage'] else np.random.uniform(50, 75),
        'height': int(patterns['height'].group(1) or patterns['height'].group(2)) if patterns['height'] else np.random.randint(8, 20),
        'units': int(patterns['units'].group(1)) if patterns['units'] else np.random.randint(200, 500)
    }

def assess_environmental_factors(text):
    """Assess environmental impact from text content"""
    green_keywords = ['green roof', 'solar', 'renewable', 'sustainable', 'trees', 'vegetation', 'garden']
    sustainability_score = sum(15 for keyword in green_keywords if keyword.lower() in text.lower())
    base_score = 40
    
    total_score = min(sustainability_score + base_score, 100)
    
    return {
        'sustainability_score': total_score,
        'has_green_features': any(keyword.lower() in text.lower() for keyword in green_keywords),
        'environmental_grade': 'A' if total_score >= 80 else 'B' if total_score >= 60 else 'C'
    }

def calculate_thermal_effects(text):
    """Calculate thermal impact based on content analysis"""
    base_temp = KILIMANI_LST_DATA['statistics']['mean_temperature']
    metrics = extract_building_metrics(text)
    
    # Calculate thermal impact based on building characteristics
    density_factor = (metrics['density'] - 50) * 0.05
    coverage_factor = (metrics['coverage'] - 60) * 0.03
    height_factor = (metrics['height'] - 10) * 0.1
    green_factor = -2.0 if 'green' in text.lower() or 'sustainable' in text.lower() else 0
    
    projected_temp = base_temp + density_factor + coverage_factor + height_factor + green_factor
    projected_temp = max(projected_temp, base_temp - 2)  # Minimum improvement limit
    
    return {
        'current_temp': base_temp,
        'projected_temp': projected_temp,
        'heat_island_intensity': abs(projected_temp - base_temp)
    }

def generate_recommendations(text):
    """Generate AI recommendations based on analysis"""
    recommendations = []
    
    if 'high density' in text.lower() or 'density' in text.lower():
        recommendations.append("Implement green roof systems to reduce heat buildup")
    if 'solar' not in text.lower():
        recommendations.append("Consider solar panel integration for energy efficiency")
    if 'tree' not in text.lower() and 'green' not in text.lower():
        recommendations.append("Increase tree coverage by 30% around the building")
    if 'parking' in text.lower():
        recommendations.append("Use permeable paving materials for parking areas")
    
    recommendations.extend([
        "Use reflective building materials to reduce heat absorption",
        "Create wind corridors to improve air circulation",
        "Implement smart building systems for energy optimization",
        "Install water features for evaporative cooling"
    ])
    
    return recommendations[:5]

def generate_building_plan(building_metrics, filename, canvas_size=(900, 700)):
    """Generate AI-powered building plan visualization"""
    img = Image.new('RGB', canvas_size, color='#f8f9fa')
    draw = ImageDraw.Draw(img)
    
    # Extract metrics
    coverage = building_metrics['coverage']
    height = building_metrics['height']
    density = building_metrics['density']
    
    # Site boundary with modern styling
    margin = 60
    site_width = canvas_size[0] - 2 * margin
    site_height = canvas_size[1] - 2 * margin
    draw.rectangle([margin, margin, canvas_size[0] - margin, canvas_size[1] - margin], 
                   outline='#2c3e50', width=4)
    
    # Building footprint based on coverage
    building_width = int(site_width * (coverage / 100) * 0.8)
    building_height = int(site_height * (coverage / 100) * 0.6)
    
    # Center the building
    building_x = (canvas_size[0] - building_width) // 2
    building_y = (canvas_size[1] - building_height) // 2
    
    # Main building with gradient effect
    building_color = '#3498db' if density < 60 else '#e74c3c'
    draw.rectangle([building_x, building_y, building_x + building_width, building_y + building_height], 
                   fill=building_color, outline='#2c3e50', width=3)
    
    # Add floor divisions
    if height > 1:
        floor_height = building_height // min(height, 15)  # Limit visual floors
        for i in range(1, min(height, 15)):
            y = building_y + i * floor_height
            draw.line([building_x + 5, y, building_x + building_width - 5, y], 
                     fill='#2c3e50', width=1)
    
    # Add windows pattern
    window_rows = min(height, 12)
    window_cols = max(3, building_width // 40)
    window_width = 15
    window_height = 10
    
    for row in range(window_rows):
        for col in range(window_cols):
            if (row + col) % 2 == 0:  # Checkerboard pattern
                wx = building_x + 20 + col * (building_width - 40) // window_cols
                wy = building_y + 15 + row * (building_height - 30) // window_rows
                draw.rectangle([wx, wy, wx + window_width, wy + window_height], 
                             fill='#ecf0f1', outline='#bdc3c7')
    
    # Green spaces
    green_size = 40
    # Multiple green spaces for better aesthetics
    green_positions = [
        (margin + 20, margin + 20),
        (canvas_size[0] - margin - 60, margin + 20),
        (margin + 20, canvas_size[1] - margin - 60),
        (canvas_size[0] - margin - 60, canvas_size[1] - margin - 60)
    ]
    
    for pos in green_positions:
        draw.ellipse([pos[0], pos[1], pos[0] + green_size, pos[1] + green_size], 
                     fill='#27ae60', outline='#229954', width=2)
        # Add smaller trees
        tree_size = 15
        draw.ellipse([pos[0] + 10, pos[1] + 10, pos[0] + 25, pos[1] + 25], 
                     fill='#2ecc71', outline='#27ae60')
    
    # Parking area
    parking_width = min(200, building_width)
    parking_height = 50
    parking_x = building_x + building_width + 30
    parking_y = building_y + building_height - parking_height
    
    if parking_x + parking_width < canvas_size[0] - margin:
        draw.rectangle([parking_x, parking_y, parking_x + parking_width, parking_y + parking_height],
                       fill='#95a5a6', outline='#7f8c8d', width=2)
        
        # Parking lines
        for i in range(0, parking_width, 25):
            draw.line([parking_x + i, parking_y, parking_x + i, parking_y + parking_height],
                     fill='#ecf0f1', width=1)
    
    # Pathways
    pathway_color = '#bdc3c7'
    # Main pathway
    draw.rectangle([building_x + building_width // 2 - 10, margin, 
                    building_x + building_width // 2 + 10, building_y],
                   fill=pathway_color, outline='#95a5a6')
    
    # Add labels with better positioning
    try:
        font = ImageFont.load_default()
        # Title
        title_text = f"Building Plan: {filename[:20]}"
        draw.text((margin + 10, margin - 45), title_text, fill='#2c3e50', font=font)
        
        # Building info
        info_text = f"{height} Floors | {coverage:.1f}% Coverage | {density:.1f}% Density"
        draw.text((building_x, building_y - 25), info_text, fill='#2c3e50', font=font)
        
        # Legend
        legend_y = canvas_size[1] - 50
        draw.text((margin, legend_y), "🏢 Building", fill='#2c3e50', font=font)
        draw.text((margin + 100, legend_y), "🌳 Green Space", fill='#2c3e50', font=font)
        draw.text((margin + 220, legend_y), "🚗 Parking", fill='#2c3e50', font=font)
        
    except:
        pass
    
    return img

# Main Application Layout
st.markdown("### 🌡️ Current Kilimani Heat Island Status")

# Display current LST statistics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-container">
        <h4>🌡️ Mean Temperature</h4>
        <h2>{KILIMANI_LST_DATA['statistics']['mean_temperature']:.1f}°C</h2>
        <p>Current LST average</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-container">
        <h4>🔥 Heat Island Intensity</h4>
        <h2>{KILIMANI_LST_DATA['statistics']['heat_island_intensity']:.1f}°C</h2>
        <p>Temperature variation</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-container">
        <h4>📊 Temperature Range</h4>
        <h2>{KILIMANI_LST_DATA['statistics']['temperature_range']:.1f}°C</h2>
        <p>Min to Max difference</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    uhi_level = KILIMANI_LST_DATA['environmental_insights']['climate_indicators']['uhi_level']
    st.markdown(f"""
    <div class="metric-container">
        <h4>⚠️ UHI Level</h4>
        <h2>{uhi_level}</h2>
        <p>Climate classification</p>
    </div>
    """, unsafe_allow_html=True)

# Document Upload Section
st.markdown("---")
st.markdown("### 📄 Document Processing & Analysis")

uploaded_files = st.file_uploader(
    "Upload building documents (PDF, DOCX, Images, TXT)",
    accept_multiple_files=True,
    type=['pdf', 'docx', 'doc', 'txt', 'jpg', 'jpeg', 'png', 'tiff']
)

extracted_data = {}
if uploaded_files:
    st.markdown("#### 🔍 Document Processing Results")
    
    for uploaded_file in uploaded_files:
        with st.expander(f"📄 {uploaded_file.name}", expanded=True):
            # Extract text content
            extracted_text = process_document(uploaded_file)
            st.text_area("Extracted Content", extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text, height=150, key=f"text_{uploaded_file.name}")
            
            # Analyze content
            analysis = analyze_extracted_content(extracted_text)
            extracted_data[uploaded_file.name] = analysis
            
            # Display analysis results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**🏗 Building Metrics:**")
                st.write(f"• Density: {analysis['building_density']['density']:.1f}%")
                st.write(f"• Coverage: {analysis['building_density']['coverage']:.1f}%")
                st.write(f"• Height: {analysis['building_density']['height']} floors")
                st.write(f"• Units: {analysis['building_density']['units']}")
            
            with col2:
                st.markdown("**🌿 Environmental Assessment:**")
                st.write(f"• Sustainability Score: {analysis['environmental_impact']['sustainability_score']}/100")
                st.write(f"• Environmental Grade: {analysis['environmental_impact']['environmental_grade']}")
                st.write(f"• Green Features: {'Yes' if analysis['environmental_impact']['has_green_features'] else 'No'}")
            
            with col3:
                temp_change = analysis['thermal_impact']['projected_temp'] - analysis['thermal_impact']['current_temp']
                st.markdown("**🌡️ Thermal Impact:**")
                st.write(f"• Current: {analysis['thermal_impact']['current_temp']:.1f}°C")
                st.write(f"• Projected: {analysis['thermal_impact']['projected_temp']:.1f}°C")
                st.write(f"• Change: {temp_change:+.1f}°C")

# AI Plan Generation Section
if extracted_data:
    st.markdown("---")
    st.markdown("### 🎨 AI-Generated Building Plans")
    
    plan_cols = st.columns(min(len(extracted_data), 2))
    
    for idx, (filename, data) in enumerate(extracted_data.items()):
        with plan_cols[idx % 2]:
            st.markdown(f"#### 🏗 Plan for {filename}")
            
            # Generate building plan
            building_plan = generate_building_plan(data['building_density'], filename)
            
            # Convert PIL image to bytes for display
            img_buffer = BytesIO()
            building_plan.save(img_buffer, format='PNG')
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Display the generated plan
            st.markdown(f'<img src="data:image/png;base64,{img_str}" style="max-width: 100%; height: auto; border: 2px solid #ddd; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
            
            # Plan features and recommendations
            with st.expander("📋 Plan Details & Recommendations"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**🏗 Plan Features:**")
                    st.write("• Multi-story building design")
                    st.write("• Integrated green spaces")
                    st.write("• Parking allocation")
                    st.write("• Pedestrian pathways")
                    st.write("• Site boundary compliance")
                
                with col2:
                    st.markdown("**💡 AI Recommendations:**")
                    for rec in data['recommendations'][:5]:
                        st.write(f"• {rec}")

# Enhanced Analysis with Sample Data
st.markdown("---")
st.markdown("### 📊 Comparative Analysis with Kilimani Data")

# Generate sample building data
df = generate_sample_data()

# Temperature distribution
col1, col2 = st.columns(2)

with col1:
    fig_hist = px.histogram(
        x=[KILIMANI_LST_DATA['statistics']['min_temperature'], 
           KILIMANI_LST_DATA['statistics']['mean_temperature'], 
           KILIMANI_LST_DATA['statistics']['max_temperature']],
        nbins=20,
        title='🌡️ Kilimani Temperature Distribution',
        labels={'x': 'Temperature (°C)', 'y': 'Frequency'}
    )
    fig_hist.add_vline(x=KILIMANI_LST_DATA['statistics']['mean_temperature'], 
                       line_dash="dash", line_color="red",
                       annotation_text="Mean Temp")
    fig_hist.update_layout(showlegend=False)
    st.plotly_chart(fig_hist, use_container_width=True)

with col2:
    # Building density impact scatter plot
    fig_scatter = px.scatter(
        df, x='building_density', y='LST_Prediction',
        color='green_space_ratio',
        size='building_height',
        title='🏗️ Building Density vs Temperature',
        labels={
            'building_density': 'Building Density (%)', 
            'LST_Prediction': 'Temperature (°C)',
            'green_space_ratio': 'Green Space %'
        },
        color_continuous_scale='RdYlGn_r'
    )
    
    # Add extracted data points if available
    if extracted_data:
        extracted_densities = [data['building_density']['density'] for data in extracted_data.values()]
        extracted_temps = [data['thermal_impact']['projected_temp'] for data in extracted_data.values()]
        
        fig_scatter.add_scatter(
            x=extracted_densities, y=extracted_temps,
            mode='markers', 
            marker=dict(size=15, color='yellow', symbol='star', line=dict(width=2, color='black')),
            name='Analyzed Documents', showlegend=True
        )
    
    st.plotly_chart(fig_scatter, use_container_width=True)

# Correlation analysis
if len(df) > 0:
    building_corr = df['LST_Prediction'].corr(df['building_density'])
    green_corr = df['LST_Prediction'].corr(df['green_space_ratio'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <h4>📊 Density Correlation</h4>
            <h2>{building_corr:.3f}</h2>
            <p>Building density vs temperature</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <h4>🌿 Green Space Impact</h4>
            <h2>{green_corr:.3f}</h2>
            <p>Green space vs temperature</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if extracted_data:
            avg_projected_increase = np.mean([
                data['thermal_impact']['projected_temp'] - data['thermal_impact']['current_temp'] 
                for data in extracted_data.values()
            ])
            st.markdown(f"""
            <div class="metric-container">
                <h4>🔍 Document Analysis</h4>
                <h2>{avg_projected_increase:+.1f}°C</h2>
                <p>Avg projected change</p>
            </div>
            """, unsafe_allow_html=True)

# Final Recommendations
if extracted_data:
    st.markdown("---")
    st.markdown("### 💡 Comprehensive Recommendations")
    
    all_recommendations = []
    for data in extracted_data.values():
        all_recommendations.extend(data['recommendations'])
    
    # Remove duplicates while preserving order
    unique_recommendations = list(dict.fromkeys(all_recommendations))
    
    # Add context-specific recommendations based on Kilimani data
    kilimani_recommendations = [
        f"Given Kilimani's {KILIMANI_LST_DATA['environmental_insights']['climate_indicators']['uhi_level'].lower()} UHI intensity, prioritize cooling strategies",
        f"With mean temperatures of {KILIMANI_LST_DATA['statistics']['mean_temperature']:.1f}°C, focus on heat mitigation measures",
        "Implement district-level cooling networks to address area-wide heat island effects",
        "Establish mandatory green building standards for new developments"
    ]
    
    unique_recommendations.extend(kilimani_recommendations)
    
    st.markdown(f"""
    <div class="insight-box">
        <h4>🤖 AI-Generated Recommendations for Kilimani:</h4>
        <ul>
            {"".join(f"<li>{rec}</li>" for rec in unique_recommendations[:8])}
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Navigation footer
st.markdown("---")
st.markdown("### 🧭 Quick Actions")

col1, col2, col3 = st.columns(3)
with col1:
    st.info("📄 **Upload Documents** to analyze building plans and generate thermal impact assessments")
with col2:
    st.info("📊 **View Analytics** to understand the correlation between building characteristics and temperature")
with col3:
    st.info("🎨 **Generate Plans** to visualize AI-created building layouts with sustainability features")

# Data source information
with st.expander("📍 Data Source Information"):
    st.write(f"**Location:** {KILIMANI_LST_DATA['location']}")
    st.write(f"**Analysis Timestamp:** {KILIMANI_LST_DATA['analysis_timestamp']}")
    st.write(f"**Data Type:** {KILIMANI_LST_DATA['data_type']}")
    st.write(f"**Total Pixels Analyzed:** {KILIMANI_LST_DATA['statistics']['total_pixels']:,}")
    
    # Additional environmental insights
    st.markdown("**Environmental Classification:**")
    climate_info = KILIMANI_LST_DATA['environmental_insights']['climate_indicators']
    st.write(f"• UHI Level: {climate_info['uhi_level']}")
    st.write(f"• Temperature Stress: {climate_info['temperature_stress_level']}")
    st.write(f"• Thermal Comfort: {climate_info['thermal_comfort_index']}")
    st.write(f"• Environmental Risk: {climate_info['environmental_risk_level']}")

# Advanced Analytics Section
st.markdown("---")
st.markdown("### 🔬 Advanced Heat Island Analytics")

# Create a comprehensive temperature analysis chart
fig_temp_analysis = go.Figure()

# Add temperature thresholds as horizontal lines
thresholds = KILIMANI_LST_DATA['environmental_insights']['heat_classification']
fig_temp_analysis.add_hline(y=thresholds['extreme_hot_threshold'], 
                           line_dash="dot", line_color="red", 
                           annotation_text="Extreme Hot")
fig_temp_analysis.add_hline(y=thresholds['very_hot_threshold'], 
                           line_dash="dash", line_color="orange", 
                           annotation_text="Very Hot")
fig_temp_analysis.add_hline(y=thresholds['hot_threshold'], 
                           line_dash="dash", line_color="yellow", 
                           annotation_text="Hot")
fig_temp_analysis.add_hline(y=thresholds['cool_threshold'], 
                           line_dash="dash", line_color="lightblue", 
                           annotation_text="Cool")
fig_temp_analysis.add_hline(y=thresholds['very_cool_threshold'], 
                           line_dash="dot", line_color="blue", 
                           annotation_text="Very Cool")

# Add current statistics as scatter points
stats = KILIMANI_LST_DATA['statistics']
fig_temp_analysis.add_scatter(
    x=['Min', 'P10', 'P25', 'Median', 'Mean', 'P75', 'P90', 'Max'],
    y=[stats['min_temperature'], stats['percentile_10'], stats['percentile_25'],
       stats['median_temperature'], stats['mean_temperature'], 
       stats['percentile_75'], stats['percentile_90'], stats['max_temperature']],
    mode='markers+lines',
    marker=dict(size=12, color='purple'),
    name='Current LST Statistics'
)

fig_temp_analysis.update_layout(
    title='🌡️ Kilimani Temperature Profile with Heat Classifications',
    xaxis_title='Statistical Measures',
    yaxis_title='Temperature (°C)',
    showlegend=True,
    height=500
)

st.plotly_chart(fig_temp_analysis, use_container_width=True)

# Heat island impact calculator
st.markdown("### 🧮 Heat Island Impact Calculator")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🏗️ Building Parameters:**")
    calc_density = st.slider("Building Density (%)", 20, 90, 50)
    calc_coverage = st.slider("Site Coverage (%)", 30, 80, 60)
    calc_height = st.slider("Building Height (floors)", 1, 30, 10)
    calc_green = st.slider("Green Space Ratio (%)", 0, 50, 15)

with col2:
    st.markdown("**🌡️ Temperature Impact Calculation:**")
    
    # Calculate temperature impact based on parameters
    base_temp = KILIMANI_LST_DATA['statistics']['mean_temperature']
    density_impact = (calc_density - 50) * 0.08
    coverage_impact = (calc_coverage - 50) * 0.04
    height_impact = (calc_height - 10) * 0.15
    green_impact = (calc_green - 20) * -0.12
    
    total_impact = density_impact + coverage_impact + height_impact + green_impact
    projected_temp = base_temp + total_impact
    
    st.metric("Current Mean Temperature", f"{base_temp:.1f}°C")
    st.metric("Projected Temperature", f"{projected_temp:.1f}°C", f"{total_impact:+.1f}°C")
    
    # Impact breakdown
    st.markdown("**Impact Breakdown:**")
    st.write(f"• Density Effect: {density_impact:+.2f}°C")
    st.write(f"• Coverage Effect: {coverage_impact:+.2f}°C")
    st.write(f"• Height Effect: {height_impact:+.2f}°C")
    st.write(f"• Green Space Effect: {green_impact:+.2f}°C")

# Sustainability scoring system
st.markdown("---")
st.markdown("### 🌱 Sustainability Assessment Framework")

if extracted_data:
    sustainability_data = []
    for filename, data in extracted_data.items():
        sustainability_data.append({
            'Document': filename,
            'Sustainability Score': data['environmental_impact']['sustainability_score'],
            'Environmental Grade': data['environmental_impact']['environmental_grade'],
            'Thermal Impact': data['thermal_impact']['projected_temp'] - data['thermal_impact']['current_temp'],
            'Building Density': data['building_density']['density'],
            'Green Features': 'Yes' if data['environmental_impact']['has_green_features'] else 'No'
        })
    
    df_sustainability = pd.DataFrame(sustainability_data)
    
    # Create sustainability comparison chart
    fig_sustainability = px.bar(
        df_sustainability, 
        x='Document', 
        y='Sustainability Score',
        color='Environmental Grade',
        title='📊 Sustainability Scores by Document',
        color_discrete_map={'A': 'green', 'B': 'orange', 'C': 'red'}
    )
    fig_sustainability.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_sustainability, use_container_width=True)
    
    # Display sustainability table
    st.dataframe(df_sustainability, use_container_width=True)

# Environmental risk assessment
st.markdown("### ⚠️ Environmental Risk Assessment")

risk_factors = {
    'High Temperature Zones': KILIMANI_LST_DATA['statistics']['hot_pixels_percentage'],
    'UHI Intensity': min(100, KILIMANI_LST_DATA['statistics']['heat_island_intensity'] * 10),
    'Temperature Variability': KILIMANI_LST_DATA['statistics']['temperature_variability_index'] * 10,
    'Extreme Heat Risk': min(100, (KILIMANI_LST_DATA['statistics']['max_temperature'] - 40) * 20)
}

# Create risk assessment radar chart
fig_risk = go.Figure()

fig_risk.add_trace(go.Scatterpolar(
    r=list(risk_factors.values()),
    theta=list(risk_factors.keys()),
    fill='toself',
    fillcolor='rgba(255,0,0,0.3)',
    line=dict(color='red'),
    name='Risk Level'
))

fig_risk.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100]
        )
    ),
    showlegend=True,
    title="🎯 Environmental Risk Profile"
)

st.plotly_chart(fig_risk, use_container_width=True)

# Action plan generator
st.markdown("---")
st.markdown("### 📋 Automated Action Plan Generator")

with st.expander("🚀 Generate Custom Action Plan", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        priority_level = st.selectbox("Priority Level", ["High", "Medium", "Low"])
        timeline = st.selectbox("Implementation Timeline", ["Immediate (0-6 months)", "Short-term (6-18 months)", "Long-term (1-5 years)"])
        budget_range = st.selectbox("Budget Range", ["< $50K", "$50K - $200K", "$200K - $1M", "> $1M"])
    
    with col2:
        focus_areas = st.multiselect(
            "Focus Areas",
            ["Temperature Reduction", "Green Infrastructure", "Energy Efficiency", "Air Quality", "Water Management", "Community Health"],
            default=["Temperature Reduction", "Green Infrastructure"]
        )
    
    if st.button("🎯 Generate Action Plan", type="primary"):
        # Generate customized action plan based on selections
        action_items = []
        
        if "Temperature Reduction" in focus_areas:
            if priority_level == "High":
                action_items.extend([
                    "Install reflective roofing materials on existing buildings",
                    "Implement emergency cooling centers in high-risk areas",
                    "Create shade structures in public spaces"
                ])
            action_items.extend([
                "Establish cool pavement pilot programs",
                "Increase urban tree canopy coverage",
                "Implement building energy efficiency retrofits"
            ])
        
        if "Green Infrastructure" in focus_areas:
            action_items.extend([
                "Develop green roof incentive programs",
                "Create urban forest corridors",
                "Install rain gardens and bioswales",
                "Establish community gardens in vacant lots"
            ])
        
        if "Energy Efficiency" in focus_areas:
            action_items.extend([
                "Promote solar panel installations",
                "Implement smart grid technologies",
                "Establish building energy benchmarking requirements"
            ])
        
        # Display generated action plan
        st.markdown("#### 📝 Generated Action Plan")
        for i, item in enumerate(action_items[:10], 1):
            st.write(f"**{i}.** {item}")
        
        # Add timeline and budget considerations
        st.markdown(f"""
        **Implementation Details:**
        - **Timeline:** {timeline}
        - **Budget Range:** {budget_range}
        - **Priority Level:** {priority_level}
        - **Focus Areas:** {', '.join(focus_areas)}
        """)

# Export functionality
st.markdown("---")
st.markdown("### 📤 Export & Reporting")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Export Analysis Report", type="secondary"):
        # Generate comprehensive report data
        report_data = {
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": KILIMANI_LST_DATA['location'],
            "temperature_stats": KILIMANI_LST_DATA['statistics'],
            "environmental_insights": KILIMANI_LST_DATA['environmental_insights'],
            "documents_analyzed": len(extracted_data),
            "avg_sustainability_score": np.mean([d['environmental_impact']['sustainability_score'] for d in extracted_data.values()]) if extracted_data else None
        }
        
        # Convert to JSON for download
        json_str = json.dumps(report_data, indent=2, default=str)
        st.download_button(
            label="💾 Download JSON Report",
            data=json_str,
            file_name=f"kilimani_heat_analysis_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

with col2:
    if extracted_data and st.button("🏗️ Export Building Plans", type="secondary"):
        st.info("Building plans are displayed above. Right-click on images to save individually.")

with col3:
    if st.button("📈 Generate Summary Dashboard", type="secondary"):
        st.balloons()
        st.success("✅ Dashboard data refreshed! Scroll up to view updated visualizations.")

# Footer with additional information
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; margin: 2rem 0;">
    <h3>🌟 Kilimani Heat Island Analysis Platform</h3>
    <p>Advanced AI-powered building impact assessment and thermal analysis</p>
    <p><strong>Current Status:</strong> {uhi_level} Urban Heat Island | <strong>Mean Temperature:</strong> {mean_temp}°C</p>
</div>
""".format(
    uhi_level=KILIMANI_LST_DATA['environmental_insights']['climate_indicators']['uhi_level'],
    mean_temp=KILIMANI_LST_DATA['statistics']['mean_temperature']
), unsafe_allow_html=True)