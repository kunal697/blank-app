import streamlit as st
import requests
import datetime
from PIL import Image
import io
import time

# Set page config
st.set_page_config(
    page_title="Military Weather Monitoring System",
    page_icon="🌤️",
    layout="wide"
)

# Default locations
DEFAULT_LOCATIONS = [
    {"name": "Ladakh", "lat": 34.1526, "lon": 77.5771},
    {"name": "Arunachal Pradesh", "lat": 28.2180, "lon": 94.7278},
    {"name": "Sikkim", "lat": 27.3389, "lon": 88.6065},
    {"name": "Kashmir", "lat": 34.0837, "lon": 74.7973}
]

# Weather code descriptions
WEATHER_CODES = {
    0: 'Clear sky',
    1: 'Mainly clear',
    2: 'Partly cloudy',
    3: 'Overcast',
    45: 'Foggy',
    48: 'Depositing rime fog',
    51: 'Light drizzle',
    53: 'Moderate drizzle',
    55: 'Dense drizzle',
    61: 'Slight rain',
    63: 'Moderate rain',
    65: 'Heavy rain',
    71: 'Slight snow',
    73: 'Moderate snow',
    75: 'Heavy snow',
    77: 'Snow grains',
    80: 'Slight rain showers',
    81: 'Moderate rain showers',
    82: 'Violent rainstorm',
    85: 'Slight snow showers',
    86: 'Heavy snow showers',
    95: 'Thunderstorm',
    96: 'Thunderstorm with slight hail',
    99: 'Thunderstorm with heavy hail',
}

def get_weather_description(code):
    return WEATHER_CODES.get(code, 'Unknown')

def get_alert_status(temp, wind_speed):
    if temp < -10 or temp > 40 or wind_speed > 20:
        return "🔴 Critical", "red"
    if temp < 0 or temp > 35 or wind_speed > 15:
        return "🟡 Warning", "yellow"
    return "🟢 Normal", "green"

def get_alert_message(temp, wind_speed):
    if temp < -10:
        return "Extreme cold conditions - Exercise caution"
    if temp > 40:
        return "Extreme heat conditions - Limit exposure"
    if wind_speed > 20:
        return "High wind speeds - Operations may be affected"
    if temp < 0:
        return "Cold conditions - Take necessary precautions"
    if temp > 35:
        return "Hot conditions - Stay hydrated"
    if wind_speed > 15:
        return "Moderate wind speeds - Monitor conditions"
    return "Normal operating conditions"

def get_weather_image(location, weather_desc):
    try:
        prompt = f"{location} cityscape, {weather_desc}, professional photograph"
        encoded_prompt = requests.utils.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=600&nologo=true"
        return image_url
    except Exception as e:
        st.error(f"Error generating image URL: {str(e)}")
        return "https://via.placeholder.com/800x600?text=Image+Not+Available"  # Fallback image

