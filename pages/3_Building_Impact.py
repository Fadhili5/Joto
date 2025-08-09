import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import rasterio
from pathlib import Path
import json
from datetime import datetime
from PIL import Image
import re
import tempfile
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# Azure OpenAI Configuration
def get_azure_openai_client():
    try:
        client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2025-01-01-preview'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
        )
        return client
    except Exception as e:
        st.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
        return None

def validate_azure_openai_config():
    required_vars = ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_DEPLOYMENT_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    return len(missing_vars) == 0, missing_vars

@st.cache_resource
def get_cached_azure_client():
    return get_azure_openai_client()

# Core Analysis Functions
def load_lst_data():
    """Load LST (Land Surface Temperature) data from raster file"""
    try:
        lst_file = Path("Kilimani_LST_Prediction.tif")
        if lst_file.exists():
            with rasterio.open(lst_file) as src:
                data = src.read(1)
                if src.nodata:
                    data = np.where(data == src.nodata, np.nan, data)
                return data, src.bounds, src.crs, src.transform
        else:
            return None, None, None, None
    except Exception as e:
        st.error(f"Error loading LST data: {str(e)}")
        return None, None, None, None

def get_temperature_at_location(lat, lon, lst_data, bounds, transform):
    """Get temperature at specific coordinates from LST data"""
    if lst_data is None or bounds is None:
        return None
    try:
        row, col = rasterio.transform.rowcol(transform, lon, lat)
        if 0 <= row < lst_data.shape[0] and 0 <= col < lst_data.shape[1]:
            temp = lst_data[row, col]
            return temp if not np.isnan(temp) else None
        return None
    except:
        return None

def calculate_building_metrics(building):
    """Calculate comprehensive building metrics including energy consumption and efficiency"""
    # Base energy consumption calculation (simplified model)
    base_consumption = building.get('size_sqm', 1000) * 120  # 120 kWh/m² base
    
    # Adjust for building characteristics
    age_factor = 1.0 + (building.get('age', 0) * 0.02)  # 2% increase per year
    insulation_factor = 1.0 - ((building.get('insulation_rating', 3) - 3) * 0.1)  # 10% per rating point
    energy_source_factor = {
        'solar': 0.3, 'mixed': 0.6, 'geothermal': 0.4, 'grid': 1.0
    }.get(building.get('energy_source', 'grid'), 1.0)
    
    energy_consumption = base_consumption * age_factor * insulation_factor * energy_source_factor
    efficiency_rating = energy_consumption / building.get('size_sqm', 1000)
    
    # Environmental score calculation
    score = 100
    score -= 20 if building.get('age', 0) > 30 else 10 if building.get('age', 0) > 15 else 0
    score -= 15 if building.get('size_sqm', 1000) > 5000 else 8 if building.get('size_sqm', 1000) > 2000 else 0
    score += (building.get('insulation_rating', 3) - 3) * 10
    score += {'solar': 15, 'mixed': 8, 'geothermal': 12}.get(building.get('energy_source', 'grid'), 0)
    score += building.get('green_features', 0) * 5
    
    # Add temperature impact if available
    if building.get('lst_temperature'):
        temp = building['lst_temperature']
        score -= 15 if temp > 35 else 8 if temp > 30 else -5 if temp < 25 else 0
    
    return {
        'energy_consumption': round(energy_consumption, 2),
        'efficiency_rating': round(efficiency_rating, 2),
        'environmental_score': max(0, min(100, round(score, 1)))
    }

