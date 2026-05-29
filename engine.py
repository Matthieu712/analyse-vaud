import pandas as pd
import numpy as np
import geopandas as gpd
import os

def charger_geodata(chemin_gpkg):
    if not os.path.exists(chemin_gpkg):
        raise FileNotFoundError(f"Le fichier {chemin_gpkg} est introuvable.")
    
    # AJOUT DU LAYER ICI (Remplace par le bon nom si différent)
    gdf = gpd.read_file(chemin_gpkg, layer="LAD_GEN_COMMUNE") 
    
    # Validation des colonnes 
    if 'NOM_MIN' not in gdf.columns:
        raise ValueError(f"Colonne 'NOM_MIN' manquante. Colonnes trouvées : {list(gdf.columns)}")
        
    return gdf


def fusionner_geo(gdf, df_merge):
    # 1. Nettoyage basique
    gdf['NOM_MIN'] = gdf['NOM_MIN'].fillna(0).astype(str).str.strip().str.lower()
    df_merge['Commune'] = df_merge['Commune'].fillna(0).astype(str).str.strip().str.lower()
    
    # 2. Fusion
    df_final = gdf.merge(df_merge, left_on='NOM_MIN', right_on='Commune', how='left')
    
    # 3. Calcul
    colonnes_a_sommer = [col for col in df_final.columns if col.endswith('_transitoire')]
    df_final["Score_final"] = df_final[colonnes_a_sommer].sum(axis=1, numeric_only=True)
    
    return df_final

def nettoyer_chaine(chaine):
    return str(chaine).lower().strip().replace(" ", "")


def fusionner_et_calculer(gdf, df_merge):
    col_cle = "commune_clean"
    gdf_copy = gdf.copy()
    df_copy = df_merge.copy()
    gdf_copy[col_cle] = gdf_copy['NOM_MIN'].apply(nettoyer_chaine)
    df_copy[col_cle] = df_copy['Commune'].apply(nettoyer_chaine)
    return gdf_copy.merge(df_copy, on=col_cle, how='inner')


def ponderer_transports(df):
    # Dictionnaire des poids
    poids = {
        "METRO": 1, 
        "TRAIN": 2, 
        "BUS|METRO": 3, 
        "BUS|TRAM": 4, 
        "BUS|METRO|TRAM": 5, 
        "BUS|TRAIN": 666
    }
    
    # Application du poids et groupement
  
    df["Poids"] = df["Moyen de transport"].map(poids).fillna(1)
    df_resultat = df.groupby(["Commune","Numero Commune"])["Poids"].sum().reset_index()
    
    return df_resultat



def fusionner(df_gauche, df_droite, col_gauche, col_droite):
   
        return df_gauche.merge(df_droite, left_on=col_gauche, right_on=col_droite, how="inner")


                            #Fonctions calculs
#-----------------------------------------------------------------------------------------


def log_per_capita(mon_df, ma_colonne, colonne_population):
    nom_var = f"{ma_colonne}_transitoire"
    mon_df[nom_var] = np.log1p(mon_df[ma_colonne] / mon_df[colonne_population])
    return mon_df


def fonction_z_score(mon_df, ma_colonne):
    nom_var = f"{ma_colonne}_transitoire"
    mon_df[nom_var] = (mon_df[ma_colonne] - mon_df[ma_colonne].mean()) / mon_df[ma_colonne].std()
    return mon_df

def changement_polarité(mon_df, ma_colonne):
    nom_var = f"{ma_colonne}_transitoire"
    mon_df[nom_var] = mon_df[nom_var] * (-1)
    return mon_df

def fonction_norm(mon_df, ma_colonne):
    nom_var = f"{ma_colonne}_transitoire"
    val_min = mon_df[nom_var].min()
    val_max = mon_df[nom_var].max()
    mon_df[nom_var] = (mon_df[nom_var] - val_min) / (val_max - val_min)
    return mon_df

def fonction_mulitplication_notes(mon_df, ma_colonne, note, note2=None):
    nom_var = f"{ma_colonne}_transitoire"
    
    # 1ère multiplication
    mon_df[nom_var] = mon_df[nom_var] * note
    
    # 2ème multiplication uniquement si note2 est renseigné
    if note2 is not None:
        mon_df[nom_var] = mon_df[nom_var] * note2
        
    return mon_df

#-----------------------------------------------------------------------------------------



