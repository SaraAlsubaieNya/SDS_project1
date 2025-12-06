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

st.sidebar.header("Filters")

# Convert CRS if needed
#restaurants = restaurants.to_crs(districts.crs)

#Spatial Join

joined = gpd.sjoin(restaurants, districts, how="left", predicate="within")

#Restaurant Count per District

count_df = (
    joined.groupby("ADM1_EN")
    .size()
    .reset_index(name="restaurant_count")
    .sort_values("restaurant_count", ascending=False)
)

st.subheader("Restaurants per District")
st.dataframe(count_df)


#Map Visualization
st.subheader("Map of Restaurants in Riyadh")

fig, ax = plt.subplots(figsize=(10, 10))
districts.plot(ax=ax, color="white", edgecolor="black")
restaurants.plot(ax=ax, color="red", markersize=2)
ax.set_title("Restaurants on Map")
st.pyplot(fig)


#District Filter
district_list = sorted(districts["ADM1_EN"].unique())
selected_district = st.sidebar.selectbox("Select a district", district_list)

st.subheader(f"Restaurants in {selected_district}")

filtered_rest = joined[joined["ADM1_EN"] == selected_district]

st.map(filtered_rest)

st.write(f"Total restaurants in this district: **{len(filtered_rest)}**")