def create_detailed_ai_prompt(plan_data, analysis_results):
    """Create a comprehensive prompt for AI analysis and detailed development plan generation"""
    
    # Summarize project data
    project_summary = f"""
PROJECT OVERVIEW:
- Name: {plan_data.get('project_name', 'Development Project')}
- Location: {plan_data.get('location', 'Not specified')}
- Type: {plan_data.get('project_type', 'Mixed-Use')}
- Total Area: {plan_data.get('total_area', 0):,} m²
- Number of Buildings: {len(plan_data.get('buildings', []))}
- Sustainability Target: {plan_data.get('sustainability_target', 'Basic Compliance')}
- Budget Range: {plan_data.get('budget_range', 'Not specified')}

BUILDING DETAILS:"""
    
    for i, building in enumerate(plan_data.get('buildings', []), 1):
        metrics = calculate_building_metrics(building)
        project_summary += f"""
Building {i}: {building.get('name', f'Building {i}')}
- Type: {building.get('type', 'Mixed')}
- Size: {building.get('size_sqm', 0):,} m² | Floors: {building.get('floors', 0)}
- Age: {building.get('age', 0)} years | Units: {building.get('units', 0)}
- Energy Source: {building.get('energy_source', 'grid').title()}
- Insulation Rating: {building.get('insulation_rating', 3)}/5
- Green Features: {building.get('green_features', 0)}/5
- Environmental Score: {metrics['environmental_score']}/100
- Energy Consumption: {metrics['energy_consumption']:,.0f} kWh/year
- Energy Efficiency: {metrics['efficiency_rating']:.1f} kWh/m²
- LST Temperature: {building.get('lst_temperature', 'N/A')}°C
- Sustainable Materials: {', '.join(building.get('sustainable_materials', []))}
- Water Features: {', '.join(building.get('water_features', []))}
- Target Certifications: {', '.join(building.get('certifications', []))}"""

    # Analysis results summary
    analysis_summary = f"""
CURRENT ANALYSIS RESULTS:
- Overall Environmental Score: {analysis_results.get('overall_score', 0):.1f}/100
- Average Temperature: {analysis_results.get('temperature_impact', {}).get('average_temperature', 'N/A')}°C
- Heat Island Risk: {analysis_results.get('temperature_impact', {}).get('heat_island_risk', 'N/A')}
- Temperature Range: {analysis_results.get('temperature_impact', {}).get('temperature_range', 'N/A')}°C"""

    prompt = f"""You are an expert urban planning and civil engineering consultant specializing in comprehensive development planning, infrastructure design, and sustainable construction in Kenya and East Africa. You have 20+ years of experience in master planning, civil works design, and environmental impact assessment.

TASK: Generate a complete, detailed development plan for this project including all civil works specifications, infrastructure requirements, and implementation strategies tailored for the Kenyan construction industry and regulatory environment.

{project_summary}

{analysis_summary}

COMPREHENSIVE DEVELOPMENT PLAN REQUIREMENTS:

## 1. MASTER PLANNING & SITE LAYOUT (15 points)
- **Site Analysis & Topographical Considerations**
  - Detailed site survey requirements and existing conditions assessment
  - Topographical analysis with contour mapping and slope considerations
  - Soil investigation requirements and geotechnical recommendations
  - Existing vegetation, trees, and environmental features to preserve
  - Drainage patterns, water bodies, and flood risk assessment

- **Master Site Plan Development**
  - Optimal building placement considering solar orientation, prevailing winds, and views
  - Setback requirements per Nairobi City County building regulations
  - Plot ratio calculations and floor area ratio compliance
  - Landscaping and green space allocation (minimum 20% open space)
  - Vehicle and pedestrian circulation planning
  - Emergency access routes and fire safety considerations

## 2. DETAILED CIVIL WORKS SPECIFICATIONS (25 points)
- **Earthworks & Site Preparation**
  - Cut and fill calculations with soil balance analysis
  - Site clearing specifications including tree removal protocols
  - Excavation depths for foundations, basements, and utilities
  - Soil stabilization requirements for poor ground conditions
  - Temporary works including shoring, dewatering, and access roads
  - Environmental mitigation during construction

- **Foundation Design & Structural Systems**
  - Foundation type recommendations (pad, strip, raft, or piled) based on soil conditions
  - Foundation depths and bearing capacity requirements
  - Concrete specifications (C20, C25, C30 grades) per BS 8110 or Eurocode
  - Steel reinforcement specifications and detailing
  - Structural frame options (reinforced concrete, steel, or hybrid)
  - Seismic design considerations for Nairobi's geological conditions

- **Infrastructure & Utilities Planning**
  - **Water Supply System**: Connection to Nairobi City Water, storage requirements, pumping systems
  - **Sewerage & Drainage**: Connection to city sewer, on-site treatment options, storm water management
  - **Electrical Systems**: KPLC connection requirements, transformer specifications, distribution systems
  - **Telecommunications**: Fiber optic infrastructure, cellular coverage enhancement
  - **Gas Supply**: LPG reticulation systems where applicable

## 3. TRANSPORTATION & ACCESS INFRASTRUCTURE (15 points)
- **Road Network & Access**
  - Primary and secondary access road specifications
  - Road construction standards (bitumen, concrete, or cabro paving)
  - Traffic impact assessment and management during construction
  - Public transport integration and bus stop provisions
  - Motorcycle and bicycle infrastructure

- **Parking & Vehicle Management**
  - Parking ratio compliance (1:1 for residential, varying for commercial)
  - Parking structure design (surface, basement, or multi-story)
  - Electric vehicle charging infrastructure preparation
  - Traffic calming measures and speed control
  - Waste collection vehicle access and management

## 4. UTILITIES & SERVICES INFRASTRUCTURE (20 points)
- **Water & Wastewater Management**
  - Water demand calculations and supply system sizing
  - Rainwater harvesting system design (mandatory for buildings >300m²)
  - Greywater treatment and reuse systems
  - Sewage treatment plant sizing for developments >100 units
  - Storm water detention and bio-retention systems

- **Electrical & Energy Systems**
  - Electrical load calculations and transformer sizing
  - High voltage and low voltage distribution design
  - Generator backup systems and fuel storage
  - Solar PV system integration and grid-tie specifications
  - Energy-efficient lighting and smart building systems
  - Fiber optic and telecommunications infrastructure

## 5. ENVIRONMENTAL & SUSTAINABILITY SYSTEMS (15 points)
- **Green Infrastructure**
  - Native landscaping plan with indigenous plant species
  - Urban forestry and tree preservation/replacement strategy
  - Green roofs and walls implementation
  - Biodiversity conservation areas within the development
  - Microclimate management through vegetation and water features

- **Waste Management & Circular Economy**
  - Integrated solid waste management system
  - Composting facilities for organic waste
  - Recycling centers and material recovery facilities
  - Construction waste management and material reuse
  - E-waste collection and processing provisions

## 6. IMPLEMENTATION STRATEGY & PROJECT MANAGEMENT (10 points)
- **Phased Development Plan**
  - Phase 1: Site preparation, infrastructure, and first buildings
  - Phase 2-N: Subsequent development phases with timing
  - Critical path analysis and project scheduling
  - Risk management and contingency planning
  - Quality control and supervision requirements

- **Regulatory Compliance & Approvals**
  - Development application process and required documentation
  - Environmental Impact Assessment (EIA) requirements
  - Building permits and occupancy certificates
  - Fire department approvals and safety systems
  - Utility connection approvals and processes

DETAILED SPECIFICATIONS REQUIRED:

### Construction Materials & Standards
- Specify concrete grades, steel reinforcement types, and masonry units
- Local material sourcing preferences and availability
- Quality control testing requirements and frequencies
- Alternative materials for sustainability (bamboo, compressed earth blocks)
- Import requirements for specialized materials and equipment

### Cost Estimation & Financial Planning
- Preliminary construction cost estimates by trade/activity
- Infrastructure development costs and utility connection fees
- Professional fees (architects, engineers, surveyors, project managers)
- Regulatory fees, permits, and approval costs
- Contingency allowances and risk provisions

### Construction Methodology
- Construction sequence and critical activities
- Access and logistics during construction
- Safety management and health protocols
- Environmental protection measures during construction
- Community engagement and impact mitigation

### Operations & Maintenance Planning
- Long-term maintenance schedules and requirements
- Facility management systems and procedures
- Asset lifecycle planning and replacement schedules
- Energy monitoring and optimization strategies
- Community management and governance structures

CONTEXT CONSIDERATIONS FOR KENYA:
- Nairobi City County planning requirements and development control
- National Construction Authority (NCA) regulations and standards
- Kenya Bureau of Standards (KEBS) specifications
- Environmental Management and Coordination Act (EMCA) requirements
- Vision 2030 development goals and Big Four Agenda alignment
- Local labor skills, equipment availability, and supply chains
- Climate considerations (two rainy seasons, altitude effects)
- Security requirements and crime prevention through environmental design

OUTPUT FORMAT:
Provide a comprehensive, professionally structured development plan that could serve as a preliminary design document. Use clear sections, technical specifications, and implementation timelines. Include specific measurements, quantities, and standards references. Format as a technical report with executive summary, detailed sections, and appendices for specifications.

The plan should be immediately actionable for engaging with local contractors, consultants, and regulatory authorities in Kenya."""

    return prompt

