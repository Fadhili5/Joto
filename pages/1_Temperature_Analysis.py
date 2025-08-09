import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import rasterio
from rasterio.plot import show
from rasterio.warp import calculate_default_transform, reproject, Resampling
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
from folium import plugins
import base64
from io import BytesIO
import requests
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    st.error(f"Failed to load environment variables: {str(e)}")

# Page configuration
st.set_page_config(
    page_title="Temperature Analysis",
    page_icon="🌡️",
    layout="wide"
)

def validate_azure_openai_config():
    """Validate Azure OpenAI configuration from environment variables"""
    required_vars = [
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT', 
        'AZURE_OPENAI_API_VERSION',
        'AZURE_OPENAI_DEPLOYMENT_NAME'
    ]
    
    missing_vars = []
    config = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            config[var] = value
    
    return config, missing_vars

def get_azure_openai_client():
    """Initialize and return Azure OpenAI client with error handling"""
    try:
        config, missing_vars = validate_azure_openai_config()
        
        if missing_vars:
            st.error(f"Missing Azure OpenAI configuration: {', '.join(missing_vars)}")
            return None
            
        client = AzureOpenAI(
            api_key=config['AZURE_OPENAI_API_KEY'],
            api_version=config['AZURE_OPENAI_API_VERSION'],
            azure_endpoint=config['AZURE_OPENAI_ENDPOINT']
        )
        
        return client
        
    except Exception as e:
        st.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
        return None

def test_azure_openai_connection(client):
    """Test Azure OpenAI connection with a simple request"""
    if client is None:
        return False, "Client not initialized"
        
    try:
        # Simple test request
        response = client.chat.completions.create(
            model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        return True, "Connection successful"
        
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def get_client_status():
    """Get comprehensive Azure OpenAI client status"""
    config, missing_vars = validate_azure_openai_config()
    
    status = {
        'configured': len(missing_vars) == 0,
        'missing_vars': missing_vars,
        'client': None,
        'connected': False,
        'error_message': None
    }
    
    if status['configured']:
        client = get_azure_openai_client()
        status['client'] = client
        
        if client:
            is_connected, message = test_azure_openai_connection(client)
            status['connected'] = is_connected
            if not is_connected:
                status['error_message'] = message
    
    return status

@st.cache_resource
def get_cached_azure_client():
    """Get cached Azure OpenAI client for better performance"""
    return get_azure_openai_client()

def display_azure_openai_status():
    """Display Azure OpenAI connection status in the UI"""
    status = get_client_status()
    
    if not status['configured']:
        st.error("❌ **Azure OpenAI Not Configured**")
        st.warning(f"Missing environment variables: {', '.join(status['missing_vars'])}")
        
        with st.expander("🔧 Setup Instructions"):
            st.markdown("""
            **Required Environment Variables:**
            ```
            AZURE_OPENAI_API_KEY=your_api_key_here
            AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
            AZURE_OPENAI_API_VERSION=2025-01-01-preview
            AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
            ```
            Add these to your `.env` file and restart the application.
            """)
        return False
        
    elif not status['connected']:
        st.warning("⚠️ **Azure OpenAI Configured but Not Connected**")
        if status['error_message']:
            st.error(f"Connection Error: {status['error_message']}")
        return False
        
    else:
        st.success("✅ **Azure OpenAI Connected**")
        st.info("Advanced AI analysis enabled")
        return True

def handle_azure_openai_error(error):
    """Handle different types of Azure OpenAI errors with appropriate user messages"""
    error_str = str(error).lower()
    
    if "authentication" in error_str or "unauthorized" in error_str:
        return "Authentication failed. Please check your API key."
    elif "rate limit" in error_str or "quota" in error_str:
        return "Rate limit exceeded. Please wait a moment before trying again."
    elif "not found" in error_str or "404" in error_str:
        return "Deployment not found. Please check your deployment name."
    elif "timeout" in error_str:
        return "Request timed out. Please try again."
    elif "network" in error_str or "connection" in error_str:
        return "Network connection error. Please check your internet connection."
    else:
        return f"Azure OpenAI error: {str(error)}"

def run_client_tests():
    """Run basic unit tests for Azure OpenAI client functionality"""
    test_results = []
    
    # Test 1: Configuration validation
    try:
        config, missing_vars = validate_azure_openai_config()
        if len(missing_vars) == 0:
            test_results.append(("✅", "Configuration validation", "All required variables present"))
        else:
            test_results.append(("❌", "Configuration validation", f"Missing: {', '.join(missing_vars)}"))
    except Exception as e:
        test_results.append(("❌", "Configuration validation", f"Error: {str(e)}"))
    
    # Test 2: Client initialization
    try:
        client = get_azure_openai_client()
        if client:
            test_results.append(("✅", "Client initialization", "Client created successfully"))
        else:
            test_results.append(("❌", "Client initialization", "Failed to create client"))
    except Exception as e:
        test_results.append(("❌", "Client initialization", f"Error: {str(e)}"))
    
    # Test 3: Connection test
    try:
        client = get_azure_openai_client()
        if client:
            is_connected, message = test_azure_openai_connection(client)
            if is_connected:
                test_results.append(("✅", "Connection test", "Successfully connected to Azure OpenAI"))
            else:
                test_results.append(("❌", "Connection test", message))
        else:
            test_results.append(("❌", "Connection test", "No client available"))
    except Exception as e:
        test_results.append(("❌", "Connection test", f"Error: {str(e)}"))
    
    return test_results

def handle_api_rate_limiting(retry_count=0, max_retries=3):
    """Handle API rate limiting with exponential backoff"""
    import time
    
    if retry_count >= max_retries:
        return False, "Maximum retry attempts exceeded. Please try again later."
    
    # Exponential backoff: 2^retry_count seconds
    wait_time = 2 ** retry_count
    st.info(f"Rate limit reached. Waiting {wait_time} seconds before retry...")
    time.sleep(wait_time)
    
    return True, f"Retrying after {wait_time} second delay"

def validate_response_quality(response_text):
    """Validate the quality and completeness of AI responses"""
    if not response_text or len(response_text.strip()) < 10:
        return False, "Response too short or empty"
    
    # Check for common error indicators
    error_indicators = [
        "i don't have access",
        "i cannot access",
        "i'm unable to",
        "error occurred",
        "something went wrong"
    ]
    
    response_lower = response_text.lower()
    for indicator in error_indicators:
        if indicator in response_lower:
            return False, f"Response contains error indicator: {indicator}"
    
    # Check for minimum content quality
    if len(response_text.split()) < 5:
        return False, "Response lacks sufficient detail"
    
    return True, "Response quality acceptable"

def create_error_recovery_response(error_type, question, stats):
    """Create informative error recovery responses"""
    base_stats = f"Based on available data: Temperature range {stats['temp_range']:.1f}°C, Average {stats['mean_temp']:.1f}°C"
    
    if error_type == "authentication":
        return f"🔐 **Authentication Issue**: Unable to connect to Azure OpenAI. {base_stats}. Please check API credentials."
    elif error_type == "rate_limit":
        return f"⏱️ **Rate Limit**: Too many requests. {base_stats}. Please wait a moment before asking again."
    elif error_type == "network":
        return f"🌐 **Network Issue**: Connection problem. {base_stats}. Please check your internet connection."
    elif error_type == "timeout":
        return f"⏰ **Timeout**: Request took too long. {base_stats}. Please try a simpler question."
    else:
        return f"⚠️ **Service Issue**: AI service temporarily unavailable. {base_stats}. Using basic analysis instead."

def test_error_handling_scenarios():
    """Test various error handling scenarios"""
    test_results = []
    
    # Test 1: Rate limiting handler
    try:
        can_retry, message = handle_api_rate_limiting(0, 1)
        if can_retry:
            test_results.append(("✅", "Rate limiting handler", "Retry mechanism works"))
        else:
            test_results.append(("❌", "Rate limiting handler", "Retry mechanism failed"))
    except Exception as e:
        test_results.append(("❌", "Rate limiting handler", f"Error: {str(e)}"))
    
    # Test 2: Response validation
    try:
        # Test valid response
        is_valid, message = validate_response_quality("This is a comprehensive analysis of temperature data with detailed insights.")
        if is_valid:
            test_results.append(("✅", "Response validation (valid)", "Correctly identified valid response"))
        else:
            test_results.append(("❌", "Response validation (valid)", f"False negative: {message}"))
        
        # Test invalid response
        is_valid, message = validate_response_quality("Error")
        if not is_valid:
            test_results.append(("✅", "Response validation (invalid)", "Correctly identified invalid response"))
        else:
            test_results.append(("❌", "Response validation (invalid)", "False positive: response should be invalid"))
    except Exception as e:
        test_results.append(("❌", "Response validation", f"Error: {str(e)}"))
    
    # Test 3: Error recovery responses
    try:
        test_stats = {'temp_range': 15.5, 'mean_temp': 28.3}
        recovery_response = create_error_recovery_response("network", "test question", test_stats)
        if "Network Issue" in recovery_response and "28.3°C" in recovery_response:
            test_results.append(("✅", "Error recovery responses", "Generated appropriate recovery response"))
        else:
            test_results.append(("❌", "Error recovery responses", "Recovery response missing expected content"))
    except Exception as e:
        test_results.append(("❌", "Error recovery responses", f"Error: {str(e)}"))
    
    return test_results

def monitor_api_usage():
    """Monitor and log API usage patterns"""
    if 'api_usage_stats' not in st.session_state:
        st.session_state.api_usage_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'fallback_requests': 0,
            'last_request_time': None,
            'error_types': {}
        }
    
    return st.session_state.api_usage_stats

