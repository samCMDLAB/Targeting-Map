import pandas as pd
import folium
from folium.features import GeoJson, GeoJsonTooltip
import json

# Load the client data
df1 = pd.read_csv(r"data\Full Intake(Full Intake Aggregate).csv", encoding="latin1")
df2 = pd.read_csv(r"data\Same Day(Same Day aggregate).csv", encoding="latin1")
geojson_zip_path = r"data\maryland-zips.geojson"
geojson_county_path = r"data\maryland-counties.geojson"

# Combine the two DataFrames into one
df_combined = pd.concat([df1, df2])

# Group data by Zip Code and County of Residence
zip_summary = df_combined.groupby(["Zip Code", "County of Residence"]).size().reset_index(name="Count")

# Calculate statewide total and percentage
total_clients = zip_summary["Count"].sum()
zip_summary["Statewide Percentage"] = (zip_summary["Count"] / total_clients) * 100

# Calculate county-level totals
county_totals = zip_summary.groupby("County of Residence")["Count"].sum().reset_index(name="County Total")
zip_summary = zip_summary.merge(county_totals, on="County of Residence")
zip_summary["County Percentage"] = (zip_summary["Count"] / zip_summary["County Total"]) * 100

# Load the ZIP code GeoJSON file
with open(geojson_zip_path, "r") as f:
    geojson_zip_data = json.load(f)

# Add the client data to ZIP code GeoJSON features
for feature in geojson_zip_data["features"]:
    zip_code = feature["properties"].get("name")  # Adjust if field is not "name"
    if zip_code and int(zip_code) in zip_summary["Zip Code"].values:
        match = zip_summary[zip_summary["Zip Code"] == int(zip_code)]
        feature["properties"]["Clients"] = int(match["Count"].values[0])
        feature["properties"]["Statewide Percentage"] = float(match["Statewide Percentage"].values[0])
        feature["properties"]["County Percentage"] = float(match["County Percentage"].values[0])
    else:
        feature["properties"]["Clients"] = 0
        feature["properties"]["Statewide Percentage"] = 0.0
        feature["properties"]["County Percentage"] = 0.0

# Load the county GeoJSON file
with open(geojson_county_path, "r") as f:
    geojson_county_data = json.load(f)

# Create a folium map
m = folium.Map(location=[39.0, -77.5], zoom_start=8)

# Add county outlines with a dashed border
GeoJson(
    geojson_county_data,
    style_function=lambda feature: {
        "color": "black",       # Black color for the county outlines
        "weight": 2,           # Slightly thicker line for visibility
        "fillOpacity": 0,      # No fill for counties
        "dashArray": "5, 5",   # Dashed lines (5 pixels dash, 5 pixels space)
    },
).add_to(m)

# Define a color scale for ZIP code client counts
def get_color(count):
    if count == 0:
        return "#f2f2f2"  # Gray for no data
    elif count < 10:
        return "#ffcccc"  # Light red
    elif count < 50:
        return "#ff6666"  # Medium red
    else:
        return "#cc0000"  # Dark red

# Add the ZIP code layer with color scaling and tooltips
GeoJson(
    geojson_zip_data,
    style_function=lambda feature: {
        "fillColor": get_color(feature["properties"]["Clients"]),
        "color": "black",
        "weight": 0.5,         # Thin border for ZIP codes
        "fillOpacity": 0.6,
    },
    tooltip=GeoJsonTooltip(
        fields=["name", "Clients", "Statewide Percentage", "County Percentage"],
        aliases=["ZIP Code:", "Clients:", "Share of Statewide Count:", "Share of County Count:"],
        localize=True,
    ),
).add_to(m)

# Save the map to an HTML file
m.save("index.html")
print("Map has been created and saved as 'clients_by_zip_code_with_counties.html'.")
