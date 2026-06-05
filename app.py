import streamlit as st
import pandas as pd
import engine
import plotly.express as px
import geopandas as gpd
import pydeck as pdk
import folium
from streamlit_folium import st_folium
import time
import base64
import os


#git add .
#git commit -m "Correction image de fond"
#git push



def ajouter_fond(image_file):
    # 1. Gestion sécurisée du chemin (local vs cloud)
    dossier_actuel = os.path.dirname(os.path.abspath(__file__))
    chemin_complet = os.path.join(dossier_actuel, image_file)
    
    # 2. Encodage Base64
    with open(chemin_complet, "rb") as image:
        encoded_string = base64.b64encode(image.read()).decode()
    
    # 3. Injection CSS propre
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{encoded_string}");
        background-size: cover; /* Ajuste tout l'écran. Utilise '100% 100%' si tu veux forcer sans coupure */
        background-repeat: no-repeat;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Activation de l'image de fond
ajouter_fond("imagea.jpg")
st.title("🏡 HabitatScore 2026")

def get_final_data(chemin_gpkg, df_merge):
    # Assure-toi que 'engine' est bien importé au début
    gdf = engine.charger_geodata(chemin_gpkg)
    return engine.fusionner_geo(gdf, df_merge)



# 1. Chargement et préparation (Sécurisé dans une fonction cache)
@st.cache_data
def charger_donnees():
    # Chargement
    df_prix = pd.read_csv("prix_immobilier.csv", sep=";")
    df_tp = pd.read_csv("tp.csv", sep=";", encoding="utf-8-sig")
    df_commerces = pd.read_csv("commerces.csv", sep=";")
    df_air = pd.read_csv("qualité_air.csv", sep=";")
    df_sport = pd.read_csv("places_sport.csv", sep=";")
    df_fisc = pd.read_csv("fisc.csv", sep=";")
    df_log = pd.read_csv("logements_vacants.csv", sep=";")
    df_pop = pd.read_csv("pop_commune.csv", sep=";", encoding="utf-8-sig", thousands=' ')
    

    
    df_tp = engine.ponderer_transports(df_tp)
  
   

    # Nettoyage
    liste_dfs = [df_prix, df_tp, df_commerces, df_air, df_sport, df_fisc, df_log]
    for df in liste_dfs:
        if "Commune" in df.columns:
            df["Commune"] = df["Commune"].astype(str).str.strip().str.lower()
    
    # Préparation
    df_prix["Moyenne_appart"] = (df_prix["Appart. Prix bas"] + df_prix["Appart. Prix haut"]) / 2
    df_prix["Moyenne_maison"] = (df_prix["Maison prix bas"] + df_prix["Maison prix haut"]) / 2

    df_tp["Commune"] = df_tp["Commune"].str.replace(r'\s*\(.*?\)', '', regex=True).str.strip()
    
    df_log["Total logements vacants"] = df_log["Total logements vacants"].fillna("0").str.replace("-","0").astype(int)
    

    #Merge 1
    df_merge = df_prix.copy()
    
    #Merge2 (poids, df_tp )
    df_score_tp_clean = df_tp[["Poids", "Commune", "Numero Commune"]]
    df_merge = engine.fusionner(df_merge, df_score_tp_clean, "Commune", "Commune")
    
    #Merge 3 (nb établissements commerciaux, df_commerces)
    df_merge = engine.fusionner(df_merge, df_commerces, "Commune", "Commune")
   
    #Merge 4 (Indice (IQA), df_air)
    df_qualité_air_clean = df_air[["Commune", "Indice (IQA)"]]
    df_merge = engine.fusionner(df_merge, df_qualité_air_clean, "Commune", "Commune")
   
    #Merge 5 (Total places, df_sport)
    df_places_sport_clean = df_sport[["Commune", "Total places"]]
    df_merge = engine.fusionner(df_merge, df_places_sport_clean, "Commune", "Commune")
    
    #Merge 6 (Impôt rentrée argent, df_fisc)
    df_fisc_clean = df_fisc[["Commune","Impôt rentrée argent"]]
    df_merge = engine.fusionner(df_merge, df_fisc_clean, "Commune", "Commune")
    
    #Merge 7 (Total logements vacants, df_log)
    df_logements_vacants_clean = df_log[["Commune", "Total logements vacants"]]
    df_merge = engine.fusionner(df_merge, df_logements_vacants_clean, "Commune", "Commune")



    #Merge 8
    df_pop = df_pop[["a", "Commune", "Total"]]
    df_merge = engine.fusionner(df_merge, df_pop, "Numero Commune", "a")

    df_merge = df_merge.rename(columns={'Commune_x': 'Commune'})

   
    
    return df_merge

