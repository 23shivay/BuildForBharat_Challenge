import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# ==============================================================================
# CONFIGURATION & MAPPINGS
# ==============================================================================

# --- API Keys ---
# Try to load from environment variables first, fall back to hardcoded values
CROP_API_KEY = os.getenv('CROP_API_KEY')
RAIN_API_KEY = os.getenv('RAIN_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Support Streamlit Cloud secrets
try:
    import streamlit as st
    if hasattr(st, 'secrets'):
        CROP_API_KEY = st.secrets.get('CROP_API_KEY', CROP_API_KEY)
        RAIN_API_KEY = st.secrets.get('RAIN_API_KEY', RAIN_API_KEY)
        GROQ_API_KEY = st.secrets.get('GROQ_API_KEY', GROQ_API_KEY)
except:
    pass

# --- API Resource IDs ---
CROP_RESOURCE_ID = "35be999b-0208-4354-b557-f6ca9a5355de"
RAIN_RESOURCE_ID = "8e0bd482-4aba-4d99-9cb9-ff124f6f1c2f"
DATA_GOV_BASE_URL = "https://api.data.gov.in/resource/"

# --- DEMO & QUERY PARAMETERS ---
DEMO_STATE_X = "Maharashtra"
DEMO_STATE_Y = "Karnataka"
DEMO_YEARS = 5
DEFAULT_CROP_Z = "Rice"

# Set to 2010 due to API data availability constraints
CURRENT_ANALYSIS_YEAR = 2010

# --- COMPREHENSIVE GEOGRAPHIC MAPPING ---
# Maps Indian states to their corresponding IMD subdivisions
IMD_SUBDIVISION_MAP = {
    "Andhra Pradesh": ["Coastal Andhra Pradesh", "Rayalaseema"],
    "Arunachal Pradesh": ["Arunachal Pradesh"],
    "Assam": ["Assam & Meghalaya"],
    "Bihar": ["Bihar"],
    "Chhattisgarh": ["Chhattisgarh"],
    "Delhi": ["Haryana Chandigarh & Delhi"],
    "Goa": ["Konkan and Goa"],
    "Gujarat": ["Gujarat Region", "Saurashtra and Kutch"],
    "Haryana": ["Haryana Chandigarh & Delhi"],
    "Himachal Pradesh": ["Himachal Pradesh"],
    "Jammu and Kashmir": ["Jammu & Kashmir"],
    "Jharkhand": ["Jharkhand"],
    "Karnataka": ["Coastal Karnataka", "North Interior Karnataka", "South Interior Karnataka"],
    "Kerala": ["Kerala"],
    "Madhya Pradesh": ["East Madhya Pradesh", "West Madhya Pradesh"],
    "Maharashtra": ["Konkan and Goa", "Madhya Maharashtra", "Marathwada", "Vidarbha"],
    "Manipur": ["Sub Himalayan West Bengal & Sikkim"],
    "Meghalaya": ["Assam & Meghalaya"],
    "Mizoram": ["Sub Himalayan West Bengal & Sikkim"],
    "Nagaland": ["Nagaland Manipur Mizoram & Tripura"],
    "Odisha": ["Odisha"],
    "Punjab": ["Punjab"],
    "Rajasthan": ["East Rajasthan", "West Rajasthan"],
    "Sikkim": ["Sub Himalayan West Bengal & Sikkim"],
    "Tamil Nadu": ["Tamil Nadu"],
    "Telangana": ["Telangana"],
    "Tripura": ["Nagaland Manipur Mizoram & Tripura"],
    "Uttar Pradesh": ["East Uttar Pradesh", "West Uttar Pradesh"],
    "Uttarakhand": ["Uttarakhand"],
    "West Bengal": ["Gangetic West Bengal", "Sub Himalayan West Bengal & Sikkim"],
}

# --- CROP CLASSIFICATION ---
CROP_TYPES = {
    "Cereals": ["Rice", "Wheat", "Maize", "Jowar", "Bajra", "Ragi", "Small millets", "Barley"],
    "Pulses": ["Gram", "Tur", "Urad", "Moong", "Masoor", "Lentil", "Other Kharif pulses", 
               "Other Rabi pulses", "Peas & beans", "Arhar/Tur", "Moth", "Horse-gram"],
    "Oilseeds": ["Groundnut", "Sesamum", "Rapeseed & Mustard", "Linseed", "Castor seed", 
                 "Safflower", "Sunflower", "Soyabean", "Niger seed", "Coconut"],
    "Cash Crops": ["Sugarcane", "Cotton", "Jute", "Mesta", "Tea", "Coffee", "Rubber", "Tobacco"],
    "Spices": ["Black pepper", "Dry chillies", "Turmeric", "Ginger", "Coriander", "Garlic"],
    "Fruits": ["Banana", "Mango", "Orange", "Apple", "Grapes"],
    "Vegetables": ["Potato", "Onion", "Tomato", "Cabbage", "Cauliflower"]
}

# --- CROP WATER REQUIREMENTS & ATTRIBUTES ---
CROP_ATTRIBUTES = {
    # High Water Use
    "Rice": {"Water_Use": "High", "Type": "Cereal", "Sensitivity": "High"},
    "Sugarcane": {"Water_Use": "High", "Type": "Cash", "Sensitivity": "High"},
    "Banana": {"Water_Use": "High", "Type": "Fruit", "Sensitivity": "High"},
    
    # Moderate Water Use
    "Wheat": {"Water_Use": "Moderate", "Type": "Cereal", "Sensitivity": "Moderate"},
    "Maize": {"Water_Use": "Moderate", "Type": "Cereal", "Sensitivity": "Moderate"},
    "Cotton": {"Water_Use": "Moderate", "Type": "Cash", "Sensitivity": "Moderate"},
    "Groundnut": {"Water_Use": "Moderate", "Type": "Oilseed", "Sensitivity": "Moderate"},
    
    # Low Water Use (Drought Resistant)
    "Bajra": {"Water_Use": "Low", "Type": "Millet", "Sensitivity": "Low"},
    "Jowar": {"Water_Use": "Low", "Type": "Millet", "Sensitivity": "Low"},
    "Ragi": {"Water_Use": "Low", "Type": "Millet", "Sensitivity": "Low"},
    "Gram": {"Water_Use": "Low", "Type": "Pulse", "Sensitivity": "Low"},
    "Tur": {"Water_Use": "Low", "Type": "Pulse", "Sensitivity": "Low"},
    "Moong": {"Water_Use": "Low", "Type": "Pulse", "Sensitivity": "Low"},
    "Urad": {"Water_Use": "Low", "Type": "Pulse", "Sensitivity": "Low"},
    "Arhar/Tur": {"Water_Use": "Low", "Type": "Pulse", "Sensitivity": "Low"},
}

# --- API CONFIGURATION ---
API_TIMEOUT = 30
MAX_RETRIES = 3
RECORDS_LIMIT = 5000  # Maximum records per API call

# --- HELPER FUNCTIONS ---
def get_crop_type(crop_name):
    """Returns the category of a crop."""
    for category, crops in CROP_TYPES.items():
        if crop_name in crops or any(crop_name.lower() in c.lower() for c in crops):
            return category
    return "Other"

def get_subdivisions_for_state(state_name):
    """Returns list of IMD subdivisions for a state."""
    return IMD_SUBDIVISION_MAP.get(state_name, [])

def is_drought_resistant(crop_name):
    """Checks if a crop is drought-resistant."""
    return CROP_ATTRIBUTES.get(crop_name, {}).get("Water_Use") == "Low"

def is_water_intensive(crop_name):
    """Checks if a crop is water-intensive."""
    return CROP_ATTRIBUTES.get(crop_name, {}).get("Water_Use") == "High"