def log_api_request(success=True, error_type=None, fallback_used=False):
    """Log API request results for monitoring"""
    stats = monitor_api_usage()
    stats['total_requests'] += 1
    stats['last_request_time'] = datetime.now()
    
    if success:
        stats['successful_requests'] += 1
    else:
        stats['failed_requests'] += 1
        if error_type:
            stats['error_types'][error_type] = stats['error_types'].get(error_type, 0) + 1
    
    if fallback_used:
        stats['fallback_requests'] += 1

def display_api_usage_stats():
    """Display API usage statistics in the UI"""
    stats = monitor_api_usage()
    
    if stats['total_requests'] > 0:
        success_rate = (stats['successful_requests'] / stats['total_requests']) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requests", stats['total_requests'])
        with col2:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col3:
            st.metric("Failed Requests", stats['failed_requests'])
        with col4:
            st.metric("Fallback Used", stats['fallback_requests'])
        
        if stats['error_types']:
            st.subheader("Error Types")
            for error_type, count in stats['error_types'].items():
                st.write(f"• {error_type}: {count} occurrences")

def run_comprehensive_error_tests():
    """Run comprehensive error handling tests"""
    st.subheader("🧪 Error Handling Test Suite")
    
    # Run client tests
    client_results = run_client_tests()
    
    # Run error handling tests
    error_results = test_error_handling_scenarios()
    
    # Run context processing tests
    context_results = test_context_data_processing()
    
    # Combine all results
    all_results = client_results + error_results + context_results
    
    # Display results
    passed = sum(1 for result in all_results if result[0] == "✅")
    total = len(all_results)
    
    if passed == total:
        st.success(f"✅ All {total} tests passed!")
    else:
        st.warning(f"⚠️ {passed}/{total} tests passed")
    
    # Show detailed results
    with st.expander("Detailed Test Results"):
        for status, test_name, message in all_results:
            st.write(f"{status} **{test_name}**: {message}")
    
    return all_results

def load_lst_data():
    """Load Land Surface Temperature data"""
    try:
        lst_file = Path("Kilimani_LST_Prediction.tif")
        if lst_file.exists():
            with rasterio.open(lst_file) as src:
                data = src.read(1)
                bounds = src.bounds
                crs = src.crs
                transform = src.transform
                nodata = src.nodata
                
                # Handle nodata values
                if nodata is not None:
                    data = np.where(data == nodata, np.nan, data)
                
                return data, bounds, crs, transform
        else:
            st.warning("LST data file not found. Please ensure Kilimani_LST_Prediction.tif is in the root directory")
            return None, None, None, None
    except Exception as e:
        st.error(f"Error loading LST data: {str(e)}")
        return None, None, None, None

def compute_lst_statistics(data):
    """Compute comprehensive statistics for LST data"""
    if data is None:
        return {}
    
    # Remove NaN values for calculations
    valid_data = data[~np.isnan(data)]
    
    if len(valid_data) == 0:
        return {}
    
    stats = {
        'min_temp': np.min(valid_data),
        'max_temp': np.max(valid_data),
        'mean_temp': np.mean(valid_data),
        'median_temp': np.median(valid_data),
        'std_temp': np.std(valid_data),
        'temp_range': np.max(valid_data) - np.min(valid_data),
        'percentile_25': np.percentile(valid_data, 25),
        'percentile_75': np.percentile(valid_data, 75),
        'hot_pixels': np.sum(valid_data > np.percentile(valid_data, 90)),
        'cold_pixels': np.sum(valid_data < np.percentile(valid_data, 10)),
        'total_pixels': len(valid_data)
    }
    
    return stats