df_merge = charger_donnees().copy()



# 2. Interface (Sliders)
st.sidebar.header("Pondération")
a = st.sidebar.slider("Prix abordables maisons", 1, 5, 3)
b = st.sidebar.slider("Prix abordables appartements", 1, 5, 3)
c = st.sidebar.slider("Desserte transports publiques", 1, 5, 3)
d = st.sidebar.slider("Offre commerces", 1, 5, 3)
e = st.sidebar.slider("Qualité de l'air", 1, 5, 3)
f = st.sidebar.slider("Offre de place de divertissements", 1, 5, 3)
g = st.sidebar.slider("Coefficient fiscaux communaux", 1, 5, 3)
h = st.sidebar.slider("Disponibilité logements", 1, 5, 3)

# 3. Pipeline de transformation


#Prix maisons
df_merge = engine.fonction_z_score(df_merge, "Moyenne_appart")
df_merge = engine.changement_polarité(df_merge, "Moyenne_appart")
df_merge = engine.fonction_norm(df_merge, "Moyenne_appart")
df_merge = engine.fonction_mulitplication_notes(df_merge, "Moyenne_appart", a, 0.5)


#Prix appartements
df_merge = engine.fonction_z_score(df_merge, "Moyenne_maison")
df_merge = engine.changement_polarité(df_merge, "Moyenne_maison")
df_merge = engine.fonction_norm(df_merge, "Moyenne_maison")
df_merge = engine.fonction_mulitplication_notes(df_merge, "Moyenne_maison", b, 0.7)


#Desserte transports publiques
df_merge = engine.fonction_z_score(df_merge, "Poids")
df_merge = engine.fonction_norm(df_merge, "Poids")
df_merge = engine.fonction_mulitplication_notes(df_merge, "Poids", c)

#Offre commerces
df_merge = engine.log_per_capita(df_merge, "nb établissements commerciaux", "Total")
df_merge = engine.fonction_z_score(df_merge, "nb établissements commerciaux")
df_merge = engine.fonction_norm(df_merge, "nb établissements commerciaux")
df_merge = engine.fonction_mulitplication_notes(df_merge, "nb établissements commerciaux", d)

#Qualité de l'air
df_merge = engine.fonction_z_score(df_merge, "Indice (IQA)")
df_merge = engine.changement_polarité(df_merge, "Indice (IQA)")
df_merge = engine.fonction_norm(df_merge, "Indice (IQA)")
df_merge = engine.fonction_mulitplication_notes(df_merge, "Indice (IQA)", e)

#Offre de place de divertissements
df_merge = engine.fonction_z_score(df_merge, "Total places")
df_merge = engine.fonction_norm(df_merge, "Total places")
df_merge = engine.fonction_mulitplication_notes(df_merge, "Total places", f, 1.5)

#Coefficient fiscaux communaux
df_merge = engine.fonction_z_score(df_merge, "Impôt rentrée argent")
df_merge = engine.changement_polarité(df_merge, "Impôt rentrée argent")
df_merge = engine.fonction_norm(df_merge, "Impôt rentrée argent")
df_merge = engine.fonction_mulitplication_notes(df_merge, "Impôt rentrée argent", g, 1.2)

#Disponibilité logements
df_merge = engine.log_per_capita(df_merge, "Total logements vacants", "Total")
df_merge = engine.fonction_z_score(df_merge, "Total logements vacants")
df_merge = engine.fonction_norm(df_merge, "Total logements vacants")
df_merge = engine.fonction_mulitplication_notes(df_merge, "Total logements vacants", h)

# 4. Calcul Score Final
cols_transitoires = [col for col in df_merge.columns if "_transitoire" in col]
df_merge["Score_final"] = df_merge[cols_transitoires].sum(axis=1)

liste_en_têtes = list(df_merge.columns)