def analyze_with_ai(plan_data, analysis_results):
    """Analyze development plan using Azure OpenAI"""
    client = get_cached_azure_client()
    if not client:
        return "Azure OpenAI client not available. Please check your configuration."
    
    try:
        prompt = create_detailed_ai_prompt(plan_data, analysis_results)
        
        response = client.chat.completions.create(
            model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
            messages=[
                {"role": "system", "content": "You are an expert urban planning and sustainable development consultant specializing in environmental impact assessment for East African development projects."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7,
            top_p=0.9
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"AI Analysis Error: {str(e)}"

def analyze_development_plan(plan_data, lst_data, bounds, transform):
    """Main analysis function that processes plan data and calculates metrics"""
    analysis = {
        'overall_score': 0,
        'temperature_impact': {},
        'recommendations': [],
        'risk_assessment': {},
        'sustainability_score': 0,
        'detailed_analysis': '',
        'ai_generated': False
    }
    
    if not plan_data.get('buildings'):
        return analysis
    
    building_scores = []
    temp_readings = []
    total_energy_consumption = 0
    
    # Process each building
    for building in plan_data['buildings']:
        # Get LST temperature
        lat, lon = building.get('location', [-1.2921, 36.8219])
        lst_temp = get_temperature_at_location(lat, lon, lst_data, bounds, transform)
        building['lst_temperature'] = lst_temp
        if lst_temp:
            temp_readings.append(lst_temp)
        
        # Calculate metrics
        metrics = calculate_building_metrics(building)
        building.update(metrics)
        
        building_scores.append(metrics['environmental_score'])
        total_energy_consumption += metrics['energy_consumption']
    
    # Calculate overall analysis results
    filtered_temp_readings = [temp for temp in temp_readings if temp is not None]
    
    analysis.update({
        'overall_score': np.mean(building_scores) if building_scores else 0,
        'sustainability_score': np.mean(building_scores) if building_scores else 0,
        'total_energy_consumption': total_energy_consumption,
        'average_efficiency': np.mean([b['efficiency_rating'] for b in plan_data['buildings']]),
        'temperature_impact': {
            'average_temperature': np.mean(filtered_temp_readings) if filtered_temp_readings else 0,
            'max_temperature': np.max(filtered_temp_readings) if filtered_temp_readings else 0,
            'min_temperature': np.min(filtered_temp_readings) if filtered_temp_readings else 0,
            'temperature_range': np.ptp(filtered_temp_readings) if filtered_temp_readings else 0,
            'heat_island_risk': 'High' if filtered_temp_readings and np.mean(filtered_temp_readings) > 32 
                               else 'Medium' if filtered_temp_readings and np.mean(filtered_temp_readings) > 28 
                               else 'Low' if filtered_temp_readings else 'N/A'
        }
    })
    
    return analysis

# File Processing Functions (Simplified)
def parse_uploaded_file(uploaded_file):
    """Simplified file parser - focuses on extracting basic project information"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'json':
            data = json.loads(uploaded_file.getvalue())
            if 'buildings' in data:
                return {"success": True, "data": data}
        
        # For other file types, extract text and create basic structure
        content = ""
        if file_extension == 'txt':
            content = uploaded_file.getvalue().decode('utf-8')
        else:
            # For PDF, DOCX, etc., would need additional libraries
            content = "File content extraction not implemented for this format"
        
        # Create basic structure from text
        plan_data = create_basic_plan_structure(content, uploaded_file.name)
        return {"success": True, "data": plan_data}
        
    except Exception as e:
        return {"error": f"Error parsing file: {str(e)}"}

def create_basic_plan_structure(content, filename):
    """Create a basic plan structure from text content"""
    return {
        "project_name": filename.split('.')[0].replace('_', ' ').title(),
        "contractor_name": "Unknown",
        "project_type": "Mixed-Use",
        "total_area": 5000,
        "location": "Kilimani, Nairobi",
        "completion_date": datetime.now().isoformat(),
        "budget_range": "$1M - $5M",
        "sustainability_target": "Basic Compliance",
        "buildings": [{
            'name': 'Building 1',
            'type': 'Mixed',
            'floors': 5,
            'size_sqm': 2000,
            'units': 20,
            'parking_spaces': 30,
            'location': [-1.2921, 36.8219],
            'green_features': 3,
            'insulation_rating': 3,
            'energy_source': 'grid',
            'hvac_type': 'Standard',
            'sustainable_materials': [],
            'water_features': [],
            'certifications': [],
            'age': 0
        }],
        'created_at': datetime.now().isoformat(),
        'source': 'uploaded_file'
    }

# UI Components
def create_development_plan_form():
    """Create the manual form for development plan input"""
    st.subheader("📋 Development Plan Details")
    
    with st.form("development_plan"):
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input("Project Name", placeholder="e.g., Green Valley Residences")
            contractor_name = st.text_input("Contractor/Developer", placeholder="Your company name")
            project_type = st.selectbox("Project Type", ["Residential", "Commercial", "Mixed-Use", "Industrial", "Institutional"])
            total_area = st.number_input("Total Project Area (m²)", min_value=100, value=5000)
        
        with col2:
            project_location = st.text_input("Project Location", placeholder="e.g., Kilimani, Nairobi")
            expected_completion = st.date_input("Expected Completion Date")
            budget_range = st.selectbox("Budget Range (USD)", ["< $100K", "$100K - $500K", "$500K - $1M", "$1M - $5M", "> $5M"])
            sustainability_target = st.selectbox("Sustainability Target", ["Basic Compliance", "Green Building Certified", "Net Zero Energy", "Carbon Neutral"])

        st.subheader("🏗️ Building Details")
        num_buildings = st.number_input("Number of Buildings", min_value=1, max_value=10, value=1)

        buildings = []
        for i in range(num_buildings):
            st.write(f"**Building {i+1}**")
            b_col1, b_col2, b_col3 = st.columns(3)
            
            with b_col1:
                b_name = st.text_input("Building Name", key=f"b_name_{i}", placeholder=f"Building {i+1}")
                b_type = st.selectbox("Type", ["Residential", "Office", "Retail", "Mixed"], key=f"b_type_{i}")
                b_floors = st.number_input("Floors", min_value=1, max_value=50, value=3, key=f"b_floors_{i}")
            
            with b_col2:
                b_size = st.number_input("Size (m²)", min_value=50, value=1000, key=f"b_size_{i}")
                b_units = st.number_input("Units/Offices", min_value=1, value=10, key=f"b_units_{i}")
                b_parking = st.number_input("Parking Spaces", min_value=0, value=20, key=f"b_parking_{i}")
            
            with b_col3:
                b_lat = st.number_input("Latitude", value=-1.2921, format="%.6f", key=f"b_lat_{i}")
                b_lon = st.number_input("Longitude", value=36.8219, format="%.6f", key=f"b_lon_{i}")
                b_green_features = st.slider("Green Features (1-5)", 1, 5, 3, key=f"b_green_{i}")

            with st.expander(f"Advanced Features - Building {i+1}"):
                adv_col1, adv_col2 = st.columns(2)
                with adv_col1:
                    b_insulation = st.slider("Insulation Rating (1-5)", 1, 5, 3, key=f"b_insulation_{i}")
                    b_energy_source = st.selectbox("Primary Energy Source", ["grid", "solar", "mixed", "geothermal"], key=f"b_energy_{i}")
                    b_hvac_type = st.selectbox("HVAC System", ["Standard", "High Efficiency", "Smart/Automated", "Passive"], key=f"b_hvac_{i}")
                with adv_col2:
                    b_materials = st.multiselect("Sustainable Materials", 
                        ["Recycled Steel", "Bamboo", "Reclaimed Wood", "Low-Carbon Concrete", "Green Insulation"], 
                        key=f"b_materials_{i}")
                    b_water_features = st.multiselect("Water Management", 
                        ["Rainwater Harvesting", "Greywater Recycling", "Permeable Paving", "Bioswales"], 
                        key=f"b_water_{i}")
                    b_certifications = st.multiselect("Target Certifications", 
                        ["LEED", "BREEAM", "Green Star", "EDGE", "Local Green Building"], 
                        key=f"b_cert_{i}")

            building_data = {
                'name': b_name or f"Building {i+1}",
                'type': b_type,
                'floors': b_floors,
                'size_sqm': b_size,
                'units': b_units,
                'parking_spaces': b_parking,
                'location': [b_lat, b_lon],
                'green_features': b_green_features,
                'insulation_rating': b_insulation,
                'energy_source': b_energy_source,
                'hvac_type': b_hvac_type,
                'sustainable_materials': b_materials,
                'water_features': b_water_features,
                'certifications': b_certifications,
                'age': 0
            }
            buildings.append(building_data)

        submitted = st.form_submit_button("🔍 Analyze Development Plan", type="primary")

        if submitted:
            plan_data = {
                'project_name': project_name,
                'contractor_name': contractor_name,
                'project_type': project_type,
                'total_area': total_area,
                'location': project_location,
                'completion_date': expected_completion.isoformat(),
                'budget_range': budget_range,
                'sustainability_target': sustainability_target,
                'buildings': buildings,
                'created_at': datetime.now().isoformat()
            }
            return plan_data

    return None

def create_file_upload_interface():
    """Create file upload interface"""
    st.subheader("📁 Upload Development Plan")
    st.markdown("""
    Upload your development plan document for AI analysis. Supported formats:
    - **JSON** (.json) - Structured data files (preferred)
    - **Text** (.txt) - Plain text descriptions
    - **PDF, Word, Excel** - Basic text extraction (limited)
    """)

    uploaded_file = st.file_uploader(
        "Choose a development plan file",
        type=['pdf', 'docx', 'txt', 'json', 'xlsx', 'xls'],
        help="Upload your development plan document for AI analysis"
    )

    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")

        if st.button("🔍 Analyze Uploaded Plan", type="primary"):
            with st.spinner("🤖 Processing your development plan..."):
                result = parse_uploaded_file(uploaded_file)
                if "error" in result:
                    st.error(f"❌ Error processing file: {result['error']}")
                    return None
                if result.get("success"):
                    st.success("✅ File processed successfully!")
                    return result["data"]
                else:
                    st.error("❌ Failed to process file")
                    return None

    return None

def display_analysis_results(plan_data, analysis_results, ai_analysis=None):
    """Display comprehensive analysis results"""
    st.header("📊 Development Plan Analysis Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall Environmental Score", 
                 f"{analysis_results['overall_score']:.1f}/100",
                 delta=f"{analysis_results['overall_score'] - 70:.1f}" if analysis_results['overall_score'] != 70 else None)
    with col2:
        st.metric("Total Energy Consumption", 
                 f"{analysis_results.get('total_energy_consumption', 0):,.0f} kWh/year")
    with col3:
        st.metric("Average Efficiency", 
                 f"{analysis_results.get('average_efficiency', 0):.1f} kWh/m²")
    with col4:
        st.metric("Heat Island Risk", 
                 analysis_results.get('temperature_impact', {}).get('heat_island_risk', 'N/A'))

    # Building details table
    st.subheader("Building Performance Summary")
    building_df = pd.DataFrame(plan_data['buildings'])
    display_columns = ['name', 'type', 'size_sqm', 'environmental_score', 'efficiency_rating', 'energy_consumption', 'lst_temperature']
    available_columns = [col for col in display_columns if col in building_df.columns]
    st.dataframe(building_df[available_columns], use_container_width=True)
    
    # Charts
    col1, col2 = st.columns(2)
    with col1:
        if len(building_df) > 1:
            fig = px.bar(building_df, x='name', y='environmental_score', 
                        title="Environmental Scores by Building")
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=building_df.iloc[0]['environmental_score'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Environmental Score"},
                gauge={'axis': {'range': [None, 100]},
                      'bar': {'color': "darkblue"},
                      'steps': [{'range': [0, 50], 'color': "lightgray"},
                               {'range': [50, 80], 'color': "gray"}]}
            ))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if len(building_df) > 1:
            fig = px.scatter(building_df, x='size_sqm', y='efficiency_rating', 
                           color='type', size='environmental_score',
                           title="Energy Efficiency vs Building Size")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.metric("Building Energy Efficiency", 
                     f"{building_df.iloc[0]['efficiency_rating']:.1f} kWh/m²")

    # AI Analysis Results
    if ai_analysis:
        st.subheader("🤖 AI Analysis & Recommendations")
        st.markdown(ai_analysis)
    
    # Temperature analysis if available
    temp_data = analysis_results.get('temperature_impact', {})
    if temp_data.get('average_temperature', 0) > 0:
        st.subheader("🌡️ Temperature Impact Analysis")
        temp_col1, temp_col2, temp_col3 = st.columns(3)
        with temp_col1:
            st.metric("Average Temperature", f"{temp_data['average_temperature']:.1f}°C")
        with temp_col2:
            st.metric("Temperature Range", f"{temp_data['temperature_range']:.1f}°C")
        with temp_col3:
            st.metric("Heat Island Risk", temp_data['heat_island_risk'])

def main():
    st.title("🏢 Building Environmental Impact Assessment")
    st.markdown("Analyze development plans for environmental sustainability and energy efficiency")
    
    # Load LST data
    lst_data, bounds, crs, transform = load_lst_data()
    
    if lst_data is None:
        st.warning("⚠️ LST temperature data is not available. Analysis will proceed without temperature-based recommendations.")
    else:
        st.success("✅ LST temperature data loaded successfully. Full analysis available.")
    
    # Check Azure OpenAI configuration
    config_valid, missing_vars = validate_azure_openai_config()
    if not config_valid:
        st.warning(f"⚠️ Azure OpenAI not configured. Missing: {', '.join(missing_vars)}. AI analysis will be limited.")
    
    # Input method selection
    input_method = st.radio("Choose input method:", 
                           ["📝 Manual Form Entry", "📁 Upload Development Plan File"], 
                           horizontal=True)
    
    # Get plan data
    if input_method == "📝 Manual Form Entry":
        plan_data = create_development_plan_form()
    else:
        plan_data = create_file_upload_interface()
    
    # Process and analyze
    if plan_data:
        with st.spinner("🤖 Analyzing your development plan..."):
            # Perform basic analysis
            analysis_results = analyze_development_plan(plan_data, lst_data, bounds, transform)
            
            # Get AI analysis if configured
            ai_analysis = None
            if config_valid:
                with st.spinner("🤖 Generating AI recommendations..."):
                    ai_analysis = analyze_with_ai(plan_data, analysis_results)
            
            # Display results
            display_analysis_results(plan_data, analysis_results, ai_analysis)
            
            # Export options
            st.subheader("💾 Export Results")
            col1, col2 = st.columns(2)
            
            with col1:
                # JSON export
                export_data = {
                    'plan': plan_data,
                    'analysis': analysis_results,
                    'ai_analysis': ai_analysis,
                    'generated_at': datetime.now().isoformat()
                }
                json_str = json.dumps(export_data, indent=2, default=str)
                st.download_button(
                    label="📊 Download Analysis Data (JSON)",
                    data=json_str,
                    file_name=f"{plan_data['project_name'].replace(' ', '_')}_analysis.json",
                    mime="application/json"
                )
            
            with col2:
                # CSV export for building data
                building_df = pd.DataFrame(plan_data['buildings'])
                csv = building_df.to_csv(index=False)
                st.download_button(
                    label="📈 Download Building Data (CSV)",
                    data=csv,
                    file_name=f"{plan_data['project_name'].replace(' ', '_')}_buildings.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()