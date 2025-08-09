"""
Data processing utilities for environmental analysis
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.plot import show
from pathlib import Path
import streamlit as st
from typing import Optional, Tuple, Dict, Any, List
import json
from shapely.geometry import Point, Polygon
import tempfile
import os

def validate_geospatial_data(uploaded_file) -> Tuple[bool, str, Optional[gpd.GeoDataFrame]]:
    """
    Validate uploaded geospatial files (Shapefile, GeoJSON)
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Tuple of (is_valid, message, geodataframe)
    """
    try:
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        if file_extension == '.geojson':
            # Handle GeoJSON files
            geojson_data = json.loads(uploaded_file.read().decode('utf-8'))
            gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
            
            if gdf.empty:
                return False, "GeoJSON file contains no features", None
                
            # Set CRS if not present
            if gdf.crs is None:
                gdf.set_crs(epsg=4326, inplace=True)
                
            return True, f"Successfully loaded {len(gdf)} features from GeoJSON", gdf
            
        elif file_extension == '.shp':
            # Handle Shapefile (note: this is simplified - real implementation would need all shapefile components)
            return False, "Shapefile upload requires all components (.shp, .shx, .dbf). Please use GeoJSON format.", None
            
        else:
            return False, f"Unsupported file format: {file_extension}. Please use GeoJSON format.", None
            
    except json.JSONDecodeError:
        return False, "Invalid GeoJSON format", None
    except Exception as e:
        return False, f"Error processing file: {str(e)}", None

def process_temperature_data(uploaded_file) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Process and clean temperature datasets
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Tuple of (is_valid, message, dataframe)
    """
    try:
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        if file_extension == '.csv':
            df = pd.read_csv(uploaded_file)
            
            # Check for required columns
            required_columns = ['temperature']
            optional_columns = ['date', 'latitude', 'longitude', 'location']
            
            missing_required = [col for col in required_columns if col not in df.columns]
            if missing_required:
                return False, f"Missing required columns: {missing_required}", None
            
            # Validate temperature data
            if df['temperature'].isnull().all():
                return False, "Temperature column contains no valid data", None
                
            # Check temperature range (reasonable values)
            temp_min, temp_max = df['temperature'].min(), df['temperature'].max()
            if temp_min < -50 or temp_max > 60:
                return False, f"Temperature values outside reasonable range: {temp_min}°C to {temp_max}°C", None
            
            # Process date column if present
            if 'date' in df.columns:
                try:
                    df['date'] = pd.to_datetime(df['date'])
                except:
                    return False, "Invalid date format. Please use standard date formats (YYYY-MM-DD, etc.)", None
            
            # Validate coordinates if present
            if 'latitude' in df.columns and 'longitude' in df.columns:
                if df['latitude'].min() < -90 or df['latitude'].max() > 90:
                    return False, "Invalid latitude values (must be between -90 and 90)", None
                if df['longitude'].min() < -180 or df['longitude'].max() > 180:
                    return False, "Invalid longitude values (must be between -180 and 180)", None
            
            return True, f"Successfully processed {len(df)} temperature records", df
            
        else:
            return False, f"Unsupported file format: {file_extension}. Please use CSV format.", None
            
    except Exception as e:
        return False, f"Error processing temperature data: {str(e)}", None

def load_lst_data(file_path: str = "resources/data/Kilimani_LST_Prediction.tif") -> Tuple[Optional[np.ndarray], Optional[rasterio.coords.BoundingBox], Optional[Any]]:
    """
    Load and preprocess LST raster data
    
    Args:
        file_path: Path to LST TIFF file
        
    Returns:
        Tuple of (data_array, bounds, crs)
    """
    try:
        if not Path(file_path).exists():
            st.warning(f"LST data file not found at {file_path}")
            return None, None, None
            
        with rasterio.open(file_path) as src:
            # Read the first band
            data = src.read(1)
            bounds = src.bounds
            crs = src.crs
            
            # Basic data validation
            if data.size == 0:
                st.error("LST file contains no data")
                return None, None, None
                
            # Handle no-data values
            if hasattr(src, 'nodata') and src.nodata is not None:
                data = np.where(data == src.nodata, np.nan, data)
            
            return data, bounds, crs
            
    except rasterio.errors.RasterioIOError:
        st.error(f"Cannot read raster file: {file_path}")
        return None, None, None
    except Exception as e:
        st.error(f"Error loading LST data: {str(e)}")
        return None, None, None

