import folium
import pandas as pd
import webbrowser
import numpy as np
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time
import random

# Read the data from the CSV file
df = pd.read_csv('locations.csv')

# Initialize geocoder with longer timeout
geolocator = Nominatim(user_agent="my_map_app", timeout=10)

# Function to get coordinates for an address with retries
def get_coordinates(address, max_retries=3):
    for attempt in range(max_retries):
        try:
            location = geolocator.geocode(address)
            if location:
                return location.latitude, location.longitude
            return None
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            if attempt == max_retries - 1:  # Last attempt
                return None
            # Exponential backoff with jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Geocoding attempt {attempt + 1} failed, waiting {wait_time:.2f} seconds...")
            time.sleep(wait_time)
    return None

# Process each row and save progress
print("Geocoding addresses...")
for index, row in df.iterrows():
    # Skip if coordinates already exist and are valid
    if pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude')):
        print(f"Skipping row {index} - coordinates already exist: {row['Latitude']}, {row['Longitude']}")
        continue
        
    address = f"{row['Address 1']}, {row['City']}, {row['State']} {row['Zip']}"
    coords = get_coordinates(address)
    
    if coords:
        df.at[index, 'Latitude'] = coords[0]
        df.at[index, 'Longitude'] = coords[1]
        # Save progress after each successful geocoding
        df.to_csv('locations.csv', index=False)
        print(f"Successfully geocoded: {address}")
    else:
        print(f"Failed to geocode: {address}")

# Remove rows where geocoding failed
df = df.dropna(subset=['Latitude', 'Longitude'])

# Define the color map based on quantity range
color_map = {
    (0, 5): '#003f5c',
    (5, 10): '#2f4b7c',
    (10, 17): '#665191',
    (17, 30): '#a05195',
    (30, 43): '#d45087',
    (43, 50): '#f95d6a',
    (50, 80): '#ff7c43',
    (80, 1000): '#ffa600'
}
# Define the boundary coordinates (2024)
boundary_coordinates = np.array([
    [44.98263383567378, -93.86964228719432],
    [44.94144076009766, -93.5193844037396],
    [44.90427410644277, -93.36382027566569],
    [44.714011061743264, -93.52511069066254],
    [44.72350521483905, -93.61959442489149],
    [44.781114844825744, -93.78756550796514],
    [44.87925755643328, -93.93263144334693]
])
# Define the boundary coordinates (2023)
boundary_coordinates_2023 = np.array([
    [44.977808186439034, -93.880324895305181],
    [44.97426774667989, -93.81418943938966],
    [44.935055413789065, -93.61328064898696],
    [44.867952910205446, -93.41308683533549],
    [44.788087678864514, -93.46921260053563],
    [44.75255650009777, -93.57788924164835],
    [44.75636445751769, -93.79988988015386]
])


# Create the map object
m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=12, tiles="cartodb positron")

# 2023 boundary
#polygon = folium.Polygon(locations=boundary_coordinates_2023, color='#ffe2e6', fill=False)
#polygon.add_to(m)

# Create the marker cluster object
marker_cluster = MarkerCluster()

# Add markers to the map
for index, row in df.iterrows():
    try:
        qty = int(row['Qty'])
        color = 'red'
        for qty_range, c in color_map.items():
            if qty in range(qty_range[0], qty_range[1]):
                color = c
                break
        html_text = f'<div style="font-weight:bold; font-size:12pt; color:{color};text-align:center;line-height: .8em;">{row["Qty"]}<br/><span style="font-weight:normal; font-size:10pt">{row["Order ID"]}</span></div>'
        folium.map.Marker(
            [row['Latitude'], row['Longitude']],
            icon=folium.features.DivIcon(
                icon_size=(150, 36),
                icon_anchor=(0, 0),
                html=html_text
            ),
            popup=f"ORDER:{row['Order ID']} Address:{row['Address 1']}, {row['City']}, {row['State']}, {row['Zip']}<br>Quantity: {row['Qty']}",
            color=color
        ).add_to(marker_cluster)
    except (ValueError, TypeError):
        print(f"Skipping row with invalid quantity: {row['Order ID']}")

# Add the marker cluster to the map
marker_cluster.add_to(m)

polygon = folium.Polygon(locations=boundary_coordinates, color='red', fill=False)
polygon.add_to(m)



# Save the map as an HTML file
m.save('map-cluster.html')