def prepare_context_data(stats, data):
    """Prepare structured context data for Azure OpenAI analysis"""
    if not stats or data is None:
        return None
    
    # Calculate additional environmental metrics
    valid_data = data[~np.isnan(data)]
    if len(valid_data) == 0:
        return None
    
    # Calculate percentiles for heat classification
    percentile_90 = np.percentile(valid_data, 90)
    percentile_10 = np.percentile(valid_data, 10)
    
    # Calculate heat island intensity
    heat_island_intensity = stats['max_temp'] - stats['mean_temp']
    
    # Calculate temperature variability index
    temp_variability = stats['std_temp'] / stats['mean_temp'] * 100
    
    context_data = {
        "location": "Kilimani area, Nairobi, Kenya",
        "data_type": "Land Surface Temperature (LST) from satellite imagery",
        "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "statistics": {
            "min_temperature": f"{stats['min_temp']:.2f}°C",
            "max_temperature": f"{stats['max_temp']:.2f}°C",
            "mean_temperature": f"{stats['mean_temp']:.2f}°C",
            "median_temperature": f"{stats['median_temp']:.2f}°C",
            "temperature_range": f"{stats['temp_range']:.2f}°C",
            "standard_deviation": f"{stats['std_temp']:.2f}°C",
            "percentile_25": f"{stats['percentile_25']:.2f}°C",
            "percentile_75": f"{stats['percentile_75']:.2f}°C",
            "percentile_90": f"{percentile_90:.2f}°C",
            "percentile_10": f"{percentile_10:.2f}°C",
            "hot_pixels_count": f"{stats['hot_pixels']:,}",
            "cold_pixels_count": f"{stats['cold_pixels']:,}",
            "hot_pixels_percentage": f"{(stats['hot_pixels']/stats['total_pixels']*100):.1f}%",
            "cold_pixels_percentage": f"{(stats['cold_pixels']/stats['total_pixels']*100):.1f}%",
            "total_pixels": f"{stats['total_pixels']:,}",
            "heat_island_intensity": f"{heat_island_intensity:.2f}°C",
            "temperature_variability_index": f"{temp_variability:.1f}%"
        },
        "environmental_insights": {
            "heat_classification": classify_heat_levels(stats, valid_data),
            "spatial_distribution": analyze_spatial_distribution(valid_data),
            "climate_indicators": calculate_climate_indicators(stats)
        }
    }
    
    return context_data

def classify_heat_levels(stats, valid_data):
    """Classify temperature data into heat level categories"""
    percentiles = {
        'extreme_hot': np.percentile(valid_data, 95),
        'very_hot': np.percentile(valid_data, 90),
        'hot': np.percentile(valid_data, 75),
        'moderate': np.percentile(valid_data, 50),
        'cool': np.percentile(valid_data, 25),
        'very_cool': np.percentile(valid_data, 10)
    }
    
    classification = {
        "extreme_hot_threshold": f"{percentiles['extreme_hot']:.2f}°C",
        "very_hot_threshold": f"{percentiles['very_hot']:.2f}°C",
        "hot_threshold": f"{percentiles['hot']:.2f}°C",
        "moderate_range": f"{percentiles['cool']:.2f}°C - {percentiles['hot']:.2f}°C",
        "cool_threshold": f"{percentiles['cool']:.2f}°C",
        "very_cool_threshold": f"{percentiles['very_cool']:.2f}°C"
    }
    
    return classification

def analyze_spatial_distribution(valid_data):
    """Analyze spatial distribution characteristics of temperature data"""
    # Calculate distribution metrics
    skewness = calculate_skewness(valid_data)
    kurtosis = calculate_kurtosis(valid_data)
    
    distribution_analysis = {
        "distribution_shape": "right-skewed" if skewness > 0.5 else "left-skewed" if skewness < -0.5 else "approximately normal",
        "skewness_value": f"{skewness:.3f}",
        "kurtosis_value": f"{kurtosis:.3f}",
        "distribution_type": "heavy-tailed" if kurtosis > 3 else "light-tailed" if kurtosis < 3 else "normal-tailed",
        "data_concentration": "concentrated around mean" if abs(skewness) < 0.5 and abs(kurtosis - 3) < 1 else "dispersed"
    }
    
    return distribution_analysis

def calculate_skewness(data):
    """Calculate skewness of temperature distribution"""
    mean = np.mean(data)
    std = np.std(data)
    n = len(data)
    
    if std == 0:
        return 0
    
    skewness = (n / ((n-1) * (n-2))) * np.sum(((data - mean) / std) ** 3)
    return skewness

def calculate_kurtosis(data):
    """Calculate kurtosis of temperature distribution"""
    mean = np.mean(data)
    std = np.std(data)
    n = len(data)
    
    if std == 0:
        return 3  # Normal distribution kurtosis
    
    kurtosis = (n * (n+1) / ((n-1) * (n-2) * (n-3))) * np.sum(((data - mean) / std) ** 4) - (3 * (n-1)**2 / ((n-2) * (n-3)))
    return kurtosis + 3  # Excess kurtosis + 3 for standard kurtosis

def calculate_climate_indicators(stats):
    """Calculate climate and environmental indicators"""
    # Urban Heat Island (UHI) intensity classification
    uhi_intensity = stats['max_temp'] - stats['min_temp']
    
    if uhi_intensity > 10:
        uhi_level = "Very Strong"
    elif uhi_intensity > 7:
        uhi_level = "Strong"
    elif uhi_intensity > 5:
        uhi_level = "Moderate"
    elif uhi_intensity > 3:
        uhi_level = "Weak"
    else:
        uhi_level = "Very Weak"
    
    # Temperature stress index
    if stats['mean_temp'] > 35:
        stress_level = "Extreme Heat Stress"
    elif stats['mean_temp'] > 30:
        stress_level = "High Heat Stress"
    elif stats['mean_temp'] > 25:
        stress_level = "Moderate Heat Stress"
    elif stats['mean_temp'] > 20:
        stress_level = "Low Heat Stress"
    else:
        stress_level = "No Heat Stress"
    
    indicators = {
        "uhi_intensity": f"{uhi_intensity:.2f}°C",
        "uhi_level": uhi_level,
        "temperature_stress_level": stress_level,
        "thermal_comfort_index": calculate_thermal_comfort(stats['mean_temp']),
        "environmental_risk_level": assess_environmental_risk(stats)
    }
    
    return indicators

def calculate_thermal_comfort(mean_temp):
    """Calculate thermal comfort index based on temperature"""
    if 18 <= mean_temp <= 24:
        return "Optimal Comfort"
    elif 15 <= mean_temp < 18 or 24 < mean_temp <= 27:
        return "Acceptable Comfort"
    elif 12 <= mean_temp < 15 or 27 < mean_temp <= 30:
        return "Slight Discomfort"
    elif mean_temp < 12 or mean_temp > 30:
        return "Significant Discomfort"
    else:
        return "Unknown"

def assess_environmental_risk(stats):
    """Assess environmental risk level based on temperature statistics"""
    risk_factors = 0
    
    # High maximum temperature
    if stats['max_temp'] > 40:
        risk_factors += 3
    elif stats['max_temp'] > 35:
        risk_factors += 2
    elif stats['max_temp'] > 30:
        risk_factors += 1
    
    # High temperature variability
    if stats['std_temp'] > 5:
        risk_factors += 2
    elif stats['std_temp'] > 3:
        risk_factors += 1
    
    # Large temperature range
    if stats['temp_range'] > 15:
        risk_factors += 2
    elif stats['temp_range'] > 10:
        risk_factors += 1
    
    if risk_factors >= 5:
        return "High Risk"
    elif risk_factors >= 3:
        return "Moderate Risk"
    elif risk_factors >= 1:
        return "Low Risk"
    else:
        return "Minimal Risk"

