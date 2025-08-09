import streamlit as st
from pathlib import Path

# Define pages using st.Page
home_page = st.Page("pages/home.py", title="Dashboard", icon="🌍", default=True)
temperature_page = st.Page("pages/1_Temperature_Analysis.py", title="Temperature Analysis", icon="🌡️")
green_space_page = st.Page("pages/2_Green_Space_Impact.py", title="Green Space Impact", icon="🌳")
building_page = st.Page("pages/3_Building_Impact.py", title="Building Impact", icon="🏢")
community_page = st.Page("pages/4_Community_Voting.py", title="Community Voting", icon="🗳️")
modules_page = st.Page("pages/modules.py", title="Modules", icon="🔧")

# Create navigation
pg = st.navigation([
    home_page,
    temperature_page, 
    green_space_page,
    building_page,
    community_page,
    modules_page
])

# Configure Streamlit page
st.set_page_config(
    page_title="Environmental Analysis App",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/environmental-analysis-app',
        'Report a bug': "https://github.com/your-repo/environmental-analysis-app/issues",
        'About': "# Environmental Analysis App \n🌍 Comprehensive tools for urban environmental analysis and sustainability assessment!"
    }
)

# Load custom CSS
def load_css():
    """Load custom CSS styling"""
    css_file = Path("assets/styles.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state variables
def initialize_session_state():
    """Initialize session state variables for data persistence"""
    if 'temperature_data' not in st.session_state:
        st.session_state.temperature_data = None
    if 'green_space_data' not in st.session_state:
        st.session_state.green_space_data = None
    if 'building_data' not in st.session_state:
        st.session_state.building_data = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    
    # Community voting data initialization
    if 'development_plans' not in st.session_state:
        st.session_state.development_plans = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}
    if 'vote_history' not in st.session_state:
        st.session_state.vote_history = {}

# Load styling and initialize session state
load_css()
initialize_session_state()

# Run the navigation
pg.run()