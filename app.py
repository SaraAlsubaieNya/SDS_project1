import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Riyadh Spatial Analysis", layout="wide")
st.title("Riyadh Spatial Data Science Dashboard")

#loading data
@st.cache_data
def load_data():
    districts = gpd.read_file("data/districts_sample_200.geojson")
    restaurants = gpd.read_file("data/Riyadh_Restaurants_filtered.geojson")
    return districts, restaurants

districts, restaurants = load_data()

# Converts restaurants CRS to districts CRS
#restaurants = restaurants.to_crs(districts.crs)


# spatial join
joined = gpd.sjoin(restaurants, districts, how="left", predicate="within")

# show joined columns (helpful for debugging column/key errors on deploy)
with st.expander("Debug: Joined columns (click to expand)"):
    # show only first 200 chars to keep UI tidy if column list is long
    cols = list(joined.columns)
    st.write(cols)

# Determine grouping column with sensible fallbacks to avoid KeyError
candidate_cols = ["NEIGHBORHENAME", "NEIGHBORHANAME", "ADM1_EN", "NAME_1"]
group_col = next((c for c in candidate_cols if c in joined.columns), None)

if group_col is None:
    st.error(
        "No suitable district/name column found in joined data. Checked: "
        + ", ".join(candidate_cols)
    )
    count_df = joined.head(0)  # empty fallback
else:
    # restaurant Count per District
    count_df = (
        joined.groupby(group_col)
        .size()
        .reset_index(name="restaurant_count")
        .sort_values("restaurant_count", ascending=False)
    )

st.subheader("🍽️ Restaurants per District")
st.dataframe(count_df)


#map Visualization
st.subheader("🗺️ Map of Restaurants in Riyadh")

fig, ax = plt.subplots(figsize=(10, 10))
districts.plot(ax=ax, color="white", edgecolor="black")
restaurants.plot(ax=ax, color="red", markersize=3)
ax.set_title("Restaurants on Map")
st.pyplot(fig)


#district Filter
district_list = sorted(districts["NEIGHBORHENAME"].unique())
selected_district = st.sidebar.selectbox("Select a district", district_list)

st.subheader(f"Restaurants in {selected_district}")

filtered_rest = joined[joined["NEIGHBORHENAME"] == selected_district]

# to Use Streamlit native map
if not filtered_rest.empty:
    # Prepare DataFrame for st.map: Streamlit requires specific lon/lat column names
    df_map = filtered_rest.copy()

    # Common name mappings -> Streamlit accepts longitude names like 'lon'/'longitude'
    if "lng" in df_map.columns and "longitude" not in df_map.columns:
        df_map = df_map.rename(columns={"lng": "longitude"})
    if "lon" in df_map.columns and "longitude" not in df_map.columns:
        df_map = df_map.rename(columns={"lon": "longitude"})
    if "lat" in df_map.columns and "latitude" not in df_map.columns:
        df_map = df_map.rename(columns={"lat": "latitude"})

    # Coerce to numeric and drop rows without valid coordinates
    df_map["longitude"] = pd.to_numeric(df_map.get("longitude"), errors="coerce")
    df_map["latitude"] = pd.to_numeric(df_map.get("latitude"), errors="coerce")
    df_map = df_map.dropna(subset=["latitude", "longitude"])

    if df_map.empty:
        st.write("No restaurants with valid latitude/longitude to plot.")
    else:
        st.map(df_map[["latitude", "longitude"]])
else:
    st.write("No restaurants found in this district.")

st.write(f"Total restaurants in this district: **{len(filtered_rest)}**")