def generate_insights_summary(context_data):
    """Generate a summary of key insights from the context data"""
    if not context_data:
        return "No data available for analysis."
    
    stats = context_data['statistics']
    insights = context_data['environmental_insights']
    
    summary = f"""
    **Kilimani LST Analysis Summary:**
    
    📊 **Temperature Overview:**
    • Range: {stats['temperature_range']} (from {stats['min_temperature']} to {stats['max_temperature']})
    • Average: {stats['mean_temperature']} ± {stats['standard_deviation']}
    • Heat Island Intensity: {stats['heat_island_intensity']}
    
    🔥 **Heat Distribution:**
    • Hot spots: {stats['hot_pixels_percentage']} of area
    • Cool zones: {stats['cold_pixels_percentage']} of area
    • Temperature variability: {stats['temperature_variability_index']}
    
    🌡️ **Environmental Assessment:**
    • UHI Level: {insights['climate_indicators']['uhi_level']}
    • Thermal Comfort: {insights['climate_indicators']['thermal_comfort_index']}
    • Environmental Risk: {insights['climate_indicators']['environmental_risk_level']}
    """
    
    return summary.strip()

def test_context_data_processing():
    """Unit tests for context data processing functions"""
    # Create sample test data
    test_data = np.array([20, 25, 30, 35, 40, 22, 28, 33, 38, 24])
    test_stats = compute_lst_statistics(test_data)
    
    test_results = []
    
    # Test context data preparation
    try:
        context = prepare_context_data(test_stats, test_data)
        if context and 'statistics' in context:
            test_results.append(("✅", "Context data preparation", "Successfully created context data"))
        else:
            test_results.append(("❌", "Context data preparation", "Failed to create context data"))
    except Exception as e:
        test_results.append(("❌", "Context data preparation", f"Error: {str(e)}"))
    
    # Test heat classification
    try:
        classification = classify_heat_levels(test_stats, test_data)
        if classification and 'extreme_hot_threshold' in classification:
            test_results.append(("✅", "Heat classification", "Successfully classified heat levels"))
        else:
            test_results.append(("❌", "Heat classification", "Failed to classify heat levels"))
    except Exception as e:
        test_results.append(("❌", "Heat classification", f"Error: {str(e)}"))
    
    # Test climate indicators
    try:
        indicators = calculate_climate_indicators(test_stats)
        if indicators and 'uhi_level' in indicators:
            test_results.append(("✅", "Climate indicators", "Successfully calculated climate indicators"))
        else:
            test_results.append(("❌", "Climate indicators", "Failed to calculate climate indicators"))
    except Exception as e:
        test_results.append(("❌", "Climate indicators", f"Error: {str(e)}"))
    
    return test_results

def detect_heat_islands(data, threshold_percentile=90):
    """Detect potential heat island areas"""
    if data is None:
        return None, None
    
    valid_data = data[~np.isnan(data)]
    if len(valid_data) == 0:
        return None, None
    
    threshold = np.percentile(valid_data, threshold_percentile)
    heat_islands = data > threshold
    
    return heat_islands, threshold

def create_ai_response(question, stats, data, analysis_mode="Comprehensive"):
    """Generate sophisticated AI responses using Azure OpenAI about the LST data"""
    if not stats:
        return "I don't have enough data to analyze. Please ensure the LST data is loaded properly."
    
    # Get Azure OpenAI client
    client = get_cached_azure_client()
    if client is None:
        # Fallback to basic responses if Azure OpenAI is not available
        return create_fallback_response(question, stats, data)
    
    try:
        # Prepare context data for AI analysis
        context_data = prepare_context_data(stats, data)
        if not context_data:
            return create_fallback_response(question, stats, data)
        
        # Build system prompt based on analysis mode
        system_prompt = build_system_prompt(context_data, analysis_mode)
        
        # Create user prompt
        user_prompt = f"""Question: {question}

Please analyze this question in the context of the Kilimani LST data and provide a comprehensive, expert-level response. Include relevant statistics from the data and explain the environmental implications."""
        
        # Call Azure OpenAI
        response = client.chat.completions.create(
            model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800,
            temperature=0.7,
            top_p=0.9
        )
        
        # Format and return response
        ai_response = response.choices[0].message.content
        
        # Validate response quality
        is_valid, validation_message = validate_response_quality(ai_response)
        if not is_valid:
            st.warning(f"Response quality issue: {validation_message}")
            log_api_request(success=False, error_type="quality", fallback_used=True)
            return create_fallback_response(question, stats, data)
        
        # Log successful request
        log_api_request(success=True)
        return format_ai_response(ai_response, analysis_mode)
        
    except Exception as e:
        # Determine error type for better handling
        error_str = str(e).lower()
        if "rate limit" in error_str or "quota" in error_str:
            error_type = "rate_limit"
            # Try rate limiting handler
            can_retry, retry_message = handle_api_rate_limiting()
            if can_retry:
                st.info(retry_message)
                # Could implement retry logic here
        elif "authentication" in error_str or "unauthorized" in error_str:
            error_type = "authentication"
        elif "timeout" in error_str:
            error_type = "timeout"
        elif "network" in error_str or "connection" in error_str:
            error_type = "network"
        else:
            error_type = "unknown"
        
        # Log failed request
        log_api_request(success=False, error_type=error_type, fallback_used=True)
        
        # Handle error and provide user feedback
        error_message = handle_azure_openai_error(e)
        st.warning(f"Azure OpenAI Error: {error_message}")
        
        # Return appropriate error recovery response
        return create_error_recovery_response(error_type, question, stats)