liste_justification = ["Accessibilité achat appartement",
                           "Accessibilité achat maison",
                           "Offre transports publiques",
                           "Offre commerces et services",
                           "Qualité de l'air",
                           "Offre place de sports et loisirs",
                           "Charge fiscale modérée",
                           "Nomre de logements à louer"]

dictionnaire_justification = dict(zip(liste_en_têtes, liste_justification))


df_merge["Justification"] = df_merge[liste_en_têtes].idxmax(axis = 1)




# Tri et sélection des colonnes
df_classement = df_merge[['Commune', 'Score_final']].sort_values(by='Score_final', ascending=False).reset_index(drop=True)
df_classement.insert(0, 'Rang', range(1, len(df_classement) + 1))


# 5. Affichage
st.subheader("Communes (Score final)")
st.dataframe(df_classement, hide_index=True)



#-----------------------------------------------------------------
#***********************CARTE DYNAMIQUE (TOP 10 BLEU + 1 ROUGE)***
#-----------------------------------------------------------------
st.subheader("Visualisation cartographique")

with st.spinner('Dessin de la carte et calcul du dégradé...'):
    try:
        import pandas as pd
        
        # 1. On prend le Top 10 et la pire commune, puis on les assemble
        top_10_tableau = df_merge.nlargest(10, 'Score_final')
        pire_tableau = df_merge.nsmallest(1, 'Score_final')
        df_carte_donnees = pd.concat([top_10_tableau, pire_tableau]).copy()
        
        # 2. Formes géographiques
        import engine
        gdf_formes = engine.charger_geodata("Limites_simplifiees.gpkg")
        
        # 3. Nettoyage des noms pour la fusion
        gdf_formes['NOM_MIN'] = gdf_formes['NOM_MIN'].astype(str).str.strip().str.lower()
        df_carte_donnees['Commune'] = df_carte_donnees['Commune'].astype(str).str.strip().str.lower()
        
        # 4. Fusion
        df_carte = gdf_formes.merge(df_carte_donnees, left_on='NOM_MIN', right_on='Commune', how='inner')
        
        # Tri et indexation : les 10 premiers (index 0-9) et le dernier (index 10)
        df_carte = df_carte.sort_values(by='Score_final', ascending=False).reset_index(drop=True)

        df_carte['Score_final'] = df_carte['Score_final'].round(2)

        # Palette : 10 bleus (foncé à clair) + 1 rouge pour la dernière
        couleurs = [
            '#08306b', # Rank 0 (Meilleur) - Bleu très foncé
            '#08519c', # Rank 1
            '#2171b5', # Rank 2
            '#4292c6', # Rank 3
            '#6baed6', # Rank 4
            '#9ecae1', # Rank 5
            '#c6dbef', # Rank 6
            '#deebf7', # Rank 7
            '#f7fbff', # Rank 8
            '#ffffff', # Rank 9 (10ème) - Blanc/Très clair
            '#e31a1c'  # Rank 10 (La moins bonne) - Rouge
        ]
        
        # 5. Affichage
        if not df_carte.empty:
            df_carte = df_carte.to_crs(epsg=4326)
            m = folium.Map(location=[46.5, 6.6], zoom_start=9)

            def style_gradient(feature):
                rank = int(feature['id']) 
                if rank > 10: rank = 10
                
                return {
                    'fillColor': couleurs[rank],   
                    'color': 'black',      
                    'weight': 1.5,        
                    'fillOpacity': 0.8     
                }

            folium.GeoJson(
                df_carte,
                style_function=style_gradient,
                tooltip=folium.GeoJsonTooltip(
                    fields=['Commune', 'Score_final'],
                    aliases=['Commune :', 'Score :']
                )
            ).add_to(m)
            
            m.fit_bounds(m.get_bounds())
            
            import time
            from streamlit_folium import st_folium 
            st_folium(m, width=700, height=500, returned_objects=[], key=f"carte_{time.time()}")
            
            st.caption("Légende : Bleu = Top 10 (foncé au plus clair) | Rouge = Moins bon score")

        else:
            st.error("Erreur de fusion : les noms de la carte et du tableau ne correspondent pas.")
            
    except Exception as e:
        st.error(f"Erreur lors du dessin de la carte : {e}")

