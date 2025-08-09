# Environmental Analysis App

A comprehensive Streamlit web application for environmental analysis focused on urban climate and sustainability metrics. This application provides interactive analysis tools for temperature patterns, green space impact assessment, and building environmental impact evaluation.

## Features

- **Temperature Analysis**: Analyze urban temperature patterns and identify heat islands
- **Green Space Impact**: Assess the cooling effects and environmental benefits of vegetation
- **Building Impact**: Evaluate environmental performance and energy efficiency of buildings
- **Interactive Visualizations**: Maps, charts, and statistical analysis tools
- **Data Export**: Download reports, charts, and processed data

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd joto-streamlit-app
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to `http://localhost:8501`

3. Use the sidebar navigation to access different analysis tools:
   - Temperature Analysis
   - Green Space Impact
   - Building Impact

## Data Requirements

### Temperature Analysis
- Land Surface Temperature (LST) data in TIFF format
- Optional: Additional temperature datasets in CSV format

### Green Space Impact
- Geospatial boundary data (Shapefile or GeoJSON)
- Vegetation indices or land cover data
- Temperature measurements for correlation analysis

### Building Impact
- Building characteristics (size, materials, age, orientation)
- Energy consumption data
- Location coordinates

## Project Structure

```
joto-streamlit-app/
├── app.py                          # Main application entry point
├── pages/                          # Streamlit pages
│   ├── 1_Temperature_Analysis.py   # Temperature analysis page
│   ├── 2_Green_Space_Impact.py     # Green space analysis page
│   └── 3_Building_Impact.py        # Building assessment page
├── utils/                          # Utility modules
│   ├── data_processing.py          # Data validation and processing
│   ├── visualization.py            # Chart and map generation
│   └── calculations.py             # Environmental calculations
├── assets/                         # Static assets
│   ├── styles.css                  # Custom styling
│   └── images/                     # Application images
├── resources/data/                 # Data directory
│   └── Kilimani_LST_Prediction.tif # Sample LST data
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues, please open an issue on the GitHub repository.