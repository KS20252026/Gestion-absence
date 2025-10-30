import streamlit as st
import pandas as pd
import json

# Clé de stockage utilisée pour simuler le 'Cloud'
FIREBASE_COLLECTION_KEY = "simulated_firestore_data"

def init_db():
    """
    Simule l'initialisation de la connexion à la base de données.
    (Dans un environnement réel, ce serait l'initialisation de Firebase/Firestore.)
    """
    # Aucune action nécessaire pour la simulation, mais la fonction est conservée pour l'architecture.
    pass

def fetch_data():
    """
    Simule la récupération des données depuis la base de données Cloud.
    Si aucune donnée n'est trouvée, retourne un DataFrame vide.
    """
    if FIREBASE_COLLECTION_KEY in st.session_state:
        # Reconstruit le DataFrame à partir de la chaîne JSON stockée
        data_json = st.session_state[FIREBASE_COLLECTION_KEY]
        df = pd.read_json(data_json, orient='split')
        
        # S'assurer que les booléens sont conservés
        for col in df.columns:
            if 'Présence' in col:
                df[col] = df[col].astype(bool)
        
        return df
    return pd.DataFrame()

def write_data(df):
    """
    Simule l'écriture des données mises à jour dans la base de données Cloud.
    """
    # Convertit le DataFrame mis à jour en JSON et le stocke
    st.session_state[FIREBASE_COLLECTION_KEY] = df.to_json(orient='split', index=False)
    st.success("💾 Modifications sauvegardées (simulation Cloud réussie).")
