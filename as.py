import geopandas as gpd
import pandas as pd

# Désactiver les limites d'affichage
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

gdf = gpd.read_file("Limites_simplifiees.gpkg", layer="LAD_GEN_COMMUNE")
print(gdf)