def handle_file_upload(uploaded_file, file_type: str) -> Tuple[bool, str, Optional[Any]]:
    """
    Generic file upload and validation handler
    
    Args:
        uploaded_file: Streamlit uploaded file object
        file_type: Type of file ('temperature', 'geospatial', 'building')
        
    Returns:
        Tuple of (is_valid, message, processed_data)
    """
    if uploaded_file is None:
        return False, "No file uploaded", None
    
    # Check file size (limit to 50MB)
    if uploaded_file.size > 50 * 1024 * 1024:
        return False, "File size too large. Please upload files smaller than 50MB.", None
    
    try:
        if file_type == 'temperature':
            return process_temperature_data(uploaded_file)
        elif file_type == 'geospatial':
            return validate_geospatial_data(uploaded_file)
        elif file_type == 'building':
            return process_building_data(uploaded_file)
        else:
            return False, f"Unknown file type: {file_type}", None
            
    except Exception as e:
        return False, f"Error processing file: {str(e)}", None

def process_building_data(uploaded_file) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Process building characteristics data
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Tuple of (is_valid, message, dataframe)
    """
    try:
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        if file_extension in ['.csv', '.xlsx']:
            if file_extension == '.csv':
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Check for required columns
            required_columns = ['building_id', 'size_sqm']
            optional_columns = ['age', 'type', 'energy_consumption', 'insulation_rating', 'energy_source']
            
            missing_required = [col for col in required_columns if col not in df.columns]
            if missing_required:
                return False, f"Missing required columns: {missing_required}", None
            
            # Validate building data
            if df['size_sqm'].isnull().any() or (df['size_sqm'] <= 0).any():
                return False, "Invalid building size values", None
            
            # Clean and validate optional columns
            if 'age' in df.columns:
                df['age'] = pd.to_numeric(df['age'], errors='coerce')
                df['age'] = df['age'].fillna(20)  # Default age
                
            if 'energy_consumption' in df.columns:
                df['energy_consumption'] = pd.to_numeric(df['energy_consumption'], errors='coerce')
                
            return True, f"Successfully processed {len(df)} building records", df
            
        else:
            return False, f"Unsupported file format: {file_extension}. Please use CSV or Excel format.", None
            
    except Exception as e:
        return False, f"Error processing building data: {str(e)}", None

def create_sample_temperature_data(start_date: str = "2024-01-01", end_date: str = "2024-12-31") -> pd.DataFrame:
    """
    Create sample temperature data for demonstration purposes
    
    Args:
        start_date: Start date for data generation
        end_date: End date for data generation
        
    Returns:
        DataFrame with sample temperature data
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    n_days = len(dates)
    
    # Generate realistic temperature patterns
    base_temp = 25  # Base temperature in Celsius
    
    # Seasonal variation (sinusoidal)
    day_of_year = dates.dayofyear
    seasonal_variation = 5 * np.sin(2 * np.pi * (day_of_year - 80) / 365)  # Peak in summer
    
    # Random daily variation
    daily_variation = np.random.normal(0, 2, n_days)
    
    # Weekend effect (slightly different pattern)
    weekend_effect = np.where(dates.weekday >= 5, np.random.normal(0.5, 0.5, n_days), 0)
    
    temperatures = base_temp + seasonal_variation + daily_variation + weekend_effect
    
    # Generate coordinates (Nairobi area)
    latitudes = np.random.uniform(-1.35, -1.25, n_days)
    longitudes = np.random.uniform(36.75, 36.85, n_days)
    
    return pd.DataFrame({
        'date': dates,
        'temperature': temperatures,
        'latitude': latitudes,
        'longitude': longitudes,
        'heat_index': temperatures + np.random.normal(2, 1, n_days),
        'location': [f"Location_{i%10}" for i in range(n_days)]
    })

def export_data_to_csv(data: pd.DataFrame, filename: str) -> str:
    """
    Export DataFrame to CSV format for download
    
    Args:
        data: DataFrame to export
        filename: Name for the exported file
        
    Returns:
        CSV string for download
    """
    try:
        return data.to_csv(index=False)
    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")
        return ""

def calculate_data_statistics(data: pd.DataFrame, column: str) -> Dict[str, float]:
    """
    Calculate basic statistics for a data column
    
    Args:
        data: DataFrame containing the data
        column: Column name to analyze
        
    Returns:
        Dictionary with statistical measures
    """
    try:
        if column not in data.columns:
            return {}
            
        series = data[column].dropna()
        
        return {
            'count': len(series),
            'mean': series.mean(),
            'median': series.median(),
            'std': series.std(),
            'min': series.min(),
            'max': series.max(),
            'q25': series.quantile(0.25),
            'q75': series.quantile(0.75)
        }
        
    except Exception as e:
        st.error(f"Error calculating statistics: {str(e)}")
        return {}