def build_system_prompt(context_data, analysis_mode):
    """Build context-aware system prompt for Azure OpenAI"""
    # Base system prompt
    base_prompt = f"""You are an expert environmental data analyst specializing in Land Surface Temperature (LST) analysis and urban heat island studies. You are analyzing satellite temperature data for the Kilimani area in Nairobi, Kenya.

CONTEXT DATA:
Location: {context_data['location']}
Data Type: {context_data['data_type']}
Analysis Timestamp: {context_data['analysis_timestamp']}

TEMPERATURE STATISTICS:
{json.dumps(context_data['statistics'], indent=2)}

ENVIRONMENTAL INSIGHTS:
Heat Classification: {json.dumps(context_data['environmental_insights']['heat_classification'], indent=2)}
Spatial Distribution: {json.dumps(context_data['environmental_insights']['spatial_distribution'], indent=2)}
Climate Indicators: {json.dumps(context_data['environmental_insights']['climate_indicators'], indent=2)}"""
    
    # Analysis mode specific instructions
    if analysis_mode == "Technical":
        complexity_instruction = """
RESPONSE STYLE - TECHNICAL MODE:
- Provide highly technical, scientific explanations with detailed methodology
- Use precise environmental science terminology and statistical concepts
- Include relevant formulas, calculations, and statistical significance
- Reference peer-reviewed research and scientific standards when applicable
- Explain measurement uncertainties and data limitations
- Use advanced concepts like heat flux, thermal conductivity, and radiative forcing"""
        
    elif analysis_mode == "Simple":
        complexity_instruction = """
RESPONSE STYLE - SIMPLE MODE:
- Provide clear, easy-to-understand explanations for general audiences
- Avoid technical jargon and complex terminology
- Use analogies and simple comparisons to explain concepts
- Focus on practical implications and everyday relevance
- Explain "what this means for people living in the area"
- Use conversational language while maintaining accuracy"""
        
    else:  # Comprehensive
        complexity_instruction = """
RESPONSE STYLE - COMPREHENSIVE MODE:
- Provide balanced explanations that are both scientifically accurate and accessible
- Include technical details when relevant but explain them clearly
- Focus on actionable insights and practical applications
- Balance scientific rigor with readability
- Provide context for both technical and non-technical audiences
- Include both immediate and long-term implications"""
    
    # Role and responsibilities
    role_instructions = """
YOUR ROLE AND RESPONSIBILITIES:
1. Provide accurate, scientifically sound explanations about temperature patterns
2. Explain urban heat island effects and their environmental implications
3. Offer insights about climate conditions and environmental health
4. Suggest practical recommendations for urban planning and sustainability
5. Use the provided statistics and context data to support your analysis
6. Address the specific question while providing broader environmental context

IMPORTANT GUIDELINES:
- Always reference specific data points from the provided statistics
- Explain the environmental and health implications of temperature patterns
- Provide actionable recommendations when relevant
- Maintain scientific accuracy while adapting to the specified complexity level
- Focus on the Kilimani area context and its unique characteristics
- Consider both current conditions and future climate resilience"""
    
    return base_prompt + complexity_instruction + role_instructions

def format_ai_response(response, analysis_mode):
    """Format AI response with appropriate styling and structure"""
    # Add analysis mode indicator
    mode_indicator = {
        "Technical": "🔬 **Technical Analysis**",
        "Comprehensive": "📊 **Comprehensive Analysis**", 
        "Simple": "📝 **Simple Explanation**"
    }
    
    formatted_response = f"{mode_indicator.get(analysis_mode, '🤖 **AI Analysis**')}\n\n{response}"
    
    # Add footer with data source
    footer = f"\n\n---\n*Analysis based on Kilimani LST satellite data • Generated using Azure OpenAI • Mode: {analysis_mode}*"
    
    return formatted_response + footer

def create_fallback_response(question, stats, data):
    """Enhanced fallback response function when Azure OpenAI is unavailable"""
    question_lower = question.lower()
    
    # Prepare context for better fallback responses
    context_data = prepare_context_data(stats, data)
    if context_data:
        insights = context_data['environmental_insights']
        climate_indicators = insights['climate_indicators']
    else:
        climate_indicators = None
    
    # Temperature-related questions
    if any(word in question_lower for word in ['temperature', 'temp', 'hot', 'cold', 'warm']):
        if 'highest' in question_lower or 'maximum' in question_lower or 'hottest' in question_lower:
            response = f"🌡️ **Temperature Analysis**: The highest temperature recorded in the Kilimani area is **{stats['max_temp']:.2f}°C**. This represents the hottest surface temperature detected in the satellite imagery, likely corresponding to built-up areas with minimal vegetation or water bodies."
            if climate_indicators:
                response += f"\n\n**Environmental Context**: This falls under the **{climate_indicators['temperature_stress_level']}** category and indicates **{climate_indicators['uhi_level']}** urban heat island intensity."
            return response
            
        elif 'lowest' in question_lower or 'minimum' in question_lower or 'coldest' in question_lower:
            response = f"❄️ **Cool Zones**: The lowest temperature recorded is **{stats['min_temp']:.2f}°C**. These cooler areas typically represent locations with vegetation, water bodies, or shaded areas that provide natural cooling effects."
            if climate_indicators:
                response += f"\n\n**Thermal Comfort**: The overall area shows **{climate_indicators['thermal_comfort_index']}** conditions."
            return response
            
        elif 'average' in question_lower or 'mean' in question_lower:
            response = f"📊 **Average Conditions**: The average surface temperature across Kilimani is **{stats['mean_temp']:.2f}°C**, with a standard deviation of **{stats['std_temp']:.2f}°C**. This indicates moderate temperature variability across the area."
            if climate_indicators:
                response += f"\n\n**Assessment**: This represents **{climate_indicators['temperature_stress_level']}** with **{climate_indicators['environmental_risk_level']}** environmental risk."
            return response
            
        elif 'range' in question_lower:
            response = f"📏 **Temperature Span**: The temperature range spans **{stats['temp_range']:.2f}°C**, from **{stats['min_temp']:.2f}°C** to **{stats['max_temp']:.2f}°C**. This significant range suggests diverse land use patterns affecting local temperatures."
            if climate_indicators:
                response += f"\n\n**UHI Analysis**: This range indicates **{climate_indicators['uhi_level']}** urban heat island effects with intensity of **{climate_indicators['uhi_intensity']}**."
            return response
    
    # Heat island questions
    elif any(word in question_lower for word in ['heat island', 'urban heat', 'hot spots', 'hotspots']):
        hot_percentage = (stats['hot_pixels'] / stats['total_pixels']) * 100
        threshold_90 = np.percentile(data[~np.isnan(data)], 90)
        response = f"🔥 **Heat Island Analysis**: Approximately **{hot_percentage:.1f}%** of the Kilimani area shows heat island characteristics (temperatures above **{threshold_90:.2f}°C**)."
        
        if climate_indicators:
            response += f"\n\n**Classification**: **{climate_indicators['uhi_level']}** UHI intensity with **{climate_indicators['environmental_risk_level']}** environmental risk."
        
        response += f"\n\n**Typical Heat Island Areas**:\n• Dense urban development\n• Areas with minimal vegetation\n• Commercial and industrial zones\n• Paved surfaces and buildings\n\n**💡 Recommendation**: Increase green spaces and tree coverage in these areas to mitigate heat island effects."
        return response
    
    # Statistical questions
    elif any(word in question_lower for word in ['statistics', 'stats', 'distribution']):
        response = f"📈 **Statistical Summary for Kilimani LST Data**:\n\n• **Mean Temperature**: {stats['mean_temp']:.2f}°C\n• **Median Temperature**: {stats['median_temp']:.2f}°C\n• **Standard Deviation**: {stats['std_temp']:.2f}°C\n• **25th Percentile**: {stats['percentile_25']:.2f}°C\n• **75th Percentile**: {stats['percentile_75']:.2f}°C\n• **Temperature Range**: {stats['temp_range']:.2f}°C\n• **Total Data Points**: {stats['total_pixels']:,} pixels"
        
        if climate_indicators:
            response += f"\n\n**Environmental Assessment**:\n• **UHI Level**: {climate_indicators['uhi_level']}\n• **Thermal Comfort**: {climate_indicators['thermal_comfort_index']}\n• **Environmental Risk**: {climate_indicators['environmental_risk_level']}"
        
        return response
    
    # Area/location questions
    elif any(word in question_lower for word in ['area', 'location', 'where', 'kilimani']):
        response = f"🗺️ **Study Area**: This analysis covers the **Kilimani area in Nairobi, Kenya**. The data reveals surface temperature variations across different land use types:\n\n• **Residential areas**: Mixed temperature patterns\n• **Commercial zones**: Generally warmer due to built infrastructure\n• **Green spaces**: Cooler temperatures providing natural cooling\n• **Road networks**: Elevated temperatures from asphalt surfaces"
        
        if climate_indicators:
            response += f"\n\n**Overall Assessment**: The area shows **{climate_indicators['uhi_level']}** urban heat island effects with **{climate_indicators['thermal_comfort_index']}** thermal conditions."
        
        return response
    
    # Data source questions
    elif any(word in question_lower for word in ['data', 'source', 'satellite', 'how']):
        return f"🛰️ **Data Source & Methodology**:\n\n**Land Surface Temperature (LST)** data is derived from satellite imagery, specifically measuring the temperature of the Earth's surface as observed from space.\n\n**Key Points**:\n• Different from air temperature measured by weather stations\n• Excellent for identifying urban heat islands\n• Useful for environmental monitoring and urban planning\n• Provides spatial temperature patterns across large areas\n• Helps identify areas needing climate adaptation measures\n\n**Current Dataset**: Covers {stats['total_pixels']:,} measurement points across Kilimani area."
    
    # General questions
    else:
        response = f"🌍 **Kilimani LST Analysis Overview**:\n\n**Key Findings**:\n• Temperature range: **{stats['temp_range']:.2f}°C** (from {stats['min_temp']:.2f}°C to {stats['max_temp']:.2f}°C)\n• Average temperature: **{stats['mean_temp']:.2f}°C**\n• Heat island areas: **{(stats['hot_pixels']/stats['total_pixels']*100):.1f}%** of total area\n• Data coverage: **{stats['total_pixels']:,}** measurement points"
        
        if climate_indicators:
            response += f"\n\n**Environmental Assessment**:\n• **UHI Level**: {climate_indicators['uhi_level']}\n• **Thermal Comfort**: {climate_indicators['thermal_comfort_index']}\n• **Environmental Risk**: {climate_indicators['environmental_risk_level']}"
        
        response += f"\n\n**Environmental Insights**:\n• Significant temperature variations suggest diverse land use\n• Heat island effects present in built-up areas\n• Opportunities for green infrastructure improvements\n\n💡 **Ask me specific questions about temperatures, heat islands, statistics, or environmental recommendations!**"
        
        return response

