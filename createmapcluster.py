import folium
import pandas as pd
import webbrowser
import numpy as np
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time
import random
import argparse
import sys
from shapely.geometry import Point, Polygon
from typing import Tuple, Optional, Dict, List

# Constants
# Update these based on this year's delivery area
BOUNDARY_COORDINATES = np.array([
    [44.98263383567378, -93.86964228719432],
    [44.94144076009766, -93.5193844037396],
    [44.90427410644277, -93.36382027566569],
    [44.714011061743264, -93.52511069066254],
    [44.72350521483905, -93.61959442489149],
    [44.781114844825744, -93.78756550796514],
    [44.87925755643328, -93.93263144334693]
])

COLOR_MAP = {
    (0, 5): '#003f5c',
    (5, 10): '#2f4b7c',
    (10, 17): '#665191',
    (17, 30): '#a05195',
    (30, 43): '#d45087',
    (43, 50): '#f95d6a',
    (50, 80): '#ff7c43',
    (80, 1000): '#ffa600'
}

def parse_arguments() -> str:
    """Parse command line arguments and return the CSV file path."""
    parser = argparse.ArgumentParser(description='Create a map from a CSV file of locations.')
    parser.add_argument('csv_file', help='Path to the CSV file containing location data')
    args = parser.parse_args()
    return args.csv_file

def read_csv_file(csv_path: str) -> pd.DataFrame:
    """Read and validate the CSV file."""
    try:
        return pd.read_csv(csv_path, dtype={'Zip': str})
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_path}' not found.")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        print(f"Error: CSV file '{csv_path}' is empty.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

def is_donation(row: pd.Series) -> bool:
    """Check if the row contains a donation item."""
    return pd.notna(row.get('Item')) and 'DONATION' in str(row['Item']).upper()

def is_within_boundary(lat: float, lon: float, boundary_polygon: Polygon) -> bool:
    """Check if coordinates are within the boundary polygon."""
    point = Point(lat, lon)
    return boundary_polygon.contains(point)

def get_coordinates(address: str, geolocator: Nominatim, max_retries: int = 3) -> Optional[Tuple[float, float]]:
    """Get coordinates for an address using Nominatim geocoding service."""
    for attempt in range(max_retries):
        try:
            location = geolocator.geocode(address)
            if location:
                return location.latitude, location.longitude
            return None
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            if attempt == max_retries - 1:
                print(f"Failed to geocode address after {max_retries} attempts: {address}")
                return None
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Geocoding attempt {attempt + 1} failed, waiting {wait_time:.2f} seconds...")
            time.sleep(wait_time)
    return None

def get_color_for_quantity(qty: int) -> str:
    """Get the color for a given quantity based on the color map."""
    for qty_range, color in COLOR_MAP.items():
        if qty in range(qty_range[0], qty_range[1]):
            return color
    return 'red'

def process_coordinates(df: pd.DataFrame, geolocator: Nominatim, csv_path: str) -> pd.DataFrame:
    """Process coordinates for all rows in the dataframe."""
    print("Geocoding addresses...")
    for index, row in df.iterrows():
        if is_donation(row):
            print(f"Skipping row {index} - contains 'DONATION' in Item: {row['Item']}")
            continue
            
        if pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude')):
            print(f"Skipping row {index} - coordinates already exist: {row['Latitude']}, {row['Longitude']}")
            continue
            
        address = f"{row['Address Line 1']}, {row['City']}, {row['State']} {row['Zip']}"
        coords = get_coordinates(address, geolocator)
        
        if coords:
            df.at[index, 'Latitude'] = coords[0]
            df.at[index, 'Longitude'] = coords[1]
            df.to_csv(csv_path, index=False)
            print(f"Successfully geocoded: {address}")
        else:
            print(f"Failed to geocode: {address}")
    
    return df.dropna(subset=['Latitude', 'Longitude'])

def check_boundaries(df: pd.DataFrame, boundary_polygon: Polygon) -> None:
    """Check all coordinates against the boundary and print warnings."""
    print("\nChecking coordinates against boundary...")
    for index, row in df.iterrows():
        if is_donation(row):
            continue
        if not is_within_boundary(row['Latitude'], row['Longitude'], boundary_polygon):
            print(f"Warning: Coordinates ({row['Latitude']}, {row['Longitude']}) for address '{row['Address Line 1']}, {row['City']}, {row['State']} {row['Zip']}' are outside the boundary.")

def create_map_markers(df: pd.DataFrame, marker_cluster: MarkerCluster) -> None:
    """Create map markers for all rows in the dataframe."""
    for index, row in df.iterrows():
        if is_donation(row):
            continue
        try:
            qty = int(row['Order Qty'])
            color = get_color_for_quantity(qty)
            html_text = f'<div style="font-weight:bold; font-size:12pt; color:{color};text-align:center;line-height: .8em;">{row["Order Qty"]}<br/><span style="font-weight:normal; font-size:10pt">{row["Order ID"]}</span></div>'
            folium.map.Marker(
                [row['Latitude'], row['Longitude']],
                icon=folium.features.DivIcon(
                    icon_size=(150, 36),
                    icon_anchor=(0, 0),
                    html=html_text
                ),
                popup=f"ORDER:{row['Order ID']} Address:{row['Address Line 1']}, {row['City']}, {row['State']}, {row['Zip']}<br>Quantity: {row['Order Qty']}",
                color=color
            ).add_to(marker_cluster)
        except (ValueError, TypeError):
            print(f"Skipping row with invalid quantity: {row['Order ID']}")

def main():
    """Main function to orchestrate the map creation process."""
    # Setup
    csv_path = parse_arguments()
    df = read_csv_file(csv_path)
    boundary_polygon = Polygon(BOUNDARY_COORDINATES)
    geolocator = Nominatim(user_agent="my_map_app", timeout=10)
    
    # Process coordinates
    df = process_coordinates(df, geolocator, csv_path)
    check_boundaries(df, boundary_polygon)
    
    # Create map
    m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], 
                  zoom_start=12, 
                  tiles="cartodb positron")
    marker_cluster = MarkerCluster()
    create_map_markers(df, marker_cluster)
    marker_cluster.add_to(m)
    
    # Add boundary polygon
    polygon = folium.Polygon(locations=BOUNDARY_COORDINATES, color='red', fill=False)
    polygon.add_to(m)
    
    # Save map
    m.save('map-cluster.html')

if __name__ == "__main__":
    main()
