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



# Sidebar filters
district_list = sorted(districts["NEIGHBORHENAME"].unique())
selected_district = st.sidebar.selectbox("Select a district", district_list)

# Category filter
category_list = sorted(set([c for c in joined["categories"].dropna().unique() if c]))
selected_category = st.sidebar.selectbox("Select a category", ["All"] + category_list)

# Price filter
price_list = sorted(set([p for p in joined["price"].dropna().unique() if p]))
selected_price = st.sidebar.selectbox("Select a price", ["All"] + price_list)

# Rating filter (convert to float, ignore blanks)
joined["rating_num"] = pd.to_numeric(joined["rating"], errors="coerce")
min_rating = float(joined["rating_num"].min()) if not joined["rating_num"].isnull().all() else 0.0
max_rating = float(joined["rating_num"].max()) if not joined["rating_num"].isnull().all() else 10.0
selected_rating = st.sidebar.slider("Minimum rating", min_value=min_rating, max_value=max_rating, value=min_rating, step=0.1)

st.subheader(f"Restaurants in {selected_district}")

# Apply all filters
filtered_rest = joined[joined["NEIGHBORHENAME"] == selected_district]
if selected_category != "All":
    filtered_rest = filtered_rest[filtered_rest["categories"] == selected_category]
if selected_price != "All":
    filtered_rest = filtered_rest[filtered_rest["price"] == selected_price]
filtered_rest = filtered_rest[filtered_rest["rating_num"] >= selected_rating]

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
    st.write("No restaurants found with the selected filters.")

st.write(f"Total restaurants with selected filters: **{len(filtered_rest)}**")
