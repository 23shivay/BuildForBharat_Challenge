import requests
import json
import numpy as np
from typing import Dict, List, Any, Optional
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from config import *

# ==============================================================================
# CRITICAL UTILITY FUNCTION - Used everywhere to prevent float conversion errors
# ==============================================================================

def safe_float_convert(value, default=0.0):
    """
    Safely convert a value to float, handling 'NA', None, and invalid strings.
    This is CRITICAL for handling government API data which often has missing values.
    """
    if value is None or value == '' or str(value).strip().upper() in ['NA', 'N/A', 'NULL']:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# ==============================================================================
# API UTILITIES
# ==============================================================================

def make_api_call(resource_id: str, api_key: str, filters: Dict[str, Any], 
                  limit: int = RECORDS_LIMIT) -> Dict[str, Any]:
    """
    Makes a robust API call to data.gov.in with error handling and retries.
    """
    url = f"{DATA_GOV_BASE_URL}{resource_id}"
    
    # Convert all filter values to strings and format for API
    string_filters = {k: str(v) for k, v in filters.items()}
    api_filters = {f"filters[{k}]": v for k, v in string_filters.items()}
    
    params = {
        "api-key": api_key,
        "format": "json",
        "limit": limit,
        "offset": 0,
        **api_filters
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=API_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok':
                return {
                    "success": True,
                    "data": data.get('records', []),
                    "total": data.get('total', 0),
                    "url": response.url
                }
            elif data.get('status') == 'error':
                return {
                    "success": False,
                    "error": f"API Error: {data.get('message', 'Unknown error')}",
                    "url": response.url
                }
            else:
                return {
                    "success": False,
                    "error": "No data found for the given filters",
                    "url": response.url
                }
                
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                return {
                    "success": False,
                    "error": f"API Request Failed: {str(e)}",
                    "url": url
                }
            continue
    
    return {"success": False, "error": "Max retries exceeded"}


def fetch_crop_data(state_name: str, years: int, crop_name: Optional[str] = None) -> Dict:
    """Fetches crop production data for a state."""
    end_year = CURRENT_ANALYSIS_YEAR
    start_year = end_year - years + 1
    
    filters = {
        "state_name": state_name,
    }
    
    if crop_name:
        filters["crop"] = crop_name
    
    result = make_api_call(CROP_RESOURCE_ID, CROP_API_KEY, filters)
    
    if result["success"]:
        # Filter by year range and clean data
        filtered_records = []
        for r in result["data"]:
            try:
                year = int(r.get("crop_year", 0))
                if start_year <= year <= end_year:
                    # Clean production and area values
                    r["production_"] = safe_float_convert(r.get("production_"), 0.0)
                    r["area_"] = safe_float_convert(r.get("area_"), 0.0)
                    filtered_records.append(r)
            except:
                continue  # Skip invalid records
        
        result["data"] = filtered_records
        result["total"] = len(filtered_records)
    
    return result


def safe_float_convert(value, default=0.0):
    """Safely convert a value to float, handling 'NA', None, and invalid strings."""
    if value is None or value == '' or value == 'NA' or value == 'N/A':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def fetch_rainfall_data(subdivisions: List[str], years: int) -> Dict:
    """Fetches rainfall data for IMD subdivisions."""
    end_year = CURRENT_ANALYSIS_YEAR
    start_year = end_year - years + 1
    
    all_records = []
    urls = []
    errors = []
    
    for subdivision in subdivisions:
        filters = {"subdivision": subdivision}
        result = make_api_call(RAIN_RESOURCE_ID, RAIN_API_KEY, filters)
        
        if result["success"]:
            urls.append(result["url"])
            # Filter by year range and clean data
            for r in result["data"]:
                try:
                    year = int(r.get("year", 0))
                    if start_year <= year <= end_year:
                        # Clean the annual rainfall value
                        annual = r.get("annual")
                        r["annual"] = safe_float_convert(annual, 0.0)
                        all_records.append(r)
                except:
                    continue  # Skip invalid records
        else:
            errors.append(f"{subdivision}: {result.get('error', 'Unknown error')}")
    
    if not all_records and errors:
        return {
            "success": False,
            "error": f"Failed to fetch data: {'; '.join(errors)}",
            "data": [],
            "total": 0,
            "url": ""
        }
    
    return {
        "success": len(all_records) > 0,
        "data": all_records,
        "total": len(all_records),
        "url": " | ".join(urls) if urls else ""
    }


# ==============================================================================
# DATA ANALYSIS FUNCTIONS
# ==============================================================================

def compare_rainfall_and_crops(state_x: str, state_y: str, years: int, 
                                crop_type: str) -> Dict[str, Any]:
    """
    Q1: Compare rainfall between two states and list top crops by type.
    """
    results = {
        "query_type": "COMPARE_ALL",
        "states": [state_x, state_y],
        "years_analyzed": years,
        "crop_type": crop_type,
    }
    
    # Fetch rainfall data for both states
    rainfall_data = {}
    for state in [state_x, state_y]:
        subdivisions = get_subdivisions_for_state(state)
        if not subdivisions:
            return {"error": f"No IMD subdivision mapping found for {state}. Please update config.py with correct subdivision names."}
        
        rain_result = fetch_rainfall_data(subdivisions, years)
        if not rain_result["success"]:
            return {"error": f"Failed to fetch rainfall data for {state}: {rain_result.get('error', 'Unknown error')}"}
        
        # Calculate average annual rainfall with safe conversion
        annual_rainfalls = []
        for r in rain_result["data"]:
            annual = safe_float_convert(r.get("annual"), 0.0)
            if annual > 0:  # Only include valid non-zero values
                annual_rainfalls.append(annual)
        
        if not annual_rainfalls:
            return {"error": f"No valid rainfall data found for {state} in the specified period"}
        
        avg_rainfall = np.mean(annual_rainfalls)
        
        rainfall_data[state] = {
            "average_annual_rainfall_mm": round(avg_rainfall, 2),
            "data_points": len(annual_rainfalls),
            "subdivisions": subdivisions,
            "source_url": rain_result["url"]
        }
    
    results["rainfall_comparison"] = rainfall_data
    
    # Fetch crop data for both states
    crop_data = {}
    for state in [state_x, state_y]:
        crop_result = fetch_crop_data(state, years)
        if not crop_result["success"]:
            return {"error": f"Failed to fetch crop data for {state}: {crop_result.get('error', 'Unknown error')}"}
        
        # Filter by crop type
        crops_of_type = CROP_TYPES.get(crop_type, [])
        if not crops_of_type:
            return {"error": f"Unknown crop type: {crop_type}. Valid types: {list(CROP_TYPES.keys())}"}
        
        filtered_crops = [
            r for r in crop_result["data"]
            if any(crop.lower() in r.get("crop", "").lower() for crop in crops_of_type)
        ]
        
        # Aggregate production by crop with safe conversion
        crop_production = {}
        for record in filtered_crops:
            crop_name = record.get("crop", "Unknown")
            production = safe_float_convert(record.get("production_", 0), 0.0)
            crop_production[crop_name] = crop_production.get(crop_name, 0) + production
        
        # Get top 3 crops
        top_crops = sorted(crop_production.items(), key=lambda x: x[1], reverse=True)[:3]
        
        crop_data[state] = {
            "top_3_crops": [
                {"crop": crop, "total_production": round(prod, 2)} 
                for crop, prod in top_crops
            ],
            "source_url": crop_result["url"]
        }
    
    results["crop_comparison"] = crop_data
    results["citations"] = {
        f"{state}_rainfall": rainfall_data[state]["source_url"] 
        for state in [state_x, state_y]
    }
    results["citations"].update({
        f"{state}_crops": crop_data[state]["source_url"] 
        for state in [state_x, state_y]
    })
    
    return results


def find_max_min_districts(state_x: str, state_y: str, crop_z: str, years: int) -> Dict[str, Any]:
    """
    Q2: Find districts with max production in state_x and min production in state_y.
    """
    results = {
        "query_type": "MAX_MIN_CROP",
        "crop": crop_z,
        "years_analyzed": years,
    }
    
    # Fetch data for state_x (max district)
    crop_result_x = fetch_crop_data(state_x, years, crop_z)
    if not crop_result_x["success"]:
        return {"error": f"Failed to fetch {crop_z} data for {state_x}: {crop_result_x.get('error', 'Unknown error')}"}
    
    # Find district with max production in state_x
    district_production_x = {}
    for record in crop_result_x["data"]:
        district = record.get("district_name", "Unknown")
        production = safe_float_convert(record.get("production_", 0), 0.0)
        district_production_x[district] = district_production_x.get(district, 0) + production
    
    if not district_production_x:
        return {"error": f"No production data found for {crop_z} in {state_x}"}
    
    max_district_x = max(district_production_x.items(), key=lambda x: x[1])
    
    # Fetch data for state_y (min district)
    crop_result_y = fetch_crop_data(state_y, years, crop_z)
    if not crop_result_y["success"]:
        return {"error": f"Failed to fetch {crop_z} data for {state_y}: {crop_result_y.get('error', 'Unknown error')}"}
    
    # Find district with min production in state_y
    district_production_y = {}
    for record in crop_result_y["data"]:
        district = record.get("district_name", "Unknown")
        production = safe_float_convert(record.get("production_", 0), 0.0)
        if production > 0:  # Exclude zero production
            district_production_y[district] = district_production_y.get(district, 0) + production
    
    if not district_production_y:
        return {"error": f"No production data found for {crop_z} in {state_y}"}
    
    min_district_y = min(district_production_y.items(), key=lambda x: x[1])
    
    results[state_x] = {
        "max_production_district": max_district_x[0],
        "total_production": round(max_district_x[1], 2),
        "source_url": crop_result_x["url"]
    }
    
    results[state_y] = {
        "min_production_district": min_district_y[0],
        "total_production": round(min_district_y[1], 2),
        "source_url": crop_result_y["url"]
    }
    
    results["comparison"] = {
        "production_ratio": round(max_district_x[1] / min_district_y[1], 2) if min_district_y[1] > 0 else "Infinite",
        "difference": round(max_district_x[1] - min_district_y[1], 2)
    }
    
    results["citations"] = {
        state_x: crop_result_x["url"],
        state_y: crop_result_y["url"]
    }
    
    return results


def analyze_correlation_and_policy(state_x: str, state_y: str, years: int) -> Dict[str, Any]:
    """
    Q3/Q4: Analyze production-rainfall correlation and provide policy recommendations.
    """
    results = {
        "query_type": "POLICY_ADVICE",
        "states": [state_x, state_y],
        "years_analyzed": years,
    }
    
    state_analysis = {}
    
    for state in [state_x, state_y]:
        # Fetch rainfall data
        subdivisions = get_subdivisions_for_state(state)
        if not subdivisions:
            continue
            
        rain_result = fetch_rainfall_data(subdivisions, years)
        
        # Fetch crop data
        crop_result = fetch_crop_data(state, years)
        
        if not rain_result["success"] or not crop_result["success"]:
            continue
        
        # Aggregate rainfall by year with safe conversion
        rainfall_by_year = {}
        for record in rain_result["data"]:
            year = int(record.get("year", 0))
            annual = safe_float_convert(record.get("annual"), 0.0)
            if year and annual > 0:  # Only include valid data
                if year not in rainfall_by_year:
                    rainfall_by_year[year] = []
                rainfall_by_year[year].append(annual)
        
        # Average rainfall across subdivisions for each year
        avg_rainfall_by_year = {
            year: np.mean(vals) for year, vals in rainfall_by_year.items()
        }
        
        # Aggregate production by year and water requirement
        high_water_prod = {}
        low_water_prod = {}
        
        for record in crop_result["data"]:
            year = int(record.get("crop_year", 0))
            crop = record.get("crop", "")
            production = safe_float_convert(record.get("production_", 0), 0.0)
            
            water_use = CROP_ATTRIBUTES.get(crop, {}).get("Water_Use", "Unknown")
            
            if water_use == "High":
                high_water_prod[year] = high_water_prod.get(year, 0) + production
            elif water_use == "Low":
                low_water_prod[year] = low_water_prod.get(year, 0) + production
        
        # Calculate correlations
        common_years = sorted(set(avg_rainfall_by_year.keys()) & set(high_water_prod.keys()) & set(low_water_prod.keys()))
        
        if len(common_years) >= 3:
            rainfall_vals = [avg_rainfall_by_year[y] for y in common_years]
            high_water_vals = [high_water_prod[y] for y in common_years]
            low_water_vals = [low_water_prod[y] for y in common_years]
            
            corr_high = np.corrcoef(rainfall_vals, high_water_vals)[0, 1] if len(rainfall_vals) > 1 else 0
            corr_low = np.corrcoef(rainfall_vals, low_water_vals)[0, 1] if len(rainfall_vals) > 1 else 0
            
            state_analysis[state] = {
                "avg_annual_rainfall_mm": round(np.mean(list(avg_rainfall_by_year.values())), 2),
                "high_water_crop_production_avg": round(np.mean(list(high_water_prod.values())), 2),
                "low_water_crop_production_avg": round(np.mean(list(low_water_prod.values())), 2),
                "correlation_rainfall_vs_high_water_crops": round(corr_high, 3),
                "correlation_rainfall_vs_low_water_crops": round(corr_low, 3),
                "years_analyzed": len(common_years),
                "sources": {
                    "rainfall": rain_result["url"],
                    "crops": crop_result["url"]
                }
            }
    
    results["state_analysis"] = state_analysis
    
    # Generate policy recommendations
    recommendations = []
    
    for state, analysis in state_analysis.items():
        high_corr = analysis["correlation_rainfall_vs_high_water_crops"]
        low_corr = analysis["correlation_rainfall_vs_low_water_crops"]
        avg_rainfall = analysis["avg_annual_rainfall_mm"]
        
        if avg_rainfall < 800:  # Low rainfall region
            recommendations.append({
                "state": state,
                "recommendation": "Promote drought-resistant crops (millets, pulses)",
                "rationale": f"Low average rainfall ({avg_rainfall}mm) makes high-water crops risky",
                "supporting_data": f"High-water crops show {abs(high_corr):.2f} correlation sensitivity"
            })
        
        if high_corr > 0.7:
            recommendations.append({
                "state": state,
                "recommendation": "Expand irrigation infrastructure for water-intensive crops",
                "rationale": f"Strong positive correlation ({high_corr:.2f}) shows high-water crops respond well to rainfall",
                "supporting_data": "Historical production aligns with rainfall patterns"
            })
        
        if abs(low_corr) < abs(high_corr):
            recommendations.append({
                "state": state,
                "recommendation": "Drought-resistant crops provide production stability",
                "rationale": f"Lower correlation ({low_corr:.2f}) indicates resilience to rainfall variation",
                "supporting_data": "Consistent production despite climate variability"
            })
    
    results["policy_recommendations"] = recommendations
    results["citations"] = {
        state: analysis["sources"] for state, analysis in state_analysis.items()
    }
    
    return results


# ==============================================================================
# LANGCHAIN TOOL DEFINITION
# ==============================================================================

class AgDataToolInput(BaseModel):
    """Input schema for the agricultural data analysis tool."""
    state_x: str = Field(description="First state name (e.g., 'Maharashtra')")
    state_y: str = Field(description="Second state name (e.g., 'Karnataka')")
    years: int = Field(description="Number of years to analyze (e.g., 5)")
    metric: str = Field(
        description="Analysis type: 'COMPARE_ALL' (Q1), 'MAX_MIN_CROP' (Q2), or 'POLICY_ADVICE' (Q3/Q4)"
    )
    crop_type: Optional[str] = Field(
        default=None,
        description="Crop category for COMPARE_ALL: 'Cereals', 'Pulses', 'Oilseeds', 'Cash Crops'"
    )
    crop_z: Optional[str] = Field(
        default=None,
        description="Specific crop name for MAX_MIN_CROP (e.g., 'Rice', 'Wheat')"
    )


def analyze_agricultural_data_func(
    state_x: str,
    state_y: str,
    years: int,
    metric: str,
    crop_type: Optional[str] = None,
    crop_z: Optional[str] = None
) -> str:
    """
    Analyzes agricultural and climate data from data.gov.in APIs.
    
    Returns JSON string with analysis results and source citations.
    """
    try:
        if metric == "COMPARE_ALL":
            if not crop_type:
                return json.dumps({"error": "crop_type required for COMPARE_ALL metric"})
            result = compare_rainfall_and_crops(state_x, state_y, years, crop_type)
        
        elif metric == "MAX_MIN_CROP":
            if not crop_z:
                return json.dumps({"error": "crop_z required for MAX_MIN_CROP metric"})
            result = find_max_min_districts(state_x, state_y, crop_z, years)
        
        elif metric == "POLICY_ADVICE":
            result = analyze_correlation_and_policy(state_x, state_y, years)
        
        else:
            return json.dumps({"error": f"Unknown metric: {metric}"})
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({"error": f"Analysis failed: {str(e)}"})


# Create the LangChain tool
analyze_agricultural_data = StructuredTool.from_function(
    func=analyze_agricultural_data_func,
    name="analyze_agricultural_data",
    description="""
    Analyzes Indian agricultural production and climate data from data.gov.in.
    
    Capabilities:
    - Compare rainfall between states and rank top crops (metric='COMPARE_ALL')
    - Find districts with max/min crop production (metric='MAX_MIN_CROP')
    - Analyze production-rainfall correlations and policy recommendations (metric='POLICY_ADVICE')
    
    All data is sourced directly from live government APIs with full citations.
    """,
    args_schema=AgDataToolInput,
    return_direct=False
)

tools = [analyze_agricultural_data]