# Mulch Troop 589
## Location Map Visualization

This project generates an interactive map to visualize location data with color-coded markers based on quantity ranges. The script uses the Folium library to create the map and pandas to handle data from a CSV file. The resulting map is saved as an HTML file.

It was originally created to support the distribution and routes for mulch delivery for Troop 589. 

## Prerequisites

Ensure you have the following packages installed:

- `folium`
- `pandas`
- `numpy`
- `webbrowser`

You can install the necessary packages using pip:

```bash
pip install folium pandas numpy
```

## Data

The script expects a CSV file named `locations.csv` with the following columns:

- `Latitude`
- `Longitude`
- `Qty`
- `Order ID`
- `Address 1`
- `City`
- `State`
- `Zip`

## Script Overview

1. **Read the Data:** The script reads location data from the CSV file into a pandas DataFrame.
2. **Define Color Map:** It defines a color map to color-code markers based on the quantity (`Qty`) range.
3. **Define Boundary Coordinates:** Two sets of boundary coordinates are defined for potential use in the map.
4. **Create Map Object:** The Folium map object is created with the initial view centered on the mean latitude and longitude from the data.
5. **Add Markers:** A marker cluster is created and populated with markers for each location in the data, with custom HTML for each marker showing the quantity and order ID.
6. **Add Boundaries:** Boundary polygons are added to the map for visual reference.
7. **Save Map:** The map is saved as `map-cluster.html`.

## Usage

1. Place the `locations.csv` file in the same directory as the script.
2. Run the script:

```bash
python createmapcluster.py
```

3. The script will generate an `map-cluster.html` file in the same directory. Open this file in a web browser to view the map.

## Example

An example of a row in the CSV file:

```csv
Latitude,Longitude,Qty,Order ID,Address 1,City,State,Zip
44.9780,-93.2650,12,12345,123 Main St,Minneapolis,MN,55401
```

The example `locations.csv` contains an example of what we download from Troop Webhost. 

## Notes

- The color map is defined with specific ranges. Adjust the `color_map` dictionary if your data has different ranges.
- The boundary coordinates are optional and can be customized or removed as needed.
- Customize the HTML for the markers in the `html_text` variable as needed.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
```

Adjust any sections as necessary to better fit your specific requirements or any additional details you want to include.