def create_advanced_temperature_map(data, bounds, transform):
    """Create advanced interactive temperature map with LST overlay"""
    if data is None or bounds is None:
        return None
    
    # Calculate center coordinates
    center_lat = (bounds.bottom + bounds.top) / 2
    center_lon = (bounds.left + bounds.right) / 2
    
    # Create folium map with multiple tile options
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles=None  # We'll add custom tiles
    )
    
    # Add multiple tile layers
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='OpenStreetMap',
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Hybrid',
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='CartoDB positron',
        name='CartoDB Light',
        control=True
    ).add_to(m)
    
    # Create temperature overlay
    try:
        # Normalize data for visualization (0-1 range)
        valid_data = data[~np.isnan(data)]
        if len(valid_data) > 0:
            data_normalized = (data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data))
            
            # Create colormap
            from matplotlib.colors import LinearSegmentedColormap
            import matplotlib.cm as cm
            
            # Use a temperature colormap
            colormap = cm.get_cmap('RdYlBu_r')  # Red-Yellow-Blue reversed (hot to cold)
            
            # Convert to RGBA
            rgba_data = colormap(data_normalized)
            rgba_data[np.isnan(data)] = [0, 0, 0, 0]  # Transparent for NaN values
            
            # Convert to image
            from PIL import Image
            img = Image.fromarray((rgba_data * 255).astype(np.uint8))
            
            # Save to bytes
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Add as image overlay
            folium.raster_layers.ImageOverlay(
                image=f"data:image/png;base64,{img_str}",
                bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
                opacity=0.7,
                name="LST Overlay"
            ).add_to(m)
    
    except Exception as e:
        st.warning(f"Could not create temperature overlay: {str(e)}")
        # Fallback to simple rectangle
        folium.Rectangle(
            bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
            popup="Temperature Data Coverage",
            tooltip="LST Data Area",
            color="red",
            weight=2,
            fill=True,
            fillColor="orange",
            fillOpacity=0.4
        ).add_to(m)
    
    # Add search functionality
    plugins.Geocoder().add_to(m)
    
    # Add measurement tool
    plugins.MeasureControl().add_to(m)
    
    # Add fullscreen option
    plugins.Fullscreen().add_to(m)
    
    # Add mouse position
    plugins.MousePosition().add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add temperature legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 150px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px; border-radius: 5px;">
    <p><b>Temperature (°C)</b></p>
    <p><i class="fa fa-square" style="color:darkred"></i> Very Hot (&gt;35°C)</p>
    <p><i class="fa fa-square" style="color:red"></i> Hot (30-35°C)</p>
    <p><i class="fa fa-square" style="color:orange"></i> Warm (25-30°C)</p>
    <p><i class="fa fa-square" style="color:yellow"></i> Moderate (20-25°C)</p>
    <p><i class="fa fa-square" style="color:blue"></i> Cool (&lt;20°C)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def generate_sample_temperature_data():
    """Generate sample temperature data for demonstration"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    base_temp = 25
    seasonal_variation = 5 * np.sin(2 * np.pi * np.arange(len(dates)) / 365)
    daily_variation = np.random.normal(0, 2, len(dates))
    temperatures = base_temp + seasonal_variation + daily_variation
    
    return pd.DataFrame({
        'date': dates,
        'temperature': temperatures,
        'heat_index': temperatures + np.random.normal(2, 1, len(dates))
    })

def main():
    st.title("🌡️ Kilimani Land Surface Temperature Analysis")
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Azure OpenAI Status Section
        st.subheader("🤖 AI Analysis")
        azure_status = display_azure_openai_status()
        
        # Analysis Mode Selection
        st.subheader("📊 Analysis Settings")
        analysis_mode = st.selectbox(
            "AI Response Mode",
            ["Comprehensive", "Technical", "Simple"],
            help="Choose the complexity level of AI responses"
        )
        
        # Store analysis mode in session state
        st.session_state['analysis_mode'] = analysis_mode
        
        # Mode descriptions
        if analysis_mode == "Technical":
            st.info("🔬 **Technical Mode**: Detailed scientific explanations with methodology and calculations")
        elif analysis_mode == "Simple":
            st.info("📝 **Simple Mode**: Easy-to-understand explanations for general audiences")
        else:
            st.info("📊 **Comprehensive Mode**: Balanced, detailed insights with practical applications")
        
        st.markdown("---")
        
        # API Usage Statistics
        if azure_status:
            st.subheader("📈 API Usage")
            display_api_usage_stats()
            
            # Test Azure OpenAI Connection
            if st.button("🔍 Test Connection"):
                with st.spinner("Testing Azure OpenAI connection..."):
                    client = get_cached_azure_client()
                    if client:
                        is_connected, message = test_azure_openai_connection(client)
                        if is_connected:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Client not available")
        
        st.markdown("---")
        
        # Advanced Settings
        st.subheader("⚙️ Advanced Settings")
        
        # Temperature Analysis Settings
        with st.expander("🌡️ Temperature Analysis"):
            temp_unit = st.selectbox("Temperature Unit", ["Celsius", "Fahrenheit"], index=0)
            show_percentiles = st.checkbox("Show Percentile Analysis", value=True)
            include_climate_indicators = st.checkbox("Include Climate Indicators", value=True)
        
        # Error Handling Settings
        with st.expander("🛡️ Error Handling"):
            enable_fallback = st.checkbox("Enable Fallback Responses", value=True, help="Use basic analysis when Azure OpenAI is unavailable")
            max_retries = st.slider("Max API Retries", 1, 5, 3, help="Maximum retry attempts for failed API calls")
            show_error_details = st.checkbox("Show Detailed Error Messages", value=False)
        
        # Diagnostic Tools
        st.subheader("🔧 Diagnostic Tools")
        
        if st.button("🧪 Run System Tests"):
            with st.spinner("Running comprehensive system tests..."):
                test_results = run_comprehensive_error_tests()
                
        if st.button("📊 Show Context Data"):
            if 'stats' in locals():
                with st.spinner("Preparing context data..."):
                    context = prepare_context_data(stats, data if 'data' in locals() else None)
                    if context:
                        st.json(context)
                    else:
                        st.warning("No context data available")
    
    # System Status Banner
    status_col1, status_col2, status_col3 = st.columns([2, 1, 1])
    
    with status_col1:
        if azure_status:
            st.success("🤖 **Azure OpenAI Enabled** - Advanced AI analysis available")
        else:
            st.info("💡 **Basic Mode** - Configure Azure OpenAI for advanced analysis")
    
    with status_col2:
        # Show current analysis mode
        current_mode = st.session_state.get('analysis_mode', 'Comprehensive')
        mode_colors = {"Technical": "🔬", "Comprehensive": "📊", "Simple": "📝"}
        st.info(f"{mode_colors.get(current_mode, '📊')} **{current_mode}**")
    
    with status_col3:
        # Show system health
        config, missing_vars = validate_azure_openai_config()
        if len(missing_vars) == 0:
            st.success("✅ **System Ready**")
        else:
            st.warning("⚙️ **Setup Needed**")
    
    st.markdown("---")
    
    # Load LST data first
    with st.spinner("Loading Kilimani LST data..."):
        data, bounds, crs, transform = load_lst_data()
    
    if data is not None:
        # Compute statistics
        stats = compute_lst_statistics(data)
        
        # Main content - Temperature Map
        st.header("🗺️ Interactive Temperature Map")
        st.markdown("*Explore the Land Surface Temperature data for Kilimani area with multiple map layers and search functionality*")
        
        # Map controls
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            opacity = st.slider("Temperature Overlay Opacity", 0.0, 1.0, 0.7, 0.1)
        with col2:
            show_heat_islands = st.checkbox("Show Heat Islands", value=False)
        with col3:
            heat_threshold = st.slider("Heat Island Threshold (%)", 80, 95, 90, 5)
        
        # Create and display map
        temp_map = create_advanced_temperature_map(data, bounds, transform)
        if temp_map:
            map_data = st_folium(temp_map, width=None, height=600, returned_objects=["last_clicked"])
        
        # Temperature Statistics Section
        st.header("📊 Temperature Analysis Results")
        
        if stats:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Average Temperature", f"{stats['mean_temp']:.2f}°C", 
                         delta=f"±{stats['std_temp']:.2f}°C")
            with col2:
                st.metric("Temperature Range", f"{stats['temp_range']:.2f}°C",
                         delta=f"{stats['min_temp']:.1f}°C to {stats['max_temp']:.1f}°C")
            with col3:
                st.metric("Hot Spots", f"{stats['hot_pixels']:,} pixels",
                         delta=f"{(stats['hot_pixels']/stats['total_pixels']*100):.1f}% of area")
            with col4:
                st.metric("Data Coverage", f"{stats['total_pixels']:,} pixels",
                         delta="Valid measurements")
            
            # Detailed analysis
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Temperature Distribution")
                
                # Create histogram
                valid_data = data[~np.isnan(data)].flatten()
                fig = px.histogram(
                    x=valid_data, 
                    nbins=50,
                    title="Temperature Distribution",
                    labels={'x': 'Temperature (°C)', 'y': 'Frequency'},
                    color_discrete_sequence=['#ff6b6b']
                )
                fig.add_vline(x=stats['mean_temp'], line_dash="dash", 
                             annotation_text=f"Mean: {stats['mean_temp']:.1f}°C")
                fig.add_vline(x=np.percentile(valid_data, 90), line_dash="dot", 
                             annotation_text=f"90th percentile: {np.percentile(valid_data, 90):.1f}°C")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Statistical Summary")
                
                # Create box plot
                fig = go.Figure()
                fig.add_trace(go.Box(
                    y=valid_data,
                    name="Temperature",
                    boxpoints='outliers',
                    marker_color='#ff6b6b'
                ))
                fig.update_layout(
                    title="Temperature Box Plot",
                    yaxis_title="Temperature (°C)",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Heat Island Analysis
            if show_heat_islands:
                st.subheader("🔥 Heat Island Analysis")
                
                heat_islands, threshold = detect_heat_islands(data, heat_threshold)
                if heat_islands is not None:
                    heat_island_pixels = np.sum(heat_islands)
                    heat_island_percentage = (heat_island_pixels / stats['total_pixels']) * 100
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Heat Island Threshold", f"{threshold:.2f}°C")
                    with col2:
                        st.metric("Heat Island Pixels", f"{heat_island_pixels:,}")
                    with col3:
                        st.metric("Heat Island Coverage", f"{heat_island_percentage:.2f}%")
                    
                    st.info(f"Areas with temperatures above {threshold:.2f}°C are classified as potential heat islands.")
        
        # AI Chat Interface
        st.header("🤖 AI Assistant - Ask Questions About the Data")
        
        # Enhanced status indicators for AI chat
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if azure_status:
                st.success("✅ **Azure OpenAI Active** - Advanced analysis available")
            else:
                st.warning("⚠️ **Fallback Mode** - Basic analysis available")
        
        with col2:
            current_mode = st.session_state.get('analysis_mode', 'Comprehensive')
            mode_icons = {"Technical": "🔬", "Comprehensive": "📊", "Simple": "📝"}
            st.info(f"{mode_icons.get(current_mode, '📊')} **{current_mode} Mode**")
        
        with col3:
            # Show API usage summary
            usage_stats = monitor_api_usage()
            if usage_stats['total_requests'] > 0:
                success_rate = (usage_stats['successful_requests'] / usage_stats['total_requests']) * 100
                st.metric("Success Rate", f"{success_rate:.0f}%")
        
        st.markdown("*Ask questions about the temperature data, heat islands, statistics, or the Kilimani area*")
        
        # Chat interface with enhanced display
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Display chat history with improved formatting
        if st.session_state.chat_history:
            st.subheader("💬 Conversation History")
            for i, (question, answer) in enumerate(st.session_state.chat_history):
                with st.container():
                    # Question with timestamp
                    st.markdown(f"**🙋 You ({len(st.session_state.chat_history) - i} questions ago):** {question}")
                    
                    # Answer with enhanced formatting
                    with st.container():
                        st.markdown(answer)
                    
                    st.markdown("---")
        
        # Input section with enhanced controls
        st.subheader("❓ Ask a New Question")
        
        # Input for new question
        user_question = st.text_input(
            "Your question:",
            placeholder="e.g., What's the hottest temperature recorded? Where are the heat islands?",
            key="user_input",
            help=f"Currently using {current_mode} analysis mode. Change in sidebar if needed."
        )
        
        # Enhanced button controls
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            ask_button = st.button("🤖 Ask AI", type="primary", use_container_width=True)
        with col2:
            clear_button = st.button("🗑️ Clear Chat", use_container_width=True)
        with col3:
            if st.button("📊 Show Stats", use_container_width=True):
                st.session_state['show_context_stats'] = True
        with col4:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        # Handle button actions
        if ask_button and user_question.strip():
            with st.spinner(f"🤖 {'Azure OpenAI' if azure_status else 'Basic AI'} is analyzing your question..."):
                # Get analysis mode from session state
                analysis_mode = st.session_state.get('analysis_mode', 'Comprehensive')
                ai_response = create_ai_response(user_question, stats, data, analysis_mode)
                st.session_state.chat_history.append((user_question, ai_response))
                st.rerun()
        
        if clear_button:
            st.session_state.chat_history = []
            st.rerun()
        
        # Show context stats if requested
        if st.session_state.get('show_context_stats', False):
            with st.expander("📊 Current Analysis Context", expanded=True):
                context_data = prepare_context_data(stats, data)
                if context_data:
                    st.json(context_data)
                    if st.button("Hide Context"):
                        st.session_state['show_context_stats'] = False
                        st.rerun()
                else:
                    st.warning("No context data available")
        
        # Enhanced sample questions organized by category
        st.subheader("💡 Sample Questions")
        
        # Organize questions by category
        question_categories = {
            "🌡️ Temperature Basics": [
                "What's the average temperature in Kilimani?",
                "What's the temperature range across the area?",
                "Where are the hottest and coolest areas?"
            ],
            "🔥 Heat Island Analysis": [
                "How much of the area shows heat island effects?",
                "What causes the heat islands in this area?",
                "How can we reduce urban heat island effects?"
            ],
            "📊 Statistical Analysis": [
                "Tell me about the temperature statistics",
                "What's the temperature distribution pattern?",
                "How variable are the temperatures across the area?"
            ],
            "🌍 Environmental Impact": [
                "What are the environmental implications?",
                "How does this affect thermal comfort?",
                "What recommendations do you have for urban planning?"
            ]
        }
        
        # Display questions in tabs or expandable sections
        tabs = st.tabs(list(question_categories.keys()))
        
        for tab, (category, questions) in zip(tabs, question_categories.items()):
            with tab:
                for i, question in enumerate(questions):
                    if st.button(question, key=f"sample_{category}_{i}", use_container_width=True):
                        with st.spinner(f"🤖 {'Azure OpenAI' if azure_status else 'Basic AI'} is analyzing..."):
                            analysis_mode = st.session_state.get('analysis_mode', 'Comprehensive')
                            ai_response = create_ai_response(question, stats, data, analysis_mode)
                            st.session_state.chat_history.append((question, ai_response))
                            st.rerun()
        
        # Quick action buttons
        st.markdown("---")
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Generate Summary Report", use_container_width=True):
                summary_question = "Generate a comprehensive summary report of the Kilimani temperature analysis including key findings, environmental implications, and recommendations."
                with st.spinner("Generating comprehensive report..."):
                    analysis_mode = st.session_state.get('analysis_mode', 'Comprehensive')
                    ai_response = create_ai_response(summary_question, stats, data, analysis_mode)
                    st.session_state.chat_history.append((summary_question, ai_response))
                    st.rerun()
        
        with col2:
            if st.button("🏙️ Urban Planning Insights", use_container_width=True):
                planning_question = "What are the key urban planning recommendations based on this temperature analysis? Focus on heat mitigation strategies and sustainable development."
                with st.spinner("Analyzing urban planning implications..."):
                    analysis_mode = st.session_state.get('analysis_mode', 'Comprehensive')
                    ai_response = create_ai_response(planning_question, stats, data, analysis_mode)
                    st.session_state.chat_history.append((planning_question, ai_response))
                    st.rerun()
        
        with col3:
            if st.button("🌱 Climate Adaptation", use_container_width=True):
                climate_question = "How can Kilimani adapt to climate change based on this temperature data? What are the priority areas for intervention?"
                with st.spinner("Analyzing climate adaptation strategies..."):
                    analysis_mode = st.session_state.get('analysis_mode', 'Comprehensive')
                    ai_response = create_ai_response(climate_question, stats, data, analysis_mode)
                    st.session_state.chat_history.append((climate_question, ai_response))
                    st.rerun()
    
    else:
        st.error("❌ Could not load the Kilimani LST data. Please ensure the file 'Kilimani_LST_Prediction.tif' is in the root directory.")
        st.info("📁 Expected file location: `Kilimani_LST_Prediction.tif`")
        
        # Show file upload option as fallback
        st.subheader("Upload LST Data")
        uploaded_file = st.file_uploader(
            "Upload your LST TIFF file",
            type=['tif', 'tiff'],
            help="Upload a GeoTIFF file containing Land Surface Temperature data"
        )
        
        if uploaded_file is not None:
            st.info("File upload functionality would be implemented here for processing custom LST data.")

if __name__ == "__main__":
    main()