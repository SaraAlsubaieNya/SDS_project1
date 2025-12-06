import geopandas as gpd

districts = gpd.read_file("data/districts_sample_200.geojson")
print(districts.columns)

restaurants = gpd.read_file("data/Riyadh_Restaurants_filtered.geojson")
print(restaurants.columns)