def fetch_weather_data(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code&timezone=auto"
        response = requests.get(url, timeout=10)  # Add timeout
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {str(e)}")
    except ValueError as e:
        st.error(f"Error parsing weather data: {str(e)}")
    return None

def weather_card(location_name, weather_data):
    if weather_data:
        current = weather_data['current']
        temp = current['temperature_2m']
        humidity = current['relative_humidity_2m']
        wind_speed = current['wind_speed_10m']
        weather_code = current['weather_code']
        weather_desc = get_weather_description(weather_code)
        
        # Create columns for layout
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.image(
                get_weather_image(location_name, weather_desc),
                caption=location_name,
                use_container_width=True
            )
        
        with col2:
            st.markdown(f"### {location_name}")
            st.markdown(f"**Temperature:** {temp}°C")
            st.markdown(f"**Weather:** {weather_desc}")
            st.markdown(f"**Humidity:** {humidity}%")
            st.markdown(f"**Wind Speed:** {wind_speed} km/h")
            
            alert_status, color = get_alert_status(temp, wind_speed)
            st.markdown(f"**Status:** {alert_status}")
            st.markdown(f"_{get_alert_message(temp, wind_speed)}_")

def get_location_suggestions(query):
    """Get location suggestions based on user input"""
    try:
        if len(query) < 2:  # Only search if user has typed at least 2 characters
            return []
            
        response = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=5&language=en&format=json"
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get('results'):
            return []
            
        # Format suggestions with country and admin area
        suggestions = []
        for result in data['results']:
            location_parts = [result['name']]
            if result.get('admin1'):  # State/Province
                location_parts.append(result['admin1'])
            if result.get('country'):  # Country
                location_parts.append(result['country'])
            
            suggestion = {
                'name': ', '.join(location_parts),
                'lat': result['latitude'],
                'lon': result['longitude']
            }
            suggestions.append(suggestion)
            
        return suggestions
    except Exception as e:
        st.error(f"Error fetching suggestions: {str(e)}")
        return []

def main():
    # Header
    st.title("🎖️ Military Weather Monitoring System")
    
    # Search box with suggestions
    st.markdown("""
        <style>
        .search-container { margin-bottom: 1rem; }
        .suggestion-item {
            padding: 8px 16px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
        }
        .suggestion-item:hover {
            background-color: #f0f2f6;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for search
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ''
    if 'selected_location' not in st.session_state:
        st.session_state.selected_location = None
    
    # Search input
    search_col, button_col = st.columns([4, 1])
    with search_col:
        search_query = st.text_input(
            "Search Location",
            value=st.session_state.search_query,
            placeholder="Start typing a location name...",
            key="location_search"
        )
    with button_col:
        search_button = st.button('🔍 Search')
    
    # Show suggestions while typing
    if search_query and len(search_query) >= 2:
        suggestions = get_location_suggestions(search_query)
        if suggestions:
            st.markdown("### Suggestions:")
            for suggestion in suggestions:
                if st.button(
                    suggestion['name'],
                    key=f"suggestion_{suggestion['name']}",
                    help=f"Click to view weather for {suggestion['name']}"
                ):
                    st.session_state.selected_location = suggestion
                    st.session_state.search_query = suggestion['name']
                    
    # Handle search
    if search_button or st.session_state.selected_location:
        try:
            with st.spinner('Fetching weather data...'):
                if st.session_state.selected_location:
                    # Use the selected location's coordinates
                    location = st.session_state.selected_location
                    weather_data = fetch_weather_data(location['lat'], location['lon'])
                    
                    if weather_data:
                        st.success(f"Found weather data for {location['name']}")
                        st.subheader(f"Weather in {location['name']}")
                        weather_card(location['name'], weather_data)
                    else:
                        st.error("Unable to fetch weather data for this location")
                    
                    # Reset selected location after displaying
                    st.session_state.selected_location = None
                else:
                    # Original search functionality
                    geo_response = requests.get(
                        f"https://geocoding-api.open-meteo.com/v1/search?name={search_query}&count=1&language=en&format=json"
                    )
                    
                    if not geo_response.ok:
                        st.error(f"Error accessing geocoding service: {geo_response.status_code}")
                        return
                    
                    geo_data = geo_response.json()
                    
                    if not geo_data.get('results'):
                        st.warning(f"No results found for '{search_query}'. Please try a different location.")
                        return
                    
                    location = geo_data['results'][0]
                    weather_data = fetch_weather_data(location['latitude'], location['longitude'])
                    
                    if weather_data:
                        st.success(f"Found weather data for {location['name']}")
                        st.subheader(f"Weather in {location['name']}")
                        weather_card(location['name'], weather_data)
                    else:
                        st.error("Unable to fetch weather data for this location")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Network error: {str(e)}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    
    # Strategic Locations
    st.markdown("---")  # Add a divider
    st.subheader("Strategic Locations")
    
    # Create two columns for the strategic locations
    col1, col2 = st.columns(2)
    
    # Display weather cards for default locations
    for idx, location in enumerate(DEFAULT_LOCATIONS):
        with col1 if idx % 2 == 0 else col2:
            weather_data = fetch_weather_data(location['lat'], location['lon'])
            if weather_data:
                with st.expander(f"📍 {location['name']}", expanded=True):
                    weather_card(location['name'], weather_data)
    
    # Add a refresh button instead of automatic refresh
    if st.button('🔄 Refresh Data'):
        st.experimental_rerun()

if __name__ == "__main__":
    main() 
